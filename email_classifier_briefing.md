# Email AI Classifier - Documentação Completa do Projeto

## 📋 Visão Geral do Projeto

Este é um sistema web para **classificação automática de emails** utilizando inteligência artificial. A solução automatiza a leitura, classificação e geração de respostas para emails, liberando tempo da equipe para tarefas mais estratégicas.

**Contexto:** Grande empresa do setor financeiro que recebe alto volume de emails diários que precisam ser classificados e respondidos.

---

## 🎯 Objetivo Simplificado

Desenvolver uma aplicação web que utilize inteligência artificial para:
1. **Classificar emails** em categorias predefinidas (Produtivo / Improdutivo)
2. **Sugerir respostas automáticas** baseadas na classificação realizada
3. **Manter histórico** de emails processados e respondidos com dados de auditoria completos

---

## 📊 Categorias de Classificação

- **Produtivo**: Emails que requerem ação específica
  - Solicitações de suporte técnico
  - Atualização sobre casos em aberto
  - Dúvidas sobre o sistema
  
- **Improdutivo**: Emails que não necessitam ação imediata
  - Mensagens de felicitações
  - Agradecimentos
  - Atualizações informativas

---

## 💻 Stack Tecnológico

### Backend
- **Framework**: FastAPI (Python)
- **Banco de Dados**: PostgreSQL
- **ORM**: SQLAlchemy com SQLModel
- **Autenticação**: JWT (JSON Web Tokens)
- **NLP**: Hugging Face Transformers (classificação zero-shot)
- **LLM**: API gratuita para geração de respostas (a definir: GitHub Models, OpenRouter ou similar)
- **Hash de Senha**: bcrypt
- **Extração de PDF**: pdfplumber ou PyPDF2

### Frontend
- **HTML5** com Jinja2 templates
- **CSS3** com design system próprio
- **JavaScript** vanilla (sem dependências pesadas)
- **Abordagem**: Single Page App com fetch API

### DevOps
- **Containerização**: Docker
- **Orquestração**: Docker Compose
- **Hospedagem**: Render, Hugging Face Spaces, Heroku ou similar (gratuito)

---

## 🏗️ Arquitetura em Camadas (Clean Architecture)

```
app/
├── api/                    # Controllers (rotas FastAPI)
│   ├── v1/
│   │   ├── auth_router.py
│   │   ├── email_router.py
│   │   └── health_router.py
│   └── __init__.py
│
├── core/                   # Infra e configs centrais
│   ├── config.py          # Settings (.env, URLs, secrets)
│   ├── security.py        # Hash de senha, JWT, etc.
│   ├── database.py        # Sessão SQLAlchemy com Postgres
│   └── __init__.py
│
├── models/                # Modelos de banco (ORM)
│   ├── user_model.py
│   ├── email_model.py
│   └── __init__.py
│
├── schemas/               # Pydantic (entrada/saída da API)
│   ├── auth_schema.py
│   ├── user_schema.py
│   ├── email_schema.py
│   └── __init__.py
│
├── repositories/          # Regras de acesso a dados
│   ├── user_repository.py
│   ├── email_repository.py
│   └── __init__.py
│
├── services/              # Regras de negócio
│   ├── auth_service.py
│   ├── email_service.py   # orquestra NLP/LLM + repos
│   └── __init__.py
│
├── nlp/                   # Integração com modelos / LLM
│   ├── classifier_client.py   # zero-shot Prod/Improd
│   ├── llm_client.py          # geração de resposta
│   └── __init__.py
│
├── web/                   # Front-end estático
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/
│   │   │   └── main.js
│   │   └── img/
│   └── templates/
│       ├── base.html
│       ├── index.html     # dashboard
│       ├── login.html
│       └── history.html
│
├── main.py                # cria FastAPI, inclui rotas, monta templates
└── __init__.py

tests/
├── test_auth.py
├── test_email_flow.py
└── __init__.py

requirements.txt
.env.example
.gitignore
Dockerfile
docker-compose.yml
README.md
```

