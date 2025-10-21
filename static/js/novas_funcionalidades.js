// ==================== NOVAS FUNCIONALIDADES - BIOMA UBERABA v3.7 ====================
// Desenvolvedor: Juan Marco (@juanmarco1999)
// Data: 2025-10-21

// ==================== UPLOAD DE LOGO DA EMPRESA ====================

function uploadLogo() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('logo', file);

        try {
            const response = await fetch('/api/upload/logo', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            if (data.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Logo Atualizado!',
                    text: 'O logo da empresa foi atualizado com sucesso.'
                });
                carregarLogo();
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: error.message || 'Erro ao fazer upload do logo'
            });
        }
    };
    input.click();
}

async function carregarLogo() {
    try {
        const response = await fetch('/api/config/logo');
        const data = await response.json();
        
        if (data.success && data.logo) {
            // Atualizar logo no sidebar
            const sidebarLogo = document.querySelector('.sidebar-logo');
            if (sidebarLogo) {
                sidebarLogo.innerHTML = `<img src="${data.logo}" alt="Logo" style="max-width: 100%; max-height: 80px; object-fit: contain;">`;
            }
            
            // Atualizar logo na tela de login
            const authLogo = document.getElementById('authLogoCustom');
            if (authLogo) {
                authLogo.src = data.logo;
                authLogo.style.display = 'block';
                document.querySelector('.logo-icon').style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Erro ao carregar logo:', error);
    }
}

// ==================== FOTO DE PERFIL DO PROFISSIONAL ====================

async function uploadFotoProfissional(profissionalId) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('foto', file);
        formData.append('profissional_id', profissionalId);

        try {
            const response = await fetch('/api/upload/foto-profissional', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            if (data.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Foto Atualizada!',
                    text: 'A foto do profissional foi atualizada com sucesso.'
                });
                loadProfissionais();
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: error.message || 'Erro ao fazer upload da foto'
            });
        }
    };
    input.click();
}

function exibirFotoProfissional(foto) {
    if (foto) {
        return `<img src="/uploads/${foto}" alt="Foto" class="foto-profissional" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; margin-right: 10px; vertical-align: middle;">`;
    }
    return `<div class="foto-profissional-placeholder" style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #7C3AED, #EC4899); display: inline-block; margin-right: 10px; vertical-align: middle;"></div>`;
}

// ==================== SISTEMA DE MULTICOMISSÕES ====================

async function calcularComissoesOrcamento() {
    const { value: orcamentoId } = await Swal.fire({
        title: 'Calcular Comissões',
        html: '<div id="swal-orcamentos-list"><div class="spinner"></div></div>',
        showCancelButton: true,
        confirmButtonText: 'Calcular',
        cancelButtonText: 'Cancelar',
        didOpen: () => {
            carregarOrcamentosParaComissao();
        },
        preConfirm: () => {
            return document.getElementById('select-orcamento')?.value;
        }
    });

    if (!orcamentoId) return;

    try {
        const response = await fetch('/api/comissoes/calcular-orcamento', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ orcamento_id: orcamentoId })
        });
        const data = await response.json();
        
        if (data.success) {
            mostrarResultadoComissoes(data);
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        Swal.fire({
            icon: 'error',
            title: 'Erro',
            text: error.message || 'Erro ao calcular comissões'
        });
    }
}

async function carregarOrcamentosParaComissao() {
    try {
        const response = await fetch('/api/orcamentos?status=Aprovado');
        const data = await response.json();
        
        const container = document.getElementById('swal-orcamentos-list');
        if (data.success && data.orcamentos.length > 0) {
            container.innerHTML = `
                <label>Selecione o Orçamento:</label>
                <select id="select-orcamento" class="form-select">
                    <option value="">Escolha um orçamento...</option>
                    ${data.orcamentos.map(orc => `
                        <option value="${orc._id}">
                            #${orc.numero} - ${orc.cliente_nome} - R$ ${orc.total.toFixed(2)}
                        </option>
                    `).join('')}
                </select>
            `;
        } else {
            container.innerHTML = '<p class="text-muted">Nenhum orçamento aprovado encontrado</p>';
        }
    } catch (error) {
        console.error('Erro ao carregar orçamentos:', error);
    }
}

