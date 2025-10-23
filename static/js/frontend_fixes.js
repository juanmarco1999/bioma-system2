/**
 * BIOMA SYSTEM - Frontend Fixes & Enhancements
 * Arquivo de correções e melhorias do frontend
 * Versão: 1.0
 */

console.log('🚀 Frontend Fixes carregado!');

// ==================== CORREÇÃO: NAVEGAÇÃO DE ABAS ====================

/**
 * Função principal de navegação entre seções
 * Corrige o problema de duplicação e carregamento infinito
 */
window.goTo = function(section) {
    console.log(`🔄 Navegando para: ${section}`);

    try {
        // 1. Esconder todas as seções
        document.querySelectorAll('.content-section').forEach(s => {
            s.classList.remove('active');
            s.style.display = 'none';
        });

        // 2. Mostrar apenas a seção selecionada
        const sectionElement = document.getElementById('section-' + section);
        if (sectionElement) {
            sectionElement.classList.add('active');
            sectionElement.style.display = 'block';
        } else {
            console.error(`❌ Seção não encontrada: section-${section}`);
            return;
        }

        // 3. Atualizar menu sidebar
        document.querySelectorAll('.sidebar-menu a').forEach(a => a.classList.remove('active'));
        const menu = document.getElementById('menu-' + section);
        if (menu) menu.classList.add('active');

        // 4. Scroll para o topo
        const mainContent = document.querySelector('.main-content');
        if (mainContent) mainContent.scrollTo({ top: 0, behavior: 'smooth' });

        // 5. Carregar dados da seção (apenas se necessário)
        carregarDadosSecao(section);

        console.log(`✅ Seção ativada: ${section}`);
    } catch (error) {
        console.error('❌ Erro ao navegar:', error);
    }
};

/**
 * Função para alternar sub-tabs
 * Corrige o problema de alternância de sub-abas
 */
