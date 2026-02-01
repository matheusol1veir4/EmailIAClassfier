from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="app/web/templates")
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    """Redireciona para a pagina de login."""
    _ = request
    return RedirectResponse(url="/login", status_code=302)


@router.get("/app", response_class=HTMLResponse)
def app_home(request: Request) -> HTMLResponse:
    """Renderiza a pagina principal de processamento de emails."""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
    """Renderiza a pagina de login."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/history", response_class=HTMLResponse)
def history_page(request: Request) -> HTMLResponse:
    """Renderiza a pagina de historico de emails."""
    return templates.TemplateResponse("history.html", {"request": request})

