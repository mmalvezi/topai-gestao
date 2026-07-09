from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.db import get_session
from app.models import Feature
from app.routers.common import apply_patch, get_or_404, salvar, to_db
from app.schemas import FeatureCreate, FeatureOut, FeatureUpdate
from app.security import get_current_user

router = APIRouter(prefix="/features", tags=["features"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=FeatureOut, status_code=status.HTTP_201_CREATED)
def criar(payload: FeatureCreate, session: Session = Depends(get_session)) -> FeatureOut:
    return FeatureOut.of(salvar(session, Feature(**to_db(payload.model_dump()))))


@router.patch("/{feat_id}", response_model=FeatureOut)
def atualizar(
    feat_id: str, payload: FeatureUpdate, session: Session = Depends(get_session)
) -> FeatureOut:
    feat = apply_patch(get_or_404(session, Feature, feat_id), payload)
    return FeatureOut.of(salvar(session, feat))


@router.delete("/{feat_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(feat_id: str, session: Session = Depends(get_session)) -> None:
    session.delete(get_or_404(session, Feature, feat_id))
    session.commit()
