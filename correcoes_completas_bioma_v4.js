// ============================================================
// CORREÇÕES COMPLETAS PARA BIOMA v4.0
// Data: 28/10/2025
// Autor: Claude AI
// Descrição: Todas as correções para os problemas identificados
// ============================================================

// ========== 1. FUNÇÕES FALTANTES PARA ATIVAR/DESATIVAR PRODUTOS E SERVIÇOS ==========

/**
 * Ativa um serviço individual
 * @param {string} id - ID do serviço
 */
async function ativarServico(id) {
    try {
        const res = await fetch(`/api/servicos/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ ativo: true })
        });

        const data = await res.json();

        if (data.success) {
            toast('✅ Serviço ativado com sucesso!', 'success');
            loadServicosLista();
        } else {
            toast(`❌ ${data.message || 'Erro ao ativar serviço'}`, 'error');
        }
    } catch (error) {
        console.error('Erro ao ativar serviço:', error);
        toast('❌ Falha ao ativar serviço', 'error');
    }
}

/**
 * Desativa um serviço individual
 * @param {string} id - ID do serviço
 */
async function desativarServico(id) {
    try {
        const res = await fetch(`/api/servicos/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ ativo: false })
        });

        const data = await res.json();

        if (data.success) {
            toast('✅ Serviço desativado com sucesso!', 'success');
            loadServicosLista();
        } else {
            toast(`❌ ${data.message || 'Erro ao desativar serviço'}`, 'error');
        }
    } catch (error) {
        console.error('Erro ao desativar serviço:', error);
        toast('❌ Falha ao desativar serviço', 'error');
    }
}

/**
 * Ativa um produto individual
 * @param {string} id - ID do produto
 */
async function ativarProduto(id) {
    try {
        const res = await fetch(`/api/produtos/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ ativo: true })
        });

        const data = await res.json();

        if (data.success) {
            toast('✅ Produto ativado com sucesso!', 'success');
            loadProdutosLista();
        } else {
            toast(`❌ ${data.message || 'Erro ao ativar produto'}`, 'error');
        }
    } catch (error) {
        console.error('Erro ao ativar produto:', error);
        toast('❌ Falha ao ativar produto', 'error');
    }
}

/**
 * Desativa um produto individual
 * @param {string} id - ID do produto
 */
async function desativarProduto(id) {
    try {
        const res = await fetch(`/api/produtos/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ ativo: false })
        });

        const data = await res.json();

        if (data.success) {
            toast('✅ Produto desativado com sucesso!', 'success');
            loadProdutosLista();
        } else {
            toast(`❌ ${data.message || 'Erro ao desativar produto'}`, 'error');
        }
    } catch (error) {
        console.error('Erro ao desativar produto:', error);
        toast('❌ Falha ao desativar produto', 'error');
    }
}


// ========== 2. CORREÇÕES PARA ESTOQUE - ÚLTIMAS MOVIMENTAÇÕES NA VISÃO GERAL ==========

/**
 * Carrega últimas movimentações na visão geral do estoque
 */