function mostrarResultadoComissoes(data) {
    let html = `
        <div class="comissoes-resultado">
            <h4>Orçamento #${data.orcamento.numero}</h4>
            <p><strong>Valor Total:</strong> R$ ${data.orcamento.valor_total.toFixed(2)}</p>
            <hr>
            <h5>Comissões Calculadas:</h5>
    `;
    
    data.comissoes.forEach(com => {
        const fotoPerfil = com.foto ? `<img src="/uploads/${com.foto}" style="width: 30px; height: 30px; border-radius: 50%; margin-right: 10px;">` : '';
        html += `
            <div class="comissao-item" style="padding: 15px; background: var(--bg-card); border-radius: 12px; margin-bottom: 10px; border-left: 4px solid ${com.tipo === 'profissional' ? '#7C3AED' : '#EC4899'};">
                <div style="display: flex; align-items: center;">
                    ${fotoPerfil}
                    <div style="flex: 1;">
                        <strong>${com.nome}</strong> - <span class="badge ${com.tipo === 'profissional' ? 'success' : 'warning'}">${com.tipo.toUpperCase()}</span>
                        <br>
                        <small>${com.servico}</small>
                        ${com.profissional_referencia ? `<br><small>Ref: ${com.profissional_referencia}</small>` : ''}
                    </div>
                    <div style="text-align: right;">
                        <strong style="font-size: 1.2rem; color: var(--success);">R$ ${com.valor_comissao.toFixed(2)}</strong>
                        <br>
                        <small>${com.percentual}% de R$ ${com.valor_base.toFixed(2)}</small>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += `
            <hr>
            <div style="text-align: right; font-size: 1.3rem; font-weight: bold; color: var(--primary);">
                Total Comissões: R$ ${data.total_comissoes.toFixed(2)}
            </div>
        </div>
    `;
    
    Swal.fire({
        title: 'Resultado do Cálculo',
        html: html,
        width: '800px',
        confirmButtonText: 'Fechar'
    });
}

async function carregarHistoricoComissoes() {
    try {
        const response = await fetch('/api/comissoes/historico');
        const data = await response.json();
        
        const tbody = document.getElementById('historicoComissoesBody');
        if (!tbody) return;
        
        if (data.success && data.historico.length > 0) {
            tbody.innerHTML = data.historico.map(hist => `
                <tr>
                    <td>${new Date(hist.calculado_em).toLocaleDateString('pt-BR')}</td>
                    <td>#${hist.numero_orcamento}</td>
                    <td>R$ ${hist.valor_total.toFixed(2)}</td>
                    <td>${hist.comissoes.length} comissões</td>
                    <td>${hist.calculado_por}</td>
                    <td>
                        <button class="btn btn-sm btn-outline" onclick="verDetalhesComissao('${hist._id}')">
                            <i class="bi bi-eye"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Nenhum histórico encontrado</td></tr>';
        }
    } catch (error) {
        console.error('Erro ao carregar histórico:', error);
    }
}

// ==================== ASSISTENTES INDEPENDENTES ====================

