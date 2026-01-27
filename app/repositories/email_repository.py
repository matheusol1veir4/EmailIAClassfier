from typing import List, Optional

from sqlmodel import Session, select

from app.models.email_model import Email


class EmailRepository:
    """Gerencia operacoes de persistencia relacionadas a emails."""

    def __init__(self, session: Session) -> None:
        """Inicializa o repositorio com uma sessao ativa do banco."""
        self._session = session

    def get_by_id(self, email_id: int) -> Optional[Email]:
        """Busca um email pelo identificador unico."""
        return self._session.get(Email, email_id)

    def list_by_user(self, user_id: int, respondido: Optional[bool] = None) -> List[Email]:
        """Lista emails de um usuario com filtro opcional por status de resposta."""
        statement = select(Email).where(Email.user_id == user_id)
        if respondido is not None:
            statement = statement.where(Email.respondido == respondido)
        return list(self._session.exec(statement).all())

    def create(self, email: Email) -> Email:
        """Persiste um novo email e retorna a entidade atualizada."""
        self._session.add(email)
        self._session.commit()
        self._session.refresh(email)
        return email

    def update(self, email: Email) -> Email:
        """Atualiza um email existente e retorna a entidade persistida."""
        self._session.add(email)
        self._session.commit()
        self._session.refresh(email)
        return email
