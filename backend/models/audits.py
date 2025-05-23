from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Literal, Dict, List, Any, OrderedDict
from utils.pydantic_utils import PyObjectId
from database.tests import QuestionSchema


class QuickAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: PyObjectId = Field(description='ID of audit in Mongo DB')
    name: str = Field(description='Name of audit')
    facility: str = Field(description='Facility short name')
    start_datetime: Optional[datetime] = Field(description='Start datetime of audit')
    end_datetime: Optional[datetime] = Field(description='End datetime of audit')
    is_active: bool = Field(description='Is audit available to fill')
    created_at: datetime = Field(description='Datetime of creation')
    change_activity: bool = Field(description="Can i change activity of audit")
    results_access: bool = Field(description="Can i access results")
    my_permissions: Optional[Dict[str, List[str]]] = Field(default=None, description="My part names and categories for audit")


class CreateAuditRequest(BaseModel):
    name: str = Field(description='Name of audit')
    description: Optional[str] = Field(default=None, description='Additional info about audit')
    facility_id: PyObjectId = Field(description='ID of facility in Mongo DB')
    start_datetime: Optional[datetime] = Field(description='Audit start datetime')
    end_datetime: Optional[datetime] = Field(description='Audit end datetime')
    activation: Literal['on_demand', 'by_datetime'] = Field(description='System that opens audit for completion. "on_demand" - controlled by audit_leader or admin, "by_datetime" - automatic controlled by current time')
    results_access: bool = Field(description='Give the access to results to auditors')
    audit_leader: Optional[str] = Field(description='Username of audit leader')
    test_id: PyObjectId = Field(description='ID of test in Mongo DB')
    auditors: Dict[str, Dict[str, List[str]]] = Field(description='[part_name[category[usernames_of_auditors]]]')


class ProcessedQuestion(QuestionSchema):
    result: Optional[Any] = Field(default=None, description='Result (answer)')
    comment: Optional[str] = Field(default=None, description='Comment to question')


class ComputedAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: PyObjectId = Field()
    name: str = Field()
    description: Optional[str] = Field()
    start_datetime: Optional[datetime] = Field()
    end_datetime: Optional[datetime] = Field()
    audit_leader: Optional[str] = Field()
    auditors: Dict[str, Dict[str, List[str]]] = Field()
    test_name: str = Field()
    facility_name: str = Field()
    data: OrderedDict[str, OrderedDict[str, OrderedDict[int, OrderedDict[int, ProcessedQuestion]]]] = Field()

class FillQuestionRequest(BaseModel):
    part_name: str = Field()
    category: str = Field()
    level: int = Field()
    question_number: int = Field()
    result: Any = Field()
    comment: Optional[str] = Field()

class AuditOutputResponse(BaseModel):
    id: PyObjectId = Field()
    name: str = Field()
    facility_name: str = Field()
    facility_id: PyObjectId = Field()
    test_name: str = Field()
    test_id: PyObjectId = Field()
    results: Dict[str, Dict[str, Dict[int, Dict[int, Any]]]] = Field()
    comments: Dict[str, Dict[str, Dict[int, Dict[int, Optional[str]]]]] = Field()
    start_datetime: Optional[datetime] = Field()
    end_datetime: Optional[datetime] = Field()
    is_active: bool = Field()
    audit_leader: Optional[str] = Field(default=None)
    auditors: Dict[str, Dict[str, List[str]]] = Field()
    auditors_full_names: Dict[str, Dict[str, List[str]]] = Field()