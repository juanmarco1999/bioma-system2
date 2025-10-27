# 📋 PLANO DE MELHORIAS COMPLETO - BIOMA v3.7

**Data**: 26 de Outubro de 2025
**Status**: Sistema funcionando - Pronto para melhorias
**Prioridade**: Organizada por impacto e urgência

---

## 🎯 RESUMO EXECUTIVO

**Total de melhorias solicitadas**: 19 áreas principais + 60+ sub-tarefas

**Categorização por urgência**:
- 🔴 **CRÍTICO** (Não funciona / Carregamento infinito): 15 itens
- 🟡 **ALTA** (Funciona mas precisa melhorar): 25 itens
- 🟢 **MÉDIA** (Melhorias de UX/UI): 20 itens

**Estimativa total**: 40-60 horas de desenvolvimento

---

## 🔴 PRIORIDADE CRÍTICA - Não Funciona

### 1. Sistema de Auto-Atualização (GLOBAL) ⭐⭐⭐⭐⭐
**Afeta**: Dashboard, Comissões, Financeiro, Estoque, todas as abas
**Problema**: Usuário precisa atualizar manualmente
**Solução**: WebSocket ou polling a cada 30 segundos

**Implementação**:
```javascript
// Auto-refresh system
setInterval(() => {
    const activeSection = document.querySelector('.content-section.active');
    const sectionId = activeSection?.id;

    if (sectionId === 'section-dashboard') loadDashboardData();
    if (sectionId === 'section-financeiro') loadFinanceiroData();
    // ... outras seções
}, 30000); // 30 segundos
```

**Arquivos afetados**:
- `templates/index.html` (adicionar JavaScript global)
- Todas as funções `load*` existentes

**Estimativa**: 3-4 horas

---

### 2. ABA FINANCEIRO - Carregamento Infinito (CRÍTICO) 🔴
**Item 7.1**: Todas as sub-abas com loading infinito

**Diagnóstico necessário**:
- [ ] Verificar se API `/api/financeiro/*` existe no backend
- [ ] Verificar se há erros no console do navegador
- [ ] Verificar logs do servidor

**Solução**:
1. Criar rotas faltantes no backend
2. Corrigir queries MongoDB
3. Adicionar tratamento de erro no frontend

**Estimativa**: 6-8 horas

---

### 3. ABA COMISSÕES - Carregamento Infinito (CRÍTICO) 🔴
**Item 6.1**: Loading infinito + dados incoerentes

**Problema provável**: API não retorna dados ou query MongoDB incorreta

**Solução**:
```python
@bp.route('/api/comissoes/pendentes')
def get_comissoes_pendentes():
    try:
        # Buscar orçamentos aprovados com comissões não pagas
        pipeline = [
            {'$match': {'status': 'aprovado', 'comissao_paga': {'$ne': True}}},
            {'$lookup': {
                'from': 'profissionais',
                'localField': 'profissional_id',
                'foreignField': '_id',
                'as': 'profissional_info'
            }},
            # ... agregação completa
        ]
        comissoes = list(db.orcamentos.aggregate(pipeline))
        return jsonify({'success': True, 'comissoes': comissoes})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
```

**Estimativa**: 4-5 horas

---

### 4. ABA ESTOQUE - Funcionalidades em Branco (CRÍTICO) 🔴
**Item 8.1**: Várias funcionalidades não funcionam
**Item 8.4**: Botões de relatório não funcionam
**Item 8.5**: Excel exportado com erro

**Soluções**:

#### 8.5 - Excel com erro:
```python
from io import BytesIO
import pandas as pd

@bp.route('/api/estoque/exportar/excel')
def exportar_estoque_excel():
    try:
        produtos = list(db.produtos.find())

        # Converter para DataFrame
        df = pd.DataFrame(produtos)
        df = df.drop('_id', axis=1)  # Remover ObjectId

        # Criar Excel em memória
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Estoque', index=False)

        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'estoque_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
```

**Dependência adicional**: `openpyxl` ou `xlsxwriter` no requirements.txt

**Estimativa**: 5-6 horas

---

### 5. ABA AGENDAMENTOS - Erro ao Carregar (CRÍTICO) 🔴
**Item 9.1**: Erro ao carregar agendamentos
**Item 9.3**: Dados "Desconhecido"

