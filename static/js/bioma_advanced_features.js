/**
 * BIOMA SYSTEM - Advanced Features
 * Funcionalidades avançadas: Impressão, WhatsApp, Perfis, Notificações, Anamnese
 * Versão: 2.0
 */

console.log('🚀 BIOMA Advanced Features carregado!');

// ==================== SISTEMA DE IMPRESSÃO ====================

/**
 * Imprime orçamento com layout formatado
 */
function imprimirOrcamento(orcamentoId) {
    console.log(`🖨️ Imprimindo orçamento ${orcamentoId}...`);

    fetch(`/api/orcamento/${orcamentoId}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                abrirJanelaImpressao(data.orcamento, 'orcamento');
            } else {
                mostrarErro('Erro ao carregar orçamento para impressão');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            mostrarErro('Erro ao imprimir orçamento');
        });
}

/**
 * Imprime contrato com layout formatado
 */
function imprimirContrato(contratoId) {
    console.log(`🖨️ Imprimindo contrato ${contratoId}...`);

    fetch(`/api/contrato/${contratoId}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                abrirJanelaImpressao(data.contrato, 'contrato');
            } else {
                mostrarErro('Erro ao carregar contrato para impressão');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            mostrarErro('Erro ao imprimir contrato');
        });
}

/**
 * Abre janela de impressão formatada
 */
