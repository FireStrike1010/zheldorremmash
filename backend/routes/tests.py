from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError
from models.tests import AddTestRequest, QuickTest, TestResponse, AddQuestionRequest, RemoveRequest
from utils.session_validator import verify_role, get_session_key
from typing import List
from database import Test


router = APIRouter(prefix='/tests', tags=['Tests'])

@router.post('/add', response_model=QuickTest)
async def add(data: AddTestRequest, session_key: str = Depends(get_session_key)):
    await verify_role(session_key, possible_roles=['Admin'])
    try:
        test = await Test.add_one(data)
        return QuickTest.model_validate(test)
    except DuplicateKeyError as e:
        raise HTTPException(409, detail=str(e))
    except Exception as e:
        raise HTTPException(502, detail=str(e))

@router.get('/@{id}', response_model=TestResponse)
async def get(id: str, session_key: str = Depends(get_session_key)):
    await verify_role(session_key)
    try:
        test = await Test.get_one(id)
        return TestResponse.model_validate(test)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))

@router.get('/', response_model=List[QuickTest])
async def get_all(session_key: str = Depends(get_session_key)):
    await verify_role(session_key)
    tests = await Test.get_all()
    return [QuickTest.model_validate(test) for test in tests]

@router.delete('/@{id}')
async def delete_test(id: str, session_key: str = Depends(get_session_key)):
    await verify_role(session_key, possible_roles=['Admin'])
    try:
        test = await Test.get_one(id)
        await test.delete()
    except ValueError as e:
        raise HTTPException(404, detail=str(e))

@router.put('/@{id}/insert_question', response_model=TestResponse)
async def insert_question(id: str, data: AddQuestionRequest, session_key: str = Depends(get_session_key)):
    await verify_role(session_key, possible_roles=['Admin'])
    try:
        test = await Test.get_one(id)
        test = await test.insert_question(data)
        return TestResponse.model_validate(test)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))

#@router.delete('/@{id}/remove', response_model=TestResponse)
#async def delete_question(id: str, data: RemoveRequest, session_key: str = Depends(get_session_key)):
#    await verify_role(session_key, possible_roles=['Admin'])
#    try:
#        test = await Test.get_one(id)
#        await test.remove(data)
#        return TestResponse.model_validate(test)
#    except ValueError as e:
#        raise HTTPException(404, detail=str(e))