---

## 📁 Modelo de Dados (Banco Postgres)

### Tabela: `users`
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email_institucional VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    must_change_password BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Tabela: `emails`
```sql
CREATE TABLE emails (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    email_destinatario VARCHAR(255) NOT NULL,
    assunto VARCHAR(255),
    raw_body TEXT NOT NULL,
    classification VARCHAR(50) NOT NULL,  -- 'Produtivo' ou 'Improdutivo'
    generated_response TEXT NOT NULL,
    respondido BOOLEAN DEFAULT false,
    respondido_em TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Tabela: `audit_logs` (opcional, para rastreamento detalhado)
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    email_id INTEGER,
    acao VARCHAR(100),  -- ex: 'LOGIN', 'EMAIL_PROCESSADO', 'RESPOSTA_MARCADA'
    detalhes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (email_id) REFERENCES emails(id)
);
```

---

## 🔐 Autenticação e Autorização

### Fluxo de Autenticação

1. **Login** (`POST /auth/login`)
   - Email + Senha
   - Retorna JWT + flag `must_change_password`

2. **Troca de Senha Obrigatória** (`POST /auth/change-password`)
   - Protegido com JWT
   - Senha atual + Nova senha
   - Seta `must_change_password = false`

3. **Uso da API**
   - Header: `Authorization: Bearer <token>`
   - Token decodificado extrai email do usuário
   - Rotas `/emails/*` validam token automaticamente

### Implementação em `core/security.py`
```python
- hash_password(password: str) -> str
- verify_password(password: str, hash: str) -> bool
- create_access_token(data: dict, expires_delta: timedelta) -> str
- decode_token(token: str) -> dict
```

---

## 🤖 Processamento de IA

### 1. Classificação (Zero-Shot)

**Modelo:** `facebook/bart-large-mnli` (Hugging Face Transformers)

**Fluxo:**
- Entrada: texto do email
- Processamento: modelo zero-shot recebe texto + labels ["Produtivo", "Improdutivo"]
- Saída: rótulo com maior score

**Implementação em `nlp/classifier_client.py`:**
```python
- classify_email(text: str) -> {"label": str, "score": float}
```

### 2. Geração de Resposta (LLM)

**API:** (Escolher dentre opções gratuitas)
- **GitHub Models** (com acesso via token GitHub)
- **Hugging Face Inference API** (free tier com limites)
- **OpenRouter** (alguns modelos open-source gratuitos)

**Fluxo:**
- Entrada: classificação + contexto do email
- Processamento: LLM recebe prompt estruturado
- Saída: resposta sugerida

**Implementação em `nlp/llm_client.py`:**
```python
- generate_response(classification: str, email_body: str) -> str
```

### 3. Orquestração em `services/email_service.py`

```python
async def process_email(
    user_id: int,
    email_body: str,
    email_destinatario: str,
    assunto: str = None
) -> EmailResponse:
    # 1. Extrair texto (se PDF)
    text = await extract_text_from_pdf_or_txt(file)
    
    # 2. Pré-processar (limpeza, normalização)
    text = preprocess_text(text)
    
    # 3. Classificar
    classification = classifier.classify_email(text)
    
    # 4. Gerar resposta
    response = llm.generate_response(classification, text)
    
    # 5. Salvar no banco
    email_obj = Email(
        user_id=user_id,
        email_destinatario=email_destinatario,
        assunto=assunto,
        raw_body=text,
        classification=classification,
        generated_response=response
    )
    await email_repository.save(email_obj)
    
    # 6. Log de auditoria
    await audit_log_repository.log("EMAIL_PROCESSADO", email_obj.id)
    
    return EmailResponse(
        classification=classification,
        generated_response=response
    )
```

---

## 🎨 Interface Web

### Páginas Principais

