from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.db import get_session
from app.models import Milestone
from app.routers.common import apply_patch, get_or_404, salvar, to_db
from app.schemas import MilestoneCreate, MilestoneOut, MilestoneUpdate
from app.security import get_current_user

router = APIRouter(
    prefix="/milestones", tags=["milestones"], dependencies=[Depends(get_current_user)]
)


@router.post("", response_model=MilestoneOut, status_code=status.HTTP_201_CREATED)
def criar(payload: MilestoneCreate, session: Session = Depends(get_session)) -> MilestoneOut:
    return MilestoneOut.of(salvar(session, Milestone(**to_db(payload.model_dump()))))


@router.patch("/{ms_id}", response_model=MilestoneOut)
def atualizar(
    ms_id: str, payload: MilestoneUpdate, session: Session = Depends(get_session)
) -> MilestoneOut:
    ms = apply_patch(get_or_404(session, Milestone, ms_id), payload)
    return MilestoneOut.of(salvar(session, ms))


@router.delete("/{ms_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(ms_id: str, session: Session = Depends(get_session)) -> None:
    session.delete(get_or_404(session, Milestone, ms_id))
    session.commit()
