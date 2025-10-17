// ============================================
// BIOMA UBERABA v3.8 - Melhorias e Novas Funcionalidades
// ============================================

// ========== PROFISSIONAIS COM MULTICOMISSÃO E FOTO ==========

async function showModalProfissionalMelhorado(profissionalId = null) {
    let profissional = null;
    let todosProfs = [];

    // Carregar lista de profissionais para assistentes
    try {
        const res = await fetch('/api/profissionais', {credentials: 'include'});
        const data = await res.json();
        if (data.success) {
            todosProfs = data.profissionais || [];
        }
    } catch (e) {
        console.error('Erro ao carregar profissionais:', e);
    }

    // Se estiver editando, carregar dados
    if (profissionalId) {
        try {
            const res = await fetch(`/api/profissionais/${profissionalId}`, {credentials: 'include'});
            const data = await res.json();
            if (data.success) {
                profissional = data.profissional;
            }
        } catch (e) {
            Swal.fire('Erro', 'Não foi possível carregar o profissional', 'error');
            return;
        }
    }

    const assistentes = profissional?.assistentes || [];
    const fotoAtual = profissional?.foto_url || '';

    // Criar HTML do modal
    const assistentesHTML = assistentes.map((a, idx) => `
        <div class="assistente-item mb-3 p-3" style="background: var(--bg-main); border-radius: 12px; border-left: 4px solid var(--primary);">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <strong>${a.nome}</strong>
                    <small class="d-block text-muted">ID: ${a.id}</small>
                </div>
                <div class="col-md-3">
                    <input type="number" class="form-control form-control-sm" value="${a.comissao_perc_sobre_profissional}"
                           id="assistente-comissao-${idx}" min="0" max="100" step="0.1" placeholder="% sobre profissional">
                </div>
                <div class="col-md-1">
                    <button class="btn btn-sm btn-danger" onclick="removerAssistente(${idx})"><i class="bi bi-trash"></i></button>
                </div>
            </div>
        </div>
    `).join('');

    const html = `
        <div style="max-height: 70vh; overflow-y: auto; padding: 10px;">
            <div class="row g-3">
                <!-- Foto do Profissional -->
                <div class="col-12 text-center mb-3">
                    <div style="width: 150px; height: 150px; margin: 0 auto; border-radius: 50%; overflow: hidden; border: 4px solid var(--primary); background: var(--bg-main);">
                        <img id="preview-foto-prof" src="${fotoAtual || 'https://via.placeholder.com/150'}"
                             style="width: 100%; height: 100%; object-fit: cover;">
                    </div>
                    <input type="file" id="foto-profissional" accept="image/*" class="form-control mt-3"
                           onchange="previewFotoProfissional(this)">
                    <small class="text-muted">Formato: JPG, PNG (máx 2MB)</small>
                </div>

                <!-- Dados básicos -->
                <div class="col-md-6">
                    <label class="fw-bold">Nome Completo *</label>
                    <input type="text" id="prof-nome" class="form-control" value="${profissional?.nome || ''}" required>
                </div>
                <div class="col-md-6">
                    <label class="fw-bold">CPF *</label>
                    <input type="text" id="prof-cpf" class="form-control" value="${profissional?.cpf || ''}"
                           maxlength="14" required>
                </div>
                <div class="col-md-6">
                    <label class="fw-bold">Email</label>
                    <input type="email" id="prof-email" class="form-control" value="${profissional?.email || ''}">
                </div>
                <div class="col-md-6">
                    <label class="fw-bold">Telefone</label>
                    <input type="text" id="prof-telefone" class="form-control" value="${profissional?.telefone || ''}">
                </div>
                <div class="col-md-6">
                    <label class="fw-bold">Especialidade</label>
                    <input type="text" id="prof-especialidade" class="form-control" value="${profissional?.especialidade || ''}">
                </div>
                <div class="col-md-6">
                    <label class="fw-bold">Comissão (%)</label>
                    <input type="number" id="prof-comissao" class="form-control" value="${profissional?.comissao_perc || 0}"
                           min="0" max="100" step="0.1">
                </div>

                <!-- Multicomissão - Assistentes -->
                <div class="col-12 mt-4">
                    <h5 style="color: var(--primary); border-bottom: 2px solid var(--primary); padding-bottom: 10px;">
                        <i class="bi bi-people"></i> Assistentes (Multicomissão)
                    </h5>
                    <p class="text-muted small">Os assistentes ganham uma porcentagem da comissão do profissional principal.</p>

                    <div id="lista-assistentes">
                        ${assistentesHTML || '<p class="text-muted text-center">Nenhum assistente adicionado</p>'}
                    </div>

                    <!-- Adicionar novo assistente -->
                    <div class="mt-3 p-3" style="background: linear-gradient(135deg, rgba(124,58,237,0.1), rgba(236,72,153,0.1)); border-radius: 12px;">
                        <h6 class="fw-bold mb-3"><i class="bi bi-plus-circle"></i> Adicionar Assistente</h6>
                        <div class="row g-2">
                            <div class="col-md-8">
                                <select id="novo-assistente-select" class="form-select">
                                    <option value="">Selecione um profissional...</option>
                                    ${todosProfs.filter(p => p._id !== profissionalId).map(p =>
                                        `<option value="${p._id}">${p.nome} - ${p.especialidade || 'N/A'}</option>`
                                    ).join('')}
                                </select>
                            </div>
                            <div class="col-md-3">
                                <input type="number" id="novo-assistente-comissao" class="form-control"
                                       placeholder="% sobre prof." min="0" max="100" step="0.1">
                            </div>
                            <div class="col-md-1">
                                <button class="btn btn-primary w-100" onclick="adicionarAssistente()">
                                    <i class="bi bi-plus"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    Swal.fire({
        title: profissionalId ? '✏️ Editar Profissional' : '➕ Novo Profissional',
        html: html,
        width: '900px',
        showCancelButton: true,
        confirmButtonText: profissionalId ? 'Atualizar' : 'Cadastrar',
        cancelButtonText: 'Cancelar',
        customClass: {
            confirmButton: 'btn btn-primary',
            cancelButton: 'btn btn-secondary'
        },
        preConfirm: async () => {
            const nome = document.getElementById('prof-nome').value.trim();
            const cpf = document.getElementById('prof-cpf').value.trim();
            const email = document.getElementById('prof-email').value.trim();
            const telefone = document.getElementById('prof-telefone').value.trim();
            const especialidade = document.getElementById('prof-especialidade').value.trim();
            const comissao = parseFloat(document.getElementById('prof-comissao').value) || 0;

            if (!nome || !cpf) {
                Swal.showValidationMessage('Nome e CPF são obrigatórios');
                return false;
            }

            // Coletar assistentes
            const assistentesAtualizados = [];
            document.querySelectorAll('.assistente-item').forEach((item, idx) => {
                const comissaoInput = document.getElementById(`assistente-comissao-${idx}`);
                if (comissaoInput) {
                    const assistenteOriginal = assistentes[idx];
                    assistentesAtualizados.push({
                        id: assistenteOriginal.id,
                        nome: assistenteOriginal.nome,
                        comissao_perc_sobre_profissional: parseFloat(comissaoInput.value) || 0
                    });
                }
            });

            // Upload de foto se selecionada
            let fotoUrl = fotoAtual;
            const fotoInput = document.getElementById('foto-profissional');
            if (fotoInput.files && fotoInput.files[0] && profissionalId) {
                const formData = new FormData();
                formData.append('foto', fotoInput.files[0]);

                try {
                    const uploadRes = await fetch(`/api/profissionais/${profissionalId}/upload-foto`, {
                        method: 'POST',
                        credentials: 'include',
                        body: formData
                    });
                    const uploadData = await uploadRes.json();
                    if (uploadData.success) {
                        fotoUrl = uploadData.foto_url;
                    }
                } catch (e) {
                    console.error('Erro ao fazer upload da foto:', e);
                }
            }

            return {
                nome, cpf, email, telefone, especialidade,
                comissao_perc: comissao,
                assistentes: assistentesAtualizados,
                foto_url: fotoUrl
            };
        }
    }).then(async (result) => {
        if (result.isConfirmed && result.value) {
            try {
                const url = profissionalId ? `/api/profissionais/${profissionalId}` : '/api/profissionais';
                const method = profissionalId ? 'PUT' : 'POST';

                const res = await fetch(url, {
                    method: method,
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify(result.value)
                });

                const data = await res.json();
                if (data.success) {
                    Swal.fire('Sucesso!', profissionalId ? 'Profissional atualizado!' : 'Profissional cadastrado!', 'success');
                    if (typeof loadProfissionais === 'function') loadProfissionais();
                } else {
                    Swal.fire('Erro', data.message || 'Erro ao salvar profissional', 'error');
                }
            } catch (e) {
                Swal.fire('Erro', 'Erro ao comunicar com o servidor', 'error');
            }
        }
    });
}

function previewFotoProfissional(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('preview-foto-prof').src = e.target.result;
        };
        reader.readAsDataURL(input.files[0]);
    }
}

let assistentesTemp = [];

function adicionarAssistente() {
    const select = document.getElementById('novo-assistente-select');
    const comissaoInput = document.getElementById('novo-assistente-comissao');

    const assistenteId = select.value;
    const assistenteNome = select.options[select.selectedIndex].text;
    const comissao = parseFloat(comissaoInput.value) || 0;

    if (!assistenteId) {
        Swal.fire('Atenção', 'Selecione um profissional', 'warning');
        return;
    }

    if (comissao <= 0) {
        Swal.fire('Atenção', 'Informe a porcentagem de comissão', 'warning');
        return;
    }

    // Adicionar à lista temporária
    assistentesTemp.push({
        id: assistenteId,
        nome: assistenteNome,
        comissao_perc_sobre_profissional: comissao
    });

    // Atualizar HTML
    const idx = assistentesTemp.length - 1;
    const novoHTML = `
        <div class="assistente-item mb-3 p-3" style="background: var(--bg-main); border-radius: 12px; border-left: 4px solid var(--primary);">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <strong>${assistenteNome}</strong>
                    <small class="d-block text-muted">ID: ${assistenteId}</small>
                </div>
                <div class="col-md-3">
                    <input type="number" class="form-control form-control-sm" value="${comissao}"
                           id="assistente-comissao-${idx}" min="0" max="100" step="0.1" placeholder="% sobre profissional">
                </div>
                <div class="col-md-1">
                    <button class="btn btn-sm btn-danger" onclick="removerAssistente(${idx})"><i class="bi bi-trash"></i></button>
                </div>
            </div>
        </div>
    `;

    const lista = document.getElementById('lista-assistentes');
    if (lista.querySelector('p.text-muted')) {
        lista.innerHTML = '';
    }
    lista.insertAdjacentHTML('beforeend', novoHTML);

    // Limpar campos
    select.value = '';
    comissaoInput.value = '';
}

function removerAssistente(idx) {
    // Remover visualmente
    const items = document.querySelectorAll('.assistente-item');
    if (items[idx]) {
        items[idx].remove();
    }
}

// ========== ESTOQUE MELHORADO COM APROVAÇÃO ==========

async function loadEstoqueMelhorado() {
    try {
        // Carregar estatísticas
        const statsRes = await fetch('/api/estoque/stats', {credentials: 'include'});
        const statsData = await statsRes.json();

        if (statsData.success) {
            const stats = statsData.stats;
            document.getElementById('estoque-total').textContent = stats.total_produtos || 0;
            document.getElementById('estoque-baixo').textContent = stats.produtos_baixo || 0;
            document.getElementById('estoque-zerado').textContent = stats.produtos_zerados || 0;
            document.getElementById('estoque-valor').textContent = `R$ ${(stats.valor_total_estoque || 0).toFixed(2)}`;

            // Atualizar badge de pendentes
            const pendentes = stats.movimentacoes_pendentes || 0;
            if (document.getElementById('estoque-pendentes')) {
                document.getElementById('estoque-pendentes').textContent = pendentes;
                // Destacar se houver pendentes
                const card = document.getElementById('estoque-pendentes').closest('.estoque-stat-card');
                if (card) {
                    if (pendentes > 0) {
                        card.style.borderLeft = '5px solid var(--warning)';
                    } else {
                        card.style.borderLeft = '5px solid var(--success)';
                    }
                }
            }
        }

        // Carregar produtos em falta
        const alertaRes = await fetch('/api/estoque/alerta', {credentials: 'include'});
        const alertaData = await alertaRes.json();

        if (alertaData.success && alertaData.produtos) {
            const tbody = document.getElementById('produtos-falta-body');
            if (alertaData.produtos.length > 0) {
                tbody.innerHTML = alertaData.produtos.map(p => `
                    <tr style="background: ${p.estoque === 0 ? 'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)'};">
                        <td><strong>${p.nome}</strong></td>
                        <td>${p.marca || '-'}</td>
                        <td><span class="badge ${p.estoque === 0 ? 'danger' : 'warning'}">${p.estoque}</span></td>
                        <td>${p.estoque_minimo}</td>
                        <td>
                            <button class="btn btn-sm btn-success" onclick="addEntradaEstoque('${p._id}', '${p.nome}')">
                                <i class="bi bi-plus-circle"></i> Entrada
                            </button>
                        </td>
                    </tr>
                `).join('');
            } else {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-success">✅ Nenhum produto em falta!</td></tr>';
            }
        }

        // Carregar movimentações
        const movRes = await fetch('/api/estoque/movimentacoes', {credentials: 'include'});
        const movData = await movRes.json();

        if (movData.success && movData.movimentacoes) {
            const tbody = document.getElementById('movimentacoes-body');
            if (movData.movimentacoes.length > 0) {
                tbody.innerHTML = movData.movimentacoes.slice(0, 30).map(m => {
                    const data = new Date(m.data).toLocaleString('pt-BR');
                    const tipoIcon = m.tipo === 'entrada' ? '📥' : '📤';
                    const tipoClass = m.tipo === 'entrada' ? 'success' : 'danger';

                    // Status da movimentação
                    let statusBadge = '';
                    let acoes = '';

                    if (m.status === 'pendente') {
                        statusBadge = '<span class="badge warning">⏳ Pendente</span>';
                        acoes = `
                            <button class="btn btn-sm btn-success" onclick="aprovarMovimentacao('${m._id}')" title="Aprovar">
                                <i class="bi bi-check-circle"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="reprovarMovimentacao('${m._id}')" title="Reprovar">
                                <i class="bi bi-x-circle"></i>
                            </button>
                        `;
                    } else if (m.status === 'aprovado') {
                        statusBadge = '<span class="badge success">✅ Aprovado</span>';
                        acoes = `<small class="text-muted">Por: ${m.aprovado_por || 'N/A'}</small>`;
                    } else if (m.status === 'reprovado') {
                        statusBadge = '<span class="badge danger">❌ Reprovado</span>';
                        acoes = `<small class="text-muted" title="${m.motivo_reprovacao || ''}">Por: ${m.reprovado_por || 'N/A'}</small>`;
                    }

                    return `
                        <tr style="background: ${m.status === 'pendente' ? 'rgba(245, 158, 11, 0.05)' : ''}">
                            <td>${data}</td>
                            <td><strong>${m.produto_nome || 'N/A'}</strong></td>
                            <td><span class="badge ${tipoClass}">${tipoIcon} ${m.tipo}</span></td>
                            <td>${m.quantidade}</td>
                            <td>${m.motivo || '-'}</td>
                            <td>${m.usuario || 'Sistema'}</td>
                            <td>${statusBadge}</td>
                            <td>${acoes}</td>
                        </tr>
                    `;
                }).join('');
            } else {
                tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Nenhuma movimentação</td></tr>';
            }
        }

        // Carregar produtos críticos
        await loadProdutosCriticos();

    } catch (e) {
        console.error('Erro ao carregar estoque:', e);
    }
}

async function aprovarMovimentacao(id) {
    const result = await Swal.fire({
        title: 'Aprovar Movimentação?',
        text: 'O estoque será atualizado imediatamente.',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Sim, Aprovar',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#10B981'
    });

    if (result.isConfirmed) {
        try {
            const res = await fetch(`/api/estoque/aprovar/${id}`, {
                method: 'POST',
                credentials: 'include'
            });

            const data = await res.json();
            if (data.success) {
                Swal.fire('Aprovado!', 'Movimentação aprovada e estoque atualizado!', 'success');
                loadEstoqueMelhorado();
            } else {
                Swal.fire('Erro', data.message || 'Erro ao aprovar', 'error');
            }
        } catch (e) {
            Swal.fire('Erro', 'Erro ao comunicar com o servidor', 'error');
        }
    }
}

async function reprovarMovimentacao(id) {
    const result = await Swal.fire({
        title: 'Reprovar Movimentação?',
        html: `
            <p class="mb-3">A movimentação será marcada como reprovada.</p>
            <textarea id="motivo-reprovacao" class="form-control" placeholder="Motivo da reprovação (opcional)" rows="3"></textarea>
        `,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Sim, Reprovar',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#EF4444',
        preConfirm: () => {
            return {
                motivo: document.getElementById('motivo-reprovacao').value.trim()
            };
        }
    });

    if (result.isConfirmed) {
        try {
            const res = await fetch(`/api/estoque/reprovar/${id}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                credentials: 'include',
                body: JSON.stringify({motivo: result.value.motivo})
            });

            const data = await res.json();
            if (data.success) {
                Swal.fire('Reprovado!', 'Movimentação reprovada!', 'success');
                loadEstoqueMelhorado();
            } else {
                Swal.fire('Erro', data.message || 'Erro ao reprovar', 'error');
            }
        } catch (e) {
            Swal.fire('Erro', 'Erro ao comunicar com o servidor', 'error');
        }
    }
}

