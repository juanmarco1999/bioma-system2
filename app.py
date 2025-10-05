#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    BIOMA UBERABA v2.5 - ULTRA PROFISSIONAL                   ║
║                     Sistema Completo de Gestão para Salões                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Desenvolvedor: Juan Marco (@juanmarco1999)                                  ║
║  Email: 180147064@aluno.unb.br                                               ║
║  Data: 2025-10-05 14:31:26 UTC                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ===== IMPORTS =====
from flask import Flask, render_template, request, jsonify, session, send_file
from flask_cors import CORS
from flask_talisman import Talisman
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson import ObjectId
from functools import wraps
from datetime import datetime, timedelta
from dotenv import load_dotenv
import urllib.parse
import os
import io
import csv
import json
import re
import requests
import logging
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle

# ===== CONFIGURAÇÃO DE LOGS =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ===== CARREGAR VARIÁVEIS DE AMBIENTE =====
load_dotenv()
logger.info("🔧 Variáveis de ambiente carregadas")

# ===== CONFIGURAÇÃO FLASK =====
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'bioma-2025-ultra-secure')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

logger.info(f"🌐 Flask Environment: {os.getenv('FLASK_ENV', 'development')}")

# ===== SEGURANÇA =====
if os.getenv('FLASK_ENV') == 'production':
    logger.info("🔒 Modo produção - Ativando segurança SSL/HTTPS")
    csp = {
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'", 'cdn.jsdelivr.net', 'cdnjs.cloudflare.com'],
        'style-src': ["'self'", "'unsafe-inline'", 'cdn.jsdelivr.net', 'fonts.googleapis.com'],
        'font-src': ["'self'", 'fonts.gstatic.com', 'cdn.jsdelivr.net'],
        'img-src': ["'self'", 'data:', 'https:'],
    }
    Talisman(app, force_https=True, strict_transport_security=True, content_security_policy=csp)

# ===== CORS =====
CORS(app, supports_credentials=True)

# ===== CRIAR PASTA UPLOADS =====
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
logger.info(f"📁 Pasta uploads: {app.config['UPLOAD_FOLDER']}")

# ===== CONEXÃO MONGODB =====
def get_db():
    try:
        u = urllib.parse.quote_plus(os.getenv('MONGO_USERNAME', ''))
        p = urllib.parse.quote_plus(os.getenv('MONGO_PASSWORD', ''))
        c = os.getenv('MONGO_CLUSTER', '')
        
        if not all([u, p, c]):
            logger.error("❌ Credenciais MongoDB não encontradas")
            return None
        
        uri = f"mongodb+srv://{u}:{p}@{c}/bioma_db?retryWrites=true&w=majority"
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.server_info()  # Testa conexão
        
        logger.info("✅ MongoDB conectado com sucesso")
        return client.bioma_db
    except Exception as e:
        logger.error(f"❌ Erro MongoDB: {e}")
        return None

db = get_db()

if db is None:
    logger.warning("⚠️ Sistema iniciando SEM banco de dados")
else:
    logger.info("💾 Banco de dados: bioma_db")

# ===== SERIALIZAÇÃO JSON CUSTOMIZADA =====
from flask.json.provider import DefaultJSONProvider

class CustomJSONProvider(DefaultJSONProvider):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

app.json = CustomJSONProvider(app)
logger.info("🔧 JSON Provider customizado ativado")

# ===== FUNÇÃO AUXILIAR PARA SERIALIZAÇÃO =====
def jsonify_safe(data):
    """
    Converte ObjectId e datetime para JSON seguro recursivamente
    """
    if isinstance(data, list):
        return [jsonify_safe(item) for item in data]
    elif isinstance(data, dict):
        return {key: jsonify_safe(value) for key, value in data.items()}
    elif isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data

# ===== DECORATOR LOGIN REQUIRED =====
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning(f"🚫 Acesso negado - Usuário não autenticado: {request.endpoint}")
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

# ===== FUNÇÕES DE EMAIL E SMS =====
def send_email(to, name, subj, html, pdf=None):
    """Envia e-mail via MailerSend"""
    key = os.getenv('MAILERSEND_API_KEY')
    if not key:
        logger.warning("⚠️ MailerSend API Key não configurada")
        return {'success': False}
    
    data = {
        "from": {
            "email": os.getenv('MAILERSEND_FROM_EMAIL', 'noreply@bioma.com'),
            "name": "BIOMA Uberaba"
        },
        "to": [{"email": to, "name": name}],
        "subject": subj,
        "html": html
    }
    
    if pdf:
        import base64
        data['attachments'] = [{
            "filename": pdf['filename'],
            "content": base64.b64encode(pdf['content']).decode()
        }]
    
    try:
        r = requests.post(
            "https://api.mailersend.com/v1/email",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}"
            },
            json=data,
            timeout=10
        )
        
        if r.status_code == 202:
            logger.info(f"📧 E-mail enviado para {to}")
            return {'success': True}
        else:
            logger.error(f"❌ Erro enviar e-mail: {r.status_code}")
            return {'success': False}
    except Exception as e:
        logger.error(f"❌ Exception enviar e-mail: {e}")
        return {'success': False}

def send_sms(num, msg):
    """Envia SMS via MailerSend"""
    key = os.getenv('MAILERSEND_API_KEY')
    if not key:
        logger.warning("⚠️ MailerSend API Key não configurada")
        return {'success': False}
    
    n = '+55' + ''.join(filter(str.isdigit, num)) if not num.startswith('+') else num
    
    try:
        r = requests.post(
            "https://api.mailersend.com/v1/sms",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}"
            },
            json={
                "from": "BIOMA",
                "to": [n],
                "text": msg
            },
            timeout=10
        )
        
        if r.status_code == 202:
            logger.info(f"📱 SMS enviado para {num}")
            return {'success': True}
        else:
            logger.error(f"❌ Erro enviar SMS: {r.status_code}")
            return {'success': False}
    except Exception as e:
        logger.error(f"❌ Exception enviar SMS: {e}")
        return {'success': False}

# ===== ROTAS BÁSICAS =====
@app.route('/')
def index():
    logger.info(f"🌐 Acesso à página inicial - IP: {request.remote_addr}")
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'time': datetime.now().isoformat(),
        'database': 'connected' if db is not None else 'disconnected'
    }), 200

@app.route('/api/system/status')
@login_required
def system_status():
    logger.info(f"📊 Verificação de status - User: {session.get('username')}")
    
    status = {
        'mongodb': {
            'operational': db is not None,
            'message': 'Conectado' if db else 'Desconectado',
            'last_check': datetime.now()
        },
        'mailersend': {
            'operational': bool(os.getenv('MAILERSEND_API_KEY'))
        },
        'server': {
            'time': datetime.now(),
            'environment': os.getenv('FLASK_ENV', 'development')
        }
    }
    
    return jsonify({'success': True, 'status': status})

# ===== AUTENTICAÇÃO =====
@app.route('/api/register', methods=['POST'])
def register():
    d = request.json
    logger.info(f"👤 Tentativa de registro: {d.get('username')}")
    
    if db.users.find_one({'$or': [{'username': d['username']}, {'email': d['email']}]}):
        logger.warning(f"⚠️ Registro falhou - Usuário/email já existe: {d.get('username')}")
        return jsonify({'success': False, 'message': 'Usuário ou email já existe'})
    
    db.users.insert_one({
        'name': d['name'],
        'username': d['username'],
        'email': d['email'],
        'password': generate_password_hash(d['password']),
        'role': 'user',
        'theme': 'light',
        'created_at': datetime.now()
    })
    
    logger.info(f"✅ Usuário registrado: {d['username']}")
    return jsonify({'success': True})