#### 1. Login (`/login`)
- Campo: email institucional
- Campo: senha
- Checkbox: lembrar-me
- Link: "Primeiro acesso ou esqueceu a senha?"
- Feedback visual de erros

#### 2. Troca de Senha (primeiro acesso) (`/change-password`)
- Título: "Defina sua nova senha"
- Campo: nova senha
- Campo: confirmar nova senha
- Indicador de força da senha
- Botão: "Salvar nova senha"

#### 3. Dashboard Principal (`/`)
Duas abas:

**Aba 1: Processar Emails**
- **Coluna Esquerda (Input):**
  - Abas: "Texto" / "Arquivo"
  - Textarea: conteúdo do email
  - Input: email do destinatário (obrigatório)
  - Input: assunto do email (opcional)
  - Botão: "Classificar e Sugerir Resposta"

- **Coluna Direita (Resultado):**
  - Badge: classificação (verde = produtivo, laranja = improdutivo)
  - Bloco: resumo da análise
  - Bloco: resposta sugerida
  - Botões: "Copiar Resposta", "Regenerar", "Marcar como Respondido" (verde)

**Aba 2: Emails Respondidos**
- Tabela com colunas:
  - Data/Hora
  - Destinatário
  - Assunto
  - Classificação
  - Ação: "Ver Detalhes"

- Modal "Ver Detalhes":
  - Corpo original do email
  - Classificação
  - Resposta usada
  - Dados de auditoria (quem, quando)

### Design System

**Cores:**
- Primária: `#0066cc` (azul)
- Produtivo: `#2e7d32` (verde)
- Improdutivo: `#e65100` (laranja)
- Background: `#f5f7fa` (cinza claro)
- Surface: `#ffffff` (branco)

**Tipografia:**
- Font-family: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- Responsive: mobile-first com media queries

**Componentes:**
- Cards com sombra discreta
- Botões com transição
- Toasts de notificação
- Loading spinners
- Badges coloridas

---

## 🚀 Endpoints da API

### Autenticação

```
POST /api/v1/auth/login
{
  "email": "usuario@empresa.com",
  "senha": "senha123"
}
Response:
{
  "access_token": "eyJh...",
  "token_type": "bearer",
  "must_change_password": true
}

POST /api/v1/auth/change-password
Headers: Authorization: Bearer <token>
{
  "senha_atual": "senha123",
  "nova_senha": "novaSenha456"
}
Response:
{
  "mensagem": "Senha alterada com sucesso"
}

GET /api/v1/auth/me
Headers: Authorization: Bearer <token>
Response:
{
  "id": 1,
  "email": "usuario@empresa.com",
  "must_change_password": false
}
```

### Processamento de Emails

```
POST /api/v1/emails/classify
Headers: Authorization: Bearer <token>
{
  "email_body": "Texto do email...",
  "email_destinatario": "cliente@empresa.com",
  "assunto": "Solicitação de suporte",
  "arquivo": <optional File>
}
Response:
{
  "id": 1,
  "classification": "Produtivo",
  "generated_response": "Obrigado por sua solicitação...",
  "email_destinatario": "cliente@empresa.com"
}

POST /api/v1/emails/:id/mark-responded
Headers: Authorization: Bearer <token>
Response:
{
  "mensagem": "Email marcado como respondido",
  "respondido_em": "2026-01-27T12:30:00"
}

GET /api/v1/emails/history
Headers: Authorization: Bearer <token>
Query params: ?respondido=true
Response:
{
  "emails": [
    {
      "id": 1,
      "email_destinatario": "cliente@empresa.com",
      "assunto": "Solicitação de suporte",
      "classification": "Produtivo",
      "respondido": true,
      "respondido_em": "2026-01-27T12:30:00",
      "created_at": "2026-01-27T12:00:00"
    }
  ],
  "total": 10
}

GET /api/v1/emails/:id
Headers: Authorization: Bearer <token>
Response:
{
  "id": 1,
  "email_body": "Texto original...",
  "email_destinatario": "cliente@empresa.com",
  "assunto": "Solicitação de suporte",
  "classification": "Produtivo",
  "generated_response": "Resposta sugerida...",
  "respondido": true,
  "respondido_em": "2026-01-27T12:30:00",
  "created_at": "2026-01-27T12:00:00"
}
```

