"""Hash de senha, JWT e a dependency que protege as rotas.

bcrypt é usado direto, sem passlib (seção 8 do PLAN): a dupla passlib+bcrypt já
nos custou um erro de `__about__` no EPR Gestão.

`dt.datetime` qualificado pelo mesmo motivo de models.py/schemas.py.
"""

import datetime as dt

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from app.config import settings
from app.db import get_session
from app.models import User

ALGORITHM = "HS256"

# auto_error=False para devolvermos 401 quando falta o header;
# o padrão do HTTPBearer devolveria 403.
bearer_scheme = HTTPBearer(auto_error=False)

CREDENCIAIS_INVALIDAS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Não autenticado.",
    headers={"WWW-Authenticate": "Bearer"},
)


def hash_senha(p: str) -> str:
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()


def confere_senha(p: str, h: str) -> bool:
    return bcrypt.checkpw(p.encode(), h.encode())


def criar_token(user_id: str) -> str:
    expira = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=settings.jwt_expire_days)
    return jwt.encode({"sub": user_id, "exp": expira}, settings.jwt_secret, algorithm=ALGORITHM)


def decodificar_token(token: str) -> str:
    """Devolve o `sub` (id do usuário) ou levanta 401."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise CREDENCIAIS_INVALIDAS from None

    user_id = payload.get("sub")
    if not user_id:
        raise CREDENCIAIS_INVALIDAS
    return user_id


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    if credentials is None:
        raise CREDENCIAIS_INVALIDAS

    user_id = decodificar_token(credentials.credentials)
    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None or not user.active:
        raise CREDENCIAIS_INVALIDAS
    return user