@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    logger.info(f"🔐 Tentativa de login: {d.get('username')}")
    
    u = db.users.find_one({'$or': [{'username': d['username']}, {'email': d['username']}]})
    
    if u and check_password_hash(u['password'], d['password']):
        session.permanent = True
        session['user_id'] = str(u['_id'])
        session['username'] = u['username']
        
        logger.info(f"✅ Login bem-sucedido: {u['username']}")
        
        return jsonify({
            'success': True,
            'user': {
                'id': str(u['_id']),
                'name': u['name'],
                'username': u['username'],
                'theme': u.get('theme', 'light')
            }
        })
    
    logger.warning(f"❌ Login falhou: {d.get('username')}")
    return jsonify({'success': False, 'message': 'Credenciais inválidas'})

@app.route('/api/logout', methods=['POST'])
def logout():
    username = session.get('username', 'Unknown')
    session.clear()
    logger.info(f"👋 Logout: {username}")
    return jsonify({'success': True})

@app.route('/api/current-user')
def current_user():
    if 'user_id' in session:
        try:
            u = db.users.find_one({'_id': ObjectId(session['user_id'])})
            if u:
                return jsonify({
                    'success': True,
                    'user': {
                        'id': str(u['_id']),
                        'name': u['name'],
                        'username': u['username'],
                        'theme': u.get('theme', 'light')
                    }
                })
        except Exception as e:
            logger.error(f"❌ Erro ao buscar usuário atual: {e}")
    
    return jsonify({'success': False})

@app.route('/api/update-theme', methods=['POST'])
@login_required
def update_theme():
    theme = request.json['theme']
    db.users.update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$set': {'theme': theme}}
    )
    logger.info(f"🎨 Tema alterado para {theme} - User: {session.get('username')}")
    return jsonify({'success': True})