function abrirJanelaImpressao(dados, tipo) {
    const janela = window.open('', '_blank', 'width=800,height=600');

    const logoUrl = '/static/img/logo.png'; // Ajustar conforme necessário

    let html = `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>${tipo === 'orcamento' ? 'Orçamento' : 'Contrato'} #${dados.numero || dados._id}</title>
            <style>
                @page { margin: 20mm; }
                body {
                    font-family: Arial, sans-serif;
                    padding: 20px;
                    color: #333;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 3px solid #7C3AED;
                    padding-bottom: 20px;
                }
                .logo {
                    max-width: 200px;
                    max-height: 80px;
                    margin-bottom: 10px;
                }
                .title {
                    color: #7C3AED;
                    font-size: 28px;
                    font-weight: bold;
                    margin: 10px 0;
                }
                .info-section {
                    margin: 20px 0;
                    padding: 15px;
                    background: #f9f9f9;
                    border-radius: 8px;
                }
                .info-row {
                    display: flex;
                    justify-content: space-between;
                    margin: 10px 0;
                }
                .info-label {
                    font-weight: bold;
                    color: #666;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }
                th, td {
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }
                th {
                    background: #7C3AED;
                    color: white;
                    font-weight: bold;
                }
                .total {
                    font-size: 24px;
                    font-weight: bold;
                    text-align: right;
                    margin-top: 20px;
                    color: #7C3AED;
                    padding: 15px;
                    background: #f0f0f0;
                    border-radius: 8px;
                }
                .footer {
                    margin-top: 50px;
                    padding-top: 20px;
                    border-top: 2px solid #ddd;
                    text-align: center;
                    color: #666;
                }
                .assinatura {
                    margin-top: 50px;
                    display: flex;
                    justify-content: space-around;
                }
                .assinatura-campo {
                    text-align: center;
                    width: 40%;
                }
                .assinatura-linha {
                    border-bottom: 1px solid #333;
                    margin-bottom: 5px;
                    height: 40px;
                }
                @media print {
                    .no-print { display: none; }
                    body { margin: 0; }
                }
            </style>
        </head>
        <body>
            <div class="header">
                <img src="${logoUrl}" class="logo" alt="BIOMA">
                <div class="title">BIOMA UBERABA</div>
                <div>${tipo === 'orcamento' ? 'ORÇAMENTO' : 'CONTRATO DE SERVIÇO'}</div>
                <div>Nº ${dados.numero || dados._id}</div>
            </div>

            <div class="info-section">
                <h3>DADOS DO CLIENTE</h3>
                <div class="info-row">
                    <div><span class="info-label">Nome:</span> ${dados.cliente_nome || 'N/A'}</div>
                    <div><span class="info-label">CPF/CNPJ:</span> ${dados.cliente_cpf || 'N/A'}</div>
                </div>
                <div class="info-row">
                    <div><span class="info-label">Telefone:</span> ${dados.cliente_telefone || 'N/A'}</div>
                    <div><span class="info-label">E-mail:</span> ${dados.cliente_email || 'N/A'}</div>
                </div>
                <div class="info-row">
                    <div><span class="info-label">Endereço:</span> ${dados.cliente_endereco || 'N/A'}</div>
                </div>
            </div>

            <div class="info-section">
                <h3>INFORMAÇÕES DO ${tipo === 'orcamento' ? 'ORÇAMENTO' : 'CONTRATO'}</h3>
                <div class="info-row">
                    <div><span class="info-label">Data:</span> ${new Date(dados.data || Date.now()).toLocaleDateString('pt-BR')}</div>
                    <div><span class="info-label">Validade:</span> ${dados.validade || '30 dias'}</div>
                </div>
                <div class="info-row">
                    <div><span class="info-label">Forma de Pagamento:</span> ${dados.forma_pagamento || 'A definir'}</div>
                    <div><span class="info-label">Status:</span> ${dados.status || 'Pendente'}</div>
                </div>
            </div>
    `;

    // Adicionar tabela de serviços
    if (dados.servicos && dados.servicos.length > 0) {
        html += `
            <h3>SERVIÇOS</h3>
            <table>
                <thead>
                    <tr>
                        <th>Descrição</th>
                        <th>Qtd</th>
                        <th>Valor Unit.</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
        `;

        dados.servicos.forEach(servico => {
            const total = (servico.quantidade || 1) * (servico.preco || 0);
            html += `
                <tr>
                    <td>${servico.nome || servico.descricao}</td>
                    <td>${servico.quantidade || 1}</td>
                    <td>R$ ${(servico.preco || 0).toFixed(2)}</td>
                    <td>R$ ${total.toFixed(2)}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
    }

    // Adicionar tabela de produtos
    if (dados.produtos && dados.produtos.length > 0) {
        html += `
            <h3>PRODUTOS</h3>
            <table>
                <thead>
                    <tr>
                        <th>Descrição</th>
                        <th>Qtd</th>
                        <th>Valor Unit.</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
        `;

        dados.produtos.forEach(produto => {
            const total = (produto.quantidade || 1) * (produto.preco || 0);
            html += `
                <tr>
                    <td>${produto.nome || produto.descricao}</td>
                    <td>${produto.quantidade || 1}</td>
                    <td>R$ ${(produto.preco || 0).toFixed(2)}</td>
                    <td>R$ ${total.toFixed(2)}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
    }

    // Total
    html += `
        <div class="total">
            VALOR TOTAL: R$ ${(dados.valor_total || 0).toFixed(2)}
        </div>
    `;

    // Observações
    if (dados.observacoes) {
        html += `
            <div class="info-section">
                <h3>OBSERVAÇÕES</h3>
                <p>${dados.observacoes}</p>
            </div>
        `;
    }

    // Assinaturas para contrato
    if (tipo === 'contrato') {
        html += `
            <div class="assinatura">
                <div class="assinatura-campo">
                    <div class="assinatura-linha"></div>
                    <div>Cliente</div>
                    <div>${dados.cliente_nome || ''}</div>
                </div>
                <div class="assinatura-campo">
                    <div class="assinatura-linha"></div>
                    <div>BIOMA Uberaba</div>
                    <div>Responsável</div>
                </div>
            </div>
        `;
    }

    // Footer
    html += `
            <div class="footer">
                <p>BIOMA Uberaba - Av. Santos Dumont 3110 - Santa Maria - Uberaba/MG</p>
                <p>Tel: (34) 99235-5890 - E-mail: biomauberaba@gmail.com</p>
            </div>

            <div class="no-print" style="text-align: center; margin-top: 30px;">
                <button onclick="window.print()" style="padding: 12px 24px; font-size: 16px; cursor: pointer; background: #7C3AED; color: white; border: none; border-radius: 8px; margin: 0 10px;">
                    🖨️ Imprimir
                </button>
                <button onclick="window.close()" style="padding: 12px 24px; font-size: 16px; cursor: pointer; background: #6B7280; color: white; border: none; border-radius: 8px; margin: 0 10px;">
                    Fechar
                </button>
            </div>
        </body>
        </html>
    `;

    janela.document.write(html);
    janela.document.close();
}

// ==================== SISTEMA DE WHATSAPP ====================

/**
 * Envia orçamento via WhatsApp
 */
function enviarWhatsAppOrcamento(orcamentoId) {
    console.log(`📱 Enviando orçamento ${orcamentoId} via WhatsApp...`);

    fetch(`/api/orcamento/${orcamentoId}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const orcamento = data.orcamento;
                const telefone = orcamento.cliente_telefone?.replace(/\D/g, '');

                if (!telefone) {
                    mostrarErro('Cliente sem telefone cadastrado');
                    return;
                }

                const mensagem = montarMensagemWhatsApp(orcamento, 'orcamento');
                const link = `https://wa.me/55${telefone}?text=${encodeURIComponent(mensagem)}`;

                window.open(link, '_blank');
                mostrarSucesso('Abrindo WhatsApp...');
            } else {
                mostrarErro('Erro ao carregar orçamento');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            mostrarErro('Erro ao enviar via WhatsApp');
        });
}

/**
 * Envia contrato via WhatsApp
 */
function enviarWhatsAppContrato(contratoId) {
    console.log(`📱 Enviando contrato ${contratoId} via WhatsApp...`);

    fetch(`/api/contrato/${contratoId}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const contrato = data.contrato;
                const telefone = contrato.cliente_telefone?.replace(/\D/g, '');

                if (!telefone) {
                    mostrarErro('Cliente sem telefone cadastrado');
                    return;
                }

                const mensagem = montarMensagemWhatsApp(contrato, 'contrato');
                const link = `https://wa.me/55${telefone}?text=${encodeURIComponent(mensagem)}`;

                window.open(link, '_blank');
                mostrarSucesso('Abrindo WhatsApp...');
            } else {
                mostrarErro('Erro ao carregar contrato');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            mostrarErro('Erro ao enviar via WhatsApp');
        });
}

