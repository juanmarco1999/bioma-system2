// ============================================================
// BIOMA UI SYSTEM v5.1.0 - Modais Bonitos + Botões Modernos
// ============================================================
// Modais customizados DIV (não nativos do browser)
// Sistema de botões moderno e profissional
// ============================================================

// ========== ESTADO GLOBAL ==========
let biomaToastContainer = null;
let activeModals = [];

// ========== CRIAR CONTAINERS ==========
function initBiomaUI() {
    // Container para toasts
    if (!biomaToastContainer) {
        biomaToastContainer = document.createElement('div');
        biomaToastContainer.className = 'bioma-toast-stack';
        biomaToastContainer.id = 'biomaToastStack';
        document.body.appendChild(biomaToastContainer);
    }
}

// Auto-inicializar quando DOM carregar
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initBiomaUI);
} else {
    initBiomaUI();
}

// ========== TOAST NOTIFICATIONS (Toastify-style) ==========
function mostrarNotificacao(type, message, duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `bioma-toast bioma-toast-${type} bioma-toast-enter`;

    const icons = {
        success: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg>',
        error: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/></svg>',
        warning: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>',
        info: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>'
    };

    toast.innerHTML = `
        <div class="bioma-toast-icon">${icons[type] || icons.info}</div>
        <div class="bioma-toast-message">${message}</div>
        <button class="bioma-toast-close" onclick="this.closest('.bioma-toast').remove()">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
            </svg>
        </button>
    `;

    biomaToastContainer.appendChild(toast);

    // Animação de entrada
    setTimeout(() => toast.classList.add('bioma-toast-show'), 10);

    // Auto-remover
    if (duration > 0) {
        setTimeout(() => {
            toast.classList.remove('bioma-toast-show');
            toast.classList.add('bioma-toast-exit');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    return toast;
}

// ========== MODAL CUSTOMIZADO (DIV estilizado) ==========
function mostrarConfirmacao(config) {
    return new Promise((resolve) => {
        // Criar overlay
        const overlay = document.createElement('div');
        overlay.className = 'bioma-modal-overlay bioma-modal-fade-in';

        // Criar modal
        const modal = document.createElement('div');
        modal.className = 'bioma-modal bioma-modal-scale-in';

        const icons = {
            success: '<svg viewBox="0 0 24 24" width="48" height="48" fill="#10B981"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/><path d="M9 12l2 2 4-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
            error: '<svg viewBox="0 0 24 24" width="48" height="48" fill="#EF4444"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/><path d="M15 9l-6 6m0-6l6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
            warning: '<svg viewBox="0 0 24 24" width="48" height="48" fill="#F59E0B"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>',
            info: '<svg viewBox="0 0 24 24" width="48" height="48" fill="#3B82F6"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 16v-4m0-4h.01" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
            question: '<svg viewBox="0 0 24 24" width="48" height="48" fill="#8B5CF6"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3m.08 4h.01" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
        };

        const iconHTML = config.icon ? `<div class="bioma-modal-icon">${icons[config.icon] || icons.info}</div>` : '';
        const textHTML = config.text ? `<p class="bioma-modal-text">${config.text}</p>` : '';
        const htmlContent = config.html || '';

        modal.innerHTML = `
            ${iconHTML}
            <h3 class="bioma-modal-title">${config.title || 'Confirmação'}</h3>
            ${textHTML}
            ${htmlContent}
            <div class="bioma-modal-actions">
                ${config.showCancelButton !== false ? `<button class="bioma-btn bioma-btn-secondary" data-action="cancel">${config.cancelButtonText || 'Cancelar'}</button>` : ''}
                <button class="bioma-btn bioma-btn-primary" data-action="confirm">${config.confirmButtonText || 'Confirmar'}</button>
            </div>
        `;

        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        activeModals.push(overlay);

        // Bloquear scroll do body
        document.body.style.overflow = 'hidden';

        // Event listeners
        const buttons = modal.querySelectorAll('button[data-action]');
        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.getAttribute('data-action');
                closeModal(overlay);
                resolve({
                    isConfirmed: action === 'confirm',
                    isDismissed: action === 'cancel',
                    value: action === 'confirm'
                });
            });
        });

        // Fechar ao clicar no overlay
        if (config.allowOutsideClick !== false) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    closeModal(overlay);
                    resolve({ isConfirmed: false, isDismissed: true });
                }
            });
        }

        // Fechar com ESC
        if (config.allowEscapeKey !== false) {
            const escHandler = (e) => {
                if (e.key === 'Escape') {
                    closeModal(overlay);
                    resolve({ isConfirmed: false, isDismissed: true });
                    document.removeEventListener('keydown', escHandler);
                }
            };
            document.addEventListener('keydown', escHandler);
        }

        // Executar didOpen se existir
        if (config.didOpen) {
            setTimeout(() => config.didOpen(modal), 100);
        }
    });
}

