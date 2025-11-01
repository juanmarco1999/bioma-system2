# BIOMA v7.2 - ANÁLISE PROFUNDA DE PERFORMANCE

**Data:** 2025-11-01
**Versão:** 7.2.0
**Tipo:** Análise Crítica de Performance

---

## 🎯 OBJETIVO

Identificar e resolver gargalos de performance no sistema BIOMA para melhorar:
- Tempo de resposta dos endpoints
- Uso de memória e CPU
- Escalabilidade do sistema
- Experiência do usuário

---

## 🔍 METODOLOGIA

1. Análise de **109 endpoints** em routes.py
2. Identificação de **queries MongoDB** problemáticas
3. Detecção de padrões anti-performance
4. Cálculo de impacto estimado

---

## ❌ PROBLEMAS CRÍTICOS IDENTIFICADOS

### 1. QUERIES SEM ÍNDICES (CRÍTICO 🔴)

**Impacto:** Queries podem levar **segundos** em vez de milissegundos

| Query | Linha | Frequência | Impacto |
|-------|-------|------------|---------|
| `{'status': 'Aprovado'}` | 463, 811, 3638, 4827, 4968, 7212, 7285, 7304, 7473, 7531 | 10+ vezes | ALTO |
| `{'cliente_cpf': cpf}` | 680, 811, 1263, 5981, 5989, 6155, 6231 | 7+ vezes | ALTO |
| `{'status': 'Ativo'}` | 3666, 7773, 7890, 8317, 8387, 8541, 8562, 8594 | 8+ vezes | ALTO |
| `{'nome': regex}` | 665, 899, 937, 942, 947, 952 | 6+ vezes | MÉDIO |

**Solução:** Criar índices MongoDB

---

### 2. QUERIES QUE CARREGAM TUDO NA MEMÓRIA (CRÍTICO 🔴)

**Impacto:** 10.000+ produtos = 100MB+ de RAM desperdiçada

| Linha | Query | Problema |
|-------|-------|----------|
| 665 | `db.clientes.find({})` | SEM LIMIT - carrega TODOS os clientes |
| 2745 | `db.produtos.find({})` | SEM LIMIT - carrega TODOS os produtos |
| 2952 | `db.produtos.find({})` | SEM LIMIT - duplicado! |
| 3666 | `db.produtos.find({'ativo': True})` | SEM LIMIT - todos os produtos ativos |
| 7890 | `db.produtos.find({'status': 'Ativo'})` | SEM LIMIT - duplicado! |
| 8317 | `db.produtos.find({'status': 'Ativo'})` | SEM LIMIT - triplicado! |
| 8387 | `db.produtos.find({'status': 'Ativo'})` | SEM LIMIT - quadruplicado! |

**Solução:** Adicionar `.limit()` ou usar agregações

---

### 3. N+1 QUERY PROBLEM (CRÍTICO 🔴)

**Impacto:** 1000 clientes = 1000 queries extras = 10-30 segundos!

**Linha 677-680:** Para CADA cliente, faz query de orçamentos
```python
for cliente in clientes_list:
    # Para CADA cliente, faz UMA query extra!
    total_faturado = sum(
        o.get('total_final', 0)
        for o in db.orcamentos.find({'cliente_cpf': cliente_cpf, 'status': 'Aprovado'})
    )
```

**Pior caso:**
- 1000 clientes
- 1 query inicial + 1000 queries extras = **1001 queries**
- Tempo: ~10ms x 1000 = **10 segundos**

**Solução:** Usar agregação com $lookup ou denormalizar dados

---

### 4. CÁLCULOS EM PYTHON (MÉDIO 🟡)

**Impacto:** MongoDB faz cálculos 10x-100x mais rápido que Python

**Linha 463:**
```python
# LENTO - traz TODOS os orçamentos para Python
'faturamento': sum(o.get('total_final', 0) for o in db.orcamentos.find({'status': 'Aprovado'}))
```

**Deveria ser:**
```python
# RÁPIDO - MongoDB faz o cálculo
result = db.orcamentos.aggregate([
    {'$match': {'status': 'Aprovado'}},
    {'$group': {'_id': None, 'total': {'$sum': '$total_final'}}}
])
```

**Outras ocorrências:**
- Linha 680, 811, 2953, 3667, 5987, 7213, 7305

---

### 5. FALTA DE CACHE (MÉDIO 🟡)

**Impacto:** Dados estáticos recalculados a cada request

**Candidatos para cache:**
- Dashboard (atualizar a cada 30s-1min)
- Estatísticas de produtos (atualizar quando muda estoque)
- Lista de profissionais (atualizar quando adiciona/remove)
- Categorias (raramente mudam)

---

### 6. REGEX SEM ÍNDICE TEXT (BAIXO 🟢)

**Impacto:** Buscas de texto lentas

**Linha 899, 937, 942, 947, 952:**
```python
regex = {'$regex': termo, '$options': 'i'}
db.clientes.find({'nome': regex})
```

**Solução:** Usar índice de texto do MongoDB
```python
db.clientes.createIndex({ nome: "text" })
db.clientes.find({ $text: { $search: termo } })
```

