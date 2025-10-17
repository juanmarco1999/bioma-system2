// ============================================
// BIOMA UBERABA v4.0 - Melhorias Adicionais Solicitadas
// Desenvolvedor: Juan Marco (@juanmarco1999)
// ============================================

console.log('🚀 Carregando BIOMA Melhorias v4.0...');

// ========== MELHORIA #3 E #13: BUSCA GLOBAL COM AUTOCOMPLETAR ==========

let buscaGlobalTimeout = null;

function setupBuscaGlobal() {
    // Criar container de busca global no topo da sidebar
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;

    // Verificar se já existe
    if (document.getElementById('busca-global-container')) return;

    const buscaHTML = `
        <div id="busca-global-container" style="padding: 15px 20px; border-bottom: 1px solid rgba(255,255,255,0.1);">
            <div style="position: relative;">
                <input type="text" id="busca-global-input" class="form-control"
                       placeholder="🔍 Buscar em todo o sistema..."
                       style="background: rgba(255,255,255,0.1); color: #fff; border: 2px solid rgba(255,255,255,0.2); padding-right: 35px;">
                <div id="busca-global-results" class="autocomplete-results" style="z-index: 9999;"></div>
            </div>
        </div>
    `;

    const logo = sidebar.querySelector('.sidebar-logo');
    if (logo) {
        logo.insertAdjacentHTML('afterend', buscaHTML);

        const input = document.getElementById('busca-global-input');
        const resultsDiv = document.getElementById('busca-global-results');

        input.addEventListener('input', function() {
            clearTimeout(buscaGlobalTimeout);
            const termo = this.value.trim();

            if (termo.length < 2) {
                resultsDiv.style.display = 'none';
                return;
            }

            buscaGlobalTimeout = setTimeout(async () => {
                try {
                    const res = await fetch(`/api/busca/global?termo=${encodeURIComponent(termo)}`, {
                        credentials: 'include'
                    });
                    const data = await res.json();

                    if (data.success && data.resultados) {
                        const resultados = data.resultados;
                        let htmlResultados = '';

                        // Processar cada categoria
                        ['clientes', 'profissionais', 'servicos', 'produtos', 'orcamentos'].forEach(categoria => {
                            if (resultados[categoria] && resultados[categoria].length > 0) {
                                const categoriaNome = {
                                    'clientes': 'Clientes',
                                    'profissionais': 'Profissionais',
                                    'servicos': 'Serviços',
                                    'produtos': 'Produtos',
                                    'orcamentos': 'Orçamentos'
                                };

                                htmlResultados += `
                                    <div style="padding: 8px 15px; background: var(--primary); color: white; font-weight: bold; font-size: 0.85rem;">
                                        ${categoriaNome[categoria]}
                                    </div>
                                `;

                                resultados[categoria].forEach(item => {
                                    const foto = item.foto ? `<img src="${item.foto}" style="width: 30px; height: 30px; border-radius: 50%; margin-right: 10px; object-fit: cover;">` : '';
                                    htmlResultados += `
                                        <div class="autocomplete-item" onclick="navegarParaItem('${item.tipo}', '${item.id}')">
                                            <div style="display: flex; align-items: center;">
                                                ${foto}
                                                <div>
                                                    <div><i class="bi ${item.icone}"></i> <strong>${item.titulo}</strong></div>
                                                    <small class="text-muted">${item.subtitulo}</small>
                                                </div>
                                            </div>
                                        </div>
                                    `;
                                });
                            }
                        });

                        if (htmlResultados) {
                            resultsDiv.innerHTML = htmlResultados;
                            resultsDiv.style.display = 'block';
                        } else {
                            resultsDiv.innerHTML = '<div class="autocomplete-item text-muted">Nenhum resultado encontrado</div>';
                            resultsDiv.style.display = 'block';
                        }
                    }
                } catch (e) {
                    console.error('Erro na busca global:', e);
                }
            }, 300);
        });

        // Fechar ao clicar fora
        document.addEventListener('click', function(e) {
            if (!input.contains(e.target) && !resultsDiv.contains(e.target)) {
                resultsDiv.style.display = 'none';
            }
        });
    }
}