async function aprovarTodas() {
    const result = await Swal.fire({
        title: 'Aprovar TODAS as Movimentações Pendentes?',
        text: 'Todas as movimentações pendentes serão aprovadas e o estoque será atualizado.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Sim, Aprovar Todas',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#10B981'
    });

    if (result.isConfirmed) {
        Swal.fire({
            title: 'Processando...',
            html: 'Aprovando movimentações...',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        try {
            const res = await fetch('/api/estoque/aprovar-todos', {
                method: 'POST',
                credentials: 'include'
            });

            const data = await res.json();
            if (data.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Concluído!',
                    html: `
                        <p><strong>${data.aprovadas}</strong> movimentações aprovadas</p>
                        ${data.erros > 0 ? `<p class="text-danger">${data.erros} erros encontrados</p>` : ''}
                    `,
                    timer: 3000
                });
                loadEstoqueMelhorado();
            } else {
                Swal.fire('Erro', data.message || 'Erro ao aprovar', 'error');
            }
        } catch (e) {
            Swal.fire('Erro', 'Erro ao comunicar com o servidor', 'error');
        }
    }
}

async function reprovarTodas() {
    const result = await Swal.fire({
        title: 'Reprovar TODAS as Movimentações Pendentes?',
        html: `
            <p class="mb-3">Todas as movimentações pendentes serão reprovadas.</p>
            <textarea id="motivo-reprovacao-massa" class="form-control" placeholder="Motivo da reprovação (opcional)" rows="3"></textarea>
        `,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Sim, Reprovar Todas',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#EF4444',
        preConfirm: () => {
            return {
                motivo: document.getElementById('motivo-reprovacao-massa').value.trim()
            };
        }
    });

    if (result.isConfirmed) {
        try {
            const res = await fetch('/api/estoque/reprovar-todos', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                credentials: 'include',
                body: JSON.stringify({motivo: result.value.motivo})
            });

            const data = await res.json();
            if (data.success) {
                Swal.fire('Reprovadas!', `${data.reprovadas} movimentações reprovadas!`, 'success');
                loadEstoqueMelhorado();
            } else {
                Swal.fire('Erro', data.message || 'Erro ao reprovar', 'error');
            }
        } catch (e) {
            Swal.fire('Erro', 'Erro ao comunicar com o servidor', 'error');
        }
    }
}

