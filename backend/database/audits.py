from typing import Optional, Self, Literal, List, NoReturn, Dict, Any
from beanie import Document, Link
from pydantic import Field
from datetime import datetime, timedelta
from models.audits import CreateAuditRequest, ComputedAuditResponse, FillQuestionRequest
from bson import ObjectId
from database.tests import Test, QuestionSchema
from database.users import User
from database.facilities import Facility
import asyncio


class ProcessedQuestion(QuestionSchema):
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
    results: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]]
    comments: Dict[str, Dict[str, Dict[str, Dict[str, Optional[str]]]]]
    test: Link[Test]
    is_active: bool

    class Settings:
        name = 'Audits'
        use_cache = True
        cache_expiration_time = timedelta(days=3)

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
        facility = await Facility.get_one(data.facility)
        if data.activation == 'by_datetime':
            if data.start_datetime is None or data.end_datetime is None:
                raise ValueError("Provide start_datetime and end_datetime to control audit's activation 'by_datetime'")
            is_active = True if (datetime.now() >= data.start_datetime and datetime.now() < data.end_datetime) else False
        else:
            is_active = False
        audit_leader = await User.get_one_by_username(data.audit_leader)
        test = await Test.get_one(data.test_id)
        ### shit code
        auditors = dict()
        for part_name, values in data.auditors.items():
            if part_name not in auditors:
                auditors[part_name] = dict()
            for category, usernames in values.items():
                auditors[part_name][category] = await asyncio.gather(*[User.get_one_by_username(username) for username in usernames])
        ###shit code again
        nested_nones = {part: {cat: {lvl: {q: None for q in q_dict} for lvl, q_dict in lvl_dict.items()} for cat, lvl_dict in cat_dict.items()} for part, cat_dict in test.data.items()}
        audit = cls(**data.model_dump(exclude=['facility', 'is_active', 'audit_leader', 'test_id', 'auditors']),
                    facility=facility,
                    is_active=is_active,
                    created_at=datetime.now(),
                    audit_leader=audit_leader,
                    test=test,
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
        access_filter = cls._validate_participant(audit, user)
        if len(access_filter) == 0:
            raise PermissionError("You are not participant of this audit")
        questions: Dict[str, Dict[str, Dict[int, Dict[int, ProcessedQuestion]]]] = dict()
        for part_name, categories in access_filter.items():
            if part_name not in questions:
                questions[part_name] = dict()
            for category in categories:
                if category not in questions[part_name]:
                    questions[part_name][category] = dict()
                for level in audit.test.data[part_name][category]:
                    if level not in questions[part_name][category]:
                        questions[part_name][category][level] = dict()
                    for question_number, question in level.items():
                        question = ProcessedQuestion.model_validate(
                            question,
                            result=audit.results[part_name][category][level][question_number],
                            comment=audit.comments[part_name][category][level][question_number]
                        )
                        questions[part_name][category][level][question_number] = question
        result = ComputedAuditResponse(
            id=audit.id,
            name=audit.name,
            description=audit.description,
            start_datetime=audit.start_datetime,
            end_datetime=audit.end_datetime,
            audit_leader=None if audit.audit_leader is None else (await audit.audit_leader.fetch()).username,
            test_name=(await audit.test.fetch()).name,
            facility_name=(await audit.facility.fetch()).short_name,
            data=questions
        )
        return result

    @classmethod
    async def get_my_audits(cls, user: User, which: Literal['future', 'active', 'passed', 'all'] = 'all') -> List[Self]:
        match which:
            case 'future':
                audits = await cls.find_many(cls.start_datetime > datetime.now()).to_list()
            case 'active':
                audits = await cls.find_many(cls.is_active).to_list()
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
            audit.is_active = data
            audit.save()
        else:
            raise PermissionError('You are not leader of this audit')
    
    async def fill_questions(self, user: User, data: List[FillQuestionRequest]) -> None | NoReturn:
        permissions = self._validate_participant(user)
        if not self.is_active:
            raise TimeoutError("Audit is closed for filling")
        for question in data:
            if question.part_name not in permissions or question.category not in permissions[question.part_name]:
                raise PermissionError(f"You dont have permission to fill that question (you're not auditor for {question.part_name} - {question.category})")
            self.results[question.part_name][question.category][question.level][question.question_number] = question.result
            self.comments[question.part_name][question.category][question.level][question.question_number] = question.comment
        self.save()
