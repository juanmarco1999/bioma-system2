/**
 * BIOMA v3.7 - Melhorias e Correções
 * Sistema de Auto-Atualização + Correções Críticas
 */

console.log('🚀 BIOMA v3.7 - Melhorias carregadas');

// ============================================================================
// SISTEMA DE AUTO-ATUALIZAÇÃO GLOBAL
// ============================================================================

let autoRefreshInterval = null;
let autoRefreshEnabled = true;
const REFRESH_INTERVAL = 30000; // 30 segundos

function initAutoRefresh() {
    console.log('🔄 Sistema de auto-atualização iniciado (30s)');

    autoRefreshInterval = setInterval(() => {
        if (!autoRefreshEnabled) return;

        const activeSection = document.querySelector('.content-section.active');
        if (!activeSection) return;

        const sectionId = activeSection.id;
        console.log(`🔄 Auto-refresh: ${sectionId}`);

        switch(sectionId) {
            case 'section-dashboard':
                if (typeof loadDashboard === 'function') loadDashboard();
                break;
            case 'section-orcamentos':
                if (typeof loadOrcamentos === 'function') loadOrcamentos();
                break;
            case 'section-agendamentos':
                refreshAgendamentos();
                break;
            case 'section-comissoes':
                refreshComissoes();
                break;
            case 'section-financeiro':
                refreshFinanceiro();
                break;
            case 'section-estoque':
                refreshEstoque();
                break;
        }
    }, REFRESH_INTERVAL);
}

function toggleAutoRefresh(enabled) {
    autoRefreshEnabled = enabled;
    const status = enabled ? 'ATIVADA' : 'PAUSADA';
    console.log(`🔄 Auto-atualização ${status}`);
}

// Iniciar quando página carregar
window.addEventListener('load', initAutoRefresh);

// ============================================================================
// CORREÇÃO: Coluna Pagamento [object Object]
// ============================================================================

function formatarPagamento(orcamento) {
    // Tentar diferentes formatos de dados
    if (typeof orcamento.forma_pagamento === 'string') {
        return orcamento.forma_pagamento;
    }

    if (orcamento.pagamento) {
        if (typeof orcamento.pagamento === 'string') {
            return orcamento.pagamento;
        }
        if (orcamento.pagamento.forma) {
            return orcamento.pagamento.forma;
        }
        if (orcamento.pagamento.tipo) {
            return orcamento.pagamento.tipo;
        }
    }

    return 'Não especificado';
}

// ============================================================================
// MELHORAR MODALS DE VISUALIZAÇÃO
// ============================================================================

