from app.core.config import get_settings
from sqlmodel import Session

from app.core.database import engine
from app.core.security import hash_password
from app.models.user_model import User
from app.repositories.user_repository import UserRepository


def seed_user() -> User:
    """Cria um usuario inicial caso nao exista no banco."""
    settings = get_settings()
    email = settings.seed_email
    password = settings.seed_password

    with Session(engine) as session:
        repository = UserRepository(session)
        existing = repository.get_by_email(email)
        if existing:
            return existing
        user = User(
            email_institucional=email,
            password_hash=hash_password(password),
            must_change_password=True,
        )
        return repository.create(user)


def main() -> None:
    """Executa o seed do usuario inicial."""
    seed_user()


if __name__ == "__main__":
    main()

