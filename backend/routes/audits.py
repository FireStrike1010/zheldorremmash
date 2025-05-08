from fastapi import APIRouter, Depends, HTTPException
from utils.session_validator import get_session_key, verify_role, get_current_user
from models.audits import CreateAuditRequest, QuickAuditResponse, ComputedAuditResponse, FillQuestionRequest, AuditOutputResponse
from database import Audit
from typing import Literal, List

router = APIRouter(prefix='/audits', tags=['Audits'])


@router.post('/add', response_model=QuickAuditResponse)
async def add_one(data: CreateAuditRequest, session_key: str = Depends(get_session_key)):
    await verify_role(session_key, possible_roles=['Admin', 'Moderator'])
    try:
        audit = await Audit.create(data)
        return QuickAuditResponse.model_validate(audit)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))

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

@router.put('/@{id}')
async def fill_questions(id: str, data: List[FillQuestionRequest], session_key: str = Depends(get_session_key)):
    user = await get_current_user(session_key)
    try:
        audit = await Audit._get_one(id)
        await audit.fill_questions(user, data)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(403, detail=str(e))
    except PermissionError as e:
        raise HTTPException(403, detail=str(e))

@router.get('/my_audits/{type}', response_model=List[QuickAuditResponse])
async def get_my_audits(type: Literal['future', 'active', 'passed', 'all'], session_key: str = Depends(get_session_key)):
    user = await get_current_user(session_key)
    audits = await Audit.get_my_audits(user, which=type)
    return [QuickAuditResponse.model_validate(audit) for audit in audits]

@router.post('/@{id}/set_active/{data}')
async def change_activity(id: str, data: bool, session_key: str = Depends(get_session_key)):
    user = await get_current_user(session_key)
    try:
        await Audit.change_activity(id, user, data)
    except ValueError as e:
        raise HTTPException(403, detail=str(e))
    except PermissionError as e:
        raise HTTPException(403, detail=str(e))

@router.get('/@{id}/results', response_model=AuditOutputResponse)
async def get_results(id: str, session_key: str = Depends(get_session_key)):
    user = await get_current_user(session_key)
    try:
        audit = await Audit._get_one(id)
        return await audit.get_results(user)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(403, detail=str(e))