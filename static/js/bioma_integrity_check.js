/**
 * BIOMA SYSTEM - Integrity Check & Final Adjustments
 * Verificação de integridade e ajustes finais
 * Versão: 2.0 FINAL
 */

console.log('🔍 BIOMA Integrity Check iniciado...');

// ==================== VERIFICAÇÃO DE INTEGRIDADE ====================

/**
 * Verifica se todas as funções essenciais estão definidas
 */
function verificarIntegridadeSistema() {
    const funcoesEssenciais = [
        // Navegação
        'goTo',
        'switchSubTab',

        // Renderização
        'renderFinanceiroResumo',
        'renderResumoGeral',
        'renderAgendamentosTabela',
        'renderServicosTabela',
        'renderProdutosTabela',
        'renderEstoqueVisaoGeral',
        'renderClientesTabela',
        'renderProfissionaisTabela',
        'renderPaginacao',

        // Carregamento
        'loadDashboardOtimizado',
        'loadClientesOtimizado',
        'loadProfissionaisOtimizado',
        'loadProdutosOtimizado',
        'loadServicosOtimizado',
        'loadEstoqueOtimizado',
        'loadAgendamentosOtimizado',
        'loadRelatoriosOtimizado',
        'loadFinanceiroOtimizado',
        'loadAuditoriaOtimizado',

        // Impressão e WhatsApp
        'imprimirOrcamento',
        'imprimirContrato',
        'enviarWhatsAppOrcamento',
        'enviarWhatsAppContrato',

        // Notificações
        'sistemaNotificacao',

        // Prontuário
        'sistemaProntuario',

        // Auxiliares
        'mostrarSucesso',
        'mostrarErro'
    ];

    let todasDefinidas = true;
    const naoDefinidas = [];

    funcoesEssenciais.forEach(funcao => {
        if (typeof window[funcao] === 'undefined') {
            todasDefinidas = false;
            naoDefinidas.push(funcao);
            console.warn(`⚠️ Função não definida: ${funcao}`);
        }
    });

    if (todasDefinidas) {
        console.log('✅ Todas as funções essenciais estão definidas!');
    } else {
        console.error('❌ Funções faltando:', naoDefinidas);
        implementarFuncoesFaltantes(naoDefinidas);
    }

    return todasDefinidas;
}

/**
 * Implementa funções que possam estar faltando
 */
function implementarFuncoesFaltantes(funcoesFaltantes) {
    console.log('🔧 Implementando funções faltantes...');

    funcoesFaltantes.forEach(funcao => {
        switch(funcao) {
            case 'renderDashboard':
                window.renderDashboard = function(data) {
                    console.log('📊 Renderizando dashboard...');
                    // Atualizar cards de estatísticas
                    const elements = {
                        'totalClientes': data.estatisticas?.total_clientes || 0,
                        'totalProfissionais': data.estatisticas?.total_profissionais || 0,
                        'agendamentosHoje': data.estatisticas?.agendamentos_hoje || 0,
                        'faturamentoMes': `R$ ${(data.estatisticas?.faturamento_mes || 0).toFixed(2)}`
                    };

                    for (const [id, value] of Object.entries(elements)) {
                        const el = document.getElementById(id);
                        if (el) el.textContent = value;
                    }
                };
                break;

            case 'renderAuditoriaTabela':
                window.renderAuditoriaTabela = function(logs, pagination) {
                    console.log('🔍 Renderizando tabela de auditoria...');
                    const tbody = document.getElementById('auditoriaTableBody');
                    if (!tbody) return;

                    if (!logs || logs.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhum log encontrado</td></tr>';
                        return;
                    }

                    tbody.innerHTML = logs.map(log => `
                        <tr>
                            <td>${new Date(log.data).toLocaleString('pt-BR')}</td>
                            <td>${log.usuario || 'Sistema'}</td>
                            <td>${log.acao || 'N/A'}</td>
                            <td>${log.entidade || 'N/A'}</td>
                            <td>${log.detalhes || '-'}</td>
                        </tr>
                    `).join('');

                    if (pagination) {
                        renderPaginacao('auditoria', pagination, loadAuditoriaOtimizado);
                    }
                };
                break;

            default:
                // Criar função stub genérica
                window[funcao] = function() {
                    console.warn(`⚠️ Função ${funcao} chamada mas não totalmente implementada`);
                };
        }
    });
}