window.switchSubTab = function(section, subtab) {
    console.log(`🔄 Alternando sub-tab: ${section} → ${subtab}`);

    try {
        // 1. Esconder todos os conteúdos de sub-tabs da seção
        const sectionElement = document.getElementById('section-' + section);
        if (!sectionElement) {
            console.error(`❌ Seção não encontrada: section-${section}`);
            return;
        }

        // Esconder todos os sub-tab-content
        sectionElement.querySelectorAll('.sub-tab-content').forEach(content => {
            content.classList.remove('active');
            content.style.display = 'none';
        });

        // 2. Desativar todos os botões de sub-tab
        sectionElement.querySelectorAll('.sub-tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // 3. Mostrar o sub-tab selecionado
        const targetId = `${section}-subtab-${subtab}`;
        const targetContent = document.getElementById(targetId);

        if (!targetContent) {
            console.error(`❌ Sub-tab não encontrada: ${targetId}`);
            return;
        }

        targetContent.classList.add('active');
        targetContent.style.display = 'block';

        // 4. Ativar o botão clicado
        const clickedButton = event?.target?.closest('.sub-tab-btn');
        if (clickedButton) {
            clickedButton.classList.add('active');
        }

        console.log(`✅ Sub-tab ativada: ${targetId}`);

        // 5. Carregar dados específicos da sub-tab
        carregarDadosSubTab(section, subtab);

    } catch (error) {
        console.error('❌ Erro ao alternar sub-tab:', error);
    }
};

/**
 * Carrega dados da seção de forma otimizada
 */
function carregarDadosSecao(section) {
    switch(section) {
        case 'dashboard':
            loadDashboardOtimizado();
            break;
        case 'clientes':
            loadClientesOtimizado();
            break;
        case 'profissionais':
            loadProfissionaisOtimizado();
            break;
        case 'produtos':
            loadProdutosOtimizado();
            break;
        case 'servicos':
            loadServicosOtimizado();
            break;
        case 'estoque':
            loadEstoqueOtimizado();
            break;
        case 'agendamentos':
            loadAgendamentosOtimizado();
            break;
        case 'relatorios':
            loadRelatoriosOtimizado();
            break;
        case 'auditoria':
            loadAuditoriaOtimizado();
            break;
        case 'financeiro':
            loadFinanceiroOtimizado();
            break;
        default:
            console.log(`ℹ️ Seção ${section} não requer carregamento automático`);
    }
}

/**
 * Carrega dados de sub-tabs específicas
 */
function carregarDadosSubTab(section, subtab) {
    const key = `${section}-${subtab}`;

    switch(key) {
        case 'orcamento-pendentes':
            loadOrcamentosPendentes();
            break;
        case 'orcamento-aprovados':
            loadOrcamentosAprovados();
            break;
        case 'orcamento-rejeitados':
            loadOrcamentosRejeitados();
            break;
        case 'estoque-alertas':
            loadEstoqueAlertas();
            break;
        case 'relatorios-mapa-calor':
            loadMapaCalor();
            break;
        default:
            console.log(`ℹ️ Sub-tab ${key} não requer carregamento específico`);
    }
}

// ==================== FUNÇÕES DE CARREGAMENTO OTIMIZADAS ====================

/**
 * Dashboard otimizado
 */
async function loadDashboardOtimizado() {
    try {
        console.log('📊 Carregando dashboard...');

        // Implementação existente ou nova otimizada
        if (typeof loadDashboard === 'function') {
            loadDashboard();
        }
    } catch (error) {
        console.error('❌ Erro ao carregar dashboard:', error);
    }
}

/**
 * Clientes otimizado com paginação
 */
async function loadClientesOtimizado(page = 1) {
    try {
        console.log('👥 Carregando clientes (página ' + page + ')...');

        const response = await fetch(`/api/clientes/lista-otimizada?page=${page}&per_page=50`);
        const data = await response.json();

        if (data.success) {
            renderClientesTabela(data.clientes, data.pagination);
        } else {
            throw new Error(data.message || 'Erro ao carregar clientes');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar clientes:', error);
        mostrarErro('Erro ao carregar clientes: ' + error.message);
    }
}

/**
 * Profissionais otimizado
 */
async function loadProfissionaisOtimizado(page = 1) {
    try {
        console.log('👨‍💼 Carregando profissionais...');

        const response = await fetch(`/api/profissionais/lista-otimizada?page=${page}&per_page=50`);
        const data = await response.json();

        if (data.success) {
            renderProfissionaisTabela(data.profissionais, data.pagination);
        } else {
            throw new Error(data.message || 'Erro ao carregar profissionais');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar profissionais:', error);
        mostrarErro('Erro ao carregar profissionais: ' + error.message);
    }
}

/**
 * Produtos otimizado
 */
async function loadProdutosOtimizado(page = 1) {
    try {
        console.log('📦 Carregando produtos...');

        const response = await fetch(`/api/produtos/lista-otimizada?page=${page}&per_page=50`);
        const data = await response.json();

        if (data.success) {
            renderProdutosTabela(data.produtos, data.pagination);
        } else {
            throw new Error(data.message || 'Erro ao carregar produtos');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar produtos:', error);
        mostrarErro('Erro ao carregar produtos: ' + error.message);
    }
}

/**
 * Serviços otimizado
 */
async function loadServicosOtimizado(page = 1) {
    try {
        console.log('✂️ Carregando serviços...');

        const response = await fetch(`/api/servicos/lista-otimizada?page=${page}&per_page=50`);
        const data = await response.json();

        if (data.success) {
            renderServicosTabela(data.servicos, data.pagination);
        } else {
            throw new Error(data.message || 'Erro ao carregar serviços');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar serviços:', error);
        mostrarErro('Erro ao carregar serviços: ' + error.message);
    }
}

/**
 * Estoque otimizado - CORRIGE CARREGAMENTO INFINITO
 */
async function loadEstoqueOtimizado() {
    try {
        console.log('📊 Carregando estoque...');

        const response = await fetch('/api/estoque/visao-geral-otimizada');
        const data = await response.json();

        if (data.success) {
            renderEstoqueVisaoGeral(data.data);
        } else {
            throw new Error(data.message || 'Erro ao carregar estoque');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar estoque:', error);
        mostrarErro('Erro ao carregar estoque: ' + error.message);
    }
}

/**
 * Agendamentos otimizado - CORRIGE CARREGAMENTO INFINITO
 */
async function loadAgendamentosOtimizado(page = 1) {
    try {
        console.log('📅 Carregando agendamentos...');

        const response = await fetch(`/api/agendamentos/lista-otimizada?page=${page}&per_page=50`);
        const data = await response.json();

        if (data.success) {
            renderAgendamentosTabela(data.agendamentos, data.pagination);
        } else {
            throw new Error(data.message || 'Erro ao carregar agendamentos');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar agendamentos:', error);
        mostrarErro('Erro ao carregar agendamentos: ' + error.message);
    }
}

/**
 * Relatórios otimizado
 */
async function loadRelatoriosOtimizado() {
    try {
        console.log('📈 Carregando relatórios...');

        const response = await fetch('/api/relatorios/resumo-geral');
        const data = await response.json();

        if (data.success) {
            renderResumoGeral(data);
        } else {
            throw new Error(data.message || 'Erro ao carregar relatórios');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar relatórios:', error);
        mostrarErro('Erro ao carregar relatórios: ' + error.message);
    }
}

/**
 * Mapa de Calor otimizado - CORRIGE CARREGAMENTO INFINITO
 */
async function loadMapaCalor() {
    try {
        console.log('🔥 Carregando mapa de calor...');

        // Pegar datas dos filtros se existirem
        const dataInicio = document.getElementById('mapaCalorDataInicio')?.value;
        const dataFim = document.getElementById('mapaCalorDataFim')?.value;

        let url = '/api/relatorios/mapa-calor?';
        if (dataInicio) url += `data_inicio=${dataInicio}&`;
        if (dataFim) url += `data_fim=${dataFim}`;

        const response = await fetch(url);
        const data = await response.json();

        if (data.success) {
            renderMapaCalor(data.mapa, data.tipo);
        } else {
            throw new Error(data.message || 'Erro ao carregar mapa de calor');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar mapa de calor:', error);
        mostrarErro('Erro ao carregar mapa de calor: ' + error.message);
    }
}

/**
 * Auditoria otimizado - CORRIGE CARREGAMENTO INFINITO
 */
async function loadAuditoriaOtimizado(page = 1) {
    try {
        console.log('🔍 Carregando auditoria...');

        const response = await fetch(`/api/auditoria/logs?page=${page}&per_page=50`);
        const data = await response.json();

        if (data.success) {
            renderAuditoriaTabela(data.logs, data.pagination);
        } else {
            throw new Error(data.message || 'Erro ao carregar auditoria');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar auditoria:', error);
        mostrarErro('Erro ao carregar auditoria: ' + error.message);
    }
}

/**
 * Financeiro - NOVA ABA
 */
async function loadFinanceiroOtimizado() {
    try {
        console.log('💰 Carregando financeiro...');

        const response = await fetch('/api/financeiro/resumo');
        const data = await response.json();

        if (data.success) {
            renderFinanceiroResumo(data.data);
        } else {
            throw new Error(data.message || 'Erro ao carregar financeiro');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar financeiro:', error);
        mostrarErro('Erro ao carregar financeiro: ' + error.message);
    }
}

// ==================== FUNÇÕES DE RENDERIZAÇÃO ====================

/**
 * Renderiza tabela de clientes
 */
function renderClientesTabela(clientes, pagination) {
    const tbody = document.getElementById('clientesTableBody');
    if (!tbody) return;

    if (!clientes || clientes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Nenhum cliente encontrado</td></tr>';
        return;
    }

    tbody.innerHTML = clientes.map(cliente => `
        <tr>
            <td>${cliente.nome || 'N/A'}</td>
            <td>${cliente.cpf || 'N/A'}</td>
            <td>${cliente.telefone || 'N/A'}</td>
            <td>${cliente.email || 'N/A'}</td>
            <td><strong>R$ ${(cliente.faturamento_total || 0).toFixed(2)}</strong></td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="visualizarCliente('${cliente._id}')">
                    <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-sm btn-outline" onclick="editarCliente('${cliente._id}')">
                    <i class="bi bi-pencil"></i>
                </button>
            </td>
        </tr>
    `).join('');

    renderPaginacao('clientes', pagination, loadClientesOtimizado);
}

/**
 * Renderiza tabela de profissionais
 */
function renderProfissionaisTabela(profissionais, pagination) {
    const tbody = document.getElementById('profissionaisTableBody');
    if (!tbody) return;

    if (!profissionais || profissionais.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Nenhum profissional encontrado</td></tr>';
        return;
    }

    tbody.innerHTML = profissionais.map(prof => `
        <tr>
            <td>
                ${prof.foto_url ? `<img src="${prof.foto_url}" class="foto-profissional" alt="${prof.nome}">` : ''}
                ${prof.nome || 'N/A'}
            </td>
            <td>${prof.especialidade || 'N/A'}</td>
            <td>${prof.telefone || 'N/A'}</td>
            <td><strong>R$ ${(prof.comissoes_total || 0).toFixed(2)}</strong></td>
            <td>${prof.total_atendimentos || 0}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="visualizarProfissional('${prof._id}')">
                    <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-sm btn-outline" onclick="editarProfissional('${prof._id}')">
                    <i class="bi bi-pencil"></i>
                </button>
            </td>
        </tr>
    `).join('');

    renderPaginacao('profissionais', pagination, loadProfissionaisOtimizado);
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

// ==================== FUNÇÕES DE IMPRESSÃO E WHATSAPP ====================

/**
 * Imprime orçamento
 */
async function imprimirOrcamento(orcamentoId) {
    try {
        console.log(`🖨️ Imprimindo orçamento ${orcamentoId}...`);

        const response = await fetch(`/api/orcamento/${orcamentoId}/imprimir`);
        const data = await response.json();

        if (data.success) {
            abrirJanelaImpressao(data.dados, 'orcamento');
        } else {
            throw new Error(data.message || 'Erro ao preparar impressão');
        }
    } catch (error) {
        console.error('❌ Erro ao imprimir orçamento:', error);
        mostrarErro('Erro ao imprimir orçamento: ' + error.message);
    }
}

/**
 * Envia orçamento via WhatsApp
 */
async function enviarWhatsAppOrcamento(orcamentoId) {
    try {
        console.log(`📱 Enviando orçamento ${orcamentoId} via WhatsApp...`);

        const response = await fetch(`/api/orcamento/${orcamentoId}/whatsapp`);
        const data = await response.json();

        if (data.success) {
            window.open(data.link, '_blank');
            mostrarSucesso('Abrindo WhatsApp...');
        } else {
            throw new Error(data.message || 'Erro ao gerar link do WhatsApp');
        }
    } catch (error) {
        console.error('❌ Erro ao enviar WhatsApp:', error);
        mostrarErro(error.message);
    }
}

/**
 * Imprime contrato
 */
async function imprimirContrato(contratoId) {
    try {
        console.log(`🖨️ Imprimindo contrato ${contratoId}...`);

        const response = await fetch(`/api/contrato/${contratoId}/imprimir`);
        const data = await response.json();

        if (data.success) {
            abrirJanelaImpressao(data.dados, 'contrato');
        } else {
            throw new Error(data.message || 'Erro ao preparar impressão');
        }
    } catch (error) {
        console.error('❌ Erro ao imprimir contrato:', error);
        mostrarErro('Erro ao imprimir contrato: ' + error.message);
    }
}

/**
 * Envia contrato via WhatsApp
 */
async function enviarWhatsAppContrato(contratoId) {
    try {
        console.log(`📱 Enviando contrato ${contratoId} via WhatsApp...`);

        const response = await fetch(`/api/contrato/${contratoId}/whatsapp`);
        const data = await response.json();

        if (data.success) {
            window.open(data.link, '_blank');
            mostrarSucesso('Abrindo WhatsApp...');
        } else {
            throw new Error(data.message || 'Erro ao gerar link do WhatsApp');
        }
    } catch (error) {
        console.error('❌ Erro ao enviar WhatsApp:', error);
        mostrarErro(error.message);
    }
}

/**
 * Abre janela de impressão
 */
function abrirJanelaImpressao(dados, tipo) {
    const janela = window.open('', '_blank', 'width=800,height=600');

    let html = `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>${tipo === 'orcamento' ? 'Orçamento' : 'Contrato'} #${dados.numero}</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                .header { text-align: center; margin-bottom: 30px; }
                .info { margin: 20px 0; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #7C3AED; color: white; }
                .total { font-size: 1.5em; font-weight: bold; text-align: right; margin-top: 20px; }
                @media print {
                    .no-print { display: none; }
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>BIOMA UBERABA</h1>
                <h2>${tipo === 'orcamento' ? 'ORÇAMENTO' : 'CONTRATO'} #${dados.numero}</h2>
                <p>Data: ${dados.data}</p>
            </div>

            <div class="info">
                <h3>Cliente</h3>
                <p><strong>Nome:</strong> ${dados.cliente.nome || 'N/A'}</p>
                <p><strong>CPF:</strong> ${dados.cliente.cpf || 'N/A'}</p>
                <p><strong>Telefone:</strong> ${dados.cliente.telefone || 'N/A'}</p>
                <p><strong>E-mail:</strong> ${dados.cliente.email || 'N/A'}</p>
            </div>
    `;

    if (tipo === 'orcamento') {
        if (dados.servicos && dados.servicos.length > 0) {
            html += `
                <h3>Serviços</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Serviço</th>
                            <th>Qtd</th>
                            <th>Valor Unit.</th>
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            dados.servicos.forEach(servico => {
                html += `
                    <tr>
                        <td>${servico.nome}</td>
                        <td>${servico.quantidade}</td>
                        <td>R$ ${servico.preco_unitario.toFixed(2)}</td>
                        <td>R$ ${servico.preco_total.toFixed(2)}</td>
                    </tr>
                `;
            });
            html += '</tbody></table>';
        }

        if (dados.produtos && dados.produtos.length > 0) {
            html += `
                <h3>Produtos</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Produto</th>
                            <th>Qtd</th>
                            <th>Valor Unit.</th>
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            dados.produtos.forEach(produto => {
                html += `
                    <tr>
                        <td>${produto.nome}</td>
                        <td>${produto.quantidade}</td>
                        <td>R$ ${produto.preco_unitario.toFixed(2)}</td>
                        <td>R$ ${produto.preco_total.toFixed(2)}</td>
                    </tr>
                `;
            });
            html += '</tbody></table>';
        }

        html += `
            <div class="total">
                TOTAL: R$ ${dados.total_final.toFixed(2)}
            </div>
        `;
    }

    html += `
            <div class="no-print" style="text-align: center; margin-top: 30px;">
                <button onclick="window.print()" style="padding: 10px 20px; font-size: 16px; cursor: pointer;">
                    🖨️ Imprimir
                </button>
                <button onclick="window.close()" style="padding: 10px 20px; font-size: 16px; cursor: pointer; margin-left: 10px;">
                    Fechar
                </button>
            </div>
        </body>
        </html>
    `;

    janela.document.write(html);
    janela.document.close();
}

// ==================== FUNÇÕES DE NOTIFICAÇÃO ====================

/**
 * Notifica cliente na fila
 */
async function notificarClienteFila(agendamentoId) {
    try {
        console.log(`🔔 Notificando cliente do agendamento ${agendamentoId}...`);

        const response = await fetch('/api/fila/notificar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ agendamento_id: agendamentoId })
        });

        const data = await response.json();

        if (data.success) {
            mostrarSucesso(`Notificação enviada! ${data.dados.mensagem}`);
        } else {
            throw new Error(data.message || 'Erro ao enviar notificação');
        }
    } catch (error) {
        console.error('❌ Erro ao notificar cliente:', error);
        mostrarErro('Erro ao notificar cliente: ' + error.message);
    }
}

// ==================== UPLOAD DE LOGO ====================

/**
 * Faz upload do logo
 */
async function uploadLogo() {
    const fileInput = document.getElementById('logoUploadInput');
    if (!fileInput || !fileInput.files[0]) {
        mostrarErro('Selecione uma imagem');
        return;
    }

    try {
        const formData = new FormData();
        formData.append('logo', fileInput.files[0]);

        const response = await fetch('/api/config/logo', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            mostrarSucesso('Logo atualizado com sucesso!');
            // Atualizar preview
            const preview = document.getElementById('logoPreview');
            if (preview) {
                preview.src = data.logo_url;
                preview.style.display = 'block';
            }
            // Atualizar logo na sidebar
            atualizarLogoSidebar(data.logo_url);
        } else {
            throw new Error(data.message || 'Erro ao fazer upload');
        }
    } catch (error) {
        console.error('❌ Erro ao fazer upload do logo:', error);
        mostrarErro('Erro ao fazer upload do logo: ' + error.message);
    }
}

/**
 * Atualiza logo na sidebar
 */
function atualizarLogoSidebar(logoUrl) {
    const sidebarLogo = document.querySelector('.sidebar-logo');
    if (sidebarLogo) {
        sidebarLogo.innerHTML = `
            <img src="${logoUrl}" alt="Logo" style="max-width: 100%; max-height: 80px; object-fit: contain;">
            <p style="margin-top: 10px;">Uberaba v3.7</p>
        `;
    }
}

/**
 * Carrega logo ao iniciar
 */
async function carregarLogo() {
    try {
        const response = await fetch('/api/config/logo');
        const data = await response.json();

        if (data.success && data.logo_url) {
            atualizarLogoSidebar(data.logo_url);
            const preview = document.getElementById('logoPreview');
            if (preview) {
                preview.src = data.logo_url;
                preview.style.display = 'block';
            }
        }
    } catch (error) {
        console.error('❌ Erro ao carregar logo:', error);
    }
}

// ==================== FUNÇÕES AUXILIARES ====================

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
        alert(mensagem);
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
        alert('ERRO: ' + mensagem);
    }
}

// ==================== INICIALIZAÇÃO ====================

/**
 * Inicializa correções ao carregar a página
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Frontend Fixes inicializado!');

    // Carregar logo
    carregarLogo();

    // Configurar event listeners adicionais se necessário
});

console.log('✅ Frontend Fixes carregado com sucesso!');

// ==================== SISTEMA DE E-MAIL ====================

/**
 * Envia orçamento por e-mail
 */
async function enviarEmailOrcamento(orcamentoId) {
    try {
        console.log(`📧 Enviando orçamento ${orcamentoId} por e-mail...`);

        const response = await fetch(`/api/email/enviar-orcamento/${orcamentoId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (data.success) {
            mostrarSucesso(`E-mail enviado com sucesso para ${data.destinatario}!`);
        } else {
            throw new Error(data.message || 'Erro ao enviar e-mail');
        }
    } catch (error) {
        console.error('❌ Erro ao enviar e-mail:', error);
        mostrarErro('Erro ao enviar e-mail: ' + error.message);
    }
}

/**
 * Testa configurações de e-mail
 */
async function testarEmailConfig() {
    try {
        console.log('🧪 Testando configurações de e-mail...');

        const emailDestino = document.getElementById('emailTesteDestino')?.value;
        if (!emailDestino) {
            mostrarErro('Informe um e-mail de destino');
            return;
        }

        const response = await fetch('/api/email/teste', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email_destino: emailDestino })
        });

        const data = await response.json();

        if (data.success) {
            mostrarSucesso('E-mail de teste enviado com sucesso!');
        } else {
            throw new Error(data.message || 'Erro ao enviar e-mail de teste');
        }
    } catch (error) {
        console.error('❌ Erro ao testar e-mail:', error);
        mostrarErro('Erro ao testar e-mail: ' + error.message);
    }
}

// ==================== UPLOAD DE FOTOS DE SERVIÇOS ====================

/**
 * Faz upload de foto de serviço
 */
async function uploadFotoServico(servicoId) {
    const fileInput = document.getElementById(`fotoServicoInput-${servicoId}`);
    if (!fileInput || !fileInput.files[0]) {
        mostrarErro('Selecione uma imagem');
        return;
    }

    try {
        console.log(`📸 Fazendo upload de foto do serviço ${servicoId}...`);

        const formData = new FormData();
        formData.append('foto', fileInput.files[0]);

        const response = await fetch(`/api/servicos/${servicoId}/foto`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            mostrarSucesso('Foto adicionada com sucesso!');
            carregarFotosServico(servicoId);
            fileInput.value = ''; // Limpar input
        } else {
            throw new Error(data.message || 'Erro ao fazer upload');
        }
    } catch (error) {
        console.error('❌ Erro ao fazer upload da foto:', error);
        mostrarErro('Erro ao fazer upload da foto: ' + error.message);
    }
}

/**
 * Carrega fotos de um serviço
 */
async function carregarFotosServico(servicoId) {
    try {
        console.log(`🖼️ Carregando fotos do serviço ${servicoId}...`);

        const response = await fetch(`/api/servicos/${servicoId}/fotos`);
        const data = await response.json();

        if (data.success) {
            renderFotosServico(servicoId, data.fotos, data.foto_principal_index);
        } else {
            throw new Error(data.message || 'Erro ao carregar fotos');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar fotos:', error);
        mostrarErro('Erro ao carregar fotos: ' + error.message);
    }
}

/**
 * Renderiza fotos de serviço
 */
function renderFotosServico(servicoId, fotos, principalIndex) {
    const container = document.getElementById(`fotosServico-${servicoId}`);
    if (!container) return;

    if (!fotos || fotos.length === 0) {
        container.innerHTML = '<p class="text-muted">Nenhuma foto adicionada</p>';
        return;
    }

    container.innerHTML = fotos.map((foto, index) => `
        <div class="foto-servico-item ${index === principalIndex ? 'principal' : ''}">
            <img src="${foto.url}" alt="Foto ${index + 1}">
            ${index === principalIndex ? '<span class="badge badge-primary">Principal</span>' : ''}
            <div class="foto-acoes">
                ${index !== principalIndex ? `<button class="btn btn-sm btn-primary" onclick="definirFotoPrincipal('${servicoId}', ${index})">
                    Definir como principal
                </button>` : ''}
                <button class="btn btn-sm btn-danger" onclick="deletarFotoServico('${servicoId}', ${index})">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
            <small class="text-muted">Enviada em ${new Date(foto.data_upload).toLocaleDateString()}</small>
        </div>
    `).join('');
}

/**
 * Deleta foto de serviço
 */
async function deletarFotoServico(servicoId, fotoIndex) {
    if (!confirm('Deseja realmente excluir esta foto?')) return;

    try {
        console.log(`🗑️ Deletando foto ${fotoIndex} do serviço ${servicoId}...`);

        const response = await fetch(`/api/servicos/${servicoId}/foto/${fotoIndex}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            mostrarSucesso('Foto excluída com sucesso!');
            carregarFotosServico(servicoId);
        } else {
            throw new Error(data.message || 'Erro ao excluir foto');
        }
    } catch (error) {
        console.error('❌ Erro ao excluir foto:', error);
        mostrarErro('Erro ao excluir foto: ' + error.message);
    }
}

// ==================== SISTEMA DE AVALIAÇÕES ====================

/**
 * Cria nova avaliação
 */
async function criarAvaliacao() {
    try {
        const avaliacaoData = {
            cliente_id: document.getElementById('avaliacaoClienteId').value,
            profissional_id: document.getElementById('avaliacaoProfissionalId').value,
            servico_id: document.getElementById('avaliacaoServicoId').value,
            nota_geral: parseInt(document.getElementById('avaliacaoNotaGeral').value),
            aspectos: {
                atendimento: parseInt(document.getElementById('avaliacaoAtendimento').value),
                qualidade: parseInt(document.getElementById('avaliacaoQualidade').value),
                pontualidade: parseInt(document.getElementById('avaliacaoPontualidade').value),
                limpeza: parseInt(document.getElementById('avaliacaoLimpeza').value),
                preco: parseInt(document.getElementById('avaliacaoPreco').value)
            },
            comentario: document.getElementById('avaliacaoComentario').value
        };

        console.log('⭐ Criando avaliação...');

        const response = await fetch('/api/avaliacoes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(avaliacaoData)
        });

        const data = await response.json();

        if (data.success) {
            mostrarSucesso('Avaliação enviada! Aguardando aprovação do administrador.');
            limparFormularioAvaliacao();
        } else {
            throw new Error(data.message || 'Erro ao criar avaliação');
        }
    } catch (error) {
        console.error('❌ Erro ao criar avaliação:', error);
        mostrarErro('Erro ao criar avaliação: ' + error.message);
    }
}

/**
 * Carrega avaliações de um profissional
 */
async function carregarAvaliacoesProfissional(profissionalId) {
    try {
        console.log(`⭐ Carregando avaliações do profissional ${profissionalId}...`);

        const response = await fetch(`/api/avaliacoes/profissional/${profissionalId}`);
        const data = await response.json();

        if (data.success) {
            renderAvaliacoesProfissional(profissionalId, data.avaliacoes, data.estatisticas);
        } else {
            throw new Error(data.message || 'Erro ao carregar avaliações');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar avaliações:', error);
        mostrarErro('Erro ao carregar avaliações: ' + error.message);
    }
}

/**
 * Renderiza avaliações de profissional
 */
function renderAvaliacoesProfissional(profissionalId, avaliacoes, estatisticas) {
    const container = document.getElementById(`avaliacoesProfissional-${profissionalId}`);
    if (!container) return;

    let html = `
        <div class="avaliacoes-resumo">
            <h4>Resumo das Avaliações</h4>
            <div class="stats">
                <p><strong>Média Geral:</strong> ${estatisticas.media_geral.toFixed(1)} ⭐</p>
                <p><strong>Total de Avaliações:</strong> ${estatisticas.total_avaliacoes}</p>
            </div>
            <div class="distribuicao">
                ${Object.entries(estatisticas.distribuicao_notas).map(([nota, qtd]) => `
                    <div class="distribuicao-item">
                        <span>${nota} ⭐</span>
                        <div class="progress">
                            <div class="progress-bar" style="width: ${(qtd / estatisticas.total_avaliacoes * 100)}%"></div>
                        </div>
                        <span>${qtd}</span>
                    </div>
                `).join('')}
            </div>
            <div class="aspectos-medios">
                <h5>Média por Aspecto</h5>
                ${Object.entries(estatisticas.aspectos_medios).map(([aspecto, media]) => `
                    <p><strong>${aspecto}:</strong> ${media.toFixed(1)} ⭐</p>
                `).join('')}
            </div>
        </div>

        <div class="avaliacoes-lista">
            <h4>Avaliações Recentes</h4>
    `;

    if (avaliacoes.length === 0) {
        html += '<p class="text-muted">Nenhuma avaliação aprovada ainda.</p>';
    } else {
        avaliacoes.forEach(avaliacao => {
            html += `
                <div class="avaliacao-item">
                    <div class="avaliacao-header">
                        <strong>${avaliacao.cliente_nome}</strong>
                        <span class="avaliacao-nota">${avaliacao.nota_geral} ⭐</span>
                    </div>
                    <div class="avaliacao-data">
                        ${new Date(avaliacao.data_avaliacao).toLocaleDateString()}
                    </div>
                    ${avaliacao.comentario ? `<p class="avaliacao-comentario">${avaliacao.comentario}</p>` : ''}
                    <div class="avaliacao-aspectos">
                        <small>Atendimento: ${avaliacao.aspectos.atendimento}⭐ |
                        Qualidade: ${avaliacao.aspectos.qualidade}⭐ |
                        Pontualidade: ${avaliacao.aspectos.pontualidade}⭐ |
                        Limpeza: ${avaliacao.aspectos.limpeza}⭐ |
                        Preço: ${avaliacao.aspectos.preco}⭐</small>
                    </div>
                    ${avaliacao.resposta_profissional ? `
                        <div class="avaliacao-resposta">
                            <strong>Resposta do profissional:</strong>
                            <p>${avaliacao.resposta_profissional}</p>
                        </div>
                    ` : ''}
                </div>
            `;
        });
    }

    html += '</div>';
    container.innerHTML = html;
}

/**
 * Carrega avaliações pendentes (admin)
 */
async function carregarAvaliacoesPendentes() {
    try {
        console.log('⭐ Carregando avaliações pendentes...');

        const response = await fetch('/api/avaliacoes/pendentes');
        const data = await response.json();

        if (data.success) {
            renderAvaliacoesPendentes(data.avaliacoes);
        } else {
            throw new Error(data.message || 'Erro ao carregar avaliações pendentes');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar avaliações pendentes:', error);
        mostrarErro('Erro ao carregar avaliações pendentes: ' + error.message);
    }
}

/**
 * Renderiza avaliações pendentes
 */
function renderAvaliacoesPendentes(avaliacoes) {
    const container = document.getElementById('avaliacoesPendentes');
    if (!container) return;

    if (avaliacoes.length === 0) {
        container.innerHTML = '<p class="text-muted">Nenhuma avaliação pendente.</p>';
        return;
    }

    container.innerHTML = avaliacoes.map(avaliacao => `
        <div class="avaliacao-pendente-item">
            <div class="avaliacao-info">
                <p><strong>Cliente:</strong> ${avaliacao.cliente_nome}</p>
                <p><strong>Profissional:</strong> ${avaliacao.profissional_nome}</p>
                <p><strong>Serviço:</strong> ${avaliacao.servico_nome}</p>
                <p><strong>Nota Geral:</strong> ${avaliacao.nota_geral} ⭐</p>
                ${avaliacao.comentario ? `<p><strong>Comentário:</strong> ${avaliacao.comentario}</p>` : ''}
                <p><strong>Data:</strong> ${new Date(avaliacao.data_avaliacao).toLocaleDateString()}</p>
            </div>
            <div class="avaliacao-acoes">
                <button class="btn btn-success" onclick="aprovarAvaliacao('${avaliacao._id}')">
                    ✓ Aprovar
                </button>
                <button class="btn btn-danger" onclick="rejeitarAvaliacao('${avaliacao._id}')">
                    ✗ Rejeitar
                </button>
            </div>
        </div>
    `).join('');
}

/**
 * Aprova avaliação
 */
async function aprovarAvaliacao(avaliacaoId) {
    try {
        console.log(`✓ Aprovando avaliação ${avaliacaoId}...`);

        const response = await fetch(`/api/avaliacoes/${avaliacaoId}/aprovar`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            mostrarSucesso('Avaliação aprovada com sucesso!');
            carregarAvaliacoesPendentes();
        } else {
            throw new Error(data.message || 'Erro ao aprovar avaliação');
        }
    } catch (error) {
        console.error('❌ Erro ao aprovar avaliação:', error);
        mostrarErro('Erro ao aprovar avaliação: ' + error.message);
    }
}

/**
 * Rejeita avaliação
 */
async function rejeitarAvaliacao(avaliacaoId) {
    if (!confirm('Deseja realmente rejeitar esta avaliação?')) return;

    try {
        console.log(`✗ Rejeitando avaliação ${avaliacaoId}...`);

        const response = await fetch(`/api/avaliacoes/${avaliacaoId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            mostrarSucesso('Avaliação rejeitada.');
            carregarAvaliacoesPendentes();
        } else {
            throw new Error(data.message || 'Erro ao rejeitar avaliação');
        }
    } catch (error) {
        console.error('❌ Erro ao rejeitar avaliação:', error);
        mostrarErro('Erro ao rejeitar avaliação: ' + error.message);
    }
}

/**
 * Responder avaliação (profissional)
 */
async function responderAvaliacao(avaliacaoId) {
    const resposta = document.getElementById(`respostaAvaliacao-${avaliacaoId}`)?.value;
    if (!resposta) {
        mostrarErro('Digite uma resposta');
        return;
    }

    try {
        console.log(`💬 Respondendo avaliação ${avaliacaoId}...`);

        const response = await fetch(`/api/avaliacoes/${avaliacaoId}/responder`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resposta: resposta })
        });

        const data = await response.json();

        if (data.success) {
            mostrarSucesso('Resposta enviada com sucesso!');
            // Recarregar avaliações do profissional
            const profissionalId = data.profissional_id;
            if (profissionalId) {
                carregarAvaliacoesProfissional(profissionalId);
            }
        } else {
            throw new Error(data.message || 'Erro ao responder avaliação');
        }
    } catch (error) {
        console.error('❌ Erro ao responder avaliação:', error);
        mostrarErro('Erro ao responder avaliação: ' + error.message);
    }
}

/**
 * Limpa formulário de avaliação
 */
function limparFormularioAvaliacao() {
    document.getElementById('avaliacaoNotaGeral').value = '5';
    document.getElementById('avaliacaoAtendimento').value = '5';
    document.getElementById('avaliacaoQualidade').value = '5';
    document.getElementById('avaliacaoPontualidade').value = '5';
    document.getElementById('avaliacaoLimpeza').value = '5';
    document.getElementById('avaliacaoPreco').value = '5';
    document.getElementById('avaliacaoComentario').value = '';
}

// ==================== GRÁFICOS INTERATIVOS (CHART.JS) ====================

/**
 * Carrega e renderiza gráfico de faturamento mensal
 */
async function carregarGraficoFaturamentoMensal() {
    try {
        console.log('📊 Carregando gráfico de faturamento mensal...');

        const response = await fetch('/api/graficos/faturamento-mensal');
        const data = await response.json();

        if (data.success) {
            renderGraficoFaturamentoMensal(data.labels, data.datasets);
        } else {
            throw new Error(data.message || 'Erro ao carregar dados do gráfico');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar gráfico:', error);
        mostrarErro('Erro ao carregar gráfico: ' + error.message);
    }
}

/**
 * Renderiza gráfico de faturamento mensal com Chart.js
 */
function renderGraficoFaturamentoMensal(labels, datasets) {
    const canvas = document.getElementById('graficoFaturamentoMensal');
    if (!canvas) return;

    // Destruir gráfico anterior se existir
    if (window.chartFaturamentoMensal) {
        window.chartFaturamentoMensal.destroy();
    }

    const ctx = canvas.getContext('2d');
    window.chartFaturamentoMensal = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Faturamento Mensal - Últimos 12 Meses'
                },
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += 'R$ ' + context.parsed.y.toFixed(2);
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'R$ ' + value.toFixed(0);
                        }
                    }
                }
            }
        }
    });
}

/**
 * Carrega e renderiza gráfico de serviços mais vendidos
 */
async function carregarGraficoServicosMaisVendidos() {
    try {
        console.log('📊 Carregando gráfico de serviços mais vendidos...');

        const response = await fetch('/api/graficos/servicos-mais-vendidos');
        const data = await response.json();

        if (data.success) {
            renderGraficoServicosMaisVendidos(data.labels, data.datasets);
        } else {
            throw new Error(data.message || 'Erro ao carregar dados do gráfico');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar gráfico:', error);
        mostrarErro('Erro ao carregar gráfico: ' + error.message);
    }
}

/**
 * Renderiza gráfico de serviços mais vendidos com Chart.js
 */
function renderGraficoServicosMaisVendidos(labels, datasets) {
    const canvas = document.getElementById('graficoServicosMaisVendidos');
    if (!canvas) return;

    // Destruir gráfico anterior se existir
    if (window.chartServicosMaisVendidos) {
        window.chartServicosMaisVendidos.destroy();
    }

    const ctx = canvas.getContext('2d');
    window.chartServicosMaisVendidos = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Top 10 Serviços Mais Vendidos'
                },
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.dataset.label === 'Faturamento') {
                                label += 'R$ ' + context.parsed.y.toFixed(2);
                            } else {
                                label += context.parsed.y;
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * Carrega e renderiza gráfico de produtos mais vendidos
 */
async function carregarGraficoProdutosMaisVendidos() {
    try {
        console.log('📊 Carregando gráfico de produtos mais vendidos...');

        const response = await fetch('/api/graficos/produtos-mais-vendidos');
        const data = await response.json();

        if (data.success) {
            renderGraficoProdutosMaisVendidos(data.labels, data.datasets);
        } else {
            throw new Error(data.message || 'Erro ao carregar dados do gráfico');
        }
    } catch (error) {
        console.error('❌ Erro ao carregar gráfico:', error);
        mostrarErro('Erro ao carregar gráfico: ' + error.message);
    }
}

/**
 * Renderiza gráfico de produtos mais vendidos com Chart.js
 */
function renderGraficoProdutosMaisVendidos(labels, datasets) {
    const canvas = document.getElementById('graficoProdutosMaisVendidos');
    if (!canvas) return;

    // Destruir gráfico anterior se existir
    if (window.chartProdutosMaisVendidos) {
        window.chartProdutosMaisVendidos.destroy();
    }

    const ctx = canvas.getContext('2d');
    window.chartProdutosMaisVendidos = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Top 10 Produtos Mais Vendidos'
                },
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.dataset.label === 'Faturamento') {
                                label += 'R$ ' + context.parsed.y.toFixed(2);
                            } else {
                                label += context.parsed.y;
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * Carrega todos os gráficos
 */
function carregarTodosGraficos() {
    carregarGraficoFaturamentoMensal();
    carregarGraficoServicosMaisVendidos();
    carregarGraficoProdutosMaisVendidos();
}