---

## 📦 Requirements.txt

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
sqlmodel==0.0.14
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
bcrypt==4.1.1
python-jose[cryptography]==3.3.0
PyJWT==2.8.1
transformers==4.35.2
torch==2.1.1
pdfplumber==0.10.3
requests==2.31.0
python-multipart==0.0.6
aiofiles==23.2.1
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.12.0
flake8==6.1.0
```

---

## 🐳 Docker & Compose

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  fastapi:
    build: .
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      SECRET_KEY: ${SECRET_KEY}
      ALGORITHM: HS256
      ACCESS_TOKEN_EXPIRE_MINUTES: 60
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - .:/app

volumes:
  postgres_data:
```

### .env.example

```
# Database
DB_USER=postgres
DB_PASSWORD=sua_senha_aqui
DB_NAME=email_classifier
DATABASE_URL=postgresql://postgres:sua_senha_aqui@localhost:5432/email_classifier

# Security
SECRET_KEY=sua_chave_secreta_super_longa_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# NLP & LLM APIs
HUGGINGFACE_API_KEY=seu_token_aqui
# (adicionar conforme escolha de LLM)

# App
DEBUG=False
ENVIRONMENT=production
```

### Comando Docker (quando tiver os dados)

```bash
docker run --name email-classifier-db \
  -e POSTGRES_USER=SEU_USER \
  -e POSTGRES_PASSWORD=SUA_SENHA \
  -e POSTGRES_DB=SEU_DB \
  -p 5432:5432 \
  -v email-classifier-data:/var/lib/postgresql/data \
  -d postgres:16-alpine
```

---

## 📋 Requisitos do Projeto

### 1. Interface Web (HTML)
✅ Formulário de Upload: `.txt` / `.pdf` / texto direto
✅ Exibição de Resultados: categoria + resposta automática
✅ Design polido: cards, botões, feedback visual
✅ Responsivo: mobile-friendly

### 2. Backend em Python (FastAPI)
✅ Leitura de arquivos (PDF/TXT)
✅ NLP Preprocessing: remoção de stop words, normalização
✅ Classificação: zero-shot com Hugging Face
✅ Geração de Resposta: integração com LLM gratuito
✅ Camadas: Controller → Service → Repository
✅ Autenticação: JWT com troca de senha obrigatória

### 3. Banco de Dados (PostgreSQL)
✅ Tabela: users (email, password_hash, must_change_password)
✅ Tabela: emails (corpo, classe, resposta, auditoria)
✅ Tabela: audit_logs (quem fez o quê e quando)
✅ Relações e constraints

### 4. Hospedagem na Nuvem (Gratuita)
✅ Deploy em: Render / Hugging Face Spaces / Heroku / Replit
✅ Link funcional e acessível

---

## 📹 Entregáveis

### 1. Código Fonte
- Repositório GitHub público
- Estrutura bem organizada
- `requirements.txt`
- `README.md` com instruções locais
- Dados de exemplo (seed emails para teste)

### 2. Vídeo Demonstrativo (3-5 minutos)
- Introdução pessoal (30s)
- Demonstração: login → processar email → resposta → histórico (3 min)
- Explicação técnica: algoritmo, tecnologias, decisões (1 min)
- Conclusão: aprendizados (30s)

### 3. Link Deployado
- URL funcional sem instalação local
- Autenticação e fluxo completo testável

---

## ✅ Critérios de Avaliação

