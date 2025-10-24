/**
 * BIOMA Render Controller
 * Sistema de controle de renderização por seção
 * Previne sobreposição e informações indevidas
 */

(function() {
    'use strict';

    /**
     * Mapa de conteúdo permitido por seção
     */
    const SECTION_CONTENT_MAP = {
        'dashboard': {
            allowed: ['dashboard', 'resumo', 'geral', 'card', 'stats', 'grafico', 'chart'],
            forbidden: ['estoque', 'orcamento', 'contrato', 'anamnese', 'prontuario'],
            containers: ['#dashboard-resumo', '#dashboard-graficos', '#dashboard-cards']
        },
        'agendamentos': {
            allowed: ['agendamento', 'agenda', 'calendario', 'horario', 'cliente', 'servico'],
            forbidden: ['estoque', 'produto', 'financeiro', 'orcamento'],
            containers: ['#agendamentos-lista', '#agendamentos-calendario']
        },
        'clientes': {
            allowed: ['cliente', 'pessoa', 'contato', 'anamnese', 'prontuario'],
            forbidden: ['estoque', 'produto', 'financeiro', 'agendamento'],
            containers: ['#clientes-lista', '#cliente-detalhes']
        },
        'profissionais': {
            allowed: ['profissional', 'funcionario', 'colaborador', 'agenda', 'comissao'],
            forbidden: ['estoque', 'produto', 'cliente'],
            containers: ['#profissionais-lista']
        },
        'servicos': {
            allowed: ['servico', 'tratamento', 'procedimento', 'categoria', 'preco'],
            forbidden: ['estoque', 'produto', 'cliente', 'financeiro'],
            containers: ['#servicos-lista', '#servico-form']
        },
        'produtos': {
            allowed: ['produto', 'item', 'estoque', 'preco', 'categoria', 'fornecedor'],
            forbidden: ['agendamento', 'cliente', 'servico'],
            containers: ['#produtos-lista', '#produto-form']
        },
        'estoque': {
            allowed: ['estoque', 'produto', 'item', 'quantidade', 'minimo', 'movimentacao'],
            forbidden: ['agendamento', 'cliente', 'servico'],
            containers: ['#estoque-visao-geral', '#estoque-lista', '#estoque-movimentacoes']
        },
        'financeiro': {
            allowed: ['financeiro', 'receita', 'despesa', 'comissao', 'pagamento', 'faturamento'],
            forbidden: ['estoque', 'produto', 'agendamento'],
            containers: ['#financeiro-resumo', '#financeiro-receitas', '#financeiro-despesas']
        },
        'comunidade': {
            allowed: ['post', 'comunidade', 'feed', 'noticia', 'anuncio'],
            forbidden: ['estoque', 'produto', 'financeiro', 'agendamento'],
            containers: ['#comunidade-feed']
        },
        'importar': {
            allowed: ['importar', 'upload', 'arquivo', 'planilha', 'dados'],
            forbidden: ['estoque', 'produto'],
            containers: ['#importar-form']
        },
        'sistema': {
            allowed: ['auditoria', 'log', 'usuario', 'acao', 'data', 'hora'],
            forbidden: ['estoque', 'produto', 'cliente'],
            containers: ['#sistema-auditoria']
        },
        'configuracoes': {
            allowed: ['configuracao', 'perfil', 'logo', 'email', 'senha', 'tema'],
            forbidden: ['estoque', 'produto', 'cliente', 'agendamento'],
            containers: ['#configuracoes-form']
        },
        'avaliacoes': {
            allowed: ['avaliacao', 'nota', 'estrela', 'comentario', 'feedback', 'servico'],
            forbidden: ['estoque', 'produto', 'financeiro'],
            containers: ['#avaliacoes-lista']
        }
    };

    /**
     * Render Controller
     */
    const RenderController = {

        /**
         * Inicializar
         */
        init: function() {
            console.log('🎨 RenderController: Inicializando...');
            this.setupSectionGuards();
            console.log('✅ RenderController: Pronto!');
        },

        /**
         * Verificar se conteúdo é permitido em uma seção
         */
        isContentAllowed: function(sectionId, content) {
            const config = SECTION_CONTENT_MAP[sectionId];
            if (!config) {
                console.warn(`⚠️ RenderController: Seção ${sectionId} não configurada`);
                return true; // Permitir se não configurado
            }

            const contentLower = content.toLowerCase();

            // Verificar se está na lista proibida
            const isForbidden = config.forbidden.some(keyword =>
                contentLower.includes(keyword)
            );

            if (isForbidden) {
                console.warn(`❌ RenderController: Conteúdo "${content}" proibido em ${sectionId}`);
                return false;
            }

            return true;
        },

        /**
         * Validar elemento
         */
        validateElement: function(element, sectionId) {
            if (!element || !sectionId) return false;

            const config = SECTION_CONTENT_MAP[sectionId];
            if (!config) return true;

            // Coletar informações do elemento
            const id = element.id || '';
            const className = element.className || '';
            const text = element.textContent || '';

            const combinedContent = `${id} ${className} ${text}`.toLowerCase();

            // Verificar palavras proibidas
            const hasForbidden = config.forbidden.some(keyword =>
                combinedContent.includes(keyword)
            );

            if (hasForbidden) {
                console.warn(`❌ RenderController: Elemento proibido em ${sectionId}:`, element);
                return false;
            }

            return true;
        },

        /**
         * Limpar seção de conteúdo indevido
         */
        cleanSection: function(sectionId) {
            const section = document.getElementById(sectionId);
            if (!section) return;

            const config = SECTION_CONTENT_MAP[sectionId];
            if (!config) return;

            console.log(`🧹 RenderController: Limpando ${sectionId}...`);

            let removed = 0;

            // Procurar e remover elementos proibidos
            const allElements = section.querySelectorAll('*');

            allElements.forEach(element => {
                // Não remover containers principais
                const isContainer = config.containers.some(c =>
                    element.matches(c)
                );
                if (isContainer) return;

                // Verificar se elemento é válido
                if (!this.validateElement(element, sectionId)) {
                    element.remove();
                    removed++;
                }
            });

            if (removed > 0) {
                console.log(`✅ RenderController: ${removed} elementos removidos de ${sectionId}`);
            }
        },

        /**
         * Configurar guards de seção
         */
        setupSectionGuards: function() {
            Object.keys(SECTION_CONTENT_MAP).forEach(sectionId => {
                const section = document.getElementById(sectionId);
                if (!section) return;

                // Observador de mutação para detectar inserções indevidas
                const observer = new MutationObserver((mutations) => {
                    let needsClean = false;

                    mutations.forEach(mutation => {
                        mutation.addedNodes.forEach(node => {
                            if (node.nodeType === 1) { // Element
                                if (!this.validateElement(node, sectionId)) {
                                    needsClean = true;
                                }
                            }
                        });
                    });

                    if (needsClean) {
                        // Limpar após um pequeno delay
                        setTimeout(() => {
                            this.cleanSection(sectionId);
                        }, 100);
                    }
                });

                observer.observe(section, {
                    childList: true,
                    subtree: true
                });

                console.log(`🛡️ RenderController: Guard ativo em ${sectionId}`);
            });
        },

        /**
         * Renderizar seção de forma segura
         */
        safeRender: function(sectionId, renderFunction) {
            console.log(`🎨 RenderController: Renderizando ${sectionId}...`);

            // Verificar se pode carregar
            if (!window.StateManager.canLoad(sectionId)) {
                console.warn(`⚠️ RenderController: ${sectionId} bloqueado pelo StateManager`);
                return Promise.reject('Carregamento bloqueado');
            }

            // Marcar como carregando
            window.StateManager.setLoading(sectionId, true);

            // Executar renderização
            return Promise.resolve()
                .then(() => renderFunction())
                .then(result => {
                    // Limpar conteúdo indevido após renderizar
                    this.cleanSection(sectionId);
                    window.StateManager.setLoading(sectionId, false);
                    console.log(`✅ RenderController: ${sectionId} renderizado com sucesso`);
                    return result;
                })
                .catch(error => {
                    window.StateManager.setLoading(sectionId, false);
                    console.error(`❌ RenderController: Erro ao renderizar ${sectionId}:`, error);
                    throw error;
                });
        },

        /**
         * Limpar todas as seções
         */
        cleanAll: function() {
            console.log('🧹 RenderController: Limpando todas as seções...');
            Object.keys(SECTION_CONTENT_MAP).forEach(sectionId => {
                this.cleanSection(sectionId);
            });
        },

        /**
         * Obter configuração de uma seção
         */
        getSectionConfig: function(sectionId) {
            return SECTION_CONTENT_MAP[sectionId] || null;
        },

        /**
         * Debug: mostrar configurações
         */
        debug: function() {
            console.log('📊 RENDER CONTROLLER CONFIG:');
            Object.keys(SECTION_CONTENT_MAP).forEach(sectionId => {
                console.log(`  ${sectionId}:`, SECTION_CONTENT_MAP[sectionId]);
            });
        }
    };

    // Expor globalmente
    window.RenderController = RenderController;
    window.SECTION_CONTENT_MAP = SECTION_CONTENT_MAP;

    // Auto-inicializar
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => RenderController.init());
    } else {
        RenderController.init();
    }

    console.log('✅ Render Controller carregado');

})();
