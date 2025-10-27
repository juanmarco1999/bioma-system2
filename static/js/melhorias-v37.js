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

// ============================================================================
// FUNÇÕES FALTANTES - CORREÇÃO DE ERROS
// ============================================================================

// Função showModalComissao - Nova Regra de Comissão
window.showModalComissao = function() {
    Swal.fire({
        title: 'Nova Regra de Comissão',
        html: `
            <div style="text-align: left;">
                <div class="form-group">
                    <label>Tipo de Regra</label>
                    <select id="tipo_regra" class="form-control">
                        <option value="profissional">Por Profissional</option>
                        <option value="servico">Por Serviço</option>
                        <option value="categoria">Por Categoria</option>
                        <option value="global">Global (Todos)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Percentual de Comissão (%)</label>
                    <input type="number" id="percentual_comissao" class="form-control" min="0" max="100" step="0.1" value="10">
                </div>
                <div class="form-group">
                    <label>Descrição</label>
                    <textarea id="descricao_comissao" class="form-control" rows="3" placeholder="Descrição da regra..."></textarea>
                </div>
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: 'Salvar Regra',
        cancelButtonText: 'Cancelar',
        width: '500px',
        preConfirm: () => {
            const tipo = document.getElementById('tipo_regra').value;
            const percentual = parseFloat(document.getElementById('percentual_comissao').value);
            const descricao = document.getElementById('descricao_comissao').value;

            if (!percentual || percentual < 0 || percentual > 100) {
                Swal.showValidationMessage('Percentual inválido (0-100%)');
                return false;
            }

            return { tipo, percentual, descricao };
        }
    }).then((result) => {
        if (result.isConfirmed) {
            // Salvar regra de comissão
            fetch('/api/comissoes/regra', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(result.value),
                credentials: 'include'
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    Swal.fire('Sucesso!', 'Regra de comissão criada', 'success');
                    if (typeof loadComissoes === 'function') loadComissoes();
                } else {
                    Swal.fire('Erro!', data.message || 'Erro ao criar regra', 'error');
                }
            })
            .catch(err => Swal.fire('Erro!', 'Erro ao salvar regra', 'error'));
        }
    });
};

// Função editarProduto - Editar Produto
window.editarProduto = function(produtoId) {
    fetch(`/api/produtos/${produtoId}`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            if (!data.success) {
                Swal.fire('Erro!', 'Produto não encontrado', 'error');
                return;
            }

            const produto = data.produto;
            Swal.fire({
                title: 'Editar Produto',
                html: `
                    <div style="text-align: left; max-height: 500px; overflow-y: auto;">
                        <div class="form-group">
                            <label>Nome do Produto *</label>
                            <input type="text" id="edit_nome" class="form-control" value="${produto.nome}" required>
                        </div>
                        <div class="form-group">
                            <label>SKU / Código</label>
                            <input type="text" id="edit_sku" class="form-control" value="${produto.sku || ''}">
                        </div>
                        <div class="form-group">
                            <label>Categoria</label>
                            <input type="text" id="edit_categoria" class="form-control" value="${produto.categoria || ''}">
                        </div>
                        <div class="form-group">
                            <label>Preço de Custo (R$)</label>
                            <input type="number" id="edit_preco_custo" class="form-control" value="${produto.preco_custo || 0}" step="0.01">
                        </div>
                        <div class="form-group">
                            <label>Preço de Venda (R$) *</label>
                            <input type="number" id="edit_preco_venda" class="form-control" value="${produto.preco_venda}" step="0.01" required>
                        </div>
                        <div class="form-group">
                            <label>Estoque Atual</label>
                            <input type="number" id="edit_estoque_atual" class="form-control" value="${produto.estoque_atual || 0}">
                        </div>
                        <div class="form-group">
                            <label>Estoque Mínimo</label>
                            <input type="number" id="edit_estoque_minimo" class="form-control" value="${produto.estoque_minimo || 0}">
                        </div>
                        <div class="form-group">
                            <label>Unidade</label>
                            <select id="edit_unidade" class="form-control">
                                <option value="un" ${produto.unidade === 'un' ? 'selected' : ''}>Unidade</option>
                                <option value="cx" ${produto.unidade === 'cx' ? 'selected' : ''}>Caixa</option>
                                <option value="kg" ${produto.unidade === 'kg' ? 'selected' : ''}>Quilograma</option>
                                <option value="l" ${produto.unidade === 'l' ? 'selected' : ''}>Litro</option>
                                <option value="m" ${produto.unidade === 'm' ? 'selected' : ''}>Metro</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Descrição</label>
                            <textarea id="edit_descricao" class="form-control" rows="3">${produto.descricao || ''}</textarea>
                        </div>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="edit_ativo" ${produto.ativo !== false ? 'checked' : ''}> Produto Ativo
                            </label>
                        </div>
                    </div>
                `,
                showCancelButton: true,
                confirmButtonText: 'Salvar Alterações',
                cancelButtonText: 'Cancelar',
                width: '600px',
                preConfirm: () => {
                    const nome = document.getElementById('edit_nome').value.trim();
                    const preco_venda = parseFloat(document.getElementById('edit_preco_venda').value);

                    if (!nome) {
                        Swal.showValidationMessage('Nome do produto é obrigatório');
                        return false;
                    }
                    if (!preco_venda || preco_venda <= 0) {
                        Swal.showValidationMessage('Preço de venda inválido');
                        return false;
                    }

                    return {
                        nome,
                        sku: document.getElementById('edit_sku').value.trim(),
                        categoria: document.getElementById('edit_categoria').value.trim(),
                        preco_custo: parseFloat(document.getElementById('edit_preco_custo').value) || 0,
                        preco_venda,
                        estoque_atual: parseInt(document.getElementById('edit_estoque_atual').value) || 0,
                        estoque_minimo: parseInt(document.getElementById('edit_estoque_minimo').value) || 0,
                        unidade: document.getElementById('edit_unidade').value,
                        descricao: document.getElementById('edit_descricao').value.trim(),
                        ativo: document.getElementById('edit_ativo').checked
                    };
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    fetch(`/api/produtos/${produtoId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(result.value),
                        credentials: 'include'
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            Swal.fire('Sucesso!', 'Produto atualizado', 'success');
                            if (typeof loadProdutos === 'function') loadProdutos();
                        } else {
                            Swal.fire('Erro!', data.message || 'Erro ao atualizar produto', 'error');
                        }
                    })
                    .catch(err => Swal.fire('Erro!', 'Erro ao salvar produto', 'error'));
                }
            });
        })
        .catch(err => Swal.fire('Erro!', 'Erro ao carregar produto', 'error'));
};

// Função editarServico - Editar Serviço
window.editarServico = function(servicoId) {
    fetch(`/api/servicos/${servicoId}`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            if (!data.success) {
                Swal.fire('Erro!', 'Serviço não encontrado', 'error');
                return;
            }

            const servico = data.servico;
            Swal.fire({
                title: 'Editar Serviço',
                html: `
                    <div style="text-align: left;">
                        <div class="form-group">
                            <label>Nome do Serviço *</label>
                            <input type="text" id="edit_nome_servico" class="form-control" value="${servico.nome}" required>
                        </div>
                        <div class="form-group">
                            <label>Categoria</label>
                            <input type="text" id="edit_categoria_servico" class="form-control" value="${servico.categoria || ''}">
                        </div>
                        <div class="form-group">
                            <label>Preço (R$) *</label>
                            <input type="number" id="edit_preco_servico" class="form-control" value="${servico.preco}" step="0.01" required>
                        </div>
                        <div class="form-group">
                            <label>Duração (minutos)</label>
                            <input type="number" id="edit_duracao" class="form-control" value="${servico.duracao || 60}">
                        </div>
                        <div class="form-group">
                            <label>Descrição</label>
                            <textarea id="edit_descricao_servico" class="form-control" rows="3">${servico.descricao || ''}</textarea>
                        </div>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="edit_ativo_servico" ${servico.ativo !== false ? 'checked' : ''}> Serviço Ativo
                            </label>
                        </div>
                    </div>
                `,
                showCancelButton: true,
                confirmButtonText: 'Salvar Alterações',
                cancelButtonText: 'Cancelar',
                width: '550px',
                preConfirm: () => {
                    const nome = document.getElementById('edit_nome_servico').value.trim();
                    const preco = parseFloat(document.getElementById('edit_preco_servico').value);

                    if (!nome) {
                        Swal.showValidationMessage('Nome do serviço é obrigatório');
                        return false;
                    }
                    if (!preco || preco <= 0) {
                        Swal.showValidationMessage('Preço inválido');
                        return false;
                    }

                    return {
                        nome,
                        categoria: document.getElementById('edit_categoria_servico').value.trim(),
                        preco,
                        duracao: parseInt(document.getElementById('edit_duracao').value) || 60,
                        descricao: document.getElementById('edit_descricao_servico').value.trim(),
                        ativo: document.getElementById('edit_ativo_servico').checked
                    };
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    fetch(`/api/servicos/${servicoId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(result.value),
                        credentials: 'include'
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            Swal.fire('Sucesso!', 'Serviço atualizado', 'success');
                            if (typeof loadServicos === 'function') loadServicos();
                        } else {
                            Swal.fire('Erro!', data.message || 'Erro ao atualizar serviço', 'error');
                        }
                    })
                    .catch(err => Swal.fire('Erro!', 'Erro ao salvar serviço', 'error'));
                }
            });
        })
        .catch(err => Swal.fire('Erro!', 'Erro ao carregar serviço', 'error'));
};

// ============================================================================
// FUNÇÕES DE NOTIFICAÇÃO PARA CONTRATOS (3.1)
// ============================================================================

// Enviar contrato por Email
window.enviarContratoEmail = async function(contratoId) {
    try {
        // Buscar dados do contrato
        const res = await fetch(`/api/orcamentos/${contratoId}`, { credentials: 'include' });
        const data = await res.json();

        if (!data.success || !data.orcamento) {
            Swal.fire('Erro', 'Contrato não encontrado', 'error');
            return;
        }

        const contrato = data.orcamento;

        // Confirmar envio de email
        const result = await Swal.fire({
            title: 'Enviar Contrato por Email',
            html: `
                <div style="text-align:left;">
                    <p><strong>Cliente:</strong> ${contrato.cliente_nome}</p>
                    <p><strong>Contrato:</strong> #${contrato.numero}</p>
                    <p><strong>Valor:</strong> R$ ${contrato.total_final.toFixed(2)}</p>
                    <br>
                    <div class="form-group">
                        <label>Email do cliente:</label>
                        <input type="email" id="emailDestino" class="form-control" value="${contrato.cliente_email || ''}" placeholder="email@exemplo.com">
                    </div>
                    <div class="form-group">
                        <label>Mensagem adicional (opcional):</label>
                        <textarea id="mensagemEmail" class="form-control" rows="3" placeholder="Digite uma mensagem personalizada..."></textarea>
                    </div>
                </div>
            `,
            showCancelButton: true,
            confirmButtonText: 'Enviar Email',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#10B981',
            width: '550px',
            preConfirm: () => {
                const email = document.getElementById('emailDestino').value.trim();
                const mensagem = document.getElementById('mensagemEmail').value.trim();

                if (!email) {
                    Swal.showValidationMessage('Email do cliente é obrigatório');
                    return false;
                }

                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(email)) {
                    Swal.showValidationMessage('Email inválido');
                    return false;
                }

                return { email, mensagem };
            }
        });

        if (result.isConfirmed) {
            // Enviar email via API
            const sendRes = await fetch(`/api/notificacoes/email/contrato/${contratoId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    destinatario: result.value.email,
                    mensagem_adicional: result.value.mensagem
                }),
                credentials: 'include'
            });

            const sendData = await sendRes.json();

            if (sendData.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Email Enviado!',
                    text: 'O contrato foi enviado com sucesso para ' + result.value.email,
                    confirmButtonColor: '#10B981'
                });
            } else {
                Swal.fire('Erro', sendData.message || 'Erro ao enviar email', 'error');
            }
        }
    } catch (err) {
        console.error('Erro ao enviar email:', err);
        Swal.fire('Erro', 'Não foi possível enviar o email', 'error');
    }
};