async function cadastrarAssistenteIndependente() {
    const { value: formValues } = await Swal.fire({
        title: 'Cadastrar Assistente',
        html: `
            <div style="text-align: left;">
                <div class="mb-3">
                    <label>Nome Completo *</label>
                    <input id="ass-nome" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label>CPF</label>
                    <input id="ass-cpf" class="form-control" maxlength="14">
                </div>
                <div class="mb-3">
                    <label>Telefone</label>
                    <input id="ass-telefone" class="form-control">
                </div>
                <div class="mb-3">
                    <label>E-mail</label>
                    <input id="ass-email" type="email" class="form-control">
                </div>
                <div class="mb-3">
                    <label>Comissão (%) *</label>
                    <input id="ass-comissao" type="number" class="form-control" value="10" min="0" max="100" required>
                </div>
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: 'Cadastrar',
        cancelButtonText: 'Cancelar',
        preConfirm: () => {
            return {
                nome: document.getElementById('ass-nome').value,
                cpf: document.getElementById('ass-cpf').value,
                telefone: document.getElementById('ass-telefone').value,
                email: document.getElementById('ass-email').value,
                comissao_percentual: document.getElementById('ass-comissao').value
            };
        }
    });

    if (!formValues || !formValues.nome) return;

    try {
        const response = await fetch('/api/assistentes/cadastrar-independente', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formValues)
        });
        const data = await response.json();
        
        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Assistente Cadastrado!',
                text: 'O assistente foi cadastrado com sucesso.'
            });
            loadAssistentes();
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        Swal.fire({
            icon: 'error',
            title: 'Erro',
            text: error.message || 'Erro ao cadastrar assistente'
        });
    }
}

// ==================== ENTRADA DE PRODUTOS NO ESTOQUE ====================

async function registrarEntradaProduto() {
    const { value: formValues } = await Swal.fire({
        title: 'Registrar Entrada de Produto',
        html: `
            <div style="text-align: left;">
                <div class="mb-3">
                    <label>Produto *</label>
                    <select id="entrada-produto" class="form-select" required>
                        <option value="">Carregando...</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label>Quantidade *</label>
                    <input id="entrada-qtd" type="number" class="form-control" min="1" required>
                </div>
                <div class="mb-3">
                    <label>Fornecedor</label>
                    <input id="entrada-fornecedor" class="form-control">
                </div>
                <div class="mb-3">
                    <label>Nota Fiscal</label>
                    <input id="entrada-nf" class="form-control">
                </div>
                <div class="mb-3">
                    <label>Valor Unitário</label>
                    <input id="entrada-valor" type="number" step="0.01" class="form-control">
                </div>
                <div class="mb-3">
                    <label>Motivo</label>
                    <textarea id="entrada-motivo" class="form-control" rows="2">Reposição de estoque</textarea>
                </div>
            </div>
        `,
        didOpen: async () => {
            const response = await fetch('/api/produtos');
            const data = await response.json();
            const select = document.getElementById('entrada-produto');
            if (data.success) {
                select.innerHTML = '<option value="">Selecione um produto...</option>' +
                    data.produtos.map(p => `<option value="${p._id}">${p.nome} - ${p.marca}</option>`).join('');
            }
        },
        showCancelButton: true,
        confirmButtonText: 'Registrar',
        cancelButtonText: 'Cancelar',
        preConfirm: () => {
            return {
                produto_id: document.getElementById('entrada-produto').value,
                quantidade: document.getElementById('entrada-qtd').value,
                fornecedor: document.getElementById('entrada-fornecedor').value,
                nota_fiscal: document.getElementById('entrada-nf').value,
                valor_unitario: document.getElementById('entrada-valor').value,
                motivo: document.getElementById('entrada-motivo').value
            };
        }
    });

    if (!formValues || !formValues.produto_id) return;

    try {
        const response = await fetch('/api/estoque/produtos/entrada', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formValues)
        });
        const data = await response.json();
        
        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Entrada Registrada!',
                text: 'A entrada está aguardando aprovação.'
            });
            carregarEntradasPendentes();
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        Swal.fire({
            icon: 'error',
            title: 'Erro',
            text: error.message || 'Erro ao registrar entrada'
        });
    }
}

async function carregarEntradasPendentes() {
    try {
        const response = await fetch('/api/estoque/produtos/pendentes');
        const data = await response.json();
        
        const tbody = document.getElementById('estoquePendentesBody');
        if (!tbody) return;
        
        if (data.success && data.entradas.length > 0) {
            tbody.innerHTML = data.entradas.map(entrada => `
                <tr>
                    <td>${entrada.produto_nome} - ${entrada.produto_marca}</td>
                    <td>${entrada.quantidade}</td>
                    <td>${entrada.fornecedor || '-'}</td>
                    <td>${entrada.motivo}</td>
                    <td>${entrada.solicitado_por}</td>
                    <td>
                        <button class="btn btn-sm btn-success" onclick="aprovarEntradaProduto('${entrada._id}')">
                            <i class="bi bi-check-circle"></i> Aprovar
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="rejeitarEntradaProduto('${entrada._id}')">
                            <i class="bi bi-x-circle"></i> Rejeitar
                        </button>
                    </td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Nenhuma entrada pendente</td></tr>';
        }
    } catch (error) {
        console.error('Erro ao carregar entradas pendentes:', error);
    }
}

