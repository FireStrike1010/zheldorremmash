from typing import Optional, Self, Literal, List, NoReturn, Dict, Any, Union
from beanie import Document, Link, Indexed
from beanie.odm.operators.find.logical import Or, And
from pydantic import Field, ConfigDict
import datetime
from models.audits import (CreateAuditRequest,
                           EditAuditRequest,
                           QuickAuditResponse,
                           ComputedAuditResponse,
                           FillQuestionRequest,
                           AuditResponse,
                           AuditResultsResponse)
from bson import ObjectId, DBRef
from database.tests import Test, QuestionSchema
from database.users import User
from database.facilities import Facility
import asyncio


class ProcessedQuestion(QuestionSchema):
    model_config = ConfigDict(from_attributes=True)
    result: Optional[Any] = Field(default=None, description='Result (answer)')
    comment: Optional[str] = Field(default=None, description='Comment to question')
    esteem_result: Optional[Any] = Field(default=None, description='Esteem result (answer) from same question of esteem audit if defined')
    esteem_comment: Optional[str] = Field(default=None, description='Esteem comment to question from same question of esteem audit if defined')

class Audit(Document):
    audit_type: Literal['common', 'self-esteem']
    esteem_audit: Optional[Link["Audit"]]
    name: str
    description: Optional[str]
    facility: Link[Facility]
    created_at: datetime.datetime
    start_datetime: Optional[Indexed(datetime.datetime)] # type: ignore
    end_datetime: Optional[Indexed(datetime.datetime)] # type: ignore
    audit_leader: Optional[Link[User]]
    _fetched_audit_leader_username: Optional[str]
    _fetched_audit_leader_full_name: Optional[str]
    activation: Literal['on_demand', 'by_datetime']
    results_access: bool
    auditors: Dict[str, Dict[str, List[Link[User]]]]
    ##Beanie's auto fetch doesn't work with nested structure, so it has to be manual fetching
    _fetched_auditors_usernames: Dict[str, Dict[str, List[str]]]
    _fetched_auditors_full_names: Dict[str, Dict[str, List[str]]]
    results: Dict[str, Dict[str, Dict[int, Dict[int, Union[str, int, None]]]]]
    comments: Dict[str, Dict[str, Dict[int, Dict[int, Union[str, None]]]]]
    test: Link[Test]
    is_active: bool
    is_archived: bool

    class Settings:
        name = 'Audits'
        use_cache = False
        use_state_management = True
        state_management_save_previous = True
        cache_expiration_time = datetime.timedelta(days=3)

    async def _fetch_auditors(self) -> None:
        '''TODO: To have hope for fixing beanie's .fetch_all_links() method'''
        self._fetched_auditors_usernames = dict()
        self._fetched_auditors_full_names = dict()
        for part_name, category in self.auditors.items():
            self._fetched_auditors_usernames[part_name] = dict()
            self._fetched_auditors_full_names[part_name] = dict()
            for category_name, users_links in category.items():
                users = list(filter(lambda x: x is not None,
                                    await asyncio.gather(*[user.fetch() for user in users_links])))
                users_full_names = [f"{u.surname} {u.name} {u.patronymic if u.patronymic else ''}".rstrip() for u in users]
                self._fetched_auditors_usernames[part_name][category_name] = [u.username for u in users]
                self._fetched_auditors_full_names[part_name][category_name] = users_full_names

    async def _update_activity(self) -> None:
        if self.activation == 'by_datetime' and not self.is_archived:
            should_be_active = self.start_datetime.replace(tzinfo=None) <= datetime.datetime.now() <= self.end_datetime.replace(tzinfo=None)
            if self.is_active != should_be_active:
                self.is_active = should_be_active
                await self.save_changes()

    @classmethod
    async def _update_audits_status(cls) -> None:
        '''TODO: Upgrade for multiprocessing work with shared memory manager lock
        to prevent running task simultaneously across uvicorn server instances'''
        async for audit in cls.find_many(cls.activation == 'by_datetime', cls.is_archived == False):  # noqa: E712
            await audit._update_activity()

    async def  _validate_participant(self, user: User) -> Dict[str, List[str]]:
        data: Dict[str, List[str]] = dict()
        if not hasattr(self, '_fetched_auditors_usernames'):
            await self._fetch_auditors()
        for part_name, values in self._fetched_auditors_usernames.items():
            found_categories = []
            for category, usernames in values.items():
                if user.role == 'Admin' or user.username in usernames:
                    found_categories.append(category)
            if found_categories:
                data[part_name] = found_categories
        return data

    @classmethod
    async def create(cls, data: CreateAuditRequest) -> Self | NoReturn:
        if data.activation == 'by_datetime':
            if data.start_datetime is None or data.end_datetime is None:
                raise ValueError("Provide start_datetime and end_datetime to control audit's activation 'by_datetime'")
        facility = await Facility.get_one(data.facility_id)
        test = await Test.get_one(data.test_id)
        if data.esteem_audit is not None:
            esteem_audit = await cls.get_one(data.esteem_audit, fetch_links=True)
            if test.id != esteem_audit.test.id:
                raise ValueError("Esteemed audit must be filled by same test")
        else:
            esteem_audit = None
        audit_leader = (await User.get_one_by_username(data.audit_leader)) if data.audit_leader else None
        if audit_leader and audit_leader.role == 'Moderator':
            raise ValueError("Moderators can't be assigned as audit leader")
        ### shit code
        auditors = dict()
        nested_nones = dict()
        for part_name, values in data.auditors.items():
            if part_name not in auditors:
                auditors[part_name] = dict()
                nested_nones[part_name] = dict()
            for category, usernames in values.items():
                users = await asyncio.gather(*[User.get_one_by_username(username) for username in usernames])
                if any(u.role == 'Moderator' for u in users):
                    raise ValueError("Moderators can't be assigned as auditor")
                auditors[part_name][category] = [user.id for user in users]
                try:
                    nested_nones[part_name][category] = {level: {question_number: None for question_number in questions.keys()} for level, questions in test.data[part_name][category].items()}
                except KeyError:
                    raise KeyError(f"Test {test.name} doesn't have {part_name} with {category}")
        audit = cls(audit_type=data.audit_type,
                    esteem_audit=esteem_audit,
                    name=data.name,
                    description=data.description,
                    facility=facility.id,
                    created_at=datetime.datetime.now(),
                    start_datetime=data.start_datetime,
                    end_datetime=data.end_datetime,
                    audit_leader=audit_leader,
                    activation=data.activation,
                    results_access=data.results_access,
                    auditors=auditors,
                    results=nested_nones,
                    comments=nested_nones,
                    test=test.id,
                    is_active=False,
                    is_archived=False)
        audit = await audit.insert()
        await audit._update_activity()
        return audit
    
    async def edit(self, data: EditAuditRequest) -> None | NoReturn:
        if self.is_archived:
            raise PermissionError(f"Audit {self.id} is archived - it can't be changed")
        data = data.model_dump(exclude_unset=True)
        if 'audit_type' in data:
            self.audit_type = data['audit_type']
        if 'esteem_audit' in data:
            esteem_audit = await Audit.get_one(data['esteem_audit'])
            if esteem_audit.test.id != self.test.id:
                raise ValueError("Esteemed audit must be filled by same test")
            self.esteem_audit = esteem_audit
        if 'name' in data:
            self.name = data['name']
        if 'description' in data:
            self.description = data['description']
        if 'facility_id' in data:
            facility = await Facility.get_one(data['facility_id'])
            self.facility = facility
        update_activity_flag = False
        if 'start_datetime' in data:
            self.start_datetime = data['start_datetime']
            update_activity_flag = True
        if 'end_datetime' in data:
            self.end_datetime = data['end_datetime']
            update_activity_flag = True
        if 'activation' in data:
            self.activation = data['activation']
            update_activity_flag = True
        if (self.start_datetime is None or self.end_datetime is None) and self.activation == 'by_datetime':
            raise ValueError("Provide start_datetime and end_datetime to control audit's activation 'by_datetime'")
        if update_activity_flag:
            await self._update_activity()
        if 'results_access' in data:
            self.results_access = data['results_access']
        if 'audit_leader' in data:
            audit_leader = await User.get_one_by_username(data['audit_leader'])
            if audit_leader.role == 'Moderator':
                raise ValueError("Moderators can't be assigned as audit leader")
            self.audit_leader = audit_leader
        if 'auditors' in data:
            auditors = dict()
            for part_name, values in data['auditors'].items():
                if part_name not in auditors:
                    auditors[part_name] = dict()
                if part_name not in self.results:
                    self.results[part_name] = dict()
                    self.comments[part_name] = dict()
                for category, usernames in values.items():
                    users = await asyncio.gather(*[User.get_one_by_username(username) for username in usernames])
                    if any(u.role == 'Moderator' for u in users):
                        raise ValueError("Moderators can't be assigned as auditor")
                    auditors[part_name][category] = [DBRef('Users', user.id) for user in users]
                    if part_name not in self.test.data or category not in self.test.data[part_name]:
                        raise ValueError(f"Test {self.test.name} doesn't have {part_name} with {category}")
                    if part_name not in self.results:
                        self.results[part_name] = {}
                    if category not in self.results[part_name]:
                        nested_nones = {level: {question_number: None for question_number in questions.keys()} for level, questions in self.test.data[part_name][category].items()}
                        self.results[part_name][category] = nested_nones
                        self.comments[part_name][category] = nested_nones
            self.auditors = auditors
        await self.save_changes()

    @classmethod
    async def delete_one(cls, id: str) -> None | NoReturn:
        await cls.find_one(cls.id == ObjectId(id)).delete()

    async def _fetch_all(self, skip_test: bool = False, skip_auditors: bool = False, skip_esteem_audit: bool = False) -> None:
        #Fuck Beanie developers, cant fetch links properly
        facility = await Facility.get(ObjectId(self.facility.ref.id))
        if facility is None:
            facility = Facility(short_name='Deleted Facility', full_name='Deleted Facility')
        self.facility = facility
        if self.audit_leader is not None:
            audit_leader = await User.get(ObjectId(self.audit_leader.ref.id))
            if audit_leader is None:
                audit_leader = User(username="Deleted User",
                                    email="deleted@user.com",
                                    name="Deleted User",
                                    surname="Deleted User",
                                    role='User',
                                    created_at=datetime.datetime.now(),
                                    password="Deleted User")
            self.audit_leader = audit_leader
            self._fetched_audit_leader_username = self.audit_leader.username
            self._fetched_audit_leader_full_name = f"{self.audit_leader.surname} {self.audit_leader.name} {self.audit_leader.patronymic}".rstrip()
        else:
            self._fetched_audit_leader_username = None
            self._fetched_audit_leader_full_name = None
        if not skip_test:
            test = await Test.get(ObjectId(self.test.ref.id))
            if test is None:
                test = Test(name='Deleted Test', created_at=datetime.datetime.now())
            self.test = test
        if not skip_auditors:
            await self._fetch_auditors()
        if not skip_esteem_audit and self.esteem_audit is not None:
            esteem_audit = await Audit.get(ObjectId(self.esteem_audit.ref.id))
            self.esteem_audit = esteem_audit

    @classmethod
    async def get_one(cls, id: str, fetch_links: bool = False, fetch_auditors: bool = False) -> Self | NoReturn:
        audit = await cls.get(ObjectId(id))
        if audit is None:
            raise ValueError(f'Audit with ID {id} not found')
        if fetch_links:
            await audit._fetch_all()
        if fetch_auditors:
            await audit._fetch_auditors()
        return audit
    
    @classmethod
    async def get_one_for_auditor(cls, id: str, user: User) -> ComputedAuditResponse | NoReturn:
        audit = await cls.get_one(id, fetch_links=True, fetch_auditors=True)
        if not audit.is_active or audit.is_archived:
            raise TimeoutError("Audit is closed for filling")
        permissions = await audit._validate_participant(user)
        if len(permissions) == 0:
            raise PermissionError("You are not participant of this audit")
        processed_questions: Dict[str, Dict[str, Dict[int, Dict[int, ProcessedQuestion]]]] = dict()
        #shit code
        for part_name, categories in permissions.items():
            processed_questions[part_name] = dict()
            for category in categories:
                processed_questions[part_name][category] = dict()
        def process_question(audit: Audit, d, part_name: str, category: str, level: int, question_number: int) -> ProcessedQuestion:
            return ProcessedQuestion(
                **d.model_dump(),
                result=audit.results[part_name][category][level][question_number],
                comment=audit.comments[part_name][category][level][question_number],
                esteem_result=audit.esteem_audit.results[part_name][category][level][question_number] if audit.esteem_audit is not None else None,
                esteem_comment=audit.esteem_audit.comments[part_name][category][level][question_number] if audit.esteem_audit is not None else None
                )
        for part_name in processed_questions:
            for category in processed_questions[part_name]:
                qs = audit.test.data[part_name][category]
                qs_rebuilt = {l: {q: process_question(
                    audit=audit,
                    d=qs[l][q],
                    part_name=part_name,
                    category=category,
                    level=l,
                    question_number=q
                    ) for q in qs[l]} for l in qs}
                processed_questions[part_name][category] = qs_rebuilt.copy()
        response = ComputedAuditResponse(
            audit_type=audit.audit_type,
            esteem_audit_id=audit.esteem_audit.id if audit.esteem_audit else None,
            id=audit.id,
            name=audit.name,
            description=audit.description,
            start_datetime=audit.start_datetime,
            end_datetime=audit.end_datetime,
            results_access=audit.results_access,
            audit_leader=audit.audit_leader.username if audit.audit_leader else None,
            auditors=audit._fetched_auditors_usernames,
            test_name=audit.test.name,
            facility_name=audit.facility.short_name,
            data=processed_questions
        )
        return response

    @classmethod
    async def get_my_audits(cls, user: User, which: Literal['archived', 'planned', 'current', 'active', 'inactive', 'passed', 'all', 'self-esteem'] = 'all', test_id: Optional[str] = None) -> List[QuickAuditResponse]:
        now = datetime.datetime.now()
        query = cls.find()
        match which:
            case 'archived':
                query = query.find(cls.is_archived == True) # type: ignore  # noqa: E712
            case 'planned':
                query = query.find(Or(And(cls.start_datetime > now, cls.is_archived == False), And(cls.is_archived == False, cls.activation == 'on_demand', cls.is_active == False))) # type: ignore  # noqa: E712
            case 'current':
                query = query.find(Or(And(cls.start_datetime <= now, cls.end_datetime >= now, cls.is_archived == False), And(cls.is_archived == False, cls.activation == 'on_demand', cls.is_active == True))) # type: ignore  # noqa: E712
            case 'active':
                query = query.find(cls.is_active == True) # type: ignore  # noqa: E712
            case 'inactive':
                query = query.find(cls.is_active == False) # type: ignore  # noqa: E712
            case 'passed':
                query = query.find(cls.end_datetime < now, cls.is_archived == False) # type: ignore  # noqa: E712
            case 'self-esteem':
                query = query.find(cls.audit_type == 'self-esteem') # type: ignore  # noqa: E712
            case 'all':
                query = query
        if test_id is not None:
            query = query.find(cls.test.id == ObjectId(test_id))
        audits = await query.to_list()
        filtered_audits = []
        if user.role in ('Admin', 'Moderator'):
            for audit in audits:
                await audit._fetch_all(skip_test=True, skip_auditors=True)
                audit = QuickAuditResponse(
                    id=audit.id,
                    name=audit.name,
                    description=audit.description,
                    facility=audit.facility.short_name,
                    start_datetime=audit.start_datetime,
                    end_datetime=audit.end_datetime,
                    is_active=audit.is_active,
                    is_archived=audit.is_archived,
                    created_at=audit.created_at,
                    change_activity=(audit.activation == 'on_demand' and not audit.is_archived),
                    results_access=True if user.role == 'Admin' else False
                )
                filtered_audits.append(audit)
        else:
            for audit in audits:
                await audit._fetch_all(skip_test=True, skip_auditors=True)
                permissions = await audit._validate_participant(user)
                if len(permissions) == 0 and audit._fetched_audit_leader_username != user.username:
                    continue
                audit = QuickAuditResponse(
                    id=audit.id,
                    name=audit.name,
                    description=audit.description,
                    facility=audit.facility.short_name,
                    start_datetime=audit.start_datetime,
                    end_datetime=audit.end_datetime,
                    is_active=audit.is_active,
                    is_archived=audit.is_archived,
                    created_at=audit.created_at,
                    change_activity=all([audit._fetched_audit_leader_username == user.username, audit.activation == 'on_demand', not audit.is_archived]),
                    results_access=audit.results_access,
                    my_permissions=permissions
                )
                filtered_audits.append(audit)
        return filtered_audits

    async def process(self) -> AuditResponse:
        return AuditResponse(
            audit_type=self.audit_type,
            esteem_audit_id=self.esteem_audit.id if self.esteem_audit is not None else None,
            esteem_audit_name=self.esteem_audit.name if self.esteem_audit is not None else None,
            id=self.id,
            name=self.name,
            description=self.description,
            facility_id=self.facility.id,
            facility_name=self.facility.short_name,
            test_id=self.test.id,
            test_name=self.test.name,
            start_datetime=self.start_datetime,
            end_datetime=self.end_datetime,
            results_access=self.results_access,
            activation=self.activation,
            is_active=self.is_active,
            is_archived=self.is_archived,
            audit_leader=self._fetched_audit_leader_username,
            audit_leader_full_name=self._fetched_audit_leader_full_name,
            auditors=self._fetched_auditors_usernames,
            auditors_full_names=self._fetched_auditors_full_names)

    async def process_with_results(self, user: User) -> AuditResultsResponse:
        data = await self.process()
        if user.role != 'Admin' and not self.results_access:
            raise PermissionError('You dont have permission to access results for this audit')
        permissions = await self._validate_participant(user)
        if len(permissions) == 0:
            raise PermissionError('You dont have permission to access results for this audit')
        filtered_results = dict()
        filtered_comments = dict()
        coefficients = dict()
        for part_name, categories in permissions.items():
            filtered_results[part_name] = dict()
            filtered_comments[part_name] = dict()
            if part_name not in coefficients:
                coefficients[part_name] = self.test.coefficients[part_name] if self.test.coefficients is not None else None
            for category in categories:
                filtered_results[part_name][category] = self.results[part_name][category]
                filtered_comments[part_name][category] = self.comments[part_name][category]
        if self.esteem_audit is not None:
            filtered_esteem_results = dict()
            filtered_esteem_comments = dict()
            for part_name, categories in permissions.items():
                filtered_esteem_results[part_name] = dict()
                filtered_esteem_comments[part_name] = dict()
                for category in categories:
                    filtered_esteem_results[part_name][category] = self.esteem_audit.results[part_name][category]
                    filtered_esteem_comments[part_name][category] = self.esteem_audit.comments[part_name][category]
        else:
            filtered_esteem_results = None
            filtered_esteem_comments = None
        return AuditResultsResponse(**data.model_dump(),
                                    coefficients=coefficients,
                                    results=filtered_results,
                                    comments=filtered_comments,
                                    esteem_results=filtered_esteem_results,
                                    esteem_comments=filtered_esteem_comments)

    async def fill_questions(self, user: User, data: List[FillQuestionRequest]) -> None | NoReturn:
        permissions = await self._validate_participant(user)
        if not self.is_active or self.is_archived:
            raise TimeoutError("Audit is closed for filling")
        for question in data:
            if "." in question.part_name or "." in question.category:
                raise ValueError("Field names couldn't contain dots in them")
            if question.part_name not in permissions or question.category not in permissions[question.part_name]:
                raise PermissionError(f"You dont have permission to fill that question (you're not auditor for {question.part_name} - {question.category})")
            self.results[question.part_name][question.category][question.level][question.question_number] = question.result
            self.comments[question.part_name][question.category][question.level][question.question_number] = question.comment
        await self.save_changes()

    async def change_activity(self, user: User, data: bool) -> None | NoReturn:
        self._fetch_all(skip_test=True, skip_auditors=True)
        if user.role == 'Admin' or user.username == self._fetched_audit_leader_username:
            if self.activation == 'by_datetime':
                raise ValueError('Activation of this audit meant to be "by_datetime", so it cant be activated/deactivated by leader')
            self.is_active = data
            await self.save_changes()
        else:
            raise PermissionError('You are not leader of this audit')
    
    async def to_archive(self) -> None:
        self.is_archived = True
        self.is_active = False
        await self.save_changes()
    
    @classmethod
    async def nuke_collection(cls) -> int:
        delete_result = await cls.get_pymongo_collection().delete_many({})
        return delete_result.deleted_count