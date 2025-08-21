from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional, Literal, Dict, List, Any, OrderedDict, Union
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
    is_archived: bool = Field(description='Is audit archived')
    created_at: datetime = Field(description='Datetime of creation')
    change_activity: bool = Field(description="Can i change activity of audit")
    results_access: bool = Field(description="Can i access results")
    my_permissions: Optional[Dict[str, List[str]]] = Field(default=None, description="My part names and categories for audit")

class CreateAuditRequest(BaseModel):
    audit_type: Literal['common', 'self-esteem'] = Field(default='common', description='Type of audit')
    esteem_audit: Optional[PyObjectId] = Field(default=None, description='ID of self esteem audit, need to be by same test. Used for comparison while filling and in results afterwards')
    name: str = Field(description='Name of audit')
    description: Optional[str] = Field(default=None, description='Additional info about audit')
    facility_id: PyObjectId = Field(description='ID of facility in Mongo DB')
    start_datetime: Optional[datetime] = Field(default=None, description='Audit start datetime')
    end_datetime: Optional[datetime] = Field(default=None, description='Audit end datetime')
    activation: Literal['on_demand', 'by_datetime'] = Field(description='System that opens audit for completion. "on_demand" - controlled by audit_leader or admin, "by_datetime" - automatic controlled by current time')
    results_access: bool = Field(description='Give the access to results to auditors')
    audit_leader: Optional[str] = Field(default=None, description='Username of audit leader')
    test_id: PyObjectId = Field(description='ID of test in Mongo DB')
    auditors: Dict[str, Dict[str, List[str]]] = Field(description='[part_name[category[usernames_of_auditors]]]')

class EditAuditRequest(BaseModel):
    audit_type: Optional[Literal['common', 'self-esteem']] = Field(default=None, description='Type of audit')
    esteem_audit: Optional[PyObjectId] = Field(default=None, description='ID of self esteem audit, need to be by same test. Used for comparison while filling and in results afterwards')
    name: Optional[str] = Field(default=None, description='Name of audit')
    description: Optional[str] = Field(default=None, description='Additional info about audit')
    facility_id: Optional[PyObjectId] = Field(default=None, description='ID of facility in Mongo DB')
    start_datetime: Optional[datetime] = Field(default=None, description='Audit start datetime')
    end_datetime: Optional[datetime] = Field(default=None, description='Audit end datetime')
    activation: Optional[Literal['on_demand', 'by_datetime']] = Field(default=None, description='System that opens audit for completion. "on_demand" - controlled by audit_leader or admin, "by_datetime" - automatic controlled by current time')
    results_access: Optional[bool] = Field(default=None, description='Give the access to results to auditors')
    audit_leader: Optional[str] = Field(default=None, description='Username of audit leader')
    auditors: Optional[Dict[str, Dict[str, List[str]]]] = Field(default=None, description='[part_name[category[usernames_of_auditors]]]')

class ProcessedQuestion(QuestionSchema):
    result: Optional[Any] = Field(default=None, description='Result (answer)')
    comment: Optional[str] = Field(default=None, description='Comment to question')
    esteem_result: Optional[Any] = Field(default=None, description='Esteem result (answer) from same question of esteem audit if defined')
    esteem_comment: Optional[str] = Field(default=None, description='Esteem comment to question from same question of esteem audit if defined')

class ComputedAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    audit_type: Literal['common', 'self-esteem'] = Field()
    esteem_audit_id: Optional[PyObjectId] = Field()
    id: PyObjectId = Field()
    name: str = Field()
    description: Optional[str] = Field()
    start_datetime: Optional[datetime] = Field()
    end_datetime: Optional[datetime] = Field()
    results_access: bool = Field()
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
    result: Union[str, int, None] = Field()
    comment: Optional[str] = Field(default=None)

    @field_validator('result', mode='before')
    def convert_result_to_int_if_possible(cls, value: object) -> Union[str, int]:
        if isinstance(value, int):
            return value
        elif value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return str(value)

class AuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    audit_type: Literal['common', 'self-esteem'] = Field()
    esteem_audit_id: Optional[PyObjectId] = Field()
    esteem_audit_name: Optional[str] = Field()
    id: PyObjectId = Field()
    name: str = Field()
    description: Optional[str] = Field()
    facility_id: PyObjectId = Field()
    facility_name: str = Field()
    test_id: PyObjectId = Field()
    test_name: str = Field()
    start_datetime: Optional[datetime] = Field()
    end_datetime: Optional[datetime] = Field()
    results_access: bool = Field()
    activation: Literal['on_demand', 'by_datetime'] = Field()
    is_active: bool = Field()
    is_archived: bool = Field()
    audit_leader: Optional[str] = Field(default=None)
    audit_leader_full_name: Optional[str] = Field(default=None)
    auditors: Dict[str, Dict[str, List[str]]] = Field()
    auditors_full_names: Dict[str, Dict[str, List[str]]] = Field()

class AuditResultsResponse(AuditResponse):
    model_config = ConfigDict(from_attributes=True)
    coefficients: Optional[OrderedDict[str, float]] = Field(default=None, description='Coefficients of parts ("part_name") of test')
    results: Dict[str, Dict[str, Dict[int, Dict[int, Any]]]] = Field()
    comments: Dict[str, Dict[str, Dict[int, Dict[int, Optional[str]]]]] = Field()
    esteem_results: Optional[Dict[str, Dict[str, Dict[int, Dict[int, Any]]]]] = Field(default=None)
    esteem_comments: Optional[Dict[str, Dict[str, Dict[int, Dict[int, Optional[str]]]]]] = Field(default=None)