// Enviar contrato por WhatsApp
window.enviarContratoWhatsApp = async function(contratoId) {
    try {
        // Buscar dados do contrato
        const res = await fetch(`/api/orcamentos/${contratoId}`, { credentials: 'include' });
        const data = await res.json();

        if (!data.success || !data.orcamento) {
            Swal.fire('Erro', 'Contrato não encontrado', 'error');
            return;
        }

        const contrato = data.orcamento;

        // Confirmar envio de WhatsApp
        const result = await Swal.fire({
            title: 'Enviar Contrato por WhatsApp',
            html: `
                <div style="text-align:left;">
                    <p><strong>Cliente:</strong> ${contrato.cliente_nome}</p>
                    <p><strong>Contrato:</strong> #${contrato.numero}</p>
                    <p><strong>Valor:</strong> R$ ${contrato.total_final.toFixed(2)}</p>
                    <br>
                    <div class="form-group">
                        <label>Telefone do cliente (com DDD):</label>
                        <input type="tel" id="telefoneDestino" class="form-control" value="${contrato.cliente_telefone || ''}" placeholder="(34) 99999-9999">
                    </div>
                    <div class="alert alert-info" style="font-size:0.9rem;margin-top:15px;">
                        <i class="bi bi-info-circle"></i> Você será redirecionado para o WhatsApp Web com uma mensagem pré-preenchida.
                    </div>
                </div>
            `,
            showCancelButton: true,
            confirmButtonText: 'Abrir WhatsApp',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#25D366',
            width: '550px',
            preConfirm: () => {
                const telefone = document.getElementById('telefoneDestino').value.trim();

                if (!telefone) {
                    Swal.showValidationMessage('Telefone do cliente é obrigatório');
                    return false;
                }

                return { telefone };
            }
        });

        if (result.isConfirmed) {
            // Gerar link do WhatsApp via API
            const whatsappRes = await fetch(`/api/notificacoes/whatsapp/contrato/${contratoId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    telefone: result.value.telefone
                }),
                credentials: 'include'
            });

            const whatsappData = await whatsappRes.json();

            if (whatsappData.success && whatsappData.url) {
                // Abrir WhatsApp em nova aba
                window.open(whatsappData.url, '_blank');

                Swal.fire({
                    icon: 'success',
                    title: 'WhatsApp Aberto!',
                    text: 'A mensagem foi pré-preenchida. Revise e envie.',
                    timer: 2500,
                    showConfirmButton: false
                });
            } else {
                Swal.fire('Erro', whatsappData.message || 'Erro ao gerar link do WhatsApp', 'error');
            }
        }
    } catch (err) {
        console.error('Erro ao enviar WhatsApp:', err);
        Swal.fire('Erro', 'Não foi possível abrir o WhatsApp', 'error');
    }
};

// ============================================================================
// FUNÇÕES DE ESTOQUE - RELATÓRIOS (8.4)
// ============================================================================

// Exportar Relatório de Estoque em PDF
window.exportarRelatorioPDF = async function() {
    try {
        const tipo = document.getElementById('relatorioTipo')?.value || 'estoque';
        const dataInicio = document.getElementById('relatorioDataInicio')?.value;
        const dataFim = document.getElementById('relatorioDataFim')?.value;

        if (!dataInicio || !dataFim) {
            Swal.fire({
                icon: 'warning',
                title: 'Atenção',
                text: 'Selecione o período do relatório (Data Início e Data Fim)',
                confirmButtonColor: '#7C3AED'
            });
            return;
        }

        // Mostrar loading
        Swal.fire({
            title: 'Gerando PDF...',
            html: 'Aguarde enquanto o relatório é gerado',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        // Chamar API do backend para gerar PDF
        const params = new URLSearchParams({
            tipo,
            data_inicio: dataInicio,
            data_fim: dataFim
        });

        const response = await fetch(`/api/estoque/relatorio/pdf?${params}`, {
            method: 'GET',
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Erro ao gerar PDF');
        }

        // Baixar o PDF
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `estoque_${tipo}_${dataInicio}_${dataFim}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        Swal.fire({
            icon: 'success',
            title: 'PDF Gerado!',
            text: 'O relatório foi baixado com sucesso',
            timer: 2000,
            showConfirmButton: false
        });

    } catch (error) {
        console.error('Erro ao exportar PDF:', error);
        Swal.fire({
            icon: 'error',
            title: 'Erro',
            text: 'Não foi possível gerar o PDF. Tente novamente.',
            confirmButtonColor: '#EF4444'
        });
    }
};

// Melhorar função de gerar relatório
window.gerarRelatorioEstoqueOriginal = window.gerarRelatorioEstoque; // Backup
window.gerarRelatorioEstoque = async function() {
    try {
        const tipo = document.getElementById('relatorioTipo')?.value || 'estoque';
        const dataInicio = document.getElementById('relatorioDataInicio')?.value;
        const dataFim = document.getElementById('relatorioDataFim')?.value;

        if (!dataInicio || !dataFim) {
            Swal.fire({
                icon: 'warning',
                title: 'Atenção',
                text: 'Selecione o período do relatório',
                confirmButtonColor: '#7C3AED'
            });
            return;
        }

        // Chamar função original se existir, senão fazer requisição
        if (typeof window.gerarRelatorioEstoqueOriginal === 'function') {
            await window.gerarRelatorioEstoqueOriginal();
        } else {
            // Implementação direta
            const params = new URLSearchParams({
                tipo,
                data_inicio: dataInicio,
                data_fim: dataFim
            });

            const response = await fetch(`/api/estoque/relatorio?${params}`, {
                credentials: 'include'
            });

            const data = await response.json();

            if (data.success) {
                const container = document.getElementById('relatorioEstoqueResultados');
                if (container) {
                    container.style.display = 'block';
                    container.innerHTML = `
                        <div class="card">
                            <div class="card-header">
                                <i class="bi bi-clipboard-data"></i> Resultado do Relatório
                            </div>
                            <div class="card-body">
                                <p><strong>Período:</strong> ${dataInicio} até ${dataFim}</p>
                                <p><strong>Tipo:</strong> ${tipo}</p>
                                <p><strong>Total de registros:</strong> ${data.total || 0}</p>
                                <div class="mt-3">
                                    ${JSON.stringify(data, null, 2)}
                                </div>
                            </div>
                        </div>
                    `;
                }
                Swal.fire({
                    icon: 'success',
                    title: 'Relatório Gerado!',
                    timer: 1500,
                    showConfirmButton: false
                });
            }
        }
    } catch (error) {
        console.error('Erro ao gerar relatório:', error);
        Swal.fire('Erro', 'Não foi possível gerar o relatório', 'error');
    }
};

// ============================================================================
// SISTEMA DE FILA INTELIGENTE (Diretrizes 10.1 e 10.2)
// ============================================================================

/**
 * Modal inteligente de fila com integração ao calendário
 * Diretriz 10.1: Sistema inteligente de automação ligado ao calendário
 * Diretriz 10.2: Notificações Email/WhatsApp ao adicionar à fila
 */
window.showModalFilaInteligente = async function() {
    try {
        // Carregar dados necessários em paralelo
        const [profissionaisRes, servicosRes] = await Promise.all([
            fetch('/api/profissionais', { credentials: 'include' }),
            fetch('/api/servicos', { credentials: 'include' })
        ]);

        const profissionaisData = await profissionaisRes.json();
        const servicosData = await servicosRes.json();

        const profissionais = profissionaisData.profissionais || [];
        const servicos = servicosData.servicos || [];

        // Criar options para selects
        const profissionaisOptions = profissionais.map(p =>
            `<option value="${p._id}">${p.nome} - ${p.especialidade || 'Geral'}</option>`
        ).join('');

        const servicosOptions = servicos.map(s =>
            `<option value="${s._id}">${s.nome} - R$ ${(s.preco || 0).toFixed(2)}</option>`
        ).join('');

        const { value: formValues } = await Swal.fire({
            title: '<strong>🎯 Fila Inteligente</strong>',
            html: `
                <div style="text-align: left; padding: 10px; max-height: 600px; overflow-y: auto;">

                    <!-- Dados do Cliente -->
                    <h6 style="color: #7C3AED; margin-top: 15px; margin-bottom: 10px;">
                        <i class="bi bi-person-fill"></i> Dados do Cliente
                    </h6>

                    <div class="mb-3">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                            <i class="bi bi-person"></i> Nome Completo *
                        </label>
                        <input type="text" id="fila_nome" class="form-control"
                               placeholder="Digite o nome completo" required>
                    </div>

                    <div class="mb-3">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                            <i class="bi bi-telephone"></i> Telefone (WhatsApp) *
                        </label>
                        <input type="text" id="fila_telefone" class="form-control"
                               placeholder="(00) 00000-0000" required>
                    </div>

                    <div class="mb-3">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                            <i class="bi bi-envelope"></i> Email (opcional)
                        </label>
                        <input type="email" id="fila_email" class="form-control"
                               placeholder="cliente@exemplo.com">
                    </div>

                    <!-- Serviço e Profissional -->
                    <h6 style="color: #7C3AED; margin-top: 20px; margin-bottom: 10px;">
                        <i class="bi bi-briefcase-fill"></i> Serviço Desejado
                    </h6>

                    <div class="mb-3">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                            <i class="bi bi-list-task"></i> Serviço *
                        </label>
                        <select id="fila_servico" class="form-control" required onchange="sugerirProfissionalDisponivel()">
                            <option value="">-- Selecione o serviço --</option>
                            ${servicosOptions}
                        </select>
                    </div>

                    <div class="mb-3">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                            <i class="bi bi-person-badge"></i> Profissional
                        </label>
                        <select id="fila_profissional" class="form-control">
                            <option value="">-- Automático (próximo disponível) --</option>
                            ${profissionaisOptions}
                        </select>
                        <small class="text-muted" id="fila_disponibilidade_info"></small>
                    </div>

                    <div class="mb-3">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                            <i class="bi bi-calendar-event"></i> Data/Hora Preferencial (opcional)
                        </label>
                        <input type="datetime-local" id="fila_data_preferencial" class="form-control">
                        <small class="text-muted">Deixe em branco para atendimento imediato na fila</small>
                    </div>

                    <!-- Notificações -->
                    <h6 style="color: #7C3AED; margin-top: 20px; margin-bottom: 10px;">
                        <i class="bi bi-bell-fill"></i> Notificações (Diretriz 10.2)
                    </h6>

                    <div class="mb-3" style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                        <div class="form-check mb-2">
                            <input type="checkbox" class="form-check-input" id="fila_notif_whatsapp" checked>
                            <label class="form-check-label" for="fila_notif_whatsapp">
                                <i class="bi bi-whatsapp" style="color: #25D366;"></i>
                                Enviar confirmação via WhatsApp
                            </label>
                        </div>
                        <div class="form-check">
                            <input type="checkbox" class="form-check-input" id="fila_notif_email">
                            <label class="form-check-label" for="fila_notif_email">
                                <i class="bi bi-envelope-fill" style="color: #3B82F6;"></i>
                                Enviar confirmação via Email (MailSender)
                            </label>
                        </div>
                        <small class="text-muted d-block mt-2">
                            <i class="bi bi-info-circle"></i> O cliente receberá sua posição na fila e tempo estimado
                        </small>
                    </div>

                    <!-- Observações -->
                    <div class="mb-3">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                            <i class="bi bi-chat-left-text"></i> Observações (opcional)
                        </label>
                        <textarea id="fila_observacoes" class="form-control" rows="3"
                                  placeholder="Alguma observação especial sobre o atendimento..."></textarea>
                    </div>

                    <div class="alert alert-info" style="margin-top: 15px; font-size: 0.9rem;">
                        <i class="bi bi-lightbulb"></i>
                        <strong>Sistema Inteligente:</strong> O profissional será automaticamente sugerido
                        baseado na disponibilidade do calendário e carga de trabalho atual.
                    </div>
                </div>
            `,
            showCancelButton: true,
            confirmButtonText: '<i class="bi bi-plus-circle"></i> Adicionar à Fila',
            cancelButtonText: 'Cancelar',
            width: '650px',
            customClass: {
                popup: 'fila-inteligente-modal'
            },
            didOpen: () => {
                // Sugerir horário automático
                const agora = new Date();
                agora.setMinutes(agora.getMinutes() + 30); // 30 min a partir de agora
                const dataInput = document.getElementById('fila_data_preferencial');
                if (dataInput) {
                    const ano = agora.getFullYear();
                    const mes = String(agora.getMonth() + 1).padStart(2, '0');
                    const dia = String(agora.getDate()).padStart(2, '0');
                    const hora = String(agora.getHours()).padStart(2, '0');
                    const min = String(agora.getMinutes()).padStart(2, '0');
                    dataInput.value = `${ano}-${mes}-${dia}T${hora}:${min}`;
                }
            },
            preConfirm: () => {
                const nome = document.getElementById('fila_nome').value.trim();
                const telefone = document.getElementById('fila_telefone').value.trim();
                const email = document.getElementById('fila_email').value.trim();
                const servicoId = document.getElementById('fila_servico').value;
                const profissionalId = document.getElementById('fila_profissional').value;
                const dataPreferencial = document.getElementById('fila_data_preferencial').value;
                const notifWhatsApp = document.getElementById('fila_notif_whatsapp').checked;
                const notifEmail = document.getElementById('fila_notif_email').checked;
                const observacoes = document.getElementById('fila_observacoes').value.trim();

                // Validações
                if (!nome) {
                    Swal.showValidationMessage('Nome do cliente é obrigatório');
                    return false;
                }
                if (!telefone) {
                    Swal.showValidationMessage('Telefone é obrigatório para notificações');
                    return false;
                }
                if (!servicoId) {
                    Swal.showValidationMessage('Selecione um serviço');
                    return false;
                }
                if (notifEmail && !email) {
                    Swal.showValidationMessage('Email é necessário para notificação por email');
                    return false;
                }

                return {
                    cliente_nome: nome,
                    cliente_telefone: telefone,
                    cliente_email: email || null,
                    servico_id: servicoId,
                    profissional_id: profissionalId || null,
                    data_preferencial: dataPreferencial || null,
                    notificacoes: {
                        whatsapp: notifWhatsApp,
                        email: notifEmail
                    },
                    observacoes: observacoes || null
                };
            }
        });

        if (formValues) {
            // Enviar para API inteligente de fila
            await adicionarFilaInteligente(formValues);
        }

    } catch (error) {
        console.error('Erro ao abrir modal de fila:', error);
        Swal.fire('Erro', 'Não foi possível carregar os dados necessários', 'error');
    }
};

/**
 * Adiciona cliente à fila com sistema inteligente
 */
async function adicionarFilaInteligente(dados) {
    try {
        Swal.fire({
            title: 'Processando...',
            text: 'Adicionando à fila e verificando disponibilidade',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        const response = await fetch('/api/fila/inteligente', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(dados)
        });

        const result = await response.json();

        if (result.success) {
            let mensagemSucesso = `
                <div style="text-align: left;">
                    <p><strong>Posição na fila:</strong> ${result.posicao}º</p>
                    <p><strong>Tempo estimado:</strong> ${result.tempo_estimado || '15-20 minutos'}</p>
                    ${result.profissional_nome ? `<p><strong>Profissional:</strong> ${result.profissional_nome}</p>` : ''}
                    ${result.horario_sugerido ? `<p><strong>Horário sugerido:</strong> ${result.horario_sugerido}</p>` : ''}
                </div>
            `;

            if (result.notificacoes_enviadas) {
                mensagemSucesso += `
                    <div style="margin-top: 15px; padding: 10px; background: #f0fdf4; border-left: 4px solid #10B981; border-radius: 4px;">
                        <strong style="color: #059669;">✓ Notificações enviadas:</strong><br>
                        ${result.notificacoes_enviadas.whatsapp ? '✓ WhatsApp<br>' : ''}
                        ${result.notificacoes_enviadas.email ? '✓ Email' : ''}
                    </div>
                `;
            }

            await Swal.fire({
                icon: 'success',
                title: '✅ Adicionado à Fila!',
                html: mensagemSucesso,
                confirmButtonText: 'OK'
            });

            // Recarregar fila
            if (typeof loadFila === 'function') {
                loadFila();
            }
        } else {
            Swal.fire('Erro', result.message || 'Não foi possível adicionar à fila', 'error');
        }

    } catch (error) {
        console.error('Erro ao adicionar à fila:', error);
        Swal.fire('Erro', 'Não foi possível processar a solicitação', 'error');
    }
}

/**
 * Sugere profissional disponível baseado no serviço selecionado
 */
window.sugerirProfissionalDisponivel = async function() {
    const servicoId = document.getElementById('fila_servico')?.value;
    if (!servicoId) return;

    try {
        const response = await fetch(`/api/fila/sugerir-profissional?servico_id=${servicoId}`, {
            credentials: 'include'
        });

        const data = await response.json();

        if (data.success && data.profissional_id) {
            const selectProfissional = document.getElementById('fila_profissional');
            if (selectProfissional) {
                selectProfissional.value = data.profissional_id;

                const infoDiv = document.getElementById('fila_disponibilidade_info');
                if (infoDiv) {
                    infoDiv.innerHTML = `
                        <span style="color: #10B981;">
                            ✓ ${data.profissional_nome} está disponível
                            ${data.proxima_disponibilidade ? `(Próxima: ${data.proxima_disponibilidade})` : ''}
                        </span>
                    `;
                }
            }
        }
    } catch (error) {
        console.error('Erro ao sugerir profissional:', error);
    }
};

/**
 * Override da função original showModalFila para usar a versão inteligente
 */
if (typeof window.showModalFila !== 'undefined') {
    window.showModalFilaOriginal = window.showModalFila;
}
window.showModalFila = window.showModalFilaInteligente;

console.log('✅ Sistema de Fila Inteligente carregado (10.1, 10.2)');

// ============================================================================
// SISTEMA DE ANAMNESE/PRONTUÁRIO COMPLETO (Diretrizes 11.1, 11.3, 11.4)
// ============================================================================

/**
 * Visualizar cliente com anamnese/prontuário integrado
 * Diretriz 11.1: Associar ao visualizar cliente
 */
window.visualizarClienteCompleto = async function(clienteId) {
    try {
        Swal.fire({
            title: 'Carregando...',
            allowOutsideClick: false,
            didOpen: () => Swal.showLoading()
        });

        // Carregar dados do cliente, anamneses e prontuários em paralelo
        const [clienteRes, anamnesesRes, prontuariosRes] = await Promise.all([
            fetch(`/api/clientes/${clienteId}`, { credentials: 'include' }),
            fetch(`/api/clientes/${clienteId}/anamneses`, { credentials: 'include' }),
            fetch(`/api/clientes/${clienteId}/prontuarios`, { credentials: 'include' })
        ]);

        const clienteData = await clienteRes.json();
        const anamnesesData = await anamnesesRes.json();
        const prontuariosData = await prontuariosRes.json();

        if (!clienteData.success) {
            Swal.fire('Erro', 'Cliente não encontrado', 'error');
            return;
        }

        const cliente = clienteData.cliente;
        const anamneses = anamnesesData.anamneses || [];
        const prontuarios = prontuariosData.prontuarios || [];

        // Criar tabs de anamneses
        const anamnesesHTML = anamneses.length > 0 ? anamneses.map((a, idx) => {
            const data = new Date(a.data_cadastro).toLocaleDateString('pt-BR');
            return `
                <div class="list-group-item" style="margin-bottom: 8px; border-radius: 6px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>Versão ${idx + 1}</strong> - ${data}
                            ${a.imagens && a.imagens.length > 0 ? `<span class="badge bg-info ms-2">${a.imagens.length} imagens</span>` : ''}
                        </div>
                        <button class="btn btn-sm btn-outline-primary" onclick="visualizarAnamnese('${a._id}', '${cliente.cpf}')">
                            <i class="bi bi-eye"></i> Ver
                        </button>
                    </div>
                </div>
            `;
        }).join('') : '<p class="text-muted text-center">Nenhuma anamnese cadastrada</p>';

        // Criar tabs de prontuários
        const prontuariosHTML = prontuarios.length > 0 ? prontuarios.map((p) => {
            const data = new Date(p.data_atendimento).toLocaleDateString('pt-BR');
            return `
                <div class="list-group-item" style="margin-bottom: 8px; border-radius: 6px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>${data}</strong> - ${p.procedimento || 'Procedimento não especificado'}
                            <br><small class="text-muted">Prof: ${p.profissional || 'N/A'}</small>
                            ${p.imagens && p.imagens.length > 0 ? `<span class="badge bg-info ms-2">${p.imagens.length} imagens</span>` : ''}
                        </div>
                        <button class="btn btn-sm btn-outline-primary" onclick="visualizarProntuario('${p._id}', '${cliente.cpf}')">
                            <i class="bi bi-eye"></i> Ver
                        </button>
                    </div>
                </div>
            `;
        }).join('') : '<p class="text-muted text-center">Nenhum prontuário cadastrado</p>';

        Swal.fire({
            title: `<i class="bi bi-person-circle"></i> ${cliente.nome}`,
            html: `
                <div style="text-align: left; max-height: 600px; overflow-y: auto;">
                    <!-- Informações Básicas -->
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                        <p style="margin: 5px 0;"><strong>CPF:</strong> ${cliente.cpf}</p>
                        <p style="margin: 5px 0;"><strong>Telefone:</strong> ${cliente.telefone || 'Não informado'}</p>
                        <p style="margin: 5px 0;"><strong>Email:</strong> ${cliente.email || 'Não informado'}</p>
                    </div>

                    <!-- Tabs -->
                    <ul class="nav nav-tabs" role="tablist" style="margin-bottom: 15px;">
                        <li class="nav-item">
                            <a class="nav-link active" data-bs-toggle="tab" href="#tab-anamneses-${clienteId}">
                                <i class="bi bi-file-medical"></i> Anamneses (${anamneses.length})
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" data-bs-toggle="tab" href="#tab-prontuarios-${clienteId}">
                                <i class="bi bi-clipboard2-pulse"></i> Prontuários (${prontuarios.length})
                            </a>
                        </li>
                    </ul>

                    <!-- Tab Content -->
                    <div class="tab-content">
                        <div id="tab-anamneses-${clienteId}" class="tab-pane fade show active">
                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <h6 style="margin: 0;">Histórico de Anamneses</h6>
                                <button class="btn btn-sm btn-success" onclick="novaAnamneseComNotificacao('${cliente.cpf}', '${cliente.nome}', '${cliente.email || ''}', '${cliente.telefone || ''}')">
                                    <i class="bi bi-plus-circle"></i> Nova
                                </button>
                            </div>
                            <div class="list-group">
                                ${anamnesesHTML}
                            </div>
                        </div>
                        <div id="tab-prontuarios-${clienteId}" class="tab-pane fade">
                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <h6 style="margin: 0;">Histórico de Atendimentos</h6>
                                <button class="btn btn-sm btn-success" onclick="novoProntuarioComNotificacao('${cliente.cpf}', '${cliente.nome}', '${cliente.email || ''}', '${cliente.telefone || ''}')">
                                    <i class="bi bi-plus-circle"></i> Novo
                                </button>
                            </div>
                            <div class="list-group">
                                ${prontuariosHTML}
                            </div>
                        </div>
                    </div>

                    <!-- Botão de Notificação -->
                    <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                        <button class="btn btn-primary w-100" onclick="notificarCliente('${cliente.cpf}', '${cliente.nome}', '${cliente.email || ''}', '${cliente.telefone || ''}')">
                            <i class="bi bi-bell"></i> Enviar Notificação ao Cliente
                        </button>
                    </div>
                </div>
            `,
            width: '800px',
            showCloseButton: true,
            showConfirmButton: false,
            customClass: {
                popup: 'cliente-completo-modal'
            }
        });

    } catch (error) {
        console.error('Erro ao visualizar cliente:', error);
        Swal.fire('Erro', 'Não foi possível carregar os dados do cliente', 'error');
    }
};

/**
 * Nova anamnese com upload de imagens e notificações
 * Diretriz 11.3: Anexar imagens físicas
 * Diretriz 11.4: Notificações Email/WhatsApp
 */
window.novaAnamneseComNotificacao = async function(cpf, nomeCliente, email, telefone) {
    const { value: formValues } = await Swal.fire({
        title: '<strong>📋 Nova Anamnese</strong>',
        html: `
            <div style="text-align: left; padding: 10px; max-height: 600px; overflow-y: auto;">
                <div class="mb-3">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                        Observações Gerais
                    </label>
                    <textarea id="anamnese_observacoes" class="form-control" rows="4"
                              placeholder="Digite as observações da anamnese..."></textarea>
                </div>

                <div class="mb-3">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                        <i class="bi bi-images"></i> Anexar Imagens/Documentos (Diretriz 11.3)
                    </label>
                    <input type="file" id="anamnese_imagens" class="form-control"
                           accept="image/*,application/pdf" multiple>
                    <small class="text-muted">Aceita imagens (JPG, PNG) e PDFs. Máximo 5 arquivos.</small>
                </div>

                <div class="mb-3" style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                    <label style="display: block; margin-bottom: 10px; font-weight: 600;">
                        <i class="bi bi-bell"></i> Notificar Cliente (Diretriz 11.4)
                    </label>
                    <div class="form-check mb-2">
                        <input type="checkbox" class="form-check-input" id="anamnese_notif_whatsapp"
                               ${telefone ? 'checked' : 'disabled'}>
                        <label class="form-check-label" for="anamnese_notif_whatsapp">
                            <i class="bi bi-whatsapp" style="color: #25D366;"></i> WhatsApp
                            ${!telefone ? '<span class="text-muted">(sem telefone cadastrado)</span>' : ''}
                        </label>
                    </div>
                    <div class="form-check">
                        <input type="checkbox" class="form-check-input" id="anamnese_notif_email"
                               ${email ? '' : 'disabled'}>
                        <label class="form-check-label" for="anamnese_notif_email">
                            <i class="bi bi-envelope-fill" style="color: #3B82F6;"></i> Email
                            ${!email ? '<span class="text-muted">(sem email cadastrado)</span>' : ''}
                        </label>
                    </div>
                </div>
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: '<i class="bi bi-check-circle"></i> Salvar Anamnese',
        cancelButtonText: 'Cancelar',
        width: '650px',
        preConfirm: () => {
            const observacoes = document.getElementById('anamnese_observacoes').value.trim();
            const imagensInput = document.getElementById('anamnese_imagens');
            const notifWhatsApp = document.getElementById('anamnese_notif_whatsapp').checked;
            const notifEmail = document.getElementById('anamnese_notif_email').checked;

            if (!observacoes) {
                Swal.showValidationMessage('Observações são obrigatórias');
                return false;
            }

            if (imagensInput.files.length > 5) {
                Swal.showValidationMessage('Máximo de 5 arquivos permitido');
                return false;
            }

            return {
                observacoes,
                imagens: imagensInput.files,
                notificacoes: {
                    whatsapp: notifWhatsApp,
                    email: notifEmail
                }
            };
        }
    });

    if (formValues) {
        await salvarAnamneseComImagens(cpf, nomeCliente, email, telefone, formValues);
    }
};

/**
 * Salvar anamnese com upload de imagens
 */
async function salvarAnamneseComImagens(cpf, nomeCliente, email, telefone, dados) {
    try {
        Swal.fire({
            title: 'Salvando...',
            text: 'Processando anamnese e enviando notificações',
            allowOutsideClick: false,
            didOpen: () => Swal.showLoading()
        });

        const formData = new FormData();
        formData.append('observacoes', dados.observacoes);
        formData.append('notificacoes', JSON.stringify(dados.notificacoes));
        formData.append('cliente_nome', nomeCliente);
        formData.append('cliente_email', email);
        formData.append('cliente_telefone', telefone);

        // Adicionar imagens
        if (dados.imagens && dados.imagens.length > 0) {
            for (let i = 0; i < dados.imagens.length; i++) {
                formData.append('imagens', dados.imagens[i]);
            }
        }

        const response = await fetch(`/api/clientes/${cpf}/anamnese`, {
            method: 'POST',
            credentials: 'include',
            body: formData  // Não incluir Content-Type, deixar o browser definir com boundary
        });

        const result = await response.json();

        if (result.success) {
            let mensagemSucesso = '<p><strong>Anamnese cadastrada com sucesso!</strong></p>';

            if (result.imagens_salvas && result.imagens_salvas.length > 0) {
                mensagemSucesso += `<p>✓ ${result.imagens_salvas.length} imagem(ns) anexada(s)</p>`;
            }

            if (result.notificacoes_enviadas) {
                mensagemSucesso += '<div style="margin-top: 10px; padding: 10px; background: #f0fdf4; border-radius: 4px;">';
                mensagemSucesso += '<strong style="color: #059669;">Notificações enviadas:</strong><br>';
                if (result.notificacoes_enviadas.whatsapp) mensagemSucesso += '✓ WhatsApp<br>';
                if (result.notificacoes_enviadas.email) mensagemSucesso += '✓ Email';
                mensagemSucesso += '</div>';
            }

            await Swal.fire({
                icon: 'success',
                title: 'Sucesso!',
                html: mensagemSucesso,
                timer: 3000
            });

            // Recarregar se estiver na tela de anamnese
            if (typeof buscarAnamnesesCliente === 'function') {
                buscarAnamnesesCliente();
            }

        } else {
            Swal.fire('Erro', result.message || 'Não foi possível salvar a anamnese', 'error');
        }

    } catch (error) {
        console.error('Erro ao salvar anamnese:', error);
        Swal.fire('Erro', 'Não foi possível processar a solicitação', 'error');
    }
}

/**
 * Novo prontuário com upload de imagens e notificações
 */
window.novoProntuarioComNotificacao = async function(cpf, nomeCliente, email, telefone) {
    const { value: formValues } = await Swal.fire({
        title: '<strong>📋 Novo Prontuário</strong>',
        html: `
            <div style="text-align: left; padding: 10px; max-height: 600px; overflow-y: auto;">
                <div class="mb-3">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                        Data do Atendimento
                    </label>
                    <input type="date" id="pront_data" class="form-control"
                           value="${new Date().toISOString().split('T')[0]}">
                </div>

                <div class="mb-3">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                        Profissional
                    </label>
                    <input type="text" id="pront_profissional" class="form-control"
                           placeholder="Nome do profissional">
                </div>

                <div class="mb-3">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                        Procedimento
                    </label>
                    <input type="text" id="pront_procedimento" class="form-control"
                           placeholder="Tipo de procedimento realizado">
                </div>

                <div class="mb-3">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                        Observações
                    </label>
                    <textarea id="pront_observacoes" class="form-control" rows="3"
                              placeholder="Detalhes do atendimento..."></textarea>
                </div>

                <div class="mb-3">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                        <i class="bi bi-images"></i> Anexar Imagens/Documentos (Diretriz 11.3)
                    </label>
                    <input type="file" id="pront_imagens" class="form-control"
                           accept="image/*,application/pdf" multiple>
                    <small class="text-muted">Fotos do procedimento, documentos, etc. Máximo 5 arquivos.</small>
                </div>

                <div class="mb-3" style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                    <label style="display: block; margin-bottom: 10px; font-weight: 600;">
                        <i class="bi bi-bell"></i> Notificar Cliente (Diretriz 11.4)
                    </label>
                    <div class="form-check mb-2">
                        <input type="checkbox" class="form-check-input" id="pront_notif_whatsapp"
                               ${telefone ? 'checked' : 'disabled'}>
                        <label class="form-check-label" for="pront_notif_whatsapp">
                            <i class="bi bi-whatsapp" style="color: #25D366;"></i> WhatsApp
                            ${!telefone ? '<span class="text-muted">(sem telefone cadastrado)</span>' : ''}
                        </label>
                    </div>
                    <div class="form-check">
                        <input type="checkbox" class="form-check-input" id="pront_notif_email"
                               ${email ? '' : 'disabled'}>
                        <label class="form-check-label" for="pront_notif_email">
                            <i class="bi bi-envelope-fill" style="color: #3B82F6;"></i> Email
                            ${!email ? '<span class="text-muted">(sem email cadastrado)</span>' : ''}
                        </label>
                    </div>
                </div>
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: '<i class="bi bi-check-circle"></i> Salvar Prontuário',
        cancelButtonText: 'Cancelar',
        width: '650px',
        preConfirm: () => {
            const dataAtendimento = document.getElementById('pront_data').value;
            const profissional = document.getElementById('pront_profissional').value.trim();
            const procedimento = document.getElementById('pront_procedimento').value.trim();
            const observacoes = document.getElementById('pront_observacoes').value.trim();
            const imagensInput = document.getElementById('pront_imagens');
            const notifWhatsApp = document.getElementById('pront_notif_whatsapp').checked;
            const notifEmail = document.getElementById('pront_notif_email').checked;

            if (!dataAtendimento || !profissional || !procedimento) {
                Swal.showValidationMessage('Data, profissional e procedimento são obrigatórios');
                return false;
            }

            if (imagensInput.files.length > 5) {
                Swal.showValidationMessage('Máximo de 5 arquivos permitido');
                return false;
            }

            return {
                data_atendimento: dataAtendimento,
                profissional,
                procedimento,
                observacoes,
                imagens: imagensInput.files,
                notificacoes: {
                    whatsapp: notifWhatsApp,
                    email: notifEmail
                }
            };
        }
    });

    if (formValues) {
        await salvarProntuarioComImagens(cpf, nomeCliente, email, telefone, formValues);
    }
};

/**
 * Salvar prontuário com upload de imagens
 */
async function salvarProntuarioComImagens(cpf, nomeCliente, email, telefone, dados) {
    try {
        Swal.fire({
            title: 'Salvando...',
            text: 'Processando prontuário e enviando notificações',
            allowOutsideClick: false,
            didOpen: () => Swal.showLoading()
        });

        const formData = new FormData();
        formData.append('data_atendimento', dados.data_atendimento);
        formData.append('profissional', dados.profissional);
        formData.append('procedimento', dados.procedimento);
        formData.append('observacoes', dados.observacoes);
        formData.append('notificacoes', JSON.stringify(dados.notificacoes));
        formData.append('cliente_nome', nomeCliente);
        formData.append('cliente_email', email);
        formData.append('cliente_telefone', telefone);

        // Adicionar imagens
        if (dados.imagens && dados.imagens.length > 0) {
            for (let i = 0; i < dados.imagens.length; i++) {
                formData.append('imagens', dados.imagens[i]);
            }
        }

        const response = await fetch(`/api/clientes/${cpf}/prontuario`, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            let mensagemSucesso = '<p><strong>Prontuário cadastrado com sucesso!</strong></p>';

            if (result.imagens_salvas && result.imagens_salvas.length > 0) {
                mensagemSucesso += `<p>✓ ${result.imagens_salvas.length} imagem(ns) anexada(s)</p>`;
            }

            if (result.notificacoes_enviadas) {
                mensagemSucesso += '<div style="margin-top: 10px; padding: 10px; background: #f0fdf4; border-radius: 4px;">';
                mensagemSucesso += '<strong style="color: #059669;">Notificações enviadas:</strong><br>';
                if (result.notificacoes_enviadas.whatsapp) mensagemSucesso += '✓ WhatsApp<br>';
                if (result.notificacoes_enviadas.email) mensagemSucesso += '✓ Email';
                mensagemSucesso += '</div>';
            }

            await Swal.fire({
                icon: 'success',
                title: 'Sucesso!',
                html: mensagemSucesso,
                timer: 3000
            });

            // Recarregar se estiver na tela de prontuário
            if (typeof buscarProntuariosCliente === 'function') {
                buscarProntuariosCliente();
            }

        } else {
            Swal.fire('Erro', result.message || 'Não foi possível salvar o prontuário', 'error');
        }

    } catch (error) {
        console.error('Erro ao salvar prontuário:', error);
        Swal.fire('Erro', 'Não foi possível processar a solicitação', 'error');
    }
}

/**
 * Notificar cliente diretamente (Diretriz 11.4)
 */
window.notificarCliente = async function(cpf, nomeCliente, email, telefone) {
    const { value: formValues } = await Swal.fire({
        title: '<strong>📧 Notificar Cliente</strong>',
        html: `
            <div style="text-align: left; padding: 10px;">
                <p><strong>Cliente:</strong> ${nomeCliente}</p>

                <div class="mb-3">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                        Tipo de Notificação
                    </label>
                    <div class="form-check">
                        <input type="checkbox" class="form-check-input" id="notif_whatsapp"
                               ${telefone ? 'checked' : 'disabled'}>
                        <label class="form-check-label" for="notif_whatsapp">
                            <i class="bi bi-whatsapp" style="color: #25D366;"></i> WhatsApp
                        </label>
                    </div>
                    <div class="form-check">
                        <input type="checkbox" class="form-check-input" id="notif_email"
                               ${email ? '' : 'disabled'}>
                        <label class="form-check-label" for="notif_email">
                            <i class="bi bi-envelope-fill" style="color: #3B82F6;"></i> Email
                        </label>
                    </div>
                </div>

                <div class="mb-3">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                        Mensagem
                    </label>
                    <textarea id="notif_mensagem" class="form-control" rows="4"
                              placeholder="Digite a mensagem que deseja enviar..."></textarea>
                </div>
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: '<i class="bi bi-send"></i> Enviar',
        cancelButtonText: 'Cancelar',
        width: '550px',
        preConfirm: () => {
            const whatsapp = document.getElementById('notif_whatsapp').checked;
            const emailNotif = document.getElementById('notif_email').checked;
            const mensagem = document.getElementById('notif_mensagem').value.trim();

            if (!whatsapp && !emailNotif) {
                Swal.showValidationMessage('Selecione pelo menos um tipo de notificação');
                return false;
            }

            if (!mensagem) {
                Swal.showValidationMessage('A mensagem é obrigatória');
                return false;
            }

            return { whatsapp, email: emailNotif, mensagem };
        }
    });

    if (formValues) {
        await enviarNotificacaoCliente(cpf, nomeCliente, email, telefone, formValues);
    }
};

/**
 * Enviar notificação ao cliente
 */
async function enviarNotificacaoCliente(cpf, nomeCliente, email, telefone, dados) {
    try {
        Swal.fire({
            title: 'Enviando...',
            allowOutsideClick: false,
            didOpen: () => Swal.showLoading()
        });

        const response = await fetch(`/api/clientes/${cpf}/notificar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                cliente_nome: nomeCliente,
                cliente_email: email,
                cliente_telefone: telefone,
                mensagem: dados.mensagem,
                notificacoes: {
                    whatsapp: dados.whatsapp,
                    email: dados.email
                }
            })
        });

        const result = await response.json();

        if (result.success) {
            let msg = '<strong>Notificação enviada com sucesso!</strong><br>';
            if (result.notificacoes_enviadas.whatsapp) msg += '✓ WhatsApp<br>';
            if (result.notificacoes_enviadas.email) msg += '✓ Email';

            Swal.fire({
                icon: 'success',
                title: 'Enviado!',
                html: msg,
                timer: 2500
            });
        } else {
            Swal.fire('Erro', result.message || 'Não foi possível enviar a notificação', 'error');
        }

    } catch (error) {
        console.error('Erro ao enviar notificação:', error);
        Swal.fire('Erro', 'Não foi possível processar a solicitação', 'error');
    }
}

