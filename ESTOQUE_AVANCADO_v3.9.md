# 📦 BIOMA UBERABA v3.9 - Sistema de Estoque Avançado

## 🎯 Novas Funcionalidades Implementadas

---

## ✅ 1. Sistema de Aprovação/Reprovação de Movimentações

### Conceito
Todas as movimentações de estoque agora podem ser criadas com status **"pendente"** e precisam ser aprovadas por um gestor antes de impactar o estoque real.

### Funcionalidades

#### ✅ **Aprovação Individual**
- Botão verde (✓) ao lado de cada movimentação pendente
- Modal de confirmação antes de aprovar
- Atualiza estoque imediatamente após aprovação
- Registra quem aprovou e quando

#### ❌ **Reprovação Individual**
- Botão vermelho (✗) ao lado de cada movimentação pendente
- Campo para informar motivo da reprovação
- Não altera o estoque
- Registra quem reprovou e o motivo

#### ✅ **Aprovar TODAS as Pendentes**
- Botão "Aprovar Todas" no topo da tabela de movimentações
- Processa todas as movimentações pendentes em massa
- Mostra resumo: quantas aprovadas e quantos erros
- Validação de estoque insuficiente automática

#### ❌ **Reprovar TODAS as Pendentes**
- Botão "Reprovar Todas" no topo da tabela
- Campo para motivo de reprovação em massa
- Marca todas como reprovadas instantaneamente

### Backend ([app.py](app.py))

**Endpoints Criados:**
- `POST /api/estoque/aprovar/<movimentacao_id>` - Linhas 1357-1405
- `POST /api/estoque/reprovar/<movimentacao_id>` - Linhas 1407-1440
- `POST /api/estoque/aprovar-todos` - Linhas 1442-1494
- `POST /api/estoque/reprovar-todos` - Linhas 1496-1522

**Status de Movimentações:**
- `pendente` - Aguardando aprovação (padrão)
- `aprovado` - Aprovada e estoque atualizado
- `reprovado` - Reprovada, não atualiza estoque

---

## 📊 2. Produtos Críticos (≤30% do Mínimo)

### Conceito
Produtos com estoque extremamente baixo (30% ou menos do estoque mínimo) são destacados em uma seção especial.

### Funcionalidades
- **Cálculo automático** do percentual de estoque
- **Tabela dedicada** para produtos críticos
- **Barra de progresso visual** mostrando o nível do estoque
- **Cores dinâmicas**:
  - 🔴 Vermelho: ≤20%
  - 🟡 Amarelo: 21-30%
- **Botões rápidos**:
  - Entrada de estoque
  - Ajuste de inventário

### Backend
- `GET /api/estoque/produtos-criticos` - Linhas 1524-1552
- Usa agregação MongoDB para cálculo eficiente

---

## 🔄 3. Ajuste de Inventário

### Conceito
Ferramenta para corrigir divergências entre estoque físico (contado) e estoque no sistema.

### Funcionalidades
- **Modal intuitivo** mostrando estoque atual
- **Campo para estoque real** (contado fisicamente)
- **Cálculo automático** da diferença
- **Motivo do ajuste** obrigatório
- **Aprovação automática** (ajustes de inventário não precisam aprovação)
- **Registro detalhado** na movimentação

### Como Usar
1. Clicar em "Ajustar" em qualquer produto
2. Informar o estoque real contado
3. Informar motivo (ex: "Inventário mensal")
4. Sistema calcula diferença e atualiza

### Backend
- `POST /api/estoque/ajustar` - Linhas 1554-1600

---

## 📤 4. Saída de Estoque Melhorada

### Funcionalidades
- **Seleção de produto** via dropdown
- **Motivos pré-definidos**:
  - Venda
  - Perda
  - Avaria
  - Devolução
  - Outro (campo livre)
- **Checkbox de aprovação automática**
- **Validação de estoque** antes de aprovar

---

## 📥 5. Entrada de Estoque Melhorada

### Funcionalidades
- **Checkbox de aprovação automática**
- **Se desmarcado**: cria movimentação pendente
- **Se marcado**: atualiza estoque imediatamente
- **Feedback visual** diferenciado

---

## 📈 6. Card de Pendentes nas Estatísticas

### Funcionalidades
- **Novo card** mostrando quantidade de movimentações pendentes
- **Cor dinâmica**:
  - 🟡 Borda amarela: há pendentes
  - 🟢 Borda verde: nenhum pendente
