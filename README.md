# BIOMA v4.0 - Sistema de Gestão para Franquias

Sistema completo de gestão para franquias do setor de beleza e bem-estar.

## 📁 Estrutura do Projeto

```
bioma-system/
├── application/              # Backend modularizado
│   ├── __init__.py          # Inicialização do app Flask
│   ├── constants.py         # Constantes do sistema
│   ├── decorators.py        # Decoradores (login_required, etc)
│   ├── extensions.py        # Extensões Flask (CORS, etc)
│   ├── utils.py             # Funções utilitárias
│   └── api/
│       ├── __init__.py
│       └── routes.py        # Todas as rotas da API (290 KB)
│
├── static/                   # Arquivos estáticos
│   └── js/
│       ├── document-generator.js  # Gerador de PDFs/Excel profissionais
│       └── offline-manager.js     # Gerenciador PWA offline
│
├── templates/               # Templates HTML
│   └── index.html          # SPA - Single Page Application (519 KB)
│
├── docs/                    # Documentação
│   ├── archive/            # Arquivos obsoletos arquivados
│   └── *.md               # Documentação do projeto
│
├── app.py                  # Aplicação Flask principal
├── config.py               # Configurações do sistema
├── run.py                  # Script de execução local
├── wsgi.py                 # Entry point para produção
├── requirements.txt        # Dependências Python
├── render.yaml            # Configuração Render
├── runtime.txt            # Versão Python
└── .gitignore             # Arquivos ignorados pelo Git
```

## 🚀 Tecnologias

**Backend:**
- Python 3.11
- Flask 3.0.0
- PyMongo (MongoDB)
- Flask-CORS

**Frontend:**
- HTML5 + CSS3 + JavaScript (Vanilla)
- Bootstrap Icons
- SweetAlert2
- Chart.js
- SheetJS (XLSX)
- jsPDF + AutoTable
- PWA (Progressive Web App)

**Database:**
- MongoDB Atlas

**Deploy:**
- Render.com
- GitHub Actions (CI/CD)

## 📦 Instalação Local

```bash
# Clone o repositório
git clone https://github.com/juanmarco1999/bioma-system2.git
cd bioma-system

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente (.env)
MONGODB_URI=sua_connection_string
SECRET_KEY=sua_chave_secreta

# Execute localmente
python run.py
```

## 🌐 Deploy

O sistema está configurado para deploy automático no Render.com através do GitHub.

Cada push para a branch `main` dispara um deploy automático.

## 📝 Funcionalidades Principais

- ✅ Gestão de Clientes
- ✅ Gestão de Profissionais e Comissões
- ✅ Orçamentos e Contratos
- ✅ Gestão de Estoque
- ✅ Agendamentos
- ✅ Relatórios e Dashboards
- ✅ Sistema de Comissões
- ✅ Exportação Excel/CSV/PDF
- ✅ PWA - Funciona Offline
- ✅ Dark/Light Mode
- ✅ Logos Personalizáveis

## 🔧 Manutenção

### Arquivos Removidos na Reorganização (27/10/2025)

Foram movidos para `docs/archive/`:
- `app_legacy.py` (312 KB) - Código legado
- `routes_backup.py` (288 KB) - Backup antigo
- `routes_melhorias.py` (135 KB) - Melhorias já aplicadas
- `app.js` (277 KB) - JS não usado (tudo inline)
- `melhorias-v37.js` (234 KB) - Melhorias já aplicadas
- Arquivos CSS separados (não usados)

**Total economizado:** ~1.5 MB de arquivos obsoletos

### Pastas Removidas

- `static/css/` - CSS inline em index.html
- `static/images/` - Vazia
- `static/img/` - Vazia

## 📊 Tamanho dos Arquivos Principais

- `index.html`: 519 KB (SPA completo)
- `routes.py`: 290 KB (Todas as APIs)
- `document-generator.js`: 12 KB
- `offline-manager.js`: 15 KB

## 🐛 Correções Recentes

**27/10/2025 - v4.0.3:**
- ✅ Corrigido export freezing (modais bloqueantes → toasts)
- ✅ Logo aumentado de 250px para 400px
- ✅ Animações CSS para toasts
- ✅ Dark mode forçado na tela de login
- ✅ Reorganização completa do projeto
- ✅ Remoção de ~1.5 MB de arquivos obsoletos

## 👨‍💻 Autor

**Juan Marco** (@juanmarco1999)

## 📄 Licença

Proprietário - BIOMA Franchising
