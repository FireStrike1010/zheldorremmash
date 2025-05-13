from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError
from utils.session_validator import get_session_key, verify_role
from database.facilities import Facility
from models.facilities import AddFacilityRequest, FacilityResponse
from typing import List


router = APIRouter(prefix='/facilities', tags=['Facilities'])


@router.get('/', response_model=List[FacilityResponse])
async def get_all(session_key: str = Depends(get_session_key)):
    await verify_role(session_key)
    facilities = await Facility.get_all()
    facilities = [FacilityResponse.model_validate(f) for f in facilities]
    return facilities

@router.get('/@{id}', response_model=FacilityResponse)
async def get_one(id: str, session_key: str = Depends(get_session_key)):
    await verify_role(session_key)
    try:
        facility = await Facility.get_one(id)
        return FacilityResponse.model_validate(facility)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))

@router.delete('/@{id}')
async def delete_one(id: str, session_key: str = Depends(get_session_key)):
    await verify_role(session_key, possible_roles=['Admin'])
    try:
        facility = await Facility.get_one(id)
        await facility.delete()
    except ValueError as e:
        raise HTTPException(404, detail=str(e))

@router.post('/add', response_model=FacilityResponse)
async def add_one(data: AddFacilityRequest,
                  session_key: str = Depends(get_session_key)):
    await verify_role(session_key, possible_roles=['Admin'])
    try:
        facility = await Facility.add_one(data)
        return facility
    except DuplicateKeyError:
        raise HTTPException(409, detail='Facility already exists')