**Problema**: Provavelmente falta populate de dados relacionados

**Solução**:
```python
@bp.route('/api/agendamentos/mes')
def get_agendamentos_mes():
    try:
        # Usar aggregation para fazer JOIN
        pipeline = [
            {'$match': {'data': {'$gte': inicio_mes, '$lt': fim_mes}}},
            {'$lookup': {
                'from': 'clientes',
                'localField': 'cliente_id',
                'foreignField': '_id',
                'as': 'cliente'
            }},
            {'$lookup': {
                'from': 'profissionais',
                'localField': 'profissional_id',
                'foreignField': '_id',
                'as': 'profissional'
            }},
            {'$lookup': {
                'from': 'servicos',
                'localField': 'servico_id',
                'foreignField': '_id',
                'as': 'servico'
            }},
            {'$unwind': {'path': '$cliente', 'preserveNullAndEmptyArrays': True}},
            {'$unwind': {'path': '$profissional', 'preserveNullAndEmptyArrays': True}},
            {'$unwind': {'path': '$servico', 'preserveNullAndEmptyArrays': True}}
        ]
        agendamentos = list(db.agendamentos.aggregate(pipeline))
        return jsonify({'success': True, 'agendamentos': agendamentos})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
```

**Estimativa**: 4-5 horas

---

### 6. ABA RELATÓRIOS - Mapa de Calor Infinito (CRÍTICO) 🔴
**Item 4.2**: Mapa de calor com loading infinito desde o início

**Problema**: Provavelmente dados não estruturados corretamente

**Solução**:
```javascript
async function loadMapaCalor() {
    try {
        const res = await fetch('/api/relatorios/mapa-calor', {credentials: 'include'});
        const data = await res.json();

        if (!data.success) throw new Error(data.message);

        // Estrutura esperada: { data: '2025-10-26', count: 15 }
        const calendarData = data.mapa.map(item => ({
            date: item.data,
            value: item.count
        }));

        // Renderizar com biblioteca de heatmap (cal-heatmap ou similar)
        new CalHeatmap().paint({
            itemSelector: '#mapaCalor',
            domain: 'month',
            subDomain: 'day',
            data: calendarData,
            // ... configurações
        });
    } catch (error) {
        console.error('Erro mapa de calor:', error);
        showError('Não foi possível carregar o mapa de calor');
    }
}
```

**Dependência**: Biblioteca `cal-heatmap` via CDN

**Estimativa**: 3-4 horas

---

### 7. ABA CLIENTES - Faturamento Não Funciona (CRÍTICO) 🔴
**Item 11.2**: Sub-aba faturamento não funciona

**Solução**:
```python
@bp.route('/api/clientes/<cliente_id>/faturamento')
def get_cliente_faturamento(cliente_id):
    try:
        from bson import ObjectId

        # Agregar todos os orçamentos aprovados do cliente
        pipeline = [
            {'$match': {
                'cliente_id': ObjectId(cliente_id),
                'status': 'aprovado'
            }},
            {'$group': {
                '_id': None,
                'total_faturado': {'$sum': '$valor_total'},
                'quantidade_orcamentos': {'$sum': 1},
                'ticket_medio': {'$avg': '$valor_total'}
            }},
            {'$project': {
                '_id': 0,
                'total_faturado': 1,
                'quantidade_orcamentos': 1,
                'ticket_medio': {'$round': ['$ticket_medio', 2]}
            }}
        ]

        resultado = list(db.orcamentos.aggregate(pipeline))
        faturamento = resultado[0] if resultado else {
            'total_faturado': 0,
            'quantidade_orcamentos': 0,
            'ticket_medio': 0
        }

        return jsonify({'success': True, 'faturamento': faturamento})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
```

**Estimativa**: 2-3 horas

---

## 🟡 PRIORIDADE ALTA - Funciona mas Precisa Melhorar

### 8. Logo da Empresa - Redimensionamento (ALTA) 🟡
**Item 0**: Logo com fundo roxo e área muito grande
**Item 19.2**: Melhorar renderização do logo

**Problema**: CSS da `.sidebar-logo` está com tamanho fixo

