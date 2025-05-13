from typing import Optional, Self, Literal, List, NoReturn, Dict, Any
from beanie import Document, Link, Indexed
from pydantic import Field, ConfigDict
import datetime
from models.audits import CreateAuditRequest, ComputedAuditResponse, FillQuestionRequest, AuditOutputResponse, QuickAuditResponse
from bson import ObjectId
from database.tests import Test, QuestionSchema
from database.users import User
from database.facilities import Facility
import asyncio


class ProcessedQuestion(QuestionSchema):
    model_config = ConfigDict(from_attributes=True)
    result: Optional[Any] = Field(default=None, description='Result (answer)')
    comment: Optional[str] = Field(default=None, description='Comment to question')


class Audit(Document):
    name: str
    description: Optional[str]
    facility: Link[Facility]
    created_at: datetime.datetime
    start_datetime: Optional[Indexed(datetime.datetime)] # type: ignore
    end_datetime: Optional[Indexed(datetime.datetime)] # type: ignore
    audit_leader: Optional[Link[User]]
    activation: Literal['on_demand', 'by_datetime']
    results_access: bool
    auditors: Dict[str, Dict[str, List[Link[User]]]]
    results: Dict[str, Dict[str, Dict[int, Dict[int, Any]]]]
    comments: Dict[str, Dict[str, Dict[int, Dict[int, Optional[str]]]]]
    test: Link[Test]
    is_active: bool

    class Settings:
        name = 'Audits'
        use_cache = False
        use_state_management = True
        state_management_save_previous = True
        cache_expiration_time = datetime.timedelta(days=3)


    @classmethod
    async def _update_audits_status(cls) -> None:
        now = datetime.datetime.now()
        async for audit in cls.find_many(cls.activation == 'by_datetime'):
            if not audit.start_datetime or not audit.end_datetime:
                continue
            should_be_active = audit.start_datetime <= now <= audit.end_datetime
            if audit.is_active != should_be_active:
                audit.is_active = should_be_active
                await audit.save_changes()

    async def _validate_participant(self, user: User) -> Dict[str, List[str]]:
        data: Dict[str, List[str]] = dict()
        for part_name, values in self.auditors.items():
            found_categories = []
            for category, user_links in values.items():
                if user.role == 'Admin':
                    found_categories.append(category)
                else:
                    if not all(link.is_fetched for link in user_links):
                        users = await asyncio.gather(*[link.fetch() for link in user_links])
                    if user in users:
                        found_categories.append(category)
            if found_categories:
                data[part_name] = found_categories
        return data
        

    @classmethod
    async def create(cls, data: CreateAuditRequest) -> Self | NoReturn:
        facility = await Facility.get_one(data.facility_id)
        if data.activation == 'by_datetime':
            if data.start_datetime is None or data.end_datetime is None:
                raise ValueError("Provide start_datetime and end_datetime to control audit's activation 'by_datetime'")
            now = datetime.datetime.now()
            is_active = True if (now >= data.start_datetime.replace(tzinfo=None) and now < data.end_datetime.replace(tzinfo=None)) else False
        else:
            is_active = False
        audit_leader = (await User.get_one_by_username(data.audit_leader)) if data.audit_leader else None
        test = await Test.get_one(data.test_id)
        ### shit code
        auditors = dict()
        nested_nones = dict()
        for part_name, values in data.auditors.items():
            if part_name not in auditors:
                auditors[part_name] = dict()
                nested_nones[part_name] = dict()
            for category, usernames in values.items():
                users = await asyncio.gather(*[User.get_one_by_username(username) for username in usernames])
                auditors[part_name][category] = [user.id for user in users]
                try:
                    nested_nones[part_name][category] = {level: {question_number: None for question_number in questions.keys()} for level, questions in test.data[part_name][category].items()}
                except KeyError:
                    raise ValueError(f'Test {test.name} doest have {part_name} with {category}')
        audit = cls(**data.model_dump(exclude=['facility', 'is_active', 'audit_leader', 'test_id', 'auditors']),
                    facility=facility.id,
                    is_active=is_active,
                    created_at=datetime.datetime.now(),
                    audit_leader=audit_leader.id if audit_leader else None,
                    auditors=auditors,
                    test=test.id,
                    results=nested_nones,
                    comments=nested_nones)
        return await audit.insert()
    
    @classmethod
    async def get_one(cls, id: str, fetch_links: bool = False) -> Self | NoReturn:
        audit = await cls.get(ObjectId(id), fetch_links=fetch_links)
        if audit is None:
            raise ValueError(f'Audit with ID {id} not found')
        return audit
    
    @classmethod
    async def get_one_for_auditor(cls, id: str, user: User) -> ComputedAuditResponse | NoReturn:
        audit = await cls.get_one(id, fetch_links=True)
        if not audit.is_active:
            raise TimeoutError("Audit is closed for filling")
        permissions = await cls._validate_participant(audit, user)
        if len(permissions) == 0:
            raise PermissionError("You are not participant of this audit")
        processed_questions: Dict[str, Dict[str, Dict[int, Dict[int, ProcessedQuestion]]]] = dict()
        #shit code
        for part_name, categories in permissions.items():
            if part_name not in processed_questions:
                processed_questions[part_name] = dict()
            for category in categories:
                if category not in processed_questions[part_name]:
                    processed_questions[part_name][category] = dict()
                for level, questions in audit.test.data[part_name][category].items():
                    if level not in processed_questions[part_name][category]:
                        processed_questions[part_name][category][level] = dict()
                    for question_number, question in questions.items():
                        if question_number not in processed_questions[part_name][category][level]:
                            processed_questions[part_name][category][level] = dict()
                        processed_question = ProcessedQuestion(
                            **question.model_dump(),
                            result=audit.results[part_name][category][level][question_number],
                            comment=audit.comments[part_name][category][level][question_number]
                        )
                        processed_questions[part_name][category][level][question_number] = processed_question
        response = ComputedAuditResponse(
            id=audit.id,
            name=audit.name,
            description=audit.description,
            start_datetime=audit.start_datetime,
            end_datetime=audit.end_datetime,
            audit_leader=None if audit.audit_leader is None else audit.audit_leader.username,
            test_name=audit.test.name,
            facility_name=audit.facility.short_name,
            data=processed_questions
        )
        return response

    @classmethod
    async def get_my_audits(cls, user: User, which: Literal['future', 'active', 'passed', 'all'] = 'all') -> List[QuickAuditResponse]:
        now = datetime.datetime.now()
        match which:
            case 'future':
                audits = await cls.find(cls.end_datetime > now, cls.is_active == False).to_list() # type: ignore  # noqa: E712
            case 'active':
                audits = await cls.find(cls.is_active == True).to_list() # type: ignore  # noqa: E712
            case 'passed':
                audits = await cls.find(cls.end_datetime < now).to_list()
            case 'all':
                audits = await cls.find_all().to_list()
        filtered_audits = []
        if user.role == 'Admin':
            for audit in audits:
                audit = QuickAuditResponse(
                    id=audit.id,
                    name=audit.name,
                    start_datetime=audit.start_datetime,
                    end_datetime=audit.end_datetime,
                    is_active=audit.is_active,
                    created_at=audit.created_at,
                    change_activity=True
                )
                filtered_audits.append(audit)
        else:
            for audit in audits:
                permissions = await audit._validate_participant(user)
                if len(permissions) == 0:
                    continue
                audit = QuickAuditResponse(
                    id=audit.id,
                    name=audit.name,
                    start_datetime=audit.start_datetime,
                    end_datetime=audit.end_datetime,
                    is_active=audit.is_active,
                    created_at=audit.created_at,
                    change_activity=(True if (await audit.audit_leader.fetch()).username == user.username else False),
                    my_permissions=permissions
                )
                filtered_audits.append(audit)
        return filtered_audits
    
    async def change_activity(self, id: str, user: User, data: bool) -> None | NoReturn:
        if user.role == 'Admin' or user.username == (await self.audit_leader.fetch()).username:
            if self.activation == 'by_datetime':
                raise ValueError('Activation of this audit meant to be "by_datetime", so it cant be activated/deactivated by leader')
            self.is_active = data
            await self.save_changes()
        else:
            raise PermissionError('You are not leader of this audit')
    
    async def fill_questions(self, user: User, data: List[FillQuestionRequest]) -> None | NoReturn:
        permissions = await self._validate_participant(user)
        if not self.is_active:
            raise TimeoutError("Audit is closed for filling")
        for question in data:
            if question.part_name not in permissions or question.category not in permissions[question.part_name]:
                raise PermissionError(f"You dont have permission to fill that question (you're not auditor for {question.part_name} - {question.category})")
            self.results[question.part_name][question.category][question.level][question.question_number] = question.result
            self.comments[question.part_name][question.category][question.level][question.question_number] = question.comment
        await self.save_changes()

    async def get_results(self, user: User) -> AuditOutputResponse:
        if user.role != 'Admin' and not self.results_access:
            raise PermissionError('You dont have permission to access results for this audit')
        permissions = await self._validate_participant(user)
        if len(permissions) == 0:
            raise PermissionError('You dont have permission to access results for this audit')
        filtered_results = dict()
        filtered_comments = dict()
        for part_name, categories in permissions.items():
            filtered_results[part_name] = dict()
            filtered_comments[part_name] = dict()
            for category in categories:
                filtered_results[part_name][category] = self.results[part_name][category]
                filtered_comments[part_name][category] = self.comments[part_name][category]
        return AuditOutputResponse(
            id=self.id,
            name=self.name,
            facility_name=self.facility.short_name,
            facility_id=self.facility.id,
            test_name=self.test.name,
            test_id=self.test.id,
            results=filtered_results,
            comments=filtered_comments,
            start_datetime=self.start_datetime,
            end_datetime=self.end_datetime,
            is_active=self.is_active
        )

    @classmethod
    async def delete_one(cls, id: str) -> None | NoReturn:
        await cls.find_one(cls.id == ObjectId(id)).delete()