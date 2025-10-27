# BIOMA v4.0 - Relatório de Problemas Identificados

**Data:** 27/10/2025
**Desenvolvedor:** Juan Marco (@juanmarco1999)
**Versão:** 4.0

---

## ✅ PROBLEMAS CORRIGIDOS

### 1. Logo com Fundo Roxo
**Status:** ✅ **RESOLVIDO**

**Problema:**
- Logo tinha background gradient roxo
- Logo era quadrado sem personalidade
- Ocupava muito espaço

**Solução Implementada:**
- `border-radius: 50%` (formato circular)
- `background: transparent !important`
- `.sidebar-logo` sem gradient (usa `var(--bg-sidebar)`)
- Tamanho otimizado: `max-width: 200px`
- Sombra suave para destaque

**Commit:** `511bf59` - Fix: Remove 404 errors + Logo redesign

---

### 2. Erros 404 (Arquivos Arquivados)
**Status:** ✅ **RESOLVIDO**

**Problema:**
- `/static/css/correcoes-v37.css` - 404 Not Found
- `/static/js/melhorias-v37.js` - 404 Not Found

**Solução Implementada:**
- Removidas todas as referências aos arquivos arquivados
- Sistema carrega apenas arquivos ativos
- Logs limpos sem erros 404

**Commit:** `511bf59` - Fix: Remove 404 errors + Logo redesign

---

### 3. Dark Mode Persistente no Login
**Status:** ✅ **CORRIGIDO** (aguardando deploy)

**Problema:**
- Login aparecia em dark mode mesmo com light forçado
- `localStorage.theme` persistia após limpar

**Solução Implementada:**
- **IIFE Super Agressivo** executado IMEDIATAMENTE no `<head>`
- Remove `theme`, `bioma_theme` de `localStorage` E `sessionStorage`
- For\u00e7a `data-theme="light"` ANTES de qualquer CSS/JS
- Define `color-scheme="light"`

```javascript
(function() {
    localStorage.removeItem('theme');
    localStorage.removeItem('bioma_theme');
    sessionStorage.removeItem('theme');
    document.documentElement.setAttribute('data-theme', 'light');
    document.documentElement.style.setProperty('color-scheme', 'light');
    console.log('🌞 LIGHT MODE FORÇADO AGRESSIVAMENTE');
})();
```

**Commit:** `5fc3590` - Fix: Forçar light mode AGRESSIVAMENTE no login

**⚠️ NOTA:** Após o deploy, limpe o cache do navegador (`Ctrl + Shift + Delete`)

---

## ❌ PROBLEMAS AINDA NÃO RESOLVIDOS

### 1. **CRÍTICO:** Botões WhatsApp e Email NÃO Funcionam
**Status:** ❌ **NÃO IMPLEMENTADO**

**Problema:**
```html
<!-- Botões existem na UI -->
<button onclick="enviarContratoEmail('${c._id}')">
    <i class="bi bi-envelope-fill"></i>
</button>

<button onclick="enviarContratoWhatsApp('${c._id}')">
    <i class="bi bi-whatsapp"></i>
</button>
```

**Funções NÃO EXISTEM:**
- `enviarContratoEmail()` - **AUSENTE**
- `enviarContratoWhatsApp()` - **AUSENTE**

**Localização:** [index.html:5542-5547](templates/index.html#L5542-L5547)

**O Que Precisa Ser Implementado:**

#### A) Função WhatsApp:
```javascript
async function enviarContratoWhatsApp(contratoId) {
    try {
        // Buscar dados do contrato
        const res = await fetch(`/api/contrato/${contratoId}`, {credentials: 'include'});
        const data = await res.json();

        if(!data.success) throw new Error(data.message);

        const contrato = data.contrato;
        const telefone = contrato.cliente_telefone.replace(/\D/g, ''); // Remove formatação

        // Montar mensagem
        const mensagem = `
🌳 *BIOMA Uberaba - Contrato #${contrato.numero}*

Olá ${contrato.cliente_nome}!

Segue seu contrato aprovado:

📊 Total: R$ ${contrato.total_final.toFixed(2)}
📅 Data: ${new Date(contrato.created_at).toLocaleDateString('pt-BR')}
✅ Status: ${contrato.status}

Acesse o PDF: ${window.location.origin}/api/contrato/${contratoId}/pdf

Obrigado pela preferência! 🌿
        `.trim();

        // Abrir WhatsApp
        const url = `https://wa.me/55${telefone}?text=${encodeURIComponent(mensagem)}`;
        window.open(url, '_blank');

    } catch(error) {
        console.error('Erro ao enviar WhatsApp:', error);
        Swal.fire('Erro', 'Não foi possível enviar pelo WhatsApp', 'error');
    }
}
```

#### B) Função Email:
```javascript
async function enviarContratoEmail(contratoId) {
    try {
        Swal.fire({
            title: 'Enviando E-mail...',
            html: '<div class="spinner"></div>',
            allowOutsideClick: false,
            showConfirmButton: false
        });

        const res = await fetch(`/api/contrato/${contratoId}/enviar-email`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include'
        });

        const data = await res.json();

        if(data.success) {
            Swal.fire({
                icon: 'success',
                title: 'E-mail Enviado!',
                text: `Contrato enviado para ${data.destinatario}`,
                timer: 3000
            });
        } else {
            throw new Error(data.message);
        }
    } catch(error) {
        console.error('Erro ao enviar email:', error);
        Swal.fire('Erro', 'Não foi possível enviar o e-mail', 'error');
    }
}
```

#### C) Rota Backend Necessária:
**Arquivo:** `application/api/routes.py`

```python
@bp.route('/api/contrato/<contrato_id>/enviar-email', methods=['POST'])
@login_required
def enviar_contrato_email(contrato_id):
    try:
        db = current_app.config['DB_CONNECTION']
        contrato = db.orcamentos.find_one({'_id': ObjectId(contrato_id)})

        if not contrato:
            return jsonify({'success': False, 'message': 'Contrato não encontrado'}), 404

        # Buscar email do cliente
        cliente = db.clientes.find_one({'_id': ObjectId(contrato['cliente_id'])})

        if not cliente or not cliente.get('email'):
            return jsonify({'success': False, 'message': 'Cliente sem e-mail cadastrado'}), 400

        # Configurar MailerSend (ou SMTP)
        # TODO: Implementar envio de email via MailerSend API

        return jsonify({
            'success': True,
            'destinatario': cliente['email'],
            'message': 'E-mail enviado com sucesso'
        })

    except Exception as e:
        logger.error(f'Erro ao enviar email: {e}')
        return jsonify({'success': False, 'message': str(e)}), 500
