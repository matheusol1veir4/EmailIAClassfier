const state = {
    token: null,
    lastAnalysis: null,
    lastResponse: null,
    lastEmailBody: null,
    lastFileUsed: false,
    history: [],
};

function setActiveTab() {
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-tab').forEach((tab) => {
        tab.classList.remove('active');
        if (tab.getAttribute('href') === currentPath) {
            tab.classList.add('active');
        }
    });
}

function showToast(message, color = '#2e7d32') {
    const toast = document.getElementById('toast');
    if (!toast) {
        return;
    }
    toast.textContent = message;
    toast.style.background = color;
    toast.style.display = 'block';
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

function setLoadingState() {
    const resultSection = document.getElementById('resultSection');
    if (!resultSection) {
        return;
    }
    resultSection.innerHTML = `
        <div class="loading-state">
            <span class="spinner"></span>
            Analisando email...
        </div>
    `;
}

function setEmptyResult() {
    const resultSection = document.getElementById('resultSection');
    if (!resultSection) {
        return;
    }
    resultSection.innerHTML = `
        <div class="result-empty">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
            </svg>
            <p><strong>Nenhum email analisado ainda</strong></p>
            <p class="muted">Insira um email a esquerda para comecar</p>
        </div>
    `;
}

function getAuthHeaders() {
    if (!state.token) {
        return { 'Content-Type': 'application/json' };
    }
    return {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${state.token}`,
    };
}

async function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('loginEmail')?.value.trim();
    const senha = document.getElementById('loginPassword')?.value.trim();

    if (!email || !senha) {
        showToast('Informe email e senha', '#ff9800');
        return;
    }

    const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, senha }),
    });

    if (!response.ok) {
        showToast('Credenciais invalidas', '#ff9800');
        return;
    }

    const data = await response.json();
    state.token = data.access_token;
    showToast('Login realizado');
    window.location.href = '/';
}

function configureLoginForm() {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
}

function setupInputTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const fileInput = document.getElementById('fileInput');
    const fileUploadArea = document.getElementById('fileUploadArea');

    tabButtons.forEach((button) => {
        button.addEventListener('click', () => {
            tabButtons.forEach((btn) => btn.classList.remove('active'));
            button.classList.add('active');
            document.querySelectorAll('.tab-content').forEach((tab) => tab.classList.remove('active'));
            const targetId = button.getAttribute('data-tab');
            if (targetId) {
                document.getElementById(targetId)?.classList.add('active');
            }
        });
    });

    if (fileUploadArea && fileInput) {
        fileUploadArea.addEventListener('click', () => fileInput.click());
    }
}

async function processEmail() {
    const emailText = document.getElementById('emailText')?.value.trim();
    const emailDestinario = document.getElementById('emailDestinario')?.value.trim();
    const emailSubject = document.getElementById('emailSubject')?.value.trim();
    const fileInput = document.getElementById('fileInput');
    const file = fileInput?.files?.[0];

    if (!emailText && !file) {
        showToast('Informe um texto ou arquivo', '#ff9800');
        return;
    }

    if (!emailDestinario) {
        showToast('Informe o email do destinatario', '#ff9800');
        return;
    }

    setLoadingState();

    const formData = new FormData();
    formData.append('email_destinatario', emailDestinario);
    if (emailSubject) {
        formData.append('assunto', emailSubject);
    }
    if (file) {
        formData.append('arquivo', file);
    } else {
        formData.append('email_body', emailText || '');
    }

    const response = await fetch('/api/v1/emails/classify', {
        method: 'POST',
        headers: state.token ? { Authorization: `Bearer ${state.token}` } : undefined,
        body: formData,
    });

    if (!response.ok) {
        setEmptyResult();
        showToast('Erro ao processar email', '#ff9800');
        return;
    }

    const data = await response.json();
    state.lastAnalysis = {
        id: data.id,
        classification: data.classification,
        email_destinatario: data.email_destinatario,
        assunto: emailSubject || '(sem assunto)',
    };
    state.lastResponse = data.generated_response;
    state.lastEmailBody = file ? null : emailText || '';
    state.lastFileUsed = Boolean(file);
    renderResult(data.classification, data.generated_response);
    showToast('Email analisado');
}

function renderResult(classification, responseText) {
    const resultSection = document.getElementById('resultSection');
    if (!resultSection) {
        return;
    }
    const badgeClass = classification === 'Produtivo' ? 'badge-productive' : 'badge-unproductive';
    const badgeText = classification === 'Produtivo' ? 'Produtivo' : 'Improdutivo';
    resultSection.innerHTML = `
        <div>
            <span class="classification-badge ${badgeClass}">${badgeText}</span>
        </div>
        <div class="result-block">
            <div class="result-block-title">Resumo da Analise</div>
            <div class="result-text">${classification}</div>
        </div>
        <div class="result-block">
            <div class="result-block-title">Resposta Sugerida</div>
            <div class="result-text" id="suggestedResponse">${responseText}</div>
            <div class="response-actions">
                <button class="btn-secondary" id="copyResponse">Copiar Resposta</button>
                <button class="btn-secondary" id="regenerateResponse">Regenerar</button>
                <button class="btn-success" id="markResponded">Marcar como Respondido</button>
            </div>
        </div>
    `;

    document.getElementById('copyResponse')?.addEventListener('click', copyResponse);
    document.getElementById('regenerateResponse')?.addEventListener('click', regenerateResponse);
    document.getElementById('markResponded')?.addEventListener('click', markResponded);
}

function copyResponse() {
    if (!state.lastResponse) {
        return;
    }
    navigator.clipboard.writeText(state.lastResponse).then(() => {
        showToast('Resposta copiada');
    });
}

async function regenerateResponse() {
    if (!state.lastAnalysis) {
        return;
    }
    if (state.lastFileUsed) {
        showToast('Regeneracao indisponivel para arquivos', '#ff9800');
        return;
    }
    if (!state.lastEmailBody) {
        showToast('Nao ha conteudo para regenerar', '#ff9800');
        return;
    }
    showToast('Gerando nova resposta', '#0066cc');
    const formData = new FormData();
    formData.append('email_destinatario', state.lastAnalysis.email_destinatario);
    formData.append('assunto', state.lastAnalysis.assunto);
    formData.append('email_body', state.lastEmailBody);

    const response = await fetch('/api/v1/emails/classify', {
        method: 'POST',
        headers: state.token ? { Authorization: `Bearer ${state.token}` } : undefined,
        body: formData,
    });

    if (!response.ok) {
        showToast('Nao foi possivel regenerar', '#ff9800');
        return;
    }

    const data = await response.json();
    state.lastResponse = data.generated_response;
    const responseElement = document.getElementById('suggestedResponse');
    if (responseElement) {
        responseElement.textContent = state.lastResponse;
    }
    showToast('Resposta atualizada');
}

async function markResponded() {
    if (!state.lastAnalysis) {
        return;
    }
    const response = await fetch(`/api/v1/emails/${state.lastAnalysis.id}/mark-responded`, {
        method: 'POST',
        headers: state.token ? { Authorization: `Bearer ${state.token}` } : undefined,
    });

    if (!response.ok) {
        showToast('Nao foi possivel marcar como respondido', '#ff9800');
        return;
    }

    setEmptyResult();
    showToast('Email marcado como respondido');
}

async function fetchHistory() {
    const response = await fetch('/api/v1/emails/history', {
        headers: state.token ? { Authorization: `Bearer ${state.token}` } : undefined,
    });

    if (!response.ok) {
        return;
    }

    const data = await response.json();
    state.history = data.emails || [];
    renderHistory(state.history);
    updateHistoryTotal(data.total);
}

function updateHistoryTotal(total) {
    const totalElement = document.getElementById('historyTotal');
    if (!totalElement) {
        return;
    }
    const safeTotal = Number.isFinite(total) ? total : 0;
    totalElement.textContent = `Total: ${safeTotal}`;
}

function renderHistory(items) {
    const historyBody = document.getElementById('historyBody');
    if (!historyBody) {
        return;
    }

    if (!items || items.length === 0) {
        historyBody.innerHTML = '<tr><td colspan="5" class="history-empty">Nenhum email respondido ainda</td></tr>';
        return;
    }

    historyBody.innerHTML = items
        .map((email, index) => {
            const badgeClass = email.classification === 'Produtivo' ? 'badge-productive' : 'badge-unproductive';
            return `
                <tr>
                    <td>${email.respondido_em || email.created_at}</td>
                    <td>${email.email_destinatario}</td>
                    <td>${email.assunto || '(sem assunto)'}</td>
                    <td><span class="classification-badge ${badgeClass}">${email.classification}</span></td>
                    <td><button class="btn-secondary" data-index="${index}">Ver Detalhes</button></td>
                </tr>
            `;
        })
        .join('');

    historyBody.querySelectorAll('button[data-index]').forEach((button) => {
        button.addEventListener('click', () => {
            const index = Number(button.getAttribute('data-index'));
            openDetailModal(state.history[index]);
        });
    });
}

async function openDetailModal(email) {
    const modal = document.getElementById('detailModal');
    const detailContent = document.getElementById('detailContent');
    if (!modal || !detailContent || !email) {
        return;
    }
    const response = await fetch(`/api/v1/emails/${email.id}`, {
        headers: state.token ? { Authorization: `Bearer ${state.token}` } : undefined,
    });
    if (!response.ok) {
        showToast('Nao foi possivel carregar detalhes', '#ff9800');
        return;
    }
    const detail = await response.json();
    detailContent.innerHTML = `
        <div><strong>Destinatario:</strong> ${detail.email_destinatario}</div>
        <div><strong>Assunto:</strong> ${detail.assunto || '(sem assunto)'}</div>
        <div><strong>Classificacao:</strong> ${detail.classification}</div>
        <div><strong>Resposta:</strong> ${detail.generated_response}</div>
    `;
    modal.style.display = 'flex';
}

function closeDetailModal() {
    const modal = document.getElementById('detailModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function setupDetailModal() {
    const closeButton = document.getElementById('closeModal');
    if (closeButton) {
        closeButton.addEventListener('click', closeDetailModal);
    }
}

function setupActions() {
    document.getElementById('submitButton')?.addEventListener('click', processEmail);
    document.getElementById('logoutButton')?.addEventListener('click', () => {
        state.token = null;
        window.location.href = '/login';
    });
}

function init() {
    setActiveTab();
    configureLoginForm();
    setupInputTabs();
    setupActions();
    setupDetailModal();

    if (document.getElementById('historyBody')) {
        fetchHistory();
    }
}

document.addEventListener('DOMContentLoaded', init);