async function aprovarEntradaProduto(id) {
    const result = await Swal.fire({
        title: 'Aprovar Entrada?',
        text: 'Isso irá adicionar os produtos ao estoque.',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Sim, Aprovar',
        cancelButtonText: 'Cancelar'
    });

    if (!result.isConfirmed) return;

    try {
        const response = await fetch(`/api/estoque/produtos/aprovar/${id}`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Entrada Aprovada!',
                text: 'Os produtos foram adicionados ao estoque.'
            });
            carregarEntradasPendentes();
            loadProdutos();
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        Swal.fire({
            icon: 'error',
            title: 'Erro',
            text: error.message || 'Erro ao aprovar entrada'
        });
    }
}

async function rejeitarEntradaProduto(id) {
    const { value: motivo } = await Swal.fire({
        title: 'Rejeitar Entrada?',
        input: 'textarea',
        inputLabel: 'Motivo da rejeição',
        inputPlaceholder: 'Digite o motivo...',
        showCancelButton: true,
        confirmButtonText: 'Rejeitar',
        cancelButtonText: 'Cancelar'
    });

    if (!motivo) return;

    try {
        const response = await fetch(`/api/estoque/produtos/rejeitar/${id}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ motivo })
        });
        const data = await response.json();
        
        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Entrada Rejeitada',
                text: 'A entrada foi rejeitada.'
            });
            carregarEntradasPendentes();
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        Swal.fire({
            icon: 'error',
            title: 'Erro',
            text: error.message || 'Erro ao rejeitar entrada'
        });
    }
}

// ==================== MAPA DE CALOR ====================

async function carregarMapaCalor() {
    try {
        const response = await fetch('/api/relatorios/mapa-calor');
        const data = await response.json();
        
        if (data.success) {
            renderizarMapaCalor(data.mapa_calor);
        }
    } catch (error) {
        console.error('Erro ao carregar mapa de calor:', error);
    }
}

function renderizarMapaCalor(dados) {
    const container = document.getElementById('mapaCalorContainer');
    if (!container) return;
    
    container.innerHTML = '<h5 class="mb-3">Mapa de Calor - Movimentação (Últimos 90 dias)</h5>';
    
    const grid = document.createElement('div');
    grid.style.cssText = 'display: grid; grid-template-columns: repeat(auto-fill, minmax(30px, 1fr)); gap: 3px;';
    
    dados.forEach(dia => {
        const cell = document.createElement('div');
        const intensity = dia.intensidade;
        const alpha = Math.floor(intensity * 255).toString(16).padStart(2, '0');
        cell.style.cssText = `
            aspect-ratio: 1;
            background: #7C3AED${alpha};
            border-radius: 4px;
            cursor: pointer;
            transition: transform 0.2s;
        `;
        cell.title = `${dia.data}\n${dia.orcamentos} orçamentos\n${dia.agendamentos} agendamentos\nR$ ${dia.valor.toFixed(2)}`;
        cell.onmouseenter = () => cell.style.transform = 'scale(1.2)';
        cell.onmouseleave = () => cell.style.transform = 'scale(1)';
        grid.appendChild(cell);
    });
    
    container.appendChild(grid);
}

// ==================== EDIÇÃO DE SERVIÇOS E PRODUTOS ====================

async function editarServico(id) {
    try {
        const response = await fetch(`/api/servicos/${id}`);
        const data = await response.json();
        
        if (!data.success) throw new Error('Serviço não encontrado');
        
        const servico = data.servico;
        
        const { value: formValues } = await Swal.fire({
            title: 'Editar Serviço',
            html: `
                <div style="text-align: left;">
                    <div class="mb-3">
                        <label>Nome *</label>
                        <input id="edit-srv-nome" class="form-control" value="${servico.nome}" required>
                    </div>
                    <div class="mb-3">
                        <label>SKU</label>
                        <input id="edit-srv-sku" class="form-control" value="${servico.sku}">
                    </div>
                    <div class="mb-3">
                        <label>Tamanho</label>
                        <input id="edit-srv-tamanho" class="form-control" value="${servico.tamanho}">
                    </div>
                    <div class="mb-3">
                        <label>Preço *</label>
                        <input id="edit-srv-preco" type="number" step="0.01" class="form-control" value="${servico.preco}" required>
                    </div>
                    <div class="mb-3">
                        <label>Categoria</label>
                        <input id="edit-srv-categoria" class="form-control" value="${servico.categoria}">
                    </div>
                    <div class="mb-3">
                        <label>Duração (min)</label>
                        <input id="edit-srv-duracao" type="number" class="form-control" value="${servico.duracao}">
                    </div>
                    <div class="mb-3">
                        <label>Descrição</label>
                        <textarea id="edit-srv-descricao" class="form-control" rows="2">${servico.descricao || ''}</textarea>
                    </div>
                </div>
            `,
            showCancelButton: true,
            confirmButtonText: 'Salvar',
            cancelButtonText: 'Cancelar',
            width: '600px',
            preConfirm: () => {
                return {
                    nome: document.getElementById('edit-srv-nome').value,
                    sku: document.getElementById('edit-srv-sku').value,
                    tamanho: document.getElementById('edit-srv-tamanho').value,
                    preco: document.getElementById('edit-srv-preco').value,
                    categoria: document.getElementById('edit-srv-categoria').value,
                    duracao: document.getElementById('edit-srv-duracao').value,
                    descricao: document.getElementById('edit-srv-descricao').value
                };
            }
        });

        if (!formValues) return;

        const updateResponse = await fetch(`/api/servicos/${id}/editar`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formValues)
        });
        const updateData = await updateResponse.json();
        
        if (updateData.success) {
            Swal.fire({
                icon: 'success',
                title: 'Serviço Atualizado!',
                text: 'O serviço foi atualizado com sucesso.'
            });
            loadServicos();
        } else {
            throw new Error(updateData.message);
        }
    } catch (error) {
        Swal.fire({
            icon: 'error',
            title: 'Erro',
            text: error.message || 'Erro ao editar serviço'
        });
    }
}

async function editarProduto(id) {
    try {
        const response = await fetch(`/api/produtos/${id}`);
        const data = await response.json();
        
        if (!data.success) throw new Error('Produto não encontrado');
        
        const produto = data.produto;
        
        const { value: formValues } = await Swal.fire({
            title: 'Editar Produto',
            html: `
                <div style="text-align: left;">
                    <div class="mb-3">
                        <label>Nome *</label>
                        <input id="edit-prod-nome" class="form-control" value="${produto.nome}" required>
                    </div>
                    <div class="mb-3">
                        <label>Marca</label>
                        <input id="edit-prod-marca" class="form-control" value="${produto.marca}">
                    </div>
                    <div class="mb-3">
                        <label>SKU</label>
                        <input id="edit-prod-sku" class="form-control" value="${produto.sku}">
                    </div>
                    <div class="mb-3">
                        <label>Preço *</label>
                        <input id="edit-prod-preco" type="number" step="0.01" class="form-control" value="${produto.preco}" required>
                    </div>
                    <div class="mb-3">
                        <label>Custo</label>
                        <input id="edit-prod-custo" type="number" step="0.01" class="form-control" value="${produto.custo || 0}">
                    </div>
                    <div class="mb-3">
                        <label>Estoque</label>
                        <input id="edit-prod-estoque" type="number" class="form-control" value="${produto.estoque}">
                    </div>
                    <div class="mb-3">
                        <label>Estoque Mínimo</label>
                        <input id="edit-prod-minimo" type="number" class="form-control" value="${produto.estoque_minimo}">
                    </div>
                    <div class="mb-3">
                        <label>Categoria</label>
                        <input id="edit-prod-categoria" class="form-control" value="${produto.categoria}">
                    </div>
                    <div class="mb-3">
                        <label>Descrição</label>
                        <textarea id="edit-prod-descricao" class="form-control" rows="2">${produto.descricao || ''}</textarea>
                    </div>
                </div>
            `,
            showCancelButton: true,
            confirmButtonText: 'Salvar',
            cancelButtonText: 'Cancelar',
            width: '600px',
            preConfirm: () => {
                return {
                    nome: document.getElementById('edit-prod-nome').value,
                    marca: document.getElementById('edit-prod-marca').value,
                    sku: document.getElementById('edit-prod-sku').value,
                    preco: document.getElementById('edit-prod-preco').value,
                    custo: document.getElementById('edit-prod-custo').value,
                    estoque: document.getElementById('edit-prod-estoque').value,
                    estoque_minimo: document.getElementById('edit-prod-minimo').value,
                    categoria: document.getElementById('edit-prod-categoria').value,
                    descricao: document.getElementById('edit-prod-descricao').value
                };
            }
        });

        if (!formValues) return;

        const updateResponse = await fetch(`/api/produtos/${id}/editar`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formValues)
        });
        const updateData = await updateResponse.json();
        
        if (updateData.success) {
            Swal.fire({
                icon: 'success',
                title: 'Produto Atualizado!',
                text: 'O produto foi atualizado com sucesso.'
            });
            loadProdutos();
        } else {
            throw new Error(updateData.message);
        }
    } catch (error) {
        Swal.fire({
            icon: 'error',
            title: 'Erro',
            text: error.message || 'Erro ao editar produto'
        });
    }
}

// ==================== ANAMNESE E PRONTUÁRIO ====================

async function gerenciarAnamnese(clienteId) {
    try {
        const response = await fetch(`/api/clientes/${clienteId}/anamnese`);
        const data = await response.json();
        
        if (!data.success) throw new Error('Erro ao carregar anamnese');
        
        // Construir formulário dinâmico
        let html = '<div style="text-align: left; max-height: 500px; overflow-y: auto;">';
        
        const anamneseData = data.anamnese || {};
        
        // Aqui você pode construir o formulário baseado em ANAMNESE_FORM
        html += '<p>Funcionalidade de anamnese carregada. Implementar formulário completo.</p>';
        html += '</div>';
        
        const { value: formValues } = await Swal.fire({
            title: 'Anamnese do Cliente',
            html: html,
            showCancelButton: true,
            confirmButtonText: 'Salvar',
            cancelButtonText: 'Cancelar',
            width: '800px'
        });
        
        // Implementar salvamento
    } catch (error) {
        Swal.fire({
            icon: 'error',
            title: 'Erro',
            text: error.message || 'Erro ao gerenciar anamnese'
        });
    }
}

async function imprimirResumoCliente(clienteId) {
    try {
        window.open(`/api/clientes/${clienteId}/resumo-pdf`, '_blank');
    } catch (error) {
        Swal.fire({
            icon: 'error',
            title: 'Erro',
            text: 'Erro ao gerar PDF do cliente'
        });
    }
}

async function carregarFaturamentoCliente(clienteId) {
    try {
        const response = await fetch(`/api/clientes/${clienteId}/faturamento`);
        const data = await response.json();
        
        if (data.success) {
            const container = document.getElementById('clienteFaturamento');
            if (container) {
                container.innerHTML = `
                    <div class="stat-card">
                        <h3>R$ ${data.total_faturado.toFixed(2)}</h3>
                        <p>Total Faturado com este Cliente</p>
                        <small>${data.quantidade_orcamentos} atendimentos | Ticket médio: R$ ${data.ticket_medio.toFixed(2)}</small>
                    </div>
                `;
            }
        }
    } catch (error) {
        console.error('Erro ao carregar faturamento:', error);
    }
}

// ==================== INICIALIZAÇÃO ====================

document.addEventListener('DOMContentLoaded', () => {
    // Carregar logo ao iniciar
    carregarLogo();
    
    // Carregar outras funcionalidades se necessário
    if (document.getElementById('mapaCalorContainer')) {
        carregarMapaCalor();
    }
    
    if (document.getElementById('estoquePendentesBody')) {
        carregarEntradasPendentes();
    }
    
    if (document.getElementById('historicoComissoesBody')) {
        carregarHistoricoComissoes();
    }
});

console.log('✅ Novas funcionalidades carregadas - BIOMA Uberaba v3.7');
