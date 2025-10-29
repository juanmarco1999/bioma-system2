// ============================================================
// SISTEMA DE MODAIS CUSTOMIZADO BIOMA v5.0
// ============================================================
// 100% customizado - SEM SweetAlert2
// Usando HTML5 <dialog> nativo
// ============================================================

// Container global para toasts
let biomaToastContainer = null;
let currentDialog = null;
let currentLoadingDialog = null;

// Criar container de toasts (executar uma única vez)
function createToastContainer() {
    if (!biomaToastContainer) {
        biomaToastContainer = document.createElement('div');
        biomaToastContainer.className = 'bioma-toast-container';
        document.body.appendChild(biomaToastContainer);
    }
    return biomaToastContainer;
}

// ========== FUNÇÃO 1: mostrarNotificacao() - Toast Notifications ==========
/**
 * Mostra notificação toast que desaparece automaticamente
 * @param {string} icon - Tipo: 'success', 'error', 'warning', 'info'
 * @param {string} title - Mensagem a exibir
 * @param {number} timer - Tempo em ms (padrão: 2500)
 */
function mostrarNotificacao(icon, title, timer = 2500) {
    const container = createToastContainer();

    const toast = document.createElement('div');
    toast.className = `bioma-toast ${icon}`;

    const iconMap = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };

    toast.innerHTML = `
        <div class="bioma-toast-icon">${iconMap[icon] || 'ℹ'}</div>
        <div class="bioma-toast-content">${title}</div>
        <button class="bioma-toast-close" aria-label="Fechar">×</button>
    `;

    container.appendChild(toast);

    // Fechar ao clicar no X
    const closeBtn = toast.querySelector('.bioma-toast-close');
    closeBtn.addEventListener('click', () => {
        removeToast(toast);
    });

    // Auto-fechar após timer
    if (timer > 0) {
        setTimeout(() => {
            removeToast(toast);
        }, timer);
    }

    return toast;
}

function removeToast(toast) {
    toast.classList.add('removing');
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

// ========== FUNÇÃO 2: mostrarConfirmacao() - Dialog Confirmation ==========
/**
 * Mostra diálogo de confirmação com botões
 * @param {object} config - Configuração do modal
 * @returns {Promise<{isConfirmed: boolean, isDenied: boolean, isDismissed: boolean}>}
 */
function mostrarConfirmacao(config) {
    return new Promise((resolve) => {
        const dialog = document.createElement('dialog');
        dialog.className = 'bioma-dialog';

        const iconMap = {
            success: { icon: '✓', class: 'success' },
            error: { icon: '✕', class: 'error' },
            warning: { icon: '⚠', class: 'warning' },
            info: { icon: 'ℹ', class: 'info' },
            question: { icon: '?', class: 'question' }
        };

        const iconData = iconMap[config.icon] || iconMap.info;

        const confirmText = config.confirmButtonText || 'Confirmar';
        const cancelText = config.cancelButtonText || 'Cancelar';
        const showCancel = config.showCancelButton !== false;
        const showDeny = config.showDenyButton === true;
        const denyText = config.denyButtonText || 'Recusar';

        dialog.innerHTML = `
            <div class="bioma-dialog-header">
                <div class="bioma-dialog-icon ${iconData.class}">${iconData.icon}</div>
                <h2 class="bioma-dialog-title">${config.title || ''}</h2>
            </div>
            <div class="bioma-dialog-body">
                ${config.html || config.text || ''}
            </div>
            <div class="bioma-dialog-footer">
                ${showCancel ? `<button class="bioma-btn-cancel" data-action="cancel">${cancelText}</button>` : ''}
                ${showDeny ? `<button class="bioma-btn-cancel" data-action="deny" style="background: #EF4444; color: white;">${denyText}</button>` : ''}
                <button class="bioma-btn-confirm" data-action="confirm">${confirmText}</button>
            </div>
        `;

        document.body.appendChild(dialog);
        currentDialog = dialog;

        // Adicionar event listeners aos botões
        dialog.querySelectorAll('button[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.getAttribute('data-action');
                dialog.close();
                dialog.remove();
                currentDialog = null;

                resolve({
                    isConfirmed: action === 'confirm',
                    isDenied: action === 'deny',
                    isDismissed: action === 'cancel',
                    value: action === 'confirm'
                });
            });
        });

        // Executar didOpen callback se existir
        if (config.didOpen) {
            setTimeout(() => config.didOpen(dialog), 100);
        }

        // Abrir modal
        dialog.showModal();

        // Fechar com ESC se permitido
        if (config.allowEscapeKey !== false) {
            dialog.addEventListener('cancel', (e) => {
                e.preventDefault();
                dialog.close();
                dialog.remove();
                currentDialog = null;
                resolve({
                    isConfirmed: false,
                    isDenied: false,
                    isDismissed: true
                });
            });
        }
    });
}