function navegarParaItem(tipo, id) {
    // Fechar resultados
    document.getElementById('busca-global-results').style.display = 'none';
    document.getElementById('busca-global-input').value = '';

    // Navegar para a aba correspondente e mostrar detalhes
    const abaMap = {
        'cliente': 'clientes',
        'profissional': 'profissionais',
        'servico': 'servicos',
        'produto': 'produtos',
        'orcamento': 'consultar'
    };

    const aba = abaMap[tipo];
    if (aba && typeof goTo === 'function') {
        goTo(aba);

        // Aguardar a aba carregar e então mostrar detalhes
        setTimeout(() => {
            if (tipo === 'profissional' && typeof visualizarProfissional === 'function') {
                visualizarProfissional(id);
            } else if (tipo === 'servico' && typeof visualizarServico === 'function') {
                visualizarServico(id);
            } else if (tipo === 'produto' && typeof visualizarProduto === 'function') {
                visualizarProduto(id);
            } else if (tipo === 'cliente' && typeof visualizarCliente === 'function') {
                visualizarCliente(id);
            } else if (tipo === 'orcamento' && typeof visualizarOrcamento === 'function') {
                visualizarOrcamento(id);
            }
        }, 300);
    }
}

// ========== MELHORIA #9: CALENDÁRIO AVANÇADO COM MAPA DE CALOR ==========

async function carregarCalendarioAvancado() {
    const mes = new Date().getMonth() + 1;
    const ano = new Date().getFullYear();

    try {
        const res = await fetch(`/api/agendamentos/calendario?mes=${mes}&ano=${ano}`, {
            credentials: 'include'
        });
        const data = await res.json();

        if (data.success) {
            renderizarCalendario(data.calendario, data.mapa_calor, mes, ano);
        }
    } catch (e) {
        console.error('Erro ao carregar calendário:', e);
    }
}

