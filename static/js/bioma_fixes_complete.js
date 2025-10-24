/**
 * BIOMA SYSTEM - Complete Fixes & Enhancements
 * Arquivo completo de correções e melhorias
 * Versão: 2.0
 */

console.log('🚀 BIOMA Fixes Complete carregado!');

// ==================== CORREÇÕES CRÍTICAS DE RENDERIZAÇÃO ====================

/**
 * Renderiza resumo financeiro
 */
function renderFinanceiroResumo(data) {
    console.log('💰 Renderizando resumo financeiro...');

    try {
        // Atualizar cards de resumo
        if (document.getElementById('financeiroReceitas')) {
            document.getElementById('financeiroReceitas').textContent = `R$ ${(data.receitas || 0).toFixed(2)}`;
        }
        if (document.getElementById('financeiroDespesas')) {
            document.getElementById('financeiroDespesas').textContent = `R$ ${(data.despesas || 0).toFixed(2)}`;
        }
        if (document.getElementById('financeiroComissoes')) {
            document.getElementById('financeiroComissoes').textContent = `R$ ${(data.comissoes_pendentes || 0).toFixed(2)}`;
        }
        if (document.getElementById('financeiroLucro')) {
            document.getElementById('financeiroLucro').textContent = `R$ ${(data.lucro_liquido || 0).toFixed(2)}`;
        }

        // Atualizar margem de lucro
        const margemElement = document.getElementById('margemLucro');
        if (margemElement && data.receitas > 0) {
            const margem = ((data.lucro_liquido / data.receitas) * 100).toFixed(1);
            margemElement.textContent = `${margem}%`;
        }

        // Carregar gráficos se Chart.js estiver disponível
        if (typeof carregarTodosGraficos === 'function') {
            setTimeout(() => carregarTodosGraficos(), 500);
        }
    } catch (error) {
        console.error('❌ Erro ao renderizar resumo financeiro:', error);
    }
}

/**
 * Renderiza resumo geral dos relatórios
 */
function renderResumoGeral(data) {
    console.log('📊 Renderizando resumo geral...');

    try {
        // Atualizar cards de estatísticas
        const elements = {
            'totalClientes': data.total_clientes || 0,
            'totalProfissionais': data.total_profissionais || 0,
            'totalServicos': data.total_servicos || 0,
            'totalProdutos': data.total_produtos || 0,
            'faturamentoTotal': `R$ ${(data.faturamento_total || 0).toFixed(2)}`,
            'cashbackGerado': `R$ ${(data.cashback_gerado || 0).toFixed(2)}`,
            'ticketMedio': `R$ ${(data.ticket_medio || 0).toFixed(2)}`
        };

        for (const [id, value] of Object.entries(elements)) {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        }

        // Renderizar top 5 serviços se existir
        if (data.top_servicos) {
            renderTopServicos(data.top_servicos);
        }
    } catch (error) {
        console.error('❌ Erro ao renderizar resumo geral:', error);
    }
}

/**
 * Renderiza tabela de agendamentos
 */