async function loadProdutosCriticos() {
    try {
        const res = await fetch('/api/estoque/produtos-criticos', {credentials: 'include'});
        const data = await res.json();

        if (data.success && data.produtos) {
            const tbody = document.getElementById('produtos-criticos-body');
            if (!tbody) return;

            if (data.produtos.length > 0) {
                tbody.innerHTML = data.produtos.map(p => {
                    const percentual = p.percentual_estoque || 0;
                    let cor = 'danger';
                    if (percentual > 20) cor = 'warning';

                    return `
                        <tr>
                            <td><strong>${p.nome}</strong></td>
                            <td>${p.marca || '-'}</td>
                            <td><span class="badge ${cor}">${p.estoque}</span></td>
                            <td>${p.estoque_minimo}</td>
                            <td>
                                <div class="progress" style="height: 25px;">
                                    <div class="progress-bar bg-${cor}" style="width: ${Math.min(percentual, 100)}%">
                                        ${percentual.toFixed(0)}%
                                    </div>
                                </div>
                            </td>
                            <td>
                                <button class="btn btn-sm btn-success" onclick="addEntradaEstoque('${p._id}', '${p.nome}')">
                                    <i class="bi bi-plus-circle"></i> Entrada
                                </button>
                                <button class="btn btn-sm btn-primary" onclick="ajustarEstoque('${p._id}', '${p.nome}', ${p.estoque})">
                                    <i class="bi bi-sliders"></i> Ajustar
                                </button>
                            </td>
                        </tr>
                    `;
                }).join('');
            } else {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center text-success">✅ Nenhum produto crítico!</td></tr>';
            }
        }
    } catch (e) {
        console.error('Erro ao carregar produtos críticos:', e);
    }
}

