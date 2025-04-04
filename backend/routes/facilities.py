from fastapi import APIRouter, Depends, HTTPException
from utils.session_validator import get_session_key, verify_role, get_current_user
from database.users import UsersOrm
from database.facilities import FacilitiesOrm, FacilitySchema
from models.facilities import AddFacilityRequest
from typing import List


router = APIRouter(prefix='/facilities', tags=['Facilities'])


@router.get('/', response_model=List[FacilitySchema])
async def get_all(session_key: str = Depends(get_session_key),
                  userorm: UsersOrm = Depends(UsersOrm.get_orm),
                  facilityorm: FacilitiesOrm = Depends(FacilitiesOrm.get_orm)):
    await get_current_user(session_key, userorm)
    facilities = await facilityorm.get_all()
    return [FacilitySchema(**facility) for facility in facilities]

@router.get('/@{id}', response_model=FacilitySchema)
async def get_one(id: str,
                  session_key: str = Depends(get_session_key),
                  userorm: UsersOrm = Depends(UsersOrm.get_orm),
                  facilityorm: FacilitiesOrm = Depends(FacilitiesOrm.get_orm)):
    await get_current_user(session_key, userorm)
    try:
        facility = await facilityorm.get_one(id)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))
    return FacilitySchema(**facility)

@router.delete('/@{id}')
async def delete_one(id: str,
                     session_key: str = Depends(get_session_key),
                     userorm: UsersOrm = Depends(UsersOrm.get_orm),
                     facilityorm: FacilitiesOrm = Depends(FacilitiesOrm.get_orm)):
    await verify_role(session_key, userorm, possible_roles=['Admin'])
    try:
        await facilityorm.delete_one(id)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))
    return

@router.post('/add', response_model=FacilitySchema)
async def add_one(data: AddFacilityRequest,
                  session_key: str = Depends(get_session_key),
                  userorm: UsersOrm = Depends(UsersOrm.get_orm),
                  facilityorm: FacilitiesOrm = Depends(FacilitiesOrm.get_orm)):
    await verify_role(session_key, userorm, possible_roles=['Admin'])
    facility = await facilityorm.add_one(FacilitySchema(**data.model_dump()))
    return facility