**Solução**:
```css
.sidebar-logo {
    min-height: auto !important; /* Era 400px */
    max-height: 200px !important; /* Reduzir de 400px */
    padding: 15px 8px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    background: transparent !important; /* Remover fundo roxo */
    background-size: contain !important;
    background-position: center !important;
    background-repeat: no-repeat !important;
}

.sidebar-logo img {
    max-width: 100%;
    max-height: 150px; /* Limitar altura */
    object-fit: contain;
    background: transparent;
}

.sidebar-logo h1,
.sidebar-logo p {
    display: none; /* Esconder texto quando tem logo */
}

.sidebar-logo.no-logo h1,
.sidebar-logo.no-logo p {
    display: block; /* Mostrar texto quando não tem logo */
}
```

**Arquivo**: `templates/index.html` (seção CSS)

**Estimativa**: 1 hora

---

### 9. Orçamento - Coluna Pagamento "[object Object]" (ALTA) 🟡
**Item 1.2**: Coluna pagamento mostrando "[object Object]"

**Problema**: JavaScript não está convertendo objeto para string

**Solução**:
```javascript
// Ao renderizar tabela de orçamentos
function renderOrcamentosTable(orcamentos) {
    const tbody = document.getElementById('orcamentosTableBody');
    tbody.innerHTML = '';

    orcamentos.forEach(orc => {
        const tr = document.createElement('tr');

        // ANTES (errado):
        // const pagamento = orc.pagamento; // [object Object]

        // DEPOIS (correto):
        const pagamento = orc.forma_pagamento ||
                          orc.pagamento?.forma ||
                          orc.pagamento?.tipo ||
                          'Não especificado';

        tr.innerHTML = `
            <td>${formatarData(orc.created_at)}</td>
            <td>${orc.cliente_nome}</td>
            <td>${formatarMoeda(orc.valor_total)}</td>
            <td>${pagamento}</td>
            <td><span class="badge ${getBadgeClass(orc.status)}">${orc.status}</span></td>
            <td>...</td>
        `;
        tbody.appendChild(tr);
    });
}
```

**Estimativa**: 30 minutos

---

### 10. Contrato PDF - Layout Melhorado (ALTA) 🟡
**Item 1.3**: Contrato com layout ruim
**Item 3.2**: Evitar páginas em branco

**Solução**: Criar template HTML otimizado para PDF

```python
from weasyprint import HTML, CSS

@bp.route('/api/contratos/<contrato_id>/pdf')
def gerar_contrato_pdf(contrato_id):
    try:
        contrato = db.contratos.find_one({'_id': ObjectId(contrato_id)})
        if not contrato:
            return jsonify({'success': False, 'message': 'Contrato não encontrado'})

        # Template HTML otimizado
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 11pt;
                    line-height: 1.4;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 3px solid #7C3AED;
                    padding-bottom: 15px;
                }}
                .clausula {{
                    margin: 15px 0;
                    page-break-inside: avoid;
                }}
                .assinatura {{
                    margin-top: 60px;
                    display: flex;
                    justify-content: space-between;
                    page-break-inside: avoid;
                }}
                .campo-assinatura {{
                    text-align: center;
                    border-top: 2px solid #000;
                    padding-top: 5px;
                    min-width: 200px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>CONTRATO DE PRESTAÇÃO DE SERVIÇOS</h1>
                <p>Nº {contrato['numero']}</p>
            </div>

            <div class="partes">
                <p><strong>CONTRATANTE:</strong> {contrato['cliente_nome']}</p>
                <p><strong>CONTRATADA:</strong> BIOMA Uberaba</p>
            </div>

            <div class="clausulas">
                <div class="clausula">
                    <h3>CLÁUSULA 1ª - DO OBJETO</h3>
                    <p>{contrato['clausula_objeto']}</p>
                </div>

                <div class="clausula">
                    <h3>CLÁUSULA 2ª - DO VALOR</h3>
                    <p>O valor total do contrato é de R$ {contrato['valor_total']:.2f}</p>
                </div>

                <!-- Mais cláusulas -->
            </div>

            <div class="assinatura">
                <div class="campo-assinatura">
                    <p>_______________________________</p>
                    <p><strong>Contratante</strong></p>
                    <p>{contrato['cliente_nome']}</p>
                </div>
                <div class="campo-assinatura">
                    <p>_______________________________</p>
                    <p><strong>Contratada</strong></p>
                    <p>BIOMA Uberaba</p>
                </div>
            </div>
        </body>
        </html>
        '''

        # Gerar PDF
        pdf = HTML(string=html_content).write_pdf()

        return send_file(
            BytesIO(pdf),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'contrato_{contrato["numero"]}.pdf'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
```