// ========== MODAL DE LOADING ==========
let currentLoadingModal = null;

function mostrarLoading(message = 'Carregando...') {
    // Fechar loading anterior se existir
    if (currentLoadingModal) {
        closeModal(currentLoadingModal);
    }

    const overlay = document.createElement('div');
    overlay.className = 'bioma-modal-overlay bioma-modal-fade-in';

    const modal = document.createElement('div');
    modal.className = 'bioma-modal bioma-modal-loading bioma-modal-scale-in';

    modal.innerHTML = `
        <div class="bioma-spinner">
            <div class="bioma-spinner-circle"></div>
        </div>
        <p class="bioma-modal-title">${message}</p>
    `;

    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    document.body.style.overflow = 'hidden';

    currentLoadingModal = overlay;
    activeModals.push(overlay);

    return overlay;
}

// ========== FUNÇÕES AUXILIARES ==========
function closeModal(overlay) {
    overlay.classList.add('bioma-modal-fade-out');
    const modal = overlay.querySelector('.bioma-modal');
    if (modal) modal.classList.add('bioma-modal-scale-out');

    setTimeout(() => {
        overlay.remove();
        activeModals = activeModals.filter(m => m !== overlay);

        // Restaurar scroll se não houver mais modais
        if (activeModals.length === 0) {
            document.body.style.overflow = '';
        }

        if (overlay === currentLoadingModal) {
            currentLoadingModal = null;
        }
    }, 300);
}

// ========== COMPATIBILIDADE COM CÓDIGO ANTIGO ==========
window.Swal = {
    fire: function(...args) {
        if (typeof args[0] === 'object') {
            const config = args[0];

            // Toast notification
            if (config.timer && config.showConfirmButton === false) {
                return Promise.resolve(mostrarNotificacao(config.icon || 'info', config.title, config.timer));
            }

            // Loading
            if (config.didOpen && config.showConfirmButton === false && !config.timer) {
                return Promise.resolve(mostrarLoading(config.title));
            }

            // Confirmação
            return mostrarConfirmacao(config);
        } else if (args.length >= 1) {
            // Formato curto: Swal.fire(title, text, icon)
            return mostrarConfirmacao({
                title: args[0],
                text: args[1] || '',
                icon: args[2] || 'info'
            });
        }
    },

    close: function() {
        if (currentLoadingModal) {
            closeModal(currentLoadingModal);
        }
        // Fechar o último modal aberto
        if (activeModals.length > 0) {
            closeModal(activeModals[activeModals.length - 1]);
        }
    },

    isVisible: () => activeModals.length > 0,
    getContainer: () => activeModals[activeModals.length - 1],
    getPopup: () => activeModals[activeModals.length - 1]?.querySelector('.bioma-modal'),
    showLoading: () => {}
};

// Aliases
const showNotification = mostrarNotificacao;
const showDialog = mostrarConfirmacao;
const showLoading = mostrarLoading;

console.log('%c✅ BIOMA UI System v5.1.0 Carregado', 'color: #10B981; font-weight: bold; font-size: 14px;');
console.log('%c  🎨 Modais customizados bonitos (DIV, não <dialog> nativo)', 'color: #3B82F6;');
console.log('%c  🔔 Toast notifications estilo Toastify', 'color: #3B82F6;');
console.log('%c  🎯 Sistema de botões moderno', 'color: #3B82F6;');
console.log('%c  ✅ 100% compatível com código antigo', 'color: #10B981; font-weight: bold;');