---

## 📊 IMPACTO ESTIMADO

| Problema | Endpoints Afetados | Impacto por Request | Severidade |
|----------|-------------------|---------------------|------------|
| Queries sem índices | 30+ | +500ms - +5s | 🔴 CRÍTICO |
| Carregar tudo na RAM | 15+ | +200ms - +2s | 🔴 CRÍTICO |
| N+1 Query | 5+ | +1s - +30s | 🔴 CRÍTICO |
| Cálculos em Python | 10+ | +100ms - +1s | 🟡 MÉDIO |
| Falta de cache | 10+ | +50ms - +500ms | 🟡 MÉDIO |
| Regex sem índice | 6+ | +50ms - +300ms | 🟢 BAIXO |

**GANHO TOTAL ESPERADO:**
- **Antes:** Alguns endpoints podem levar 10-30 segundos
- **Depois:** Todos endpoints < 500ms (melhoria de 20x-60x)

---

## ✅ SOLUÇÕES PRIORITÁRIAS

### PRIORIDADE 1 - Índices MongoDB (IMEDIATO)

```javascript
// Orçamentos (mais importante - usado em quase tudo)
db.orcamentos.createIndex({ status: 1 })
db.orcamentos.createIndex({ cliente_cpf: 1 })
db.orcamentos.createIndex({ created_at: -1 })
db.orcamentos.createIndex({ status: 1, created_at: -1 })  // Compound

// Produtos
db.produtos.createIndex({ status: 1 })
db.produtos.createIndex({ estoque: 1 })

// Clientes
db.clientes.createIndex({ cpf: 1 }, { unique: true })

// Profissionais
db.profissionais.createIndex({ ativo: 1 })

// Text search
db.clientes.createIndex({ nome: "text" })
db.produtos.createIndex({ nome: "text" })
db.servicos.createIndex({ nome: "text" })
```

### PRIORIDADE 2 - Agregações no lugar de loops Python

**Linha 677-680 - Faturamento por cliente:**
```python
# ANTES (N+1 query)
for cliente in clientes_list:
    total = sum(o.get('total_final', 0) for o in db.orcamentos.find({'cliente_cpf': cpf}))

# DEPOIS (1 query agregada)
pipeline = [
    {'$match': {'status': 'Aprovado'}},
    {'$group': {
        '_id': '$cliente_cpf',
        'total_faturado': {'$sum': '$total_final'}
    }}
]
faturamento_por_cliente = {r['_id']: r['total_faturado'] for r in db.orcamentos.aggregate(pipeline)}
```

### PRIORIDADE 3 - Adicionar limits e paginação

```python
# ANTES
produtos = list(db.produtos.find({}))

# DEPOIS
produtos = list(db.produtos.find({}).limit(1000))  # ou usar paginação
```

### PRIORIDADE 4 - Cache estratégico

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache de 60 segundos
cache_dashboard = {'data': None, 'timestamp': None}

def get_dashboard_stats():
    now = datetime.now()
    if cache_dashboard['timestamp'] and (now - cache_dashboard['timestamp']) < timedelta(seconds=60):
        return cache_dashboard['data']

    # Calcular...
    cache_dashboard['data'] = resultado
    cache_dashboard['timestamp'] = now
    return resultado
```

---

## 🎯 ROADMAP DE OTIMIZAÇÃO

### SPRINT 1 - Correções Críticas (1-2 horas)
- [x] ✅ Análise de performance completa
- [ ] 🔄 Criar todos os índices MongoDB
- [ ] 🔄 Corrigir N+1 query em clientes (linha 677-680)
- [ ] 🔄 Adicionar limits em queries sem paginação

### SPRINT 2 - Otimizações (2-3 horas)
- [ ] 🔄 Substituir loops Python por agregações MongoDB
- [ ] 🔄 Implementar cache em dashboard e estatísticas
- [ ] 🔄 Adicionar paginação em listagens grandes

### SPRINT 3 - Melhorias (1-2 horas)
- [ ] 🔄 Compressão de respostas (gzip)
- [ ] 🔄 Lazy loading de imagens
- [ ] 🔄 Índices de texto para buscas

### SPRINT 4 - Testes (1 hora)
- [ ] 🔄 Testes de carga/estresse
- [ ] 🔄 Métricas antes/depois
- [ ] 🔄 Documentação final

---

## 📈 MÉTRICAS DE SUCESSO

| Métrica | Antes | Meta Depois | Como Medir |
|---------|-------|-------------|------------|
| Tempo médio resposta | 1-5s | < 500ms | Logs/monitoring |
| P95 tempo resposta | 10-30s | < 1s | Logs/monitoring |
| Queries por listagem | 1000+ | < 10 | MongoDB profiler |
| Uso de memória | Alto | -50% | Process monitor |
| Carga MongoDB | Alta | -70% | db.serverStatus() |

---

**Desenvolvedor:** @juanmarco1999
**Claude Code:** v7.2
**Última Atualização:** 2025-11-01