async function ajustarEstoque(produtoId, produtoNome, estoqueAtual) {
    const result = await Swal.fire({
        title: `📊 Ajuste de Inventário`,
        html: `
            <p class="mb-3"><strong>Produto:</strong> ${produtoNome}</p>
            <p class="mb-3">Estoque atual no sistema: <strong>${estoqueAtual}</strong></p>
            <div class="mb-3">
                <label class="fw-bold">Estoque Real (contado)</label>
                <input type="number" id="estoque-real" class="form-control" min="0" value="${estoqueAtual}" autofocus>
            </div>
            <div class="mb-3">
                <label class="fw-bold">Motivo do Ajuste</label>
                <input type="text" id="motivo-ajuste" class="form-control" placeholder="Ex: Inventário mensal, Perda, Avaria...">
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: 'Ajustar Estoque',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#7C3AED',
        preConfirm: () => {
            const estoqueReal = parseInt(document.getElementById('estoque-real').value);
            const motivo = document.getElementById('motivo-ajuste').value.trim();

            if (isNaN(estoqueReal) || estoqueReal < 0) {
                Swal.showValidationMessage('Estoque real inválido');
                return false;
            }

            return {estoqueReal, motivo};
        }
    });

    if (result.isConfirmed && result.value) {
        try {
            const res = await fetch('/api/estoque/ajustar', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                credentials: 'include',
                body: JSON.stringify({
                    produto_id: produtoId,
                    estoque_real: result.value.estoqueReal,
                    motivo: result.value.motivo || 'Ajuste de inventário'
                })
            });

            const data = await res.json();
            if (data.success) {
                const diferenca = data.diferenca;
                const sinal = diferenca > 0 ? '+' : '';
                Swal.fire({
                    icon: 'success',
                    title: 'Estoque Ajustado!',
                    html: `
                        <p>Diferença: <strong style="color: ${diferenca >= 0 ? 'var(--success)' : 'var(--danger)'}">${sinal}${diferenca} unidades</strong></p>
                        <p>Novo estoque: <strong>${result.value.estoqueReal}</strong></p>
                    `,
                    timer: 3000
                });
                loadEstoqueMelhorado();
            } else {
                Swal.fire('Erro', data.message || 'Erro ao ajustar estoque', 'error');
            }
        } catch (e) {
            Swal.fire('Erro', 'Erro ao comunicar com o servidor', 'error');
        }
    }
}

async function addEntradaEstoque(produtoId, produtoNome) {
    const result = await Swal.fire({
        title: `Entrada de Estoque`,
        html: `
            <p class="mb-3"><strong>Produto:</strong> ${produtoNome}</p>
            <div class="mb-3">
                <label class="fw-bold">Quantidade</label>
                <input type="number" id="qtd-entrada" class="form-control" min="1" value="1">
            </div>
            <div class="mb-3">
                <label class="fw-bold">Motivo</label>
                <input type="text" id="motivo-entrada" class="form-control" placeholder="Ex: Compra, Devolução...">
            </div>
            <div class="mb-3">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="aprovar-automatico" checked>
                    <label class="form-check-label" for="aprovar-automatico">
                        Aprovar automaticamente (atualizar estoque imediatamente)
                    </label>
                </div>
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: 'Confirmar Entrada',
        preConfirm: () => {
            const qtd = parseInt(document.getElementById('qtd-entrada').value);
            const motivo = document.getElementById('motivo-entrada').value.trim();
            const aprovarAuto = document.getElementById('aprovar-automatico').checked;

            if (!qtd || qtd <= 0) {
                Swal.showValidationMessage('Quantidade inválida');
                return false;
            }

            return {qtd, motivo, aprovarAuto};
        }
    });

    if (result.isConfirmed && result.value) {
        try {
            const res = await fetch('/api/estoque/movimentacao', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                credentials: 'include',
                body: JSON.stringify({
                    produto_id: produtoId,
                    tipo: 'entrada',
                    quantidade: result.value.qtd,
                    motivo: result.value.motivo,
                    aprovar_automatico: result.value.aprovarAuto
                })
            });

            const data = await res.json();
            if (data.success) {
                const msg = data.status === 'aprovado' ?
                    'Entrada registrada e aprovada!' :
                    'Entrada registrada! Aguardando aprovação.';
                Swal.fire('Sucesso!', msg, 'success');
                loadEstoqueMelhorado();
            }
        } catch (e) {
            Swal.fire('Erro', 'Erro ao registrar entrada', 'error');
        }
    }
}

