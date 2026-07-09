"""Tabelas do Topaí (seção 6 do PLAN.md).

Convenções:
- PK `id` em texto (uuid4 em str), gerada por default.
- `created_at` / `updated_at` em toda tabela, em UTC.
- A etapa da tarefa é `stage` — `column` é palavra reservada no SQL.
  O front chama de `col`; o mapeamento acontece na serialização.

Os tipos de data são usados qualificados (`dt.date`) de propósito: há campos
chamados `date`, e um `from datetime import date` faria o nome do campo sombrear
o do tipo na hora de resolver a anotação.
"""

import datetime as dt
from uuid import uuid4

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def _new_id() -> str:
    return str(uuid4())


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _today() -> dt.date:
    return _utcnow().date()


class Base(SQLModel):
    """Campos comuns a todas as tabelas. Não é uma tabela por si só."""

    id: str = Field(default_factory=_new_id, primary_key=True)
    created_at: dt.datetime = Field(default_factory=_utcnow, sa_type=DateTime(timezone=True))
    updated_at: dt.datetime = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": _utcnow},
    )


class User(Base, table=True):
    __tablename__ = "users"

    name: str
    email: str = Field(unique=True, index=True)
    password_hash: str
    role: str = Field(default="member")  # owner | member
    color: str = Field(default="#4C6EF5")  # avatar no front
    active: bool = Field(default=True)


class Task(Base, table=True):
    __tablename__ = "tasks"

    title: str
    description: str = Field(default="")
    category: str = Field(default="")
    priority: str = Field(default="media")
    assignee: str = Field(default="none")
    stage: str = Field(default="ideias", index=True)
    due: dt.date | None = Field(default=None)
    feedback: str = Field(default="")
    position: float = Field(default=0.0)


class Goal(Base, table=True):
    __tablename__ = "goals"

    title: str
    current: int = Field(default=0)
    target: int = Field(default=0)
    color: str = Field(default="")
    position: float = Field(default=0.0)


class Milestone(Base, table=True):
    __tablename__ = "milestones"

    title: str
    description: str = Field(default="")
    date: dt.date | None = Field(default=None)
    status: str = Field(default="todo")  # todo | doing | done
    position: float = Field(default=0.0)


class Feature(Base, table=True):
    __tablename__ = "features"

    title: str
    description: str = Field(default="")
    impact: int = Field(default=1)  # 1-3
    effort: int = Field(default=1)  # 1-3
    status: str = Field(default="ideia")  # ideia | planejado | construindo | pronto
    position: float = Field(default=0.0)


class Feedback(Base, table=True):
    __tablename__ = "feedback"

    text: str
    source: str = Field(default="outro")  # prestador | cliente | condominio | outro
    type: str = Field(default="ideia")  # elogio | problema | ideia
    author: str = Field(default="")
    date: dt.date = Field(default_factory=_today)


class Decision(Base, table=True):
    __tablename__ = "decisions"

    title: str
    decision: str = Field(default="")
    rationale: str = Field(default="")
    date: dt.date = Field(default_factory=_today)
    status: str = Field(default="ativa")  # ativa | revisada


class AppSettings(Base, table=True):
    """Registro único, sempre com id `1`."""

    __tablename__ = "settings"

    id: str = Field(default="1", primary_key=True)
    app_name: str = Field(default="Topaí")
    launch_date: dt.date | None = Field(default=None)
    launch_city: str = Field(default="")
