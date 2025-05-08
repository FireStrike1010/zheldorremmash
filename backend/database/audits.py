from typing import Optional, Self, Literal, List, NoReturn, Dict, Any
from beanie import Document, Link
from pydantic import Field, ConfigDict
from datetime import datetime, timedelta
from models.audits import CreateAuditRequest, ComputedAuditResponse, FillQuestionRequest, AuditOutputResponse
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
    created_at: datetime
    start_datetime: Optional[datetime]
    end_datetime: Optional[datetime]
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
        use_cache = True
        cache_expiration_time = timedelta(days=3)
        indexes = [
            "is_active"
            "activation",
            "start_datetime",
            "end_datetime",
        ]

    @classmethod
    async def _update_audits_status(cls) -> None:
        now = datetime.now()
        async for audit in cls.find_many(cls.activation == 'by_datetime'):
            if audit.start_datetime <= now <= audit.end_datetime:
                changed_status = True
            else:
                changed_status = False
            if audit.is_active != changed_status: 
                audit.is_active = changed_status
                await audit.sync()

    async def _validate_participant(self, user: User) -> Dict[str, List[str]]:
        data: Dict[str, List[str]] = dict()
        for part_name, values in self.auditors.items():
            found_categories = []
            for category, user_links in values.items():
                if user.role == 'Admin':
                    found_categories.append(category)
                else:
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
            is_active = True if (datetime.now() >= data.start_datetime.replace(tzinfo=None) and datetime.now() < data.end_datetime.replace(tzinfo=None)) else False
        else:
            is_active = False
        audit_leader = await User.get_one_by_username(data.audit_leader)
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
                    created_at=datetime.now(),
                    audit_leader=audit_leader.id,
                    auditors=auditors,
                    test=test.id,
                    results=nested_nones,
                    comments=nested_nones)
        return await audit.insert()
    
    @classmethod
    async def _get_one(cls, id: str) -> Self | NoReturn:
        audit = await cls.get(ObjectId(id), fetch_links=True)
        if audit is None:
            raise ValueError(f'Audit with ID {id} not found')
        return audit
    
    @classmethod
    async def get_one_for_auditor(cls, id: str, user: User) -> ComputedAuditResponse | NoReturn:
        audit = await cls._get_one(id)
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
    async def get_my_audits(cls, user: User, which: Literal['future', 'active', 'passed', 'all'] = 'all') -> List[Self]:
        match which:
            case 'future':
                audits = await cls.find_many(cls.end_datetime > datetime.now(), cls.is_active == False).to_list() # type: ignore  # noqa: E712
            case 'active':
                audits = await cls.find_many(cls.is_active == True).to_list() # type: ignore  # noqa: E712
            case 'passed':
                audits = await cls.find_many(cls.end_datetime < datetime.now()).to_list()
            case 'all':
                audits = await cls.find_all().to_list()
        if user.role == 'Admin':
            return audits
        audits = list(filter(lambda x: x._validate_participant(user), audits))
        return audits
    
    @classmethod
    async def change_activity(cls, id: str, user: User, data: bool) -> None | NoReturn:
        audit = await cls._get_one(id)
        if user.role == 'Admin' or user.username == audit.audit_leader:
            if audit.activation == 'by_datetime':
                raise ValueError('Activation of this audit meant to be "by_datetime", so it cant be activated/deactivated by leader')
            audit.is_active = data
            await audit.sync()
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
        await self.sync()

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
