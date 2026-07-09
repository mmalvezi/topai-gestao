from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.db import get_session
from app.models import Decision
from app.routers.common import apply_patch, get_or_404, salvar, sem_nulos, to_db
from app.schemas import DecisionCreate, DecisionOut, DecisionUpdate
from app.security import get_current_user

router = APIRouter(
    prefix="/decisions", tags=["decisions"], dependencies=[Depends(get_current_user)]
)

# `date` é NOT NULL com default "hoje" no model: sem valor, deixamos o default agir.
COM_DEFAULT = ("date",)


@router.post("", response_model=DecisionOut, status_code=status.HTTP_201_CREATED)
def criar(payload: DecisionCreate, session: Session = Depends(get_session)) -> DecisionOut:
    dados = sem_nulos(payload.model_dump(), COM_DEFAULT)
    return DecisionOut.of(salvar(session, Decision(**to_db(dados))))


@router.patch("/{dec_id}", response_model=DecisionOut)
def atualizar(
    dec_id: str, payload: DecisionUpdate, session: Session = Depends(get_session)
) -> DecisionOut:
    dec = apply_patch(get_or_404(session, Decision, dec_id), payload, ignorar_none=COM_DEFAULT)
    return DecisionOut.of(salvar(session, dec))


@router.delete("/{dec_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(dec_id: str, session: Session = Depends(get_session)) -> None:
    session.delete(get_or_404(session, Decision, dec_id))
    session.commit()
