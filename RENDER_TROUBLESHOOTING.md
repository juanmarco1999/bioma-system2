# 🔧 Guia de Troubleshooting - Render HTTP 503

**Erro atual**: `HTTP ERROR 503` em `bioma-system2.onrender.com`

## 🔍 Diagnóstico do Problema

### Causa Provável: Cold Start (Plano Free)

O plano **Free** do Render tem as seguintes limitações:
- ⏰ **Hibernação automática**: Serviço hiberna após **15 minutos** de inatividade
- 🐌 **Cold start lento**: Leva **1-3 minutos** para "acordar" na primeira requisição
- ⚠️ **Durante cold start**: Retorna `HTTP 503` (Service Unavailable)

**Solução**: Aguarde 2-3 minutos e tente acessar novamente. O serviço deve voltar automaticamente.

---

## ✅ Checklist de Verificação no Render Dashboard

Acesse: https://dashboard.render.com/

### 1. Verificar Status do Serviço
- [ ] Ir para o serviço `bioma-system`
- [ ] Verificar se está **"Live"** ou **"Sleeping"**
- [ ] Se estiver "Sleeping", aguardar o wake-up automático

### 2. Verificar Logs de Deploy
- [ ] Clicar em **"Logs"** no menu lateral
- [ ] Verificar se há mensagens de erro
- [ ] Procurar por:
  ```
  ✅ MongoDB Connected
  ✅ Blueprint API registrado
  ✅ Sistema auto-contido
  ```

### 3. Verificar Variáveis de Ambiente **CRÍTICO**
- [ ] Clicar em **"Environment"** no menu lateral
- [ ] **OBRIGATÓRIAS** - Verificar se estas variáveis existem:
  - `MONGO_USERNAME` → Seu usuário do MongoDB Atlas
  - `MONGO_PASSWORD` → Sua senha do MongoDB Atlas
  - `MONGO_CLUSTER` → URL do cluster (ex: `ac-upnvxoi.n9if9sp.mongodb.net`)

- [ ] **OPCIONAIS** - Podem existir:
  - `SECRET_KEY` → Chave secreta do Flask
  - `FLASK_ENV` → `production`
  - `PYTHON_VERSION` → `3.11.0`

⚠️ **Se alguma variável MONGO_* estiver faltando, o serviço FALHARÁ!**

### 4. Verificar Start Command
- [ ] Clicar em **"Settings"** no menu lateral
- [ ] Verificar **"Start Command"**:
  ```bash
  gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --log-level info
  ```

### 5. Verificar Build Command
- [ ] Em **"Settings"**, verificar **"Build Command"**:
  ```bash
  pip install -r requirements.txt
  ```

---

## 🚀 Como Adicionar Variáveis de Ambiente no Render

Se as variáveis `MONGO_*` estiverem faltando:

1. Vá para **Environment** no menu lateral
2. Clique em **"Add Environment Variable"**
3. Adicione uma por uma:

```
Key: MONGO_USERNAME
Value: [SEU_USUARIO_MONGODB]

Key: MONGO_PASSWORD
Value: [SUA_SENHA_MONGODB]

Key: MONGO_CLUSTER
Value: [SEU_CLUSTER_MONGODB]
```

4. Clique em **"Save Changes"**
5. O Render vai **automaticamente fazer redeploy**
6. Aguarde 2-3 minutos para o build completar

---

## 🔍 Como Obter as Credenciais do MongoDB Atlas

1. Acesse: https://cloud.mongodb.com/
2. Faça login na sua conta
3. Selecione seu projeto
4. Clique em **"Database"** no menu lateral
5. Clique em **"Connect"** no seu cluster
6. Escolha **"Connect your application"**
7. Copie a **connection string**:
   ```
   mongodb+srv://<username>:<password>@<cluster>.mongodb.net/
   ```

**Extrair valores**:
- `MONGO_USERNAME` = `<username>`
- `MONGO_PASSWORD` = `<password>` (senha real, não `<password>`)
- `MONGO_CLUSTER` = `<cluster>.mongodb.net` (ex: `ac-upnvxoi.n9if9sp.mongodb.net`)

---

## 🧪 Testar se o Serviço Está Funcionando

### Teste 1: Health Check
Acesse: https://bioma-system2.onrender.com/health

**Resposta esperada**:
```json
{
  "status": "healthy",
  "time": "2025-10-26T20:43:00.000Z",
  "database": "connected",
  "version": "3.7.0"
}
```

Se retornar `"database": "disconnected"`, as variáveis de ambiente estão incorretas!

### Teste 2: Página Principal
Acesse: https://bioma-system2.onrender.com/

**Resultado esperado**: Tela de login do BIOMA Uberaba v3.7

---

## 📊 Cenários Comuns e Soluções

### Cenário 1: Cold Start (503 por 1-2 minutos)
**Sintoma**: 503 → depois de 2 minutos → site funciona
**Causa**: Plano free hibernou
**Solução**: Aguardar ou fazer upgrade para plano pago ($7/mês)

### Cenário 2: 503 Permanente (não volta)
**Sintoma**: 503 → aguarda 5 minutos → continua 503
**Causa**: Variáveis de ambiente faltando ou serviço crashou
**Solução**:
1. Verificar logs no Render dashboard
2. Verificar variáveis `MONGO_*`
3. Se necessário, fazer "Manual Deploy" em Settings

### Cenário 3: 500 Internal Server Error
**Sintoma**: Site carrega mas retorna 500 nas APIs
**Causa**: MongoDB não conectado ou erro no código
**Solução**:
1. Testar `/health` → ver `"database": "disconnected"`
2. Verificar credenciais MongoDB
3. Verificar whitelist de IPs no MongoDB Atlas (permitir 0.0.0.0/0)

### Cenário 4: 404 Not Found
**Sintoma**: 404 em todas as rotas
**Causa**: Start command incorreto
**Solução**: Verificar que está usando `gunicorn run:app` (não `app:app`)

---

## 🛠️ Comandos de Diagnóstico Local

Para testar se o problema é no Render ou no código:

```bash
# Testar localmente com gunicorn (simula produção)
cd C:\Users\Usuario\bioma-system
gunicorn run:app --bind 0.0.0.0:5000 --workers 2 --timeout 120

# Testar se MongoDB conecta
python -c "from application import create_app; app = create_app(); print('OK' if app.config.get('DB_CONNECTION') else 'FAIL')"
```

---

## 📞 Próximos Passos

### Se o problema persistir após 5 minutos:

1. **Verificar variáveis de ambiente** no Render (PRIORITÁRIO)
2. **Ver logs** no Render dashboard
3. **Fazer Manual Deploy**:
   - Settings → Manual Deploy → Deploy Latest Commit
4. **Verificar MongoDB Atlas**:
   - Network Access → Add IP Address → Allow Access from Anywhere (0.0.0.0/0)
5. **Se tudo falhar**: Deletar e recriar o serviço no Render

---

## ✅ Resolução Esperada

**Tempo estimado**: 2-5 minutos (cold start normal)

Após correções:
- ✅ `/health` retorna `"database": "connected"`
- ✅ Site carrega normalmente
- ✅ APIs funcionam (`/api/login`, `/api/register`)

---

**Última atualização**: 26/10/2025
**Commits recentes**:
- `bc6ac82` - Documentação (não afeta backend)
- `562e3e6` - Correção de HTML (não afeta backend)
- `8ac3878` - Fix de conexão MongoDB ✅
