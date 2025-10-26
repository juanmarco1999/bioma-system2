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
console.log('✅ Melhorias v3.7 carregadas com sucesso!');
