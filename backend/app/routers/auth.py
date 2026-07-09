from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlmodel import Session, select

from app.db import get_session
from app.models import User
from app.schemas import LoginIn, TokenOut, UserPublic
from app.security import confere_senha, criar_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, session: Session = Depends(get_session)) -> TokenOut:
    email = payload.email.strip().lower()
    user = session.exec(select(User).where(func.lower(User.email) == email)).first()

    # Mensagem genérica de propósito: não revelar se o erro foi no email ou na senha.
    if user is None or not user.active or not confere_senha(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos.",
        )

    return TokenOut(token=criar_token(user.id), user=UserPublic.model_validate(user))


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)) -> User:
    return user
