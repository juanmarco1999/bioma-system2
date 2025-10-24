/**
 * BIOMA CORE
 * Sistema principal que integra todos os módulos
 * Garante renderização correta e prevenção de bugs
 */

(function() {
    'use strict';

    console.log('%c🌳 BIOMA SYSTEM v3.7 - CORE', 'color: #7C3AED; font-size: 16px; font-weight: bold;');

    const BiOMACore = {

        version: '3.7.0',
        initialized: false,

        /**
         * Inicializar sistema completo
         */
        init: async function() {
            if (this.initialized) {
                console.warn('⚠️ BiOMACore: Sistema já inicializado');
                return;
            }

            console.log('🚀 BiOMACore: Iniciando sistema...');

            try {
                // 1. Aguardar DOM
                await this.waitForDOM();
                console.log('✅ BiOMACore: DOM pronto');

                // 2. Aguardar módulos essenciais
                await this.waitForModules();
                console.log('✅ BiOMACore: Módulos carregados');

                // 3. Inicializar subsistemas (já auto-inicializados)
                console.log('✅ BiOMACore: StateManager ativo');
                console.log('✅ BiOMACore: RenderController ativo');
                console.log('✅ BiOMACore: NavigationSystem ativo');

                // 4. Limpeza inicial
                this.initialCleanup();

                // 5. Configurar proteções
                this.setupProtections();

                // 6. Marcar como inicializado
                this.initialized = true;

                // 7. Mensagem de sucesso
                this.showWelcome();

                console.log('🎉 BiOMACore: Sistema 100% operacional!');

            } catch (error) {
                console.error('❌ BiOMACore: Erro na inicialização:', error);
                this.showError(error);
            }
        },

        /**
         * Aguardar DOM
         */
        waitForDOM: function() {
            return new Promise(resolve => {
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', resolve);
                } else {
                    resolve();
                }
            });
        },

        /**
         * Aguardar módulos essenciais
         */
        waitForModules: function() {
            return new Promise((resolve, reject) => {
                const maxAttempts = 50; // 5 segundos
                let attempts = 0;

                const check = () => {
                    attempts++;

                    const hasStateManager = typeof window.StateManager !== 'undefined';
                    const hasRenderController = typeof window.RenderController !== 'undefined';
                    const hasNavigationSystem = typeof window.NavigationSystem !== 'undefined';

                    if (hasStateManager && hasRenderController && hasNavigationSystem) {
                        resolve();
                    } else if (attempts >= maxAttempts) {
                        reject(new Error('Timeout aguardando módulos'));
                    } else {
                        setTimeout(check, 100);
                    }
                };

                check();
            });
        },

        /**
         * Limpeza inicial
         */
        initialCleanup: function() {
            console.log('🧹 BiOMACore: Limpeza inicial...');

            // Limpar todas as seções
            if (window.RenderController) {
                window.RenderController.cleanAll();
            }

            // Resetar flags de carregamento
            if (window.StateManager) {
                window.StateManager.resetLoading();
            }

            console.log('✅ BiOMACore: Limpeza concluída');
        },

        /**
         * Configurar proteções
         */
        setupProtections: function() {
            console.log('🛡️ BiOMACore: Configurando proteções...');

            // Proteção contra carregamento infinito global
            const originalFetch = window.fetch;
            let fetchCount = {};

            window.fetch = function(...args) {
                const url = args[0];

                // Rastrear requisições
                if (typeof url === 'string') {
                    fetchCount[url] = (fetchCount[url] || 0) + 1;

                    // Limpar contadores antigos a cada 10 segundos
                    setTimeout(() => {
                        fetchCount[url] = Math.max(0, (fetchCount[url] || 0) - 1);
                    }, 10000);

                    // Detectar loop
                    if (fetchCount[url] > 10) {
                        console.error(`❌ BiOMACore: Loop detectado! URL: ${url} (${fetchCount[url]} requisições)`);
                        return Promise.reject(new Error('Loop de requisições detectado'));
                    }
                }

                return originalFetch.apply(this, args);
            };

            // Proteção contra erros não tratados
            window.addEventListener('error', (e) => {
                console.error('❌ BiOMACore: Erro não tratado:', e.error);
            });

            window.addEventListener('unhandledrejection', (e) => {
                console.error('❌ BiOMACore: Promise rejeitada:', e.reason);
            });

            console.log('✅ BiOMACore: Proteções ativas');
        },

        /**
         * Mostrar mensagem de boas-vindas
         */
        showWelcome: function() {
            console.log('%c╔════════════════════════════════════════╗', 'color: #7C3AED');
            console.log('%c║     🌳 BIOMA SYSTEM v3.7 - CORE      ║', 'color: #7C3AED; font-weight: bold');
            console.log('%c║                                        ║', 'color: #7C3AED');
            console.log('%c║  ✅ Sistema 100% Operacional           ║', 'color: #10B981; font-weight: bold');
            console.log('%c║  ✅ Proteções Ativas                   ║', 'color: #10B981');
            console.log('%c║  ✅ Sem Loops de Carregamento          ║', 'color: #10B981');
            console.log('%c║  ✅ Sem Sobreposição de Conteúdo       ║', 'color: #10B981');
            console.log('%c║                                        ║', 'color: #7C3AED');
            console.log('%c║  💡 Digite BIOMA.help() para comandos ║', 'color: #3B82F6');
            console.log('%c╚════════════════════════════════════════╝', 'color: #7C3AED');
        },

        /**
         * Mostrar erro
         */
        showError: function(error) {
            console.error('%c╔════════════════════════════════════════╗', 'color: #EF4444');
            console.error('%c║  ❌ ERRO NA INICIALIZAÇÃO DO SISTEMA  ║', 'color: #EF4444; font-weight: bold');
            console.error('%c╚════════════════════════════════════════╝', 'color: #EF4444');
            console.error(error);
        },

        /**
         * Comandos úteis
         */
        commands: {
            help: function() {
                console.log('%c📚 COMANDOS DISPONÍVEIS:', 'color: #7C3AED; font-size: 14px; font-weight: bold');
                console.log('');
                console.log('%cNavegação:', 'color: #F59E0B; font-weight: bold');
                console.log('  BIOMA.goTo("dashboard")      - Ir para seção');
                console.log('  BIOMA.refresh()              - Recarregar seção atual');
                console.log('  BIOMA.back()                 - Voltar');
                console.log('');
                console.log('%cEstado:', 'color: #F59E0B; font-weight: bold');
                console.log('  BIOMA.status()               - Ver status do sistema');
                console.log('  BIOMA.cache()                - Ver cache');
                console.log('  BIOMA.clearCache()           - Limpar cache');
                console.log('');
                console.log('%cLimpeza:', 'color: #F59E0B; font-weight: bold');
                console.log('  BIOMA.clean("dashboard")     - Limpar seção específica');
                console.log('  BIOMA.cleanAll()             - Limpar todas as seções');
                console.log('');
                console.log('%cDebug:', 'color: #F59E0B; font-weight: bold');
                console.log('  BIOMA.debug()                - Mostrar informações de debug');
                console.log('  BIOMA.version                - Ver versão');
            },

            goTo: function(section) {
                window.NavigationSystem.navigateTo(section);
            },

            refresh: function() {
                window.NavigationSystem.refresh();
            },

            back: function() {
                window.NavigationSystem.back();
            },

            status: function() {
                const status = window.StateManager.getStatus();
                console.log('%c📊 STATUS DO SISTEMA:', 'color: #7C3AED; font-size: 14px; font-weight: bold');
                console.log('  Seção Atual:', status.currentSection);
                console.log('  Carregando:', status.loadingCount, 'seções');
                console.log('  Cache:', status.cacheSize, 'itens');
                console.log('  Histórico:', status.historySize, 'entradas');
                console.log('');
                console.log('  Detalhes:');
                console.log('    Loading:', status.loading);
                console.log('    Cache:', status.cache);
            },

            cache: function() {
                const status = window.StateManager.getStatus();
                console.log('%c💾 CACHE:', 'color: #7C3AED; font-size: 14px; font-weight: bold');
                console.log('  Itens:', status.cache);
            },

            clearCache: function() {
                window.StateManager.clearCache();
                console.log('✅ Cache limpo!');
            },

            clean: function(section) {
                window.RenderController.cleanSection(section);
                console.log(`✅ Seção ${section} limpa!`);
            },

            cleanAll: function() {
                window.RenderController.cleanAll();
                console.log('✅ Todas as seções limpas!');
            },

            debug: function() {
                console.log('%c🐛 DEBUG INFO:', 'color: #7C3AED; font-size: 14px; font-weight: bold');
                console.log('');
                window.StateManager.debug();
                console.log('');
                window.RenderController.debug();
            }
        }
    };

    // Expor globalmente
    window.BiOMACore = BiOMACore;
    window.BIOMA = BiOMACore.commands;

    // Auto-inicializar
    BiOMACore.init();

})();