async function carregarUltimasMovimentacoesVisaoGeral() {
    const tbody = document.getElementById('estoqueUltimasMovimentacoesVisaoGeral');
    if (!tbody) return;

    try {
        console.log('📋 Carregando últimas movimentações do estoque...');

        const res = await fetch('/api/estoque/movimentacoes?per_page=10', {
            credentials: 'include'
        });

        const data = await res.json();

        if (data.success && data.movimentacoes && data.movimentacoes.length > 0) {
            tbody.innerHTML = data.movimentacoes.map(mov => {
                const tipoClass = mov.tipo === 'entrada' ? 'success' : 'danger';
                const tipoIcon = mov.tipo === 'entrada' ? 'arrow-down-circle' : 'arrow-up-circle';

                return `
                    <tr>
                        <td>${formatarDataHora(mov.data || mov.created_at)}</td>
                        <td><strong>${mov.produto_nome || 'Produto não identificado'}</strong></td>
                        <td><span class="badge ${tipoClass}"><i class="bi bi-${tipoIcon}"></i> ${mov.tipo || 'N/A'}</span></td>
                        <td><strong>${mov.quantidade || 0}</strong></td>
                        <td>${mov.usuario || mov.responsavel || 'Sistema'}</td>
                    </tr>
                `;
            }).join('');

            console.log(`✅ ${data.movimentacoes.length} movimentações carregadas`);
        } else {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted">
                        <i class="bi bi-inbox" style="font-size: 2rem; opacity: 0.3;"></i>
                        <p style="margin-top: 10px;">Nenhuma movimentação recente</p>
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('❌ Erro ao carregar últimas movimentações:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-danger">
                    <i class="bi bi-exclamation-triangle"></i> Erro ao carregar movimentações
                </td>
            </tr>
        `;
    }
}


// ========== 3. CORREÇÕES PARA ESTOQUE - GRÁFICOS DE RELATÓRIOS ==========

/**
 * Cria ou atualiza gráfico de movimentações por mês
 */
async function criarGraficoMovimentacoesEstoque() {
    const canvas = document.getElementById('chartMovimentacoesEstoque');
    if (!canvas || !window.Chart) return;

    try {
        console.log('📊 Criando gráfico de movimentações por mês...');

        // Buscar dados dos últimos 6 meses
        const dataFim = new Date();
        const dataInicio = new Date();
        dataInicio.setMonth(dataInicio.getMonth() - 6);

        const res = await fetch(
            `/api/estoque/movimentacoes?data_inicio=${dataInicio.toISOString()}&data_fim=${dataFim.toISOString()}&per_page=10000`,
            { credentials: 'include' }
        );

        const data = await res.json();

        if (data.success && data.movimentacoes) {
            // Agrupar por mês
            const mesesData = {};
            const meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

            data.movimentacoes.forEach(mov => {
                const date = new Date(mov.data || mov.created_at);
                const mesAno = `${meses[date.getMonth()]}/${date.getFullYear().toString().slice(-2)}`;

                if (!mesesData[mesAno]) {
                    mesesData[mesAno] = { entradas: 0, saidas: 0 };
                }

                if (mov.tipo === 'entrada') {
                    mesesData[mesAno].entradas += mov.quantidade || 0;
                } else if (mov.tipo === 'saida' || mov.tipo === 'saída') {
                    mesesData[mesAno].saidas += mov.quantidade || 0;
                }
            });

            const labels = Object.keys(mesesData);
            const entradasData = labels.map(label => mesesData[label].entradas);
            const saidasData = labels.map(label => mesesData[label].saidas);

            // Destruir gráfico anterior se existir
            if (window.chartMovimentacoesEstoqueInstance) {
                window.chartMovimentacoesEstoqueInstance.destroy();
            }

            // Criar novo gráfico
            window.chartMovimentacoesEstoqueInstance = new Chart(canvas, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Entradas',
                            data: entradasData,
                            borderColor: 'rgb(16, 185, 129)',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            tension: 0.4,
                            fill: true
                        },
                        {
                            label: 'Saídas',
                            data: saidasData,
                            borderColor: 'rgb(239, 68, 68)',
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            tension: 0.4,
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    }
                }
            });

            console.log('✅ Gráfico de movimentações criado com sucesso');
        }
    } catch (error) {
        console.error('❌ Erro ao criar gráfico de movimentações:', error);
    }
}

/**
 * Cria ou atualiza gráfico de distribuição de valor do estoque
 */
async function criarGraficoValorEstoque() {
    const canvas = document.getElementById('chartValorEstoque');
    if (!canvas || !window.Chart) return;

    try {
        console.log('📊 Criando gráfico de distribuição de valor...');

        const res = await fetch('/api/produtos', { credentials: 'include' });
        const data = await res.json();

        if (data.success && data.produtos) {
            // Agrupar produtos por categoria de valor
            let valorAlto = 0;
            let valorMedio = 0;
            let valorBaixo = 0;

            data.produtos.forEach(prod => {
                const valorTotal = (prod.preco || 0) * (prod.estoque || prod.quantidade || 0);

                if (valorTotal > 1000) {
                    valorAlto += valorTotal;
                } else if (valorTotal > 100) {
                    valorMedio += valorTotal;
                } else {
                    valorBaixo += valorTotal;
                }
            });

            // Destruir gráfico anterior se existir
            if (window.chartValorEstoqueInstance) {
                window.chartValorEstoqueInstance.destroy();
            }

            // Criar novo gráfico
            window.chartValorEstoqueInstance = new Chart(canvas, {
                type: 'pie',
                data: {
                    labels: ['Alto Valor (>R$1000)', 'Médio Valor (R$100-1000)', 'Baixo Valor (<R$100)'],
                    datasets: [{
                        data: [valorAlto, valorMedio, valorBaixo],
                        backgroundColor: [
                            'rgba(124, 58, 237, 0.8)',
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)'
                        ],
                        borderColor: [
                            'rgb(124, 58, 237)',
                            'rgb(59, 130, 246)',
                            'rgb(16, 185, 129)'
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    return `${label}: R$ ${value.toFixed(2)}`;
                                }
                            }
                        }
                    }
                }
            });

            console.log('✅ Gráfico de distribuição de valor criado com sucesso');
        }
    } catch (error) {
        console.error('❌ Erro ao criar gráfico de valor:', error);
    }
}

/**
 * Função melhorada para exportar relatório em Excel
 */
async function exportarRelatorioExcel() {
    const dataInicio = document.getElementById('relatorioDataInicio')?.value;
    const dataFim = document.getElementById('relatorioDataFim')?.value;
    const tipo = document.getElementById('relatorioTipo')?.value || 'movimentacoes';

    if (!dataInicio || !dataFim) {
        Swal.fire('Atenção', 'Selecione o período do relatório', 'warning');
        return;
    }

    try {
        Swal.fire({
            title: 'Gerando Excel...',
            html: 'Por favor, aguarde...',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        const url = `/api/estoque/relatorio?tipo=${tipo}&data_inicio=${dataInicio}&data_fim=${dataFim}&formato=excel`;
        const res = await fetch(url, { credentials: 'include' });

        if (!res.ok) throw new Error('Erro ao gerar relatório');

        const blob = await res.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `relatorio_estoque_${tipo}_${dataInicio}_${dataFim}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);

        Swal.fire({
            icon: 'success',
            title: 'Excel Gerado!',
            text: 'O arquivo foi baixado com sucesso',
            timer: 3000
        });
    } catch (error) {
        console.error('Erro:', error);
        Swal.fire('Erro', 'Não foi possível gerar o arquivo Excel', 'error');
    }
}

/**
 * Função melhorada para exportar relatório em PDF
 */
async function exportarRelatorioPDF() {
    const dataInicio = document.getElementById('relatorioDataInicio')?.value;
    const dataFim = document.getElementById('relatorioDataFim')?.value;
    const tipo = document.getElementById('relatorioTipo')?.value || 'movimentacoes';

    if (!dataInicio || !dataFim) {
        Swal.fire('Atenção', 'Selecione o período do relatório', 'warning');
        return;
    }

    try {
        Swal.fire({
            title: 'Gerando PDF...',
            html: 'Por favor, aguarde...',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        const url = `/api/estoque/relatorio?tipo=${tipo}&data_inicio=${dataInicio}&data_fim=${dataFim}&formato=pdf`;
        const res = await fetch(url, { credentials: 'include' });

        if (!res.ok) throw new Error('Erro ao gerar relatório');

        const blob = await res.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `relatorio_estoque_${tipo}_${dataInicio}_${dataFim}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);

        Swal.fire({
            icon: 'success',
            title: 'PDF Gerado!',
            text: 'O arquivo foi baixado com sucesso',
            timer: 3000
        });
    } catch (error) {
        console.error('Erro:', error);
        Swal.fire('Erro', 'Não foi possível gerar o arquivo PDF', 'error');
    }
}


// ========== 4. FUNÇÃO PARA ATIVAR ALERTA DE ESTOQUE BAIXO NO DASHBOARD ==========

/**
 * Carrega alerta de estoque baixo no dashboard
 */
async function carregarAlertaEstoqueBaixo() {
    try {
        console.log('🔍 Verificando alertas de estoque...');

        const estoqueRes = await fetch('/api/estoque/alerta', {
            credentials: 'include'
        });
        const estoqueData = await estoqueRes.json();

        const alertaCard = document.getElementById('alertaEstoqueBaixo');
        const alertaBody = document.getElementById('estoqueBaixoBody');

        if (estoqueData.success && estoqueData.produtos && estoqueData.produtos.length > 0) {
            // Mostrar card de alerta
            if (alertaCard) {
                alertaCard.style.display = 'block';
                alertaCard.style.animation = 'fadeIn 0.5s ease';
            }

            // Renderizar produtos com estoque baixo
            const html = estoqueData.produtos.map(p => {
                const estoqueAtual = p.estoque || p.quantidade || 0;
                const estoqueMinimo = p.estoque_minimo || p.minimo || 0;
                const percentual = estoqueMinimo > 0 ? (estoqueAtual / estoqueMinimo * 100).toFixed(0) : 0;

                // Status badge com cores
                let statusBadge = '';
                let urgencia = '';

                if (estoqueAtual === 0) {
                    statusBadge = '<span class="badge danger pulse">🚫 ESGOTADO</span>';
                    urgencia = '🔴';
                } else if (estoqueAtual < estoqueMinimo) {
                    statusBadge = `<span class="badge danger">⚠️ CRÍTICO (${percentual}%)</span>`;
                    urgencia = '🟠';
                } else if (estoqueAtual < estoqueMinimo * 1.5) {
                    statusBadge = `<span class="badge warning">⚡ BAIXO (${percentual}%)</span>`;
                    urgencia = '🟡';
                }

                return `
                <tr style="background: ${estoqueAtual === 0 ? 'rgba(220, 38, 38, 0.15)' : 'rgba(234, 179, 8, 0.08)'};">
                    <td>${urgencia}</td>
                    <td><strong>${p.nome || 'Produto'}</strong></td>
                    <td>${p.marca || 'N/A'}</td>
                    <td style="color: ${estoqueAtual === 0 ? 'var(--danger)' : 'var(--warning)'}; font-weight: bold;">
                        ${estoqueAtual}
                    </td>
                    <td>${estoqueMinimo}</td>
                    <td>${statusBadge}</td>
                </tr>
                `;
            }).join('');

            if (alertaBody) {
                alertaBody.innerHTML = html;
            }

            // Notificação toast se houver produtos esgotados
            const produtosEsgotados = estoqueData.produtos.filter(p =>
                (p.estoque || p.quantidade || 0) === 0
            );

            if (produtosEsgotados.length > 0) {
                toast(`🚨 ATENÇÃO: ${produtosEsgotados.length} produto(s) ESGOTADO(S)!`, 'error');
            } else {
                console.log(`⚠️ ${estoqueData.produtos.length} produto(s) com estoque baixo`);
            }

            // Adicionar indicador visual no menu de estoque
            const menuEstoque = document.getElementById('menu-estoque');
            if (menuEstoque && !menuEstoque.querySelector('.badge-alert')) {
                const badge = document.createElement('span');
                badge.className = 'badge-alert';
                badge.style.cssText = `
                    position: absolute;
                    top: 5px;
                    right: 5px;
                    width: 10px;
                    height: 10px;
                    background: var(--danger);
                    border-radius: 50%;
                    animation: pulse 2s infinite;
                `;
                menuEstoque.style.position = 'relative';
                menuEstoque.appendChild(badge);
            }

        } else {
            // Esconder card se não houver alertas
            if (alertaCard) {
                alertaCard.style.display = 'none';
            }
            console.log('✅ Estoque OK - Nenhum produto abaixo do mínimo');

            // Remover indicador do menu se existir
            const badge = document.querySelector('#menu-estoque .badge-alert');
            if (badge) badge.remove();
        }
    } catch (error) {
        console.error('❌ Erro ao carregar alertas de estoque:', error);
        const alertaCard = document.getElementById('alertaEstoqueBaixo');
        if (alertaCard) alertaCard.style.display = 'none';
    }
}


// ========== 5. CALENDÁRIO DE PROFISSIONAIS COM CORES ==========

/**
 * Inicializa calendário de profissionais com cores
 */
async function initProfissionaisCalendar() {
    const calendarEl = document.getElementById('profissionaisCalendar');
    if (!calendarEl || !window.FullCalendar) {
        console.warn('⚠️ Elemento do calendário ou FullCalendar não encontrado');
        return;
    }

    try {
        console.log('📅 Inicializando calendário de profissionais...');

        // Buscar configurações do sistema (horário de funcionamento)
        const configRes = await fetch('/api/config', { credentials: 'include' });
        const configData = await configRes.json();

        const horarioInicio = configData.config?.horario_inicio || '07:00';
        const horarioFim = configData.config?.horario_fim || '21:00';

        // Buscar agendamentos
        const agendRes = await fetch('/api/agendamentos', { credentials: 'include' });
        const agendData = await agendRes.json();

        // Transformar agendamentos em eventos do calendário
        const eventos = [];

        if (agendData.success && agendData.agendamentos) {
            agendData.agendamentos.forEach(agend => {
                let backgroundColor = '#10B981'; // Verde padrão (disponível)
                let borderColor = '#059669';
                let textColor = '#FFFFFF';

                // Definir cores baseado no status
                if (agend.status === 'confirmado' || agend.status === 'ocupado') {
                    backgroundColor = '#EF4444'; // Vermelho (ocupado)
                    borderColor = '#DC2626';
                } else if (agend.status === 'pendente') {
                    backgroundColor = '#F59E0B'; // Amarelo (pendente)
                    borderColor = '#D97706';
                    textColor = '#000000';
                }

                eventos.push({
                    id: agend._id || agend.id,
                    title: `${agend.cliente_nome || 'Cliente'} - ${agend.servico_nome || 'Serviço'}`,
                    start: agend.data || agend.data_hora,
                    end: agend.data_fim || agend.data_hora,
                    backgroundColor: backgroundColor,
                    borderColor: borderColor,
                    textColor: textColor,
                    extendedProps: {
                        profissional: agend.profissional_nome || 'Profissional',
                        cliente: agend.cliente_nome || 'Cliente',
                        servico: agend.servico_nome || 'Serviço',
                        status: agend.status || 'pendente'
                    }
                });
            });
        }

        // Destruir calendário anterior se existir
        if (window.profissionaisCalendarInstance) {
            window.profissionaisCalendarInstance.destroy();
        }

        // Criar novo calendário
        window.profissionaisCalendarInstance = new FullCalendar.Calendar(calendarEl, {
            initialView: 'timeGridWeek',
            locale: 'pt-br',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            buttonText: {
                today: 'Hoje',
                month: 'Mês',
                week: 'Semana',
                day: 'Dia'
            },
            slotMinTime: horarioInicio,
            slotMaxTime: horarioFim,
            slotDuration: '00:30:00',
            slotLabelInterval: '01:00',
            allDaySlot: false,
            height: 700,
            expandRows: true,
            nowIndicator: true,
            editable: true,
            selectable: true,
            selectMirror: true,
            dayMaxEvents: 3,
            weekends: true,
            events: eventos,

            eventClick: function(info) {
                const event = info.event;
                Swal.fire({
                    title: event.title,
                    html: `
                        <div class="text-start">
                            <p><strong>Profissional:</strong> ${event.extendedProps.profissional}</p>
                            <p><strong>Cliente:</strong> ${event.extendedProps.cliente}</p>
                            <p><strong>Serviço:</strong> ${event.extendedProps.servico}</p>
                            <p><strong>Status:</strong> <span class="badge ${event.extendedProps.status === 'confirmado' ? 'danger' : event.extendedProps.status === 'pendente' ? 'warning' : 'success'}">${event.extendedProps.status}</span></p>
                            <p><strong>Horário:</strong> ${new Date(event.start).toLocaleString('pt-BR')}</p>
                        </div>
                    `,
                    showCancelButton: true,
                    confirmButtonText: 'Editar',
                    cancelButtonText: 'Fechar',
                    confirmButtonColor: '#7C3AED'
                }).then((result) => {
                    if (result.isConfirmed) {
                        // Abrir modal de edição
                        showModalAgendamento(event.id);
                    }
                });
            },

            select: function(info) {
                showModalAgendamento(null, {
                    data_hora: info.start,
                    data_fim: info.end
                });
            },

            eventDrop: function(info) {
                Swal.fire({
                    title: 'Reagendar?',
                    text: 'Deseja confirmar a mudança de horário?',
                    icon: 'question',
                    showCancelButton: true,
                    confirmButtonText: 'Sim, confirmar',
                    cancelButtonText: 'Cancelar'
                }).then((result) => {
                    if (result.isConfirmed) {
                        // Atualizar agendamento via API
                        atualizarAgendamento(info.event.id, {
                            data_hora: info.event.start,
                            data_fim: info.event.end
                        });
                    } else {
                        info.revert();
                    }
                });
            },

            eventResize: function(info) {
                Swal.fire({
                    title: 'Alterar duração?',
                    text: 'Deseja confirmar a alteração de duração?',
                    icon: 'question',
                    showCancelButton: true,
                    confirmButtonText: 'Sim, confirmar',
                    cancelButtonText: 'Cancelar'
                }).then((result) => {
                    if (result.isConfirmed) {
                        // Atualizar agendamento via API
                        atualizarAgendamento(info.event.id, {
                            data_hora: info.event.start,
                            data_fim: info.event.end
                        });
                    } else {
                        info.revert();
                    }
                });
            }
        });

        window.profissionaisCalendarInstance.render();
        console.log('✅ Calendário de profissionais inicializado com sucesso');

    } catch (error) {
        console.error('❌ Erro ao inicializar calendário de profissionais:', error);
        Swal.fire('Erro', 'Não foi possível carregar o calendário de profissionais', 'error');
    }
}

/**
 * Atualiza um agendamento via API
 */
async function atualizarAgendamento(id, dados) {
    try {
        const res = await fetch(`/api/agendamentos/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(dados)
        });

        const data = await res.json();

        if (data.success) {
            toast('✅ Agendamento atualizado com sucesso!', 'success');
            initProfissionaisCalendar(); // Recarregar calendário
        } else {
            toast(`❌ ${data.message || 'Erro ao atualizar agendamento'}`, 'error');
        }
    } catch (error) {
        console.error('Erro ao atualizar agendamento:', error);
        toast('❌ Falha ao atualizar agendamento', 'error');
    }
}


// ========== 6. CORREÇÕES PARA FINANCEIRO ==========

/**
 * Carrega gráficos do financeiro que estavam faltando
 */
async function carregarGraficosFinanceiro() {
    await Promise.all([
        carregarFaturamentoMensal(),
        carregarServicosMaisVendidos(),
        carregarProdutosMaisVendidos()
    ]);
}


// ========== 7. CORREÇÃO PARA AGENDAMENTOS - DADOS "DESCONHECIDO" ==========

/**
 * Função corrigida para carregar agendamentos do mês
 * Corrige problema de dados "desconhecido"
 */
async function carregarAgendamentosMes() {
    const tbody = document.getElementById('agendamentosMesBody');
    if (!tbody) return;

    try {
        console.log('📅 Carregando agendamentos do mês...');
        tbody.innerHTML = '<tr><td colspan="6" class="text-center"><div class="spinner"></div></td></tr>';

        const res = await fetch('/api/agendamentos/mes', { credentials: 'include' });
        const data = await res.json();

        if (data.success && data.agendamentos && data.agendamentos.length > 0) {
            tbody.innerHTML = data.agendamentos.map(agend => {
                // Garantir que os nomes não sejam undefined
                const clienteNome = agend.cliente_nome || agend.cliente?.nome || 'Cliente não identificado';
                const profissionalNome = agend.profissional_nome || agend.profissional?.nome || 'Profissional não identificado';
                const servicoNome = agend.servico_nome || agend.servico?.nome || 'Serviço não identificado';
                const dataFormatada = agend.data_formatada || formatarDataHora(agend.data || agend.data_hora);
                const status = agend.status || 'pendente';

                const statusClass = status === 'confirmado' ? 'success' :
                                  status === 'cancelado' ? 'danger' :
                                  status === 'concluido' || status === 'concluído' ? 'info' : 'warning';

                const statusText = status.charAt(0).toUpperCase() + status.slice(1);

                return `
                    <tr>
                        <td>${dataFormatada}</td>
                        <td><strong>${clienteNome}</strong></td>
                        <td>${profissionalNome}</td>
                        <td>${servicoNome}</td>
                        <td><span class="badge ${statusClass}">${statusText}</span></td>
                        <td>
                            <button class="btn btn-sm btn-danger" onclick="deleteAgendamento('${agend._id || agend.id}')" title="Cancelar">
                                <i class="bi bi-x-circle"></i>
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');

            console.log(`✅ ${data.agendamentos.length} agendamentos do mês carregados`);
        } else {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted">
                        <i class="bi bi-calendar-x" style="font-size: 2rem; opacity: 0.3;"></i>
                        <p style="margin-top: 10px;">Nenhum agendamento para este mês</p>
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('❌ Erro ao carregar agendamentos do mês:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-danger">
                    <i class="bi bi-exclamation-triangle"></i> Erro ao carregar agendamentos
                </td>
            </tr>
        `;
    }
}


// ========== FIM DAS CORREÇÕES ==========

console.log('✅ Arquivo de correções completas carregado - BIOMA v4.0');
