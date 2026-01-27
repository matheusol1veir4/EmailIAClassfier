# Email AI Classifier

Aplicacao web para classificar emails como Produtivo ou Improdutivo e sugerir respostas automaticas.

## Requisitos
- Python 3.11+
- Docker e Docker Compose

## Como rodar localmente

### Ambiente
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Servicos
```bash
docker compose up -d postgres
```

### Aplicacao
```bash
uvicorn app.main:app --reload
```

Acesse http://localhost:8000

## Variaveis de ambiente
Veja `.env.example`.