console.log('✅ Sistema de Anamnese/Prontuário completo carregado (11.1, 11.3, 11.4)');

// ============================================================================
// SISTEMA DE MULTICOMISSÃO (Diretriz 12.1)
// ============================================================================

/**
 * Carregar regras de multicomissão
 * Diretriz 12.1: Comissão sobre comissão (assistente recebe % da comissão do profissional)
 */
window.carregarMulticomissoes = async function() {
    try {
        const response = await fetch('/api/multicomissao/regras', {
            credentials: 'include'
        });

        const data = await response.json();

        if (data.success) {
            const regras = data.regras || [];
            const container = document.getElementById('multicomissoesBody');

            if (regras.length === 0) {
                container.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center text-muted">
                            <i class="bi bi-info-circle"></i> Nenhuma regra de multicomissão cadastrada
                        </td>
                    </tr>
                `;
                return;
            }

            container.innerHTML = regras.map(regra => {
                const statusBadge = regra.ativa
                    ? '<span class="badge bg-success">Ativa</span>'
                    : '<span class="badge bg-secondary">Inativa</span>';

                return `
                    <tr>
                        <td><strong>${regra.profissional_principal_nome || 'N/A'}</strong></td>
                        <td>${regra.assistente_nome || 'N/A'}</td>
                        <td><span class="badge bg-primary">${regra.percentual_assistente}%</span></td>
                        <td>${regra.servicos_especificos ? 'Específicos' : 'Todos'}</td>
                        <td>${statusBadge}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary" onclick="visualizarMulticomissao('${regra._id}')">
                                <i class="bi bi-eye"></i>
                            </button>
                            <button class="btn btn-sm btn-warning" onclick="editarMulticomissao('${regra._id}')">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm ${regra.ativa ? 'btn-secondary' : 'btn-success'}"
                                    onclick="toggleMulticomissao('${regra._id}', ${!regra.ativa})">
                                <i class="bi bi-${regra.ativa ? 'pause' : 'play'}-fill"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="deletarMulticomissao('${regra._id}')">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');

        } else {
            console.error('Erro ao carregar multicomissões:', data.message);
        }

    } catch (error) {
        console.error('Erro ao carregar multicomissões:', error);
    }
};

/**
 * Modal para nova regra de multicomissão
 */
window.novaMulticomissao = async function() {
    try {
        // Carregar profissionais
        const profRes = await fetch('/api/profissionais', { credentials: 'include' });
        const profData = await profRes.json();
        const profissionais = profData.profissionais || [];

        if (profissionais.length < 2) {
            Swal.fire('Atenção', 'É necessário ter pelo menos 2 profissionais cadastrados', 'warning');
            return;
        }

        const profOptions = profissionais.map(p =>
            `<option value="${p._id}">${p.nome} - ${p.especialidade || 'Geral'}</option>`
        ).join('');

        const { value: formValues } = await Swal.fire({
            title: '<strong>💰 Nova Regra de Multicomissão</strong>',
            html: `
                <div style="text-align: left; padding: 10px; max-height: 600px; overflow-y: auto;">

                    <div class="alert alert-info" style="font-size: 0.9rem;">
                        <i class="bi bi-info-circle"></i>
                        <strong>Como funciona:</strong> O assistente receberá uma porcentagem da comissão
                        que o profissional principal recebe em cada atendimento.
                    </div>

                    <div class="mb-3">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                            <i class="bi bi-person-fill"></i> Profissional Principal *
                        </label>
                        <select id="multi_profissional_principal" class="form-control" required>
                            <option value="">-- Selecione o profissional principal --</option>
                            ${profOptions}
                        </select>
                        <small class="text-muted">Quem realiza o atendimento</small>
                    </div>

                    <div class="mb-3">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                            <i class="bi bi-person-badge"></i> Assistente *
                        </label>
                        <select id="multi_assistente" class="form-control" required>
                            <option value="">-- Selecione o assistente --</option>
                            ${profOptions}
                        </select>
                        <small class="text-muted">Quem auxilia no atendimento</small>
                    </div>

                    <div class="mb-3">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                            <i class="bi bi-percent"></i> Percentual da Comissão do Profissional *
                        </label>
                        <input type="number" id="multi_percentual" class="form-control"
                               min="1" max="100" step="0.5" value="20" required>
                        <small class="text-muted">
                            Exemplo: Se o profissional recebe 10% de comissão e você configurar 20%,
                            o assistente receberá 2% do valor total (20% de 10%)
                        </small>
                    </div>

                    <div class="mb-3">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                            <i class="bi bi-calendar-range"></i> Período de Vigência
                        </label>
                        <div class="row">
                            <div class="col-6">
                                <label>Data Início</label>
                                <input type="date" id="multi_data_inicio" class="form-control"
                                       value="${new Date().toISOString().split('T')[0]}">
                            </div>
                            <div class="col-6">
                                <label>Data Fim (opcional)</label>
                                <input type="date" id="multi_data_fim" class="form-control">
                            </div>
                        </div>
                        <small class="text-muted">Deixe a data fim vazia para vigência indeterminada</small>
                    </div>

                    <div class="mb-3">
                        <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                            <i class="bi bi-list-task"></i> Observações (opcional)
                        </label>
                        <textarea id="multi_observacoes" class="form-control" rows="2"
                                  placeholder="Detalhes sobre esta regra..."></textarea>
                    </div>

                    <div class="form-check mb-3">
                        <input type="checkbox" class="form-check-input" id="multi_ativa" checked>
                        <label class="form-check-label" for="multi_ativa">
                            <strong>Regra ativa</strong>
                        </label>
                    </div>

                </div>
            `,
            showCancelButton: true,
            confirmButtonText: '<i class="bi bi-check-circle"></i> Criar Regra',
            cancelButtonText: 'Cancelar',
            width: '700px',
            preConfirm: () => {
                const profPrincipalId = document.getElementById('multi_profissional_principal').value;
                const assistenteId = document.getElementById('multi_assistente').value;
                const percentual = parseFloat(document.getElementById('multi_percentual').value);
                const dataInicio = document.getElementById('multi_data_inicio').value;
                const dataFim = document.getElementById('multi_data_fim').value;
                const observacoes = document.getElementById('multi_observacoes').value.trim();
                const ativa = document.getElementById('multi_ativa').checked;

                // Validações
                if (!profPrincipalId || !assistenteId) {
                    Swal.showValidationMessage('Profissional principal e assistente são obrigatórios');
                    return false;
                }

                if (profPrincipalId === assistenteId) {
                    Swal.showValidationMessage('Profissional principal e assistente não podem ser a mesma pessoa');
                    return false;
                }

                if (!percentual || percentual < 1 || percentual > 100) {
                    Swal.showValidationMessage('Percentual deve estar entre 1% e 100%');
                    return false;
                }

                if (!dataInicio) {
                    Swal.showValidationMessage('Data de início é obrigatória');
                    return false;
                }

                return {
                    profissional_principal_id: profPrincipalId,
                    assistente_id: assistenteId,
                    percentual_assistente: percentual,
                    data_inicio: dataInicio,
                    data_fim: dataFim || null,
                    observacoes: observacoes || null,
                    ativa: ativa
                };
            }
        });

        if (formValues) {
            await salvarMulticomissao(formValues);
        }

    } catch (error) {
        console.error('Erro ao abrir modal de multicomissão:', error);
        Swal.fire('Erro', 'Não foi possível carregar os dados', 'error');
    }
};

/**
 * Salvar regra de multicomissão
 */
async function salvarMulticomissao(dados) {
    try {
        Swal.fire({
            title: 'Salvando...',
            allowOutsideClick: false,
            didOpen: () => Swal.showLoading()
        });

        const response = await fetch('/api/multicomissao/regras', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(dados)
        });

        const result = await response.json();

        if (result.success) {
            await Swal.fire({
                icon: 'success',
                title: 'Regra Criada!',
                html: `
                    <p><strong>Profissional:</strong> ${result.profissional_principal_nome}</p>
                    <p><strong>Assistente:</strong> ${result.assistente_nome}</p>
                    <p><strong>Comissão do Assistente:</strong> ${result.percentual_assistente}% da comissão do profissional</p>
                `,
                timer: 3000
            });

            // Recarregar lista
            if (typeof carregarMulticomissoes === 'function') {
                carregarMulticomissoes();
            }

        } else {
            Swal.fire('Erro', result.message || 'Não foi possível criar a regra', 'error');
        }

    } catch (error) {
        console.error('Erro ao salvar multicomissão:', error);
        Swal.fire('Erro', 'Não foi possível processar a solicitação', 'error');
    }
}

