/**
 * BIOMA - Remover AGRESSIVAMENTE estoque do Dashboard
 * Este script remove FISICAMENTE qualquer elemento de estoque que aparecer no Dashboard
 */

(function() {
    'use strict';

    console.log('🚀 [ANTI-ESTOQUE] Iniciando proteção do Dashboard...');

    /**
     * Remove TODOS os elementos de estoque do Dashboard
     */
    function removerEstoqueDoDashboard() {
        const dashboard = document.getElementById('section-dashboard');
        if (!dashboard) return;

        // Se Dashboard não está visível, não faz nada
        if (dashboard.style.display === 'none' || !dashboard.classList.contains('active')) {
            return;
        }

        let removidos = 0;

        // PASSO 1: Remover elementos com texto "Estoque Baixo"
        const todosElementos = dashboard.querySelectorAll('*');
        todosElementos.forEach(elemento => {
            const texto = elemento.textContent || '';

            // Verifica se contém texto relacionado a estoque
            if (texto.includes('Estoque Baixo') ||
                texto.includes('ESTOQUE BAIXO') ||
                texto.includes('Estoque Crítico') ||
                texto.includes('PRODUTO') && texto.includes('SKU') && texto.includes('MÍNIMO')) {

                // Só remove se for um card ou tabela (não remove palavras soltas)
                if (elemento.classList.contains('card') ||
                    elemento.classList.contains('table-responsive') ||
                    elemento.tagName === 'TABLE' ||
                    elemento.classList.contains('col-md-6') ||
                    elemento.classList.contains('col-xl-8')) {

                    console.warn('🗑️ [ANTI-ESTOQUE] Removendo elemento com texto de estoque:', elemento.className || elemento.tagName);
                    elemento.remove();
                    removidos++;
                }
            }
        });

        // PASSO 2: Remover elementos com IDs relacionados a estoque
        const idsEstoque = [
            'alertasEstoque',
            'estoqueAlertas',
            'estoqueBaixoBody',
            'estoqueBaixoBodyResumo',
            'estoqueVisaoGeral',
            'estoque-resumo',
            'estoque-lista',
            'estoqueCritico',
            'estoqueAtencao',
            'estoqueNormal',
            'produtosCriticos',
            'produtosAtencao',
            'produtosNormais'
        ];

        idsEstoque.forEach(id => {
            const elemento = dashboard.querySelector(`#${id}`);
            if (elemento) {
                // Remove o card/container pai, não apenas o elemento
                let container = elemento.closest('.card');
                if (!container) container = elemento.closest('.col-md-6');
                if (!container) container = elemento.closest('.col-xl-8');
                if (!container) container = elemento;

                console.warn(`🗑️ [ANTI-ESTOQUE] Removendo elemento por ID: #${id}`);
                container.remove();
                removidos++;
            }
        });

        // PASSO 3: Remover elementos com classes relacionadas a estoque
        const classesEstoque = [
            'estoque-card',
            'estoque-item',
            'estoque-alert',
            'estoque-warning',
            'stock-summary-card'
        ];

        classesEstoque.forEach(classe => {
            const elementos = dashboard.querySelectorAll(`.${classe}`);
            elementos.forEach(elemento => {
                console.warn(`🗑️ [ANTI-ESTOQUE] Removendo elemento por classe: .${classe}`);
                elemento.remove();
                removidos++;
            });
        });

        // PASSO 4: Remover qualquer tabela com cabeçalhos de estoque
        const tabelas = dashboard.querySelectorAll('table');
        tabelas.forEach(tabela => {
            const thead = tabela.querySelector('thead');
            if (thead) {
                const textoHeader = thead.textContent || '';
                if (textoHeader.includes('PRODUTO') && textoHeader.includes('SKU') && textoHeader.includes('ESTOQUE')) {
                    console.warn('🗑️ [ANTI-ESTOQUE] Removendo tabela de estoque');
                    const container = tabela.closest('.card') || tabela.closest('.table-responsive') || tabela;
                    container.remove();
                    removidos++;
                }
            }
        });

        if (removidos > 0) {
            console.warn(`⚠️ [ANTI-ESTOQUE] ${removidos} elementos de estoque removidos do Dashboard!`);
        }
    }

    /**
     * Configurar MutationObserver para detectar quando elementos são adicionados ao Dashboard
     */
    function configurarObservador() {
        const dashboard = document.getElementById('section-dashboard');
        if (!dashboard) {
            console.warn('⚠️ [ANTI-ESTOQUE] Dashboard não encontrado, tentando novamente em 1s...');
            setTimeout(configurarObservador, 1000);
            return;
        }

        console.log('👁️ [ANTI-ESTOQUE] Observador configurado no Dashboard');

        const observer = new MutationObserver((mutations) => {
            let temEstoque = false;

            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const texto = node.textContent || '';
                        const id = node.id || '';
                        const className = node.className || '';

                        // Detecta se é elemento de estoque
                        if (texto.includes('Estoque Baixo') ||
                            texto.includes('ESTOQUE') ||
                            id.toLowerCase().includes('estoque') ||
                            className.toLowerCase().includes('estoque')) {
                            temEstoque = true;
                        }
                    }
                });
            });

            if (temEstoque) {
                console.warn('⚠️ [ANTI-ESTOQUE] Estoque detectado sendo adicionado ao Dashboard! Removendo...');
                setTimeout(removerEstoqueDoDashboard, 50);
            }
        });

        observer.observe(dashboard, {
            childList: true,
            subtree: true
        });
    }

    /**
     * Limpeza periódica AGRESSIVA
     */
    function iniciarLimpezaPeriodica() {
        console.log('🔄 [ANTI-ESTOQUE] Limpeza periódica iniciada (a cada 1 segundo)');

        setInterval(() => {
            const dashboard = document.getElementById('section-dashboard');
            if (dashboard && (dashboard.style.display !== 'none' || dashboard.classList.contains('active'))) {
                removerEstoqueDoDashboard();
            }
        }, 1000); // A cada 1 segundo
    }

    /**
     * Inicialização
     */
    function init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                removerEstoqueDoDashboard();
                configurarObservador();
                iniciarLimpezaPeriodica();
            });
        } else {
            removerEstoqueDoDashboard();
            configurarObservador();
            iniciarLimpezaPeriodica();
        }
    }

    // Executar limpeza imediata
    if (document.getElementById('section-dashboard')) {
        removerEstoqueDoDashboard();
    }

    // Inicializar sistema
    init();

    // Expor função global para limpeza manual
    window.limparEstoqueDashboard = function() {
        console.log('🧹 [ANTI-ESTOQUE] Limpeza manual executada');
        removerEstoqueDoDashboard();
    };

    console.log('✅ [ANTI-ESTOQUE] Proteção do Dashboard ativada!');
    console.log('💡 Use: window.limparEstoqueDashboard() para limpar manualmente');

})();
