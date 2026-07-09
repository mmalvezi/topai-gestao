from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.db import get_session
from app.models import Goal
from app.routers.common import apply_patch, get_or_404, salvar, to_db
from app.schemas import GoalCreate, GoalOut, GoalUpdate
from app.security import get_current_user

router = APIRouter(prefix="/goals", tags=["goals"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def criar(payload: GoalCreate, session: Session = Depends(get_session)) -> GoalOut:
    return GoalOut.of(salvar(session, Goal(**to_db(payload.model_dump()))))


@router.patch("/{goal_id}", response_model=GoalOut)
def atualizar(
    goal_id: str, payload: GoalUpdate, session: Session = Depends(get_session)
) -> GoalOut:
    goal = apply_patch(get_or_404(session, Goal, goal_id), payload)
    return GoalOut.of(salvar(session, goal))


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(goal_id: str, session: Session = Depends(get_session)) -> None:
    session.delete(get_or_404(session, Goal, goal_id))
    session.commit()