/**
 * Visualizar detalhes da regra de multicomissão
 */
window.visualizarMulticomissao = async function(regraId) {
    try {
        const response = await fetch(`/api/multicomissao/regras/${regraId}`, {
            credentials: 'include'
        });

        const data = await response.json();

        if (data.success) {
            const regra = data.regra;
            const calculos = data.calculos || {};

            Swal.fire({
                title: '<i class="bi bi-graph-up"></i> Detalhes da Multicomissão',
                html: `
                    <div style="text-align: left; padding: 15px;">
                        <h5 style="color: #7C3AED; margin-bottom: 15px;">Configuração</h5>
                        <p><strong>Profissional Principal:</strong> ${regra.profissional_principal_nome}</p>
                        <p><strong>Assistente:</strong> ${regra.assistente_nome}</p>
                        <p><strong>Percentual:</strong> <span class="badge bg-primary">${regra.percentual_assistente}%</span> da comissão do profissional</p>
                        <p><strong>Período:</strong> ${regra.data_inicio} ${regra.data_fim ? 'até ' + regra.data_fim : '(indeterminado)'}</p>
                        <p><strong>Status:</strong> ${regra.ativa ? '<span class="badge bg-success">Ativa</span>' : '<span class="badge bg-secondary">Inativa</span>'}</p>
                        ${regra.observacoes ? `<p><strong>Observações:</strong> ${regra.observacoes}</p>` : ''}

                        <hr>

                        <h5 style="color: #7C3AED; margin-bottom: 15px;">Estatísticas</h5>
                        <p><strong>Total de Atendimentos:</strong> ${calculos.total_atendimentos || 0}</p>
                        <p><strong>Valor Total Gerado:</strong> R$ ${(calculos.valor_total || 0).toFixed(2)}</p>
                        <p><strong>Comissão do Profissional:</strong> R$ ${(calculos.comissao_profissional || 0).toFixed(2)}</p>
                        <p><strong>Comissão do Assistente:</strong> <span style="color: #10B981; font-weight: bold;">R$ ${(calculos.comissao_assistente || 0).toFixed(2)}</span></p>
                    </div>
                `,
                width: '600px',
                showCloseButton: true,
                showConfirmButton: false
            });

        } else {
            Swal.fire('Erro', data.message || 'Não foi possível carregar os detalhes', 'error');
        }

    } catch (error) {
        console.error('Erro ao visualizar multicomissão:', error);
        Swal.fire('Erro', 'Não foi possível carregar os dados', 'error');
    }
};

/**
 * Ativar/Desativar regra de multicomissão
 */
window.toggleMulticomissao = async function(regraId, novoStatus) {
    try {
        const response = await fetch(`/api/multicomissao/regras/${regraId}/toggle`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ ativa: novoStatus })
        });

        const result = await response.json();

        if (result.success) {
            Swal.fire({
                icon: 'success',
                title: novoStatus ? 'Regra Ativada!' : 'Regra Desativada!',
                timer: 1500,
                showConfirmButton: false
            });

            // Recarregar lista
            if (typeof carregarMulticomissoes === 'function') {
                carregarMulticomissoes();
            }

        } else {
            Swal.fire('Erro', result.message || 'Não foi possível alterar o status', 'error');
        }

    } catch (error) {
        console.error('Erro ao toggle multicomissão:', error);
        Swal.fire('Erro', 'Não foi possível processar a solicitação', 'error');
    }
};

/**
 * Deletar regra de multicomissão
 */
window.deletarMulticomissao = async function(regraId) {
    const result = await Swal.fire({
        title: 'Confirmar exclusão?',
        text: 'Esta ação não pode ser desfeita!',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sim, deletar!',
        cancelButtonText: 'Cancelar'
    });

    if (result.isConfirmed) {
        try {
            const response = await fetch(`/api/multicomissao/regras/${regraId}`, {
                method: 'DELETE',
                credentials: 'include'
            });

            const data = await response.json();

            if (data.success) {
                Swal.fire('Deletado!', 'Regra removida com sucesso', 'success');

                // Recarregar lista
                if (typeof carregarMulticomissoes === 'function') {
                    carregarMulticomissoes();
                }

            } else {
                Swal.fire('Erro', data.message || 'Não foi possível deletar a regra', 'error');
            }

        } catch (error) {
            console.error('Erro ao deletar multicomissão:', error);
            Swal.fire('Erro', 'Não foi possível processar a solicitação', 'error');
        }
    }
};

console.log('✅ Sistema de Multicomissão carregado (12.1)');

// ============================================================================
// MELHORIAS NOS PROFISSIONAIS (Diretrizes 12.2 e 12.3)
// ============================================================================

/**
 * Visualizar profissional com detalhes completos
 * Diretriz 12.2: Detalhes muito mais completos
 */
window.visualizarProfissionalCompleto = async function(profissionalId) {
    try {
        Swal.fire({
            title: 'Carregando...',
            allowOutsideClick: false,
            didOpen: () => Swal.showLoading()
        });

        // Carregar dados completos do profissional
        const response = await fetch(`/api/profissionais/${profissionalId}/completo`, {
            credentials: 'include'
        });

        const data = await response.json();

        if (!data.success) {
            Swal.fire('Erro', 'Profissional não encontrado', 'error');
            return;
        }

        const prof = data.profissional;
        const stats = data.estatisticas || {};

        // Formatação de valores
        const formatMoney = (val) => `R$ ${(val || 0).toFixed(2)}`;
        const formatPercent = (val) => `${(val || 0).toFixed(1)}%`;

        Swal.fire({
            title: `<i class="bi bi-person-badge"></i> ${prof.nome}`,
            html: `
                <div style="text-align: left; max-height: 700px; overflow-y: auto; padding: 15px;">

                    <!-- Informações Básicas -->
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                        <p style="margin: 5px 0;"><strong>CPF:</strong> ${prof.cpf || 'Não informado'}</p>
                        <p style="margin: 5px 0;"><strong>Telefone:</strong> ${prof.telefone || 'Não informado'}</p>
                        <p style="margin: 5px 0;"><strong>Email:</strong> ${prof.email || 'Não informado'}</p>
                        <p style="margin: 5px 0;"><strong>Especialidade:</strong> ${prof.especialidade || 'Não informado'}</p>
                        <p style="margin: 5px 0;"><strong>Comissão:</strong> <span class="badge bg-success">${prof.comissao_percentual || 10}%</span></p>
                    </div>

                    <!-- Estatísticas de Performance -->
                    <h5 style="color: #7C3AED; margin-bottom: 15px;">
                        <i class="bi bi-graph-up"></i> Estatísticas de Performance
                    </h5>
                    <div class="row g-3 mb-4">
                        <div class="col-6">
                            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #7C3AED;">
                                <small class="text-muted">Total de Atendimentos</small>
                                <h4 style="margin: 5px 0; color: #7C3AED;">${stats.total_atendimentos || 0}</h4>
                            </div>
                        </div>
                        <div class="col-6">
                            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #10B981;">
                                <small class="text-muted">Faturamento Total</small>
                                <h4 style="margin: 5px 0; color: #10B981;">${formatMoney(stats.faturamento_total)}</h4>
                            </div>
                        </div>
                        <div class="col-6">
                            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #3B82F6;">
                                <small class="text-muted">Comissões Ganhas</small>
                                <h4 style="margin: 5px 0; color: #3B82F6;">${formatMoney(stats.comissoes_total)}</h4>
                            </div>
                        </div>
                        <div class="col-6">
                            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #F59E0B;">
                                <small class="text-muted">Ticket Médio</small>
                                <h4 style="margin: 5px 0; color: #F59E0B;">${formatMoney(stats.ticket_medio)}</h4>
                            </div>
                        </div>
                    </div>

                    <!-- Serviços Realizados -->
                    <h5 style="color: #7C3AED; margin-bottom: 15px;">
                        <i class="bi bi-list-check"></i> Top 5 Serviços
                    </h5>
                    <div class="mb-4">
                        ${stats.top_servicos && stats.top_servicos.length > 0
                            ? stats.top_servicos.map((s, idx) => `
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; background: ${idx % 2 === 0 ? '#f8f9fa' : '#fff'}; border-radius: 4px; margin-bottom: 5px;">
                                    <span><strong>${idx + 1}.</strong> ${s.servico || 'N/A'}</span>
                                    <span class="badge bg-primary">${s.quantidade} vezes</span>
                                </div>
                            `).join('')
                            : '<p class="text-muted text-center">Nenhum serviço realizado ainda</p>'
                        }
                    </div>

                    <!-- Agenda do Mês -->
                    <h5 style="color: #7C3AED; margin-bottom: 15px;">
                        <i class="bi bi-calendar-week"></i> Agenda do Mês
                    </h5>
                    <div class="mb-4">
                        <p><strong>Agendamentos este mês:</strong> ${stats.agendamentos_mes || 0}</p>
                        <p><strong>Dias trabalhados:</strong> ${stats.dias_trabalhados || 0}</p>
                        <p><strong>Taxa de ocupação:</strong> <span class="badge bg-info">${formatPercent(stats.taxa_ocupacao)}</span></p>
                    </div>

                    <!-- Ações Rápidas -->
                    <div style="margin-top: 25px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                        <h6 style="margin-bottom: 15px;"><i class="bi bi-lightning-fill"></i> Ações Rápidas</h6>
                        <div class="d-grid gap-2">
                            <button class="btn btn-primary" onclick="enviarOrdemServico('${profissionalId}', '${prof.nome}', '${prof.email || ''}', '${prof.telefone || ''}')">
                                <i class="bi bi-file-earmark-text"></i> Enviar Ordem de Serviço
                            </button>
                            <button class="btn btn-success" onclick="notificarProfissional('${profissionalId}', '${prof.nome}', '${prof.email || ''}', '${prof.telefone || ''}')">
                                <i class="bi bi-bell"></i> Enviar Notificação
                            </button>
                        </div>
                    </div>

                </div>
            `,
            width: '800px',
            showCloseButton: true,
            showConfirmButton: false,
            customClass: {
                popup: 'profissional-completo-modal'
            }
        });

    } catch (error) {
        console.error('Erro ao visualizar profissional:', error);
        Swal.fire('Erro', 'Não foi possível carregar os dados do profissional', 'error');
    }
};

/**
 * Enviar ordem de serviço para profissional
 * Diretriz 12.3: Email/WhatsApp para ordens de serviço
 */
window.enviarOrdemServico = async function(profissionalId, nomeProfissional, email, telefone) {
    const { value: formValues } = await Swal.fire({
        title: '<strong>📋 Ordem de Serviço</strong>',
        html: `
            <div style="text-align: left; padding: 10px; max-height: 600px; overflow-y: auto;">

                <p><strong>Profissional:</strong> ${nomeProfissional}</p>

                <div class="mb-3">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                        <i class="bi bi-calendar-event"></i> Data do Serviço *
                    </label>
                    <input type="date" id="os_data" class="form-control"
                           value="${new Date().toISOString().split('T')[0]}" required>
                </div>

                <div class="mb-3">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                        <i class="bi bi-clock"></i> Horário *
                    </label>
                    <input type="time" id="os_horario" class="form-control" required>
                </div>

                <div class="mb-3">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                        <i class="bi bi-person"></i> Cliente
                    </label>
                    <input type="text" id="os_cliente" class="form-control"
                           placeholder="Nome do cliente">
                </div>

                <div class="mb-3">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                        <i class="bi bi-list-task"></i> Serviço a Realizar *
                    </label>
                    <input type="text" id="os_servico" class="form-control"
                           placeholder="Ex: Limpeza de Pele Profunda" required>
                </div>

                <div class="mb-3">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                        <i class="bi bi-geo-alt"></i> Local
                    </label>
                    <input type="text" id="os_local" class="form-control"
                           placeholder="Endereço ou sala" value="Clínica Principal">
                </div>

                <div class="mb-3">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                        <i class="bi bi-chat-left-text"></i> Observações
                    </label>
                    <textarea id="os_observacoes" class="form-control" rows="3"
                              placeholder="Instruções especiais, materiais necessários, etc..."></textarea>
                </div>

                <div class="mb-3" style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                    <label style="display: block; margin-bottom: 10px; font-weight: 600;">
                        <i class="bi bi-send"></i> Enviar Ordem por (Diretriz 12.3)
                    </label>
                    <div class="form-check mb-2">
                        <input type="checkbox" class="form-check-input" id="os_notif_whatsapp"
                               ${telefone ? 'checked' : 'disabled'}>
                        <label class="form-check-label" for="os_notif_whatsapp">
                            <i class="bi bi-whatsapp" style="color: #25D366;"></i> WhatsApp
                            ${!telefone ? '<span class="text-muted">(sem telefone)</span>' : ''}
                        </label>
                    </div>
                    <div class="form-check">
                        <input type="checkbox" class="form-check-input" id="os_notif_email"
                               ${email ? 'checked' : 'disabled'}>
                        <label class="form-check-label" for="os_notif_email">
                            <i class="bi bi-envelope-fill" style="color: #3B82F6;"></i> Email
                            ${!email ? '<span class="text-muted">(sem email)</span>' : ''}
                        </label>
                    </div>
                </div>

            </div>
        `,
        showCancelButton: true,
        confirmButtonText: '<i class="bi bi-send-fill"></i> Enviar Ordem',
        cancelButtonText: 'Cancelar',
        width: '650px',
        preConfirm: () => {
            const data = document.getElementById('os_data').value;
            const horario = document.getElementById('os_horario').value;
            const cliente = document.getElementById('os_cliente').value.trim();
            const servico = document.getElementById('os_servico').value.trim();
            const local = document.getElementById('os_local').value.trim();
            const observacoes = document.getElementById('os_observacoes').value.trim();
            const notifWhatsApp = document.getElementById('os_notif_whatsapp').checked;
            const notifEmail = document.getElementById('os_notif_email').checked;

            // Validações
            if (!data || !horario || !servico) {
                Swal.showValidationMessage('Data, horário e serviço são obrigatórios');
                return false;
            }

            if (!notifWhatsApp && !notifEmail) {
                Swal.showValidationMessage('Selecione pelo menos um método de envio');
                return false;
            }

            return {
                data,
                horario,
                cliente: cliente || 'Não especificado',
                servico,
                local: local || 'Não especificado',
                observacoes: observacoes || '',
                notificacoes: {
                    whatsapp: notifWhatsApp,
                    email: notifEmail
                }
            };
        }
    });

    if (formValues) {
        await processarOrdemServico(profissionalId, nomeProfissional, email, telefone, formValues);
    }
};

/**
 * Processar envio de ordem de serviço
 */