- **Atualização em tempo real**

---

## 🎨 7. Melhorias Visuais

### Tabela de Movimentações
- **8 colunas** agora (incluindo Status e Ações)
- **Background diferenciado** para pendentes (amarelo claro)
- **Badges coloridos** para status:
  - ⏳ Amarelo: Pendente
  - ✅ Verde: Aprovado
  - ❌ Vermelho: Reprovado
- **Informações de quem aprovou/reprovou**
- **Tooltip** com motivo de reprovação ao passar o mouse

### Cards de Estatísticas
- **5 cards** agora (incluindo Pendentes)
- **Ícones melhorados**
- **Animações suaves**

---

## 📋 Fluxo de Trabalho Recomendado

### Cenário 1: Entrada de Compra
1. Funcionário recebe produtos
2. Clica em "Entrada" no produto
3. Informa quantidade e motivo
4. **Desmarca** "Aprovar automaticamente"
5. Gerente revisa na aba Estoque
6. Gerente **aprova** a entrada
7. Estoque é atualizado

### Cenário 2: Inventário Mensal
1. Funcionário conta estoque físico
2. Clica em "Ajustar" no produto
3. Informa estoque real contado
4. Sistema mostra diferença
5. Informa motivo "Inventário de Outubro/2025"
6. Sistema registra e atualiza automaticamente

### Cenário 3: Venda com Estoque
1. Funcionário vende produto
2. Clica em "Nova Saída"
3. Seleciona produto e quantidade
4. Motivo: "Venda"
5. **Marca** "Aprovar automaticamente"
6. Estoque é reduzido imediatamente

### Cenário 4: Aprovação em Massa
1. Gerente acessa aba Estoque
2. Vê 15 movimentações pendentes
3. Clica em "Aprovar Todas"
4. Confirma ação
5. Sistema processa todas de uma vez
6. Mostra resumo: "15 aprovadas, 0 erros"

---

## 🔧 Arquivos Modificados

### Backend
**[app.py](app.py:1276-1600)**
- Movimentação com status pendente/aprovado/reprovado
- 5 novos endpoints de aprovação/reprovação
- Ajuste de inventário
- Produtos críticos

### Frontend
**[bioma_melhorias.js](static/js/bioma_melhorias.js:309-886)**
- 8 novas funções:
  - `aprovarMovimentacao(id)`
  - `reprovarMovimentacao(id)`
  - `aprovarTodas()`
  - `reprovarTodas()`
  - `loadProdutosCriticos()`
  - `ajustarEstoque(produtoId, nome, estoqueAtual)`
  - `addSaidaEstoque()`
  - Melhorias em `addEntradaEstoque()`

**[index.html](templates/index.html:169-321)**
- Card de pendentes
- Tabela de produtos críticos
- Tabela de movimentações com 8 colunas
- Botões "Aprovar Todas" e "Reprovar Todas"

---

## 📊 Estatísticas e Métricas

### Dados Rastreados
- **Total de produtos** ativos
- **Produtos em falta** (≤ mínimo)
- **Produtos zerados** (estoque = 0)
- **Produtos críticos** (≤30% mínimo)
- **Movimentações pendentes**
- **Valor total em estoque** (R$)

### Informações de Auditoria
Para cada movimentação:
- Usuário que criou
- Data/hora de criação
- Usuário que aprovou/reprovou
- Data/hora de aprovação/reprovação
- Motivo (da movimentação e da reprovação)
- Status atual

---

## 🚀 Como Testar

### Teste 1: Criar Movimentação Pendente
1. Ir para **Estoque**
2. Clicar em "Entrada" em um produto
3. **Desmarcar** "Aprovar automaticamente"
4. Preencher e enviar
5. Verificar que aparece com status "Pendente"
6. Estoque não mudou

### Teste 2: Aprovar Movimentação
1. Clicar no botão verde (✓) da movimentação pendente
2. Confirmar
3. Verificar que status mudou para "Aprovado"
4. Verificar que estoque foi atualizado
5. Ver informação de quem aprovou

### Teste 3: Reprovar Movimentação
1. Clicar no botão vermelho (✗)
2. Informar motivo: "Quantidade incorreta"
3. Confirmar
4. Verificar status "Reprovado"
5. Passar mouse sobre o status para ver motivo

### Teste 4: Aprovar em Massa
1. Criar 5 movimentações pendentes
2. Clicar em "Aprovar Todas"
3. Confirmar
4. Verificar modal com resumo
5. Verificar que todas foram aprovadas
6. Verificar estoque atualizado