function renderizarCalendario(calendario, mapaCalor, mes, ano) {
    const container = document.getElementById('calendario-container');
    if (!container) return;

    const diasNoMes = new Date(ano, mes, 0).getDate();
    const primeiroDia = new Date(ano, mes - 1, 1).getDay();

    const diasSemana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
    const mesNome = new Date(ano, mes - 1).toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });

    let html = `
        <div style="text-align: center; margin-bottom: 20px;">
            <h3 style="color: var(--primary); text-transform: capitalize;">${mesNome}</h3>
        </div>
        <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; margin-bottom: 30px;">
    `;

    // Cabeçalho com dias da semana
    diasSemana.forEach(dia => {
        html += `<div style="text-align: center; font-weight: bold; padding: 10px; background: var(--primary); color: white; border-radius: 8px;">${dia}</div>`;
    });

    // Células vazias antes do primeiro dia
    for (let i = 0; i < primeiroDia; i++) {
        html += `<div></div>`;
    }

    // Dias do mês
    const hoje = new Date();
    for (let dia = 1; dia <= diasNoMes; dia++) {
        const dataAtual = new Date(ano, mes - 1, dia);
        const ehPassado = dataAtual < hoje.setHours(0, 0, 0, 0);
        const ehHoje = dataAtual.toDateString() === new Date().toDateString();

        const agendamentos = calendario[dia] || { total: 0 };
        const movimentacao = mapaCalor[dia] || { orcamentos: 0, valor: 0 };

        // Determinar cor baseado em ocupação (verde = livre, vermelho = ocupado)
        let corFundo = 'var(--bg-card)';
        let corBorda = 'var(--border-color)';

        if (ehPassado) {
            corFundo = 'rgba(150, 150, 150, 0.1)';
            corBorda = 'rgba(150, 150, 150, 0.3)';
        } else if (agendamentos.total >= 8) {
            // Totalmente ocupado
            corFundo = 'rgba(239, 68, 68, 0.2)';
            corBorda = 'var(--danger)';
        } else if (agendamentos.total > 0) {
            // Parcialmente ocupado
            corFundo = 'rgba(245, 158, 11, 0.2)';
            corBorda = 'var(--warning)';
        } else {
            // Livre
            corFundo = 'rgba(16, 185, 129, 0.1)';
            corBorda = 'var(--success)';
        }

        // Intensidade do mapa de calor
        const intensidadeCalor = movimentacao.orcamentos > 0 ? Math.min(movimentacao.orcamentos / 5, 1) : 0;

        html += `
            <div style="
                background: ${corFundo};
                border: 2px solid ${corBorda};
                border-radius: 12px;
                padding: 10px;
                min-height: 100px;
                cursor: pointer;
                position: relative;
                ${ehHoje ? 'box-shadow: 0 0 15px var(--primary);' : ''}
                ${ehPassado ? 'text-decoration: line-through; opacity: 0.5;' : ''}
            " onclick="${ehPassado ? '' : `abrirDiaCalendario(${dia}, ${mes}, ${ano})`}">
                <div style="font-size: 1.5rem; font-weight: bold; margin-bottom: 5px;">${dia}</div>
                ${agendamentos.total > 0 ? `<div style="font-size: 0.75rem;">📅 ${agendamentos.total} agend.</div>` : ''}
                ${movimentacao.orcamentos > 0 ? `<div style="font-size: 0.75rem;">📊 ${movimentacao.orcamentos} orç.</div>` : ''}
                ${movimentacao.valor > 0 ? `<div style="font-size: 0.7rem; color: var(--success);">💰 R$ ${movimentacao.valor.toFixed(0)}</div>` : ''}
                ${intensidadeCalor > 0 ? `
                    <div style="position: absolute; bottom: 5px; right: 5px; font-size: 1.2rem;">
                        🔥${'🔥'.repeat(Math.ceil(intensidadeCalor * 3))}
                    </div>
                ` : ''}
            </div>
        `;
    }

    html += '</div>';

    // Legenda
    html += `
        <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; margin-top: 20px; padding: 20px; background: var(--bg-main); border-radius: 12px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="width: 20px; height: 20px; background: rgba(16, 185, 129, 0.3); border: 2px solid var(--success); border-radius: 4px;"></div>
                <span>Disponível</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="width: 20px; height: 20px; background: rgba(245, 158, 11, 0.3); border: 2px solid var(--warning); border-radius: 4px;"></div>
                <span>Parcial</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="width: 20px; height: 20px; background: rgba(239, 68, 68, 0.3); border: 2px solid var(--danger); border-radius: 4px;"></div>
                <span>Ocupado</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span>🔥</span>
                <span>Alta movimentação</span>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

function abrirDiaCalendario(dia, mes, ano) {
    Swal.fire({
        title: `📅 Dia ${dia}/${mes}/${ano}`,
        text: 'Criar novo agendamento para este dia?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Sim, criar agendamento',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed && typeof showModalAgendamento === 'function') {
            // Pré-preencher data
            const dataStr = `${ano}-${String(mes).padStart(2, '0')}-${String(dia).padStart(2, '0')}`;
            showModalAgendamento(dataStr);
        }
    });
}

// ========== MELHORIA #10: VISUALIZAÇÃO DETALHADA DE PROFISSIONAL COM COMISSÕES ==========

async function visualizarProfissional(id) {
    try {
        // Buscar dados do profissional e estatísticas
        const [profRes, statsRes] = await Promise.all([
            fetch(`/api/profissionais/${id}`, {credentials: 'include'}),
            fetch(`/api/profissionais/${id}/stats`, {credentials: 'include'})
        ]);

        const profData = await profRes.json();
        const statsData = await statsRes.json();

        if (!profData.success || !profData.profissional) {
            Swal.fire('Erro', 'Profissional não encontrado', 'error');
            return;
        }

        const prof = profData.profissional;
        const stats = statsData.success ? statsData.stats : {};

        const foto = prof.foto_url || 'https://via.placeholder.com/150';

        let assistentesHTML = '';
        if (prof.assistentes && prof.assistentes.length > 0) {
            assistentesHTML = `
                <div class="mt-4" style="border-top: 2px solid var(--border-color); padding-top: 20px;">
                    <h5 style="color: var(--primary);">👥 Assistentes</h5>
                    ${prof.assistentes.map(a => `
                        <div style="background: var(--bg-main); padding: 12px; border-radius: 8px; margin-top: 10px; border-left: 4px solid var(--secondary);">
                            <strong>${a.nome}</strong>
                            <div class="text-muted small">
                                Comissão: ${a.comissao_perc_sobre_profissional}% sobre a comissão do profissional
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        Swal.fire({
            title: '👤 Detalhes do Profissional',
            html: `
                <div style="text-align: left; max-height: 70vh; overflow-y: auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <img src="${foto}" style="width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 4px solid var(--primary); box-shadow: 0 5px 20px rgba(124,58,237,0.3);">
                        <h3 style="margin-top: 15px; color: var(--primary);">${prof.nome}</h3>
                        <p style="color: var(--text-secondary); font-size: 1.1rem;">${prof.especialidade || 'N/A'}</p>
                    </div>

                    <div class="row g-3 mb-4">
                        <div class="col-6">
                            <div style="background: linear-gradient(135deg, rgba(124,58,237,0.1), rgba(236,72,153,0.1)); padding: 20px; border-radius: 12px; text-align: center;">
                                <div style="font-size: 2rem; font-weight: bold; color: var(--success);">R$ ${(stats.total_comissoes || 0).toFixed(2)}</div>
                                <div class="text-muted">Total em Comissões</div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div style="background: linear-gradient(135deg, rgba(16,185,129,0.1), rgba(245,158,11,0.1)); padding: 20px; border-radius: 12px; text-align: center;">
                                <div style="font-size: 2rem; font-weight: bold; color: var(--primary);">${stats.total_servicos || 0}</div>
                                <div class="text-muted">Serviços Realizados</div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div style="background: linear-gradient(135deg, rgba(245,158,11,0.1), rgba(239,68,68,0.1)); padding: 20px; border-radius: 12px; text-align: center;">
                                <div style="font-size: 1.5rem; font-weight: bold; color: var(--secondary);">R$ ${(stats.total_faturamento_gerado || 0).toFixed(2)}</div>
                                <div class="text-muted">Faturamento Gerado</div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div style="background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(124,58,237,0.1)); padding: 20px; border-radius: 12px; text-align: center;">
                                <div style="font-size: 1.5rem; font-weight: bold; color: var(--info);">R$ ${(stats.ticket_medio || 0).toFixed(2)}</div>
                                <div class="text-muted">Ticket Médio</div>
                            </div>
                        </div>
                    </div>

                    <div style="background: var(--bg-main); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                        <h5 style="color: var(--primary); margin-bottom: 15px;">📋 Informações</h5>
                        <p><strong>CPF:</strong> ${prof.cpf || 'N/A'}</p>
                        <p><strong>Email:</strong> ${prof.email || 'N/A'}</p>
                        <p><strong>Telefone:</strong> ${prof.telefone || 'N/A'}</p>
                        <p><strong>Comissão:</strong> <span style="font-size: 1.2rem; color: var(--success); font-weight: bold;">${prof.comissao_perc || 0}%</span></p>
                        <p><strong>Status:</strong> <span class="badge ${prof.ativo ? 'success' : 'danger'}">${prof.ativo ? 'Ativo' : 'Inativo'}</span></p>
                    </div>

                    ${assistentesHTML}

                    <div class="mt-4" style="text-align: center;">
                        <button class="btn btn-primary" onclick="editarProfissional('${id}')">
                            <i class="bi bi-pencil"></i> Editar Profissional
                        </button>
                        <button class="btn btn-success" onclick="calcularComissoesProfissional('${id}')">
                            <i class="bi bi-calculator"></i> Calcular Comissões
                        </button>
                    </div>
                </div>
            `,
            width: '800px',
            showConfirmButton: false,
            showCloseButton: true
        });
    } catch (e) {
        Swal.fire('Erro', 'Não foi possível carregar os dados do profissional', 'error');
        console.error('Erro:', e);
    }
}

function editarProfissional(id) {
    Swal.close();
    if (typeof showModalProfissionalMelhorado === 'function') {
        showModalProfissionalMelhorado(id);
    }
}

async function calcularComissoesProfissional(profId) {
    // Buscar orçamentos
    const res = await fetch('/api/orcamentos', {credentials: 'include'});
    const data = await res.json();

    if (!data.success) {
        Swal.fire('Erro', 'Não foi possível carregar orçamentos', 'error');
        return;
    }

    const orcamentos = data.orcamentos.filter(o => o.status === 'Aprovado');

    // Criar lista de orçamentos para seleção
    const opcoesHTML = orcamentos.map(orc => {
        // Verificar se tem serviços do profissional
        const temServico = orc.servicos?.some(s => s.profissional_id === profId);
        if (!temServico) return '';

        return `<option value="${orc._id}">Orçamento #${orc.numero} - ${orc.cliente_nome} - R$ ${orc.total_final.toFixed(2)}</option>`;
    }).filter(Boolean).join('');

    if (!opcoesHTML) {
        Swal.fire('Info', 'Nenhum orçamento encontrado para este profissional', 'info');
        return;
    }

    const result = await Swal.fire({
        title: '💰 Calcular Comissões',
        html: `
            <div class="mb-3">
                <label class="fw-bold">Selecione um Orçamento:</label>
                <select id="orcamento-comissao" class="form-select">
                    ${opcoesHTML}
                </select>
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: 'Calcular',
        cancelButtonText: 'Cancelar',
        preConfirm: () => {
            return document.getElementById('orcamento-comissao').value;
        }
    });

    if (result.isConfirmed && result.value) {
        try {
            const calcRes = await fetch('/api/comissoes/calcular', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                credentials: 'include',
                body: JSON.stringify({orcamento_id: result.value})
            });

            const calcData = await calcRes.json();

            if (calcData.success && calcData.comissoes) {
                const comissoes = calcData.comissoes;

                let htmlComissoes = '';
                comissoes.forEach(c => {
                    htmlComissoes += `
                        <div style="background: var(--bg-main); padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid var(--primary);">
                            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
                                ${c.profissional_foto ? `<img src="${c.profissional_foto}" style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover;">` : ''}
                                <div>
                                    <h5 style="margin: 0; color: var(--primary);">${c.profissional_nome}</h5>
                                    <div class="text-muted">Serviço: ${c.servico_nome}</div>
                                </div>
                            </div>
                            <div class="row g-2 mb-3">
                                <div class="col-6">
                                    <strong>Valor do Serviço:</strong><br>
                                    <span style="font-size: 1.2rem; color: var(--info);">R$ ${c.valor_servico.toFixed(2)}</span>
                                </div>
                                <div class="col-6">
                                    <strong>Comissão (${c.comissao_perc}%):</strong><br>
                                    <span style="font-size: 1.3rem; color: var(--success); font-weight: bold;">R$ ${c.comissao_valor.toFixed(2)}</span>
                                </div>
                            </div>
                    `;

                    if (c.assistentes && c.assistentes.length > 0) {
                        htmlComissoes += `
                            <div style="border-top: 1px solid var(--border-color); padding-top: 15px; margin-top: 15px;">
                                <h6 style="color: var(--secondary);"><i class="bi bi-people"></i> Assistentes:</h6>
                                ${c.assistentes.map(a => `
                                    <div style="padding: 10px; background: rgba(236,72,153,0.1); border-radius: 8px; margin-top: 8px;">
                                        <strong>${a.assistente_nome}</strong>
                                        <div class="small">
                                            ${a.comissao_perc_sobre_profissional}% sobre a comissão do profissional =
                                            <span style="color: var(--success); font-weight: bold;">R$ ${a.comissao_valor.toFixed(2)}</span>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        `;
                    }

                    htmlComissoes += '</div>';
                });

                Swal.fire({
                    title: '📊 Comissões Calculadas',
                    html: `
                        <div style="max-height: 60vh; overflow-y: auto; text-align: left;">
                            ${htmlComissoes}
                        </div>
                    `,
                    width: '900px',
                    confirmButtonText: 'Fechar'
                });
            }
        } catch (e) {
            Swal.fire('Erro', 'Erro ao calcular comissões', 'error');
        }
    }
}

