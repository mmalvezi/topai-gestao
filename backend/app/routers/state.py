"""GET /api/state — o estado inteiro numa tacada.

É o que o front chama no lugar do `localStorage`, tanto na carga inicial quanto no
polling de sincronização. A ordenação é estável para o polling não embaralhar a tela:
tasks por (col, order), o resto por `created_at` ascendente.
"""

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import Decision, Feature, Feedback, Goal, Milestone, Task, User
from app.routers.settings import carregar_ou_criar
from app.schemas import (
    DecisionOut,
    FeatureOut,
    FeedbackOut,
    GoalOut,
    MilestoneOut,
    SettingsOut,
    StateOut,
    TaskOut,
    UserMini,
)
from app.security import get_current_user

router = APIRouter(prefix="/state", tags=["state"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=StateOut)
def estado(session: Session = Depends(get_session)) -> StateOut:
    tasks = session.exec(select(Task).order_by(Task.stage, Task.position)).all()
    goals = session.exec(select(Goal).order_by(Goal.created_at)).all()
    milestones = session.exec(select(Milestone).order_by(Milestone.created_at)).all()
    features = session.exec(select(Feature).order_by(Feature.created_at)).all()
    feedback = session.exec(select(Feedback).order_by(Feedback.created_at)).all()
    decisions = session.exec(select(Decision).order_by(Decision.created_at)).all()
    users = session.exec(select(User).where(User.active).order_by(User.created_at)).all()

    return StateOut(
        settings=SettingsOut.of(carregar_ou_criar(session)),
        tasks=[TaskOut.of(t) for t in tasks],
        goals=[GoalOut.of(g) for g in goals],
        milestones=[MilestoneOut.of(m) for m in milestones],
        features=[FeatureOut.of(f) for f in features],
        feedback=[FeedbackOut.of(f) for f in feedback],
        decisions=[DecisionOut.of(d) for d in decisions],
        users=[UserMini.of(u) for u in users],
    )
