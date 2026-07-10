from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.core.containers import Context, get_context
from app.core.services import DialogCounterService
from app.schemas.services import UnreadCountersResult


router = APIRouter(prefix="/counters", tags=["Counters"])


@router.get("/{user_id}/unread", status_code=HTTPStatus.OK)
async def get_unread_counters(
    user_id: UUID,
    context: Context = Depends(get_context),
) -> UnreadCountersResult:
    service = DialogCounterService(context)
    response = await service.get_unread_counters(user_id=user_id)
    if not response.is_success:
        raise HTTPException(status_code=response.status, detail=response.error_message)
    return response.result


@router.get("/{user_id}/unread/total", status_code=HTTPStatus.OK)
async def get_unread_total(
    user_id: UUID,
    context: Context = Depends(get_context),
) -> int:
    service = DialogCounterService(context)
    response = await service.get_unread_counters(user_id=user_id)
    if not response.is_success:
        raise HTTPException(status_code=response.status, detail=response.error_message)
    return response.result.total
