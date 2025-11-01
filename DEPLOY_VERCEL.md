# DEPLOY NO VERCEL - BIOMA Sistema

**Data:** 31/10/2025
**Plataforma:** Vercel (Serverless)
**Versão:** 6.2

---

## 🌐 INFORMAÇÕES DO PROJETO

- **URL Produção:** https://bioma-system2.vercel.app/
- **URL Development:** bioma-system2-kxj93hf8h-juanmarco1999s-projects.vercel.app
- **Project ID:** `prj_xz79Xoy6nOdXwfLlzM4qDnux093v`
- **Região:** US East (iad1)

---

## 📋 ARQUIVOS DE CONFIGURAÇÃO

### **1. vercel.json**
Arquivo principal de configuração do Vercel:

```json
{
  "version": 2,
  "name": "bioma-system2",
  "builds": [
    {
      "src": "run.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "run.py"
    }
  ],
  "functions": {
    "run.py": {
      "memory": 1024,
      "maxDuration": 60
    }
  }
}
```

**Configurações:**
- **Memory:** 1024 MB (2x mais que Render Free)
- **Timeout:** 60 segundos (vs 120s no Render)
- **Runtime:** Python 3.11

### **2. .vercelignore**
Arquivos ignorados no deploy:
- Backups e documentação
- Cache Python (`__pycache__`)
- Arquivos de desenvolvimento
- Scripts locais

### **3. requirements.txt**
Dependências Python instaladas automaticamente:
```
Flask==3.0.0
Flask-CORS==4.0.0
pymongo==4.6.0
python-dotenv==1.0.0
Werkzeug==3.0.1
requests==2.31.0
reportlab==4.0.7
openpyxl==3.1.2
Pillow>=11.0.0
```

**Nota:** Gunicorn NÃO é usado no Vercel (serverless)

---

## 🚀 COMO FAZER DEPLOY

### **Método 1: Via Git (Recomendado)**

1. **Commit as mudanças:**
   ```bash
   git add .
   git commit -m "feat: configuração para deploy no Vercel"
   git push origin main
   ```

2. **Deploy automático:**
   - Vercel detecta push no GitHub
   - Build automático inicia
   - Deploy em ~2-3 minutos

### **Método 2: Via Vercel CLI**

1. **Instalar Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login:**
   ```bash
   vercel login
   ```

3. **Deploy:**
   ```bash
   vercel --prod
   ```

### **Método 3: Via Dashboard Vercel**

1. Acessar: https://vercel.com/dashboard
2. Clicar em **"Import Project"**
3. Conectar repositório GitHub
4. Configurar variáveis de ambiente
5. Clicar em **"Deploy"**

---

## 🔐 VARIÁVEIS DE AMBIENTE

Configure no Dashboard Vercel:

**Settings → Environment Variables**

```
FLASK_ENV=production
MONGO_USERNAME=seu_usuario
MONGO_PASSWORD=sua_senha
MONGO_CLUSTER=cluster.mongodb.net
SECRET_KEY=sua_chave_secreta_aqui
```

**IMPORTANTE:**
- Adicione todas as variáveis do `.env` local
- Use valores de **produção**, não desenvolvimento
- Nunca commite o arquivo `.env`

---

## 📊 DIFERENÇAS: RENDER vs VERCEL

| Recurso | Render (Free) | Vercel (Hobby) |
|---------|---------------|----------------|
| **RAM** | 512 MB | **1024 MB** ✅ |
| **Timeout** | 120s | 60s ⚠️ |
| **Custo** | Grátis | Grátis |
| **Arquitetura** | Server | **Serverless** |
| **Cold Start** | Lento (~30s) | **Rápido (~2s)** ✅ |
| **Deploy** | Manual | **Automático** ✅ |
| **SSL** | Sim | Sim |
| **CDN** | Não | **Sim** ✅ |
| **Domínio** | Sim | Sim |

**Vantagens do Vercel:**
- ✅ **2x mais RAM** (1024 MB vs 512 MB)
- ✅ **Deploy automático** via Git
- ✅ **Cold start mais rápido** (~2s vs ~30s)
- ✅ **CDN global** integrado
- ✅ **Preview deployments** para cada commit

**Desvantagens:**
- ⚠️ **Timeout menor** (60s vs 120s) - pode afetar operações longas
- ⚠️ **Serverless** - reinicia a cada requisição (SSE pode ter problemas)

---

## ⚠️ CONSIDERAÇÕES IMPORTANTES

### **1. Timeout de 60 segundos**
Operações longas podem falhar:
- **Importação de muitas linhas** (>500) → Dividir em lotes
- **Geração de relatórios grandes** → Otimizar queries
- **Deletar muitos registros** → Usar paginação

**Solução:** Já implementado `fetchWithTimeout()` de 30s no frontend

