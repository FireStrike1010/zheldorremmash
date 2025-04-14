from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from database.tests import QuestionSchema
from utils.pydantic_utils import PyObjectId

class AddTestRequest(BaseModel):
    name: str = Field(description='Name of the test')
    description: Optional[str] = Field(default=None, description='Additional description of the test')
    created_at: datetime = Field(description='Datetime of creation')
    ### [Разделы[Категории[Уровни[Вопросы(QuestionSchema)]]]]
    data: Optional[Dict[str, Dict[str, List[List[QuestionSchema]]]]] = Field(default=None, description='The test - {"part_name": {"category": List of levels[List of questions[]]}}')

class AddTestResponse(BaseModel):
    id: PyObjectId = Field(description='Id of test that is accessible by tests/@{id}')
    created_at: datetime = Field(description='Datetime of creation')

class QuickTest(BaseModel):
    id: PyObjectId = Field(description='Id of test that is accessible by tests/@{id}')
    name: str = Field(description='Name of the test')
    description: Optional[str] = Field(description='Additional description of the test')
    created_at: datetime = Field(description='Datetime of creation')