async function processarOrdemServico(profissionalId, nomeProfissional, email, telefone, dados) {
    try {
        Swal.fire({
            title: 'Enviando...',
            text: 'Processando ordem de serviço',
            allowOutsideClick: false,
            didOpen: () => Swal.showLoading()
        });

        const response = await fetch(`/api/profissionais/${profissionalId}/ordem-servico`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                profissional_nome: nomeProfissional,
                profissional_email: email,
                profissional_telefone: telefone,
                ...dados
            })
        });

        const result = await response.json();

        if (result.success) {
            let mensagemSucesso = '<p><strong>Ordem de serviço enviada com sucesso!</strong></p>';

            if (result.notificacoes_enviadas) {
                mensagemSucesso += '<div style="margin-top: 10px; padding: 10px; background: #f0fdf4; border-radius: 4px;">';
                mensagemSucesso += '<strong style="color: #059669;">Enviado por:</strong><br>';
                if (result.notificacoes_enviadas.whatsapp) mensagemSucesso += '✓ WhatsApp<br>';
                if (result.notificacoes_enviadas.email) mensagemSucesso += '✓ Email';
                mensagemSucesso += '</div>';
            }

            await Swal.fire({
                icon: 'success',
                title: 'Enviado!',
                html: mensagemSucesso,
                timer: 3000
            });

        } else {
            Swal.fire('Erro', result.message || 'Não foi possível enviar a ordem', 'error');
        }

    } catch (error) {
        console.error('Erro ao enviar ordem de serviço:', error);
        Swal.fire('Erro', 'Não foi possível processar a solicitação', 'error');
    }
}

/**
 * Notificar profissional diretamente
 * Diretriz 12.3: Notificações Email/WhatsApp
 */
window.notificarProfissional = async function(profissionalId, nomeProfissional, email, telefone) {
    const { value: formValues } = await Swal.fire({
        title: '<strong>📧 Notificar Profissional</strong>',
        html: `
            <div style="text-align: left; padding: 10px;">
                <p><strong>Profissional:</strong> ${nomeProfissional}</p>

                <div class="mb-3">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                        Tipo de Notificação
                    </label>
                    <div class="form-check">
                        <input type="checkbox" class="form-check-input" id="prof_notif_whatsapp"
                               ${telefone ? 'checked' : 'disabled'}>
                        <label class="form-check-label" for="prof_notif_whatsapp">
                            <i class="bi bi-whatsapp" style="color: #25D366;"></i> WhatsApp
                        </label>
                    </div>
                    <div class="form-check">
                        <input type="checkbox" class="form-check-input" id="prof_notif_email"
                               ${email ? 'checked' : 'disabled'}>
                        <label class="form-check-label" for="prof_notif_email">
                            <i class="bi bi-envelope-fill" style="color: #3B82F6;"></i> Email
                        </label>
                    </div>
                </div>

                <div class="mb-3">
                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">
                        Mensagem
                    </label>
                    <textarea id="prof_notif_mensagem" class="form-control" rows="4"
                              placeholder="Digite a mensagem para o profissional..."></textarea>
                </div>
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: '<i class="bi bi-send"></i> Enviar',
        cancelButtonText: 'Cancelar',
        width: '550px',
        preConfirm: () => {
            const whatsapp = document.getElementById('prof_notif_whatsapp').checked;
            const emailNotif = document.getElementById('prof_notif_email').checked;
            const mensagem = document.getElementById('prof_notif_mensagem').value.trim();

            if (!whatsapp && !emailNotif) {
                Swal.showValidationMessage('Selecione pelo menos um tipo de notificação');
                return false;
            }

            if (!mensagem) {
                Swal.showValidationMessage('A mensagem é obrigatória');
                return false;
            }

            return { whatsapp, email: emailNotif, mensagem };
        }
    });

    if (formValues) {
        await enviarNotificacaoProfissional(profissionalId, nomeProfissional, email, telefone, formValues);
    }
};

/**
 * Enviar notificação ao profissional
 */
async function enviarNotificacaoProfissional(profissionalId, nomeProfissional, email, telefone, dados) {
    try {
        Swal.fire({
            title: 'Enviando...',
            allowOutsideClick: false,
            didOpen: () => Swal.showLoading()
        });

        const response = await fetch(`/api/profissionais/${profissionalId}/notificar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                profissional_nome: nomeProfissional,
                profissional_email: email,
                profissional_telefone: telefone,
                mensagem: dados.mensagem,
                notificacoes: {
                    whatsapp: dados.whatsapp,
                    email: dados.email
                }
            })
        });

        const result = await response.json();

        if (result.success) {
            let msg = '<strong>Notificação enviada com sucesso!</strong><br>';
            if (result.notificacoes_enviadas.whatsapp) msg += '✓ WhatsApp<br>';
            if (result.notificacoes_enviadas.email) msg += '✓ Email';

            Swal.fire({
                icon: 'success',
                title: 'Enviado!',
                html: msg,
                timer: 2500
            });
        } else {
            Swal.fire('Erro', result.message || 'Não foi possível enviar a notificação', 'error');
        }

    } catch (error) {
        console.error('Erro ao enviar notificação:', error);
        Swal.fire('Erro', 'Não foi possível processar a solicitação', 'error');
    }
}

// ==================== HISTÓRICO DE ATENDIMENTOS (Diretriz 12.4) ====================

/**
 * Visualizar histórico completo de atendimentos do profissional
 */
window.visualizarHistoricoProfissional = async function(profissionalId) {
    try {
        Swal.fire({
            title: 'Carregando histórico...',
            allowOutsideClick: false,
            didOpen: () => Swal.showLoading()
        });

        // Buscar histórico sem filtros (padrão: últimos 50)
        const response = await fetch(`/api/profissionais/${profissionalId}/historico?limite=50&pagina=1`, {
            credentials: 'include'
        });

        const data = await response.json();

        if (!data.success) {
            Swal.fire('Erro', data.message || 'Não foi possível carregar o histórico', 'error');
            return;
        }

        const prof = data.profissional;
        const atendimentos = data.atendimentos || [];
        const stats = data.estatisticas || {};
        const paginacao = data.paginacao || {};

        // Construir tabela de atendimentos
        let tabelaHtml = '';
        if (atendimentos.length === 0) {
            tabelaHtml = '<p class="text-center text-muted">Nenhum atendimento encontrado</p>';
        } else {
            tabelaHtml = `
                <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
                    <table class="table table-striped table-hover table-sm">
                        <thead class="table-dark sticky-top">
                            <tr>
                                <th>Data</th>
                                <th>Horário</th>
                                <th>Cliente</th>
                                <th>Serviço</th>
                                <th>Valor</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            atendimentos.forEach(atend => {
                const data = atend.data ? formatarData(atend.data) : '-';
                const horario = atend.horario || '-';
                const cliente = atend.cliente_nome || 'Não informado';
                const servico = atend.servico_nome || 'Não informado';
                const valor = atend.valor_total || atend.valor_servico || 0;
                const valorFormatado = formatarMoeda(valor);
                const status = atend.status || 'desconhecido';
                const badgeStatus = getBadgeClassStatus(status);

                tabelaHtml += `
                    <tr>
                        <td>${data}</td>
                        <td>${horario}</td>
                        <td>${cliente}</td>
                        <td>${servico}</td>
                        <td>${valorFormatado}</td>
                        <td><span class="badge ${badgeStatus}">${status}</span></td>
                    </tr>
                `;
            });

            tabelaHtml += `
                        </tbody>
                    </table>
                </div>
            `;
        }

        // Estatísticas do histórico
        const statsHtml = `
            <div class="row g-2 mb-3">
                <div class="col-md-3">
                    <div class="card bg-primary text-white">
                        <div class="card-body p-2 text-center">
                            <h6 class="mb-0">${stats.total_atendimentos || 0}</h6>
                            <small>Total</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-success text-white">
                        <div class="card-body p-2 text-center">
                            <h6 class="mb-0">${stats.atendimentos_concluidos || 0}</h6>
                            <small>Concluídos</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-danger text-white">
                        <div class="card-body p-2 text-center">
                            <h6 class="mb-0">${stats.atendimentos_cancelados || 0}</h6>
                            <small>Cancelados</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-info text-white">
                        <div class="card-body p-2 text-center">
                            <h6 class="mb-0">${stats.taxa_conclusao || 0}%</h6>
                            <small>Taxa Conclusão</small>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row g-2 mb-3">
                <div class="col-md-4">
                    <div class="card bg-light">
                        <div class="card-body p-2 text-center">
                            <h6 class="mb-0">${formatarMoeda(stats.faturamento_total || 0)}</h6>
                            <small>Faturamento Total</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card bg-light">
                        <div class="card-body p-2 text-center">
                            <h6 class="mb-0">${formatarMoeda(stats.ticket_medio || 0)}</h6>
                            <small>Ticket Médio</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card bg-light">
                        <div class="card-body p-2 text-center">
                            <h6 class="mb-0">${stats.clientes_atendidos || 0}</h6>
                            <small>Clientes Únicos</small>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Paginação info
        const paginacaoHtml = `
            <p class="text-muted text-center mb-2">
                Página ${paginacao.pagina_atual || 1} de ${paginacao.total_paginas || 1}
                (${paginacao.total_registros || 0} registros no total)
            </p>
        `;

        Swal.fire({
            title: `<i class="bi bi-clock-history"></i> Histórico - ${prof.nome}`,
            html: `
                <div class="text-start">
                    ${statsHtml}
                    ${tabelaHtml}
                    ${paginacaoHtml}
                    <div class="d-flex gap-2 justify-content-center mt-3">
                        <button class="btn btn-sm btn-primary" onclick="abrirFiltrosHistorico('${profissionalId}')">
                            <i class="bi bi-funnel"></i> Filtrar
                        </button>
                        <button class="btn btn-sm btn-info" onclick="visualizarTimelineProfissional('${profissionalId}')">
                            <i class="bi bi-graph-up"></i> Timeline
                        </button>
                    </div>
                </div>
            `,
            width: '900px',
            showCloseButton: true,
            showConfirmButton: false
        });

    } catch (error) {
        console.error('Erro ao visualizar histórico:', error);
        Swal.fire('Erro', 'Não foi possível carregar o histórico', 'error');
    }
};

/**
 * Abrir modal de filtros para o histórico
 */
window.abrirFiltrosHistorico = async function(profissionalId) {
    const { value: formValues } = await Swal.fire({
        title: '<strong><i class="bi bi-funnel"></i> Filtrar Histórico</strong>',
        html: `
            <div class="text-start">
                <div class="mb-3">
                    <label class="form-label">Data Início</label>
                    <input type="date" id="filtro-data-inicio" class="form-control">
                </div>
                <div class="mb-3">
                    <label class="form-label">Data Fim</label>
                    <input type="date" id="filtro-data-fim" class="form-control">
                </div>
                <div class="mb-3">
                    <label class="form-label">Status</label>
                    <select id="filtro-status" class="form-select">
                        <option value="">Todos</option>
                        <option value="pendente">Pendente</option>
                        <option value="confirmado">Confirmado</option>
                        <option value="em_andamento">Em Andamento</option>
                        <option value="concluido">Concluído</option>
                        <option value="cancelado">Cancelado</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">Buscar Serviço</label>
                    <input type="text" id="filtro-servico" class="form-control" placeholder="Nome do serviço...">
                </div>
            </div>
        `,
        width: '500px',
        showCancelButton: true,
        confirmButtonText: 'Aplicar Filtros',
        cancelButtonText: 'Cancelar',
        preConfirm: () => {
            return {
                data_inicio: document.getElementById('filtro-data-inicio').value,
                data_fim: document.getElementById('filtro-data-fim').value,
                status: document.getElementById('filtro-status').value,
                servico: document.getElementById('filtro-servico').value
            };
        }
    });

    if (formValues) {
        await visualizarHistoricoFiltrado(profissionalId, formValues);
    }
};

/**
 * Visualizar histórico com filtros aplicados
 */
async function visualizarHistoricoFiltrado(profissionalId, filtros) {
    try {
        Swal.fire({
            title: 'Aplicando filtros...',
            allowOutsideClick: false,
            didOpen: () => Swal.showLoading()
        });

        // Construir query string
        const params = new URLSearchParams();
        params.append('limite', '50');
        params.append('pagina', '1');
        if (filtros.data_inicio) params.append('data_inicio', filtros.data_inicio);
        if (filtros.data_fim) params.append('data_fim', filtros.data_fim);
        if (filtros.status) params.append('status', filtros.status);
        if (filtros.servico) params.append('servico', filtros.servico);

        const response = await fetch(`/api/profissionais/${profissionalId}/historico?${params.toString()}`, {
            credentials: 'include'
        });

        const data = await response.json();

        if (!data.success) {
            Swal.fire('Erro', data.message || 'Não foi possível aplicar os filtros', 'error');
            return;
        }

        const atendimentos = data.atendimentos || [];
        const stats = data.estatisticas || {};

        // Construir tabela
        let tabelaHtml = '';
        if (atendimentos.length === 0) {
            tabelaHtml = '<p class="text-center text-muted">Nenhum atendimento encontrado com esses filtros</p>';
        } else {
            tabelaHtml = `
                <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
                    <table class="table table-striped table-hover table-sm">
                        <thead class="table-dark sticky-top">
                            <tr>
                                <th>Data</th>
                                <th>Cliente</th>
                                <th>Serviço</th>
                                <th>Valor</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            atendimentos.forEach(atend => {
                const data_formatada = atend.data ? formatarData(atend.data) : '-';
                const cliente = atend.cliente_nome || 'Não informado';
                const servico = atend.servico_nome || 'Não informado';
                const valor = formatarMoeda(atend.valor_total || atend.valor_servico || 0);
                const badgeStatus = getBadgeClassStatus(atend.status || 'desconhecido');

                tabelaHtml += `
                    <tr>
                        <td>${data_formatada}</td>
                        <td>${cliente}</td>
                        <td>${servico}</td>
                        <td>${valor}</td>
                        <td><span class="badge ${badgeStatus}">${atend.status || '-'}</span></td>
                    </tr>
                `;
            });

            tabelaHtml += '</tbody></table></div>';
        }

        // Mostrar resultados filtrados
        Swal.fire({
            title: '<i class="bi bi-funnel-fill"></i> Resultados Filtrados',
            html: `
                <div class="text-start">
                    <div class="alert alert-info mb-3">
                        <strong>Filtros aplicados:</strong><br>
                        ${filtros.data_inicio ? `Data Início: ${formatarData(filtros.data_inicio)}<br>` : ''}
                        ${filtros.data_fim ? `Data Fim: ${formatarData(filtros.data_fim)}<br>` : ''}
                        ${filtros.status ? `Status: ${filtros.status}<br>` : ''}
                        ${filtros.servico ? `Serviço: ${filtros.servico}<br>` : ''}
                    </div>
                    <div class="row g-2 mb-3">
                        <div class="col-4">
                            <div class="card bg-primary text-white">
                                <div class="card-body p-2 text-center">
                                    <h6 class="mb-0">${stats.total_atendimentos || 0}</h6>
                                    <small>Encontrados</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="card bg-success text-white">
                                <div class="card-body p-2 text-center">
                                    <h6 class="mb-0">${stats.atendimentos_concluidos || 0}</h6>
                                    <small>Concluídos</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="card bg-info text-white">
                                <div class="card-body p-2 text-center">
                                    <h6 class="mb-0">${formatarMoeda(stats.faturamento_total || 0)}</h6>
                                    <small>Faturamento</small>
                                </div>
                            </div>
                        </div>
                    </div>
                    ${tabelaHtml}
                </div>
            `,
            width: '800px',
            showCloseButton: true,
            showConfirmButton: false
        });

    } catch (error) {
        console.error('Erro ao aplicar filtros:', error);
        Swal.fire('Erro', 'Não foi possível aplicar os filtros', 'error');
    }
}

/**
 * Visualizar timeline mensal de atendimentos
 */
window.visualizarTimelineProfissional = async function(profissionalId) {
    try {
        Swal.fire({
            title: 'Carregando timeline...',
            allowOutsideClick: false,
            didOpen: () => Swal.showLoading()
        });

        const response = await fetch(`/api/profissionais/${profissionalId}/timeline`, {
            credentials: 'include'
        });

        const data = await response.json();

        if (!data.success) {
            Swal.fire('Erro', data.message || 'Não foi possível carregar a timeline', 'error');
            return;
        }

        const prof = data.profissional;
        const timeline = data.timeline || [];

        if (timeline.length === 0) {
            Swal.fire('Info', 'Nenhum dado de timeline disponível', 'info');
            return;
        }

        // Construir gráfico de barras simples com HTML/CSS
        let timelineHtml = '<div style="max-height: 400px; overflow-y: auto;">';

        timeline.forEach(item => {
            const percentual = item.total_atendimentos > 0 ? (item.concluidos / item.total_atendimentos * 100) : 0;
            const barWidth = Math.min(percentual, 100);

            timelineHtml += `
                <div class="mb-3">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <strong>${item.label}</strong>
                        <span class="badge bg-primary">${item.total_atendimentos} atendimentos</span>
                    </div>
                    <div class="progress" style="height: 25px;">
                        <div class="progress-bar bg-success" role="progressbar"
                             style="width: ${barWidth}%"
                             aria-valuenow="${percentual}" aria-valuemin="0" aria-valuemax="100">
                            ${item.concluidos} concluídos (${item.taxa_conclusao}%)
                        </div>
                    </div>
                    <div class="text-muted small mt-1">
                        Cancelados: ${item.cancelados}
                    </div>
                </div>
            `;
        });

        timelineHtml += '</div>';

        Swal.fire({
            title: `<i class="bi bi-graph-up"></i> Timeline - ${prof.nome}`,
            html: `
                <div class="text-start">
                    <p class="text-muted mb-3">Últimos 12 meses de atividade</p>
                    ${timelineHtml}
                </div>
            `,
            width: '700px',
            showCloseButton: true,
            showConfirmButton: false
        });

    } catch (error) {
        console.error('Erro ao visualizar timeline:', error);
        Swal.fire('Erro', 'Não foi possível carregar a timeline', 'error');
    }
};

/**
 * Helper: Badge de status para atendimentos
 */
function getBadgeClassStatus(status) {
    const badges = {
        'pendente': 'bg-warning',
        'confirmado': 'bg-info',
        'em_andamento': 'bg-primary',
        'concluido': 'bg-success',
        'cancelado': 'bg-danger',
        'desconhecido': 'bg-secondary'
    };
    return badges[status] || 'bg-secondary';
}

// ==================== SISTEMA DE NÍVEIS DE ACESSO (Diretriz 5.1) ====================

// Variável global para armazenar perfil do usuário
window.perfilUsuario = null;

/**
 * Carregar perfil do usuário logado
 */
async function carregarPerfilUsuario() {
    try {
        const response = await fetch('/api/usuarios/meu-perfil', {
            credentials: 'include'
        });

        const data = await response.json();

        if (data.success) {
            window.perfilUsuario = data.perfil;
            console.log('Perfil carregado:', window.perfilUsuario.nivel_nome);
            return data.perfil;
        }

    } catch (error) {
        console.error('Erro ao carregar perfil:', error);
    }

    return null;
}

/**
 * Verificar se usuário tem permissão específica
 */
window.verificarPermissao = async function(permissao) {
    try {
        const response = await fetch(`/api/verificar-permissao/${permissao}`, {
            credentials: 'include'
        });

        const data = await response.json();
        return data.success && data.tem_permissao;

    } catch (error) {
        console.error('Erro ao verificar permissão:', error);
        return false;
    }
};

/**
 * Verificar se usuário tem nível mínimo
 */
function verificarNivelMinimo(nivelMinimo) {
    if (!window.perfilUsuario) return false;

    const niveis = { 'profissional': 1, 'gestor': 2, 'admin': 3 };
    const nivelUsuario = niveis[window.perfilUsuario.nivel_acesso] || 1;
    const nivelRequerido = niveis[nivelMinimo] || 1;

    return nivelUsuario >= nivelRequerido;
}

/**
 * Gerenciar usuários (somente admin/gestor)
 */
window.gerenciarUsuarios = async function() {
    try {
        // Verificar permissão
        if (!window.perfilUsuario || !verificarNivelMinimo('gestor')) {
            Swal.fire('Acesso Negado', 'Você não tem permissão para gerenciar usuários', 'error');
            return;
        }

        Swal.fire({
            title: 'Carregando usuários...',
            allowOutsideClick: false,
            didOpen: () => Swal.showLoading()
        });

        const response = await fetch('/api/usuarios', {
            credentials: 'include'
        });

        const data = await response.json();

        if (!data.success) {
            Swal.fire('Erro', data.message || 'Não foi possível carregar usuários', 'error');
            return;
        }

        const usuarios = data.usuarios || [];

        // Construir tabela de usuários
        let tabelaHtml = `
            <div class="table-responsive" style="max-height: 500px; overflow-y: auto;">
                <table class="table table-striped table-hover">
                    <thead class="table-dark sticky-top">
                        <tr>
                            <th>Nome</th>
                            <th>Email</th>
                            <th>Nível de Acesso</th>
                            <th>Status</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        usuarios.forEach(usuario => {
            const badgeNivel = usuario.nivel_numero === 3 ? 'bg-danger' :
                              usuario.nivel_numero === 2 ? 'bg-warning' : 'bg-info';
            const badgeStatus = usuario.ativo ? 'bg-success' : 'bg-secondary';
            const isAdmin = verificarNivelMinimo('admin');

            // Não permitir editar próprio usuário
            const isProprio = usuario.id === window.perfilUsuario.id;

            tabelaHtml += `
                <tr>
                    <td>${usuario.nome}</td>
                    <td>${usuario.email}</td>
                    <td><span class="badge ${badgeNivel}">${usuario.nivel_nome}</span></td>
                    <td><span class="badge ${badgeStatus}">${usuario.ativo ? 'Ativo' : 'Inativo'}</span></td>
                    <td>
                        ${isAdmin && !isProprio ? `
                            <button class="btn btn-sm btn-primary" onclick="alterarNivelAcesso('${usuario.id}', '${usuario.nome}', '${usuario.nivel_acesso}')">
                                <i class="bi bi-key"></i>
                            </button>
                            <button class="btn btn-sm ${usuario.ativo ? 'btn-warning' : 'btn-success'}"
                                    onclick="toggleUsuarioAtivo('${usuario.id}', '${usuario.nome}', ${usuario.ativo})">
                                <i class="bi bi-${usuario.ativo ? 'pause' : 'play'}"></i>
                            </button>
                        ` : '<span class="text-muted">-</span>'}
                    </td>
                </tr>
            `;
        });

        tabelaHtml += `
                    </tbody>
                </table>
            </div>
        `;

        Swal.fire({
            title: '<i class="bi bi-people"></i> Gerenciar Usuários',
            html: `
                <div class="text-start">
                    <p class="text-muted mb-3">Total: ${usuarios.length} usuários</p>
                    ${tabelaHtml}
                    ${isAdmin ? `
                        <div class="alert alert-info mt-3">
                            <strong><i class="bi bi-info-circle"></i> Informações:</strong><br>
                            <i class="bi bi-key"></i> = Alterar nível de acesso<br>
                            <i class="bi bi-pause"></i> = Desativar usuário<br>
                            <i class="bi bi-play"></i> = Ativar usuário
                        </div>
                    ` : ''}
                </div>
            `,
            width: '900px',
            showCloseButton: true,
            showConfirmButton: false
        });

    } catch (error) {
        console.error('Erro ao gerenciar usuários:', error);
        Swal.fire('Erro', 'Não foi possível carregar usuários', 'error');
    }
};

/**
 * Alterar nível de acesso de um usuário
 */
window.alterarNivelAcesso = async function(usuarioId, nomeUsuario, nivelAtual) {
    try {
        const { value: novoNivel } = await Swal.fire({
            title: `<strong>Alterar Nível de Acesso</strong>`,
            html: `
                <div class="text-start">
                    <p><strong>Usuário:</strong> ${nomeUsuario}</p>
                    <p><strong>Nível atual:</strong> <span class="badge bg-secondary">${nivelAtual}</span></p>
                    <hr>
                    <div class="mb-3">
                        <label class="form-label">Novo Nível de Acesso</label>
                        <select id="select-nivel" class="form-select">
                            <option value="profissional" ${nivelAtual === 'profissional' ? 'selected' : ''}>
                                Profissional (Nível 1)
                            </option>
                            <option value="gestor" ${nivelAtual === 'gestor' ? 'selected' : ''}>
                                Gestor (Nível 2)
                            </option>
                            <option value="admin" ${nivelAtual === 'admin' ? 'selected' : ''}>
                                Administrador (Nível 3)
                            </option>
                        </select>
                    </div>
                    <div class="alert alert-warning">
                        <small>
                            <strong>Profissional:</strong> Acesso limitado a próprios agendamentos<br>
                            <strong>Gestor:</strong> Acesso a relatórios e gestão<br>
                            <strong>Admin:</strong> Acesso total ao sistema
                        </small>
                    </div>
                </div>
            `,
            width: '500px',
            showCancelButton: true,
            confirmButtonText: 'Alterar',
            cancelButtonText: 'Cancelar',
            preConfirm: () => {
                return document.getElementById('select-nivel').value;
            }
        });

        if (novoNivel && novoNivel !== nivelAtual) {
            Swal.fire({
                title: 'Alterando...',
                allowOutsideClick: false,
                didOpen: () => Swal.showLoading()
            });

            const response = await fetch(`/api/usuarios/${usuarioId}/nivel-acesso`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ nivel_acesso: novoNivel })
            });

            const result = await response.json();

            if (result.success) {
                await Swal.fire('Sucesso!', result.message, 'success');
                gerenciarUsuarios(); // Recarregar lista
            } else {
                Swal.fire('Erro', result.message, 'error');
            }
        }

    } catch (error) {
        console.error('Erro ao alterar nível:', error);
        Swal.fire('Erro', 'Não foi possível alterar o nível de acesso', 'error');
    }
};