/**
 * Monta mensagem formatada para WhatsApp
 */
function montarMensagemWhatsApp(dados, tipo) {
    let mensagem = `🌳 *BIOMA UBERABA*\n\n`;
    mensagem += `📋 *${tipo === 'orcamento' ? 'ORÇAMENTO' : 'CONTRATO'}* Nº ${dados.numero || dados._id}\n`;
    mensagem += `📅 Data: ${new Date(dados.data || Date.now()).toLocaleDateString('pt-BR')}\n\n`;

    mensagem += `👤 *Cliente:* ${dados.cliente_nome}\n\n`;

    if (dados.servicos && dados.servicos.length > 0) {
        mensagem += `✂️ *SERVIÇOS:*\n`;
        dados.servicos.forEach(servico => {
            mensagem += `• ${servico.nome}: R$ ${(servico.preco || 0).toFixed(2)}\n`;
        });
        mensagem += `\n`;
    }

    if (dados.produtos && dados.produtos.length > 0) {
        mensagem += `📦 *PRODUTOS:*\n`;
        dados.produtos.forEach(produto => {
            mensagem += `• ${produto.nome}: R$ ${(produto.preco || 0).toFixed(2)}\n`;
        });
        mensagem += `\n`;
    }

    mensagem += `💰 *VALOR TOTAL: R$ ${(dados.valor_total || 0).toFixed(2)}*\n\n`;

    if (dados.observacoes) {
        mensagem += `📝 *Observações:* ${dados.observacoes}\n\n`;
    }

    mensagem += `📞 Para mais informações:\n`;
    mensagem += `Tel: (34) 99235-5890\n`;
    mensagem += `📍 Av. Santos Dumont 3110 - Uberaba/MG`;

    return mensagem;
}

