from typing import Optional

from sqlmodel import Session, select

from app.models.user_model import User


class UserRepository:
    """Gerencia operacoes de persistencia relacionadas a usuarios."""

    def __init__(self, session: Session) -> None:
        """Inicializa o repositorio com uma sessao ativa do banco."""
        self._session = session

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Busca um usuario pelo identificador unico."""
        return self._session.get(User, user_id)

    def get_by_email(self, email_institucional: str) -> Optional[User]:
        """Busca um usuario pelo email institucional."""
        statement = select(User).where(User.email_institucional == email_institucional)
        return self._session.exec(statement).first()

    def create(self, user: User) -> User:
        """Persiste um novo usuario e retorna a entidade atualizada."""
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user

    def update(self, user: User) -> User:
        """Atualiza um usuario existente e retorna a entidade persistida."""
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user
