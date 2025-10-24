/**
 * BIOMA Navigation System
 * Sistema de navegação robusto e seguro
 * Integra StateManager e RenderController
 */

(function() {
    'use strict';

    const NavigationSystem = {

        /**
         * Inicializar
         */
        init: function() {
            console.log('🧭 NavigationSystem: Inicializando...');
            this.override Functions();
            this.setupInterceptors();
            console.log('✅ NavigationSystem: Pronto!');
        },

        /**
         * Sobrescrever funções originais
         */
        overrideFunctions: function() {
            // Salvar função original goTo
            window._originalGoTo = window.goTo;

            // Nova função goTo segura
            window.goTo = (secao) => {
                console.log(`🧭 NavigationSystem: goTo(${secao})`);
                return this.navigateTo(secao);
            };

            // Salvar função original switchSubTab
            window._originalSwitchSubTab = window.switchSubTab;

            // Nova função switchSubTab segura
            window.switchSubTab = (mainTab, subTab) => {
                console.log(`🧭 NavigationSystem: switchSubTab(${mainTab}, ${subTab})`);
                return this.switchSubTab(mainTab, subTab);
            };

            console.log('✅ NavigationSystem: Funções sobrescritas');
        },

        /**
         * Navegar para seção (versão segura)
         */
        navigateTo: function(sectionId) {
            if (!sectionId) {
                console.error('❌ NavigationSystem: sectionId inválido');
                return;
            }

            console.log(`📍 NavigationSystem: Navegando para ${sectionId}...`);

            // 1. Verificar se pode carregar
            if (!window.StateManager.canLoad(sectionId)) {
                console.warn(`⚠️ NavigationSystem: ${sectionId} está sendo carregado, ignorando...`);
                return;
            }

            // 2. Esconder todas as seções
            this.hideAllSections();

            // 3. Atualizar estado
            window.StateManager.setCurrentSection(sectionId);

            // 4. Remover classe active de todos os links
            document.querySelectorAll('.sidebar a').forEach(link => {
                link.classList.remove('active');
            });

            // 5. Mostrar seção alvo
            const targetSection = document.getElementById(sectionId);
            if (targetSection) {
                targetSection.style.display = 'block';

                // 6. Adicionar classe active ao link correspondente
                const activeLink = document.querySelector(`.sidebar a[onclick*="${sectionId}"]`);
                if (activeLink) {
                    activeLink.classList.add('active');
                }

                // 7. Limpar conteúdo indevido
                setTimeout(() => {
                    if (window.RenderController) {
                        window.RenderController.cleanSection(sectionId);
                    }
                }, 100);

                // 8. Carregar dados da seção
                this.loadSectionData(sectionId);

                console.log(`✅ NavigationSystem: ${sectionId} exibido`);
            } else {
                console.error(`❌ NavigationSystem: Seção ${sectionId} não encontrada no DOM`);
            }

            // 9. Chamar função original se existir
            if (window._originalGoTo && window._originalGoTo !== window.goTo) {
                try {
                    window._originalGoTo(sectionId);
                } catch (e) {
                    console.warn('⚠️ NavigationSystem: Erro na função original goTo:', e);
                }
            }
        },

        /**
         * Esconder todas as seções
         */
        hideAllSections: function() {
            document.querySelectorAll('.secao, [id$="dashboard"], [id$="agendamentos"], [id$="clientes"], [id$="profissionais"], [id$="servicos"], [id$="produtos"], [id$="estoque"], [id$="financeiro"], [id$="comunidade"], [id$="importar"], [id$="sistema"], [id$="auditoria"], [id$="configuracoes"], [id$="avaliacoes"]').forEach(secao => {
                if (secao.id && !secao.id.includes('-')) {
                    secao.style.display = 'none';
                }
            });
        },

        /**
         * Alternar sub-tab (versão segura)
         */
        switchSubTab: function(mainTab, subTab) {
            console.log(`🔀 NavigationSystem: switchSubTab(${mainTab}, ${subTab})`);

            // 1. Esconder todas as sub-tabs da seção
            const mainSection = document.getElementById(mainTab);
            if (!mainSection) {
                console.error(`❌ NavigationSystem: Seção ${mainTab} não encontrada`);
                return;
            }

            const allSubTabs = mainSection.querySelectorAll('.sub-tab-content');
            allSubTabs.forEach(tab => {
                tab.style.display = 'none';
            });

            // 2. Remover classe active de todos os botões
            const allButtons = mainSection.querySelectorAll('.sub-nav-btn');
            allButtons.forEach(btn => {
                btn.classList.remove('active');
            });

            // 3. Mostrar sub-tab selecionada
            const targetSubTab = document.getElementById(`${mainTab}-${subTab}`);
            if (targetSubTab) {
                targetSubTab.style.display = 'block';
                console.log(`✅ NavigationSystem: Sub-tab ${mainTab}-${subTab} exibida`);
            } else {
                console.warn(`⚠️ NavigationSystem: Sub-tab ${mainTab}-${subTab} não encontrada`);
            }

            // 4. Adicionar classe active ao botão clicado
            const clickedButton = event?.target?.closest('.sub-nav-btn');
            if (clickedButton) {
                clickedButton.classList.add('active');
            }

            // 5. Carregar dados da sub-tab se necessário
            const loadFunctionName = `load${this.capitalize(mainTab)}${this.capitalize(subTab)}`;
            if (typeof window[loadFunctionName] === 'function') {
                const key = `${mainTab}-${subTab}`;
                if (window.StateManager.canLoad(key)) {
                    window.StateManager.setLoading(key, true);

                    Promise.resolve()
                        .then(() => window[loadFunctionName]())
                        .then(() => {
                            window.StateManager.setLoading(key, false);
                            console.log(`✅ NavigationSystem: ${loadFunctionName}() executado`);
                        })
                        .catch(error => {
                            window.StateManager.setLoading(key, false);
                            console.error(`❌ NavigationSystem: Erro em ${loadFunctionName}():`, error);
                        });
                }
            }

            // 6. Chamar função original se existir
            if (window._originalSwitchSubTab && window._originalSwitchSubTab !== window.switchSubTab) {
                try {
                    window._originalSwitchSubTab(mainTab, subTab);
                } catch (e) {
                    console.warn('⚠️ NavigationSystem: Erro na função original switchSubTab:', e);
                }
            }
        },

        /**
         * Carregar dados da seção
         */
        loadSectionData: function(sectionId) {
            // Verificar cache primeiro
            const cached = window.StateManager.getCache(sectionId);
            if (cached) {
                console.log(`💾 NavigationSystem: Usando dados em cache para ${sectionId}`);
                return Promise.resolve(cached);
            }

            // Nome da função de carregamento
            const loadFunctionName = `load${this.capitalize(sectionId)}`;

            if (typeof window[loadFunctionName] === 'function') {
                if (!window.StateManager.canLoad(sectionId)) {
                    console.warn(`⚠️ NavigationSystem: ${sectionId} já está carregando`);
                    return Promise.resolve();
                }

                console.log(`⏳ NavigationSystem: Executando ${loadFunctionName}()...`);

                window.StateManager.setLoading(sectionId, true);

                return Promise.resolve()
                    .then(() => window[loadFunctionName]())
                    .then(result => {
                        window.StateManager.setLoading(sectionId, false);
                        window.StateManager.setCache(sectionId, result);
                        console.log(`✅ NavigationSystem: ${loadFunctionName}() concluído`);
                        return result;
                    })
                    .catch(error => {
                        window.StateManager.setLoading(sectionId, false);
                        console.error(`❌ NavigationSystem: Erro em ${loadFunctionName}():`, error);
                        throw error;
                    });
            } else {
                console.log(`ℹ️ NavigationSystem: Função ${loadFunctionName}() não definida`);
                return Promise.resolve();
            }
        },

        /**
         * Configurar interceptors
         */
        setupInterceptors: function() {
            // Interceptar cliques em links da sidebar
            document.addEventListener('click', (e) => {
                const link = e.target.closest('.sidebar a[onclick*="goTo"]');
                if (link) {
                    e.preventDefault();
                    const match = link.getAttribute('onclick')?.match(/goTo\('(\w+)'\)/);
                    if (match) {
                        this.navigateTo(match[1]);
                    }
                }
            }, true);

            console.log('✅ NavigationSystem: Interceptors configurados');
        },

        /**
         * Capitalizar string
         */
        capitalize: function(str) {
            return str.charAt(0).toUpperCase() + str.slice(1);
        },

        /**
         * Recarregar seção atual
         */
        refresh: function() {
            const current = window.BiOMAState.currentSection;
            if (current) {
                console.log(`🔄 NavigationSystem: Recarregando ${current}...`);
                window.StateManager.clearCache(current);
                window.StateManager.resetLoading(current);
                this.navigateTo(current);
            }
        },

        /**
         * Voltar para seção anterior
         */
        back: function() {
            const history = window.BiOMAState.history;
            if (history.length >= 2) {
                const previous = history[history.length - 2];
                this.navigateTo(previous.section);
            }
        }
    };

    // Expor globalmente
    window.NavigationSystem = NavigationSystem;

    // Auto-inicializar
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => NavigationSystem.init());
    } else {
        NavigationSystem.init();
    }

    console.log('✅ Navigation System carregado');

})();
