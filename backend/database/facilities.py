from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError
from typing import Optional, Self, List, NoReturn
from utils.pydanctic_utils import PyObjectId
from bson import ObjectId
from pydantic import BaseModel, Field


class FacilitySchema(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias='_id')
    short_name: str
    full_name: str
    description: Optional[str] = None

    class Config:
        pupulate_by_name = True

class FacilitiesOrm:
    @staticmethod
    def get_orm(request: Request) -> Self:
        return FacilitiesOrm(request.app.state.db['Facilities'])

    def __init__(self, collection_instance: AsyncIOMotorCollection) -> None:
        self.collection = collection_instance
    
    async def add_one(self, facility: FacilitySchema) -> FacilitySchema | NoReturn:
        if await self.collection.find_one({'short_name': facility.short_name}):
            raise DuplicateKeyError(f'Short name {facility.short_name} is taken')
        if await self.collection.find_one({'full_name': facility.full_name}):
            raise DuplicateKeyError(f'Full name {facility.full_name} is taken')
        orm_response = await self.collection.insert_one(facility.model_dump(exclude={'id'}), True)
        facility = await self.get_one_by(_id=orm_response.inserted_id)
        return FacilitySchema(**facility)
    
    async def get_all(self) -> List[FacilitySchema]:
        facilities = await self.collection.find({}).to_list()
        return [FacilitySchema(**facility) for facility in facilities]
    
    async def get_one(self, id: str) -> FacilitySchema:
        facility = await self.collection.find_one({'_id': ObjectId(id)})
        if not facility:
            raise ValueError(f'Facility with ID {id} not found')
        return FacilitySchema(**facility)
    
    async def delete_one(self, id: str) -> None | NoReturn:
        facility = await self.collection.find_one_and_delete({'_id': id})
        if not facility:
            raise ValueError(f'Facility with ID {id} not found')