/**
 * Ativar/desativar usuário
 */
window.toggleUsuarioAtivo = async function(usuarioId, nomeUsuario, ativoAtual) {
    try {
        const acao = ativoAtual ? 'desativar' : 'ativar';

        const confirmar = await Swal.fire({
            title: `${acao.charAt(0).toUpperCase() + acao.slice(1)} Usuário?`,
            html: `
                <p>Tem certeza que deseja ${acao} o usuário <strong>${nomeUsuario}</strong>?</p>
                ${ativoAtual ? '<p class="text-danger">O usuário não poderá fazer login enquanto estiver inativo.</p>' : ''}
            `,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: `Sim, ${acao}`,
            cancelButtonText: 'Cancelar'
        });

        if (confirmar.isConfirmed) {
            Swal.fire({
                title: 'Processando...',
                allowOutsideClick: false,
                didOpen: () => Swal.showLoading()
            });

            const response = await fetch(`/api/usuarios/${usuarioId}/ativar`, {
                method: 'PUT',
                credentials: 'include'
            });

            const result = await response.json();

            if (result.success) {
                await Swal.fire('Sucesso!', result.message, 'success');
                gerenciarUsuarios(); // Recarregar lista
            } else {
                Swal.fire('Erro', result.message, 'error');
            }
        }

    } catch (error) {
        console.error('Erro ao alterar status:', error);
        Swal.fire('Erro', 'Não foi possível alterar o status do usuário', 'error');
    }
};

/**
 * Visualizar meu perfil
 */
window.visualizarMeuPerfil = async function() {
    try {
        const perfil = await carregarPerfilUsuario();

        if (!perfil) {
            Swal.fire('Erro', 'Não foi possível carregar seu perfil', 'error');
            return;
        }

        const badgeNivel = perfil.nivel_numero === 3 ? 'bg-danger' :
                          perfil.nivel_numero === 2 ? 'bg-warning' : 'bg-info';

        Swal.fire({
            title: '<i class="bi bi-person-circle"></i> Meu Perfil',
            html: `
                <div class="text-start">
                    <div class="card mb-3">
                        <div class="card-body">
                            <h5>${perfil.nome}</h5>
                            <p class="text-muted mb-2">${perfil.email}</p>
                            <p><strong>Nível de Acesso:</strong> <span class="badge ${badgeNivel}">${perfil.nivel_nome}</span></p>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header bg-light">
                            <strong>Minhas Permissões</strong>
                        </div>
                        <div class="card-body">
                            ${perfil.permissoes.includes('*') ?
                                '<p class="text-success"><i class="bi bi-check-circle-fill"></i> Acesso total ao sistema</p>' :
                                '<ul class="list-unstyled mb-0">' +
                                perfil.permissoes.map(p => `<li><i class="bi bi-check"></i> ${formatarPermissao(p)}</li>`).join('') +
                                '</ul>'
                            }
                        </div>
                    </div>
                </div>
            `,
            width: '600px',
            showCloseButton: true,
            showConfirmButton: false
        });

    } catch (error) {
        console.error('Erro ao visualizar perfil:', error);
        Swal.fire('Erro', 'Não foi possível carregar perfil', 'error');
    }
};

/**
 * Formatar nome de permissão para exibição
 */
function formatarPermissao(permissao) {
    const map = {
        'visualizar_orcamentos': 'Visualizar Orçamentos',
        'visualizar_clientes': 'Visualizar Clientes',
        'visualizar_profissionais': 'Visualizar Profissionais',
        'visualizar_relatorios': 'Visualizar Relatórios',
        'visualizar_financeiro': 'Visualizar Financeiro',
        'visualizar_agendamentos': 'Visualizar Agendamentos',
        'visualizar_estoque': 'Visualizar Estoque',
        'editar_orcamentos': 'Editar Orçamentos',
        'editar_clientes': 'Editar Clientes',
        'aprovar_orcamentos': 'Aprovar Orçamentos',
        'visualizar_proprios_agendamentos': 'Visualizar Próprios Agendamentos',
        'visualizar_proprios_orcamentos': 'Visualizar Próprios Orçamentos',
        'visualizar_clientes_basico': 'Visualizar Clientes (Básico)',
        'atualizar_status_agendamento': 'Atualizar Status de Agendamento'
    };

    return map[permissao] || permissao;
}

// ==================== LAYOUT MELHORADO DO CONTRATO (Diretriz 1.3) ====================

/**
 * Imprimir contrato com layout profissional melhorado
 */