**Dependência**: `weasyprint` no requirements.txt

**Estimativa**: 4-5 horas

---

### 11. Múltiplos Produtos/Serviços no Orçamento (ALTA) 🟡
**Item 1.5**: Possibilidade de incluir múltiplos produtos/serviços

**Problema**: Frontend limita a 1 produto/serviço

**Solução**:
```javascript
let produtosAdicionados = [];
let servicosAdicionados = [];

function adicionarProduto() {
    const produtoId = document.getElementById('produtoSelect').value;
    const quantidade = parseInt(document.getElementById('quantidadeProduto').value);

    // Buscar produto no cache ou API
    const produto = produtos.find(p => p._id === produtoId);

    produtosAdicionados.push({
        produto_id: produtoId,
        nome: produto.nome,
        quantidade: quantidade,
        preco_unitario: produto.preco_venda,
        total: produto.preco_venda * quantidade
    });

    renderProdutosAdicionados();
    calcularTotalOrcamento();
}

function renderProdutosAdicionados() {
    const tbody = document.getElementById('produtosAdicionadosBody');
    tbody.innerHTML = '';

    produtosAdicionados.forEach((prod, index) => {
        tbody.innerHTML += `
            <tr>
                <td>${prod.nome}</td>
                <td>${prod.quantidade}</td>
                <td>${formatarMoeda(prod.preco_unitario)}</td>
                <td>${formatarMoeda(prod.total)}</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="removerProduto(${index})">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
}

function salvarOrcamento() {
    const orcamento = {
        cliente_id: document.getElementById('clienteSelect').value,
        produtos: produtosAdicionados,
        servicos: servicosAdicionados,
        valor_total: calcularTotalOrcamento(),
        // ... outros campos
    };

    fetch('/api/orcamentos', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        credentials: 'include',
        body: JSON.stringify(orcamento)
    });
}
```

**Estimativa**: 3-4 horas

---

### 12. Múltiplos Profissionais por Serviço (ALTA) 🟡
**Item 1.6**: Escolher múltiplos profissionais/assistentes

**Solução**: Sistema de multicomissão (item 12.1 combinado)

```javascript
let profissionaisServico = [];

function adicionarProfissionalServico() {
    const profId = document.getElementById('profissionalSelect').value;
    const tipo = document.getElementById('tipoProfissional').value; // 'principal' ou 'assistente'
    const percentualComissao = parseFloat(document.getElementById('percentualComissao').value);

    profissionaisServico.push({
        profissional_id: profId,
        nome: profissionais.find(p => p._id === profId).nome,
        tipo: tipo,
        percentual_comissao: percentualComissao
    });

    renderProfissionaisServico();
}

// Backend - Calcular comissões
@bp.route('/api/orcamentos/<orcamento_id>/calcular-comissoes')
def calcular_comissoes(orcamento_id):
    orc = db.orcamentos.find_one({'_id': ObjectId(orcamento_id)})

    comissoes = []
    for servico in orc['servicos']:
        for prof in servico['profissionais']:
            if prof['tipo'] == 'principal':
                valor_comissao = servico['total'] * (prof['percentual_comissao'] / 100)
            else:  # assistente - percentual da comissão do principal
                principal = next(p for p in servico['profissionais'] if p['tipo'] == 'principal')
                valor_principal = servico['total'] * (principal['percentual_comissao'] / 100)
                valor_comissao = valor_principal * (prof['percentual_comissao'] / 100)

            comissoes.append({
                'profissional_id': prof['profissional_id'],
                'nome': prof['nome'],
                'tipo': prof['tipo'],
                'valor': valor_comissao
            })

    return jsonify({'success': True, 'comissoes': comissoes})