// ==================== SISTEMA DE PERFIS DE ACESSO ====================

/**
 * Define perfis de acesso
 */
const PERFIS_ACESSO = {
    ADMIN: {
        nome: 'Administrador',
        permissoes: ['*'], // Acesso total
        menus: ['*']
    },
    GESTAO: {
        nome: 'Gestão',
        permissoes: [
            'visualizar_relatorios',
            'gerenciar_orcamentos',
            'gerenciar_clientes',
            'gerenciar_profissionais',
            'visualizar_financeiro',
            'visualizar_auditoria'
        ],
        menus: [
            'dashboard',
            'orcamento',
            'consultar',
            'contratos',
            'relatorios',
            'clientes',
            'profissionais',
            'financeiro',
            'auditoria'
        ]
    },
    PROFISSIONAL: {
        nome: 'Profissional',
        permissoes: [
            'visualizar_proprios_agendamentos',
            'visualizar_proprias_comissoes',
            'visualizar_fila',
            'atualizar_perfil'
        ],
        menus: [
            'dashboard',
            'agendamentos',
            'fila',
            'perfil',
            'comissoes'
        ]
    }
};

/**
 * Verifica permissão do usuário
 */
function verificarPermissao(permissao) {
    if (!window.currentUser) return false;

    const perfil = window.currentUser.perfil || 'PROFISSIONAL';
    const perfilConfig = PERFIS_ACESSO[perfil];

    if (!perfilConfig) return false;

    // Admin tem acesso total
    if (perfilConfig.permissoes.includes('*')) return true;

    return perfilConfig.permissoes.includes(permissao);
}

/**
 * Configura menus baseado no perfil
 */
function configurarMenusPorPerfil() {
    if (!window.currentUser) return;

    const perfil = window.currentUser.perfil || 'PROFISSIONAL';
    const perfilConfig = PERFIS_ACESSO[perfil];

    if (!perfilConfig) return;

    // Se não tem acesso total, esconde menus não permitidos
    if (!perfilConfig.menus.includes('*')) {
        document.querySelectorAll('.sidebar-menu li a').forEach(menu => {
            const menuId = menu.id?.replace('menu-', '');
            if (menuId && !perfilConfig.menus.includes(menuId)) {
                menu.parentElement.style.display = 'none';
            }
        });
    }
}

// ==================== SISTEMA DE NOTIFICAÇÕES INTELIGENTES ====================

/**
 * Sistema de notificação para fila
 */
class SistemaNotificacaoFila {
    constructor() {
        this.clientesNotificados = new Set();
    }

