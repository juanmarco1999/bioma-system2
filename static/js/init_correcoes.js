/**
 * BIOMA - Inicialização e Verificação das Correções
 * Este arquivo garante que todas as correções sejam aplicadas na ordem correta
 */

(function() {
    'use strict';

    console.log('🚀 Iniciando sistema BIOMA com correções...');

    // Aguardar carregamento completo do DOM
    function waitForDOM() {
        return new Promise(resolve => {
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', resolve);
            } else {
                resolve();
            }
        });
    }

    // Função principal de inicialização
    async function init() {
        await waitForDOM();

        console.log('✅ DOM carregado, aplicando correções...');

        // 1. Aplicar correções de estoque
        aplicarCorrecoesEstoque();

        // 2. Configurar observadores de mutação
        configurarObservadores();

        // 3. Corrigir navegação
        corrigirNavegacao();

        // 4. Verificar funções essenciais
        verificarFuncoesEssenciais();

        // 5. Aplicar correções de layout
        aplicarCorrecoesLayout();

        console.log('🎉 Todas as correções aplicadas com sucesso!');
        console.log('📊 Sistema BIOMA pronto para uso!');

        // Notificar usuário
        mostrarNotificacao('✅ Sistema BIOMA carregado com sucesso!', 'success');
    }

    // Aplicar correções de estoque
    function aplicarCorrecoesEstoque() {
        console.log('🔧 Aplicando correções de estoque...');

        // Seções que NÃO devem ter estoque
        const secoesProibidas = [
            'dashboard', 'agendamentos', 'clientes', 'profissionais',
            'servicos', 'financeiro', 'comunidade', 'importar',
            'sistema', 'auditoria', 'configuracoes', 'avaliacoes'
        ];

        secoesProibidas.forEach(secaoId => {
            const secao = document.getElementById(secaoId);
            if (secao) {
                limparEstoqueDaSecao(secao);
            }
        });

        console.log('✅ Correções de estoque aplicadas');
    }

    // Limpar estoque de uma seção - VERSÃO AGRESSIVA
    function limparEstoqueDaSecao(secao) {
        if (!secao) return;

        console.log(`🧹 Limpando estoque de: ${secao.id}`);

        // PASSO 1: Remover por seletores CSS
        const seletoresEstoque = [
            '[id*="estoque" i]',
            '[class*="estoque" i]',
            '[id*="Estoque"]',
            '[class*="Estoque"]',
            '.estoque-card',
            '.estoque-item',
            '.estoque-alert',
            '.estoque-warning',
            '#estoqueVisaoGeral',
            '#estoque-resumo',
            '#estoque-lista',
            '[data-estoque]',
            '[data-type="estoque"]'
        ];

        let removidos = 0;

        seletoresEstoque.forEach(seletor => {
            try {
                const elementos = secao.querySelectorAll(seletor);
                elementos.forEach(el => {
                    // NUNCA remover se estiver dentro de #estoque ou #produtos
                    if (!el.closest('#estoque') && !el.closest('#produtos')) {
                        console.log(`  ❌ Removendo por seletor "${seletor}": ${el.id || el.className || el.tagName}`);
                        el.remove();
                        removidos++;
                    }
                });
            } catch (e) {
                // Seletor inválido, ignorar
            }
        });

        // PASSO 2: Buscar por TEXTO contendo "estoque" (case insensitive)
        const todosElementos = secao.querySelectorAll('*');
        todosElementos.forEach(el => {
            // Pular se for a própria seção de estoque
            if (el.closest('#estoque') || el.closest('#produtos')) return;

            // Verificar texto do elemento
            const texto = el.textContent || '';
            const textoLower = texto.toLowerCase();

            // Se contém "estoque" no texto E não tem muitos filhos (não é um container grande)
            if (textoLower.includes('estoque') && el.children.length < 5) {
                // Verificar se é um elemento de interface relacionado a estoque
                const palavrasChave = [
                    'estoque baixo',
                    'estoque mínimo',
                    'estoque crítico',
                    'produtos em estoque',
                    'baixo estoque',
                    'sem estoque'
                ];

                const temPalavraChave = palavrasChave.some(palavra =>
                    textoLower.includes(palavra)
                );

                if (temPalavraChave) {
                    console.log(`  ❌ Removendo por texto: "${texto.substring(0, 50)}..."`);
                    el.remove();
                    removidos++;
                }
            }
        });

        // PASSO 3: Remover elementos com atributo style contendo "estoque"
        const elementosComStyle = secao.querySelectorAll('[style]');
        elementosComStyle.forEach(el => {
            if (el.closest('#estoque') || el.closest('#produtos')) return;

            const style = el.getAttribute('style') || '';
            if (style.toLowerCase().includes('estoque')) {
                console.log(`  ❌ Removendo por style: ${el.tagName}`);
                el.remove();
                removidos++;
            }
        });

        if (removidos > 0) {
            console.log(`  ✅ Total removido: ${removidos} elementos de estoque`);
        } else {
            console.log(`  ✅ Nenhum elemento de estoque encontrado`);
        }
    }

    // Configurar observadores de mutação
    function configurarObservadores() {
        console.log('🔧 Configurando observadores...');

        const secoesObservar = [
            'dashboard', 'agendamentos', 'clientes', 'profissionais',
            'servicos', 'financeiro', 'comunidade', 'importar',
            'sistema', 'auditoria', 'configuracoes', 'avaliacoes'
        ];

        secoesObservar.forEach(secaoId => {
            const secao = document.getElementById(secaoId);
            if (secao) {
                const observer = new MutationObserver((mutations) => {
                    let temEstoque = false;
                    mutations.forEach(mutation => {
                        mutation.addedNodes.forEach(node => {
                            if (node.nodeType === 1) { // Element node
                                const texto = node.textContent || '';
                                const id = node.id || '';
                                const className = node.className || '';

                                if (
                                    texto.toLowerCase().includes('estoque') ||
                                    id.toLowerCase().includes('estoque') ||
                                    className.toLowerCase().includes('estoque')
                                ) {
                                    temEstoque = true;
                                }
                            }
                        });
                    });

                    if (temEstoque) {
                        console.log(`⚠️ Estoque detectado em ${secaoId}, limpando...`);
                        setTimeout(() => limparEstoqueDaSecao(secao), 100);
                    }
                });

                observer.observe(secao, {
                    childList: true,
                    subtree: true
                });
            }
        });

        console.log('✅ Observadores configurados');
    }

    // Corrigir navegação
    function corrigirNavegacao() {
        console.log('🔧 Corrigindo navegação...');

        // Interceptar cliques nos links do menu
        document.addEventListener('click', function(e) {
            const link = e.target.closest('a[onclick*="goTo"]');
            if (link) {
                const secao = link.getAttribute('onclick')?.match(/goTo\('(\w+)'\)/)?.[1];
                if (secao) {
                    // Limpar flags de carregamento
                    if (window.loadingFlags) {
                        Object.keys(window.loadingFlags).forEach(key => {
                            window.loadingFlags[key] = false;
                        });
                    }

                    // Limpar estoque após navegação
                    setTimeout(() => {
                        const secaoElement = document.getElementById(secao);
                        if (secaoElement && secao !== 'estoque' && secao !== 'produtos') {
                            limparEstoqueDaSecao(secaoElement);
                        }
                    }, 300);
                }
            }
        });

        console.log('✅ Navegação corrigida');

        // LIMPEZA PERIÓDICA AGRESSIVA - A cada 2 segundos
        setInterval(() => {
            const dashboard = document.getElementById('dashboard');
            if (dashboard && dashboard.style.display !== 'none') {
                limparEstoqueDaSecao(dashboard);
            }
        }, 2000);

        console.log('✅ Limpeza periódica do Dashboard ativada (2s)');
    }

    // Verificar funções essenciais
    function verificarFuncoesEssenciais() {
        console.log('🔧 Verificando funções essenciais...');

        const funcoesNecessarias = [
            'goTo',
            'switchSubTab',
            'safeLoad',
            'renderTabela',
            'renderAgendamentosTabela',
            'renderServicosTabela',
            'renderProdutosTabela',
            'renderFinanceiroResumo',
            'renderResumoGeral',
            'renderEstoqueVisaoGeral'
        ];

        const funcoesFaltando = [];
        funcoesNecessarias.forEach(funcao => {
            if (typeof window[funcao] !== 'function') {
                funcoesFaltando.push(funcao);
                console.warn(`⚠️ Função ${funcao} não está definida`);
            }
        });

        if (funcoesFaltando.length === 0) {
            console.log('✅ Todas as funções essenciais estão definidas');
        } else {
            console.error(`❌ ${funcoesFaltando.length} funções faltando:`, funcoesFaltando);
        }

        return funcoesFaltando.length === 0;
    }

    // Aplicar correções de layout
    function aplicarCorrecoesLayout() {
        console.log('🔧 Aplicando correções de layout...');

        // Garantir que o conteúdo principal tenha scroll
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.style.overflowY = 'auto';
            mainContent.style.maxHeight = '100vh';
        }

        // Garantir que as seções tenham altura adequada
        const secoes = document.querySelectorAll('.secao');
        secoes.forEach(secao => {
            secao.style.minHeight = 'auto';
            secao.style.maxHeight = 'none';
        });

        console.log('✅ Correções de layout aplicadas');
    }

    // Mostrar notificação
    function mostrarNotificacao(mensagem, tipo = 'info') {
        // Verificar se SweetAlert2 está disponível
        if (typeof Swal !== 'undefined') {
            const Toast = Swal.mixin({
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 3000,
                timerProgressBar: true
            });

            Toast.fire({
                icon: tipo,
                title: mensagem
            });
        } else {
            console.log(mensagem);
        }
    }

    // Executar inicialização
    init().catch(error => {
        console.error('❌ Erro na inicialização:', error);
        mostrarNotificacao('Erro ao inicializar sistema', 'error');
    });

    // Expor função de limpeza manual
    window.limparEstoqueManual = function() {
        console.log('🧹 Limpeza manual iniciada...');
        aplicarCorrecoesEstoque();
        console.log('✅ Limpeza manual concluída');
    };

    // Expor função de diagnóstico
    window.diagnosticoSistema = function() {
        console.log('\n' + '='.repeat(60));
        console.log('📊 DIAGNÓSTICO DO SISTEMA BIOMA');
        console.log('='.repeat(60));

        console.log('\n1. Funções Essenciais:');
        verificarFuncoesEssenciais();

        console.log('\n2. Elementos de Estoque Indevidos:');
        const secoesProibidas = [
            'dashboard', 'agendamentos', 'clientes', 'profissionais',
            'servicos', 'financeiro', 'comunidade', 'importar',
            'sistema', 'auditoria', 'configuracoes', 'avaliacoes'
        ];

        let totalEstoqueIndevido = 0;
        secoesProibidas.forEach(secaoId => {
            const secao = document.getElementById(secaoId);
            if (secao) {
                const estoque = secao.querySelectorAll('[id*="estoque"], [class*="estoque"]');
                if (estoque.length > 0) {
                    console.warn(`   ⚠️ ${secaoId}: ${estoque.length} elementos de estoque encontrados`);
                    totalEstoqueIndevido += estoque.length;
                }
            }
        });

        if (totalEstoqueIndevido === 0) {
            console.log('   ✅ Nenhum elemento de estoque indevido encontrado');
        } else {
            console.log(`   ⚠️ Total: ${totalEstoqueIndevido} elementos de estoque indevidos`);
        }

        console.log('\n3. Flags de Carregamento:');
        if (window.loadingFlags) {
            const flagsAtivas = Object.keys(window.loadingFlags).filter(k => window.loadingFlags[k]);
            if (flagsAtivas.length === 0) {
                console.log('   ✅ Nenhuma flag de carregamento ativa');
            } else {
                console.warn(`   ⚠️ ${flagsAtivas.length} flags ativas:`, flagsAtivas);
            }
        }

        console.log('\n' + '='.repeat(60));
        console.log('💡 Execute window.limparEstoqueManual() para limpar estoque manualmente');
        console.log('='.repeat(60) + '\n');
    };

    console.log('💡 Dica: Execute diagnosticoSistema() para verificar o estado do sistema');

})();
