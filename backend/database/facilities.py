from typing import Optional, Self, List, NoReturn
from beanie import Document, Indexed
from bson import ObjectId
from models.facilities import AddFacilityRequest

class Facility(Document):
    short_name: Indexed(str, unique=True) # type: ignore
    full_name: Indexed(str, unique=True) # type: ignore
    description: Optional[str] = None

    class Settings:
        name = "Facilities"
        use_cache = False
        use_state_management = True

    @classmethod
    async def add_one(cls, facility: AddFacilityRequest) -> Self | NoReturn:
        new_facility = cls(**facility.model_dump())
        return await new_facility.insert()

    @classmethod
    async def get_all(cls) -> List[Self]:
        return await cls.find_all().to_list()
    
    @classmethod
    async def get_one(cls, id: str) -> Self | NoReturn:
        facility = await cls.get(ObjectId(id))
        if not facility:
            raise ValueError(f'Facility with ID {id} not found')
        return facility