### **2. Server-Sent Events (SSE)**
SSE pode ter problemas em serverless:
- **Problema:** Conexão reinicia a cada cold start
- **Solução atual:** SSE com heartbeat apenas (60s intervalo)
- **Alternativa futura:** Usar WebSockets ou Polling

### **3. MongoDB Connection**
- **Connection pooling** é gerenciado pelo Vercel
- **Timeouts** podem ocorrer em cold starts
- **Solução:** Implementado retry automático

### **4. Arquivos Estáticos**
- **Templates e static/** são servidos pelo CDN do Vercel
- **Performance:** Muito mais rápida que Render
- **Cache:** Automático

---

## 🧪 TESTES PÓS-DEPLOY

Após deploy, testar:

### **Funcionalidades Críticas:**
- [ ] **Login/Logout** - Autenticação funciona
- [ ] **Dashboard** - Carrega estatísticas
- [ ] **Cadastro de profissional** - Sem CPF funciona
- [ ] **Importação de serviços** - 100% sucesso esperado
- [ ] **Mapa de calor** - Carrega com diferentes períodos
- [ ] **SSE (tempo real)** - Notificações funcionam
- [ ] **Upload de arquivos** - Importação funciona
- [ ] **Geração de PDF** - Orçamentos geram PDF

### **Performance:**
- [ ] **Carregamento inicial** < 5s (vs ~15s no Render)
- [ ] **Cold start** < 3s (primeira requisição)
- [ ] **Requisições subsequentes** < 1s
- [ ] **Importação 100 linhas** < 30s

### **Logs e Monitoring:**
- [ ] Ver logs no Dashboard Vercel
- [ ] Verificar erros no Sentry (se configurado)
- [ ] Monitorar uso de RAM (não deve ultrapassar 1024 MB)

---

## 🔍 DEBUGGING

### **Ver Logs:**
```bash
# Via CLI
vercel logs

# Via Dashboard
https://vercel.com/juanmarco1999s-projects/bioma-system2/logs
```

### **Logs do Vercel:**
- **Build logs:** Erros durante instalação de dependências
- **Runtime logs:** Erros durante execução
- **Analytics:** Performance e uso de recursos

### **Erros Comuns:**

#### **1. Error: Module not found**
```
Solução: Adicionar módulo ao requirements.txt
```

#### **2. Error: Function timeout (60s)**
```
Solução: Otimizar query/operação ou dividir em partes
```

#### **3. Error: Memory exceeded (1024 MB)**
```
Solução: Otimizar código, reduzir objetos em memória
```

#### **4. SSE não funciona**
```
Solução: Trocar para polling ou WebSockets
```

---

## 📈 MONITORING

### **Métricas do Vercel:**
- **Analytics:** Requisições, tempo de resposta, erros
- **Bandwidth:** Tráfego total (100 GB/mês grátis)
- **Function Executions:** Número de execuções (100 GB-Hrs grátis)

### **Limites do Plano Hobby (Grátis):**
- **Bandwidth:** 100 GB/mês
- **Function Executions:** 100 GB-Hrs/mês
- **Build Time:** 6000 minutos/mês
- **Serverless Functions:** 100 max

**IMPORTANTE:** Monitorar uso mensalmente

---

## 🔄 ROLLBACK

Se houver problemas, fazer rollback:

### **Via Dashboard:**
1. Acessar **Deployments**
2. Encontrar deploy anterior estável
3. Clicar em **"..."** → **"Promote to Production"**

### **Via CLI:**
```bash
vercel rollback
```

---

## 🚀 PRÓXIMOS PASSOS

### **Após Deploy Inicial:**
1. ✅ Verificar todas funcionalidades
2. ✅ Monitorar logs por 24h
3. ✅ Ajustar timeouts se necessário
4. ✅ Otimizar operações lentas

### **Otimizações Futuras:**
- [ ] Implementar cache Redis (Vercel KV)
- [ ] Migrar SSE para WebSockets
- [ ] Adicionar Sentry para error tracking
- [ ] Implementar rate limiting
- [ ] Adicionar monitoring avançado

---

## 📞 SUPORTE

### **Documentação Oficial:**
- Vercel Docs: https://vercel.com/docs
- Python Runtime: https://vercel.com/docs/runtimes#official-runtimes/python

### **Comunidade:**
- Discord: https://vercel.com/discord
- GitHub Discussions: https://github.com/vercel/vercel/discussions

---

## 📝 CHANGELOG

### **v6.2 - Configuração Vercel**
- Criado `vercel.json` com configuração serverless
- Criado `.vercelignore` para otimizar deploy
- Documentação completa de deploy
- Memória: 1024 MB (2x Render)
- Timeout: 60s (vs 120s Render)

---

**Status:** ✅ Pronto para deploy no Vercel!
**URL:** https://bioma-system2.vercel.app/