1. **Funcionalidade**: Classifica corretamente, respostas relevantes, UX fluida
2. **Qualidade Técnica**: Clean Code, SOLID, Clean Architecture
3. **Uso de AI**: Zero-shot classification + LLM efetivos
4. **Hospedagem**: URL ativa e funcional
5. **Interface**: Bonita, intuitiva, acessível
6. **Autonomia**: Resolveu problemas independentemente
7. **Comunicação**: Vídeo claro e conciso

---

## 🎯 Boas Práticas Não Negociáveis

- ✅ **Clean Code**: sem cheiros de código, nomes claros
- ✅ **SOLID**: responsabilidade única, interface segregada, etc.
- ✅ **Clean Architecture**: camadas bem definidas (controller/service/repository/model)
- ✅ **Sem try-catch aninhados**: trate erros de forma elegante
- ✅ **Sem duplicação**: DRY (Don't Repeat Yourself)
- ✅ **Tipos claros**: type hints em Python, schemas Pydantic
- ✅ **Testes unitários**: cobertura mínima nas regras de negócio
- ✅ **Documentação**: docstrings, README claro, comentários onde necessário

---

## 🛠️ Próximos Passos de Desenvolvimento

1. **Setup Inicial**
   - Criar repositório GitHub
   - Clonar localmente
   - Instalar dependências (venv + pip)
   - Configurar `.env`

2. **Banco de Dados**
   - Subir Postgres via Docker
   - Rodar migrações (Alembic)
   - Popular seed data

3. **Autenticação**
   - Implementar `core/security.py`
   - Criar `services/auth_service.py`
   - Rotas: login, change-password, me

4. **Modelos ORM**
   - User, Email, AuditLog em `models/`
   - Relationships SQLAlchemy
   - Constraints

5. **Repositories**
   - `user_repository.py`: buscar, criar, atualizar
   - `email_repository.py`: CRUD + filtros

6. **Services**
   - `auth_service.py`: lógica de login e troca senha
   - `email_service.py`: orquestra classificação + geração

7. **NLP Integration**
   - `classifier_client.py`: integra Hugging Face
   - `llm_client.py`: integra LLM (GitHub Models / HF / etc)

8. **Routers (Controllers)**
   - `auth_router.py`: POST /login, /change-password, GET /me
   - `email_router.py`: POST /classify, POST /:id/mark-responded, GET /history, GET /:id
   - `health_router.py`: GET /health (para monitoramento)

9. **Frontend**
   - Extrair HTML do protótipo
   - Integrar com fetch API real
   - Adaptar templates Jinja2

10. **Testes**
    - Tests de auth
    - Tests do fluxo email (classificação + resposta)
    - Tests do repository

11. **Deploy**
    - Dockerfile pronto
    - docker-compose pronto
    - Criar conta na plataforma (Render, HF Spaces, etc)
    - Configurar variáveis de ambiente
    - Deploy inicial
    - Testar link público

12. **Vídeo + Documentação Final**
    - Gravar demonstração
    - Fazer README detalhado
    - Upload para GitHub + YouTube

---

## 📞 Contato e Suporte

**Desenvolvedor:** Você (engenheiro de software apaixonado por sistemas)  
**Localização:** Brasília, DF  
**Stack:** Java, Python, React, Docker, PostgreSQL  

---

## 🚀 Visão Final

Um sistema **production-ready**, com:
- ✅ Autenticação robusta
- ✅ Classificação IA eficiente (zero-shot)
- ✅ Geração automática de respostas
- ✅ Auditoria completa
- ✅ UI/UX excelente
- ✅ Código limpo e manutenível
- ✅ Hospedado e funcional

**Objetivo:** Demonstrar excelência técnica, criatividade e capacidade de resolver problemas complexos de forma elegante, seguindo rigorosamente boas práticas de engenharia de software.

---

**Versão:** 1.0  
**Data:** 27 de janeiro de 2026  
**Status:** Pronto para início do desenvolvimento