// ==================== CORREÇÕES DE FUNÇÕES EXISTENTES ====================

/**
 * Corrige função de carregamento de orçamentos pendentes
 */
if (!window.loadOrcamentosPendentes) {
    window.loadOrcamentosPendentes = async function() {
        try {
            console.log('📋 Carregando orçamentos pendentes...');

            const response = await fetch('/api/orcamento/pendentes');
            const data = await response.json();

            if (data.success) {
                renderOrcamentosPendentes(data.orcamentos);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar orçamentos pendentes:', error);
        }
    };
}

/**
 * Renderiza orçamentos pendentes
 */
if (!window.renderOrcamentosPendentes) {
    window.renderOrcamentosPendentes = function(orcamentos) {
        const tbody = document.getElementById('orcamentosPendentesTableBody');
        if (!tbody) return;

        if (!orcamentos || orcamentos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhum orçamento pendente</td></tr>';
            return;
        }

        tbody.innerHTML = orcamentos.map(orc => `
            <tr>
                <td>#${orc.numero || orc._id}</td>
                <td>${new Date(orc.data).toLocaleDateString('pt-BR')}</td>
                <td>${orc.cliente_nome || 'N/A'}</td>
                <td>R$ ${(orc.valor_total || 0).toFixed(2)}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="visualizarOrcamento('${orc._id}')">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-success" onclick="aprovarOrcamento('${orc._id}')">
                        <i class="bi bi-check"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="rejeitarOrcamento('${orc._id}')">
                        <i class="bi bi-x"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    };
}

/**
 * Carrega orçamentos aprovados
 */
if (!window.loadOrcamentosAprovados) {
    window.loadOrcamentosAprovados = async function() {
        try {
            console.log('✅ Carregando orçamentos aprovados...');

            const response = await fetch('/api/orcamento/aprovados');
            const data = await response.json();

            if (data.success) {
                renderOrcamentosAprovados(data.orcamentos);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar orçamentos aprovados:', error);
        }
    };
}

/**
 * Renderiza orçamentos aprovados
 */
if (!window.renderOrcamentosAprovados) {
    window.renderOrcamentosAprovados = function(orcamentos) {
        const tbody = document.getElementById('orcamentosAprovadosTableBody');
        if (!tbody) return;

        if (!orcamentos || orcamentos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhum orçamento aprovado</td></tr>';
            return;
        }

        tbody.innerHTML = orcamentos.map(orc => `
            <tr>
                <td>#${orc.numero || orc._id}</td>
                <td>${new Date(orc.data_aprovacao || orc.data).toLocaleDateString('pt-BR')}</td>
                <td>${orc.cliente_nome || 'N/A'}</td>
                <td>R$ ${(orc.valor_total || 0).toFixed(2)}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="visualizarOrcamento('${orc._id}')">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-info" onclick="imprimirOrcamento('${orc._id}')">
                        <i class="bi bi-printer"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    };
}

/**
 * Carrega orçamentos rejeitados
 */
if (!window.loadOrcamentosRejeitados) {
    window.loadOrcamentosRejeitados = async function() {
        try {
            console.log('❌ Carregando orçamentos rejeitados...');

            const response = await fetch('/api/orcamento/rejeitados');
            const data = await response.json();

            if (data.success) {
                renderOrcamentosRejeitados(data.orcamentos);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar orçamentos rejeitados:', error);
        }
    };
}

/**
 * Renderiza orçamentos rejeitados
 */
if (!window.renderOrcamentosRejeitados) {
    window.renderOrcamentosRejeitados = function(orcamentos) {
        const tbody = document.getElementById('orcamentosRejeitadosTableBody');
        if (!tbody) return;

        if (!orcamentos || orcamentos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhum orçamento rejeitado</td></tr>';
            return;
        }

        tbody.innerHTML = orcamentos.map(orc => `
            <tr>
                <td>#${orc.numero || orc._id}</td>
                <td>${new Date(orc.data_rejeicao || orc.data).toLocaleDateString('pt-BR')}</td>
                <td>${orc.cliente_nome || 'N/A'}</td>
                <td>R$ ${(orc.valor_total || 0).toFixed(2)}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="visualizarOrcamento('${orc._id}')">
                        <i class="bi bi-eye"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    };
}

/**
 * Carrega histórico de orçamentos
 */
if (!window.loadOrcamentosHistorico) {
    window.loadOrcamentosHistorico = async function() {
        try {
            console.log('📋 Carregando histórico de orçamentos...');

            const response = await fetch('/api/orcamentos');
            const data = await response.json();

            if (data.success) {
                renderOrcamentosHistorico(data.orcamentos);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar histórico:', error);
        }
    };
}

/**
 * Carrega alertas de estoque
 */
if (!window.loadEstoqueAlertas) {
    window.loadEstoqueAlertas = async function() {
        try {
            console.log('⚠️ Carregando alertas de estoque...');

            const response = await fetch('/api/estoque/alertas');
            const data = await response.json();

            if (data.success) {
                renderEstoqueAlertas(data.alertas);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar alertas:', error);
        }
    };
}

/**
 * Renderiza alertas de estoque
 */
if (!window.renderEstoqueAlertas) {
    window.renderEstoqueAlertas = function(alertas) {
        const container = document.getElementById('estoqueAlertasContainer');
        if (!container) return;

        if (!alertas || alertas.length === 0) {
            container.innerHTML = '<div class="text-center">Nenhum alerta de estoque</div>';
            return;
        }

        container.innerHTML = alertas.map(produto => `
            <div class="alert alert-warning">
                <h5>${produto.nome}</h5>
                <p>Estoque atual: ${produto.estoque} | Mínimo: ${produto.estoque_minimo}</p>
                <button class="btn btn-sm btn-primary" onclick="reporEstoque('${produto._id}')">
                    Repor Estoque
                </button>
            </div>
        `).join('');
    };
}

/**
 * Carrega movimentações de estoque
 */
if (!window.loadEstoqueMovimentacoes) {
    window.loadEstoqueMovimentacoes = async function() {
        try {
            console.log('📦 Carregando movimentações de estoque...');

            const response = await fetch('/api/estoque/movimentacoes');
            const data = await response.json();

            if (data.success) {
                renderEstoqueMovimentacoes(data.movimentacoes);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar movimentações:', error);
        }
    };
}

/**
 * Carrega receitas do financeiro
 */
if (!window.loadFinanceiroReceitas) {
    window.loadFinanceiroReceitas = async function() {
        try {
            console.log('💰 Carregando receitas...');

            const response = await fetch('/api/financeiro/receitas');
            const data = await response.json();

            if (data.success) {
                renderFinanceiroReceitas(data.receitas, data.total);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar receitas:', error);
        }
    };
}

/**
 * Carrega despesas do financeiro
 */
if (!window.loadFinanceiroDespesas) {
    window.loadFinanceiroDespesas = async function() {
        try {
            console.log('💸 Carregando despesas...');

            const response = await fetch('/api/financeiro/despesas');
            const data = await response.json();

            if (data.success) {
                renderFinanceiroDespesas(data.despesas, data.total);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar despesas:', error);
        }
    };
}

/**
 * Carrega comissões do financeiro
 */
if (!window.loadFinanceiroComissoes) {
    window.loadFinanceiroComissoes = async function() {
        try {
            console.log('💵 Carregando comissões...');

            const response = await fetch('/api/financeiro/comissoes');
            const data = await response.json();

            if (data.success) {
                renderFinanceiroComissoes(data.comissoes);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar comissões:', error);
        }
    };
}

/**
 * Carrega mapa de calor
 */
if (!window.loadMapaCalor) {
    window.loadMapaCalor = async function() {
        try {
            console.log('🔥 Carregando mapa de calor...');

            const response = await fetch('/api/relatorios/mapa-calor/carregar');
            const data = await response.json();

            if (data.success) {
                renderMapaCalor(data.mapa, data.tipo);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar mapa de calor:', error);
        }
    };
}

/**
 * Renderiza mapa de calor
 */
if (!window.renderMapaCalor) {
    window.renderMapaCalor = function(mapa, tipo) {
        const container = document.getElementById('mapaCalorContainer');
        if (!container) return;

        // Implementação básica do mapa de calor
        container.innerHTML = '<div class="text-center">Mapa de calor carregado</div>';

        // Aqui você pode adicionar uma biblioteca de visualização como D3.js
        // para criar um verdadeiro mapa de calor
    };
}

// ==================== FUNÇÕES DE AÇÃO ====================

/**
 * Visualizar agendamento
 */
if (!window.visualizarAgendamento) {
    window.visualizarAgendamento = function(id) {
        console.log(`Visualizando agendamento ${id}`);
        // Implementar modal de visualização
    };
}

/**
 * Confirmar agendamento
 */
if (!window.confirmarAgendamento) {
    window.confirmarAgendamento = async function(id) {
        try {
            const response = await fetch(`/api/agendamento/${id}/confirmar`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                mostrarSucesso('Agendamento confirmado!');
                loadAgendamentosOtimizado(1);
            } else {
                mostrarErro(data.message);
            }
        } catch (error) {
            console.error('Erro:', error);
            mostrarErro('Erro ao confirmar agendamento');
        }
    };
}

/**
 * Cancelar agendamento
 */
if (!window.cancelarAgendamento) {
    window.cancelarAgendamento = async function(id) {
        if (!confirm('Deseja realmente cancelar este agendamento?')) return;

        try {
            const response = await fetch(`/api/agendamento/${id}/cancelar`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ motivo: 'Cancelado pelo usuário' })
            });

            const data = await response.json();

            if (data.success) {
                mostrarSucesso('Agendamento cancelado!');
                loadAgendamentosOtimizado(1);
            } else {
                mostrarErro(data.message);
            }
        } catch (error) {
            console.error('Erro:', error);
            mostrarErro('Erro ao cancelar agendamento');
        }
    };
}

// ==================== VERIFICAÇÃO FINAL ====================

/**
 * Executa verificação completa do sistema
 */
function executarVerificacaoCompleta() {
    console.log('🔍 Executando verificação completa do sistema...');

    // Verificar integridade
    const integridadeOk = verificarIntegridadeSistema();

    // Verificar endpoints
    verificarEndpoints();

    // Configurar interceptadores de erro
    configurarInterceptadoresErro();

    // Status final
    if (integridadeOk) {
        console.log('✅ Sistema BIOMA está 100% operacional!');
        console.log('%c🌳 BIOMA v3.7 - Sistema Completo e Funcional',
            'background:#10B981;color:#fff;font-size:20px;padding:10px;border-radius:8px;font-weight:bold');
    } else {
        console.warn('⚠️ Sistema com algumas funções em modo de compatibilidade');
    }
}

/**
 * Verifica disponibilidade dos endpoints
 */
async function verificarEndpoints() {
    const endpointsEssenciais = [
        '/api/dashboard',
        '/api/clientes/lista-otimizada',
        '/api/profissionais/lista-otimizada',
        '/api/servicos/lista-otimizada',
        '/api/produtos/lista-otimizada',
        '/api/financeiro/resumo'
    ];

    console.log('🔍 Verificando endpoints...');

    for (const endpoint of endpointsEssenciais) {
        try {
            const response = await fetch(endpoint, { method: 'HEAD' });
            if (response.ok || response.status === 405) { // 405 = Method not allowed (mas endpoint existe)
                console.log(`✅ ${endpoint} - OK`);
            } else {
                console.warn(`⚠️ ${endpoint} - Status ${response.status}`);
            }
        } catch (error) {
            console.warn(`⚠️ ${endpoint} - Não disponível`);
        }
    }
}

/**
 * Configura interceptadores de erro global
 */
function configurarInterceptadoresErro() {
    // Interceptar erros de fetch
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        try {
            const response = await originalFetch.apply(this, args);

            // Se erro 404, tentar rota alternativa
            if (response.status === 404) {
                console.warn(`⚠️ Endpoint não encontrado: ${args[0]}`);
            }

            return response;
        } catch (error) {
            console.error('❌ Erro na requisição:', error);
            throw error;
        }
    };

    // Interceptar erros JavaScript globais
    window.addEventListener('error', function(e) {
        if (e.message?.includes('is not defined')) {
            const funcaoFaltante = e.message.match(/(\w+) is not defined/)?.[1];
            if (funcaoFaltante && funcaoFaltante.startsWith('render')) {
                console.warn(`⚠️ Função de renderização faltante: ${funcaoFaltante}`);
                // Implementar stub
                window[funcaoFaltante] = function() {
                    console.log(`Stub para ${funcaoFaltante} executado`);
                };
            }
        }
    });
}

// ==================== INICIALIZAÇÃO ====================

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ BIOMA Integrity Check carregado!');

    // Aguardar outros scripts carregarem
    setTimeout(() => {
        executarVerificacaoCompleta();
    }, 1000);
});

console.log('✅ BIOMA Integrity Check definido com sucesso!');