async function addSaidaEstoque() {
    // Buscar produtos disponíveis
    const produtosRes = await fetch('/api/produtos', {credentials: 'include'});
    const produtosData = await produtosRes.json();

    if (!produtosData.success || !produtosData.produtos) {
        Swal.fire('Erro', 'Erro ao carregar produtos', 'error');
        return;
    }

    const produtosOptions = produtosData.produtos
        .filter(p => p.ativo)
        .map(p => `<option value="${p._id}">${p.nome} - Estoque: ${p.estoque}</option>`)
        .join('');

    const result = await Swal.fire({
        title: `Saída de Estoque`,
        html: `
            <div class="mb-3">
                <label class="fw-bold">Produto</label>
                <select id="produto-saida" class="form-select">
                    <option value="">Selecione...</option>
                    ${produtosOptions}
                </select>
            </div>
            <div class="mb-3">
                <label class="fw-bold">Quantidade</label>
                <input type="number" id="qtd-saida" class="form-control" min="1" value="1">
            </div>
            <div class="mb-3">
                <label class="fw-bold">Motivo</label>
                <select id="motivo-saida" class="form-select">
                    <option value="Venda">Venda</option>
                    <option value="Perda">Perda</option>
                    <option value="Avaria">Avaria</option>
                    <option value="Devolução">Devolução</option>
                    <option value="Outro">Outro</option>
                </select>
            </div>
            <div class="mb-3" id="outro-motivo-container" style="display:none">
                <input type="text" id="outro-motivo" class="form-control" placeholder="Especifique o motivo...">
            </div>
            <div class="mb-3">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="aprovar-automatico-saida" checked>
                    <label class="form-check-label" for="aprovar-automatico-saida">
                        Aprovar automaticamente
                    </label>
                </div>
            </div>
        `,
        width: '600px',
        showCancelButton: true,
        confirmButtonText: 'Confirmar Saída',
        didOpen: () => {
            document.getElementById('motivo-saida').addEventListener('change', (e) => {
                const container = document.getElementById('outro-motivo-container');
                container.style.display = e.target.value === 'Outro' ? 'block' : 'none';
            });
        },
        preConfirm: () => {
            const produtoId = document.getElementById('produto-saida').value;
            const qtd = parseInt(document.getElementById('qtd-saida').value);
            let motivo = document.getElementById('motivo-saida').value;
            const aprovarAuto = document.getElementById('aprovar-automatico-saida').checked;

            if (!produtoId) {
                Swal.showValidationMessage('Selecione um produto');
                return false;
            }

            if (!qtd || qtd <= 0) {
                Swal.showValidationMessage('Quantidade inválida');
                return false;
            }

            if (motivo === 'Outro') {
                motivo = document.getElementById('outro-motivo').value.trim();
                if (!motivo) {
                    Swal.showValidationMessage('Especifique o motivo');
                    return false;
                }
            }

            return {produtoId, qtd, motivo, aprovarAuto};
        }
    });

    if (result.isConfirmed && result.value) {
        try {
            const res = await fetch('/api/estoque/movimentacao', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                credentials: 'include',
                body: JSON.stringify({
                    produto_id: result.value.produtoId,
                    tipo: 'saida',
                    quantidade: result.value.qtd,
                    motivo: result.value.motivo,
                    aprovar_automatico: result.value.aprovarAuto
                })
            });

            const data = await res.json();
            if (data.success) {
                const msg = data.status === 'aprovado' ?
                    'Saída registrada e aprovada!' :
                    'Saída registrada! Aguardando aprovação.';
                Swal.fire('Sucesso!', msg, 'success');
                loadEstoqueMelhorado();
            } else {
                Swal.fire('Erro', data.message || 'Erro ao registrar saída', 'error');
            }
        } catch (e) {
            Swal.fire('Erro', 'Erro ao comunicar com o servidor', 'error');
        }
    }
}

