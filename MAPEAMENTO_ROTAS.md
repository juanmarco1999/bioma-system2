# MAPEAMENTO DE ROTAS - BIOMA Backend

**Total de rotas:** 134
**Arquivo original:** application/api/routes.py (8.433 linhas)

---

## ORGANIZAÇÃO EM BLUEPRINTS

### 1. **system.py** - Rotas de Sistema (10 rotas)
- `/` - Home
- `/health` - Health check
- `/api/ping` - Ping
- `/api/system/status` - Status do sistema
- `/api/dashboard/stats` - Estatísticas do dashboard
- `/api/dashboard/stats/realtime` - Estatísticas em tempo real
- `/api/current-user` - Usuário atual
- `/api/permissions` - Permissões do usuário
- `/api/update-theme` - Atualizar tema
- `/api/search/suggest` - Sugestões de busca
- `/api/busca/global` - Busca global

### 2. **auth.py** - Autenticação (6 rotas)
- `/api/login` - Login
- `/api/register` - Registro
- `/api/logout` - Logout
- `/api/users` - Listar usuários
- `/api/users/<id>` - Detalhes do usuário
- `/api/users/<id>/tipo-acesso` - Atualizar tipo de acesso

### 3. **clientes.py** - Clientes (5 rotas)
- `/api/clientes` [GET, POST] - Listar/Criar clientes
- `/api/clientes/<id>` [GET, PUT, DELETE] - CRUD de cliente
- `/api/clientes/buscar` - Buscar clientes

### 4. **profissionais.py** - Profissionais (10 rotas)
- `/api/profissionais` [GET, POST] - Listar/Criar profissionais
- `/api/profissionais/<id>` [GET, PUT, DELETE] - CRUD de profissional
- `/api/profissionais/<id>/avaliacoes` - Avaliações do profissional
- `/api/profissionais/<id>/upload-foto` - Upload de foto
- `/api/assistentes` [GET, POST] - CRUD de assistentes
- `/api/assistentes/<id>` [DELETE] - Deletar assistente

### 5. **servicos.py** - Serviços (15 rotas)
- `/api/servicos` [GET, POST] - Listar/Criar serviços
- `/api/servicos/<id>` [GET, PUT, DELETE] - CRUD de serviço
- `/api/servicos/buscar` - Buscar serviços
- `/api/servicos/toggle-todos` - Ativar/Desativar todos

### 6. **produtos.py** - Produtos (15 rotas)
- `/api/produtos` [GET, POST] - Listar/Criar produtos
- `/api/produtos/<id>` [GET, PUT, DELETE] - CRUD de produto
- `/api/produtos/buscar` - Buscar produtos
- `/api/produtos/toggle-todos` - Ativar/Desativar todos

### 7. **estoque.py** - Estoque (20 rotas)
- `/api/estoque/entrada` - Entrada de estoque
- `/api/estoque/entrada/pendentes` - Entradas pendentes
- `/api/estoque/entrada/<id>` - Atualizar entrada
- `/api/estoque/entrada/<id>/aprovar` - Aprovar entrada
- `/api/estoque/entrada/<id>/rejeitar` - Rejeitar entrada
- `/api/estoque/alerta` - Alertas de estoque
- `/api/estoque/movimentacoes` - Movimentações
- `/api/estoque/resumo` - Resumo do estoque

### 8. **orcamentos.py** - Orçamentos (10 rotas)
- `/api/orcamento/<id>/pdf` - Gerar PDF
- `/api/contratos` - Contratos

### 9. **agendamentos.py** - Agendamentos (15 rotas)
- `/api/agendamentos` [GET, POST] - Listar/Criar agendamentos
- `/api/agendamentos/<id>` [DELETE] - Deletar agendamento
- `/api/agendamentos/horarios-disponiveis` - Horários disponíveis
- `/api/agendamentos/mapa-calor` - Mapa de calor
- `/api/agendamentos/hoje` - Agendamentos de hoje
- `/api/agendamentos/semana` - Agendamentos da semana
- `/api/agendamentos/mes` - Agendamentos do mês
- `/api/agendamentos/heatmap` - Heatmap

### 10. **fila.py** - Fila de Atendimento (5 rotas)
- `/api/fila` [GET, POST] - Listar/Adicionar à fila
- `/api/fila/<id>` [DELETE] - Remover da fila
- `/api/fila/<id>/notificar` - Notificar cliente
- `/api/fila/notificar-todos` - Notificar todos

### 11. **financeiro.py** - Financeiro (15 rotas)
- `/api/despesas` - Despesas
- `/api/despesas/<id>` - CRUD de despesa
- `/api/faturamento` - Faturamento
- `/api/financeiro/resumo` - Resumo financeiro

### 12. **comissoes.py** - Comissões (8 rotas)
- `/api/comissao/calcular` - Calcular comissão
- `/api/comissoes` - Listar comissões
- `/api/comissoes/<id>` - Detalhes da comissão

### 13. **importacao.py** - Importação (3 rotas)
- `/api/importar` - Importar planilha
- `/api/importar/desfazer` - Desfazer importação
- `/api/estoque/importar` - Importar estoque (alias)

### 14. **sse.py** - Server-Sent Events (1 rota)
- `/api/stream` - Stream SSE

### 15. **configuracoes.py** - Configurações (10 rotas)
- `/api/configuracoes` - Configurações
- `/api/configuracoes/logo` - Upload de logo
- `/api/configuracoes/whatsapp` - Configurações WhatsApp
- `/api/configuracoes/email` - Configurações Email

---

## ESTRUTURA PROPOSTA

```
application/api/
├── __init__.py (modificado - registra blueprints)
├── routes.py (será removido ou simplificado)
└── blueprints/
    ├── __init__.py
    ├── auth.py
    ├── clientes.py
    ├── profissionais.py
    ├── servicos.py
    ├── produtos.py
    ├── estoque.py
    ├── orcamentos.py
    ├── agendamentos.py
    ├── fila.py
    ├── financeiro.py
    ├── comissoes.py
    ├── configuracoes.py
    ├── importacao.py
    ├── sse.py
    └── system.py
```

---

## PRÓXIMOS PASSOS

1. ✅ Criar estrutura de diretórios
2. ⏳ Criar cada blueprint
3. ⏳ Registrar blueprints no __init__.py
4. ⏳ Testar todas as rotas
5. ⏳ Remover/arquivar routes.py antigo
6. ⏳ Commit das mudanças

---

**Status:** Em Progresso
**Estimativa:** 4-6h de trabalho
