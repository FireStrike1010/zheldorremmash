from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError
from typing import Optional, Self, Literal, List, NoReturn, Dict, Any
from utils.pydanctic_utils import PyObjectId
from bson import ObjectId
from pydantic import BaseModel, Field
from datetime import datetime


FieldType = Literal['checkbox', 'text', 'number', 'radio']

class QuestionSchema(BaseModel):
    task_value: str
    control_element: Optional[str]
    list_events: Optional[str]
    additional_info: Optional[str] = None
    answer_type: FieldType
    answer_label: Optional[str] = None
    answer_type_attributes: Optional[Dict[str, Any]] = None

class TestSchema(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias='_id')
    name: str
    description: Optional[str] = None
    created_at: datetime
    ### [Разделы[Категории[Уровни[Вопросы(QuestionSchema)]]]]
    data: Optional[Dict[str, Dict[str, List[List[QuestionSchema]]]]] = None

    class Config:
        pupulate_by_name = True
    

class TestsOrm:
    @staticmethod
    def get_orm(request: Request) -> Self:
        return TestsOrm(request.app.state.db['Tests'])
    
    def __init__(self, collection_instance: AsyncIOMotorCollection) -> None:
        self.collection = collection_instance
    
    async def add_one(self, test: TestSchema) -> TestSchema | NoReturn:
        if await self.collection.find_one({'name': test.name}):
            raise DuplicateKeyError(f'Test {test.name} is taken')
        orm_response = await self.collection.insert_one(test.model_dump(exclude={'id'}), True)
        test = await self.get_one(id=orm_response.inserted_id)
        return test
    
    async def get_one(self, id: str) -> Optional[TestSchema]:
        return await self.collection.find_one({'_id': ObjectId(id)})
        
    async def get_all(self) -> List[TestSchema]:
        tests = await self.collection.find({}).to_list()
        return [TestSchema(**test) for test in tests]
    
    async def delete_test(self, id: str) -> None | NoReturn:
        result = await self.collection.find_one_and_delete({'_id': ObjectId(id)})
        if not result:
            raise ValueError(f'Test with ID {id} not found')
    
    async def add_question(self,
                           id: str,
                           part_name: str,
                           category: str,
                           level: int,
                           data: QuestionSchema) -> None | NoReturn:
        await self.collection.update_one(
            {'_id': ObjectId(id)},
            {'$push': {f'data.{part_name}.{category}.{level}': data.model_dump()}})
    
    async def update_question(self,
                              id: str,
                              part_name: str,
                              category: str,
                              level: int,
                              data: QuestionSchema) -> None | NoReturn:
        await self.collection.update_one(
            {'_id': ObjectId(id)},
            {'$set': {f'data.{part_name}.{category}.{level}': data.model_dump()}})

    async def delete_question(self,
                              id: str,
                              part_name: str,
                              category: str,
                              level: int,
                              index: int) -> None | NoReturn:
        await self.collection.update_one(
            {'_id': ObjectId(id)},
            {'$set': {f'data.{part_name}.{category}.{level}.{index}': None}})
        
    async def add_level(self,
                        id: str,
                        part_name: str,
                        category: str,
                        data: List[QuestionSchema]) -> None | NoReturn:
        await self.collection.update_one(
            {'_id': ObjectId(id)},
            {'$push': {f'data.{part_name}.{category}': data}})
    
    async def update_level(self,
                           id: str,
                           part_name: str,
                           category: str,
                           level: int,
                           data: List[QuestionSchema]) -> None | NoReturn:
        await self.collection.update_one(
            {'_id': ObjectId(id)},
            {'$set': {f'data.{part_name}.{category}.{level}': [x.model_dump() for x in data]}})
    
    async def delete_level(self,
                           id: str,
                           part_name: str,
                           category: str,
                           level: int) -> None | NoReturn:
        await self.collection.update_one(
            {'_id': ObjectId(id)},
            {'$set': {f'data.{part_name}.{category}.{level}': None}})
    
    async def update_category(self,
                              id: str,
                              part_name: str,
                              category: str,
                              data: List[List[QuestionSchema]]) -> None | NoReturn:
        await self.collection.update_one(
            {'_id': ObjectId(id)},
            {'$set': {f'data.{part_name}.{category}': [[x.model_dump() for x in data[index]] for index in range(data)]}})
    
    async def delete_category(self,
                              id: str,
                              part_name: str,
                              category: str) -> None | NoReturn:
        await self.collection.update_one(
            {'_id': ObjectId(id)},
            {'$unset': {f'data.{part_name}.{category}': None}})
    
    async def update_part_name(self,
                               id: str,
                               part_name: str,
                               data: Dict[str, List[List[QuestionSchema]]]) -> None | NoReturn:
        await self.collection.update_one(
            {'_id': ObjectId(id)},
            {'$set': {f'data.{part_name}': {key: [[x.model_dump() for x in value[index]] for index in range(value)] for key, value in data.items()}}},)
    
    async def delete_category(self,
                              id: str,
                              part_name: str) -> None | NoReturn:
        await self.collection.update_one(
            {'_id': ObjectId(id)},
            {'$unset': {f'data.{part_name}': None}})
    