// ========== CAMPO DE PESQUISA COM AUTOCOMPLETE ==========

function setupBuscaUniversal(inputId, resultsId, apiUrl, displayField, onSelect) {
    const input = document.getElementById(inputId);
    const resultsDiv = document.getElementById(resultsId);

    if (!input || !resultsDiv) return;

    let timeoutId;

    input.addEventListener('input', function() {
        clearTimeout(timeoutId);
        const termo = this.value.trim();

        if (termo.length < 2) {
            resultsDiv.style.display = 'none';
            return;
        }

        timeoutId = setTimeout(async () => {
            try {
                const res = await fetch(`${apiUrl}?termo=${encodeURIComponent(termo)}`, {credentials: 'include'});
                const data = await res.json();

                if (data.success && data[displayField] && data[displayField].length > 0) {
                    const items = data[displayField];
                    resultsDiv.innerHTML = items.map(item => `
                        <div class="autocomplete-item" onclick='${onSelect}(${JSON.stringify(item).replace(/'/g, "&apos;")})'>
                            <strong>${item.display_name || item.nome}</strong>
                            ${item.cpf ? `<br><small>CPF: ${item.cpf}</small>` : ''}
                            ${item.telefone ? `<br><small>Tel: ${item.telefone}</small>` : ''}
                        </div>
                    `).join('');
                    resultsDiv.style.display = 'block';
                } else {
                    resultsDiv.innerHTML = '<div class="autocomplete-item text-muted">Nenhum resultado</div>';
                    resultsDiv.style.display = 'block';
                }
            } catch (e) {
                console.error('Erro na busca:', e);
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

// ========== VISUALIZAÇÃO E EDIÇÃO ==========

async function visualizarServico(id) {
    try {
        const res = await fetch(`/api/servicos/${id}`, {credentials: 'include'});
        const data = await res.json();

        if (data.success && data.servico) {
            const s = data.servico;
            Swal.fire({
                title: '👁️ Visualizar Serviço',
                html: `
                    <div style="text-align: left; padding: 20px;">
                        <h4 style="color: var(--primary); border-bottom: 2px solid var(--primary); padding-bottom: 10px;">
                            ${s.nome}
                        </h4>
                        <div class="row g-3 mt-3">
                            <div class="col-6">
                                <p><strong>SKU:</strong> ${s.sku}</p>
                                <p><strong>Tamanho:</strong> ${s.tamanho}</p>
                                <p><strong>Categoria:</strong> ${s.categoria}</p>
                            </div>
                            <div class="col-6">
                                <p><strong>Preço:</strong> <span style="color: var(--success); font-size: 1.5rem;">R$ ${s.preco.toFixed(2)}</span></p>
                                <p><strong>Duração:</strong> ${s.duracao} min</p>
                                <p><strong>Status:</strong> <span class="badge ${s.ativo ? 'success' : 'danger'}">${s.ativo ? 'Ativo' : 'Inativo'}</span></p>
                            </div>
                        </div>
                    </div>
                `,
                confirmButtonText: 'Fechar',
                width: '600px'
            });
        }
    } catch (e) {
        Swal.fire('Erro', 'Não foi possível carregar o serviço', 'error');
    }
}

async function visualizarProduto(id) {
    try {
        const res = await fetch(`/api/produtos/${id}`, {credentials: 'include'});
        const data = await res.json();

        if (data.success && data.produto) {
            const p = data.produto;
            Swal.fire({
                title: '👁️ Visualizar Produto',
                html: `
                    <div style="text-align: left; padding: 20px;">
                        <h4 style="color: var(--primary); border-bottom: 2px solid var(--primary); padding-bottom: 10px;">
                            ${p.nome}
                        </h4>
                        <div class="row g-3 mt-3">
                            <div class="col-6">
                                <p><strong>Marca:</strong> ${p.marca || '-'}</p>
                                <p><strong>SKU:</strong> ${p.sku}</p>
                                <p><strong>Categoria:</strong> ${p.categoria}</p>
                            </div>
                            <div class="col-6">
                                <p><strong>Preço:</strong> <span style="color: var(--success); font-size: 1.5rem;">R$ ${p.preco.toFixed(2)}</span></p>
                                <p><strong>Custo:</strong> R$ ${p.custo.toFixed(2)}</p>
                                <p><strong>Estoque:</strong> <span class="badge ${p.estoque > p.estoque_minimo ? 'success' : 'warning'}">${p.estoque} un.</span></p>
                                <p><strong>Estoque Mínimo:</strong> ${p.estoque_minimo} un.</p>
                            </div>
                        </div>
                    </div>
                `,
                confirmButtonText: 'Fechar',
                width: '600px'
            });
        }
    } catch (e) {
        Swal.fire('Erro', 'Não foi possível carregar o produto', 'error');
    }
}

// Exportar funções globalmente
window.showModalProfissionalMelhorado = showModalProfissionalMelhorado;
window.previewFotoProfissional = previewFotoProfissional;
window.adicionarAssistente = adicionarAssistente;
window.removerAssistente = removerAssistente;
window.loadEstoqueMelhorado = loadEstoqueMelhorado;
window.addEntradaEstoque = addEntradaEstoque;
window.addSaidaEstoque = addSaidaEstoque;
window.aprovarMovimentacao = aprovarMovimentacao;
window.reprovarMovimentacao = reprovarMovimentacao;
window.aprovarTodas = aprovarTodas;
window.reprovarTodas = reprovarTodas;
window.loadProdutosCriticos = loadProdutosCriticos;
window.ajustarEstoque = ajustarEstoque;
window.setupBuscaUniversal = setupBuscaUniversal;
window.visualizarServico = visualizarServico;
window.visualizarProduto = visualizarProduto;
window.assinarPlano = assinarPlano;

// ========== COMUNIDADE - ASSINATURA DE PLANOS ==========

async function assinarPlano(plano) {
    const planosInfo = {
        'vivencia': {
            nome: 'Vivência 🥉',
            valor: 'R$ 1.170,00 (3x R$ 390)',
            beneficios: '1 corte/mês, 5% desconto, Acesso à comunidade, Agendamento prioritário'
        },
        'imersao': {
            nome: 'Imersão 🥈',
            valor: 'R$ 2.340,00 (6x R$ 390)',
            beneficios: '6 cortes, 10% desconto, Cashback 3%, Brinde exclusivo, Agendamento VIP'
        },
        'conexao': {
            nome: 'Conexão 🥇',
            valor: 'R$ 4.680,00 (12x R$ 390)',
            beneficios: '12 cortes, 15% desconto, Cashback 5%, Kit boas-vindas, Acesso VIP total, Eventos exclusivos'
        }
    };

    const planoInfo = planosInfo[plano];

    const result = await Swal.fire({
        title: `✨ Assinar ${planoInfo.nome}`,
        html: `
            <div style="text-align: left; padding: 20px;">
                <div style="background: linear-gradient(135deg, rgba(124,58,237,0.1), rgba(236,72,153,0.1)); padding: 20px; border-radius: 15px; margin-bottom: 20px;">
                    <h3 style="color: var(--primary); margin: 0 0 10px 0;">💰 Investimento</h3>
                    <p style="font-size: 1.5rem; font-weight: 900; margin: 0;">${planoInfo.valor}</p>
                </div>

                <div style="margin-bottom: 20px;">
                    <h4 style="color: var(--primary);">📋 Benefícios Inclusos:</h4>
                    <p style="color: var(--text-secondary);">${planoInfo.beneficios}</p>
                </div>

                <div class="mb-3">
                    <label class="fw-bold">Nome Completo do Cliente *</label>
                    <input type="text" id="assinatura-nome" class="form-control" placeholder="Nome completo">
                </div>

                <div class="mb-3">
                    <label class="fw-bold">CPF *</label>
                    <input type="text" id="assinatura-cpf" class="form-control" placeholder="000.000.000-00" maxlength="14">
                </div>

                <div class="mb-3">
                    <label class="fw-bold">Email</label>
                    <input type="email" id="assinatura-email" class="form-control" placeholder="email@exemplo.com">
                </div>

                <div class="mb-3">
                    <label class="fw-bold">Telefone</label>
                    <input type="text" id="assinatura-telefone" class="form-control" placeholder="(00) 00000-0000">
                </div>

                <div class="mb-3">
                    <label class="fw-bold">Forma de Pagamento</label>
                    <select id="assinatura-pagamento" class="form-select">
                        <option value="Pix">Pix</option>
                        <option value="Cartão de Crédito">Cartão de Crédito</option>
                        <option value="Cartão de Débito">Cartão de Débito</option>
                        <option value="Dinheiro">Dinheiro</option>
                    </select>
                </div>
            </div>
        `,
        width: '700px',
        showCancelButton: true,
        confirmButtonText: '✅ Confirmar Assinatura',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#7C3AED',
        preConfirm: () => {
            const nome = document.getElementById('assinatura-nome').value.trim();
            const cpf = document.getElementById('assinatura-cpf').value.trim();
            const email = document.getElementById('assinatura-email').value.trim();
            const telefone = document.getElementById('assinatura-telefone').value.trim();
            const pagamento = document.getElementById('assinatura-pagamento').value;

            if (!nome || !cpf) {
                Swal.showValidationMessage('Nome e CPF são obrigatórios');
                return false;
            }

            return {nome, cpf, email, telefone, pagamento};
        }
    });

    if (result.isConfirmed && result.value) {
        Swal.fire({
            icon: 'success',
            title: '🎉 Assinatura Confirmada!',
            html: `
                <p><strong>${result.value.nome}</strong> foi cadastrado no plano <strong>${planoInfo.nome}</strong>!</p>
                <p>Em breve você receberá um email com todos os detalhes.</p>
                <p style="color: var(--success); font-weight: 700; margin-top: 20px;">Bem-vindo à Comunidade BIOMA! 🌿</p>
            `,
            timer: 4000,
            showConfirmButton: false
        });

        // Aqui você pode adicionar lógica para salvar a assinatura no banco de dados
        console.log('Nova assinatura:', {plano, ...result.value});
    }
}

// ========== RELATÓRIOS AVANÇADOS ==========

async function loadRelatoriosAvancados() {
    console.log('🔄 Carregando relatórios avançados...');

    // Chamar a função original de relatórios
    if (typeof loadRelatorios === 'function') {
        await loadRelatorios();
    }

    // Carregar novos gráficos
    await loadGraficoEstoque();
    await loadGraficoVendasCategoria();
    await loadGraficoFaturamentoProfissional();
    await loadMapaCalorSemanal();
}

async function loadGraficoEstoque() {
    try {
        const res = await fetch('/api/estoque/stats', {credentials: 'include'});
        const data = await res.json();

        if (data.success && data.stats) {
            const ctx = document.getElementById('chartEstoque');
            if (!ctx) return;

            // Destruir gráfico anterior se existir
            if (window.chartEstoque) {
                window.chartEstoque.destroy();
            }

            window.chartEstoque = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Em Estoque', 'Em Falta', 'Zerados'],
                    datasets: [{
                        data: [
                            data.stats.total_produtos - data.stats.produtos_baixo - data.stats.produtos_zerados,
                            data.stats.produtos_baixo,
                            data.stats.produtos_zerados
                        ],
                        backgroundColor: [
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(245, 158, 11, 0.8)',
                            'rgba(239, 68, 68, 0.8)'
                        ],
                        borderColor: [
                            'rgba(16, 185, 129, 1)',
                            'rgba(245, 158, 11, 1)',
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
                            position: 'bottom',
                            labels: {
                                font: {
                                    size: 12,
                                    weight: 'bold'
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.label + ': ' + context.parsed + ' produtos';
                                }
                            }
                        }
                    }
                }
            });
        }
    } catch (e) {
        console.error('Erro ao carregar gráfico de estoque:', e);
    }
}

async function loadGraficoVendasCategoria() {
    try {
        const res = await fetch('/api/orcamentos', {credentials: 'include'});
        const data = await res.json();

        if (data.success && data.orcamentos) {
            const aprovados = data.orcamentos.filter(o => o.status === 'Aprovado');

            // Agrupar por categoria de serviço
            const categorias = {};
            aprovados.forEach(orc => {
                (orc.servicos || []).forEach(s => {
                    const cat = s.categoria || 'Outros';
                    if (!categorias[cat]) categorias[cat] = 0;
                    categorias[cat] += s.total || 0;
                });
            });

            const ctx = document.getElementById('chartVendasCategoria');
            if (!ctx) return;

            if (window.chartVendasCategoria) {
                window.chartVendasCategoria.destroy();
            }

            const labels = Object.keys(categorias);
            const valores = Object.values(categorias);

            window.chartVendasCategoria = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Faturamento por Categoria (R$)',
                        data: valores,
                        backgroundColor: 'rgba(124, 58, 237, 0.8)',
                        borderColor: 'rgba(124, 58, 237, 1)',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return 'R$ ' + value.toFixed(0);
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }
    } catch (e) {
        console.error('Erro ao carregar gráfico de vendas por categoria:', e);
    }
}

async function loadGraficoFaturamentoProfissional() {
    try {
        // Buscar orçamentos e profissionais
        const [orcRes, profRes] = await Promise.all([
            fetch('/api/orcamentos', {credentials: 'include'}),
            fetch('/api/profissionais', {credentials: 'include'})
        ]);

        const orcData = await orcRes.json();
        const profData = await profRes.json();

        if (orcData.success && profData.success) {
            const aprovados = orcData.orcamentos.filter(o => o.status === 'Aprovado');
            const profissionais = profData.profissionais || [];

            // Calcular comissões por profissional
            const faturamentoPorProf = {};

            profissionais.forEach(p => {
                faturamentoPorProf[p.nome] = 0;
            });

            aprovados.forEach(orc => {
                (orc.servicos || []).forEach(s => {
                    if (s.profissional_nome && faturamentoPorProf.hasOwnProperty(s.profissional_nome)) {
                        faturamentoPorProf[s.profissional_nome] += (s.total || 0);
                    }
                });
            });

            const ctx = document.getElementById('chartFaturamentoProfissional');
            if (!ctx) return;

            if (window.chartFaturamentoProfissional) {
                window.chartFaturamentoProfissional.destroy();
            }

            // Pegar top 5
            const sorted = Object.entries(faturamentoPorProf).sort((a, b) => b[1] - a[1]).slice(0, 5);
            const labels = sorted.map(s => s[0]);
            const valores = sorted.map(s => s[1]);

            window.chartFaturamentoProfissional = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Faturamento (R$)',
                        data: valores,
                        backgroundColor: [
                            'rgba(124, 58, 237, 0.8)',
                            'rgba(236, 72, 153, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(245, 158, 11, 0.8)',
                            'rgba(59, 130, 246, 0.8)'
                        ],
                        borderColor: [
                            'rgba(124, 58, 237, 1)',
                            'rgba(236, 72, 153, 1)',
                            'rgba(16, 185, 129, 1)',
                            'rgba(245, 158, 11, 1)',
                            'rgba(59, 130, 246, 1)'
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return 'R$ ' + value.toFixed(0);
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.label + ': R$ ' + context.parsed.x.toFixed(2);
                                }
                            }
                        }
                    }
                }
            });
        }
    } catch (e) {
        console.error('Erro ao carregar gráfico de faturamento por profissional:', e);
    }
}

