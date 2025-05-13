from typing import Optional, Self, Literal, List, NoReturn, Dict, Any, OrderedDict
from pydantic import BaseModel, Field, ConfigDict
from beanie import Document, Indexed
from datetime import datetime, timedelta
from models.tests import AddTestRequest, AddQuestionRequest, RemoveRequest
from bson import ObjectId


FieldType = Literal['checkbox', 'text', 'number', 'radio']

class QuestionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_value: str = Field(description="Roadmap requirements, how to achieve")
    control_element: Optional[str] = Field(default=None, description="Control validation records (Names of mandatory documents that demonstrate proper control execution)")
    additional_info: Optional[str] = Field(default=None, description="Additional info")
    answer_type: FieldType = Field(description="HTML input type: checkbox - boolean, text - text (free-form text), number - integer/float, radio - text (selector)")
    answer_label: Optional[str] = Field(default=None, description="HTML label for input")
    answer_type_attributes: Optional[Dict[str, Any]] = Field(default=None, description="Additional field for HTML input style or whatever")

class Test(Document):
    name: Indexed(str) # type: ignore
    description: Optional[str] = None
    created_at: datetime
    ### {Разделы{Категории[Уровни[Вопросы(QuestionSchema)]]}}
    data: Optional[OrderedDict[str, OrderedDict[str, OrderedDict[int, OrderedDict[int, QuestionSchema]]]]] = None
    
    class Settings:
        name = "Tests"
        use_cache = False
        use_state_management = True
        cache_expiration_time = timedelta(days=3)
    
    @classmethod
    async def add_one(cls, test: AddTestRequest) -> Self | NoReturn:
        new_test = cls(**test.model_dump(), created_at=datetime.now())
        return await new_test.insert()
    
    @classmethod
    async def get_one(cls, id: str) -> Self | NoReturn:
        test = await cls.get(ObjectId(id))
        if test is None:
            raise ValueError(f'Test with ID {id} not found')
        return test
    
    async def insert_question(self, data: AddQuestionRequest) -> Self | NoReturn:
        part_name: str = data.part_name
        category: str = data.category
        level: int | None = data.level
        question_index: int | None = data.number
        if self.data is None:
            self.data = dict()
        if part_name not in self.data:
            self.data[part_name] = dict()
        if category not in self.data[part_name]:
            self.data[part_name][category] = dict()
        if level is None:
            keys = self.data[part_name][category].keys()
            level = 1 if not keys else max(keys) + 1
        if level not in self.data[part_name][category].keys():
            self.data[part_name][category][level] = dict()
            self.data[part_name][category] = dict(sorted(self.data[part_name][category].items()))
        if question_index is None:
            keys = self.data[part_name][category][level].keys()
            question_index = 1 if not keys else max(keys) + 1
        if question_index not in self.data[part_name][category][level].keys():
            self.data[part_name][category][level][question_index] = None
            self.data[part_name][category][level] = dict(sorted(self.data[part_name][category][level].items()))
        data = QuestionSchema.model_validate(data)
        self.data[part_name][category][level][question_index] = data
        return await self.save_changes()

    @classmethod
    async def get_all(cls) -> List[Self]:
        return await cls.find_all().to_list()
    