function mostrarDetalhesOrcamentoCompleto(orcamentoId) {
    fetch(`/api/orcamentos/${orcamentoId}`, {credentials: 'include'})
        .then(res => res.json())
        .then(data => {
            if (!data.success) {
                Swal.fire('Erro', data.message || 'Erro ao carregar orçamento', 'error');
                return;
            }

            const orc = data.orcamento;

            const modalHtml = `
                <div class="modal-detalhes-completo" style="text-align: left; max-height: 80vh; overflow-y: auto;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 3px solid var(--primary);">
                        <h2 style="margin: 0; color: var(--primary);">
                            <i class="bi bi-file-earmark-text"></i> Orçamento #${orc.numero || orc._id}
                        </h2>
                        <span class="badge ${getBadgeClass(orc.status)}" style="font-size: 1rem; padding: 8px 16px;">
                            ${orc.status?.toUpperCase()}
                        </span>
                    </div>

                    <!-- Cliente -->
                    <div class="secao-detalhes" style="margin-bottom: 25px; padding: 20px; background: var(--bg-card); border-radius: 15px; border: 2px solid var(--border-color);">
                        <h3 style="margin-top: 0; color: var(--primary); display: flex; align-items: center; gap: 10px;">
                            <i class="bi bi-person-circle"></i> Cliente
                        </h3>
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                            <p><strong>Nome:</strong> ${orc.cliente_nome || 'N/A'}</p>
                            <p><strong>CPF:</strong> ${orc.cliente_cpf || 'N/A'}</p>
                            <p><strong>Telefone:</strong> ${orc.cliente_telefone || 'N/A'}</p>
                            <p><strong>Email:</strong> ${orc.cliente_email || 'N/A'}</p>
                        </div>
                    </div>

                    <!-- Produtos -->
                    ${orc.produtos && orc.produtos.length > 0 ? `
                    <div class="secao-detalhes" style="margin-bottom: 25px; padding: 20px; background: var(--bg-card); border-radius: 15px; border: 2px solid var(--border-color);">
                        <h3 style="margin-top: 0; color: var(--primary); display: flex; align-items: center; gap: 10px;">
                            <i class="bi bi-box-seam"></i> Produtos (${orc.produtos.length})
                        </h3>
                        <table style="width: 100%; margin-top: 15px; font-size: 0.9rem;">
                            <thead>
                                <tr style="background: var(--primary); color: white;">
                                    <th style="padding: 10px; text-align: left;">Produto</th>
                                    <th style="padding: 10px; text-align: center;">Qtd</th>
                                    <th style="padding: 10px; text-align: right;">Preço Unit.</th>
                                    <th style="padding: 10px; text-align: right;">Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${orc.produtos.map(p => `
                                    <tr style="border-bottom: 1px solid var(--border-color);">
                                        <td style="padding: 10px;">${p.nome || p.produto_nome || 'Produto'}</td>
                                        <td style="padding: 10px; text-align: center;">${p.quantidade || 1}</td>
                                        <td style="padding: 10px; text-align: right;">${formatarMoeda(p.preco_unitario || 0)}</td>
                                        <td style="padding: 10px; text-align: right; font-weight: bold;">${formatarMoeda(p.total || 0)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                    ` : ''}

                    <!-- Serviços -->
                    ${orc.servicos && orc.servicos.length > 0 ? `
                    <div class="secao-detalhes" style="margin-bottom: 25px; padding: 20px; background: var(--bg-card); border-radius: 15px; border: 2px solid var(--border-color);">
                        <h3 style="margin-top: 0; color: var(--primary); display: flex; align-items: center; gap: 10px;">
                            <i class="bi bi-scissors"></i> Serviços (${orc.servicos.length})
                        </h3>
                        <table style="width: 100%; margin-top: 15px; font-size: 0.9rem;">
                            <thead>
                                <tr style="background: var(--primary); color: white;">
                                    <th style="padding: 10px; text-align: left;">Serviço</th>
                                    <th style="padding: 10px; text-align: left;">Profissional</th>
                                    <th style="padding: 10px; text-align: right;">Valor</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${orc.servicos.map(s => `
                                    <tr style="border-bottom: 1px solid var(--border-color);">
                                        <td style="padding: 10px;">${s.nome || s.servico_nome || 'Serviço'}</td>
                                        <td style="padding: 10px;">${s.profissional_nome || 'N/A'}</td>
                                        <td style="padding: 10px; text-align: right; font-weight: bold;">${formatarMoeda(s.preco || s.valor || 0)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                    ` : ''}

                    <!-- Resumo Financeiro -->
                    <div class="secao-detalhes" style="margin-bottom: 25px; padding: 20px; background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: white; border-radius: 15px;">
                        <h3 style="margin-top: 0; display: flex; align-items: center; gap: 10px;">
                            <i class="bi bi-cash-stack"></i> Resumo Financeiro
                        </h3>
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-top: 15px;">
                            <p><strong>Subtotal:</strong> ${formatarMoeda(orc.subtotal || orc.valor_total || 0)}</p>
                            <p><strong>Desconto:</strong> ${orc.desconto_percentual || 0}% (${formatarMoeda(orc.desconto_valor || 0)})</p>
                            <p><strong>Forma de Pagamento:</strong> ${formatarPagamento(orc)}</p>
                            <p style="font-size: 1.3rem;"><strong>TOTAL:</strong> <span style="font-size: 1.5rem; font-weight: 900;">${formatarMoeda(orc.valor_total || 0)}</span></p>
                        </div>
                    </div>

                    <!-- Ações -->
                    <div style="display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; margin-top: 25px;">
                        <button class="btn btn-primary" onclick="enviarPorEmail('${orcamentoId}', 'orcamento')">
                            <i class="bi bi-envelope"></i> Enviar por E-mail
                        </button>
                        <button class="btn btn-success" onclick="enviarPorWhatsApp('${orcamentoId}', 'orcamento')">
                            <i class="bi bi-whatsapp"></i> Enviar WhatsApp
                        </button>
                        ${orc.status === 'pendente' ? `
                        <button class="btn btn-success" onclick="aprovarOrcamento('${orcamentoId}')">
                            <i class="bi bi-check-circle"></i> Aprovar
                        </button>
                        <button class="btn btn-danger" onclick="rejeitarOrcamento('${orcamentoId}')">
                            <i class="bi bi-x-circle"></i> Rejeitar
                        </button>
                        ` : ''}
                    </div>
                </div>
            `;

            Swal.fire({
                html: modalHtml,
                width: '1000px',
                showConfirmButton: false,
                showCloseButton: true
            });
        })
        .catch(error => {
            console.error('Erro ao carregar detalhes:', error);
            Swal.fire('Erro', 'Erro ao carregar detalhes do orçamento', 'error');
        });
}

// ============================================================================
// SISTEMA DE NOTIFICAÇÕES (E-mail + WhatsApp)
// ============================================================================

async function enviarPorEmail(id, tipo) {
    try {
        const res = await fetch(`/api/notificacoes/email/${tipo}/${id}`, {
            method: 'POST',
            credentials: 'include'
        });

        const data = await res.json();

        if (data.success) {
            Swal.fire('Sucesso!', 'E-mail enviado com sucesso!', 'success');
        } else {
            Swal.fire('Erro', data.message || 'Erro ao enviar e-mail', 'error');
        }
    } catch (error) {
        console.error('Erro:', error);
        Swal.fire('Erro', 'Erro ao enviar e-mail', 'error');
    }
}

async function enviarPorWhatsApp(id, tipo) {
    try {
        const res = await fetch(`/api/notificacoes/whatsapp/${tipo}/${id}`, {
            method: 'POST',
            credentials: 'include'
        });

        const data = await res.json();

        if (data.success && data.url) {
            // Abrir WhatsApp em nova aba
            window.open(data.url, '_blank');
            Swal.fire('WhatsApp', 'Link aberto em nova aba!', 'success');
        } else {
            Swal.fire('Erro', data.message || 'Erro ao gerar link do WhatsApp', 'error');
        }
    } catch (error) {
        console.error('Erro:', error);
        Swal.fire('Erro', 'Erro ao enviar WhatsApp', 'error');
    }
}

// ============================================================================
// REFRESH FUNCTIONS PARA AUTO-ATUALIZAÇÃO
// ============================================================================

function refreshAgendamentos() {
    const activeSubTab = document.querySelector('.sub-tab-btn.active');
    if (!activeSubTab) return;

    const subTabText = activeSubTab.textContent.trim().toLowerCase();

    if (subTabText.includes('hoje')) {
        if (typeof loadAgendamentosHoje === 'function') loadAgendamentosHoje();
    } else if (subTabText.includes('semana')) {
        if (typeof loadAgendamentosSemana === 'function') loadAgendamentosSemana();
    } else if (subTabText.includes('mês')) {
        if (typeof loadAgendamentosMes === 'function') loadAgendamentosMes();
    } else if (subTabText.includes('todos')) {
        if (typeof loadAgendamentosTodos === 'function') loadAgendamentosTodos();
    }
}

function refreshComissoes() {
    if (typeof loadComissoesPendentes === 'function') {
        loadComissoesPendentes();
    }
    if (typeof loadComissoesPagas === 'function') {
        loadComissoesPagas();
    }
}

function refreshFinanceiro() {
    const activeFinTab = document.querySelector('#section-financeiro .sub-tab-btn.active');
    if (!activeFinTab) return;

    const tabText = activeFinTab.textContent.trim().toLowerCase();

    if (tabText.includes('resumo')) {
        if (typeof loadFinanceiroResumo === 'function') loadFinanceiroResumo();
    } else if (tabText.includes('receitas')) {
        if (typeof loadReceitas === 'function') loadReceitas();
    } else if (tabText.includes('despesas')) {
        if (typeof loadDespesas === 'function') loadDespesas();
    } else if (tabText.includes('fluxo')) {
        if (typeof loadFluxoCaixa === 'function') loadFluxoCaixa();
    }
}

function refreshEstoque() {
    const activeEstTab = document.querySelector('#section-estoque .sub-tab-btn.active');
    if (!activeEstTab) return;

    const tabText = activeEstTab.textContent.trim().toLowerCase();

    if (tabText.includes('visão geral') || tabText.includes('visao geral')) {
        if (typeof loadEstoqueResumo === 'function') loadEstoqueResumo();
    } else if (tabText.includes('produtos')) {
        if (typeof loadProdutosEstoque === 'function') loadProdutosEstoque();
    } else if (tabText.includes('movimentações') || tabText.includes('movimentacoes')) {
        if (typeof loadEstoqueMovimentacoes === 'function') loadEstoqueMovimentacoes();
    }
}

// ============================================================================
// HELPERS GLOBAIS
// ============================================================================

function getBadgeClass(status) {
    const classes = {
        'pendente': 'warning',
        'aprovado': 'success',
        'rejeitado': 'danger',
        'cancelado': 'danger',
        'confirmado': 'success',
        'pago': 'success',
        'em_aberto': 'warning',
        'vencido': 'danger',
        'ativo': 'success',
        'inativo': 'secondary'
    };

    return `badge ${classes[status] || 'secondary'}`;
}

// Sobrescrever função global de formatarMoeda se não existir
if (typeof formatarMoeda !== 'function') {
    window.formatarMoeda = function(valor) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(valor || 0);
    };
}

// Sobrescrever função global de formatarData se não existir
if (typeof formatarData !== 'function') {
    window.formatarData = function(data) {
        if (!data) return 'N/A';
        const d = new Date(data);
        return d.toLocaleDateString('pt-BR');
    };
}

console.log('✅ Melhorias v3.7 carregadas com sucesso!');
