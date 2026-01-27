from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Define o payload para autenticacao de usuario."""

    email: EmailStr
    senha: str = Field(min_length=6)


class TokenResponse(BaseModel):
    """Define o retorno do login com token JWT."""

    access_token: str
    token_type: str
    must_change_password: bool


class ChangePasswordRequest(BaseModel):
    """Define o payload de troca de senha obrigatoria."""

    senha_atual: str = Field(min_length=6)
    nova_senha: str = Field(min_length=6)


class MessageResponse(BaseModel):
    """Resposta generica com mensagem textual."""

    mensagem: str