# ===== CLIENTES (GET, POST, DELETE) =====
@app.route('/api/clientes', methods=['GET', 'POST'])
@login_required
def clientes():
    if request.method == 'GET':
        logger.info("📋 Listando clientes")
        try:
            clientes_list = list(db.clientes.find({}).sort('nome', 1))
            logger.info(f"✅ {len(clientes_list)} clientes encontrados")
            return jsonify({'success': True, 'clientes': jsonify_safe(clientes_list)})
        except Exception as e:
            logger.error(f"❌ Erro listar clientes: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    # POST
    d = request.json
    logger.info(f"➕ Cadastrando/atualizando cliente: {d.get('nome')}")
    
    try:
        existing = db.clientes.find_one({'cpf': d['cpf']})
        
        if existing:
            db.clientes.update_one(
                {'cpf': d['cpf']},
                {'$set': {**d, 'updated_at': datetime.now()}}
            )
            logger.info(f"✅ Cliente atualizado: {d['nome']}")
        else:
            db.clientes.insert_one({**d, 'created_at': datetime.now()})
            logger.info(f"✅ Cliente criado: {d['nome']}")
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Erro salvar cliente: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/clientes/<id>', methods=['DELETE'])
@login_required
def delete_cliente(id):
    logger.info(f"🗑️ Deletando cliente ID: {id}")
    try:
        result = db.clientes.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            logger.info(f"✅ Cliente deletado: {id}")
            return jsonify({'success': True})
        else:
            logger.warning(f"⚠️ Cliente não encontrado: {id}")
            return jsonify({'success': False, 'message': 'Cliente não encontrado'})
    except Exception as e:
        logger.error(f"❌ Erro deletar cliente: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/clientes/buscar')
@login_required
def buscar_clientes():
    termo = request.args.get('termo', '')
    logger.info(f"🔍 Buscando clientes: {termo}")
    
    try:
        regex = {'$regex': termo, '$options': 'i'}
        clientes = list(db.clientes.find({
            '$or': [{'nome': regex}, {'cpf': regex}]
        }).limit(10))
        
        logger.info(f"✅ {len(clientes)} clientes encontrados para '{termo}'")
        return jsonify({'success': True, 'clientes': jsonify_safe(clientes)})
    except Exception as e:
        logger.error(f"❌ Erro buscar clientes: {e}")
        return jsonify({'success': False, 'message': str(e)})

# ===== PROFISSIONAIS (GET, POST, DELETE) =====
@app.route('/api/profissionais', methods=['GET', 'POST'])
@login_required
def profissionais():
    if request.method == 'GET':
        logger.info("📋 Listando profissionais")
        try:
            profs_list = list(db.profissionais.find({}).sort('nome', 1))
            logger.info(f"✅ {len(profs_list)} profissionais encontrados")
            return jsonify({'success': True, 'profissionais': jsonify_safe(profs_list)})
        except Exception as e:
            logger.error(f"❌ Erro listar profissionais: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    # POST
    d = request.json
    logger.info(f"➕ Cadastrando profissional: {d.get('nome')}")
    
    try:
        db.profissionais.insert_one({
            'nome': d['nome'],
            'cpf': d['cpf'],
            'email': d.get('email', ''),
            'telefone': d.get('telefone', ''),
            'especialidade': d.get('especialidade', ''),
            'comissao_perc': float(d.get('comissao_perc', 0)),
            'ativo': True,
            'created_at': datetime.now()
        })
        
        logger.info(f"✅ Profissional criado: {d['nome']}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Erro salvar profissional: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/profissionais/<id>', methods=['DELETE'])
@login_required
def delete_profissional(id):
    logger.info(f"🗑️ Deletando profissional ID: {id}")
    try:
        result = db.profissionais.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            logger.info(f"✅ Profissional deletado: {id}")
            return jsonify({'success': True})
        else:
            logger.warning(f"⚠️ Profissional não encontrado: {id}")
            return jsonify({'success': False, 'message': 'Profissional não encontrado'})
    except Exception as e:
        logger.error(f"❌ Erro deletar profissional: {e}")
        return jsonify({'success': False, 'message': str(e)})

# ===== SERVIÇOS (GET, POST, DELETE) =====
@app.route('/api/servicos', methods=['GET', 'POST'])
@login_required
def servicos():
    if request.method == 'GET':
        logger.info("📋 Listando serviços")
        try:
            servs_list = list(db.servicos.find({}).sort('nome', 1))
            logger.info(f"✅ {len(servs_list)} serviços encontrados")
            return jsonify({'success': True, 'servicos': jsonify_safe(servs_list)})
        except Exception as e:
            logger.error(f"❌ Erro listar serviços: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    # POST
    d = request.json
    logger.info(f"➕ Cadastrando serviço: {d.get('nome')}")
    
    try:
        tamanhos = {
            'Kids': d.get('preco_kids', 0),
            'Masculino': d.get('preco_masculino', 0),
            'Curto': d.get('preco_curto', 0),
            'Médio': d.get('preco_medio', 0),
            'Longo': d.get('preco_longo', 0),
            'Extra Longo': d.get('preco_extra_longo', 0)
        }
        
        count = 0
        for tam, preco in tamanhos.items():
            db.servicos.insert_one({
                'nome': d['nome'],
                'sku': f"{d['nome'].upper().replace(' ', '-')}-{tam.upper().replace(' ', '-')}",
                'tamanho': tam,
                'preco': float(preco),
                'categoria': d.get('categoria', 'Serviço'),
                'ativo': True,
                'created_at': datetime.now()
            })
            count += 1
        
        logger.info(f"✅ Serviço criado com {count} SKUs: {d['nome']}")
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        logger.error(f"❌ Erro salvar serviço: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/servicos/<id>', methods=['DELETE'])
@login_required
def delete_servico(id):
    logger.info(f"🗑️ Deletando serviço ID: {id}")
    try:
        result = db.servicos.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            logger.info(f"✅ Serviço deletado: {id}")
            return jsonify({'success': True})
        else:
            logger.warning(f"⚠️ Serviço não encontrado: {id}")
            return jsonify({'success': False, 'message': 'Serviço não encontrado'})
    except Exception as e:
        logger.error(f"❌ Erro deletar serviço: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/servicos/buscar')
@login_required
def buscar_servicos():
    termo = request.args.get('termo', '')
    logger.info(f"🔍 Buscando serviços: {termo}")
    
    try:
        regex = {'$regex': termo, '$options': 'i'}
        servicos = list(db.servicos.find({'nome': regex}).limit(20))
        
        logger.info(f"✅ {len(servicos)} serviços encontrados para '{termo}'")
        return jsonify({'success': True, 'servicos': jsonify_safe(servicos)})
    except Exception as e:
        logger.error(f"❌ Erro buscar serviços: {e}")
        return jsonify({'success': False, 'message': str(e)})
    
# ===== PRODUTOS (GET, POST, DELETE) =====
@app.route('/api/produtos', methods=['GET', 'POST'])
@login_required
def produtos():
    if request.method == 'GET':
        logger.info("📋 Listando produtos")
        try:
            prods_list = list(db.produtos.find({}).sort('nome', 1))
            logger.info(f"✅ {len(prods_list)} produtos encontrados")
            return jsonify({'success': True, 'produtos': jsonify_safe(prods_list)})
        except Exception as e:
            logger.error(f"❌ Erro listar produtos: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    # POST
    d = request.json
    logger.info(f"➕ Cadastrando produto: {d.get('nome')}")
    
    try:
        db.produtos.insert_one({
            'nome': d['nome'],
            'marca': d.get('marca', ''),
            'sku': d.get('sku', ''),
            'preco': float(d.get('preco', 0)),
            'custo': float(d.get('custo', 0)),
            'estoque': int(d.get('estoque', 0)),
            'categoria': d.get('categoria', 'Produto'),
            'ativo': True,
            'created_at': datetime.now()
        })
        
        logger.info(f"✅ Produto criado: {d['nome']}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Erro salvar produto: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/produtos/<id>', methods=['DELETE'])
@login_required
def delete_produto(id):
    logger.info(f"🗑️ Deletando produto ID: {id}")
    try:
        result = db.produtos.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            logger.info(f"✅ Produto deletado: {id}")
            return jsonify({'success': True})
        else:
            logger.warning(f"⚠️ Produto não encontrado: {id}")
            return jsonify({'success': False, 'message': 'Produto não encontrado'})
    except Exception as e:
        logger.error(f"❌ Erro deletar produto: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/produtos/buscar')
@login_required
def buscar_produtos():
    termo = request.args.get('termo', '')
    logger.info(f"🔍 Buscando produtos: {termo}")
    
    try:
        regex = {'$regex': termo, '$options': 'i'}
        produtos = list(db.produtos.find({'nome': regex}).limit(20))
        
        logger.info(f"✅ {len(produtos)} produtos encontrados para '{termo}'")
        return jsonify({'success': True, 'produtos': jsonify_safe(produtos)})
    except Exception as e:
        logger.error(f"❌ Erro buscar produtos: {e}")
        return jsonify({'success': False, 'message': str(e)})

# ===== ORÇAMENTOS (GET, POST, DELETE) =====
@app.route('/api/orcamentos', methods=['GET', 'POST'])
@login_required
def orcamentos():
    if request.method == 'GET':
        logger.info("📋 Listando orçamentos")
        try:
            status = request.args.get('status')
            query = {'status': status} if status else {}
            orcs_list = list(db.orcamentos.find(query).sort('created_at', -1))
            
            logger.info(f"✅ {len(orcs_list)} orçamentos encontrados")
            return jsonify({'success': True, 'orcamentos': jsonify_safe(orcs_list)})
        except Exception as e:
            logger.error(f"❌ Erro listar orçamentos: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    # POST
    d = request.json
    logger.info(f"➕ Criando orçamento para: {d.get('cliente_nome')}")
    
    try:
        # Salvar/atualizar cliente
        db.clientes.update_one(
            {'cpf': d['cliente_cpf']},
            {'$set': {
                'cpf': d['cliente_cpf'],
                'nome': d['cliente_nome'],
                'email': d.get('cliente_email', ''),
                'telefone': d.get('cliente_telefone', ''),
                'updated_at': datetime.now()
            }},
            upsert=True
        )
        
        # Calcular totais
        subtotal = sum(s['total'] for s in d['servicos']) + sum(p['total'] for p in d['produtos'])
        desconto_valor = subtotal * (d.get('desconto_global', 0) / 100)
        total_com_desconto = subtotal - desconto_valor
        cashback_valor = total_com_desconto * (d.get('cashback_perc', 0) / 100)
        
        # Gerar número sequencial
        ultimo = db.orcamentos.find_one(sort=[('numero', -1)])
        numero = (ultimo['numero'] + 1) if ultimo and 'numero' in ultimo else 1
        
        # Salvar orçamento
        orc_id = db.orcamentos.insert_one({
            'numero': numero,
            'cliente_cpf': d['cliente_cpf'],
            'cliente_nome': d['cliente_nome'],
            'cliente_email': d.get('cliente_email', ''),
            'cliente_telefone': d.get('cliente_telefone', ''),
            'servicos': d['servicos'],
            'produtos': d['produtos'],
            'subtotal': subtotal,
            'desconto_global': d.get('desconto_global', 0),
            'desconto_valor': desconto_valor,
            'total_com_desconto': total_com_desconto,
            'cashback_perc': d.get('cashback_perc', 0),
            'cashback_valor': cashback_valor,
            'total_final': total_com_desconto,
            'pagamento': d.get('pagamento', {}),
            'status': d.get('status', 'Pendente'),
            'created_at': datetime.now(),
            'user_id': session['user_id']
        }).inserted_id
        
        logger.info(f"✅ Orçamento #{numero} criado - ID: {orc_id}")
        
        # Se aprovado, gerar PDF e enviar email/SMS
        if d.get('status') == 'Aprovado':
            logger.info(f"📄 Gerando contrato PDF para orçamento #{numero}")
            
            orc = db.orcamentos.find_one({'_id': orc_id})
            pdf_bytes = gerar_contrato_pdf(orc)
            
            if d.get('cliente_email'):
                logger.info(f"📧 Enviando e-mail para {d['cliente_email']}")
                send_email(
                    d['cliente_email'],
                    d['cliente_nome'],
                    f"Contrato BIOMA #{numero}",
                    f"<h2>Olá {d['cliente_nome']},</h2><p>Segue em anexo seu contrato de prestação de serviços.</p><p><strong>Total: R$ {total_com_desconto:.2f}</strong></p>",
                    {'filename': f'contrato_bioma_{numero}.pdf', 'content': pdf_bytes}
                )
            
            if d.get('cliente_telefone'):
                logger.info(f"📱 Enviando SMS para {d['cliente_telefone']}")
                send_sms(
                    d['cliente_telefone'],
                    f"BIOMA: Contrato #{numero} aprovado! Total: R$ {total_com_desconto:.2f}. Acesse seu email para detalhes."
                )
        
        return jsonify({'success': True, 'numero': numero, 'id': str(orc_id)})
        
    except Exception as e:
        logger.error(f"❌ Erro criar orçamento: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/orcamentos/<id>', methods=['DELETE'])
@login_required
def delete_orcamento(id):
    logger.info(f"🗑️ Deletando orçamento ID: {id}")
    try:
        result = db.orcamentos.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            logger.info(f"✅ Orçamento deletado: {id}")
            return jsonify({'success': True})
        else:
            logger.warning(f"⚠️ Orçamento não encontrado: {id}")
            return jsonify({'success': False, 'message': 'Orçamento não encontrado'})
    except Exception as e:
        logger.error(f"❌ Erro deletar orçamento: {e}")
        return jsonify({'success': False, 'message': str(e)})

# ===== CONTRATOS =====
@app.route('/api/contratos')
@login_required
def contratos():
    logger.info("📋 Listando contratos aprovados")
    try:
        contratos_list = list(db.orcamentos.find({'status': 'Aprovado'}).sort('created_at', -1))
        logger.info(f"✅ {len(contratos_list)} contratos encontrados")
        return jsonify({'success': True, 'contratos': jsonify_safe(contratos_list)})
    except Exception as e:
        logger.error(f"❌ Erro listar contratos: {e}")
        return jsonify({'success': False, 'message': str(e)})

# ===== DASHBOARD =====
@app.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    logger.info("📊 Carregando estatísticas do dashboard")
    try:
        stats = {
            'total_orcamentos': db.orcamentos.count_documents({}),
            'total_clientes': db.clientes.count_documents({}),
            'total_servicos': db.servicos.count_documents({'ativo': True}),
            'faturamento': sum(o.get('total_final', 0) for o in db.orcamentos.find({'status': 'Aprovado'}))
        }
        
        logger.info(f"✅ Stats: {stats['total_orcamentos']} orçamentos, {stats['total_clientes']} clientes, R$ {stats['faturamento']:.2f} faturamento")
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        logger.error(f"❌ Erro carregar stats: {e}")
        return jsonify({'success': False, 'message': str(e)})

# ===== FILA DE ATENDIMENTO (GET, POST, DELETE) =====
@app.route('/api/fila', methods=['GET', 'POST'])
@login_required
def fila():
    if request.method == 'GET':
        logger.info("📋 Listando fila de atendimento")
        try:
            fila_list = list(db.fila_atendimento.find({
                'status': {'$in': ['aguardando', 'atendendo']}
            }).sort('created_at', 1))
            
            logger.info(f"✅ {len(fila_list)} pessoas na fila")
            return jsonify({'success': True, 'fila': jsonify_safe(fila_list)})
        except Exception as e:
            logger.error(f"❌ Erro listar fila: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    # POST
    d = request.json
    logger.info(f"➕ Adicionando à fila: {d.get('cliente_nome')}")
    
    try:
        total = db.fila_atendimento.count_documents({
            'status': {'$in': ['aguardando', 'atendendo']}
        })
        
        db.fila_atendimento.insert_one({
            'cliente_nome': d['cliente_nome'],
            'cliente_telefone': d['cliente_telefone'],
            'servico': d.get('servico', ''),
            'profissional': d.get('profissional', ''),
            'posicao': total + 1,
            'status': 'aguardando',
            'created_at': datetime.now()
        })
        
        logger.info(f"✅ Cliente adicionado à fila na posição {total + 1}")
        
        if d.get('cliente_telefone'):
            send_sms(
                d['cliente_telefone'],
                f"BIOMA: Você está na posição {total + 1} da fila. Aguarde ser chamado!"
            )
        
        return jsonify({'success': True, 'posicao': total + 1})
        
    except Exception as e:
        logger.error(f"❌ Erro adicionar à fila: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/fila/chamar/<id>', methods=['POST'])
@login_required
def chamar_fila(id):
    logger.info(f"📢 Chamando cliente da fila ID: {id}")
    try:
        item = db.fila_atendimento.find_one({'_id': ObjectId(id)})
        
        if item:
            db.fila_atendimento.update_one(
                {'_id': ObjectId(id)},
                {'$set': {'status': 'atendendo', 'chamado_at': datetime.now()}}
            )
            
            logger.info(f"✅ Cliente chamado: {item.get('cliente_nome')}")
            
            if item.get('cliente_telefone'):
                send_sms(
                    item['cliente_telefone'],
                    f"BIOMA: {item['cliente_nome']}, é sua vez! Dirija-se ao atendimento."
                )
            
            return jsonify({'success': True})
        else:
            logger.warning(f"⚠️ Item da fila não encontrado: {id}")
            return jsonify({'success': False, 'message': 'Item não encontrado'})
            
    except Exception as e:
        logger.error(f"❌ Erro chamar fila: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/fila/finalizar/<id>', methods=['POST'])
@login_required
def finalizar_fila(id):
    logger.info(f"✅ Finalizando atendimento ID: {id}")
    try:
        db.fila_atendimento.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'status': 'finalizado', 'finalizado_at': datetime.now()}}
        )
        
        logger.info(f"✅ Atendimento finalizado: {id}")
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"❌ Erro finalizar atendimento: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/fila/<id>', methods=['DELETE'])
@login_required
def delete_fila(id):
    logger.info(f"🗑️ Deletando item da fila ID: {id}")
    try:
        result = db.fila_atendimento.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            logger.info(f"✅ Item da fila deletado: {id}")
            return jsonify({'success': True})
        else:
            logger.warning(f"⚠️ Item da fila não encontrado: {id}")
            return jsonify({'success': False, 'message': 'Item não encontrado'})
    except Exception as e:
        logger.error(f"❌ Erro deletar item da fila: {e}")
        return jsonify({'success': False, 'message': str(e)})

# ===== CONFIGURAÇÕES =====
@app.route('/api/config', methods=['GET', 'POST'])
@login_required
def config():
    if request.method == 'GET':
        logger.info("📋 Carregando configurações")
        try:
            cfg = db.config.find_one({'key': 'unidade'}) or {}
            return jsonify({'success': True, 'config': jsonify_safe(cfg)})
        except Exception as e:
            logger.error(f"❌ Erro carregar config: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    # POST
    d = request.json
    logger.info("💾 Salvando configurações")
    
    try:
        db.config.update_one(
            {'key': 'unidade'},
            {'$set': d},
            upsert=True
        )
        
        logger.info("✅ Configurações salvas")
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"❌ Erro salvar config: {e}")
        return jsonify({'success': False, 'message': str(e)})

# ===== BUSCAR CEP =====
@app.route('/api/cep/<cep>')
@login_required
def buscar_cep(cep):
    logger.info(f"📍 Buscando CEP: {cep}")
    try:
        r = requests.get(f'https://viacep.com.br/ws/{cep}/json/', timeout=5)
        data = r.json()
        
        if 'erro' not in data:
            logger.info(f"✅ CEP encontrado: {data.get('localidade')}")
            return jsonify({
                'success': True,
                'endereco': {
                    'logradouro': data.get('logradouro', ''),
                    'bairro': data.get('bairro', ''),
                    'cidade': data.get('localidade', ''),
                    'estado': data.get('uf', '')
                }
            })
        else:
            logger.warning(f"⚠️ CEP não encontrado: {cep}")
            return jsonify({'success': False, 'message': 'CEP não encontrado'})
            
    except Exception as e:
        logger.error(f"❌ Erro buscar CEP: {e}")
        return jsonify({'success': False, 'message': str(e)})

# ===== IMPORTAR CSV/XLSX =====
@app.route('/api/importar', methods=['POST'])
@login_required
def importar():
    logger.info("📤 Iniciando importação de dados")
    
    if 'file' not in request.files:
        logger.warning("⚠️ Nenhum arquivo enviado")
        return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'})
    
    f = request.files['file']
    t = request.form.get('tipo', 'produtos')
    
    if not f.filename:
        logger.warning("⚠️ Arquivo inválido")
        return jsonify({'success': False, 'message': 'Arquivo inválido'})
    
    ext = f.filename.rsplit('.', 1)[1].lower() if '.' in f.filename else ''
    
    if ext not in ['csv', 'xlsx', 'xls']:
        logger.warning(f"⚠️ Formato não suportado: {ext}")
        return jsonify({'success': False, 'message': 'Apenas CSV ou XLSX'})
    
    logger.info(f"📄 Importando {ext.upper()} - Tipo: {t}")
    
    try:
        fn = secure_filename(f.filename)
        fp = os.path.join(app.config['UPLOAD_FOLDER'], fn)
        f.save(fp)
        logger.info(f"💾 Arquivo salvo: {fp}")
        
        cs = 0  # count success
        ce = 0  # count error
        rows = []
        
        # Ler arquivo
        if ext == 'csv':
            logger.info("🔄 Lendo CSV com múltiplos encodings...")
            encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(fp, 'r', encoding=encoding) as csvfile:
                        reader = csv.DictReader(csvfile)
                        rows = list(reader)
                        logger.info(f"✅ CSV lido com encoding {encoding}")
                        break
                except UnicodeDecodeError:
                    logger.debug(f"❌ Falha com encoding {encoding}")
                    continue
            
            if not rows:
                logger.error("❌ Erro ao ler CSV - encoding não suportado")
                return jsonify({'success': False, 'message': 'Erro ao ler CSV - encoding não suportado'})
                
        else:  # xlsx ou xls
            logger.info("🔄 Lendo XLSX...")
            from openpyxl import load_workbook
            wb = load_workbook(fp, read_only=True, data_only=True)
            ws = wb.active
            
            headers = []
            for cell in next(ws.iter_rows(min_row=1, max_row=1)):
                val = str(cell.value).strip().lower() if cell.value else ''
                headers.append(val)
            
            logger.info(f"📋 Cabeçalhos encontrados: {headers}")
            
            for row in ws.iter_rows(min_row=2, values_only=True):
                row_dict = {}
                for i in range(len(headers)):
                    if i < len(row):
                        val = row[i]
                        if isinstance(val, str):
                            val = val.strip()
                            if 'r$' in val.lower():
                                val = val.replace('R$', '').replace('r$', '').strip()
                                val = val.replace('.', '').replace(',', '.')
                        row_dict[headers[i]] = val
                rows.append(row_dict)
            
            wb.close()
            logger.info(f"✅ XLSX lido - {len(rows)} linhas")
        
        logger.info(f"🔄 Processando {len(rows)} linhas para {t}...")
        
        # Processar dados
        if t == 'produtos':
            logger.info("📦 Importando PRODUTOS...")
            
            # Colunas flexíveis
            nome_cols = ['nome', 'produto', 'name', 'descricao', 'descrição', 'description']
            marca_cols = ['marca', 'brand', 'fabricante', 'manufacturer']
            preco_cols = ['preco', 'preço', 'price', 'valor', 'value']
            custo_cols = ['custo', 'cost', 'preco custo', 'preço custo']
            estoque_cols = ['estoque', 'quantidade', 'qtd', 'stock', 'qty']
            categoria_cols = ['categoria', 'category', 'tipo', 'type']
            sku_cols = ['sku', 'codigo', 'código', 'code', 'ref', 'referencia', 'referência']
            
            for idx, row in enumerate(rows, start=1):
                try:
                    row_lower = {k.lower().strip(): v for k, v in row.items() if k}
                    
                    # Buscar nome
                    nome = None
                    for col in nome_cols:
                        if col in row_lower and row_lower[col]:
                            nome = str(row_lower[col]).strip()
                            break
                    
                    if not nome or len(nome) < 2:
                        logger.debug(f"⚠️ Linha {idx}: Nome inválido")
                        ce += 1
                        continue
                    
                    # Buscar marca
                    marca = ''
                    for col in marca_cols:
                        if col in row_lower and row_lower[col]:
                            marca = str(row_lower[col]).strip()
                            break
                    
                    # Buscar SKU
                    sku = ''
                    for col in sku_cols:
                        if col in row_lower and row_lower[col]:
                            sku = str(row_lower[col]).strip()
                            break
                    
                    if not sku:
                        sku_base = re.sub(r'[^A-Z0-9]', '', nome.upper())[:10]
                        sku = f"{sku_base}-{cs+1}"
                    
                    # Buscar preço
                    preco = 0.0
                    for col in preco_cols:
                        if col in row_lower and row_lower[col]:
                            try:
                                val = str(row_lower[col]).replace('R$', '').replace('r$', '').strip()
                                val = val.replace('.', '').replace(',', '.')
                                preco = float(val)
                                break
                            except:
                                continue
                    
                    # Buscar custo
                    custo = 0.0
                    for col in custo_cols:
                        if col in row_lower and row_lower[col]:
                            try:
                                val = str(row_lower[col]).replace('R$', '').replace('r$', '').strip()
                                val = val.replace('.', '').replace(',', '.')
                                custo = float(val)
                                break
                            except:
                                continue
                    
                    # Buscar estoque
                    estoque = 0
                    for col in estoque_cols:
                        if col in row_lower and row_lower[col]:
                            try:
                                estoque = int(float(row_lower[col]))
                                break
                            except:
                                continue
                    
                    # Buscar categoria
                    categoria = 'Produto'
                    for col in categoria_cols:
                        if col in row_lower and row_lower[col]:
                            categoria = str(row_lower[col]).strip().title()
                            break
                    
                    # Inserir
                    db.produtos.insert_one({
                        'nome': nome,
                        'marca': marca,
                        'sku': sku,
                        'preco': preco,
                        'custo': custo,
                        'estoque': estoque,
                        'categoria': categoria,
                        'ativo': True,
                        'created_at': datetime.now()
                    })
                    cs += 1
                    logger.debug(f"✅ Produto {cs}: {nome}")
                    
                except Exception as e:
                    logger.error(f"❌ Erro linha {idx}: {e}")
                    ce += 1
                    continue
        
        else:  # servicos
            logger.info("✂️ Importando SERVIÇOS...")
            
            nome_cols = ['nome', 'servico', 'serviço', 'service', 'concat', 'concatenado']
            categoria_cols = ['categoria', 'category', 'tipo', 'type']
            
            tamanho_map = {
                'kids': ['kids', 'kid', 'infantil', 'crianca', 'criança', 'child'],
                'masculino': ['masculino', 'male', 'homem', 'masc', 'man'],
                'curto': ['curto', 'short', 'pequeno', 'small'],
                'medio': ['medio', 'médio', 'medium', 'm', 'mid'],
                'longo': ['longo', 'long', 'grande', 'large', 'l'],
                'extra_longo': ['extra_longo', 'extra longo', 'xl', 'extra', 'extralongo', 'x-large']
            }
            
            for idx, row in enumerate(rows, start=1):
                try:
                    row_lower = {k.lower().strip(): v for k, v in row.items() if k}
                    
                    # Buscar nome
                    nome = None
                    for col in nome_cols:
                        if col in row_lower and row_lower[col]:
                            val = str(row_lower[col]).strip()
                            # Extrair nome se tiver número na frente
                            match = re.search(r'\d*([A-Za-zÀ-ú\s]+)', val)
                            nome = match.group(1).strip() if match else val
                            break
                    
                    if not nome or len(nome) < 2:
                        logger.debug(f"⚠️ Linha {idx}: Nome inválido")
                        ce += 1
                        continue
                    
                    # Buscar categoria
                    categoria = 'Serviço'
                    for col in categoria_cols:
                        if col in row_lower and row_lower[col]:
                            categoria = str(row_lower[col]).strip().title()
                            break
                    
                    # Buscar preços por tamanho
                    precos = {}
                    for tam_key, tam_aliases in tamanho_map.items():
                        for alias in tam_aliases:
                            if alias in row_lower and row_lower[alias]:
                                try:
                                    val = str(row_lower[alias]).replace('R$', '').replace('r$', '').strip()
                                    val = val.replace('.', '').replace(',', '.')
                                    preco = float(val)
                                    if preco > 0:
                                        precos[tam_key] = preco
                                        break
                                except:
                                    continue
                    
                    # Se não achou, usar padrão
                    if not precos:
                        precos = {'curto': 0.0}
                    
                    # Inserir serviços
                    for tam_key, preco in precos.items():
                        tam_nome = tam_key.replace('_', ' ').title()
                        
                        db.servicos.insert_one({
                            'nome': nome,
                            'sku': f"{nome.upper().replace(' ', '-')}-{tam_nome.upper().replace(' ', '-')}",
                            'tamanho': tam_nome,
                            'preco': preco,
                            'categoria': categoria,
                            'ativo': True,
                            'created_at': datetime.now()
                        })
                    
                    cs += 1
                    logger.debug(f"✅ Serviço {cs}: {nome} ({len(precos)} tamanhos)")
                    
                except Exception as e:
                    logger.error(f"❌ Erro linha {idx}: {e}")
                    ce += 1
                    continue
        
        # Remover arquivo
        os.remove(fp)
        logger.info(f"🗑️ Arquivo temporário removido: {fp}")
        
        msg = f'{cs} registros importados com sucesso!'
        if ce > 0:
            msg += f' ({ce} linhas com erro foram ignoradas)'
        
        logger.info(f"✅ Importação concluída: {cs} sucesso, {ce} erros")
        
        return jsonify({
            'success': True,
            'message': msg,
            'count_success': cs,
            'count_error': ce
        })
    
    except Exception as e:
        logger.error(f"❌ Erro geral na importação: {e}")
        if os.path.exists(fp):
            os.remove(fp)
        return jsonify({'success': False, 'message': f'Erro ao processar: {str(e)}'})

# ===== DOWNLOAD TEMPLATE =====
@app.route('/api/template/download/<tipo>')
@login_required
def download_template(tipo):
    logger.info(f"📥 Download template: {tipo}")
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    if tipo == 'produtos':
        writer.writerow(['nome', 'marca', 'sku', 'preco', 'custo', 'estoque', 'categoria'])
        writer.writerow(['Shampoo 500ml', 'Loreal', 'SHAMP-500', '49.90', '20.00', '50', 'SHAMPOO'])
        writer.writerow(['Condicionador 400ml', 'Pantene', 'COND-400', '39.90', '15.00', '30', 'CONDICIONADOR'])
    else:
        writer.writerow(['nome', 'categoria', 'kids', 'masculino', 'curto', 'medio', 'longo', 'extra_longo'])
        writer.writerow(['Hidratação', 'Tratamento', '50', '60', '80', '100', '120', '150'])
        writer.writerow(['Corte', 'Cabelo', '40', '50', '60', '80', '100', '120'])
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'template_{tipo}.csv'
    )
# ===== GERAÇÃO DE PDF PROFISSIONAL (MODELO ANEXADO) =====
def gerar_contrato_pdf(orc):
    """
    Gera PDF do contrato igual ao modelo fornecido
    """
    logger.info(f"📄 Gerando PDF para contrato #{orc.get('numero')}")
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    
    # ===== CABEÇALHO =====
    c.setFillColor(HexColor('#7C3AED'))
    c.setFont('Helvetica-Bold', 28)
    c.drawRightString(w - 2*cm, h - 2*cm, 'BIOMA')
    
    c.setFillColor(black)
    c.setFont('Helvetica-Bold', 16)
    c.drawCentredString(w/2, h - 3*cm, 'CONTRATO DE PRESTAÇÃO DE SERVIÇOS')
    
    c.setFont('Helvetica', 10)
    c.drawCentredString(w/2, h - 3.7*cm, 'Pelo presente Instrumento Particular e na melhor forma de direito, as partes abaixo qualificadas:')
    
    # Linha horizontal
    c.setStrokeColor(HexColor('#7C3AED'))
    c.setLineWidth(2)
    c.line(2*cm, h - 4.2*cm, w - 2*cm, h - 4.2*cm)
    
    y = h - 5*cm
    
    # ===== PARTES =====
    c.setFillColor(black)
    c.setFont('Helvetica-Bold', 12)
    c.drawCentredString(w/2, y, 'PARTES')
    y -= 0.8*cm
    
    # CONTRATANTE
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(w/2, y, 'CONTRATANTE')
    y -= 0.6*cm
    
    c.setFont('Helvetica', 9)
    c.drawString(2*cm, y, f"Nome: {orc.get('cliente_nome', 'N/A')}")
    y -= 0.5*cm
    
    c.drawString(2*cm, y, f"CPF: {orc.get('cliente_cpf', 'N/A')}")
    if orc.get('cliente_telefone'):
        c.drawString(11*cm, y, f"Tel: {orc['cliente_telefone']}")
    y -= 0.5*cm
    
    if orc.get('cliente_email'):
        c.drawString(2*cm, y, f"E-mail: {orc['cliente_email']}")
    y -= 0.8*cm
    
    # CONTRATADA
    cfg = db.config.find_one({'key': 'unidade'}) or {}
    
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(w/2, y, 'CONTRATADA')
    y -= 0.6*cm
    
    c.setFont('Helvetica', 9)
    c.drawString(2*cm, y, f"Raz. Soc: {cfg.get('nome', 'BIOMA UBERABA')}")
    y -= 0.5*cm
    
    c.drawString(2*cm, y, f"CNPJ: {cfg.get('cnpj', '49.470.937/0001-10')}")
    y -= 0.5*cm
    
    c.drawString(2*cm, y, "Cidade: UBERABA")
    c.drawString(11*cm, y, "Estado: MINAS GERAIS")
    y -= 0.5*cm
    
    c.drawString(2*cm, y, f"END.: {cfg.get('endereco', 'Av. Santos Dumont 3110 - Santa Maria - CEP 38050-400')}")
    y -= 0.5*cm
    
    c.drawString(2*cm, y, f"Tel: {cfg.get('telefone', '34 99235-5890')}")
    c.drawString(11*cm, y, f"E-mail: {cfg.get('email', 'biomauberaba@gmail.com')}")
    y -= 1*cm
    
    # ===== ALERGIAS E CONDIÇÕES DE SAÚDE =====
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(w/2, y, 'ALERGIAS E CONDIÇÕES ESPECIAIS DE SAÚDE')
    y -= 0.6*cm
    
    c.setFont('Helvetica', 9)
    c.drawString(2*cm, y, "SUBSTÂNCIAS ALÉRGENAS:")
    y -= 0.5*cm
    
    c.setFillColor(HexColor('#DC2626'))
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(w/2, y, 'NÃO')
    c.setFillColor(black)
    y -= 0.7*cm
    
    c.setFont('Helvetica', 9)
    c.drawString(2*cm, y, "CONDIÇÕES ESPECIAIS DE SAÚDE:")
    y -= 0.5*cm
    
    c.setFillColor(HexColor('#DC2626'))
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(w/2, y, 'NÃO')
    c.setFillColor(black)
    y -= 1*cm
    
    # ===== TABELA DE SERVIÇOS =====
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(w/2, y, 'SERVIÇOS')
    y -= 0.6*cm
    
    # Preparar dados da tabela
    table_data = [['Qtde.', 'SERVIÇOS', 'Desc.', 'Total s/ Desc.', 'Total c/ Desc.']]
    
    for srv in orc.get('servicos', []):
        valor_sem_desc = srv['preco_unit'] * srv['qtd']
        table_data.append([
            str(srv['qtd']),
            f"{srv['nome']} - {srv['tamanho']}",
            f"{srv.get('desconto', 0)}%",
            f"R$ {valor_sem_desc:.2f}",
            f"R$ {srv['total']:.2f}"
        ])
    
    # Criar tabela
    if len(table_data) > 1:
        table = Table(table_data, colWidths=[2*cm, 9*cm, 2*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#7C3AED')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        table.wrapOn(c, w, h)
        table_height = len(table_data) * 0.8*cm
        table.drawOn(c, 2*cm, y - table_height)
        y -= (table_height + 0.5*cm)
    
    y -= 0.5*cm
    
    # ===== TOTAIS =====
    c.setFont('Helvetica-Bold', 10)
    c.drawRightString(15*cm, y, 'TOTAL BRUTO')
    c.drawRightString(w - 2*cm, y, f"R$ {orc.get('subtotal', 0):.2f}")
    y -= 0.5*cm
    
    if orc.get('desconto_valor', 0) > 0:
        c.drawRightString(15*cm, y, f"Desconto Total ({orc.get('desconto_global', 0)}%)")
        c.drawRightString(w - 2*cm, y, f"R$ {orc['desconto_valor']:.2f}")
        y -= 0.5*cm
    
    c.setFont('Helvetica-Bold', 12)
    c.setFillColor(HexColor('#7C3AED'))
    c.drawRightString(15*cm, y, 'TOTAL')
    c.drawRightString(w - 2*cm, y, f"R$ {orc.get('total_final', 0):.2f}")
    c.setFillColor(black)
    y -= 0.8*cm
    
    # ===== UTILIZAÇÃO =====
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(w/2, y, 'UTILIZAÇÃO')
    y -= 0.5*cm
    
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(w/2, y, 'PRAZO PARA UTILIZAÇÃO')
    y -= 0.5*cm
    
    c.setFont('Helvetica', 9)
    c.drawCentredString(w/2, y, '03 mês(es) contados da assinatura deste Contrato.')
    y -= 1*cm
    
    # ===== VALOR E FORMA DE PAGAMENTO =====
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(w/2, y, 'VALOR E FORMA DE PAGAMENTO')
    y -= 0.6*cm
    
    c.setFont('Helvetica', 9)
    c.drawString(2*cm, y, f"VALOR TOTAL: R$ {orc.get('total_final', 0):.2f}")
    y -= 0.5*cm
    
    pagamento_tipo = orc.get('pagamento', {}).get('tipo', 'Pix')
    c.drawString(2*cm, y, f"FORMA DE PAGAMENTO: {pagamento_tipo}")
    y -= 1*cm
    
    # ===== DISPOSIÇÕES GERAIS =====
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(w/2, y, 'DISPOSIÇÕES GERAIS')
    y -= 0.5*cm
    
    c.setFont('Helvetica', 8)
    texto = 'Pelo presente instrumento particular, as "Partes" resolvem celebrar o presente "Contrato", de acordo com as cláusulas e condições a seguir.'
    c.drawString(2*cm, y, texto)
    y -= 0.5*cm
    
    clausulas = [
        "1. O Contrato tem por objeto a prestação de serviços acima descritos, pela Contratada à Contratante, mediante agendamento prévio.",
        "2. A Contratante declara estar ciente que (i) os serviços têm caráter pessoal e não são transferíveis.",
        "3. Os serviços deverão ser utilizados em conformidade com o prazo acima indicado à Contratante."
    ]
    
    for clausula in clausulas:
        # Quebrar texto se muito longo
        words = clausula.split()
        line = ""
        for word in words:
            if len(line + word) < 120:
                line += word + " "
            else:
                c.drawString(2*cm, y, line.strip())
                y -= 0.35*cm
                line = word + " "
        if line:
            c.drawString(2*cm, y, line.strip())
            y -= 0.35*cm
        y -= 0.2*cm
    
    y -= 0.5*cm
    
    # ===== ASSINATURAS =====
    from datetime import datetime
    meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 
             'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
    
    agora = datetime.now()
    data_extenso = f"UBERABA, {agora.day} de {meses[agora.month - 1]} de {agora.year}"
    
    c.setFont('Helvetica', 9)
    c.drawCentredString(w/2, y, data_extenso)
    y -= 1.5*cm
    
    # Linhas de assinatura
    c.setLineWidth(1)
    c.line(3*cm, y, 8.5*cm, y)
    c.line(11*cm, y, 17*cm, y)
    y -= 0.4*cm
    
    c.setFont('Helvetica-Bold', 8)
    c.drawCentredString(5.75*cm, y, f"CONTRATANTE: {orc.get('cliente_nome', 'N/A')}")
    c.drawCentredString(14*cm, y, f"CONTRATADA: BIOMA UBERABA - {cfg.get('cnpj', '49.470.937/0001-10')}")
    
    # ===== RODAPÉ =====
    c.setFont('Helvetica', 7)
    c.setFillColor(HexColor('#6B7280'))
    c.drawCentredString(
        w/2, 
        1.5*cm, 
        f"Contrato #{orc.get('numero')} | BIOMA UBERABA | {cfg.get('telefone', '34 99235-5890')} | {cfg.get('email', 'biomauberaba@gmail.com')}"
    )
    
    c.save()
    buffer.seek(0)
    
    logger.info(f"✅ PDF gerado com sucesso para contrato #{orc.get('numero')}")
    return buffer.getvalue()

# ===== ROTA PARA GERAR/BAIXAR PDF =====
@app.route('/api/gerar-contrato-pdf/<id>')
@login_required
def gerar_contrato_pdf_route(id):
    logger.info(f"📥 Solicitação download PDF - ID: {id}")
    
    try:
        orc = db.orcamentos.find_one({'_id': ObjectId(id)})
        
        if not orc:
            logger.warning(f"⚠️ Orçamento não encontrado: {id}")
            return "Orçamento não encontrado", 404
        
        pdf_bytes = gerar_contrato_pdf(orc)
        
        logger.info(f"✅ PDF enviado - Contrato #{orc.get('numero')}")
        
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'contrato_bioma_{orc["numero"]}.pdf'
        )
    except Exception as e:
        logger.error(f"❌ Erro gerar PDF: {e}")
        return f"Erro ao gerar PDF: {str(e)}", 500

# ===== ENDPOINT DE DEBUG =====
@app.route('/api/debug/test-db')
@login_required
def test_db():
    logger.info("🔬 Teste de debug do banco de dados")
    
    try:
        # Testar conexão
        db.command('ping')
        
        # Contar documentos
        counts = {
            'clientes': db.clientes.count_documents({}),
            'servicos': db.servicos.count_documents({}),
            'produtos': db.produtos.count_documents({}),
            'orcamentos': db.orcamentos.count_documents({}),
            'profissionais': db.profissionais.count_documents({}),
            'fila': db.fila_atendimento.count_documents({})
        }
        
        # Pegar exemplos
        samples = {
            'cliente': jsonify_safe(db.clientes.find_one()),
            'servico': jsonify_safe(db.servicos.find_one()),
            'produto': jsonify_safe(db.produtos.find_one()),
            'orcamento': jsonify_safe(db.orcamentos.find_one())
        }
        
        logger.info(f"✅ Debug OK - Counts: {counts}")
        
        return jsonify({
            'success': True,
            'mongodb': 'CONNECTED',
            'database': 'bioma_db',
            'counts': counts,
            'samples': samples,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Erro no debug: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

# ===== INICIALIZAÇÃO DO BANCO DE DADOS =====
def init_db():
    """Inicializa banco com dados padrão"""
    if db is None:
        logger.warning("⚠️ Banco de dados não disponível - Pulando inicialização")
        return
    
    logger.info("🔧 Inicializando banco de dados...")
    
    # Usuário admin
    if db.users.count_documents({}) == 0:
        db.users.insert_one({
            'name': 'Administrador',
            'username': 'admin',
            'email': 'admin@bioma.com',
            'password': generate_password_hash('admin123'),
            'role': 'admin',
            'theme': 'light',
            'created_at': datetime.now()
        })
        logger.info("✅ Usuário admin criado: admin/admin123")
    
    # Serviços padrão
    if db.servicos.count_documents({}) == 0:
        servicos_padrao = [
            ('Hidratação', 'Tratamento', 50, 60, 80, 100, 120, 150),
            ('Corte Feminino', 'Cabelo', 40, 50, 60, 80, 100, 120),
            ('Corte Masculino', 'Cabelo', 30, 40, 50, 60, 70, 80)
        ]
        
        for nome, cat, kids, masc, curto, medio, longo, xl in servicos_padrao:
            tamanhos = {
                'Kids': kids,
                'Masculino': masc,
                'Curto': curto,
                'Médio': medio,
                'Longo': longo,
                'Extra Longo': xl
            }
            
            for tam, preco in tamanhos.items():
                db.servicos.insert_one({
                    'nome': nome,
                    'sku': f"{nome.upper().replace(' ', '-')}-{tam.upper().replace(' ', '-')}",
                    'tamanho': tam,
                    'preco': preco,
                    'categoria': cat,
                    'ativo': True,
                    'created_at': datetime.now()
                })
        
        logger.info("✅ Serviços padrão criados (18 SKUs)")
    
    # Produto padrão
    if db.produtos.count_documents({}) == 0:
        db.produtos.insert_one({
            'nome': 'Shampoo 500ml',
            'marca': 'BIOMA',
            'sku': 'SHAMP-500',
            'preco': 49.90,
            'custo': 20.00,
            'estoque': 50,
            'categoria': 'SHAMPOO',
            'ativo': True,
            'created_at': datetime.now()
        })
        logger.info("✅ Produto padrão criado")
    
    # Profissional padrão
    if db.profissionais.count_documents({}) == 0:
        db.profissionais.insert_one({
            'nome': 'Maria Silva',
            'cpf': '000.000.000-00',
            'email': 'maria@bioma.com',
            'telefone': '(34) 99999-9999',
            'especialidade': 'Coloração',
            'comissao_perc': 10.0,
            'ativo': True,
            'created_at': datetime.now()
        })
        logger.info("✅ Profissional padrão criado")
    
    # Configuração padrão
    if db.config.count_documents({}) == 0:
        db.config.insert_one({
            'key': 'unidade',
            'nome': 'BIOMA UBERABA',
            'cnpj': '49.470.937/0001-10',
            'endereco': 'Av. Santos Dumont 3110 - Santa Maria - Uberaba/MG - CEP 38050-400',
            'telefone': '34 99235-5890',
            'email': 'biomauberaba@gmail.com'
        })
        logger.info("✅ Configuração padrão criada")
    
    # Pacotes do Clube BIOMA
    if db.pacotes.count_documents({}) == 0:
        pacotes = [
            {
                'nome': 'BRONZE',
                'tipo': 'mensal',
                'valor': 100.00,
                'conteudo': '1 corte + 1 hidratação por mês',
                'beneficios': '5% desconto, 5% cashback',
                'desconto_perc': 5,
                'cashback_perc': 5,
                'ativo': True
            },
            {
                'nome': 'PRATA',
                'tipo': 'semestral',
                'valor': 540.00,
                'conteudo': '6 cortes + 6 hidratações semestrais',
                'beneficios': '10% desconto, 10% cashback, prioridade fila',
                'desconto_perc': 10,
                'cashback_perc': 10,
                'ativo': True
            },
            {
                'nome': 'OURO',
                'tipo': 'anual',
                'valor': 1000.00,
                'conteudo': '12 cortes + 12 hidratações + 4 tratamentos especiais',
                'beneficios': '15% desconto, 15% cashback, atendimento VIP',
                'desconto_perc': 15,
                'cashback_perc': 15,
                'ativo': True
            }
        ]
        
        for pacote in pacotes:
            pacote['created_at'] = datetime.now()
            db.pacotes.insert_one(pacote)
        
        logger.info("✅ Pacotes Clube BIOMA criados")
    
    logger.info("🎉 Banco de dados inicializado com sucesso!")

# ===== EXECUÇÃO PRINCIPAL =====
if __name__ == '__main__':
    # Banner inicial
    print("\n" + "=" * 80)
    print("🌳 BIOMA UBERABA v2.5 - ULTRA PROFISSIONAL")
    print("=" * 80)
    
    # Inicializar banco
    init_db()
    
    # Informações do sistema
    is_prod = os.getenv('FLASK_ENV') == 'production'
    url = 'https://bioma-system2.onrender.com' if is_prod else 'http://localhost:5000'
    
    print(f"🚀 URL: {url}")
    print(f"🔒 HTTPS: {'✅ ATIVO' if is_prod else '⚠️  Local'}")
    print(f"👤 Login padrão: admin / admin123")
    print(f"📧 Email: {'✅ Configurado' if os.getenv('MAILERSEND_API_KEY') else '⚠️  Não configurado'}")
    print(f"📱 SMS: {'✅ Configurado' if os.getenv('MAILERSEND_API_KEY') else '⚠️  Não configurado'}")
    print(f"💾 MongoDB: {'✅ CONECTADO' if db is not None else '❌ OFFLINE'}")
    print(f"📊 Logs: {'✅ Ativado (INFO)' if logger.level == logging.INFO else 'DEBUG'}")
    print("=" * 80)
    print(f"🕐 Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"👨‍💻 Desenvolvedor: @juanmarco1999")
    print(f"📧 Email: 180147064@aluno.unb.br")
    print("=" * 80 + "\n")
    
    # Iniciar servidor
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"🚀 Iniciando servidor Flask na porta {port}...")
    
    app.run(
        debug=False,
        host='0.0.0.0',
        port=port,
        threaded=True
    )
    