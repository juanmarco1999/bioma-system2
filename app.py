#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA UBERABA v3.1 - Sistema Ultra Profissional
Desenvolvedor: Juan Marco (@juanmarco1999)
Email: 180147064@aluno.unb.br
Data: 2025-10-05
"""

from flask import Flask, render_template, request, jsonify, session, send_file
from flask_cors import CORS
from pymongo import MongoClient, ASCENDING, DESCENDING
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
import random
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle

# ===== LOGGING =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

load_dotenv()

# ===== FLASK CONFIG =====
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'bioma-2025-v3-ultra-secure-key')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

CORS(app, supports_credentials=True)

# ===== MONGODB CONNECTION =====
def get_db():
    try:
        username = urllib.parse.quote_plus(os.getenv('MONGO_USERNAME', ''))
        password = urllib.parse.quote_plus(os.getenv('MONGO_PASSWORD', ''))
        cluster = os.getenv('MONGO_CLUSTER', '')
        
        if not all([username, password, cluster]):
            logger.error("❌ MongoDB credentials missing")
            return None
        
        uri = f"mongodb+srv://{username}:{password}@{cluster}/bioma_db?retryWrites=true&w=majority"
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        
        db_instance = client.bioma_db
        logger.info("✅ MongoDB Connected")
        return db_instance
        
    except Exception as e:
        logger.error(f"❌ MongoDB Error: {e}")
        return None

db = get_db()

# ===== HELPER FUNCTIONS =====
def convert_objectid(obj):
    """Convert ObjectId to string recursively"""
    if isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    elif isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            if isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                result[key] = convert_objectid(value)
            else:
                result[key] = value
        return result
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning(f"🚫 Unauthorized access: {request.endpoint}")
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

# ===== EMAIL & SMS =====
def send_email(to, name, subject, html_content, pdf=None):
    api_key = os.getenv('MAILERSEND_API_KEY')
    if not api_key:
        logger.warning("⚠️ MailerSend API Key not configured")
        return {'success': False}
    
    data = {
        "from": {"email": os.getenv('MAILERSEND_FROM_EMAIL', 'noreply@bioma.com'), "name": "BIOMA Uberaba"},
        "to": [{"email": to, "name": name}],
        "subject": subject,
        "html": html_content
    }
    
    if pdf:
        import base64
        data['attachments'] = [{
            "filename": pdf['filename'], 
            "content": base64.b64encode(pdf['content']).decode()
        }]
    
    try:
        r = requests.post("https://api.mailersend.com/v1/email",
                         headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                         json=data, timeout=10)
        if r.status_code == 202:
            logger.info(f"📧 Email sent to: {to}")
            return {'success': True}
        logger.error(f"❌ Email failed: {r.status_code}")
        return {'success': False}
    except Exception as e:
        logger.error(f"❌ Email exception: {e}")
        return {'success': False}

def send_sms(phone, message):
    api_key = os.getenv('MAILERSEND_API_KEY')
    if not api_key:
        return {'success': False}
    
    formatted_phone = '+55' + ''.join(filter(str.isdigit, phone)) if not phone.startswith('+') else phone
    
    try:
        r = requests.post("https://api.mailersend.com/v1/sms",
                         headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                         json={"from": "BIOMA", "to": [formatted_phone], "text": message}, timeout=10)
        if r.status_code == 202:
            logger.info(f"📱 SMS sent to: {phone}")
            return {'success': True}
        return {'success': False}
    except:
        return {'success': False}

# ===== ROUTES =====
@app.route('/')
def index():
    logger.info(f"🌐 Index accessed from {request.remote_addr}")
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'time': datetime.now().isoformat(),
        'database': 'connected' if db is not None else 'disconnected'
    }), 200

# ===== AUTH =====
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    logger.info(f"👤 Register attempt: {data.get('username')}")
    
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    if db.users.find_one({'$or': [{'username': data['username']}, {'email': data['email']}]}):
        logger.warning(f"⚠️ User already exists: {data.get('username')}")
        return jsonify({'success': False, 'message': 'Usuário ou email já existe'})
    
    # Gerar código de verificação
    verification_code = str(random.randint(100000, 999999))
    
    user_data = {
        'name': data['name'],
        'username': data['username'],
        'email': data['email'],
        'password': generate_password_hash(data['password']),
        'role': 'user',
        'theme': 'light',
        'verified': False,
        'verification_code': verification_code,
        'created_at': datetime.now()
    }
    
    db.users.insert_one(user_data)
    
    # Enviar email de verificação
    send_email(
        data['email'],
        data['name'],
        'Código de Verificação BIOMA',
        f"<h2>Bem-vindo ao BIOMA Uberaba!</h2><p>Seu código de verificação é: <strong style='font-size:24px'>{verification_code}</strong></p>"
    )
    
    # Enviar SMS se tiver telefone
    if data.get('telefone'):
        send_sms(data['telefone'], f"BIOMA: Seu código de verificação é {verification_code}")
    
    logger.info(f"✅ User registered: {data['username']}")
    return jsonify({'success': True, 'message': 'Conta criada! Verifique seu email para o código de verificação.'})

@app.route('/api/verify', methods=['POST'])
def verify():
    data = request.json
    username = data.get('username')
    code = data.get('code')
    
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    user = db.users.find_one({'username': username})
    
    if not user:
        return jsonify({'success': False, 'message': 'Usuário não encontrado'})
    
    if user.get('verification_code') == code:
        db.users.update_one({'username': username}, {'$set': {'verified': True}, '$unset': {'verification_code': ''}})
        logger.info(f"✅ User verified: {username}")
        return jsonify({'success': True, 'message': 'Conta verificada com sucesso!'})
    else:
        return jsonify({'success': False, 'message': 'Código inválido'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    logger.info(f"🔐 Login attempt: {data.get('username')}")
    
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    user = db.users.find_one({'$or': [{'username': data['username']}, {'email': data['username']}]})
    
    if user and check_password_hash(user['password'], data['password']):
        if not user.get('verified', False):
            logger.warning(f"⚠️ Unverified user: {data.get('username')}")
            return jsonify({'success': False, 'message': 'Conta não verificada. Verifique seu email.'})
        
        session.permanent = True
        session['user_id'] = str(user['_id'])
        session['username'] = user['username']
        
        # Enviar SMS de login
        if user.get('telefone'):
            send_sms(user['telefone'], f"BIOMA: Login realizado em {datetime.now().strftime('%d/%m às %H:%M')}")
        
        logger.info(f"✅ Login successful: {user['username']}")
        
        return jsonify({
            'success': True,
            'user': {
                'id': str(user['_id']),
                'name': user['name'],
                'username': user['username'],
                'theme': user.get('theme', 'light')
            }
        })
    
    logger.warning(f"❌ Login failed: {data.get('username')}")
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
        if db is None:
            return jsonify({'success': False})
        try:
            user = db.users.find_one({'_id': ObjectId(session['user_id'])})
            if user:
                return jsonify({
                    'success': True,
                    'user': {
                        'id': str(user['_id']),
                        'name': user['name'],
                        'username': user['username'],
                        'theme': user.get('theme', 'light')
                    }
                })
        except:
            pass
    return jsonify({'success': False})

@app.route('/api/update-theme', methods=['POST'])
@login_required
def update_theme():
    if db is None:
        return jsonify({'success': False}), 500
    
    theme = request.json['theme']
    db.users.update_one({'_id': ObjectId(session['user_id'])}, {'$set': {'theme': theme}})
    logger.info(f"🎨 Theme updated: {theme}")
    return jsonify({'success': True})

# ===== SYSTEM STATUS =====
@app.route('/api/system/status')
@login_required
def system_status():
    logger.info("📊 System status check")
    
    mongo_ok = False
    mongo_msg = 'Desconectado'
    last_check = datetime.now().isoformat()
    
    try:
        if db is not None:
            db.command('ping')
            mongo_ok = True
            mongo_msg = 'Conectado e operacional'
            logger.info("✅ MongoDB ping OK")
        else:
            mongo_msg = 'Banco não inicializado'
    except Exception as e:
        logger.error(f"❌ MongoDB ping failed: {e}")
        mongo_msg = f'Erro: {str(e)[:100]}'
    
    return jsonify({
        'success': True,
        'status': {
            'mongodb': {
                'operational': mongo_ok,
                'message': mongo_msg,
                'last_check': last_check
            },
            'mailersend': {
                'operational': bool(os.getenv('MAILERSEND_API_KEY')),
                'message': 'Configurado' if os.getenv('MAILERSEND_API_KEY') else 'API Key ausente'
            },
            'server': {
                'time': datetime.now().isoformat(),
                'environment': os.getenv('FLASK_ENV', 'development'),
                'version': '3.1.0'
            }
        }
    })

# ===== DASHBOARD =====
@app.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    logger.info("📊 Loading dashboard stats")
    
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        stats = {
            'total_orcamentos': db.orcamentos.count_documents({}),
            'total_clientes': db.clientes.count_documents({}),
            'total_servicos': db.servicos.count_documents({'ativo': True}),
            'faturamento': sum(o.get('total_final', 0) for o in db.orcamentos.find({'status': 'Aprovado'})),
            'produtos_estoque_baixo': db.produtos.count_documents({'$expr': {'$lte': ['$estoque', '$estoque_minimo']}}),
            'agendamentos_hoje': db.agendamentos.count_documents({
                'data': {
                    '$gte': datetime.now().replace(hour=0, minute=0, second=0),
                    '$lt': datetime.now().replace(hour=23, minute=59, second=59)
                },
                'status': {'$in': ['confirmado', 'em_andamento']}
            }) if db else 0
        }
        
        logger.info(f"✅ Stats loaded: {stats['total_orcamentos']} orçamentos")
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        logger.error(f"❌ Dashboard error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== CLIENTES =====
@app.route('/api/clientes', methods=['GET', 'POST'])
@login_required
def clientes():
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    if request.method == 'GET':
        logger.info("📋 Loading clients")
        try:
            clientes_list = list(db.clientes.find({}).sort('nome', 1))
            
            for cliente in clientes_list:
                cliente_id = cliente['_id']
                total_gasto = sum(o.get('total_final', 0) for o in db.orcamentos.find({'cliente_cpf': cliente.get('cpf'), 'status': 'Aprovado'}))
                cliente['total_gasto'] = total_gasto
                
                ultimo_orc = db.orcamentos.find_one({'cliente_cpf': cliente.get('cpf')}, sort=[('created_at', DESCENDING)])
                cliente['ultima_visita'] = ultimo_orc['created_at'] if ultimo_orc else None
                cliente['total_visitas'] = db.orcamentos.count_documents({'cliente_cpf': cliente.get('cpf')})
            
            result = convert_objectid(clientes_list)
            logger.info(f"✅ {len(result)} clients loaded")
            return jsonify({'success': True, 'clientes': result})
        except Exception as e:
            logger.error(f"❌ Error loading clients: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # POST
    data = request.json
    logger.info(f"➕ Saving client: {data.get('nome')}")
    
    try:
        existing = db.clientes.find_one({'cpf': data['cpf']})
        
        cliente_data = {**data, 'updated_at': datetime.now()}
        
        if existing:
            db.clientes.update_one({'cpf': data['cpf']}, {'$set': cliente_data})
        else:
            cliente_data['created_at'] = datetime.now()
            cliente_data['tags'] = []
            cliente_data['notas'] = []
            db.clientes.insert_one(cliente_data)
        
        logger.info(f"✅ Client saved: {data['nome']}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Error saving client: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clientes/<id>', methods=['DELETE'])
@login_required
def delete_cliente(id):
    if db is None:
        return jsonify({'success': False}), 500
    
    logger.info(f"🗑️ Deleting client: {id}")
    try:
        result = db.clientes.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Cliente não encontrado'})
    except Exception as e:
        logger.error(f"❌ Error deleting client: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clientes/buscar')
@login_required
def buscar_clientes():
    if db is None:
        return jsonify({'success': False}), 500
    
    termo = request.args.get('termo', '')
    logger.info(f"🔍 Searching clients: {termo}")
    try:
        regex = {'$regex': termo, '$options': 'i'}
        clientes = list(db.clientes.find({'$or': [{'nome': regex}, {'cpf': regex}]}).limit(10))
        result = convert_objectid(clientes)
        return jsonify({'success': True, 'clientes': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== PROFISSIONAIS =====
@app.route('/api/profissionais', methods=['GET', 'POST'])
@login_required
def profissionais():
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    if request.method == 'GET':
        logger.info("📋 Loading professionals")
        try:
            profs = list(db.profissionais.find({}).sort('nome', 1))
            result = convert_objectid(profs)
            logger.info(f"✅ {len(result)} professionals loaded")
            return jsonify({'success': True, 'profissionais': result})
        except Exception as e:
            logger.error(f"❌ Error loading professionals: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # POST
    data = request.json
    logger.info(f"➕ Saving professional: {data.get('nome')}")
    try:
        db.profissionais.insert_one({
            'nome': data['nome'],
            'cpf': data['cpf'],
            'email': data.get('email', ''),
            'telefone': data.get('telefone', ''),
            'especialidade': data.get('especialidade', ''),
            'comissao_perc': float(data.get('comissao_perc', 0)),
            'ativo': True,
            'created_at': datetime.now()
        })
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Error saving professional: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profissionais/<id>', methods=['DELETE'])
@login_required
def delete_profissional(id):
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        result = db.profissionais.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            return jsonify({'success': True})
        return jsonify({'success': False})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== SERVIÇOS =====
@app.route('/api/servicos', methods=['GET', 'POST'])
@login_required
def servicos():
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    if request.method == 'GET':
        logger.info("📋 Loading services")
        try:
            servs = list(db.servicos.find({}).sort('nome', 1))
            result = convert_objectid(servs)
            logger.info(f"✅ {len(result)} services loaded")
            return jsonify({'success': True, 'servicos': result})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # POST
    data = request.json
    logger.info(f"➕ Creating service: {data.get('nome')}")
    try:
        tamanhos = {
            'Kids': data.get('preco_kids', 0),
            'Masculino': data.get('preco_masculino', 0),
            'Curto': data.get('preco_curto', 0),
            'Médio': data.get('preco_medio', 0),
            'Longo': data.get('preco_longo', 0),
            'Extra Longo': data.get('preco_extra_longo', 0)
        }
        
        count = 0
        for tam, preco in tamanhos.items():
            if preco > 0:
                db.servicos.insert_one({
                    'nome': data['nome'],
                    'sku': f"{data['nome'].upper().replace(' ', '-')}-{tam.upper().replace(' ', '-')}",
                    'tamanho': tam,
                    'preco': float(preco),
                    'categoria': data.get('categoria', 'Serviço'),
                    'duracao': int(data.get('duracao', 60)),
                    'ativo': True,
                    'created_at': datetime.now()
                })
                count += 1
        
        logger.info(f"✅ Service created: {count} SKUs")
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        logger.error(f"❌ Error creating service: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/servicos/<id>', methods=['DELETE'])
@login_required
def delete_servico(id):
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        result = db.servicos.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            return jsonify({'success': True})
        return jsonify({'success': False})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/servicos/buscar')
@login_required
def buscar_servicos():
    if db is None:
        return jsonify({'success': False}), 500
    
    termo = request.args.get('termo', '')
    try:
        regex = {'$regex': termo, '$options': 'i'}
        servicos = list(db.servicos.find({'nome': regex}).limit(20))
        result = convert_objectid(servicos)
        return jsonify({'success': True, 'servicos': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== PRODUTOS =====
@app.route('/api/produtos', methods=['GET', 'POST'])
@login_required
def produtos():
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    if request.method == 'GET':
        logger.info("📋 Loading products")
        try:
            prods = list(db.produtos.find({}).sort('nome', 1))
            result = convert_objectid(prods)
            logger.info(f"✅ {len(result)} products loaded")
            return jsonify({'success': True, 'produtos': result})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # POST
    data = request.json
    logger.info(f"➕ Creating product: {data.get('nome')}")
    try:
        produto_id = db.produtos.insert_one({
            'nome': data['nome'],
            'marca': data.get('marca', ''),
            'sku': data.get('sku', ''),
            'preco': float(data.get('preco', 0)),
            'custo': float(data.get('custo', 0)),
            'estoque': int(data.get('estoque', 0)),
            'estoque_minimo': int(data.get('estoque_minimo', 5)),
            'categoria': data.get('categoria', 'Produto'),
            'ativo': True,
            'created_at': datetime.now()
        }).inserted_id
        
        if int(data.get('estoque', 0)) > 0:
            db.estoque_movimentacoes.insert_one({
                'produto_id': produto_id,
                'tipo': 'entrada',
                'quantidade': int(data.get('estoque', 0)),
                'motivo': 'Cadastro inicial',
                'custo_unitario': float(data.get('custo', 0)),
                'usuario': session.get('username'),
                'data': datetime.now()
            })
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Error creating product: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/produtos/<id>', methods=['DELETE'])
@login_required
def delete_produto(id):
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        result = db.produtos.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            return jsonify({'success': True})
        return jsonify({'success': False})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/produtos/buscar')
@login_required
def buscar_produtos():
    if db is None:
        return jsonify({'success': False}), 500
    
    termo = request.args.get('termo', '')
    try:
        regex = {'$regex': termo, '$options': 'i'}
        produtos = list(db.produtos.find({'nome': regex}).limit(20))
        result = convert_objectid(produtos)
        return jsonify({'success': True, 'produtos': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== ORÇAMENTOS =====
@app.route('/api/orcamentos', methods=['GET', 'POST'])
@login_required
def orcamentos():
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    if request.method == 'GET':
        logger.info("📋 Loading budgets")
        try:
            status = request.args.get('status')
            query = {'status': status} if status else {}
            orcs = list(db.orcamentos.find(query).sort('created_at', DESCENDING))
            result = convert_objectid(orcs)
            logger.info(f"✅ {len(result)} budgets loaded")
            return jsonify({'success': True, 'orcamentos': result})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # POST
    data = request.json
    logger.info(f"➕ Creating budget for: {data.get('cliente_nome')}")
    
    try:
        # Salvar/atualizar cliente
        db.clientes.update_one(
            {'cpf': data['cliente_cpf']},
            {'$set': {
                'cpf': data['cliente_cpf'],
                'nome': data['cliente_nome'],
                'email': data.get('cliente_email', ''),
                'telefone': data.get('cliente_telefone', ''),
                'updated_at': datetime.now()
            }},
            upsert=True
        )
        
        # Calcular totais
        subtotal = sum(s['total'] for s in data.get('servicos', [])) + sum(p['total'] for p in data.get('produtos', []))
        desconto_valor = subtotal * (data.get('desconto_global', 0) / 100)
        total_com_desconto = subtotal - desconto_valor
        cashback_valor = total_com_desconto * (data.get('cashback_perc', 0) / 100)
        
        # Gerar número
        ultimo = db.orcamentos.find_one(sort=[('numero', DESCENDING)])
        numero = (ultimo['numero'] + 1) if ultimo and 'numero' in ultimo else 1
        
        # Salvar orçamento
        orc_id = db.orcamentos.insert_one({
            'numero': numero,
            'cliente_cpf': data['cliente_cpf'],
            'cliente_nome': data['cliente_nome'],
            'cliente_email': data.get('cliente_email', ''),
            'cliente_telefone': data.get('cliente_telefone', ''),
            'servicos': data.get('servicos', []),
            'produtos': data.get('produtos', []),
            'subtotal': subtotal,
            'desconto_global': data.get('desconto_global', 0),
            'desconto_valor': desconto_valor,
            'total_com_desconto': total_com_desconto,
            'cashback_perc': data.get('cashback_perc', 0),
            'cashback_valor': cashback_valor,
            'total_final': total_com_desconto,
            'pagamento': data.get('pagamento', {}),
            'status': data.get('status', 'Pendente'),
            'created_at': datetime.now(),
            'user_id': session['user_id']
        }).inserted_id
        
        logger.info(f"✅ Budget #{numero} created")
        
        # Atualizar estoque
        for produto in data.get('produtos', []):
            if 'id' in produto:
                prod = db.produtos.find_one({'_id': ObjectId(produto['id'])})
                if prod:
                    novo_estoque = prod.get('estoque', 0) - produto.get('qtd', 1)
                    db.produtos.update_one({'_id': ObjectId(produto['id'])}, {'$set': {'estoque': novo_estoque}})
                    
                    db.estoque_movimentacoes.insert_one({
                        'produto_id': ObjectId(produto['id']),
                        'tipo': 'saida',
                        'quantidade': produto.get('qtd', 1),
                        'motivo': f"Orçamento #{numero}",
                        'usuario': session.get('username'),
                        'data': datetime.now()
                    })
        
        # Se aprovado, enviar email/SMS
        if data.get('status') == 'Aprovado' and data.get('cliente_email'):
            send_email(
                data['cliente_email'],
                data['cliente_nome'],
                f"Contrato BIOMA #{numero}",
                f"<h2>Olá {data['cliente_nome']},</h2><p>Seu contrato foi aprovado!</p><p><strong>Total: R$ {total_com_desconto:.2f}</strong></p>"
            )
        
        if data.get('status') == 'Aprovado' and data.get('cliente_telefone'):
            send_sms(
                data['cliente_telefone'],
                f"BIOMA: Contrato #{numero} aprovado! Total: R$ {total_com_desconto:.2f}"
            )
        
        return jsonify({'success': True, 'numero': numero, 'id': str(orc_id)})
        
    except Exception as e:
        logger.error(f"❌ Error creating budget: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/orcamentos/<id>', methods=['DELETE'])
@login_required
def delete_orcamento(id):
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        result = db.orcamentos.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            return jsonify({'success': True})
        return jsonify({'success': False})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== CONTRATOS =====
@app.route('/api/contratos')
@login_required
def contratos():
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        contratos_list = list(db.orcamentos.find({'status': 'Aprovado'}).sort('created_at', DESCENDING))
        result = convert_objectid(contratos_list)
        return jsonify({'success': True, 'contratos': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== FILA =====
@app.route('/api/fila', methods=['GET', 'POST'])
@login_required
def fila():
    if db is None:
        return jsonify({'success': False}), 500
    
    if request.method == 'GET':
        try:
            fila_list = list(db.fila_atendimento.find({'status': {'$in': ['aguardando', 'atendendo']}}).sort('created_at', ASCENDING))
            result = convert_objectid(fila_list)
            return jsonify({'success': True, 'fila': result})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # POST
    data = request.json
    try:
        total = db.fila_atendimento.count_documents({'status': {'$in': ['aguardando', 'atendendo']}})
        
        db.fila_atendimento.insert_one({
            'cliente_nome': data['cliente_nome'],
            'cliente_telefone': data['cliente_telefone'],
            'servico': data.get('servico', ''),
            'profissional': data.get('profissional', ''),
            'posicao': total + 1,
            'status': 'aguardando',
            'created_at': datetime.now()
        })
        
        if data.get('cliente_telefone'):
            send_sms(data['cliente_telefone'], f"BIOMA: Você está na posição {total + 1} da fila!")
        
        return jsonify({'success': True, 'posicao': total + 1})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/fila/<id>', methods=['DELETE'])
@login_required
def delete_fila(id):
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        result = db.fila_atendimento.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            return jsonify({'success': True})
        return jsonify({'success': False})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== IMPORTAÇÃO CSV =====
@app.route('/api/importar', methods=['POST'])
@login_required
def importar():
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'})
    
    file = request.files['file']
    tipo = request.form.get('tipo', 'produtos')
    
    if not file.filename:
        return jsonify({'success': False, 'message': 'Arquivo inválido'})
    
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if ext not in ['csv', 'xlsx', 'xls']:
        return jsonify({'success': False, 'message': 'Apenas CSV ou XLSX'})
    
    logger.info(f"📤 Importing {ext.upper()} - Type: {tipo}")
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join('/tmp', filename)
        file.save(filepath)
        
        count_success = 0
        count_error = 0
        rows = []
        
        # Ler arquivo
        if ext == 'csv':
            encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as csvfile:
                        reader = csv.DictReader(csvfile)
                        rows = list(reader)
                        logger.info(f"✅ CSV read with {encoding} - {len(rows)} rows")
                        break
                except UnicodeDecodeError:
                    continue
        else:
            from openpyxl import load_workbook
            wb = load_workbook(filepath, read_only=True, data_only=True)
            ws = wb.active
            headers = [str(c.value).strip().lower() if c.value else '' for c in next(ws.iter_rows(min_row=1, max_row=1))]
            
            for row in ws.iter_rows(min_row=2, values_only=True):
                row_dict = {}
                for i in range(len(headers)):
                    if i < len(row) and row[i] is not None:
                        val = row[i]
                        if isinstance(val, str):
                            val = val.strip()
                        row_dict[headers[i]] = val
                if row_dict:
                    rows.append(row_dict)
            wb.close()
        
        # Processar produtos
        if tipo == 'produtos':
            for idx, row in enumerate(rows, 1):
                try:
                    r = {k.lower().strip(): v for k, v in row.items() if k and v is not None}
                    
                    if not r or all(not v for v in r.values()):
                        continue
                    
                    nome = None
                    for col in ['nome', 'produto', 'name']:
                        if col in r and r[col] and str(r[col]).strip():
                            nome = str(r[col]).strip()
                            break
                    
                    if not nome or len(nome) < 2:
                        count_error += 1
                        continue
                    
                    marca = ''
                    for col in ['marca', 'brand']:
                        if col in r and r[col]:
                            marca = str(r[col]).strip()
                            break
                    
                    sku = f"PROD-{count_success+1}"
                    for col in ['sku', 'codigo', 'code']:
                        if col in r and r[col]:
                            sku = str(r[col]).strip()
                            break
                    
                    preco = 0.0
                    for col in ['preco', 'preço', 'price', 'valor']:
                        if col in r and r[col]:
                            try:
                                val = str(r[col]).replace('R$', '').replace('r$', '').strip()
                                if ',' in val and '.' in val:
                                    val = val.replace('.', '').replace(',', '.')
                                elif ',' in val:
                                    val = val.replace(',', '.')
                                val = ''.join(c for c in val if c.isdigit() or c == '.')
                                if val:
                                    preco = float(val)
                                    break
                            except:
                                continue
                    
                    if preco <= 0:
                        count_error += 1
                        continue
                    
                    custo = 0.0
                    for col in ['custo', 'cost']:
                        if col in r and r[col]:
                            try:
                                val = str(r[col]).replace('R$', '').strip()
                                if ',' in val:
                                    val = val.replace(',', '.')
                                custo = float(val)
                                break
                            except:
                                continue
                    
                    estoque = 0
                    for col in ['estoque', 'quantidade', 'qtd']:
                        if col in r and r[col]:
                            try:
                                estoque = int(float(r[col]))
                                break
                            except:
                                continue
                    
                    categoria = 'Produto'
                    for col in ['categoria', 'category']:
                        if col in r and r[col]:
                            categoria = str(r[col]).strip().title()
                            break
                    
                    db.produtos.insert_one({
                        'nome': nome,
                        'marca': marca,
                        'sku': sku,
                        'preco': preco,
                        'custo': custo,
                        'estoque': estoque,
                        'estoque_minimo': 5,
                        'categoria': categoria,
                        'ativo': True,
                        'created_at': datetime.now()
                    })
                    count_success += 1
                    
                except Exception as e:
                    logger.error(f"❌ Row {idx} error: {e}")
                    count_error += 1
        
        # Processar serviços
        elif tipo == 'servicos':
            for idx, row in enumerate(rows, 1):
                try:
                    r = {k.lower().strip(): v for k, v in row.items() if k and v is not None}
                    
                    if not r:
                        continue
                    
                    nome = None
                    for col in ['nome', 'servico', 'service']:
                        if col in r and r[col]:
                            nome = str(r[col]).strip()
                            break
                    
                    if not nome:
                        count_error += 1
                        continue
                    
                    categoria = 'Serviço'
                    for col in ['categoria', 'category']:
                        if col in r and r[col]:
                            categoria = str(r[col]).strip().title()
                            break
                    
                    tamanhos_criados = 0
                    tamanhos_map = {
                        'kids': 'Kids',
                        'masculino': 'Masculino',
                        'curto': 'Curto',
                        'medio': 'Médio',
                        'longo': 'Longo',
                        'extra_longo': 'Extra Longo'
                    }
                    
                    for key, tam_nome in tamanhos_map.items():
                        if key in r and r[key]:
                            try:
                                val = str(r[key]).replace('R$', '').strip()
                                if ',' in val:
                                    val = val.replace(',', '.')
                                preco = float(val)
                                
                                if preco > 0:
                                    db.servicos.insert_one({
                                        'nome': nome,
                                        'sku': f"{nome.upper().replace(' ', '-')}-{tam_nome.upper().replace(' ', '-')}",
                                        'tamanho': tam_nome,
                                        'preco': preco,
                                        'categoria': categoria,
                                        'duracao': 60,
                                        'ativo': True,
                                        'created_at': datetime.now()
                                    })
                                    tamanhos_criados += 1
                            except:
                                continue
                    
                    if tamanhos_criados > 0:
                        count_success += 1
                    else:
                        count_error += 1
                    
                except Exception as e:
                    logger.error(f"❌ Row {idx} error: {e}")
                    count_error += 1
        
        os.remove(filepath)
        
        logger.info(f"🎉 Import complete: {count_success} success, {count_error} errors")
        
        return jsonify({
            'success': True,
            'message': f'{count_success} registros importados com sucesso!',
            'count_success': count_success,
            'count_error': count_error
        })
        
    except Exception as e:
        logger.error(f"❌ Import error: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@app.route('/api/template/download/<tipo>')
@login_required
def download_template(tipo):
    output = io.StringIO()
    writer = csv.writer(output)
    
    if tipo == 'produtos':
        writer.writerow(['nome', 'marca', 'sku', 'preco', 'custo', 'estoque', 'categoria'])
        writer.writerow(['Shampoo 500ml', 'Loreal', 'SHAMP-500', '49,90', '20,00', '50', 'SHAMPOO'])
    else:
        writer.writerow(['nome', 'categoria', 'kids', 'masculino', 'curto', 'medio', 'longo', 'extra_longo'])
        writer.writerow(['Hidratação', 'Tratamento', '50', '60', '80', '100', '120', '150'])
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'template_{tipo}.csv'
    )

# ===== CONFIGURAÇÕES =====
@app.route('/api/config', methods=['GET', 'POST'])
@login_required
def config():
    if db is None:
        return jsonify({'success': False}), 500
    
    if request.method == 'GET':
        try:
            cfg = db.config.find_one({'key': 'unidade'}) or {}
            result = convert_objectid(cfg)
            return jsonify({'success': True, 'config': result})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # POST
    data = request.json
    try:
        db.config.update_one({'key': 'unidade'}, {'$set': data}, upsert=True)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== INICIALIZAÇÃO =====
def init_db():
    if db is None:
        logger.warning("⚠️ Database not available")
        return
    
    logger.info("🔧 Initializing database...")
    
    # Admin user
    if db.users.count_documents({}) == 0:
        db.users.insert_one({
            'name': 'Administrador',
            'username': 'admin',
            'email': 'admin@bioma.com',
            'password': generate_password_hash('admin123'),
            'role': 'admin',
            'theme': 'light',
            'verified': True,
            'created_at': datetime.now()
        })
        logger.info("✅ Admin created: admin/admin123")
    
    # Sample services
    if db.servicos.count_documents({}) == 0:
        services = [
            ('Hidratação', 'Tratamento', 50, 60, 80, 100, 120, 150),
            ('Corte Feminino', 'Cabelo', 40, 50, 60, 80, 100, 120),
            ('Corte Masculino', 'Cabelo', 30, 40, 50, 60, 70, 80)
        ]
        
        for nome, cat, kids, masc, curto, medio, longo, xl in services:
            for tam, preco in [('Kids', kids), ('Masculino', masc), ('Curto', curto), ('Médio', medio), ('Longo', longo), ('Extra Longo', xl)]:
                db.servicos.insert_one({
                    'nome': nome,
                    'sku': f"{nome.upper().replace(' ', '-')}-{tam.upper().replace(' ', '-')}",
                    'tamanho': tam,
                    'preco': preco,
                    'categoria': cat,
                    'duracao': 60,
                    'ativo': True,
                    'created_at': datetime.now()
                })
        logger.info("✅ Services created (18 SKUs)")
    
    logger.info("🎉 Database initialized!")

# ===== RUN =====
if __name__ == '__main__':
    print("\n" + "="*80)
    print("🌳 BIOMA UBERABA v3.1 - ULTRA PROFISSIONAL")
    print("="*80)
    
    init_db()
    
    is_prod = os.getenv('FLASK_ENV') == 'production'
    url = 'https://bioma-system2.onrender.com' if is_prod else 'http://localhost:5000'
    
    print(f"🚀 URL: {url}")
    print(f"🔒 HTTPS: {'✅ ATIVO' if is_prod else '⚠️  Local'}")
    print(f"👤 Login: admin / admin123")
    print(f"💾 MongoDB: {'✅ CONECTADO' if db else '❌ OFFLINE'}")
    print("="*80)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"👨‍💻 Dev: @juanmarco1999")
    print("="*80 + "\n")
    
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"🚀 Starting Flask on port {port}")
    
    app.run(
        debug=False,
        host='0.0.0.0',
        port=port,
        threaded=True
    )
    
    