```

**Estimativa**: 5-6 horas

---

## 🟢 PRIORIDADE MÉDIA - Melhorias de UX/UI

### 13. Navegação Direta ao Editar Orçamento (MÉDIA) 🟢
**Item 2.1**: Ir direto para orçamento e sub-aba correta

**Solução**:
```javascript
function editarOrcamento(orcamentoId) {
    // Navegar para aba principal
    switchTab('novo-orcamento');

    // Aguardar aba carregar
    setTimeout(() => {
        // Navegar para sub-aba "editar"
        switchSubTab('novo-orcamento', 'editar');

        // Carregar dados do orçamento
        loadOrcamentoParaEdicao(orcamentoId);
    }, 300);
}
```

**Estimativa**: 1 hora

---

### 14. Melhorar Detalhamento de Visualização (MÉDIA) 🟢
**Item 1.4, 2.2, 3.1, 12.2**: Melhorar modals de visualização

**Solução**: Template modal completo

```javascript
function mostrarDetalhesOrcamento(orcamentoId) {
    fetch(`/api/orcamentos/${orcamentoId}`, {credentials: 'include'})
        .then(res => res.json())
        .then(data => {
            const orc = data.orcamento;

            const modalHtml = `
                <div class="modal-detalhes">
                    <h2>Orçamento #${orc.numero}</h2>

                    <div class="secao">
                        <h3><i class="bi bi-person"></i> Cliente</h3>
                        <p><strong>Nome:</strong> ${orc.cliente.nome}</p>
                        <p><strong>CPF:</strong> ${orc.cliente.cpf}</p>
                        <p><strong>Telefone:</strong> ${orc.cliente.telefone}</p>
                    </div>

                    <div class="secao">
                        <h3><i class="bi bi-box"></i> Produtos</h3>
                        <table>
                            <thead>
                                <tr><th>Produto</th><th>Qtd</th><th>Preço Unit.</th><th>Total</th></tr>
                            </thead>
                            <tbody>
                                ${orc.produtos.map(p => `
                                    <tr>
                                        <td>${p.nome}</td>
                                        <td>${p.quantidade}</td>
                                        <td>${formatarMoeda(p.preco_unitario)}</td>
                                        <td>${formatarMoeda(p.total)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>

                    <div class="secao">
                        <h3><i class="bi bi-cash"></i> Resumo Financeiro</h3>
                        <p><strong>Subtotal:</strong> ${formatarMoeda(orc.subtotal)}</p>
                        <p><strong>Desconto:</strong> ${orc.desconto_percentual}% (${formatarMoeda(orc.desconto_valor)})</p>
                        <p><strong>Total:</strong> <span class="total-destaque">${formatarMoeda(orc.valor_total)}</span></p>
                        <p><strong>Forma de Pagamento:</strong> ${orc.forma_pagamento}</p>
                    </div>

                    <div class="acoes-modal">
                        <button class="btn btn-primary" onclick="enviarPorEmail('${orcamentoId}')">
                            <i class="bi bi-envelope"></i> Enviar por E-mail
                        </button>
                        <button class="btn btn-success" onclick="enviarPorWhatsApp('${orcamentoId}')">
                            <i class="bi bi-whatsapp"></i> Enviar WhatsApp
                        </button>
                        <button class="btn btn-secondary" onclick="fecharModal()">
                            Fechar
                        </button>
                    </div>
                </div>
            `;

            Swal.fire({
                html: modalHtml,
                width: '900px',
                showConfirmButton: false
            });
        });
}
```

**Estimativa**: 4-5 horas (para todos os modais)

---

### 15. Notificações E-mail e WhatsApp (MÉDIA) 🟢
**Item 9.2, 10.2, 11.4, 12.3**: Sistema de notificações

**Solução Backend**:
```python
# E-mail via MailerSend
import requests

@bp.route('/api/notificacoes/email', methods=['POST'])
def enviar_email():
    data = request.json

    payload = {
        "from": {
            "email": "noreply@biomauberaba.com.br",
            "name": "BIOMA Uberaba"
        },
        "to": [{
            "email": data['destinatario_email'],
            "name": data['destinatario_nome']
        }],
        "subject": data['assunto'],
        "html": data['conteudo_html'],
        "text": data['conteudo_texto']
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('MAILERSEND_API_KEY')}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://api.mailersend.com/v1/email",
        json=payload,
        headers=headers
    )

    return jsonify({
        'success': response.status_code == 202,
        'message': 'E-mail enviado com sucesso' if response.status_code == 202 else 'Erro ao enviar'
    })

# WhatsApp (simulado)
@bp.route('/api/notificacoes/whatsapp', methods=['POST'])
def enviar_whatsapp():
    data = request.json

    # Por enquanto, apenas retornar URL de compartilhamento
    numero = data['telefone'].replace('+', '').replace('-', '').replace(' ', '')
    mensagem = urllib.parse.quote(data['mensagem'])

    whatsapp_url = f"https://wa.me/{numero}?text={mensagem}"

    return jsonify({
        'success': True,
        'url': whatsapp_url,
        'message': 'Link do WhatsApp gerado'
    })
```

**Frontend**:
```javascript
function enviarPorWhatsApp(orcamentoId) {
    fetch(`/api/orcamentos/${orcamentoId}/whatsapp-link`, {credentials: 'include'})
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                window.open(data.url, '_blank');
                Swal.fire('Sucesso!', 'WhatsApp aberto em nova aba', 'success');
            }
        });
}
```

**Estimativa**: 6-8 horas

---

### 16. Anamnese e Prontuário Associados (MÉDIA) 🟢
**Item 11.1, 11.3**: Associar documentos aos clientes

**Solução**:
```python
# Modelo de dados
{
    "_id": ObjectId("..."),
    "cliente_id": ObjectId("..."),
    "tipo": "anamnese",  # ou "prontuario"
    "data": datetime.now(),
    "conteudo": {
        "campo1": "valor1",
        # ... campos específicos
    },
    "anexos": [
        {
            "nome": "anamnese_fisica.jpg",
            "url": "s3://...",
            "tipo": "imagem"
        }
    ],
    "created_by": "usuario_id",
    "created_at": datetime.now()
}

@bp.route('/api/clientes/<cliente_id>/documentos')
def get_documentos_cliente(cliente_id):
    documentos = list(db.documentos_medicos.find({
        'cliente_id': ObjectId(cliente_id)
    }).sort('created_at', -1))

    return jsonify({
        'success': True,
        'anamneses': [d for d in documentos if d['tipo'] == 'anamnese'],
        'prontuarios': [d for d in documentos if d['tipo'] == 'prontuario']
    })
```

**Estimativa**: 5-6 horas

---

### 17. Melhorar Gráficos Dashboard (MÉDIA) 🟢
**Item 4.1**: Melhorar gráficos da aba resumo

**Solução**: Usar Chart.js com configuração avançada

```javascript
function criarGraficoReceita() {
    const ctx = document.getElementById('chartReceita').getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
            datasets: [{
                label: 'Receita 2025',
                data: receitaMensal,
                borderColor: '#7C3AED',
                backgroundColor: 'rgba(124, 58, 237, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 5,
                pointHoverRadius: 7
            }, {
                label: 'Meta',
                data: metaMensal,
                borderColor: '#10B981',
                borderDash: [5, 5],
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            return `${context.dataset.label}: ${formatarMoeda(context.parsed.y)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (value) => formatarMoeda(value)
                    }
                }
            }
        }
    });
}
```

**Estimativa**: 3-4 horas

---

### 18. Sistema de Fila Inteligente (MÉDIA) 🟢
**Item 10.1**: Sistema de automação completo ligado ao calendário

**Solução**: Sistema de priorização automática

```python
@bp.route('/api/fila/processar')
def processar_fila():
    """Processar fila e alocar automaticamente em horários disponíveis"""

    # Buscar pessoas na fila ordenadas por prioridade
    fila = list(db.fila.find({'status': 'aguardando'}).sort([
        ('prioridade', -1),  # Alta prioridade primeiro
        ('created_at', 1)    # FIFO para mesma prioridade
    ]))

    for item in fila:
        # Buscar horários disponíveis do profissional preferido
        horarios = db.agendamentos.find({
            'profissional_id': item['profissional_id'],
            'data': {'$gte': datetime.now()},
            'status': 'disponivel'
        }).sort('data', 1).limit(10)

        for horario in horarios:
            # Verificar se cliente está disponível
            conflito = db.agendamentos.find_one({
                'cliente_id': item['cliente_id'],
                'data': horario['data'],
                'horario': horario['horario']
            })

            if not conflito:
                # Alocar agendamento
                db.agendamentos.update_one(
                    {'_id': horario['_id']},
                    {'$set': {
                        'cliente_id': item['cliente_id'],
                        'servico_id': item['servico_id'],
                        'status': 'confirmado',
                        'origem': 'fila_automatica'
                    }}
                )

                # Atualizar status na fila
                db.fila.update_one(
                    {'_id': item['_id']},
                    {'$set': {
                        'status': 'agendado',
                        'agendamento_id': horario['_id'],
                        'data_agendamento': horario['data']
                    }}
                )

                # Notificar cliente
                enviar_notificacao_agendamento(item['cliente_id'], horario)

                break

    return jsonify({'success': True, 'message': 'Fila processada'})