    /**
     * Notifica cliente sobre posição na fila
     */
    async notificarPosicaoFila(clienteId, posicao, tempoEstimado) {
        const mensagem = this.gerarMensagemFila(posicao, tempoEstimado);

        try {
            // Enviar notificação via API
            const response = await fetch('/api/fila/notificar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    cliente_id: clienteId,
                    tipo: 'posicao_fila',
                    mensagem: mensagem
                })
            });

            const data = await response.json();

            if (data.success) {
                this.clientesNotificados.add(clienteId);
                mostrarSucesso('Cliente notificado com sucesso!');

                // Atualizar interface
                this.atualizarStatusNotificacao(clienteId, 'notificado');
            }
        } catch (error) {
            console.error('Erro ao notificar cliente:', error);
            mostrarErro('Erro ao enviar notificação');
        }
    }

    /**
     * Gera mensagem personalizada para fila
     */
    gerarMensagemFila(posicao, tempoEstimado) {
        let mensagem = `Olá! Equipe BIOMA informa:\n`;

        if (posicao === 1) {
            mensagem += `🎉 Você é o próximo! Seu atendimento será iniciado em breve.`;
        } else if (posicao <= 3) {
            mensagem += `📍 Você está na posição ${posicao} da fila.\n`;
            mensagem += `⏰ Tempo estimado: ${tempoEstimado} minutos.`;
        } else {
            mensagem += `📍 Você está na posição ${posicao} da fila.\n`;
            mensagem += `⏰ Tempo estimado: ${tempoEstimado} minutos.\n`;
            mensagem += `Avisaremos quando estiver próximo!`;
        }

        return mensagem;
    }

    /**
     * Notifica confirmação de agendamento
     */
    async notificarConfirmacaoAgendamento(agendamentoId) {
        try {
            const response = await fetch(`/api/agendamento/${agendamentoId}`);
            const data = await response.json();

            if (data.success) {
                const agendamento = data.agendamento;
                const mensagem = `Olá ${agendamento.cliente_nome}, equipe BIOMA passa para confirmar seu atendimento que será iniciado às ${agendamento.hora} do dia ${new Date(agendamento.data).toLocaleDateString('pt-BR')}.`;

                // Enviar notificação
                await this.enviarNotificacao(agendamento.cliente_id, mensagem, 'confirmacao_agendamento');
            }
        } catch (error) {
            console.error('Erro ao notificar confirmação:', error);
        }
    }

    /**
     * Envia notificação genérica
     */
    async enviarNotificacao(clienteId, mensagem, tipo) {
        const response = await fetch('/api/notificacao/enviar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                cliente_id: clienteId,
                mensagem: mensagem,
                tipo: tipo,
                canais: ['sms', 'email', 'whatsapp']
            })
        });

        return response.json();
    }

    /**
     * Atualiza status de notificação na interface
     */
    atualizarStatusNotificacao(clienteId, status) {
        const elemento = document.querySelector(`[data-cliente-id="${clienteId}"] .status-notificacao`);
        if (elemento) {
            elemento.textContent = status;
            elemento.className = `status-notificacao badge ${status === 'notificado' ? 'success' : 'warning'}`;
        }
    }
}

// Instanciar sistema de notificações
const sistemaNotificacao = new SistemaNotificacaoFila();

// ==================== SISTEMA DE ANAMNESE E PRONTUÁRIO ====================

/**
 * Sistema de anamnese e prontuário
 */
