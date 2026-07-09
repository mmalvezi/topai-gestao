from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.db import get_session
from app.models import Feedback
from app.routers.common import apply_patch, get_or_404, salvar, sem_nulos, to_db
from app.schemas import FeedbackCreate, FeedbackOut, FeedbackUpdate
from app.security import get_current_user

router = APIRouter(prefix="/feedback", tags=["feedback"], dependencies=[Depends(get_current_user)])

# `date` é NOT NULL com default "hoje" no model: sem valor, deixamos o default agir.
COM_DEFAULT = ("date",)


@router.post("", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
def criar(payload: FeedbackCreate, session: Session = Depends(get_session)) -> FeedbackOut:
    dados = sem_nulos(payload.model_dump(), COM_DEFAULT)
    return FeedbackOut.of(salvar(session, Feedback(**to_db(dados))))


@router.patch("/{fb_id}", response_model=FeedbackOut)
def atualizar(
    fb_id: str, payload: FeedbackUpdate, session: Session = Depends(get_session)
) -> FeedbackOut:
    fb = apply_patch(get_or_404(session, Feedback, fb_id), payload, ignorar_none=COM_DEFAULT)
    return FeedbackOut.of(salvar(session, fb))


@router.delete("/{fb_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(fb_id: str, session: Session = Depends(get_session)) -> None:
    session.delete(get_or_404(session, Feedback, fb_id))
    session.commit()
