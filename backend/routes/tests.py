from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError
from datetime import datetime
from models.tests import AddTestRequest, AddTestResponse, QuickTest
from database.users import UsersOrm
from database.tests import TestsOrm, TestSchema
from utils.session_validator import verify_role, get_session_key, get_current_user
from utils.pydantic_utils import pass_fields
from typing import List

router = APIRouter(prefix='/tests', tags=['Tests'])

@router.post('/add', response_model=AddTestResponse)
async def add(data: AddTestRequest,
              session_key: str = Depends(get_session_key),
              userorm: UsersOrm = Depends(UsersOrm.get_orm),
              testorm: TestsOrm = Depends(TestsOrm.get_orm)):
    await verify_role(session_key, userorm, possible_roles=['Admin'])
    test = TestSchema(**data.model_dump(), created_at=datetime.now())
    try:
        test = await testorm.add_one(test)
    except DuplicateKeyError as e:
        raise HTTPException(409, detail=str(e))
    except Exception as e:
        raise HTTPException(502, detail=str(e))
    return AddTestResponse(_id=test.id, created_at=test.created_at)

@router.get('/@{test_id}', response_model=TestSchema)
async def get(test_id: str,
              session_key: str = Depends(get_session_key),
              userorm: UsersOrm = Depends(UsersOrm.get_orm),
              testorm: TestsOrm = Depends(TestsOrm.get_orm)):
    await get_current_user(session_key, userorm)
    test = await testorm.get_one(test_id)
    if not test:
        raise HTTPException(404, detail='Test not found')
    return pass_fields(TestSchema, test)

@router.get('/', response_model=List[QuickTest])
async def get_all(session_key: str = Depends(get_session_key),
                  userorm: UsersOrm = Depends(UsersOrm.get_orm),
                  testorm: TestsOrm = Depends(TestsOrm.get_orm)):
    await get_current_user(session_key, userorm)
    tests = await testorm.get_all()
    return [pass_fields(QuickTest, test) for test in tests]

@router.delete('/@{id}')
async def delete(id: str,
                 session_key: str = Depends(get_session_key),
                 userorm: UsersOrm = Depends(UsersOrm.get_orm),
                 testorm: TestsOrm = Depends(TestsOrm.get_orm)):
    await verify_role(session_key, userorm, possible_roles=['Admin'])
    try:
        await testorm.delete_test(id)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))
    return

##TODO: Complete CRUD operations for part_name, category, level, question individually

