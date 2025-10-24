/**
 * BIOMA State Manager
 * Sistema centralizado de gerenciamento de estado
 * Previne carregamentos infinitos e conflitos de renderização
 */

(function() {
    'use strict';

    // Estado global do sistema
    const BiOMAState = {
        // Seção atual
        currentSection: null,

        // Seções carregadas (cache)
        loadedSections: {},

        // Flags de carregamento
        loading: {},

        // Timestamps de último carregamento
        lastLoad: {},

        // Dados em cache
        cache: {},

        // Configurações
        config: {
            cacheTimeout: 30000, // 30 segundos
            loadTimeout: 5000,   // 5 segundos máximo para carregar
            maxRetries: 2,       // Máximo de 2 tentativas
            debounceTime: 300    // 300ms de debounce
        },

        // Observadores
        observers: {},

        // Histórico de navegação
        history: []
    };

    /**
     * Gerenciador de Estado
     */
    const StateManager = {

        /**
         * Inicializar o estado
         */
        init: function() {
            console.log('🔧 StateManager: Inicializando...');
            this.setupEventListeners();
            this.startMonitoring();
            console.log('✅ StateManager: Pronto!');
        },

        /**
         * Definir seção atual
         */
        setCurrentSection: function(sectionId) {
            if (!sectionId) return;

            const previous = BiOMAState.currentSection;
            BiOMAState.currentSection = sectionId;

            // Adicionar ao histórico
            BiOMAState.history.push({
                section: sectionId,
                timestamp: Date.now(),
                from: previous
            });

            // Limitar histórico a 50 itens
            if (BiOMAState.history.length > 50) {
                BiOMAState.history.shift();
            }

            console.log(`📍 StateManager: Seção atual = ${sectionId}`);

            // Notificar observadores
            this.notify('sectionChange', { from: previous, to: sectionId });
        },

        /**
         * Verificar se uma seção está carregando
         */
        isLoading: function(sectionId) {
            return BiOMAState.loading[sectionId] === true;
        },

        /**
         * Marcar seção como carregando
         */
        setLoading: function(sectionId, isLoading) {
            BiOMAState.loading[sectionId] = isLoading;

            if (isLoading) {
                BiOMAState.lastLoad[sectionId] = Date.now();
            }

            console.log(`${isLoading ? '⏳' : '✅'} StateManager: ${sectionId} ${isLoading ? 'carregando' : 'carregado'}`);
        },

        /**
         * Verificar se pode carregar (anti-loop)
         */
        canLoad: function(sectionId) {
            // Já está carregando?
            if (this.isLoading(sectionId)) {
                console.warn(`⚠️ StateManager: ${sectionId} já está carregando!`);
                return false;
            }

            // Carregou recentemente?
            const lastLoad = BiOMAState.lastLoad[sectionId];
            if (lastLoad) {
                const elapsed = Date.now() - lastLoad;
                if (elapsed < BiOMAState.config.debounceTime) {
                    console.warn(`⚠️ StateManager: ${sectionId} carregou há ${elapsed}ms (debounce)`);
                    return false;
                }
            }

            return true;
        },

        /**
         * Obter dados do cache
         */
        getCache: function(key) {
            const cached = BiOMAState.cache[key];
            if (!cached) return null;

            // Verificar se expirou
            const age = Date.now() - cached.timestamp;
            if (age > BiOMAState.config.cacheTimeout) {
                delete BiOMAState.cache[key];
                return null;
            }

            console.log(`💾 StateManager: Cache hit para ${key} (${age}ms)`);
            return cached.data;
        },

        /**
         * Salvar dados no cache
         */
        setCache: function(key, data) {
            BiOMAState.cache[key] = {
                data: data,
                timestamp: Date.now()
            };
            console.log(`💾 StateManager: Cache salvo para ${key}`);
        },

        /**
         * Limpar cache
         */
        clearCache: function(key) {
            if (key) {
                delete BiOMAState.cache[key];
                console.log(`🗑️ StateManager: Cache limpo para ${key}`);
            } else {
                BiOMAState.cache = {};
                console.log(`🗑️ StateManager: Todo cache limpo`);
            }
        },

        /**
         * Resetar flags de carregamento
         */
        resetLoading: function(sectionId) {
            if (sectionId) {
                BiOMAState.loading[sectionId] = false;
            } else {
                BiOMAState.loading = {};
            }
            console.log(`🔄 StateManager: Flags de carregamento resetadas`);
        },

        /**
         * Adicionar observador
         */
        observe: function(event, callback) {
            if (!BiOMAState.observers[event]) {
                BiOMAState.observers[event] = [];
            }
            BiOMAState.observers[event].push(callback);
        },

        /**
         * Notificar observadores
         */
        notify: function(event, data) {
            const observers = BiOMAState.observers[event];
            if (observers) {
                observers.forEach(callback => {
                    try {
                        callback(data);
                    } catch (e) {
                        console.error(`❌ StateManager: Erro no observador ${event}:`, e);
                    }
                });
            }
        },

        /**
         * Configurar listeners
         */
        setupEventListeners: function() {
            // Detectar mudanças de visibilidade da página
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) {
                    console.log('👁️ StateManager: Página oculta');
                } else {
                    console.log('👁️ StateManager: Página visível');
                    // Limpar flags antigas
                    this.cleanupStaleFlags();
                }
            });
        },

        /**
         * Limpar flags antigas (mais de 10 segundos)
         */
        cleanupStaleFlags: function() {
            const now = Date.now();
            const maxAge = 10000; // 10 segundos

            Object.keys(BiOMAState.lastLoad).forEach(key => {
                const age = now - BiOMAState.lastLoad[key];
                if (age > maxAge && BiOMAState.loading[key]) {
                    console.warn(`⚠️ StateManager: Flag de ${key} estava travada há ${age}ms, resetando...`);
                    BiOMAState.loading[key] = false;
                }
            });
        },

        /**
         * Monitorar sistema
         */
        startMonitoring: function() {
            // Verificar flags presas a cada 5 segundos
            setInterval(() => {
                this.cleanupStaleFlags();
            }, 5000);

            // Limpar cache antigo a cada 1 minuto
            setInterval(() => {
                const now = Date.now();
                let cleaned = 0;

                Object.keys(BiOMAState.cache).forEach(key => {
                    const age = now - BiOMAState.cache[key].timestamp;
                    if (age > BiOMAState.config.cacheTimeout) {
                        delete BiOMAState.cache[key];
                        cleaned++;
                    }
                });

                if (cleaned > 0) {
                    console.log(`🧹 StateManager: ${cleaned} itens expirados removidos do cache`);
                }
            }, 60000);
        },

        /**
         * Obter status do sistema
         */
        getStatus: function() {
            return {
                currentSection: BiOMAState.currentSection,
                loadingCount: Object.values(BiOMAState.loading).filter(v => v).length,
                cacheSize: Object.keys(BiOMAState.cache).length,
                historySize: BiOMAState.history.length,
                loading: { ...BiOMAState.loading },
                cache: Object.keys(BiOMAState.cache)
            };
        },

        /**
         * Debug: imprimir estado
         */
        debug: function() {
            console.log('📊 BIOMA STATE:');
            console.log('  Seção Atual:', BiOMAState.currentSection);
            console.log('  Carregando:', BiOMAState.loading);
            console.log('  Cache:', Object.keys(BiOMAState.cache));
            console.log('  Histórico:', BiOMAState.history.slice(-5));
        }
    };

    // Expor globalmente
    window.BiOMAState = BiOMAState;
    window.StateManager = StateManager;

    // Auto-inicializar
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => StateManager.init());
    } else {
        StateManager.init();
    }

    console.log('✅ State Manager carregado');

})();