```

---

### 2. Travamentos do Sistema
**Status:** ⚠️ **EM INVESTIGAÇÃO**

**Causas Identificadas:**

#### A) Worker Timeout no Render:
```
[CRITICAL] WORKER TIMEOUT (pid:65)
Worker (pid:65) was sent SIGKILL! Perhaps out of memory?
```

**Possíveis Causas:**
- Plano Free do Render (512MB RAM)
- Auto-refresh a cada 30s causando sobrecarga
- Múltiplas conexões SSE simultâneas

**Soluções Recomendadas:**
1. Aumentar intervalo do auto-refresh (30s → 60s)
2. Desabilitar auto-refresh quando página inativa
3. Limitar conexões SSE por usuário
4. Considerar upgrade do plano Render

#### B) Rotas 404 Causando Loop:
```
GET /api/financeiro/resumo - 404 (Not Found)
GET /api/comissoes - 404 (Not Found)
```

**Problema:**
- Auto-refresh tenta carregar rotas que não existem
- Gera erro a cada 30 segundos
- Acumula requests falhando

**Solução:**
- Adicionar rotas faltantes em `routes.py`
- OU remover chamadas a rotas inexistentes

---

### 3. Botões de Fechar Não Funcionam
**Status:** ❓ **NECESSITA MAIS INFORMAÇÕES**

**Informação Necessária:**
- Quais modais especificamente?
- Botão "Fechar" ou "X" no canto?
- Erro no console?

**Verificações Necessárias:**
- Verificar `Swal.close()` em todos os modais
- Verificar event listeners em botões `.swal2-close`
- Verificar se SafeSwal está bloqueando close

---

## 📊 Resumo do Status

| Problema | Status | Prioridade |
|----------|--------|-----------|
| Logo roxo/quadrado | ✅ RESOLVIDO | Alta |
| Erros 404 arquivos | ✅ RESOLVIDO | Alta |
| Dark mode login | ✅ CORRIGIDO* | Alta |
| WhatsApp/Email | ❌ NÃO IMPL. | **CRÍTICA** |
| Worker Timeout | ⚠️ INVESTIGANDO | Alta |
| Rotas 404 | ❌ PENDENTE | Média |
| Botões fechar | ❓ INFO NEEDED | Média |

\* Aguardando deploy + limpar cache

---

## 🚀 Próximos Passos Recomendados

### Prioridade 1 - CRÍTICO:
1. **Implementar funções WhatsApp e Email**
   - Adicionar `enviarContratoWhatsApp()`
   - Adicionar `enviarContratoEmail()`
   - Criar rota backend `/api/contrato/:id/enviar-email`

### Prioridade 2 - Alta:
2. **Resolver Worker Timeout**
   - Otimizar auto-refresh
   - Limitar conexões SSE
   - Considerar upgrade Render

3. **Adicionar Rotas Faltantes**
   - `/api/financeiro/resumo`
   - `/api/comissoes`

### Prioridade 3 - Média:
4. **Investigar Botões de Fechar**
   - Coletar mais informações do usuário
   - Reproduzir problema localmente
   - Corrigir event listeners

---

## 📦 Commits Recentes

```bash
5fc3590 - Fix: Forçar light mode AGRESSIVAMENTE no login
511bf59 - Fix: Remove 404 errors + Logo redesign (arredondado sem fundo)
877c56b - Hotfix: Remove import de routes_melhorias obsoleto
3dff6dc - Refactor: Reorganização completa do projeto BIOMA v4.0
```

---

## ⏳ Deploy em Andamento

**Commit Atual:** `5fc3590`
**Status:** Deploy automático no Render (2-3 minutos)
**Ação Pós-Deploy:** Limpar cache do navegador (`Ctrl + Shift + Delete`)

---

**Desenvolvido por:** Juan Marco (@juanmarco1999)
**Data:** 27/10/2025
**Versão:** BIOMA v4.0