// ========== MELHORIA #11: UPLOAD DE LOGO ==========

async function configurarLogoEmpresa() {
    const result = await Swal.fire({
        title: '🏢 Logo da Empresa',
        html: `
            <div style="text-align: center; padding: 20px;">
                <div id="preview-logo-container" style="margin: 20px auto; max-width: 300px;">
                    <img id="preview-logo-empresa" src="https://via.placeholder.com/300x100?text=Logo+da+Empresa"
                         style="max-width: 100%; border: 2px solid var(--border-color); border-radius: 12px; padding: 10px; background: white;">
                </div>
                <input type="file" id="logo-empresa-input" accept="image/*" class="form-control mt-3">
                <small class="text-muted">Formato: PNG, JPG, SVG (máx 2MB) - Recomendado: 300x100px</small>
            </div>
        `,
        width: '600px',
        showCancelButton: true,
        confirmButtonText: 'Salvar Logo',
        cancelButtonText: 'Cancelar',
        didOpen: () => {
            document.getElementById('logo-empresa-input').addEventListener('change', function(e) {
                if (e.target.files && e.target.files[0]) {
                    const reader = new FileReader();
                    reader.onload = function(event) {
                        document.getElementById('preview-logo-empresa').src = event.target.result;
                    };
                    reader.readAsDataURL(e.target.files[0]);
                }
            });

            // Carregar logo atual se existir
            fetch('/api/config', {credentials: 'include'})
                .then(res => res.json())
                .then(data => {
                    if (data.success && data.config && data.config.logo_url) {
                        document.getElementById('preview-logo-empresa').src = data.config.logo_url;
                    }
                });
        },
        preConfirm: () => {
            const input = document.getElementById('logo-empresa-input');
            if (!input.files || !input.files[0]) {
                Swal.showValidationMessage('Selecione uma imagem');
                return false;
            }
            return input.files[0];
        }
    });

    if (result.isConfirmed && result.value) {
        const formData = new FormData();
        formData.append('logo', result.value);

        try {
            Swal.fire({
                title: 'Uploading...',
                html: 'Enviando logo...',
                allowOutsideClick: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });

            const res = await fetch('/api/config/logo', {
                method: 'POST',
                credentials: 'include',
                body: formData
            });

            const data = await res.json();
            if (data.success) {
                Swal.fire('Sucesso!', 'Logo atualizado! Recarregue a página para ver as mudanças.', 'success');

                // Atualizar logo no sidebar
                setTimeout(() => {
                    atualizarLogosSistema();
                }, 1000);
            } else {
                Swal.fire('Erro', data.message || 'Erro ao fazer upload', 'error');
            }
        } catch (e) {
            Swal.fire('Erro', 'Erro ao comunicar com o servidor', 'error');
        }
    }
}