window.imprimirContratoMelhorado = async function(orcamentoId) {
    try {
        Swal.fire({
            title: 'Gerando contrato...',
            allowOutsideClick: false,
            didOpen: () => Swal.showLoading()
        });

        // Buscar orçamento
        const response = await fetch(`/api/orcamentos/${orcamentoId}`, {
            credentials: 'include'
        });

        const data = await response.json();

        if (!data.success || !data.orcamento) {
            Swal.fire('Erro', 'Orçamento não encontrado', 'error');
            return;
        }

        const orc = data.orcamento;

        // Tentar gerar PDF via backend primeiro
        const pdfRes = await fetch(`/api/orcamentos/${orcamentoId}/pdf`, {
            method: 'GET',
            credentials: 'include'
        });

        if (pdfRes.ok) {
            // PDF gerado com sucesso - baixar
            const blob = await pdfRes.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `contrato_${orc.numero || orcamentoId}_bioma.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            Swal.fire({
                icon: 'success',
                title: 'Contrato Gerado!',
                text: 'O PDF do contrato foi baixado com sucesso',
                timer: 2500,
                showConfirmButton: false
            });
        } else {
            // Fallback: HTML melhorado
            Swal.close();
            gerarContratoHTML(orc, orcamentoId);
        }

    } catch (error) {
        console.error('Erro ao imprimir contrato:', error);
        Swal.fire('Erro', 'Não foi possível gerar o contrato', 'error');
    }
};

/**
 * Gerar HTML melhorado do contrato
 */
function gerarContratoHTML(orc, orcamentoId) {
    const hoje = new Date().toLocaleDateString('pt-BR', { day: '2-digit', month: 'long', year: 'numeric' });

    // Calcular totais
    const subtotalServicos = (orc.servicos || []).reduce((acc, s) =>
        acc + ((s.quantidade || 1) * (s.preco || 0)), 0);
    const subtotalProdutos = (orc.produtos || []).reduce((acc, p) =>
        acc + ((p.quantidade || 1) * (p.preco || 0)), 0);
    const subtotal = subtotalServicos + subtotalProdutos;
    const desconto = orc.desconto_global || 0;
    const cashback = orc.cashback_valor || 0;
    const total = orc.total_final || subtotal - desconto;

    // Status badge
    const statusColors = {
        'pendente': '#FFA500',
        'aprovado': '#28A745',
        'cancelado': '#DC3545',
        'em_andamento': '#007BFF'
    };
    const statusColor = statusColors[orc.status?.toLowerCase()] || '#6C757D';

    const printWindow = window.open('', '_blank', 'width=1024,height=768');
    printWindow.document.write(`
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contrato de Serviços - BIOMA #${orc.numero || orcamentoId}</title>
    <style>
        /* Reset e Base */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
            background: #fff;
            padding: 0;
        }

        .container {
            max-width: 210mm;
            margin: 0 auto;
            padding: 20mm;
            background: white;
        }

        /* Cabeçalho */
        .header {
            border-bottom: 4px solid #7C3AED;
            padding-bottom: 20px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }

        .logo-section {
            flex: 1;
        }

        .logo-placeholder {
            width: 120px;
            height: 60px;
            background: linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .company-info {
            font-size: 9pt;
            color: #666;
            line-height: 1.4;
        }

        .header-right {
            text-align: right;
        }

        .document-title {
            font-size: 24px;
            font-weight: bold;
            color: #7C3AED;
            margin-bottom: 5px;
        }

        .document-number {
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }

        .status-badge {
            display: inline-block;
            padding: 6px 16px;
            background-color: ${statusColor};
            color: white;
            border-radius: 20px;
            font-size: 10pt;
            font-weight: 600;
            text-transform: uppercase;
        }

        /* Informações do Cliente */
        .section-title {
            font-size: 16px;
            font-weight: bold;
            color: #7C3AED;
            border-bottom: 2px solid #E9ECEF;
            padding-bottom: 8px;
            margin-top: 25px;
            margin-bottom: 15px;
        }

        .client-info {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px 30px;
            background: #F8F9FA;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #7C3AED;
        }

        .info-item {
            display: flex;
            flex-direction: column;
        }

        .info-label {
            font-size: 9pt;
            color: #666;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }

        .info-value {
            font-size: 11pt;
            color: #333;
            font-weight: 500;
        }

        /* Tabelas */
        .table-container {
            margin: 20px 0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }

        thead {
            background: linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%);
            color: white;
        }

        th {
            padding: 14px 12px;
            text-align: left;
            font-weight: 600;
            font-size: 10pt;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        th:last-child,
        td:last-child {
            text-align: right;
        }

        tbody tr {
            border-bottom: 1px solid #E9ECEF;
        }

        tbody tr:nth-child(even) {
            background-color: #F8F9FA;
        }

        tbody tr:hover {
            background-color: #EDE9FE;
        }

        td {
            padding: 12px;
            font-size: 10pt;
        }

        .item-name {
            font-weight: 600;
            color: #333;
        }

        .item-desc {
            font-size: 9pt;
            color: #666;
            margin-top: 2px;
        }

        /* Totais */
        .totals-section {
            margin-top: 30px;
            background: #F8F9FA;
            border-radius: 8px;
            padding: 20px;
            border: 2px solid #E9ECEF;
        }

        .total-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            font-size: 11pt;
        }

        .total-row.subtotal {
            border-bottom: 1px solid #DEE2E6;
        }

        .total-row.discount {
            color: #28A745;
        }

        .total-row.cashback {
            color: #FFA500;
        }

        .total-row.final {
            border-top: 2px solid #7C3AED;
            margin-top: 10px;
            padding-top: 15px;
            font-size: 16pt;
            font-weight: bold;
            color: #7C3AED;
        }

        .total-label {
            font-weight: 600;
        }

        .total-value {
            font-weight: 700;
        }

        /* Termos e Condições */
        .terms-box {
            margin-top: 30px;
            padding: 20px;
            background: #FFFBEB;
            border-left: 4px solid #F59E0B;
            border-radius: 4px;
        }

        .terms-title {
            font-weight: bold;
            color: #92400E;
            margin-bottom: 10px;
            font-size: 12pt;
        }

        .terms-content {
            font-size: 9pt;
            color: #78350F;
            line-height: 1.5;
        }

        /* Assinaturas */
        .signatures {
            margin-top: 60px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
        }

        .signature-box {
            text-align: center;
        }

        .signature-line {
            border-top: 2px solid #333;
            margin-bottom: 12px;
            padding-top: 60px;
        }

        .signature-label {
            font-weight: 600;
            font-size: 10pt;
            color: #666;
        }

        .signature-sublabel {
            font-size: 8pt;
            color: #999;
            margin-top: 4px;
        }

        /* Rodapé */
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #E9ECEF;
            text-align: center;
            font-size: 8pt;
            color: #999;
        }

        .footer-row {
            margin: 5px 0;
        }

        /* Watermark Status */
        .watermark {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-45deg);
            font-size: 120px;
            font-weight: bold;
            color: ${statusColor};
            opacity: 0.08;
            z-index: -1;
            pointer-events: none;
            white-space: nowrap;
        }

        /* Botão de Impressão */
        .print-button {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 14px 28px;
            background: linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
            transition: all 0.3s ease;
            z-index: 1000;
        }

        .print-button:hover {
            background: linear-gradient(135deg, #6D28D9 0%, #5B21B6 100%);
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(124, 58, 237, 0.4);
        }

        /* Print Styles */
        @media print {
            body {
                padding: 0;
                margin: 0;
            }

            .container {
                max-width: 100%;
                padding: 15mm;
            }

            .print-button {
                display: none;
            }

            .signatures {
                page-break-inside: avoid;
            }

            .table-container {
                page-break-inside: avoid;
            }

            .totals-section {
                page-break-inside: avoid;
            }

            .terms-box {
                page-break-inside: avoid;
            }

            @page {
                size: A4;
                margin: 15mm;
            }
        }

        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #999;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="watermark">${orc.status?.toUpperCase() || 'PENDENTE'}</div>

    <button class="print-button" onclick="window.print()">
        🖨️ Imprimir Contrato
    </button>

    <div class="container">
        <!-- Cabeçalho -->
        <div class="header">
            <div class="logo-section">
                <div class="logo-placeholder">BIOMA</div>
                <div class="company-info">
                    <strong>BIOMA Estética & Bem-Estar</strong><br>
                    CNPJ: 00.000.000/0001-00<br>
                    contato@bioma.com.br | (11) 0000-0000
                </div>
            </div>
            <div class="header-right">
                <div class="document-title">CONTRATO DE SERVIÇOS</div>
                <div class="document-number">#${orc.numero || orcamentoId}</div>
                <span class="status-badge">${orc.status || 'Pendente'}</span>
                <div style="margin-top: 10px; font-size: 9pt; color: #666;">
                    ${hoje}
                </div>
            </div>
        </div>

        <!-- Informações do Cliente -->
        <div class="section-title">📋 Dados do Cliente</div>
        <div class="client-info">
            <div class="info-item">
                <span class="info-label">Nome Completo</span>
                <span class="info-value">${orc.cliente_nome || 'Não informado'}</span>
            </div>
            <div class="info-item">
                <span class="info-label">CPF</span>
                <span class="info-value">${orc.cliente_cpf || 'Não informado'}</span>
            </div>
            <div class="info-item">
                <span class="info-label">E-mail</span>
                <span class="info-value">${orc.cliente_email || 'Não informado'}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Telefone</span>
                <span class="info-value">${orc.cliente_telefone || 'Não informado'}</span>
            </div>
            ${orc.profissional_nome ? `
                <div class="info-item">
                    <span class="info-label">Profissional Responsável</span>
                    <span class="info-value">${orc.profissional_nome}</span>
                </div>
            ` : ''}
            <div class="info-item">
                <span class="info-label">Forma de Pagamento</span>
                <span class="info-value">${orc.forma_pagamento || 'A definir'}</span>
            </div>
        </div>

        <!-- Serviços Contratados -->
        ${(orc.servicos && orc.servicos.length > 0) ? `
            <div class="section-title">💼 Serviços Contratados</div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th style="width: 50%;">Descrição do Serviço</th>
                            <th style="width: 15%; text-align: center;">Quantidade</th>
                            <th style="width: 17.5%;">Valor Unit.</th>
                            <th style="width: 17.5%;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${orc.servicos.map(s => {
                            const qtd = s.quantidade || 1;
                            const preco = s.preco || 0;
                            const total = qtd * preco;
                            return `
                                <tr>
                                    <td>
                                        <div class="item-name">${s.nome || 'Serviço'}</div>
                                        ${s.descricao ? `<div class="item-desc">${s.descricao}</div>` : ''}
                                    </td>
                                    <td style="text-align: center;">${qtd}</td>
                                    <td>R$ ${preco.toFixed(2)}</td>
                                    <td><strong>R$ ${total.toFixed(2)}</strong></td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        ` : ''}

        <!-- Produtos Inclusos -->
        ${(orc.produtos && orc.produtos.length > 0) ? `
            <div class="section-title">📦 Produtos Inclusos</div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th style="width: 50%;">Descrição do Produto</th>
                            <th style="width: 15%; text-align: center;">Quantidade</th>
                            <th style="width: 17.5%;">Valor Unit.</th>
                            <th style="width: 17.5%;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${orc.produtos.map(p => {
                            const qtd = p.quantidade || 1;
                            const preco = p.preco || 0;
                            const total = qtd * preco;
                            return `
                                <tr>
                                    <td>
                                        <div class="item-name">${p.nome || 'Produto'}</div>
                                        ${p.descricao ? `<div class="item-desc">${p.descricao}</div>` : ''}
                                    </td>
                                    <td style="text-align: center;">${qtd}</td>
                                    <td>R$ ${preco.toFixed(2)}</td>
                                    <td><strong>R$ ${total.toFixed(2)}</strong></td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        ` : ''}

        <!-- Totais -->
        <div class="totals-section">
            <div class="total-row subtotal">
                <span class="total-label">Subtotal</span>
                <span class="total-value">R$ ${subtotal.toFixed(2)}</span>
            </div>
            ${desconto > 0 ? `
                <div class="total-row discount">
                    <span class="total-label">Desconto Aplicado</span>
                    <span class="total-value">- R$ ${desconto.toFixed(2)}</span>
                </div>
            ` : ''}
            ${cashback > 0 ? `
                <div class="total-row cashback">
                    <span class="total-label">Cashback (a receber)</span>
                    <span class="total-value">R$ ${cashback.toFixed(2)}</span>
                </div>
            ` : ''}
            <div class="total-row final">
                <span class="total-label">VALOR TOTAL</span>
                <span class="total-value">R$ ${total.toFixed(2)}</span>
            </div>
        </div>

        <!-- Termos e Condições -->
        <div class="terms-box">
            <div class="terms-title">📜 Termos e Condições</div>
            <div class="terms-content">
                ${orc.observacoes || `
                    Este contrato é válido conforme os termos gerais de prestação de serviços da BIOMA.
                    O cliente está ciente dos procedimentos a serem realizados e concorda com os valores apresentados.
                    Os serviços serão executados conforme agendamento prévio e disponibilidade.
                    Pagamentos devem ser realizados conforme a forma acordada.
                `}
            </div>
        </div>

        <!-- Assinaturas -->
        <div class="signatures">
            <div class="signature-box">
                <div class="signature-line"></div>
                <div class="signature-label">${orc.cliente_nome || 'Cliente'}</div>
                <div class="signature-sublabel">CPF: ${orc.cliente_cpf || '__________________'}</div>
            </div>
            <div class="signature-box">
                <div class="signature-line"></div>
                <div class="signature-label">BIOMA Estética & Bem-Estar</div>
                <div class="signature-sublabel">Representante Legal</div>
            </div>
        </div>

        <!-- Rodapé -->
        <div class="footer">
            <div class="footer-row">
                <strong>BIOMA Estética & Bem-Estar</strong> | CNPJ: 00.000.000/0001-00
            </div>
            <div class="footer-row">
                Endereço: Rua Exemplo, 123 - Bairro - Cidade/UF - CEP 00000-000
            </div>
            <div class="footer-row">
                contato@bioma.com.br | (11) 0000-0000 | www.bioma.com.br
            </div>
            <div class="footer-row" style="margin-top: 10px; font-size: 7pt;">
                Documento gerado em ${new Date().toLocaleString('pt-BR')} | Contrato #${orc.numero || orcamentoId}
            </div>
        </div>
    </div>
</body>
</html>
    `);

    printWindow.document.close();
}

// ==================== MELHORAR DETALHAMENTO EM CONSULTAR (Diretriz 2.2) ====================

// Estado dos filtros de consultar
let filtrosConsultar = {
    status: 'todos',
    dataInicio: '',
    dataFim: '',
    busca: ''
};

/**
 * Carregar Consultar com melhorias (substitui loadConsultar original)
 */
window.loadConsultarMelhorado = async function() {
    try {
        Swal.fire({
            title: 'Carregando orçamentos...',
            allowOutsideClick: false,
            didOpen: () => Swal.showLoading()
        });

        const response = await fetch('/api/orcamentos', {
            credentials: 'include'
        });

        const data = await response.json();

        if (!data.success) {
            Swal.fire('Erro', 'Não foi possível carregar orçamentos', 'error');
            return;
        }

        const orcamentos = data.orcamentos || [];

        // Aplicar filtros
        const orcamentosFiltrados = aplicarFiltrosConsultar(orcamentos);

        // Calcular estatísticas
        const stats = calcularEstatisticasConsultar(orcamentos, orcamentosFiltrados);

        // Renderizar estatísticas
        renderizarEstatisticasConsultar(stats);

        // Renderizar tabela
        renderizarTabelaConsultar(orcamentosFiltrados);

        Swal.close();

    } catch (error) {
        console.error('Erro ao carregar Consultar:', error);
        Swal.fire('Erro', 'Não foi possível carregar orçamentos', 'error');
    }
};

/**
 * Aplicar filtros aos orçamentos
 */
function aplicarFiltrosConsultar(orcamentos) {
    return orcamentos.filter(orc => {
        // Filtro de status
        if (filtrosConsultar.status !== 'todos') {
            const statusMatch = filtrosConsultar.status.toLowerCase() === orc.status?.toLowerCase();
            if (!statusMatch) return false;
        }

        // Filtro de data início
        if (filtrosConsultar.dataInicio) {
            const orcData = new Date(orc.created_at);
            const filtroData = new Date(filtrosConsultar.dataInicio);
            if (orcData < filtroData) return false;
        }

        // Filtro de data fim
        if (filtrosConsultar.dataFim) {
            const orcData = new Date(orc.created_at);
            const filtroData = new Date(filtrosConsultar.dataFim);
            filtroData.setHours(23, 59, 59); // Incluir o dia inteiro
            if (orcData > filtroData) return false;
        }

        // Filtro de busca (cliente ou número)
        if (filtrosConsultar.busca) {
            const busca = filtrosConsultar.busca.toLowerCase();
            const clienteMatch = orc.cliente_nome?.toLowerCase().includes(busca);
            const numeroMatch = orc.numero?.toString().includes(busca);
            if (!clienteMatch && !numeroMatch) return false;
        }

        return true;
    });
}

/**
 * Calcular estatísticas dos orçamentos
 */
function calcularEstatisticasConsultar(todos, filtrados) {
    const stats = {
        // Todos os orçamentos
        totalGeral: todos.length,
        valorTotalGeral: todos.reduce((acc, o) => acc + (o.total_final || 0), 0),

        // Filtrados
        totalFiltrados: filtrados.length,
        valorTotalFiltrados: filtrados.reduce((acc, o) => acc + (o.total_final || 0), 0),

        // Por status (filtrados)
        pendentes: filtrados.filter(o => o.status?.toLowerCase() === 'pendente').length,
        aprovados: filtrados.filter(o => o.status?.toLowerCase() === 'aprovado').length,
        cancelados: filtrados.filter(o => o.status?.toLowerCase() === 'cancelado').length,

        // Valores por status
        valorPendentes: filtrados.filter(o => o.status?.toLowerCase() === 'pendente')
            .reduce((acc, o) => acc + (o.total_final || 0), 0),
        valorAprovados: filtrados.filter(o => o.status?.toLowerCase() === 'aprovado')
            .reduce((acc, o) => acc + (o.total_final || 0), 0)
    };

    // Ticket médio
    stats.ticketMedio = stats.totalFiltrados > 0 ? stats.valorTotalFiltrados / stats.totalFiltrados : 0;

    // Taxa de conversão
    stats.taxaConversao = stats.totalFiltrados > 0 ? (stats.aprovados / stats.totalFiltrados * 100) : 0;

    return stats;
}

/**
 * Renderizar cards de estatísticas
 */
function renderizarEstatisticasConsultar(stats) {
    // Buscar ou criar container de estatísticas
    let statsContainer = document.getElementById('consultar-stats');

    if (!statsContainer) {
        // Criar container antes da tabela
        const tbody = document.getElementById('consultaBody');
        const table = tbody?.closest('table');

        if (table && table.parentNode) {
            statsContainer = document.createElement('div');
            statsContainer.id = 'consultar-stats';
            statsContainer.className = 'mb-4';
            table.parentNode.insertBefore(statsContainer, table);
        }
    }

    if (!statsContainer) return;

    // HTML dos cards
    statsContainer.innerHTML = `
        <div class="row g-3 mb-4">
            <div class="col-md-3">
                <div class="card border-0" style="background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%); color: white;">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h6 class="card-subtitle mb-2" style="opacity: 0.9;">Total de Orçamentos</h6>
                                <h2 class="card-title mb-0">${stats.totalFiltrados}</h2>
                                ${stats.totalFiltrados !== stats.totalGeral ?
                                    `<small style="opacity: 0.8;">de ${stats.totalGeral} no total</small>` :
                                    ''}
                            </div>
                            <i class="bi bi-file-earmark-text" style="font-size: 2rem; opacity: 0.5;"></i>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card border-0" style="background: linear-gradient(135deg, #F093FB 0%, #F5576C 100%); color: white;">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h6 class="card-subtitle mb-2" style="opacity: 0.9;">Valor Total</h6>
                                <h2 class="card-title mb-0">${formatarMoeda(stats.valorTotalFiltrados)}</h2>
                                <small style="opacity: 0.8;">Ticket: ${formatarMoeda(stats.ticketMedio)}</small>
                            </div>
                            <i class="bi bi-cash-stack" style="font-size: 2rem; opacity: 0.5;"></i>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card border-0" style="background: linear-gradient(135deg, #4FACFE 0%, #00F2FE 100%); color: white;">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h6 class="card-subtitle mb-2" style="opacity: 0.9;">Aprovados</h6>
                                <h2 class="card-title mb-0">${stats.aprovados}</h2>
                                <small style="opacity: 0.8;">${formatarMoeda(stats.valorAprovados)}</small>
                            </div>
                            <i class="bi bi-check-circle" style="font-size: 2rem; opacity: 0.5;"></i>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card border-0" style="background: linear-gradient(135deg, #FA709A 0%, #FEE140 100%); color: white;">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h6 class="card-subtitle mb-2" style="opacity: 0.9;">Taxa de Conversão</h6>
                                <h2 class="card-title mb-0">${stats.taxaConversao.toFixed(1)}%</h2>
                                <small style="opacity: 0.8;">${stats.pendentes} pendentes</small>
                            </div>
                            <i class="bi bi-graph-up-arrow" style="font-size: 2rem; opacity: 0.5;"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Renderizar tabela melhorada
 */
function renderizarTabelaConsultar(orcamentos) {
    const tbody = document.getElementById('consultaBody');

    if (!tbody) return;

    if (orcamentos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center" style="padding: 60px;">
                    <i class="bi bi-inbox" style="font-size: 4rem; opacity: 0.2;"></i>
                    <p class="text-muted mt-3">Nenhum orçamento encontrado com os filtros aplicados</p>
                </td>
            </tr>
        `;
        return;
    }

    // Ordenar por data (mais recente primeiro)
    orcamentos.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

    const html = orcamentos.map(orc => {
        const data = new Date(orc.created_at).toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });

        // Badge de status
        let badgeClass = 'bg-secondary';
        let badgeIcon = 'bi-question-circle';

        if (orc.status?.toLowerCase() === 'aprovado') {
            badgeClass = 'bg-success';
            badgeIcon = 'bi-check-circle-fill';
        } else if (orc.status?.toLowerCase() === 'pendente') {
            badgeClass = 'bg-warning';
            badgeIcon = 'bi-clock-fill';
        } else if (orc.status?.toLowerCase() === 'cancelado') {
            badgeClass = 'bg-danger';
            badgeIcon = 'bi-x-circle-fill';
        }

        // Informações extras
        const numServicos = orc.servicos?.length || 0;
        const numProdutos = orc.produtos?.length || 0;

        return `
            <tr style="cursor: pointer; transition: all 0.2s;"
                onmouseover="this.style.backgroundColor='#F8F9FA'"
                onmouseout="this.style.backgroundColor=''">
                <td>
                    <strong style="font-size: 1.1rem; color: #7C3AED;">#${orc.numero || orc._id.substring(0, 6)}</strong>
                </td>
                <td>
                    <div>${data}</div>
                    <small class="text-muted">${new Date(orc.created_at).toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'})}</small>
                </td>
                <td>
                    <div><strong>${orc.cliente_nome || 'N/A'}</strong></div>
                    <small class="text-muted">${orc.cliente_telefone || ''}</small>
                </td>
                <td>
                    <div><strong style="font-size: 1.1rem; color: #28A745;">R$ ${(orc.total_final || 0).toFixed(2)}</strong></div>
                    <small class="text-muted">${numServicos} serv. | ${numProdutos} prod.</small>
                </td>
                <td>
                    <span class="badge ${badgeClass}">
                        <i class="bi ${badgeIcon}"></i> ${orc.status || 'Pendente'}
                    </span>
                </td>
                <td>
                    ${orc.profissional_nome ?
                        `<small class="text-muted"><i class="bi bi-person"></i> ${orc.profissional_nome}</small>` :
                        '<small class="text-muted">-</small>'}
                </td>
                <td>
                    <div class="btn-group" role="group">
                        <button class="btn btn-sm btn-info"
                                onclick="visualizarOrcamento('${orc._id}')"
                                title="Visualizar">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-primary"
                                onclick="editarOrcamento('${orc._id}')"
                                title="Editar">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-danger"
                                onclick="deleteOrcamento('${orc._id}')"
                                title="Deletar">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');

    tbody.innerHTML = html;
}

/**
 * Abrir modal de filtros avançados
 */
window.abrirFiltrosConsultar = async function() {
    const { value: formValues } = await Swal.fire({
        title: '<strong><i class="bi bi-funnel"></i> Filtros Avançados</strong>',
        html: `
            <div class="text-start">
                <div class="mb-3">
                    <label class="form-label">Status</label>
                    <select id="filtro-status" class="form-select">
                        <option value="todos" ${filtrosConsultar.status === 'todos' ? 'selected' : ''}>Todos</option>
                        <option value="pendente" ${filtrosConsultar.status === 'pendente' ? 'selected' : ''}>Pendente</option>
                        <option value="aprovado" ${filtrosConsultar.status === 'aprovado' ? 'selected' : ''}>Aprovado</option>
                        <option value="cancelado" ${filtrosConsultar.status === 'cancelado' ? 'selected' : ''}>Cancelado</option>
                    </select>
                </div>
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Data Início</label>
                        <input type="date" id="filtro-data-inicio" class="form-control"
                               value="${filtrosConsultar.dataInicio}">
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Data Fim</label>
                        <input type="date" id="filtro-data-fim" class="form-control"
                               value="${filtrosConsultar.dataFim}">
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label">Buscar Cliente ou Número</label>
                    <input type="text" id="filtro-busca" class="form-control"
                           placeholder="Digite nome do cliente ou número..."
                           value="${filtrosConsultar.busca}">
                </div>
            </div>
        `,
        width: '600px',
        showCancelButton: true,
        confirmButtonText: 'Aplicar Filtros',
        cancelButtonText: 'Limpar Filtros',
        showDenyButton: true,
        denyButtonText: 'Cancelar',
        preConfirm: () => {
            return {
                status: document.getElementById('filtro-status').value,
                dataInicio: document.getElementById('filtro-data-inicio').value,
                dataFim: document.getElementById('filtro-data-fim').value,
                busca: document.getElementById('filtro-busca').value
            };
        }
    });

    if (formValues) {
        // Aplicar filtros
        filtrosConsultar = formValues;
        loadConsultarMelhorado();
    } else if (formValues === null) {
        // Limpar filtros
        filtrosConsultar = {
            status: 'todos',
            dataInicio: '',
            dataFim: '',
            busca: ''
        };
        loadConsultarMelhorado();
    }
};

/**
 * Busca rápida (ao digitar)
 */
window.buscaRapidaConsultar = function(termo) {
    filtrosConsultar.busca = termo;
    // Debounce: aguardar 500ms após última digitação
    clearTimeout(window.buscaRapidaTimeout);
    window.buscaRapidaTimeout = setTimeout(() => {
        loadConsultarMelhorado();
    }, 500);
};

// ==================== MELHORAR GRÁFICOS DA ABA RESUMO (Diretriz 4.1) ====================

// Instâncias dos gráficos melhorados
let chartServicosMelhorado = null;
let chartFaturamentoMelhorado = null;
let chartConversao = null;
let chartStatusDistribuicao = null;

/**
 * Carregar Relatórios com gráficos melhorados
 */
window.loadRelatoriosMelhorado = async function() {
    try {
        // Buscar dados
        const response = await fetch('/api/orcamentos', {
            credentials: 'include'
        });

        const data = await response.json();

        if (!data.success || !data.orcamentos) {
            console.error('Erro ao carregar orçamentos');
            return;
        }

        const todosOrcamentos = data.orcamentos || [];
        const orcamentosAprovados = todosOrcamentos.filter(o => o.status?.toLowerCase() === 'aprovado');

        // Atualizar cards de estatísticas (mantém originais)
        atualizarCardsRelatorios(todosOrcamentos, orcamentosAprovados);

        // Gerar gráficos melhorados
        gerarGraficoServicosMelhorado(orcamentosAprovados);
        gerarGraficoFaturamentoMelhorado(orcamentosAprovados);
        gerarGraficoConversao(todosOrcamentos);
        gerarGraficoStatusDistribuicao(todosOrcamentos);

        // Carregar top clientes e produtos (mantém original)
        await carregarTopClientes();
        carregarTopProdutos(orcamentosAprovados);

    } catch (error) {
        console.error('Erro ao carregar relatórios melhorados:', error);
    }
};

/**
 * Atualizar cards de estatísticas
 */
function atualizarCardsRelatorios(todos, aprovados) {
    const faturamentoTotal = aprovados.reduce((acc, o) => acc + (o.total_final || 0), 0);
    const faturamentoMes = calcularFaturamentoMesAtual(aprovados);
    const cashbackTotal = aprovados.reduce((acc, o) => acc + (o.cashback_valor || 0), 0);
    const ticketMedio = aprovados.length > 0 ? faturamentoTotal / aprovados.length : 0;

    // Atualizar elementos (se existirem)
    const elFatTotal = document.getElementById('relFaturamentoTotal');
    const elFatMes = document.getElementById('relFaturamentoMes');
    const elCashback = document.getElementById('relCashbackTotal');
    const elTicket = document.getElementById('relTicketMedio');

    if (elFatTotal) elFatTotal.textContent = `R$ ${faturamentoTotal.toFixed(0)}`;
    if (elFatMes) elFatMes.textContent = `R$ ${faturamentoMes.toFixed(0)}`;
    if (elCashback) elCashback.textContent = `R$ ${cashbackTotal.toFixed(0)}`;
    if (elTicket) elTicket.textContent = `R$ ${ticketMedio.toFixed(0)}`;
}

function calcularFaturamentoMesAtual(orcamentos) {
    const hoje = new Date();
    const mesAtual = hoje.getMonth();
    const anoAtual = hoje.getFullYear();

    return orcamentos
        .filter(o => {
            const d = new Date(o.created_at);
            return d.getMonth() === mesAtual && d.getFullYear() === anoAtual;
        })
        .reduce((acc, o) => acc + (o.total_final || 0), 0);
}

/**
 * Gráfico de Serviços Melhorado (Bar Chart com gradientes)
 */
function gerarGraficoServicosMelhorado(orcamentos) {
    const canvas = document.getElementById('chartServicos');
    if (!canvas) return;

    // Destruir gráfico anterior
    if (chartServicosMelhorado) {
        chartServicosMelhorado.destroy();
    }

    // Calcular top 8 serviços (aumentado de 5)
    const servicosCount = {};
    orcamentos.forEach(orc => {
        (orc.servicos || []).forEach(s => {
            const nome = s.nome || 'Sem nome';
            if (!servicosCount[nome]) {
                servicosCount[nome] = { total: 0, quantidade: 0 };
            }
            servicosCount[nome].total += s.total || s.preco || 0;
            servicosCount[nome].quantidade += s.quantidade || 1;
        });
    });

    const topServicos = Object.entries(servicosCount)
        .sort((a, b) => b[1].total - a[1].total)
        .slice(0, 8);

    if (topServicos.length === 0) return;

    // Cores em gradiente
    const colors = [
        'rgba(124, 58, 237, 0.8)',   // Roxo
        'rgba(59, 130, 246, 0.8)',   // Azul
        'rgba(16, 185, 129, 0.8)',   // Verde
        'rgba(251, 191, 36, 0.8)',   // Amarelo
        'rgba(239, 68, 68, 0.8)',    // Vermelho
        'rgba(236, 72, 153, 0.8)',   // Rosa
        'rgba(139, 92, 246, 0.8)',   // Roxo claro
        'rgba(14, 165, 233, 0.8)'    // Azul claro
    ];

    const borderColors = colors.map(c => c.replace('0.8', '1'));

    chartServicosMelhorado = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: topServicos.map(s => s[0]),
            datasets: [{
                label: 'Faturamento (R$)',
                data: topServicos.map(s => s[1].total),
                backgroundColor: colors,
                borderColor: borderColors,
                borderWidth: 2,
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#666',
                        font: {
                            size: 12,
                            weight: '600'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 13
                    },
                    callbacks: {
                        label: function(context) {
                            const servico = topServicos[context.dataIndex];
                            return [
                                `Faturamento: R$ ${servico[1].total.toFixed(2)}`,
                                `Quantidade: ${servico[1].quantidade} un.`,
                                `Média: R$ ${(servico[1].total / servico[1].quantidade).toFixed(2)}`
                            ];
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Top 8 Serviços Mais Rentáveis',
                    color: '#333',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'R$ ' + value.toLocaleString('pt-BR');
                        },
                        color: '#666'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    ticks: {
                        color: '#666',
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: {
                        display: false
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        }
    });
}

/**
 * Gráfico de Faturamento Mensal Melhorado (Line Chart com gradiente)
 */
function gerarGraficoFaturamentoMelhorado(orcamentos) {
    const canvas = document.getElementById('chartFaturamento');
    if (!canvas) return;

    // Destruir gráfico anterior
    if (chartFaturamentoMelhorado) {
        chartFaturamentoMelhorado.destroy();
    }

    // Últimos 12 meses (aumentado de 6)
    const meses = [];
    const faturamento = [];
    const quantidades = [];

    for (let i = 11; i >= 0; i--) {
        const d = new Date();
        d.setMonth(d.getMonth() - i);
        const mes = d.getMonth();
        const ano = d.getFullYear();

        meses.push(d.toLocaleDateString('pt-BR', { month: 'short', year: '2-digit' }));

        const orcamentosMes = orcamentos.filter(o => {
            const od = new Date(o.created_at);
            return od.getMonth() === mes && od.getFullYear() === ano;
        });

        faturamento.push(orcamentosMes.reduce((acc, o) => acc + (o.total_final || 0), 0));
        quantidades.push(orcamentosMes.length);
    }

    chartFaturamentoMelhorado = new Chart(canvas, {
        type: 'line',
        data: {
            labels: meses,
            datasets: [
                {
                    label: 'Faturamento (R$)',
                    data: faturamento,
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderColor: 'rgba(16, 185, 129, 1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    pointBackgroundColor: 'rgba(16, 185, 129, 1)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    yAxisID: 'y'
                },
                {
                    label: 'Quantidade de Vendas',
                    data: quantidades,
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: 'rgba(59, 130, 246, 1)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 15,
                        color: '#666',
                        font: {
                            size: 12,
                            weight: '600'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                if (context.datasetIndex === 0) {
                                    label += 'R$ ' + context.parsed.y.toFixed(2);
                                } else {
                                    label += context.parsed.y + ' vendas';
                                }
                            }
                            return label;
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Evolução de Faturamento e Vendas (Últimos 12 Meses)',
                    color: '#333',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'R$ ' + value.toLocaleString('pt-BR');
                        },
                        color: 'rgba(16, 185, 129, 1)'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + ' un.';
                        },
                        color: 'rgba(59, 130, 246, 1)'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                },
                x: {
                    ticks: {
                        color: '#666'
                    },
                    grid: {
                        display: false
                    }
                }
            },
            animation: {
                duration: 1200,
                easing: 'easeInOutQuart'
            }
        }
    });
}

/**
 * Gráfico de Conversão (Funil de Vendas)
 */
function gerarGraficoConversao(orcamentos) {
    const canvas = document.getElementById('chartConversao');
    if (!canvas) {
        // Criar canvas se não existir
        criarCanvasConversao();
        return gerarGraficoConversao(orcamentos);
    }

    // Destruir gráfico anterior
    if (chartConversao) {
        chartConversao.destroy();
    }

    // Calcular conversão
    const total = orcamentos.length;
    const pendentes = orcamentos.filter(o => o.status?.toLowerCase() === 'pendente').length;
    const aprovados = orcamentos.filter(o => o.status?.toLowerCase() === 'aprovado').length;
    const cancelados = orcamentos.filter(o => o.status?.toLowerCase() === 'cancelado').length;

    const taxaAprovacao = total > 0 ? (aprovados / total * 100) : 0;
    const taxaCancelamento = total > 0 ? (cancelados / total * 100) : 0;

    chartConversao = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: ['Aprovados', 'Pendentes', 'Cancelados'],
            datasets: [{
                data: [aprovados, pendentes, cancelados],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.8)',   // Verde
                    'rgba(251, 191, 36, 0.8)',   // Amarelo
                    'rgba(239, 68, 68, 0.8)'     // Vermelho
                ],
                borderColor: [
                    'rgba(16, 185, 129, 1)',
                    'rgba(251, 191, 36, 1)',
                    'rgba(239, 68, 68, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        color: '#666',
                        font: {
                            size: 12,
                            weight: '600'
                        },
                        generateLabels: function(chart) {
                            const data = chart.data;
                            return data.labels.map((label, i) => {
                                const value = data.datasets[0].data[i];
                                const percent = total > 0 ? (value / total * 100).toFixed(1) : 0;
                                return {
                                    text: `${label}: ${value} (${percent}%)`,
                                    fillStyle: data.datasets[0].backgroundColor[i],
                                    hidden: false,
                                    index: i
                                };
                            });
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            const percent = total > 0 ? (value / total * 100).toFixed(1) : 0;
                            return `${context.label}: ${value} (${percent}%)`;
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Taxa de Conversão de Orçamentos',
                    color: '#333',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 1000
            }
        }
    });
}

/**
 * Gráfico de Distribuição de Status
 */
function gerarGraficoStatusDistribuicao(orcamentos) {
    const canvas = document.getElementById('chartStatusDistribuicao');
    if (!canvas) {
        criarCanvasStatus();
        return gerarGraficoStatusDistribuicao(orcamentos);
    }

    // Destruir gráfico anterior
    if (chartStatusDistribuicao) {
        chartStatusDistribuicao.destroy();
    }

    // Calcular valores por status
    const aprovados = orcamentos.filter(o => o.status?.toLowerCase() === 'aprovado');
    const pendentes = orcamentos.filter(o => o.status?.toLowerCase() === 'pendente');
    const cancelados = orcamentos.filter(o => o.status?.toLowerCase() === 'cancelado');

    const valorAprovados = aprovados.reduce((acc, o) => acc + (o.total_final || 0), 0);
    const valorPendentes = pendentes.reduce((acc, o) => acc + (o.total_final || 0), 0);
    const valorCancelados = cancelados.reduce((acc, o) => acc + (o.total_final || 0), 0);

    chartStatusDistribuicao = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: ['Aprovados', 'Pendentes', 'Cancelados'],
            datasets: [{
                label: 'Valor Total (R$)',
                data: [valorAprovados, valorPendentes, valorCancelados],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(251, 191, 36, 0.8)',
                    'rgba(239, 68, 68, 0.8)'
                ],
                borderColor: [
                    'rgba(16, 185, 129, 1)',
                    'rgba(251, 191, 36, 1)',
                    'rgba(239, 68, 68, 1)'
                ],
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: 'y',  // Horizontal bars
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const quantidade = context.label === 'Aprovados' ? aprovados.length :
                                              context.label === 'Pendentes' ? pendentes.length :
                                              cancelados.length;
                            return [
                                `Valor: R$ ${context.parsed.x.toFixed(2)}`,
                                `Quantidade: ${quantidade}`,
                                `Média: R$ ${quantidade > 0 ? (context.parsed.x / quantidade).toFixed(2) : 0}`
                            ];
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Valor Total por Status',
                    color: '#333',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'R$ ' + value.toLocaleString('pt-BR');
                        },
                        color: '#666'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                y: {
                    ticks: {
                        color: '#666',
                        font: {
                            size: 13,
                            weight: '600'
                        }
                    },
                    grid: {
                        display: false
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        }
    });
}

/**
 * Criar canvas para gráfico de conversão (se não existir)
 */
function criarCanvasConversao() {
    const ctxFaturamento = document.getElementById('chartFaturamento');
    if (!ctxFaturamento || !ctxFaturamento.parentNode) return;

    const container = document.createElement('div');
    container.className = 'col-md-6 mb-4';
    container.innerHTML = `
        <div class="card" style="height: 350px;">
            <div class="card-body">
                <canvas id="chartConversao"></canvas>
            </div>
        </div>
    `;

    // Inserir após o gráfico de faturamento
    const parentRow = ctxFaturamento.closest('.row');
    if (parentRow) {
        parentRow.appendChild(container);
    }
}

/**
 * Criar canvas para gráfico de status (se não existir)
 */
function criarCanvasStatus() {
    const ctxServicos = document.getElementById('chartServicos');
    if (!ctxServicos || !ctxServicos.parentNode) return;

    const container = document.createElement('div');
    container.className = 'col-md-6 mb-4';
    container.innerHTML = `
        <div class="card" style="height: 350px;">
            <div class="card-body">
                <canvas id="chartStatusDistribuicao"></canvas>
            </div>
        </div>
    `;

    // Inserir após o gráfico de serviços
    const parentRow = ctxServicos.closest('.row');
    if (parentRow) {
        parentRow.appendChild(container);
    }
}

/**
 * Carregar top clientes
 */
async function carregarTopClientes() {
    try {
        const response = await fetch('/api/clientes', {
            credentials: 'include'
        });

        const data = await response.json();

        if (data.success && data.clientes) {
            const topClientes = data.clientes
                .sort((a, b) => (b.total_gasto || 0) - (a.total_gasto || 0))
                .slice(0, 10);

            const tbody = document.getElementById('topClientesBody');
            if (!tbody) return;

            const html = topClientes.map((c, idx) => {
                const medalha = idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : '';
                return `
                    <tr>
                        <td><strong style="font-size:1.3rem;">${medalha} ${idx + 1}º</strong></td>
                        <td><strong>${c.nome}</strong></td>
                        <td><strong style="color:#10B981">R$ ${(c.total_gasto || 0).toFixed(2)}</strong></td>
                        <td>${c.total_visitas || 0}</td>
                        <td>${c.ultima_visita ? new Date(c.ultima_visita).toLocaleDateString('pt-BR') : '-'}</td>
                    </tr>
                `;
            }).join('');

            tbody.innerHTML = html || '<tr><td colspan="5" class="text-center text-muted">Nenhum</td></tr>';
        }
    } catch (error) {
        console.error('Erro ao carregar top clientes:', error);
    }
}

/**
 * Carregar top produtos
 */
function carregarTopProdutos(orcamentos) {
    const produtosCount = {};

    orcamentos.forEach(orc => {
        (orc.produtos || []).forEach(p => {
            const nome = p.nome || 'Sem nome';
            if (!produtosCount[nome]) {
                produtosCount[nome] = { total: 0, quantidade: 0 };
            }
            produtosCount[nome].total += p.total || p.preco || 0;
            produtosCount[nome].quantidade += p.quantidade || 1;
        });
    });

    const topProdutos = Object.entries(produtosCount)
        .sort((a, b) => b[1].quantidade - a[1].quantidade)
        .slice(0, 10);

    const tbody = document.getElementById('topProdutosBody');
    if (!tbody) return;

    if (topProdutos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Nenhum</td></tr>';
        return;
    }

    const html = topProdutos.map(p => `
        <tr>
            <td><strong>${p[0]}</strong></td>
            <td>${p[1].quantidade}</td>
            <td><strong>R$ ${p[1].total.toFixed(2)}</strong></td>
        </tr>
    `).join('');

    tbody.innerHTML = html;
}

// Carregar perfil automaticamente ao carregar a página
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', carregarPerfilUsuario);
} else {
    carregarPerfilUsuario();
}

console.log('✅ Melhorias nos Profissionais carregadas (12.2, 12.3)');
console.log('✅ Histórico de Atendimentos carregado (12.4)');
console.log('✅ Sistema de Níveis de Acesso carregado (5.1)');
console.log('✅ Layout Melhorado do Contrato carregado (1.3)');
console.log('✅ Detalhamento em Consultar melhorado (2.2)');
console.log('✅ Gráficos da aba Resumo melhorados (4.1)');
console.log('✅ Melhorias v3.7 carregadas com sucesso!');
