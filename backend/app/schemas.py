"""Payloads de entrada da API.

Para cada entidade: um schema de criação e um de update parcial (tudo opcional,
para casar com o `PATCH`). Os routers das próximas fases consomem estes tipos.

`dt.date` qualificado pelo mesmo motivo de `models.py`: há campos chamados `date`.
"""

import datetime as dt

from sqlmodel import SQLModel


class TaskCreate(SQLModel):
    title: str
    description: str = ""
    category: str = ""
    priority: str = "media"
    assignee: str = "none"
    stage: str = "ideias"
    due: dt.date | None = None
    feedback: str = ""
    position: float = 0.0


class TaskUpdate(SQLModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    priority: str | None = None
    assignee: str | None = None
    stage: str | None = None
    due: dt.date | None = None
    feedback: str | None = None
    position: float | None = None


class GoalCreate(SQLModel):
    title: str
    current: int = 0
    target: int = 0
    color: str = ""
    position: float = 0.0


class GoalUpdate(SQLModel):
    title: str | None = None
    current: int | None = None
    target: int | None = None
    color: str | None = None
    position: float | None = None


class MilestoneCreate(SQLModel):
    title: str
    description: str = ""
    date: dt.date | None = None
    status: str = "todo"
    position: float = 0.0


class MilestoneUpdate(SQLModel):
    title: str | None = None
    description: str | None = None
    date: dt.date | None = None
    status: str | None = None
    position: float | None = None


class FeatureCreate(SQLModel):
    title: str
    description: str = ""
    impact: int = 1
    effort: int = 1
    status: str = "ideia"
    position: float = 0.0


class FeatureUpdate(SQLModel):
    title: str | None = None
    description: str | None = None
    impact: int | None = None
    effort: int | None = None
    status: str | None = None
    position: float | None = None


class FeedbackCreate(SQLModel):
    text: str
    source: str = "outro"
    type: str = "ideia"
    author: str = ""
    date: dt.date | None = None


class FeedbackUpdate(SQLModel):
    text: str | None = None
    source: str | None = None
    type: str | None = None
    author: str | None = None
    date: dt.date | None = None


class DecisionCreate(SQLModel):
    title: str
    decision: str = ""
    rationale: str = ""
    date: dt.date | None = None
    status: str = "ativa"


class DecisionUpdate(SQLModel):
    title: str | None = None
    decision: str | None = None
    rationale: str | None = None
    date: dt.date | None = None
    status: str | None = None


class SettingsUpdate(SQLModel):
    app_name: str | None = None
    launch_date: dt.date | None = None
    launch_city: str | None = None


class UserCreate(SQLModel):
    name: str
    email: str
    password: str
    role: str = "member"


class UserRead(SQLModel):
    id: str
    name: str
    email: str
    role: str
    active: bool
