from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.models import AppSettings
from app.routers.common import apply_patch, salvar
from app.schemas import SettingsOut, SettingsUpdate
from app.security import get_current_user

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(get_current_user)])

SETTINGS_ID = "1"


def carregar_ou_criar(session: Session) -> AppSettings:
    """O registro é único e fixo em id="1". Nasce na primeira leitura/escrita."""
    settings = session.get(AppSettings, SETTINGS_ID)
    if settings is None:
        settings = salvar(session, AppSettings(id=SETTINGS_ID))
    return settings


@router.put("", response_model=SettingsOut)
def atualizar(payload: SettingsUpdate, session: Session = Depends(get_session)) -> SettingsOut:
    settings = apply_patch(carregar_ou_criar(session), payload)
    return SettingsOut.of(salvar(session, settings))
