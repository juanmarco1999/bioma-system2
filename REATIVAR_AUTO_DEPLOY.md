# 🔄 REATIVAR AUTO DEPLOY NO RENDER

## 🔴 **PROBLEMA**

O Render não está mais fazendo deploy automático quando você faz push para o GitHub.
Você tem que fazer **Manual Deploy** toda vez.

---

## ✅ **SOLUÇÃO - PASSO A PASSO**

### **PASSO 1: Acessar o Render Dashboard**

1. Vá para: https://dashboard.render.com
2. Faça login
3. Clique no serviço **"bioma-system2"** (ou o nome do seu serviço)

---

### **PASSO 2: Verificar Configurações de Deploy**

1. No menu lateral, clique em **"Settings"** (Configurações)

2. Procure pela seção **"Build & Deploy"**

3. Verifique as seguintes configurações:

#### **A) Auto-Deploy**
   - Procure por: **"Auto-Deploy"** ou **"Auto Deploy"**
   - Status deve estar: **"Yes"** ou **"Enabled"** ou **"ON"**
   - Se estiver **"No"** ou **"Disabled"** ou **"OFF"**:
     - Clique em **"Enable Auto Deploy"**
     - OU mude o toggle para **ON**
     - Salve as alterações

#### **B) Branch**
   - Verifique se está configurado para: **"main"**
   - Se estiver em outra branch (master, develop, etc.), mude para **"main"**

---

### **PASSO 3: Reconectar GitHub (Se Necessário)**

Se ainda não funcionar, pode ser que a conexão com o GitHub expirou:

1. No Render Dashboard, vá em **"Settings"**

2. Procure por:
   - **"GitHub Repository"**
   - **"Connected Repository"**
   - **"Source"**

3. Clique em **"Reconnect"** ou **"Update Source"**

4. Autorize novamente a conexão GitHub ↔ Render

5. Selecione:
   - **Repository:** `juanmarco1999/bioma-system2`
   - **Branch:** `main`

6. Salve as alterações

---

### **PASSO 4: Verificar Webhooks do GitHub**

Às vezes o webhook do GitHub → Render fica quebrado:

1. Vá para: https://github.com/juanmarco1999/bioma-system2

2. Clique em **"Settings"** (do repositório)

3. No menu lateral, clique em **"Webhooks"**

4. Procure por um webhook do Render:
   - URL deve ser algo como: `https://api.render.com/deploy/...`

5. Verifique o status:
   - ✅ **Verde** = Funcionando
   - ❌ **Vermelho/Erro** = Quebrado

6. Se estiver quebrado:
   - Delete o webhook antigo
   - Volte ao Render e clique em **"Reconnect"** (Passo 3)
   - O Render vai criar um novo webhook automaticamente

---

### **PASSO 5: Forçar Reconexão Completa**

Se nada acima funcionar, force uma reconexão:

1. No Render Dashboard → **"Settings"**

2. Procure por **"Disconnect Repository"** ou **"Remove Source"**
   - **CUIDADO:** Isso NÃO deleta o serviço, apenas desconecta o GitHub

3. Clique em **"Disconnect"**

4. Depois clique em **"Connect Repository"**

5. Autorize o GitHub novamente

6. Selecione:
   - **Account:** `juanmarco1999`
   - **Repository:** `bioma-system2`
   - **Branch:** `main`

7. Clique em **"Connect"**

8. Ative **"Auto-Deploy"**

9. Salve tudo

---

### **PASSO 6: Testar Auto Deploy**

Para confirmar que funcionou:

1. Faça uma pequena alteração no código (pode ser só adicionar um espaço em branco)

2. Commit e push:
   ```bash
   cd C:\Users\Usuario\bioma-system
   git add .
   git commit -m "Test auto deploy"
   git push origin main
   ```

3. Vá para o Render Dashboard

4. Na aba **"Events"** ou **"Logs"**, você deve ver:
   ```
   📢 New commit detected
   🔨 Starting build...
   ```

5. Se aparecer isso = **Auto deploy está funcionando!** ✅

6. Se NÃO aparecer nada = **Auto deploy ainda está OFF** ❌

---

## 📋 **CHECKLIST DE VERIFICAÇÃO**

Marque cada item conforme verifica:

- [ ] Auto-Deploy está **"Enabled"** nas Settings
- [ ] Branch configurada é **"main"**
- [ ] Repositório conectado: `juanmarco1999/bioma-system2`
- [ ] Webhook do GitHub existe e está **verde**
- [ ] Teste de commit ativa o deploy automaticamente

---

## 🎯 **CONFIGURAÇÃO CORRETA**

No Render Settings → Build & Deploy, deve estar assim:

```
Repository: juanmarco1999/bioma-system2
Branch: main
Auto-Deploy: ✅ Yes (Enabled)
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

---

## 🔍 **MOTIVOS COMUNS PARA AUTO DEPLOY PARAR**

1. ❌ **Token do GitHub expirou** → Reconecte (Passo 3)
2. ❌ **Auto-Deploy desligado manualmente** → Ative (Passo 2)
3. ❌ **Branch errada configurada** → Mude para "main" (Passo 2)
4. ❌ **Webhook quebrado** → Delete e recrie (Passo 4)
5. ❌ **Render perdeu permissões GitHub** → Reconecte (Passo 5)

---

## 🆘 **SE AINDA NÃO FUNCIONAR**

Me envie screenshots de:

1. **Render Dashboard** → Settings → Build & Deploy (toda a seção)
2. **GitHub** → Settings → Webhooks (lista de webhooks)
3. **Render Dashboard** → Events (últimos eventos)

Com essas informações, posso identificar o problema exato.

---

## ✅ **CONFIRMAÇÃO DE SUCESSO**

Você saberá que o auto deploy voltou a funcionar quando:

1. ✅ Faz push para o GitHub
2. ✅ Render **automaticamente** detecta o commit
3. ✅ Render **automaticamente** inicia o build
4. ✅ Render **automaticamente** faz o deploy
5. ✅ Você **NÃO precisa** clicar em "Manual Deploy"

---

**🎯 O auto deploy deve funcionar! Siga os passos acima.**

**Depois me diga:** Em qual passo conseguiu resolver?