### Teste 5: Ajuste de Inventário
1. Clicar em "Ajustar" em um produto
2. Alterar estoque real
3. Informar motivo
4. Verificar diferença calculada
5. Confirmar
6. Ver movimentação criada automaticamente aprovada

### Teste 6: Produtos Críticos
1. Configurar produto com estoque mínimo = 100
2. Reduzir estoque para 25 (25% do mínimo)
3. Ir para aba Estoque
4. Verificar produto na tabela "Produtos Críticos"
5. Ver barra de progresso em vermelho

---

## 📝 Notas Técnicas

### Banco de Dados
**Coleção: `estoque_movimentacoes`**

Novos campos:
```javascript
{
  produto_id: ObjectId,
  tipo: 'entrada' | 'saida',
  quantidade: Number,
  motivo: String,
  usuario: String,
  data: Date,

  // NOVOS CAMPOS
  status: 'pendente' | 'aprovado' | 'reprovado',
  aprovado_por: String,
  aprovado_em: Date,
  reprovado_por: String,
  reprovado_em: Date,
  motivo_reprovacao: String,
  tipo_movimentacao: 'normal' | 'ajuste_inventario'
}
```

### Performance
- Agregações otimizadas para produtos críticos
- Índices recomendados:
  ```javascript
  db.estoque_movimentacoes.createIndex({ status: 1 })
  db.estoque_movimentacoes.createIndex({ data: -1 })
  db.produtos.createIndex({ estoque: 1, estoque_minimo: 1 })
  ```

### Segurança
- Todas as rotas exigem `@login_required`
- Validações de estoque insuficiente
- Logs detalhados de todas as ações
- Auditoria completa de quem fez o quê

---

## 🎯 Benefícios para o Negócio

### Controle
- ✅ Gestor tem controle total sobre movimentações
- ✅ Evita erros de digitação impactando estoque
- ✅ Rastreabilidade completa de todas as ações

### Auditoria
- ✅ Histórico completo de quem aprovou/reprovou
- ✅ Motivos documentados
- ✅ Relatórios precisos

### Eficiência
- ✅ Aprovação em massa economiza tempo
- ✅ Produtos críticos destacados automaticamente
- ✅ Ajuste de inventário rápido e preciso

### Prevenção de Perdas
- ✅ Alertas de produtos críticos
- ✅ Validação de estoque antes de aprovar saídas
- ✅ Registro de perdas e avarias

---

## 🔄 Próximas Melhorias Sugeridas

1. **Relatório de Movimentações**
   - Exportar para Excel/PDF
   - Filtros por data, produto, status

2. **Alertas por Email**
   - Notificar gestor quando houver pendentes
   - Alertar quando produto ficar crítico

3. **Previsão de Reposição**
   - IA para prever quando produto ficará em falta
   - Sugestão automática de compra

4. **Integração com Fornecedores**
   - Pedido de compra automático
   - Rastreamento de entrega

5. **Código de Barras**
   - Entrada/saída via scanner
   - Inventário com leitor de código de barras

---

## 📞 Suporte

**Desenvolvedor:** Juan Marco
**Versão:** 3.9.0
**Data:** 2025-10-17

---

## ✨ Resumo Final

### Funcionalidades Adicionadas
1. ✅ Aprovação/Reprovação individual de movimentações
2. ✅ Aprovação/Reprovação em massa
3. ✅ Produtos críticos (≤30% mínimo)
4. ✅ Ajuste de inventário
5. ✅ Entrada/Saída com aprovação automática opcional
6. ✅ Card de pendentes nas estatísticas
7. ✅ Auditoria completa de todas as ações
8. ✅ Interface moderna e intuitiva

### Endpoints Backend (5 novos)
- `POST /api/estoque/aprovar/<id>`
- `POST /api/estoque/reprovar/<id>`
- `POST /api/estoque/aprovar-todos`
- `POST /api/estoque/reprovar-todos`
- `GET /api/estoque/produtos-criticos`
- `POST /api/estoque/ajustar`

### Funções JavaScript (8 novas)
- `aprovarMovimentacao()`
- `reprovarMovimentacao()`
- `aprovarTodas()`
- `reprovarTodas()`
- `loadProdutosCriticos()`
- `ajustarEstoque()`
- `addSaidaEstoque()`

---

**Sistema de Estoque Avançado 100% Funcional e Pronto para Uso!** 🎉