```

**Estimativa**: 8-10 horas

---

### 19. Melhorias de Layout e Ícones (MÉDIA) 🟢
**Item 8.3, 11, 15.1**: Melhorar layout e ícones

**Solução**: Padronizar ícones Bootstrap Icons

```javascript
const iconMapping = {
    'anamnese': 'bi-clipboard-pulse',
    'prontuario': 'bi-file-medical',
    'visualizar': 'bi-eye',
    'editar': 'bi-pencil-square',
    'deletar': 'bi-trash',
    'email': 'bi-envelope',
    'whatsapp': 'bi-whatsapp',
    'pdf': 'bi-file-pdf',
    'excel': 'bi-file-excel',
    // ... mais ícones
};

function atualizarIcones() {
    document.querySelectorAll('[data-icon]').forEach(el => {
        const iconName = el.dataset.icon;
        const iconClass = iconMapping[iconName];
        el.innerHTML = `<i class="${iconClass}"></i> ${el.dataset.label || ''}`;
    });
}
```

**Estimativa**: 2-3 horas

---

### 20. Ativar/Desativar Todos (MÉDIA) 🟢
**Item 13.1, 14.1**: Ativar/desativar todos serviços/produtos

**Solução**:
```javascript
async function toggleTodosProdutos(ativo) {
    const confirmacao = await Swal.fire({
        title: `${ativo ? 'Ativar' : 'Desativar'} TODOS os produtos?`,
        text: 'Esta ação afetará todos os produtos cadastrados',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Sim, confirmar',
        cancelButtonText: 'Cancelar'
    });

    if (confirmacao.isConfirmed) {
        const res = await fetch('/api/produtos/toggle-todos', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({ ativo: ativo })
        });

        const data = await res.json();
        if (data.success) {
            Swal.fire('Sucesso!', `${data.count} produtos ${ativo ? 'ativados' : 'desativados'}`, 'success');
            loadProdutos();
        }
    }
}