class SistemaProntuario {
    /**
     * Cria nova anamnese
     */
    async criarAnamnese(clienteId, dados) {
        try {
            const response = await fetch('/api/anamnese', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    cliente_id: clienteId,
                    ...dados,
                    data: new Date().toISOString()
                })
            });

            const data = await response.json();

            if (data.success) {
                mostrarSucesso('Anamnese salva com sucesso!');
                return data.anamnese;
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Erro ao criar anamnese:', error);
            mostrarErro('Erro ao salvar anamnese');
            return null;
        }
    }

    /**
     * Carrega histórico de anamnese
     */
    async carregarHistoricoAnamnese(clienteId) {
        try {
            const response = await fetch(`/api/cliente/${clienteId}/anamneses`);
            const data = await response.json();

            if (data.success) {
                return data.anamneses;
            }
            return [];
        } catch (error) {
            console.error('Erro ao carregar histórico:', error);
            return [];
        }
    }

    /**
     * Imprime prontuário
     */
    imprimirProntuario(clienteId) {
        fetch(`/api/cliente/${clienteId}/prontuario`)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    this.abrirJanelaImpressaoProntuario(data.prontuario);
                }
            })
            .catch(error => {
                console.error('Erro:', error);
                mostrarErro('Erro ao imprimir prontuário');
            });
    }

    /**
     * Abre janela de impressão do prontuário
     */
    abrirJanelaImpressaoProntuario(prontuario) {
        const janela = window.open('', '_blank', 'width=800,height=600');

        let html = `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Prontuário - ${prontuario.cliente_nome}</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; }
                    .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #7C3AED; }
                    .section { margin: 20px 0; padding: 15px; background: #f9f9f9; }
                    h2 { color: #7C3AED; }
                    .info-row { margin: 10px 0; }
                    .label { font-weight: bold; }
                    @media print { .no-print { display: none; } }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>BIOMA UBERABA</h1>
                    <h2>PRONTUÁRIO DO CLIENTE</h2>
                    <p>Data de Impressão: ${new Date().toLocaleDateString('pt-BR')}</p>
                </div>

                <div class="section">
                    <h3>DADOS PESSOAIS</h3>
                    <div class="info-row"><span class="label">Nome:</span> ${prontuario.cliente_nome}</div>
                    <div class="info-row"><span class="label">CPF:</span> ${prontuario.cliente_cpf}</div>
                    <div class="info-row"><span class="label">Telefone:</span> ${prontuario.cliente_telefone}</div>
                    <div class="info-row"><span class="label">E-mail:</span> ${prontuario.cliente_email}</div>
                    <div class="info-row"><span class="label">Data de Nascimento:</span> ${prontuario.data_nascimento || 'N/A'}</div>
                </div>

                <div class="section">
                    <h3>HISTÓRICO DE ANAMNESES</h3>
                    ${prontuario.anamneses?.map(anamnese => `
                        <div style="border: 1px solid #ddd; padding: 10px; margin: 10px 0;">
                            <div class="info-row"><span class="label">Data:</span> ${new Date(anamnese.data).toLocaleDateString('pt-BR')}</div>
                            <div class="info-row"><span class="label">Queixa Principal:</span> ${anamnese.queixa_principal || 'N/A'}</div>
                            <div class="info-row"><span class="label">Observações:</span> ${anamnese.observacoes || 'N/A'}</div>
                        </div>
                    `).join('') || '<p>Nenhuma anamnese registrada</p>'}
                </div>

                <div class="section">
                    <h3>HISTÓRICO DE ATENDIMENTOS</h3>
                    ${prontuario.atendimentos?.map(atend => `
                        <div style="border: 1px solid #ddd; padding: 10px; margin: 10px 0;">
                            <div class="info-row"><span class="label">Data:</span> ${new Date(atend.data).toLocaleDateString('pt-BR')}</div>
                            <div class="info-row"><span class="label">Serviço:</span> ${atend.servico_nome}</div>
                            <div class="info-row"><span class="label">Profissional:</span> ${atend.profissional_nome}</div>
                            <div class="info-row"><span class="label">Observações:</span> ${atend.observacoes || 'N/A'}</div>
                        </div>
                    `).join('') || '<p>Nenhum atendimento registrado</p>'}
                </div>

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

    /**
     * Envia prontuário via email
     */
    async enviarProntuarioEmail(clienteId) {
        try {
            const response = await fetch(`/api/cliente/${clienteId}/prontuario/enviar-email`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                mostrarSucesso('Prontuário enviado por e-mail!');
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Erro:', error);
            mostrarErro('Erro ao enviar prontuário');
        }
    }

    /**
     * Envia prontuário via WhatsApp
     */
    enviarProntuarioWhatsApp(clienteId) {
        fetch(`/api/cliente/${clienteId}/prontuario`)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const prontuario = data.prontuario;
                    const telefone = prontuario.cliente_telefone?.replace(/\D/g, '');

                    if (!telefone) {
                        mostrarErro('Cliente sem telefone cadastrado');
                        return;
                    }

                    let mensagem = `📋 *PRONTUÁRIO - BIOMA UBERABA*\n\n`;
                    mensagem += `👤 *Cliente:* ${prontuario.cliente_nome}\n`;
                    mensagem += `📅 *Data:* ${new Date().toLocaleDateString('pt-BR')}\n\n`;

                    if (prontuario.ultima_anamnese) {
                        mensagem += `📝 *Última Anamnese:*\n`;
                        mensagem += `Data: ${new Date(prontuario.ultima_anamnese.data).toLocaleDateString('pt-BR')}\n`;
                        mensagem += `${prontuario.ultima_anamnese.observacoes || 'Sem observações'}\n\n`;
                    }

                    mensagem += `Para mais informações, entre em contato conosco!`;

                    const link = `https://wa.me/55${telefone}?text=${encodeURIComponent(mensagem)}`;
                    window.open(link, '_blank');
                    mostrarSucesso('Abrindo WhatsApp...');
                }
            })
            .catch(error => {
                console.error('Erro:', error);
                mostrarErro('Erro ao enviar via WhatsApp');
            });
    }
}

