"""Contrato de JSON da API.

O vocabulário externo é o do front (`index.html`), não o do banco. Onde os dois
divergem — por palavra reservada no SQL ou por convenção — o mapa está em
`routers/common.py:FIELD_MAP`:

    desc -> description    col -> stage    order -> position
    appName -> app_name    launchDate -> launch_date    launchCity -> launch_city

Os schemas de saída trazem um `.of(obj)` que constrói a partir do model. É explícito
de propósito: alias do Pydantic silenciaria um campo renomeado no banco, o `.of()`
quebra na hora.

`position` existe em goals/milestones/features mas não faz parte do contrato — só a
Task usa ordem de verdade (kanban).

`dt.date` qualificado porque há campos chamados `date` (Python 3.14, PEP 649).
"""

import datetime as dt

from pydantic import computed_field
from sqlmodel import SQLModel

from app.models import (
    AppSettings,
    Decision,
    Feature,
    Feedback,
    Goal,
    Milestone,
    Task,
    User,
)

# ----------------------------------------------------------------- auth (Fase 2)


class UserCreate(SQLModel):
    name: str
    email: str
    password: str
    role: str = "member"


class UserPublic(SQLModel):
    """Única forma de devolver um usuário completo. Nunca inclui `password_hash`."""

    id: str
    name: str
    email: str
    role: str
    color: str

    @computed_field
    @property
    def initials(self) -> str:
        return self.name[:2].upper()


class UserMini(SQLModel):
    """Versão do /state: sem email, sem role, sem hash."""

    id: str
    name: str
    initials: str
    color: str

    @classmethod
    def of(cls, u: User) -> "UserMini":
        return cls(id=u.id, name=u.name, initials=u.name[:2].upper(), color=u.color)


class LoginIn(SQLModel):
    email: str
    password: str


class TokenOut(SQLModel):
    token: str
    user: UserPublic


# ----------------------------------------------------------------------- tasks


class TaskCreate(SQLModel):
    title: str
    desc: str = ""
    col: str = "ideias"
    category: str = ""
    priority: str = "media"
    assignee: str = "none"
    due: dt.date | None = None
    feedback: str = ""
    order: float | None = None  # ausente => max(order da coluna) + 1


class TaskUpdate(SQLModel):
    title: str | None = None
    desc: str | None = None
    col: str | None = None
    category: str | None = None
    priority: str | None = None
    assignee: str | None = None
    due: dt.date | None = None
    feedback: str | None = None
    order: float | None = None


class TaskOut(SQLModel):
    id: str
    title: str
    desc: str
    col: str
    category: str
    priority: str
    assignee: str
    due: dt.date | None
    feedback: str
    order: float

    @classmethod
    def of(cls, t: Task) -> "TaskOut":
        return cls(
            id=t.id,
            title=t.title,
            desc=t.description,
            col=t.stage,
            category=t.category,
            priority=t.priority,
            assignee=t.assignee,
            due=t.due,
            feedback=t.feedback,
            order=t.position,
        )


# ----------------------------------------------------------------------- goals


class GoalCreate(SQLModel):
    title: str
    current: int = 0
    target: int = 0
    color: str = ""


class GoalUpdate(SQLModel):
    title: str | None = None
    current: int | None = None
    target: int | None = None
    color: str | None = None


class GoalOut(SQLModel):
    id: str
    title: str
    current: int
    target: int
    color: str

    @classmethod
    def of(cls, g: Goal) -> "GoalOut":
        return cls(id=g.id, title=g.title, current=g.current, target=g.target, color=g.color)


# ------------------------------------------------------------------ milestones


class MilestoneCreate(SQLModel):
    title: str
    desc: str = ""
    date: dt.date | None = None
    status: str = "todo"


class MilestoneUpdate(SQLModel):
    title: str | None = None
    desc: str | None = None
    date: dt.date | None = None
    status: str | None = None


class MilestoneOut(SQLModel):
    id: str
    title: str
    desc: str
    date: dt.date | None
    status: str

    @classmethod
    def of(cls, m: Milestone) -> "MilestoneOut":
        return cls(id=m.id, title=m.title, desc=m.description, date=m.date, status=m.status)


# -------------------------------------------------------------------- features


class FeatureCreate(SQLModel):
    title: str
    desc: str = ""
    impact: int = 1
    effort: int = 1
    status: str = "ideia"


class FeatureUpdate(SQLModel):
    title: str | None = None
    desc: str | None = None
    impact: int | None = None
    effort: int | None = None
    status: str | None = None


class FeatureOut(SQLModel):
    id: str
    title: str
    desc: str
    impact: int
    effort: int
    status: str

    @classmethod
    def of(cls, f: Feature) -> "FeatureOut":
        return cls(
            id=f.id,
            title=f.title,
            desc=f.description,
            impact=f.impact,
            effort=f.effort,
            status=f.status,
        )


# -------------------------------------------------------------------- feedback


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


class FeedbackOut(SQLModel):
    id: str
    text: str
    source: str
    type: str
    author: str
    date: dt.date

    @classmethod
    def of(cls, f: Feedback) -> "FeedbackOut":
        return cls(
            id=f.id, text=f.text, source=f.source, type=f.type, author=f.author, date=f.date
        )


# ------------------------------------------------------------------- decisions


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


class DecisionOut(SQLModel):
    id: str
    title: str
    decision: str
    rationale: str
    date: dt.date
    status: str

    @classmethod
    def of(cls, d: Decision) -> "DecisionOut":
        return cls(
            id=d.id,
            title=d.title,
            decision=d.decision,
            rationale=d.rationale,
            date=d.date,
            status=d.status,
        )


# -------------------------------------------------------------------- settings


class SettingsUpdate(SQLModel):
    appName: str | None = None  # noqa: N815 - o contrato do front é camelCase
    launchDate: dt.date | None = None  # noqa: N815
    launchCity: str | None = None  # noqa: N815


class SettingsOut(SQLModel):
    appName: str  # noqa: N815
    launchDate: dt.date | None  # noqa: N815
    launchCity: str  # noqa: N815

    @classmethod
    def of(cls, s: AppSettings) -> "SettingsOut":
        return cls(appName=s.app_name, launchDate=s.launch_date, launchCity=s.launch_city)


# ----------------------------------------------------------------------- state


class StateOut(SQLModel):
    settings: SettingsOut
    tasks: list[TaskOut]
    goals: list[GoalOut]
    milestones: list[MilestoneOut]
    features: list[FeatureOut]
    feedback: list[FeedbackOut]
    decisions: list[DecisionOut]
    users: list[UserMini]
