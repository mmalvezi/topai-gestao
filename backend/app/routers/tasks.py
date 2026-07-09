from fastapi import APIRouter, Depends, status
from sqlalchemy import func
from sqlmodel import Session, select

from app.db import get_session
from app.models import Task
from app.routers.common import apply_patch, get_or_404, salvar, to_db
from app.schemas import TaskCreate, TaskOut, TaskUpdate
from app.security import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(get_current_user)])

COLUNA_CONCLUIDO = "concluido"


def proxima_ordem(session: Session, stage: str) -> float:
    """max(order) da coluna destino + 1. Coluna vazia começa em 0."""
    maior = session.exec(select(func.max(Task.position)).where(Task.stage == stage)).one()
    return 0.0 if maior is None else float(maior) + 1


def aplicar_regras(task: Task) -> Task:
    # Seção 7 do PLAN: ao chegar em `concluido`, o pedido de ajuste deixa de fazer sentido.
    if task.stage == COLUNA_CONCLUIDO:
        task.feedback = ""
    return task


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def criar(payload: TaskCreate, session: Session = Depends(get_session)) -> TaskOut:
    dados = to_db(payload.model_dump())
    if dados["position"] is None:
        dados["position"] = proxima_ordem(session, dados["stage"])

    task = aplicar_regras(Task(**dados))
    return TaskOut.of(salvar(session, task))


@router.patch("/{task_id}", response_model=TaskOut)
def atualizar(
    task_id: str, payload: TaskUpdate, session: Session = Depends(get_session)
) -> TaskOut:
    task = get_or_404(session, Task, task_id)
    aplicar_regras(apply_patch(task, payload))
    return TaskOut.of(salvar(session, task))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(task_id: str, session: Session = Depends(get_session)) -> None:
    session.delete(get_or_404(session, Task, task_id))
    session.commit()