// ========== FUNÇÃO 3: mostrarLoading() - Loading Dialog ==========
/**
 * Mostra diálogo de loading (sem botões)
 * @param {string} title - Título do loading
 */
function mostrarLoading(title = 'Processando...') {
    // Fechar loading anterior se existir
    if (currentLoadingDialog) {
        currentLoadingDialog.close();
        currentLoadingDialog.remove();
    }

    const dialog = document.createElement('dialog');
    dialog.className = 'bioma-dialog';

    dialog.innerHTML = `
        <div class="bioma-dialog-header" style="border-bottom: none; padding-bottom: 30px;">
            <div class="bioma-loading"></div>
            <h2 class="bioma-dialog-title">${title}</h2>
        </div>
    `;

    document.body.appendChild(dialog);
    currentLoadingDialog = dialog;
    dialog.showModal();

    return dialog;
}

// ========== COMPATIBILIDADE COM CÓDIGO ANTIGO ==========

// Criar objeto Swal falso para compatibilidade
window.Swal = {
    fire: function(...args) {
        if (typeof args[0] === 'object') {
            const config = args[0];

            // Se tem timer e não tem botões, é notificação
            if (config.timer && config.showConfirmButton === false) {
                return Promise.resolve(mostrarNotificacao(config.icon || 'info', config.title, config.timer));
            }

            // Se é loading (showLoading ou didOpen com showLoading)
            if (config.didOpen && config.showConfirmButton === false && !config.timer) {
                return Promise.resolve(mostrarLoading(config.title));
            }

            // Senão é confirmação
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
        if (currentLoadingDialog) {
            currentLoadingDialog.close();
            currentLoadingDialog.remove();
            currentLoadingDialog = null;
        }
        if (currentDialog) {
            currentDialog.close();
            currentDialog.remove();
            currentDialog = null;
        }
    },

    isVisible: function() {
        return currentDialog !== null || currentLoadingDialog !== null;
    },

    getContainer: function() {
        return currentDialog || currentLoadingDialog;
    },

    getPopup: function() {
        return currentDialog || currentLoadingDialog;
    },

    showLoading: function() {
        // Já mostrado no mostrarLoading()
    }
};

// Aliases para compatibilidade
const showNotification = mostrarNotificacao;
const showDialog = mostrarConfirmacao;
const showLoading = mostrarLoading;

// Log do sistema
console.log('%c✅ Sistema de Modais Customizado BIOMA v5.0 Carregado', 'color: green; font-weight: bold; font-size: 14px;');
console.log('%c  📢 mostrarNotificacao() - Toast notifications', 'color: blue;');
console.log('%c  ❓ mostrarConfirmacao() - Diálogos de confirmação', 'color: blue;');
console.log('%c  ⏳ mostrarLoading() - Loading sem botões', 'color: blue;');
console.log('%c  🎨 100% Customizado - SEM SweetAlert2', 'color: magenta; font-weight: bold;');
console.log('%c  ✅ HTML5 <dialog> nativo - SEM problemas de z-index', 'color: green; font-weight: bold;');