async function atualizarLogosSistema() {
    try {
        const res = await fetch('/api/config', {credentials: 'include'});
        const data = await res.json();

        if (data.success && data.config && data.config.logo_url) {
            const logoUrl = data.config.logo_url;

            // Atualizar no sidebar
            const sidebarLogo = document.querySelector('.sidebar-logo h1');
            if (sidebarLogo) {
                sidebarLogo.innerHTML = `<img src="${logoUrl}" style="max-width: 100%; max-height: 60px; object-fit: contain;">`;
            }

            // Atualizar no login
            const authLogo = document.querySelector('.auth-logo .logo-icon');
            if (authLogo) {
                authLogo.innerHTML = `<img src="${logoUrl}" style="max-width: 200px; max-height: 100px; object-fit: contain;">`;
            }
        }
    } catch (e) {
        console.error('Erro ao atualizar logos:', e);
    }
}

// ========== MELHORIA #8: RELATÓRIOS COM CARREGAMENTO AUTOMÁTICO ==========

function setupRelatoriosAutomaticos() {
    // Verificar se está na aba de relatórios
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const relatoriosSection = document.getElementById('section-relatorios');
                if (relatoriosSection && relatoriosSection.classList.contains('active')) {
                    // Carregar relatórios automaticamente
                    setTimeout(() => {
                        if (typeof loadRelatoriosAvancados === 'function') {
                            loadRelatoriosAvancados();
                        } else if (typeof loadRelatorios === 'function') {
                            loadRelatorios();
                        }
                    }, 300);
                }
            }
        });
    });

    const relatoriosSection = document.getElementById('section-relatorios');
    if (relatoriosSection) {
        observer.observe(relatoriosSection, {
            attributes: true,
            attributeFilter: ['class']
        });
    }
}

// ========== EXPORTAR FUNÇÕES GLOBALMENTE ==========

window.setupBuscaGlobal = setupBuscaGlobal;
window.navegarParaItem = navegarParaItem;
window.carregarCalendarioAvancado = carregarCalendarioAvancado;
window.renderizarCalendario = renderizarCalendario;
window.abrirDiaCalendario = abrirDiaCalendario;
window.visualizarProfissional = visualizarProfissional;
window.editarProfissional = editarProfissional;
window.calcularComissoesProfissional = calcularComissoesProfissional;
window.configurarLogoEmpresa = configurarLogoEmpresa;
window.atualizarLogosSistema = atualizarLogosSistema;
window.setupRelatoriosAutomaticos = setupRelatoriosAutomaticos;

// ========== INICIALIZAÇÃO AUTOMÁTICA ==========

document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 Inicializando melhorias v4.0...');

    // Aguardar um pouco para garantir que o DOM esteja pronto
    setTimeout(() => {
        setupBuscaGlobal();
        setupRelatoriosAutomaticos();
        atualizarLogosSistema();
        console.log('✅ BIOMA Melhorias v4.0 inicializadas!');
    }, 500);
});

console.log('✅ BIOMA Melhorias v4.0 carregadas com sucesso!');