function renderAgendamentosTabela(agendamentos, pagination) {
    console.log('📅 Renderizando tabela de agendamentos...');

    const tbody = document.getElementById('agendamentosTableBody');
    if (!tbody) {
        console.warn('Elemento agendamentosTableBody não encontrado');
        return;
    }

    if (!agendamentos || agendamentos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted">
                    <i class="bi bi-calendar-x" style="font-size: 2rem;"></i>
                    <p>Nenhum agendamento encontrado</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = agendamentos.map(agendamento => {
        const dataFormatada = new Date(agendamento.data).toLocaleDateString('pt-BR');
        const statusClass = getStatusClass(agendamento.status);

        return `
            <tr>
                <td>${dataFormatada}</td>
                <td>${agendamento.hora || 'N/A'}</td>
                <td>${agendamento.cliente_nome || 'N/A'}</td>
                <td>${agendamento.servico_nome || 'N/A'}</td>
                <td>${agendamento.profissional_nome || 'N/A'}</td>
                <td><span class="badge ${statusClass}">${agendamento.status || 'Pendente'}</span></td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="visualizarAgendamento('${agendamento._id}')">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-success" onclick="confirmarAgendamento('${agendamento._id}')">
                        <i class="bi bi-check"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="cancelarAgendamento('${agendamento._id}')">
                        <i class="bi bi-x"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');

    // Renderizar paginação
    if (pagination) {
        renderPaginacao('agendamentos', pagination, loadAgendamentosOtimizado);
    }
}

/**
 * Renderiza tabela de serviços
 */
function renderServicosTabela(servicos, pagination) {
    console.log('✂️ Renderizando tabela de serviços...');

    const tbody = document.getElementById('servicosTableBody');
    if (!tbody) {
        console.warn('Elemento servicosTableBody não encontrado');
        return;
    }

    if (!servicos || servicos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted">
                    <i class="bi bi-scissors" style="font-size: 2rem;"></i>
                    <p>Nenhum serviço cadastrado</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = servicos.map(servico => `
        <tr>
            <td>${servico.nome || 'N/A'}</td>
            <td>${servico.categoria || 'N/A'}</td>
            <td>${servico.tamanho || 'N/A'}</td>
            <td><strong>R$ ${(servico.preco || 0).toFixed(2)}</strong></td>
            <td>
                <span class="badge ${servico.ativo ? 'success' : 'danger'}">
                    ${servico.ativo ? 'Ativo' : 'Inativo'}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="visualizarServico('${servico._id}')">
                    <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-sm btn-outline" onclick="editarServico('${servico._id}')">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-info" onclick="abrirModalFotoServico('${servico._id}')">
                    <i class="bi bi-camera"></i>
                </button>
            </td>
        </tr>
    `).join('');

    if (pagination) {
        renderPaginacao('servicos', pagination, loadServicosOtimizado);
    }
}

/**
 * Renderiza tabela de produtos
 */
function renderProdutosTabela(produtos, pagination) {
    console.log('📦 Renderizando tabela de produtos...');

    const tbody = document.getElementById('produtosTableBody');
    if (!tbody) {
        console.warn('Elemento produtosTableBody não encontrado');
        return;
    }

    if (!produtos || produtos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted">
                    <i class="bi bi-box" style="font-size: 2rem;"></i>
                    <p>Nenhum produto cadastrado</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = produtos.map(produto => `
        <tr>
            <td>${produto.nome || 'N/A'}</td>
            <td>${produto.marca || 'N/A'}</td>
            <td><strong>R$ ${(produto.preco || 0).toFixed(2)}</strong></td>
            <td>
                <span class="badge ${produto.estoque > 0 ? 'success' : 'danger'}">
                    ${produto.estoque || 0}
                </span>
            </td>
            <td>
                <span class="badge ${produto.ativo ? 'success' : 'danger'}">
                    ${produto.ativo ? 'Ativo' : 'Inativo'}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="visualizarProduto('${produto._id}')">
                    <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-sm btn-outline" onclick="editarProduto('${produto._id}')">
                    <i class="bi bi-pencil"></i>
                </button>
            </td>
        </tr>
    `).join('');

    if (pagination) {
        renderPaginacao('produtos', pagination, loadProdutosOtimizado);
    }
}

/**
 * Renderiza visão geral do estoque
 */
function renderEstoqueVisaoGeral(data) {
    console.log('📊 Renderizando visão geral do estoque...');

    try {
        // Atualizar estatísticas
        const stats = {
            'totalProdutosEstoque': data.total_produtos || 0,
            'valorTotalEstoque': `R$ ${(data.valor_total || 0).toFixed(2)}`,
            'produtosBaixoEstoque': data.produtos_baixo_estoque || 0,
            'produtosEmFalta': data.produtos_em_falta || 0
        };

        for (const [id, value] of Object.entries(stats)) {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        }

        // Renderizar lista de produtos com baixo estoque
        if (data.alertas && data.alertas.length > 0) {
            renderAlertasEstoque(data.alertas);
        }

        // Esconder spinner
        const spinner = document.querySelector('#section-estoque .spinner');
        if (spinner) {
            spinner.style.display = 'none';
        }
    } catch (error) {
        console.error('❌ Erro ao renderizar visão geral do estoque:', error);
    }
}

// ==================== CORREÇÃO DE NAVEGAÇÃO ====================

/**
 * Função principal de navegação corrigida
 */
window.goTo = function(section) {
    console.log(`🔄 Navegando para: ${section}`);

    try {
        // Esconder TODAS as seções
        document.querySelectorAll('.content-section').forEach(s => {
            s.classList.remove('active');
            s.style.display = 'none';
        });

        // Mostrar apenas a seção desejada
        const sectionElement = document.getElementById('section-' + section);
        if (sectionElement) {
            sectionElement.classList.add('active');
            sectionElement.style.display = 'block';

            // Remover elementos de estoque se não for a página de estoque
            if (section !== 'estoque') {
                removeEstoqueIndevido(sectionElement);
            }
        } else {
            console.error(`❌ Seção não encontrada: section-${section}`);
            return;
        }

        // Atualizar menu sidebar
        document.querySelectorAll('.sidebar-menu a').forEach(a => {
            a.classList.remove('active');
        });
        const menuItem = document.getElementById('menu-' + section);
        if (menuItem) {
            menuItem.classList.add('active');
        }

        // Scroll para o topo
        window.scrollTo({ top: 0, behavior: 'smooth' });

        // Carregar dados da seção (sem loop infinito)
        carregarDadosSecaoOtimizado(section);

    } catch (error) {
        console.error('❌ Erro ao navegar:', error);
    }
};

/**
 * Função para alternar sub-tabs corrigida
 */
window.switchSubTab = function(section, subtab) {
    console.log(`🔄 Alternando sub-tab: ${section} → ${subtab}`);

    try {
        const sectionElement = document.getElementById('section-' + section);
        if (!sectionElement) {
            console.error(`❌ Seção não encontrada: section-${section}`);
            return;
        }

        // Esconder todos os conteúdos de sub-tabs
        sectionElement.querySelectorAll('.sub-tab-content').forEach(content => {
            content.classList.remove('active');
            content.style.display = 'none';
        });

        // Desativar todos os botões de sub-tab
        sectionElement.querySelectorAll('.sub-tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Mostrar o sub-tab selecionado
        const targetId = `${section}-subtab-${subtab}`;
        const targetContent = document.getElementById(targetId);

        if (targetContent) {
            targetContent.classList.add('active');
            targetContent.style.display = 'block';
        } else {
            console.error(`❌ Sub-tab não encontrada: ${targetId}`);
            return;
        }

        // Ativar o botão clicado
        if (event && event.target) {
            const clickedButton = event.target.closest('.sub-tab-btn');
            if (clickedButton) {
                clickedButton.classList.add('active');
            }
        }

        // Carregar dados específicos da sub-tab
        carregarDadosSubTabOtimizado(section, subtab);

    } catch (error) {
        console.error('❌ Erro ao alternar sub-tab:', error);
    }
};

/**
 * Remove elementos de estoque indevidos
 */
function removeEstoqueIndevido(sectionElement) {
    // Remover elementos de estoque que aparecem indevidamente
    const estoqueIndevido = sectionElement.querySelectorAll('.estoque-baixo, .estoque-card, .estoque-widget');
    estoqueIndevido.forEach(el => {
        el.style.display = 'none';
    });
}

/**
 * Carrega dados da seção com proteção contra loop infinito
 */
function carregarDadosSecaoOtimizado(section) {
    // Prevenir múltiplas chamadas
    if (window.carregandoSecao === section) {
        console.log(`⚠️ Já carregando seção: ${section}`);
        return;
    }

    window.carregandoSecao = section;

    const carregarFuncoes = {
        'dashboard': loadDashboardOtimizado,
        'clientes': () => loadClientesOtimizado(1),
        'profissionais': () => loadProfissionaisOtimizado(1),
        'produtos': () => loadProdutosOtimizado(1),
        'servicos': () => loadServicosOtimizado(1),
        'estoque': loadEstoqueOtimizado,
        'agendamentos': () => loadAgendamentosOtimizado(1),
        'relatorios': loadRelatoriosOtimizado,
        'financeiro': loadFinanceiroOtimizado,
        'auditoria': () => loadAuditoriaOtimizado(1),
        'avaliacoes': carregarAvaliacoesPendentes
    };

    const funcao = carregarFuncoes[section];
    if (funcao && typeof funcao === 'function') {
        setTimeout(() => {
            funcao();
            window.carregandoSecao = null;
        }, 300);
    } else {
        window.carregandoSecao = null;
        console.log(`ℹ️ Seção ${section} não requer carregamento automático`);
    }
}

/**
 * Carrega dados de sub-tabs com proteção
 */
function carregarDadosSubTabOtimizado(section, subtab) {
    const key = `${section}-${subtab}`;

    // Prevenir múltiplas chamadas
    if (window.carregandoSubTab === key) {
        console.log(`⚠️ Já carregando sub-tab: ${key}`);
        return;
    }

    window.carregandoSubTab = key;

    const carregarFuncoes = {
        'orcamento-pendentes': loadOrcamentosPendentes,
        'orcamento-aprovados': loadOrcamentosAprovados,
        'orcamento-rejeitados': loadOrcamentosRejeitados,
        'orcamento-historico': loadOrcamentosHistorico,
        'estoque-alertas': loadEstoqueAlertas,
        'estoque-movimentacoes': loadEstoqueMovimentacoes,
        'relatorios-mapa-calor': loadMapaCalor,
        'financeiro-receitas': loadFinanceiroReceitas,
        'financeiro-despesas': loadFinanceiroDespesas,
        'financeiro-comissoes': loadFinanceiroComissoes
    };

    const funcao = carregarFuncoes[key];
    if (funcao && typeof funcao === 'function') {
        setTimeout(() => {
            funcao();
            window.carregandoSubTab = null;
        }, 300);
    } else {
        window.carregandoSubTab = null;
    }
}

// ==================== FUNÇÕES DE CARREGAMENTO OTIMIZADAS ====================

/**
 * Dashboard otimizado
 */
async function loadDashboardOtimizado() {
    try {
        console.log('📊 Carregando dashboard...');

        // Prevenir carregamento duplicado
        if (window.carregandoDashboard) return;
        window.carregandoDashboard = true;

        const response = await fetch('/api/dashboard');
        const data = await response.json();

        if (data.success) {
            renderDashboard(data.data);
        }

        window.carregandoDashboard = false;
    } catch (error) {
        console.error('❌ Erro ao carregar dashboard:', error);
        window.carregandoDashboard = false;
    }
}

/**
 * Clientes otimizado com paginação
 */
async function loadClientesOtimizado(page = 1) {
    try {
        console.log(`👥 Carregando clientes (página ${page})...`);

        if (window.carregandoClientes) return;
        window.carregandoClientes = true;

        const response = await fetch(`/api/clientes/lista-otimizada?page=${page}&per_page=50`);
        const data = await response.json();

        if (data.success) {
            renderClientesTabela(data.clientes, data.pagination);
        }

        window.carregandoClientes = false;
    } catch (error) {
        console.error('❌ Erro ao carregar clientes:', error);
        window.carregandoClientes = false;
    }
}

/**
 * Profissionais otimizado
 */
async function loadProfissionaisOtimizado(page = 1) {
    try {
        console.log(`👨‍💼 Carregando profissionais (página ${page})...`);

        if (window.carregandoProfissionais) return;
        window.carregandoProfissionais = true;

        const response = await fetch(`/api/profissionais/lista-otimizada?page=${page}&per_page=50`);
        const data = await response.json();

        if (data.success) {
            renderProfissionaisTabela(data.profissionais, data.pagination);
        }

        window.carregandoProfissionais = false;
    } catch (error) {
        console.error('❌ Erro ao carregar profissionais:', error);
        window.carregandoProfissionais = false;
    }
}

/**
 * Produtos otimizado
 */
async function loadProdutosOtimizado(page = 1) {
    try {
        console.log(`📦 Carregando produtos (página ${page})...`);

        if (window.carregandoProdutos) return;
        window.carregandoProdutos = true;

        const response = await fetch(`/api/produtos/lista-otimizada?page=${page}&per_page=50`);
        const data = await response.json();

        if (data.success) {
            renderProdutosTabela(data.produtos, data.pagination);
        }

        window.carregandoProdutos = false;
    } catch (error) {
        console.error('❌ Erro ao carregar produtos:', error);
        window.carregandoProdutos = false;
    }
}

/**
 * Serviços otimizado
 */
async function loadServicosOtimizado(page = 1) {
    try {
        console.log(`✂️ Carregando serviços (página ${page})...`);

        if (window.carregandoServicos) return;
        window.carregandoServicos = true;

        const response = await fetch(`/api/servicos/lista-otimizada?page=${page}&per_page=50`);
        const data = await response.json();

        if (data.success) {
            renderServicosTabela(data.servicos, data.pagination);
        }

        window.carregandoServicos = false;
    } catch (error) {
        console.error('❌ Erro ao carregar serviços:', error);
        window.carregandoServicos = false;
    }
}

/**
 * Estoque otimizado - CORRIGE CARREGAMENTO INFINITO
 */
async function loadEstoqueOtimizado() {
    try {
        console.log('📊 Carregando estoque...');

        if (window.carregandoEstoque) return;
        window.carregandoEstoque = true;

        const response = await fetch('/api/estoque/visao-geral-otimizada');
        const data = await response.json();

        if (data.success) {
            renderEstoqueVisaoGeral(data.data);
        }

        window.carregandoEstoque = false;
    } catch (error) {
        console.error('❌ Erro ao carregar estoque:', error);
        window.carregandoEstoque = false;
    }
}

/**
 * Agendamentos otimizado - CORRIGE CARREGAMENTO INFINITO
 */
async function loadAgendamentosOtimizado(page = 1) {
    try {
        console.log(`📅 Carregando agendamentos (página ${page})...`);

        if (window.carregandoAgendamentos) return;
        window.carregandoAgendamentos = true;

        const response = await fetch(`/api/agendamentos/lista-otimizada?page=${page}&per_page=50`);
        const data = await response.json();

        if (data.success) {
            renderAgendamentosTabela(data.agendamentos, data.pagination);
        }

        window.carregandoAgendamentos = false;
    } catch (error) {
        console.error('❌ Erro ao carregar agendamentos:', error);
        window.carregandoAgendamentos = false;
    }
}

/**
 * Relatórios otimizado
 */
async function loadRelatoriosOtimizado() {
    try {
        console.log('📈 Carregando relatórios...');

        if (window.carregandoRelatorios) return;
        window.carregandoRelatorios = true;

        const response = await fetch('/api/relatorios/resumo-geral');
        const data = await response.json();

        if (data.success) {
            renderResumoGeral(data);
        }

        window.carregandoRelatorios = false;
    } catch (error) {
        console.error('❌ Erro ao carregar relatórios:', error);
        window.carregandoRelatorios = false;
    }
}

/**
 * Financeiro otimizado
 */
async function loadFinanceiroOtimizado() {
    try {
        console.log('💰 Carregando financeiro...');

        if (window.carregandoFinanceiro) return;
        window.carregandoFinanceiro = true;

        const response = await fetch('/api/financeiro/resumo');
        const data = await response.json();

        if (data.success) {
            renderFinanceiroResumo(data.data);
        }

        window.carregandoFinanceiro = false;
    } catch (error) {
        console.error('❌ Erro ao carregar financeiro:', error);
        window.carregandoFinanceiro = false;
    }
}

/**
 * Auditoria otimizado
 */
async function loadAuditoriaOtimizado(page = 1) {
    try {
        console.log(`🔍 Carregando auditoria (página ${page})...`);

        if (window.carregandoAuditoria) return;
        window.carregandoAuditoria = true;

        const response = await fetch(`/api/auditoria/logs?page=${page}&per_page=50`);
        const data = await response.json();

        if (data.success) {
            renderAuditoriaTabela(data.logs, data.pagination);
        }

        window.carregandoAuditoria = false;
    } catch (error) {
        console.error('❌ Erro ao carregar auditoria:', error);
        window.carregandoAuditoria = false;
    }
}

// ==================== FUNÇÕES AUXILIARES ====================

/**
 * Retorna classe de badge baseada no status
 */
function getStatusClass(status) {
    const classes = {
        'confirmado': 'success',
        'pendente': 'warning',
        'cancelado': 'danger',
        'concluido': 'info',
        'aprovado': 'success',
        'rejeitado': 'danger'
    };
    return classes[status?.toLowerCase()] || 'secondary';
}

/**
 * Renderiza paginação genérica
 */
function renderPaginacao(tipo, pagination, loadFunction) {
    const container = document.getElementById(`${tipo}Paginacao`);
    if (!container || !pagination) return;

    const { page, total_pages } = pagination;

    let html = '<nav><ul class="pagination justify-content-center">';

    // Botão anterior
    html += `<li class="page-item ${page === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="event.preventDefault(); ${loadFunction.name}(${page - 1})">Anterior</a>
    </li>`;

    // Números das páginas
    for (let i = 1; i <= total_pages; i++) {
        if (i === 1 || i === total_pages || (i >= page - 2 && i <= page + 2)) {
            html += `<li class="page-item ${i === page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="event.preventDefault(); ${loadFunction.name}(${i})">${i}</a>
            </li>`;
        } else if (i === page - 3 || i === page + 3) {
            html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
    }

    // Botão próximo
    html += `<li class="page-item ${page === total_pages ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="event.preventDefault(); ${loadFunction.name}(${page + 1})">Próximo</a>
    </li>`;

    html += '</ul></nav>';
    container.innerHTML = html;
}

/**
 * Mostra mensagem de sucesso
 */
function mostrarSucesso(mensagem) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: 'success',
            title: 'Sucesso!',
            text: mensagem,
            timer: 3000,
            showConfirmButton: false
        });
    } else {
        alert('✅ ' + mensagem);
    }
}

/**
 * Mostra mensagem de erro
 */
function mostrarErro(mensagem) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: 'error',
            title: 'Erro!',
            text: mensagem
        });
    } else {
        alert('❌ ' + mensagem);
    }
}

// ==================== INICIALIZAÇÃO ====================

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ BIOMA Fixes Complete inicializado!');

    // Remover elementos de estoque de páginas incorretas ao iniciar
    const currentSection = document.querySelector('.content-section.active');
    if (currentSection && !currentSection.id.includes('estoque')) {
        removeEstoqueIndevido(currentSection);
    }

    // Configurar proteção contra loops infinitos
    window.carregandoSecao = null;
    window.carregandoSubTab = null;
});

console.log('✅ BIOMA Fixes Complete carregado com sucesso!');