// Backend
@bp.route('/api/produtos/toggle-todos', methods=['POST'])
def toggle_todos_produtos():
    ativo = request.json.get('ativo', True)

    result = db.produtos.update_many(
        {},
        {'$set': {'ativo': ativo}}
    )

    return jsonify({
        'success': True,
        'count': result.modified_count
    })
```

**Estimativa**: 1-2 horas

---

### 21. Modo Offline (MÉDIA) 🟢
**Item 17.1**: Sistema funcional offline

**Solução**: Service Worker + IndexedDB

```javascript
// service-worker.js
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open('bioma-v3.7').then((cache) => {
            return cache.addAll([
                '/',
                '/static/css/global.css',
                '/static/js/app.js',
                // ... outros arquivos essenciais
            ]);
        })
    );
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );
});

// Registrar Service Worker
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js');
}

// Sincronizar quando voltar online
window.addEventListener('online', () => {
    sincronizarDadosOffline();
});
```

**Estimativa**: 12-15 horas (complexo)

---

### 22. Tornar Auditoria Funcional (MÉDIA) 🟢
**Item 18.1**: Tornar aba auditoria funcional

**Solução**: Sistema de logging automático

```python
# Decorator para auditoria
from functools import wraps

def auditoria(acao, entidade):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Executar função original
            result = f(*args, **kwargs)

            # Registrar auditoria
            try:
                user_id = session.get('user_id')
                username = session.get('username')

                db.auditoria.insert_one({
                    'usuario_id': user_id,
                    'username': username,
                    'acao': acao,  # criar, editar, deletar, etc.
                    'entidade': entidade,  # cliente, produto, orçamento, etc.
                    'timestamp': datetime.now(),
                    'ip': request.remote_addr,
                    'detalhes': kwargs
                })
            except:
                pass  # Não falhar se auditoria falhar

            return result
        return decorated_function
    return decorator

