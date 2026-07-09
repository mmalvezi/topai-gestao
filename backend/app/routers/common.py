"""Peças compartilhadas pelos routers de CRUD."""

import datetime as dt
from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session, SQLModel

# Vocabulário do front -> vocabulário do banco.
# `col`/`order` viram `stage`/`position` porque `column` e `order` são reservadas no SQL.
FIELD_MAP = {
    "desc": "description",
    "col": "stage",
    "order": "position",
    "appName": "app_name",
    "launchDate": "launch_date",
    "launchCity": "launch_city",
}


def to_db(data: dict[str, Any]) -> dict[str, Any]:
    """Traduz as chaves do JSON externo para os nomes das colunas."""
    return {FIELD_MAP.get(k, k): v for k, v in data.items()}


def get_or_404(session: Session, model: type[SQLModel], obj_id: str) -> Any:
    obj = session.get(model, obj_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro não encontrado.",
        )
    return obj


def sem_nulos(dados: dict[str, Any], campos: tuple[str, ...]) -> dict[str, Any]:
    """Remove chaves cujo valor é None. Para colunas NOT NULL com default no model
    (`Feedback.date`, `Decision.date`): omitir deixa o default agir; mandar None
    tentaria gravar NULL."""
    return {k: v for k, v in dados.items() if not (k in campos and v is None)}


def apply_patch(obj: Any, payload: SQLModel, ignorar_none: tuple[str, ...] = ()) -> Any:
    """Aplica só os campos enviados (`exclude_unset`) e carimba `updated_at`."""
    dados = sem_nulos(payload.model_dump(exclude_unset=True), ignorar_none)
    for campo, valor in to_db(dados).items():
        setattr(obj, campo, valor)
    obj.updated_at = dt.datetime.now(dt.timezone.utc)
    return obj


def salvar(session: Session, obj: Any) -> Any:
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj
