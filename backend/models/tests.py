from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, OrderedDict, Any, Dict, Literal
from datetime import datetime
from utils.pydantic_utils import PyObjectId


FieldType = Literal['checkbox', 'text', 'number', 'radio']


class QuestionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_value: str = Field(description="Roadmap requirements, how to achieve")
    control_element: Optional[str] = Field(default=None, description="Control validation records (Names of mandatory documents that demonstrate proper control execution)")
    additional_info: Optional[str] = Field(default=None, description="Additional info")
    answer_type: FieldType = Field(description="HTML input type: checkbox - boolean, text - text (free-form text), number - integer/float, radio - text (selector)")
    answer_label: Optional[str] = Field(default=None, description="HTML label for input")
    answer_type_attributes: Optional[Dict[str, Any]] = Field(default=None, description="Additional field for HTML input style or whatever")


##TODO: replace copy of QuestionSchema with ForwardRef or whatever to prevent circular import

class TestBase(BaseModel):
    name: str = Field(description='Name of the test')
    description: Optional[str] = Field(default=None, description='Additional description of the test')


class AddTestRequest(TestBase):
    ### [Разделы[Категории[Уровни[Вопросы(QuestionSchema)]]]]
    data: Optional[OrderedDict[str, OrderedDict[str, OrderedDict[int, OrderedDict[int, QuestionSchema]]]]] = Field(default=None, description='The test - {"part_name": {"category": List of levels[List of questions[question]]}}')

class QuickTest(TestBase):
    model_config = ConfigDict(from_attributes=True)
    id: PyObjectId = Field(description='Id of test that is accessible by tests/@{id}')
    created_at: datetime = Field(description='Datetime of creation')

class QuestionBaseRequest(BaseModel):
    part_name: str = Field(description="Part name (first nested key entry)")
    category: str = Field(description="Category (second nested key entry)")
    level: Optional[int] = Field(default=None, description="Level (third nested number (starting from 1) entry) (by default writes in the end of ordered dictionary)")
    number: Optional[int] = Field(default=None, description="Number of question (fourth and last nested number (started from 1) entry) (by default writes in the end of ordered dictionary)")

class TestResponse(QuickTest):
    ### [Разделы[Категории[Уровни[Вопросы(QuestionSchema)]]]]
    data: Optional[OrderedDict[str, OrderedDict[str, OrderedDict[int, OrderedDict[int, QuestionSchema]]]]] = Field(default=None, description='The test - {"part_name": {"category": List of levels[List of questions[question]]}}')

class AddQuestionRequest(QuestionBaseRequest):
    question: QuestionSchema

class RemoveRequest(BaseModel):
    part_name: Optional[str] = Field(description="Part name (first nested key entry)")
    category: Optional[str] = Field(description="Category (second nested key entry)")
    level: Optional[int] = Field(default=None, description="Level (third nested number (starting from 1) entry)")
    number: Optional[int] = Field(default=None, description="Number of question (fourth and last nested number (started from 1) entry)")
