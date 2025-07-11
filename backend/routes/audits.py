from fastapi import APIRouter, Depends, HTTPException
from utils.session_validator import get_session_key, verify_role, get_current_user, get_password
from utils.password_hasher import verify_password
from models.audits import CreateAuditRequest, EditAuditRequest, QuickAuditResponse, ComputedAuditResponse, FillQuestionRequest, AuditResponse, AuditResultsResponse
from database import Audit
from typing import Literal, List

router = APIRouter(prefix='/audits', tags=['Audits'])


@router.post('/add')
async def add_one(data: CreateAuditRequest, session_key: str = Depends(get_session_key)):
    await verify_role(session_key, possible_roles=['Admin', 'Moderator'])
    try:
        await Audit.create(data)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))
    except KeyError as e:
        raise HTTPException(404, detail=str(e))

@router.patch('/@{id}/edit', response_model=AuditResponse)
async def edit(data: EditAuditRequest, id: str, session_key: str = Depends(get_session_key)):
    await verify_role(session_key, ['Admin', 'Moderator'])
    try:
        audit = await Audit.get_one(id, fetch_links=True)
        await audit.edit(data)
        audit = await Audit.get_one(id, fetch_links=True)
        return await audit.process()
    except ValueError as e:
        raise HTTPException(404, detail=str(e))

@router.get('/@{id}', response_model=ComputedAuditResponse)
async def get(id: str, session_key: str = Depends(get_session_key)):
    user = await get_current_user(session_key)
    try:
        audit = await Audit.get_one_for_auditor(id, user)
        return audit
    except ValueError as e:
        raise HTTPException(404, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(403, detail=str(e))
    except PermissionError as e:
        raise HTTPException(403, detail=str(e))


@router.get('/@{id}/full_data', response_model=AuditResponse)
async def get_full_data(id: str, session_key: str = Depends(get_session_key)):
    await verify_role(session_key, ['Admin', 'Moderator'])
    try:
        audit = await Audit.get_one(id, fetch_links=True)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))
    return await audit.process()

@router.put('/@{id}')
async def fill_questions(id: str, data: List[FillQuestionRequest], session_key: str = Depends(get_session_key)):
    user = await get_current_user(session_key)
    try:
        audit = await Audit.get_one(id, fetch_links=True)
        await audit.fill_questions(user, data)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(403, detail=str(e))
    except PermissionError as e:
        raise HTTPException(403, detail=str(e))

@router.get('/my_audits/{type}', response_model=List[QuickAuditResponse])
async def get_my_audits(type: Literal['archived', 'planned', 'current', 'active', 'inactive', 'passed', 'all'], session_key: str = Depends(get_session_key)):
    user = await get_current_user(session_key)
    audits = await Audit.get_my_audits(user, which=type)
    return audits

@router.post('/@{id}/set_active/{data}')
async def change_activity(id: str, data: bool, session_key: str = Depends(get_session_key)):
    user = await get_current_user(session_key)
    try:
        audit = await Audit.get_one(id)
        await audit.change_activity(user, data)
    except ValueError as e:
        raise HTTPException(403, detail=str(e))
    except PermissionError as e:
        raise HTTPException(403, detail=str(e))

@router.get('/@{id}/results', response_model=AuditResultsResponse)
async def get_results(id: str, session_key: str = Depends(get_session_key)):
    user = await get_current_user(session_key)
    try:
        audit = await Audit.get_one(id, fetch_links=True)
        return await audit.process_with_results(user)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(403, detail=str(e))

@router.delete('/@{id}')
async def delete(id: str, session_key: str = Depends(get_session_key)):
    await verify_role(session_key, possible_roles=['Admin', 'Moderator'])
    try:
        await Audit.delete_one(id)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))

@router.post('/@{id}/archive')
async def to_archive(id: str, session_key: str = Depends(get_session_key), password: str = Depends(get_password)):
    user = await get_current_user(session_key)
    if user.role != 'Admin':
        raise HTTPException(403, "You don't have that privilege, you must be ['Admin']")
    if user.username == 'root' or verify_password(user.password, password):
        audit = await Audit.get_one(id)
        await audit.to_archive()
    else:
        raise HTTPException(401, detail='Invalid password')

@router.delete('/nuke_collection')
async def nuke_collection(session_key: str = Depends(get_session_key)):
    user = await get_current_user(session_key)
    if user.username != 'root':
        raise HTTPException(403, "You don't have that privilege, you must use MASTER_KEY")
    return await Audit.nuke_collection()