async function loadMapaCalorSemanal() {
    try {
        const res = await fetch('/api/orcamentos', {credentials: 'include'});
        const data = await res.json();

        if (data.success && data.orcamentos) {
            const aprovados = data.orcamentos.filter(o => o.status === 'Aprovado');

            // Agrupar por dia da semana
            const diasSemana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
            const vendas = [0, 0, 0, 0, 0, 0, 0];

            aprovados.forEach(orc => {
                const data = new Date(orc.created_at);
                const dia = data.getDay();
                vendas[dia] += orc.total_final || 0;
            });

            const ctx = document.getElementById('chartMapaCalor');
            if (!ctx) return;

            if (window.chartMapaCalor) {
                window.chartMapaCalor.destroy();
            }

            // Encontrar max para gradiente
            const maxVenda = Math.max(...vendas);

            window.chartMapaCalor = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: diasSemana,
                    datasets: [{
                        label: 'Faturamento por Dia da Semana (R$)',
                        data: vendas,
                        backgroundColor: vendas.map(v => {
                            const intensidade = maxVenda > 0 ? v / maxVenda : 0;
                            return `rgba(239, 68, 68, ${0.3 + intensidade * 0.7})`;
                        }),
                        borderColor: 'rgba(239, 68, 68, 1)',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return 'R$ ' + value.toFixed(0);
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return 'Faturamento: R$ ' + context.parsed.y.toFixed(2);
                                }
                            }
                        }
                    }
                }
            });
        }
    } catch (e) {
        console.error('Erro ao carregar mapa de calor semanal:', e);
    }
}

// Exportar função
window.loadRelatoriosAvancados = loadRelatoriosAvancados;

console.log('✅ BIOMA Melhorias v3.9 - Estoque Avançado + Comunidade + Relatórios carregadas com sucesso!');