# Usar em rotas
@bp.route('/api/produtos', methods=['POST'])
@auditoria('criar', 'produto')
def criar_produto():
    # ... lógica normal
    pass
```

**Estimativa**: 4-5 horas

---

### 23. Configurações Funcionais (MÉDIA) 🟢
**Item 19.1**: Tornar funções de configuração funcionais

**Solução**:
```python
@bp.route('/api/configuracoes', methods=['GET'])
def get_configuracoes():
    configs = db.configuracoes.find_one() or {}
    return jsonify({'success': True, 'configuracoes': configs})

@bp.route('/api/configuracoes', methods=['POST'])
def salvar_configuracoes():
    data = request.json

    db.configuracoes.update_one(
        {},
        {'$set': data},
        upsert=True
    )

    return jsonify({'success': True, 'message': 'Configurações salvas'})
```

**Estimativa**: 2-3 horas

---

## 📊 SUMÁRIO DE ESTIMATIVAS

| Categoria | Itens | Horas | Prioridade |
|-----------|-------|-------|------------|
| Sistema Auto-Atualização | 1 | 3-4h | 🔴 CRÍTICO |
| Financeiro Completo | 1 | 6-8h | 🔴 CRÍTICO |
| Comissões | 1 | 4-5h | 🔴 CRÍTICO |
| Estoque - Funcionalidades | 3 | 5-6h | 🔴 CRÍTICO |
| Agendamentos - Erro | 1 | 4-5h | 🔴 CRÍTICO |
| Relatórios - Mapa Calor | 1 | 3-4h | 🔴 CRÍTICO |
| Clientes - Faturamento | 1 | 2-3h | 🔴 CRÍTICO |
| **SUBTOTAL CRÍTICO** | **9** | **27-35h** | |
| Logo Redimensionamento | 1 | 1h | 🟡 ALTA |
| Orçamento - Pagamento | 1 | 0.5h | 🟡 ALTA |
| Contrato PDF | 1 | 4-5h | 🟡 ALTA |
| Múltiplos Produtos/Serviços | 1 | 3-4h | 🟡 ALTA |
| Múltiplos Profissionais | 1 | 5-6h | 🟡 ALTA |
| **SUBTOTAL ALTA** | **5** | **14-17h** | |
| Melhorias de UX/UI | 11 | 20-30h | 🟢 MÉDIA |
| **TOTAL GERAL** | **25** | **61-82h** | |

---

## 🎯 PLANO DE EXECUÇÃO SUGERIDO

### Sprint 1 - Correções Críticas (1 semana)
- [ ] Sistema auto-atualização global
- [ ] Financeiro - resolver carregamento infinito
- [ ] Comissões - resolver carregamento infinito
- [ ] Estoque - exportar Excel funcional

### Sprint 2 - Funcionalidades Essenciais (1 semana)
- [ ] Agendamentos - corrigir erro de carregamento
- [ ] Relatórios - mapa de calor
- [ ] Clientes - faturamento
- [ ] Orçamento - coluna pagamento

### Sprint 3 - Melhorias de Fluxo (1 semana)
- [ ] Múltiplos produtos/serviços
- [ ] Múltiplos profissionais
- [ ] Contrato PDF melhorado
- [ ] Logo redimensionamento

### Sprint 4 - Notificações e Automação (1 semana)
- [ ] Sistema de notificações (E-mail + WhatsApp)
- [ ] Fila inteligente
- [ ] Anamnese/Prontuário associados

### Sprint 5 - Polimento e UX (1 semana)
- [ ] Melhorar modals de visualização
- [ ] Melhorar gráficos
- [ ] Melhorar ícones e layout
- [ ] Configurações funcionais
- [ ] Auditoria funcional

---

## 📋 PRÓXIMOS PASSOS IMEDIATOS

1. **Confirmar prioridades** com o cliente
2. **Escolher Sprint 1** para começar
3. **Criar branch** `feature/sprint-1-criticas`
4. **Implementar item por item** testando cada um
5. **Deploy incremental** após cada melhoria funcionar

---

**Última atualização**: 26/10/2025
**Status**: Aguardando confirmação de prioridades