// Instanciar sistema de prontuário
const sistemaProntuario = new SistemaProntuario();

// ==================== UPLOAD DE FOTO DE PROFISSIONAL ====================

/**
 * Upload de foto de profissional
 */
async function uploadFotoProfissional(profissionalId) {
    const fileInput = document.getElementById(`fotoProfissionalInput-${profissionalId}`);
    if (!fileInput || !fileInput.files[0]) {
        mostrarErro('Selecione uma imagem');
        return;
    }

    try {
        console.log(`📸 Fazendo upload de foto do profissional ${profissionalId}...`);

        const formData = new FormData();
        formData.append('foto', fileInput.files[0]);

        const response = await fetch(`/api/profissional/${profissionalId}/foto`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            mostrarSucesso('Foto atualizada com sucesso!');

            // Atualizar preview da foto
            const preview = document.getElementById(`fotoProfissionalPreview-${profissionalId}`);
            if (preview) {
                preview.src = data.foto_url;
            }

            // Atualizar foto na lista
            atualizarFotoProfissionalLista(profissionalId, data.foto_url);
        } else {
            throw new Error(data.message || 'Erro ao fazer upload');
        }
    } catch (error) {
        console.error('❌ Erro ao fazer upload da foto:', error);
        mostrarErro('Erro ao fazer upload da foto: ' + error.message);
    }
}

/**
 * Atualiza foto do profissional na lista
 */
function atualizarFotoProfissionalLista(profissionalId, fotoUrl) {
    const elementos = document.querySelectorAll(`[data-profissional-id="${profissionalId}"] .foto-profissional`);
    elementos.forEach(el => {
        el.src = fotoUrl;
        el.style.display = 'inline-block';
    });
}

// ==================== MELHORIAS VISUAIS E CORREÇÕES ====================

/**
 * Corrige ícone do Financeiro para cifrão
 */
function corrigirIconeFinanceiro() {
    const menuFinanceiro = document.getElementById('menu-financeiro');
    if (menuFinanceiro) {
        const icon = menuFinanceiro.querySelector('i');
        if (icon) {
            icon.className = 'bi bi-currency-dollar';
        }
    }
}

/**
 * Adiciona botões de ação em modais de visualização
 */
function adicionarBotoesAcaoModal(tipo, id) {
    const modalFooter = document.querySelector('.modal-footer');
    if (!modalFooter) return;

    // Adicionar botões de impressão e WhatsApp
    const botoesHTML = `
        <button class="btn btn-primary" onclick="imprimir${tipo}('${id}')">
            <i class="bi bi-printer"></i> Imprimir
        </button>
        <button class="btn btn-success" onclick="enviarWhatsApp${tipo}('${id}')">
            <i class="bi bi-whatsapp"></i> WhatsApp
        </button>
    `;

    // Inserir antes do botão fechar
    const btnFechar = modalFooter.querySelector('.btn-secondary');
    if (btnFechar) {
        btnFechar.insertAdjacentHTML('beforebegin', botoesHTML);
    }
}

// ==================== INICIALIZAÇÃO ====================

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ BIOMA Advanced Features inicializado!');

    // Configurar perfis de acesso
    configurarMenusPorPerfil();

    // Corrigir ícone do Financeiro
    corrigirIconeFinanceiro();

    // Inicializar tooltips se Bootstrap estiver disponível
    if (typeof bootstrap !== 'undefined') {
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(el => new bootstrap.Tooltip(el));
    }
});

// Exportar funções para uso global
window.imprimirOrcamento = imprimirOrcamento;
window.imprimirContrato = imprimirContrato;
window.enviarWhatsAppOrcamento = enviarWhatsAppOrcamento;
window.enviarWhatsAppContrato = enviarWhatsAppContrato;
window.verificarPermissao = verificarPermissao;
window.sistemaNotificacao = sistemaNotificacao;
window.sistemaProntuario = sistemaProntuario;
window.uploadFotoProfissional = uploadFotoProfissional;

console.log('✅ BIOMA Advanced Features carregado com sucesso!');