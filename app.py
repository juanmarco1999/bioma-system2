#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA UBERABA v3.4 FINAL - Sistema Ultra Profissional COMPLETO
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

# ReportLab para PDF
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle

# OpenPyXL para Excel
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

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
app.secret_key = os.getenv('SECRET_KEY', 'bioma-2025-v3-4-ultra-secure-key-final')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = '/tmp'

CORS(app, supports_credentials=True)

# ===== MONGODB CONNECTION =====
def get_db():
    """Conecta ao MongoDB"""
    try:
        username = urllib.parse.quote_plus(os.getenv('MONGO_USERNAME', ''))
        password = urllib.parse.quote_plus(os.getenv('MONGO_PASSWORD', ''))
        cluster = os.getenv('MONGO_CLUSTER', '')
        
        if not all([username, password, cluster]):
            logger.error("❌ MongoDB credentials missing")
            return None
        
        uri = f"mongodb+srv://{username}:{password}@{cluster}/bioma_db?retryWrites=true&w=majority&appName=Juan-Analytics-DBServer"
        
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        
        db_instance = client.bioma_db
        logger.info("✅ MongoDB Connected")
        return db_instance
        
    except Exception as e:
        logger.error(f"❌ MongoDB Failed: {e}")
        return None

db = get_db()

# ===== HELPERS =====
def convert_objectid(obj):
    """Convert ObjectId to string"""
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
    """Decorator autenticação"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning(f"🚫 Unauthorized: {request.endpoint}")
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

# ===== EMAIL =====
def send_email(to, name, subject, html_content, pdf=None):
    """Envia email via MailerSend"""
    api_key = os.getenv('MAILERSEND_API_KEY')
    from_email = os.getenv('MAILERSEND_FROM_EMAIL')
    from_name = os.getenv('MAILERSEND_FROM_NAME', 'BIOMA Uberaba')
    
    if not api_key or not from_email:
        logger.warning("⚠️ MailerSend não configurado")
        return {'success': False, 'message': 'Email não configurado'}
    
    data = {
        "from": {
            "email": from_email,
            "name": from_name
        },
        "to": [{"email": to, "name": name}],
        "subject": subject,
        "html": html_content
    }
    
    if pdf:
        import base64
        data['attachments'] = [{
            "filename": pdf['filename'], 
            "content": base64.b64encode(pdf['content']).decode(),
            "disposition": "attachment"
        }]
    
    try:
        logger.info(f"📧 Enviando para: {to}")
        r = requests.post(
            "https://api.mailersend.com/v1/email",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json=data,
            timeout=10
        )
        
        if r.status_code == 202:
            logger.info(f"✅ Email enviado: {to}")
            return {'success': True}
        else:
            logger.error(f"❌ Email falhou: {r.status_code}")
            return {'success': False}
    except Exception as e:
        logger.error(f"❌ Email exception: {e}")
        return {'success': False}

# ===== ROUTES =====
@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check"""
    db_status = 'connected' if db is not None else 'disconnected'
    
    if db is not None:
        try:
            db.command('ping')
        except:
            db_status = 'error'
    
    return jsonify({
        'status': 'healthy',
        'time': datetime.now().isoformat(),
        'database': db_status,
        'version': '3.4.0'
    }), 200

# ===== AUTH =====
@app.route('/api/login', methods=['POST'])
def login():
    """Login"""
    data = request.json
    logger.info(f"🔐 Login: {data.get('username')}")
    
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    user = db.users.find_one({
        '$or': [
            {'username': data['username']},
            {'email': data['username']}
        ]
    })
    
    if user and check_password_hash(user['password'], data['password']):
        
        if not user.get('verified', True):
            logger.warning(f"⚠️ Unverified: {data.get('username')}")
            return jsonify({
                'success': False,
                'message': 'Conta não verificada',
                'verification_required': True,
                'username': user['username']
            })
        
        session.permanent = True
        session['user_id'] = str(user['_id'])
        session['username'] = user['username']
        
        logger.info(f"✅ Login OK: {user['username']}")
        
        return jsonify({
            'success': True,
            'user': {
                'id': str(user['_id']),
                'name': user['name'],
                'username': user['username'],
                'email': user['email'],
                'theme': user.get('theme', 'light')
            }
        })
    
    logger.warning(f"❌ Login failed: {data.get('username')}")
    return jsonify({'success': False, 'message': 'Usuário ou senha inválidos'})

@app.route('/api/register', methods=['POST'])
def register():
    """Registro com verificação"""
    data = request.json
    logger.info(f"👤 Register: {data.get('username')}")
    
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    if db.users.find_one({'$or': [
        {'username': data['username']},
        {'email': data['email']}
    ]}):
        return jsonify({'success': False, 'message': 'Usuário ou email já existe'})
    
    verification_code = str(random.randint(100000, 999999))
    
    user_data = {
        'name': data['name'],
        'username': data['username'],
        'email': data['email'],
        'telefone': data.get('telefone', ''),
        'password': generate_password_hash(data['password']),
        'role': 'user',
        'theme': 'light',
        'verified': False,
        'verification_code': verification_code,
        'verification_code_expires': datetime.now() + timedelta(hours=24),
        'created_at': datetime.now()
    }
    
    try:
        db.users.insert_one(user_data)
        logger.info(f"✅ User created: {data['username']}")
        
        send_email(
            data['email'],
            data['name'],
            '🔐 Código de Verificação BIOMA',
            f"""
            <div style="font-family: Arial; max-width: 600px; margin: 0 auto; padding: 40px; background: #f9fafb;">
                <div style="background: white; padding: 40px; border-radius: 15px;">
                    <h1 style="color: #7C3AED; text-align: center;">🌳 BIOMA UBERABA</h1>
                    <h2 style="color: #1F2937;">Bem-vindo, {data['name']}!</h2>
                    <p>Seu código de verificação é:</p>
                    <div style="background: linear-gradient(135deg, #7C3AED, #EC4899); color: white; font-size: 3rem; font-weight: 900; padding: 30px; border-radius: 15px; text-align: center; letter-spacing: 10px;">
                        {verification_code}
                    </div>
                    <p style="color: #9CA3AF; margin-top: 20px;">Este código expira em 24 horas.</p>
                </div>
            </div>
            """
        )
        
        return jsonify({
            'success': True,
            'message': 'Conta criada! Verifique seu email.',
            'verification_required': True
        })
        
    except Exception as e:
        logger.error(f"❌ Register error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/verify', methods=['POST'])
def verify():
    """Verifica código"""
    data = request.json
    username = data.get('username')
    code = data.get('code')
    
    if db is None:
        return jsonify({'success': False}), 500
    
    user = db.users.find_one({'username': username})
    
    if not user:
        return jsonify({'success': False, 'message': 'Usuário não encontrado'})
    
    if user.get('verified'):
        return jsonify({'success': False, 'message': 'Já verificado'})
    
    if 'verification_code_expires' in user:
        if datetime.now() > user['verification_code_expires']:
            return jsonify({'success': False, 'message': 'Código expirado'})
    
    if user.get('verification_code') == code:
        db.users.update_one(
            {'username': username},
            {
                '$set': {'verified': True},
                '$unset': {'verification_code': '', 'verification_code_expires': ''}
            }
        )
        logger.info(f"✅ Verified: {username}")
        return jsonify({'success': True, 'message': 'Conta ativada!'})
    
    return jsonify({'success': False, 'message': 'Código inválido'})

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout"""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/current-user')
def current_user():
    """Usuário logado"""
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
                        'email': user['email'],
                        'theme': user.get('theme', 'light')
                    }
                })
        except:
            pass
    
    return jsonify({'success': False})

@app.route('/api/update-theme', methods=['POST'])
@login_required
def update_theme():
    """Atualiza tema"""
    if db is None:
        return jsonify({'success': False}), 500
    
    theme = request.json['theme']
    db.users.update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$set': {'theme': theme}}
    )
    return jsonify({'success': True})

# ===== SYSTEM =====
@app.route('/api/system/status')
@login_required
def system_status():
    """Status"""
    mongo_ok = False
    mongo_msg = 'Desconectado'
    
    try:
        if db is not None:
            db.command('ping')
            mongo_ok = True
            mongo_msg = 'Conectado'
    except Exception as e:
        mongo_msg = f'Erro: {str(e)[:100]}'
    
    mailersend_ok = bool(os.getenv('MAILERSEND_API_KEY'))
    
    return jsonify({
        'success': True,
        'status': {
            'mongodb': {
                'operational': mongo_ok,
                'message': mongo_msg,
                'last_check': datetime.now().isoformat()
            },
            'mailersend': {
                'operational': mailersend_ok,
                'message': 'Configurado' if mailersend_ok else 'Não configurado'
            },
            'server': {
                'time': datetime.now().isoformat(),
                'version': '3.4.0'
            }
        }
    })

# ===== DASHBOARD =====
@app.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    """Stats"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        hoje_inicio = datetime.now().replace(hour=0, minute=0, second=0)
        hoje_fim = datetime.now().replace(hour=23, minute=59, second=59)
        
        agendamentos_hoje = 0
        if 'agendamentos' in db.list_collection_names():
            agendamentos_hoje = db.agendamentos.count_documents({
                'data': {'$gte': hoje_inicio, '$lte': hoje_fim}
            })
        
        stats = {
            'total_orcamentos': db.orcamentos.count_documents({}),
            'total_clientes': db.clientes.count_documents({}),
            'total_servicos': db.servicos.count_documents({}),
            'faturamento': sum(
                o.get('total_final', 0) 
                for o in db.orcamentos.find({'status': 'Aprovado'})
            ),
            'agendamentos_hoje': agendamentos_hoje
        }
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== CLIENTES =====
@app.route('/api/clientes', methods=['GET', 'POST'])
@login_required
def clientes():
    """CRUD clientes"""
    if db is None:
        return jsonify({'success': False}), 500
    
    if request.method == 'GET':
        try:
            clientes_list = list(db.clientes.find({}).sort('nome', ASCENDING))
            
            for cliente in clientes_list:
                cliente_cpf = cliente.get('cpf')
                
                cliente['total_gasto'] = sum(
                    o.get('total_final', 0)
                    for o in db.orcamentos.find({
                        'cliente_cpf': cliente_cpf,
                        'status': 'Aprovado'
                    })
                )
                
                ultimo_orc = db.orcamentos.find_one(
                    {'cliente_cpf': cliente_cpf},
                    sort=[('created_at', DESCENDING)]
                )
                cliente['ultima_visita'] = ultimo_orc['created_at'] if ultimo_orc else None
                cliente['total_visitas'] = db.orcamentos.count_documents({'cliente_cpf': cliente_cpf})
            
            result = convert_objectid(clientes_list)
            return jsonify({'success': True, 'clientes': result})
            
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # POST
    data = request.json
    try:
        existing = db.clientes.find_one({'cpf': data['cpf']})
        
        cliente_data = {
            'nome': data['nome'],
            'cpf': data['cpf'],
            'email': data.get('email', ''),
            'telefone': data.get('telefone', ''),
            'updated_at': datetime.now()
        }
        
        if existing:
            db.clientes.update_one({'cpf': data['cpf']}, {'$set': cliente_data})
        else:
            cliente_data['created_at'] = datetime.now()
            db.clientes.insert_one(cliente_data)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clientes/<id>', methods=['DELETE'])
@login_required
def delete_cliente(id):
    """Deleta cliente"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        result = db.clientes.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            return jsonify({'success': True})
        return jsonify({'success': False})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clientes/buscar')
@login_required
def buscar_clientes():
    """Busca clientes"""
    if db is None:
        return jsonify({'success': False}), 500
    
    termo = request.args.get('termo', '')
    try:
        regex = {'$regex': termo, '$options': 'i'}
        clientes = list(db.clientes.find({
            '$or': [{'nome': regex}, {'cpf': regex}]
        }).limit(10))
        
        return jsonify({'success': True, 'clientes': convert_objectid(clientes)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== PROFISSIONAIS =====
@app.route('/api/profissionais', methods=['GET', 'POST'])
@login_required
def profissionais():
    """CRUD profissionais"""
    if db is None:
        return jsonify({'success': False}), 500
    
    if request.method == 'GET':
        try:
            profs = list(db.profissionais.find({}).sort('nome', ASCENDING))
            return jsonify({'success': True, 'profissionais': convert_objectid(profs)})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # POST
    data = request.json
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
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profissionais/<id>', methods=['DELETE'])
@login_required
def delete_profissional(id):
    """Deleta profissional"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        result = db.profissionais.delete_one({'_id': ObjectId(id)})
        return jsonify({'success': result.deleted_count > 0})
    except Exception as e:
        return jsonify({'success': False}), 500

# ===== SERVIÇOS =====
@app.route('/api/servicos', methods=['GET', 'POST'])
@login_required
def servicos():
    """CRUD serviços"""
    if db is None:
        return jsonify({'success': False}), 500
    
    if request.method == 'GET':
        try:
            servs = list(db.servicos.find({}).sort('nome', ASCENDING))
            return jsonify({'success': True, 'servicos': convert_objectid(servs)})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # POST
    data = request.json
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
            preco_float = float(preco) if preco else 0
            if preco_float > 0:
                db.servicos.insert_one({
                    'nome': data['nome'],
                    'sku': f"{data['nome'].upper().replace(' ', '-')}-{tam.upper().replace(' ', '-')}",
                    'tamanho': tam,
                    'preco': preco_float,
                    'categoria': data.get('categoria', 'Serviço'),
                    'duracao': int(data.get('duracao', 60)),
                    'ativo': True,
                    'created_at': datetime.now()
                })
                count += 1
        
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/servicos/<id>', methods=['DELETE'])
@login_required
def delete_servico(id):
    """Deleta serviço"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        result = db.servicos.delete_one({'_id': ObjectId(id)})
        return jsonify({'success': result.deleted_count > 0})
    except Exception as e:
        return jsonify({'success': False}), 500

@app.route('/api/servicos/buscar')
@login_required
def buscar_servicos():
    """Busca serviços"""
    if db is None:
        return jsonify({'success': False}), 500
    
    termo = request.args.get('termo', '')
    try:
        servicos = list(db.servicos.find({'nome': {'$regex': termo, '$options': 'i'}}).limit(20))
        return jsonify({'success': True, 'servicos': convert_objectid(servicos)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== PRODUTOS =====
@app.route('/api/produtos', methods=['GET', 'POST'])
@login_required
def produtos():
    """CRUD produtos"""
    if db is None:
        return jsonify({'success': False}), 500
    
    if request.method == 'GET':
        try:
            prods = list(db.produtos.find({}).sort('nome', ASCENDING))
            return jsonify({'success': True, 'produtos': convert_objectid(prods)})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # POST
    data = request.json
    try:
        produto_id = db.produtos.insert_one({
            'nome': data['nome'],
            'marca': data.get('marca', ''),
            'sku': data.get('sku', f"PROD-{datetime.now().timestamp()}"),
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
                'usuario': session.get('username', 'system'),
                'data': datetime.now()
            })
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/produtos/<id>', methods=['DELETE'])
@login_required
def delete_produto(id):
    """Deleta produto"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        result = db.produtos.delete_one({'_id': ObjectId(id)})
        return jsonify({'success': result.deleted_count > 0})
    except Exception as e:
        return jsonify({'success': False}), 500

@app.route('/api/produtos/buscar')
@login_required
def buscar_produtos():
    """Busca produtos"""
    if db is None:
        return jsonify({'success': False}), 500
    
    termo = request.args.get('termo', '')
    try:
        produtos = list(db.produtos.find({'nome': {'$regex': termo, '$options': 'i'}}).limit(20))
        return jsonify({'success': True, 'produtos': convert_objectid(produtos)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== ORÇAMENTOS =====
@app.route('/api/orcamentos', methods=['GET', 'POST'])
@login_required
def orcamentos():
    """CRUD orçamentos"""
    if db is None:
        return jsonify({'success': False}), 500
    
    if request.method == 'GET':
        try:
            orcs = list(db.orcamentos.find({}).sort('created_at', DESCENDING))
            return jsonify({'success': True, 'orcamentos': convert_objectid(orcs)})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # POST
    data = request.json
    try:
        # Salvar cliente
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
        subtotal = sum(s['total'] for s in data.get('servicos', [])) + \
                   sum(p['total'] for p in data.get('produtos', []))
        
        desconto_global = float(data.get('desconto_global', 0))
        desconto_valor = subtotal * (desconto_global / 100)
        total_com_desconto = subtotal - desconto_valor
        
        cashback_perc = float(data.get('cashback_perc', 0))
        cashback_valor = total_com_desconto * (cashback_perc / 100)
        
        # Número sequencial
        ultimo = db.orcamentos.find_one(sort=[('numero', DESCENDING)])
        numero = (ultimo['numero'] + 1) if ultimo and 'numero' in ultimo else 1
        
        # Salvar
        orc_id = db.orcamentos.insert_one({
            'numero': numero,
            'cliente_cpf': data['cliente_cpf'],
            'cliente_nome': data['cliente_nome'],
            'cliente_email': data.get('cliente_email', ''),
            'cliente_telefone': data.get('cliente_telefone', ''),
            'servicos': data.get('servicos', []),
            'produtos': data.get('produtos', []),
            'subtotal': subtotal,
            'desconto_global': desconto_global,
            'desconto_valor': desconto_valor,
            'total_com_desconto': total_com_desconto,
            'cashback_perc': cashback_perc,
            'cashback_valor': cashback_valor,
            'total_final': total_com_desconto,
            'pagamento': data.get('pagamento', {}),
            'status': data.get('status', 'Pendente'),
            'created_at': datetime.now(),
            'user_id': session['user_id']
        }).inserted_id
        
        # Atualizar estoque
        for produto in data.get('produtos', []):
            if 'id' in produto:
                prod = db.produtos.find_one({'_id': ObjectId(produto['id'])})
                if prod:
                    novo_estoque = prod.get('estoque', 0) - produto.get('qtd', 1)
                    db.produtos.update_one(
                        {'_id': ObjectId(produto['id'])},
                        {'$set': {'estoque': novo_estoque}}
                    )
                    
                    db.estoque_movimentacoes.insert_one({
                        'produto_id': ObjectId(produto['id']),
                        'tipo': 'saida',
                        'quantidade': produto.get('qtd', 1),
                        'motivo': f"Orçamento #{numero}",
                        'usuario': session.get('username'),
                        'data': datetime.now()
                    })
        
        # Email se aprovado
        if data.get('status') == 'Aprovado' and data.get('cliente_email'):
            send_email(
                data['cliente_email'],
                data['cliente_nome'],
                f'✅ Contrato BIOMA #{numero}',
                f"""
                <div style="font-family: Arial; padding: 40px; background: #f9fafb;">
                    <div style="background: white; padding: 40px; border-radius: 15px;">
                        <h1 style="color: #10B981;">✅ Contrato Aprovado!</h1>
                        <h2>Olá {data['cliente_nome']},</h2>
                        <p>Contrato <strong>#{numero}</strong> aprovado!</p>
                        <h3 style="color: #7C3AED;">Total: R$ {total_com_desconto:.2f}</h3>
                        <p>Cashback: R$ {cashback_valor:.2f}</p>
                        <p>Pagamento: {data.get('pagamento', {}).get('tipo', 'N/A')}</p>
                        <p style="margin-top: 30px;">Obrigado!</p>
                        <p><strong>BIOMA Uberaba</strong></p>
                    </div>
                </div>
                """
            )
        
        return jsonify({'success': True, 'numero': numero, 'id': str(orc_id)})
        
    except Exception as e:
        logger.error(f"❌ Orçamento error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/orcamentos/<id>', methods=['DELETE'])
@login_required
def delete_orcamento(id):
    """Deleta orçamento"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        result = db.orcamentos.delete_one({'_id': ObjectId(id)})
        return jsonify({'success': result.deleted_count > 0})
    except Exception as e:
        return jsonify({'success': False}), 500

# ===== PDF CONTRATO - MODELO EXATO =====
@app.route('/api/orcamento/<id>/pdf')
@login_required
def gerar_pdf_orcamento(id):
    """PDF conforme modelo"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        orcamento = db.orcamentos.find_one({'_id': ObjectId(id)})
        if not orcamento:
            return jsonify({'success': False}), 404
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # HEADER ROXO
        p.setFillColor(HexColor('#7C3AED'))
        p.setFont("Helvetica-Bold", 28)
        p.drawString(50, height - 60, "BIOMA UBERABA")
        
        p.setFillColor(black)
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 80, "Av. Santos Dumont 3110 - Santa Maria - Uberaba/MG")
        p.drawString(50, height - 95, "Tel: (34) 99235-5890 | Email: biomauberaba@gmail.com")
        
        # LINHA ROXA
        p.setStrokeColor(HexColor('#7C3AED'))
        p.setLineWidth(2)
        p.line(50, height - 110, width - 50, height - 110)
        
        # TÍTULO
        p.setFillColor(HexColor('#7C3AED'))
        p.setFont("Helvetica-Bold", 20)
        p.drawString(50, height - 145, f"CONTRATO #{orcamento.get('numero', 'N/A')}")
        
        p.setStrokeColor(HexColor('#7C3AED'))
        p.line(50, height - 155, width - 50, height - 155)
        
        # DADOS CLIENTE
        y = height - 190
        p.setFillColor(black)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "DADOS DO CLIENTE")
        y -= 25
        
        p.setFont("Helvetica", 11)
        p.drawString(50, y, f"Nome: {orcamento.get('cliente_nome', 'N/A')}")
        y -= 18
        p.drawString(50, y, f"CPF: {orcamento.get('cliente_cpf', 'N/A')}")
        y -= 18
        p.drawString(50, y, f"Email: {orcamento.get('cliente_email', 'N/A')}")
        y -= 18
        p.drawString(50, y, f"Telefone: {orcamento.get('cliente_telefone', 'N/A')}")
        y -= 30
        
        # SERVIÇOS
        if orcamento.get('servicos'):
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, y, "SERVIÇOS")
            y -= 25
            
            data_servicos = [['Serviço', 'Tamanho', 'Qtd', 'Valor Unit.', 'Total']]
            for s in orcamento.get('servicos', []):
                data_servicos.append([
                    s.get('nome', ''),
                    s.get('tamanho', ''),
                    str(s.get('qtd', 1)),
                    f"R$ {s.get('preco_unit', 0):.2f}",
                    f"R$ {s.get('total', 0):.2f}"
                ])
            
            table = Table(data_servicos, colWidths=[200, 80, 50, 80, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#7C3AED')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#E5E7EB'))
            ]))
            
            table.wrapOn(p, width, height)
            table.drawOn(p, 50, y - len(data_servicos) * 22)
            y -= len(data_servicos) * 22 + 30
        
        # PRODUTOS
        if orcamento.get('produtos') and y > 250:
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, y, "PRODUTOS")
            y -= 25
            
            data_produtos = [['Produto', 'Marca', 'Qtd', 'Valor Unit.', 'Total']]
            for prod in orcamento.get('produtos', []):
                data_produtos.append([
                    prod.get('nome', ''),
                    prod.get('marca', ''),
                    str(prod.get('qtd', 1)),
                    f"R$ {prod.get('preco_unit', 0):.2f}",
                    f"R$ {prod.get('total', 0):.2f}"
                ])
            
            table_prod = Table(data_produtos, colWidths=[200, 80, 50, 80, 80])
            table_prod.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#7C3AED')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#E5E7EB'))
            ]))
            
            table_prod.wrapOn(p, width, height)
            table_prod.drawOn(p, 50, y - len(data_produtos) * 22)
            y -= len(data_produtos) * 22 + 30
        
        # TOTAL
        if y < 180:
            p.showPage()
            y = height - 50
        
        p.setFont("Helvetica-Bold", 18)
        p.setFillColor(HexColor('#7C3AED'))
        p.drawString(width - 250, y, f"TOTAL: R$ {orcamento.get('total_final', 0):.2f}")
        y -= 25
        
        p.setFont("Helvetica", 11)
        p.setFillColor(black)
        p.drawString(50, y, f"Forma de pagamento: {orcamento.get('pagamento', {}).get('tipo', 'N/A')}")
        
        # RODAPÉ
        p.line(50, 80, width - 50, 80)
        p.setFont("Helvetica", 8)
        p.drawString(50, 65, f"Emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        p.drawString(50, 50, "BIOMA Uberaba - CNPJ: 49.470.937/0001-10")
        
        p.save()
        buffer.seek(0)
        
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'contrato_{orcamento.get("numero")}.pdf')
        
    except Exception as e:
        logger.error(f"❌ PDF error: {e}")
        return jsonify({'success': False}), 500

# ===== CONTRATOS =====
@app.route('/api/contratos')
@login_required
def contratos():
    """Contratos aprovados"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        contratos_list = list(db.orcamentos.find({'status': 'Aprovado'}).sort('created_at', DESCENDING))
        return jsonify({'success': True, 'contratos': convert_objectid(contratos_list)})
    except Exception as e:
        return jsonify({'success': False}), 500

# ===== AGENDAMENTOS =====
@app.route('/api/agendamentos', methods=['GET', 'POST'])
@login_required
def agendamentos():
    """CRUD agendamentos"""
    if db is None:
        return jsonify({'success': False}), 500
    
    if request.method == 'GET':
        try:
            agora = datetime.now()
            agends = list(db.agendamentos.find({
                'data': {'$gte': agora}
            }).sort('data', ASCENDING).limit(10))
            
            return jsonify({'success': True, 'agendamentos': convert_objectid(agends)})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # POST
    data = request.json
    try:
        data_agendamento = datetime.fromisoformat(data['data'].replace('Z', '+00:00'))
        
        agend_id = db.agendamentos.insert_one({
            'cliente_id': data.get('cliente_id'),
            'cliente_nome': data.get('cliente_nome'),
            'cliente_telefone': data.get('cliente_telefone'),
            'profissional_id': data.get('profissional_id'),
            'profissional_nome': data.get('profissional_nome'),
            'servico_id': data.get('servico_id'),
            'servico_nome': data.get('servico_nome'),
            'data': data_agendamento,
            'horario': data['horario'],
            'status': 'confirmado',
            'created_at': datetime.now()
        }).inserted_id
        
        logger.info(f"✅ Agendamento: {data.get('cliente_nome')} - {data['horario']}")
        return jsonify({'success': True, 'id': str(agend_id)})
    except Exception as e:
        logger.error(f"❌ Agendamento error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== FILA =====
@app.route('/api/fila', methods=['GET', 'POST'])
@login_required
def fila():
    """Fila de atendimento"""
    if db is None:
        return jsonify({'success': False}), 500
    
    if request.method == 'GET':
        try:
            fila_list = list(db.fila_atendimento.find({
                'status': {'$in': ['aguardando', 'atendendo']}
            }).sort('created_at', ASCENDING))
            return jsonify({'success': True, 'fila': convert_objectid(fila_list)})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # POST
    data = request.json
    try:
        total = db.fila_atendimento.count_documents({
            'status': {'$in': ['aguardando', 'atendendo']}
        })
        
        db.fila_atendimento.insert_one({
            'cliente_nome': data['cliente_nome'],
            'cliente_telefone': data['cliente_telefone'],
            'servico': data.get('servico', ''),
            'profissional': data.get('profissional', ''),
            'posicao': total + 1,
            'status': 'aguardando',
            'created_at': datetime.now()
        })
        
        return jsonify({'success': True, 'posicao': total + 1})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/fila/<id>', methods=['DELETE'])
@login_required
def delete_fila(id):
    """Remove da fila"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        result = db.fila_atendimento.delete_one({'_id': ObjectId(id)})
        return jsonify({'success': result.deleted_count > 0})
    except Exception as e:
        return jsonify({'success': False}), 500

# ===== ESTOQUE =====
@app.route('/api/estoque/alerta')
@login_required
def estoque_alerta():
    """Produtos com estoque baixo"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        produtos = list(db.produtos.find({
            '$expr': {'$lte': ['$estoque', '$estoque_minimo']}
        }))
        return jsonify({'success': True, 'produtos': convert_objectid(produtos)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/movimentacao', methods=['POST'])
@login_required
def estoque_movimentacao():
    """Registra movimentação"""
    if db is None:
        return jsonify({'success': False}), 500
    
    data = request.json
    try:
        produto = db.produtos.find_one({'_id': ObjectId(data['produto_id'])})
        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'})
        
        qtd = int(data['quantidade'])
        tipo = data['tipo']
        
        novo_estoque = produto.get('estoque', 0)
        if tipo == 'entrada':
            novo_estoque += qtd
        else:
            novo_estoque -= qtd
        
        db.produtos.update_one(
            {'_id': ObjectId(data['produto_id'])},
            {'$set': {'estoque': novo_estoque}}
        )
        
        db.estoque_movimentacoes.insert_one({
            'produto_id': ObjectId(data['produto_id']),
            'tipo': tipo,
            'quantidade': qtd,
            'motivo': data.get('motivo', ''),
            'usuario': session.get('username'),
            'data': datetime.now()
        })
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== IMPORTAÇÃO CSV/XLSX =====
@app.route('/api/importar', methods=['POST'])
@login_required
def importar():
    """Importa CSV/XLSX"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum arquivo'}), 400
    
    file = request.files['file']
    tipo = request.form.get('tipo', 'produtos')
    
    if not file.filename:
        return jsonify({'success': False, 'message': 'Arquivo inválido'}), 400
    
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if ext not in ['csv', 'xlsx', 'xls']:
        return jsonify({'success': False, 'message': 'Apenas CSV ou XLSX'}), 400
    
    logger.info(f"📤 Importing {ext.upper()} - Type: {tipo}")
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        count_success = 0
        count_error = 0
        erros_detalhados = []
        rows = []
        
        # Ler CSV
        if ext == 'csv':
            encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as csvfile:
                        reader = csv.DictReader(csvfile)
                        rows = list(reader)
                        logger.info(f"✅ CSV: {len(rows)} rows")
                        break
                except:
                    continue
        else:
            # Ler XLSX
            try:
                from openpyxl import load_workbook
                wb = load_workbook(filepath, read_only=True, data_only=True)
                ws = wb.active
                
                headers = [str(c.value).strip().lower() if c.value else '' 
                          for c in next(ws.iter_rows(min_row=1, max_row=1))]
                
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
                logger.info(f"✅ XLSX: {len(rows)} rows")
            except Exception as e:
                logger.error(f"❌ XLSX error: {e}")
                return jsonify({'success': False, 'message': f'Erro XLSX: {str(e)}'}), 500
        
        # Processar PRODUTOS
        if tipo == 'produtos':
            for idx, row in enumerate(rows, 1):
                try:
                    r = {k.lower().strip(): v for k, v in row.items() if k and v is not None}
                    
                    if not r or all(not v for v in r.values()):
                        continue
                    
                    # Nome
                    nome = None
                    for col in ['nome', 'produto', 'name']:
                        if col in r and r[col]:
                            nome = str(r[col]).strip()
                            break
                    
                    if not nome or len(nome) < 2:
                        erros_detalhados.append(f"Linha {idx}: Nome inválido")
                        count_error += 1
                        continue
                    
                    # Marca
                    marca = ''
                    for col in ['marca', 'brand']:
                        if col in r and r[col]:
                            marca = str(r[col]).strip()
                            break
                    
                    # SKU
                    sku = f"PROD-{count_success+1}"
                    for col in ['sku', 'codigo', 'code']:
                        if col in r and r[col]:
                            sku = str(r[col]).strip()
                            break
                    
                    # Preço
                    preco = 0.0
                    for col in ['preco', 'preço', 'price', 'valor']:
                        if col in r and r[col]:
                            try:
                                val = str(r[col]).replace('R$', '').strip()
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
                        erros_detalhados.append(f"Linha {idx}: Preço inválido")
                        count_error += 1
                        continue
                    
                    # Custo
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
                    
                    # Estoque
                    estoque = 0
                    for col in ['estoque', 'quantidade', 'qtd', 'stock']:
                        if col in r and r[col]:
                            try:
                                estoque = int(float(r[col]))
                                break
                            except:
                                continue
                    
                    # Categoria
                    categoria = 'Produto'
                    for col in ['categoria', 'category']:
                        if col in r and r[col]:
                            categoria = str(r[col]).strip().title()
                            break
                    
                    # Inserir
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
                    erros_detalhados.append(f"Linha {idx}: {str(e)}")
                    count_error += 1
        
        # Processar SERVIÇOS
        elif tipo == 'servicos':
            for idx, row in enumerate(rows, 1):
                try:
                    r = {k.lower().strip(): v for k, v in row.items() if k and v is not None}
                    
                    if not r:
                        continue
                    
                    # Nome
                    nome = None
                    for col in ['nome', 'servico', 'service']:
                        if col in r and r[col]:
                            nome = str(r[col]).strip()
                            break
                    
                    if not nome:
                        erros_detalhados.append(f"Linha {idx}: Nome vazio")
                        count_error += 1
                        continue
                    
                    # Categoria
                    categoria = 'Serviço'
                    for col in ['categoria', 'category']:
                        if col in r and r[col]:
                            categoria = str(r[col]).strip().title()
                            break
                    
                    # Tamanhos
                    tamanhos_criados = 0
                    tamanhos_map = {
                        'kids': 'Kids',
                        'infantil': 'Kids',
                        'masculino': 'Masculino',
                        'male': 'Masculino',
                        'curto': 'Curto',
                        'short': 'Curto',
                        'medio': 'Médio',
                        'médio': 'Médio',
                        'medium': 'Médio',
                        'longo': 'Longo',
                        'long': 'Longo',
                        'extra_longo': 'Extra Longo',
                        'xl': 'Extra Longo'
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
                        erros_detalhados.append(f"Linha {idx}: Sem preços")
                        count_error += 1
                    
                except Exception as e:
                    erros_detalhados.append(f"Linha {idx}: {str(e)}")
                    count_error += 1
        
        # Remover arquivo
        if os.path.exists(filepath):
            os.remove(filepath)
        
        logger.info(f"🎉 Import: {count_success} OK, {count_error} errors")
        
        return jsonify({
            'success': True,
            'message': f'{count_success} importados!',
            'count_success': count_success,
            'count_error': count_error,
            'erros_detalhados': erros_detalhados[:10]
        })
        
    except Exception as e:
        logger.error(f"❌ Import error: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== TEMPLATE XLSX =====
@app.route('/api/template/download/<tipo>')
@login_required
def download_template(tipo):
    """Template XLSX profissional"""
    wb = Workbook()
    ws = wb.active
    
    header_fill = PatternFill(start_color='7C3AED', end_color='7C3AED', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True, size=12)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    if tipo == 'produtos':
        ws.title = 'Produtos BIOMA'
        headers = ['nome', 'marca', 'sku', 'preco', 'custo', 'estoque', 'categoria']
        ws.append(headers)
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border
        
        ws.append(['Shampoo 500ml', 'Loreal', 'SHAMP-500', 49.90, 20.00, 50, 'SHAMPOO'])
        ws.append(['Condicionador 500ml', 'Loreal', 'COND-500', 49.90, 20.00, 50, 'CONDICIONADOR'])
        
        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            ws.column_dimensions[col].width = 18
        
    else:
        ws.title = 'Serviços BIOMA'
        headers = ['nome', 'categoria', 'kids', 'masculino', 'curto', 'medio', 'longo', 'extra_longo']
        ws.append(headers)
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border
        
        ws.append(['Hidratação', 'Tratamento', 50, 60, 80, 100, 120, 150])
        ws.append(['Corte', 'Cabelo', 40, 50, 60, 80, 100, 120])
        
        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            ws.column_dimensions[col].width = 15
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'template_{tipo}_bioma.xlsx'
    )

# ===== CONFIGURAÇÕES =====
@app.route('/api/config', methods=['GET', 'POST'])
@login_required
def config():
    """Configurações"""
    if db is None:
        return jsonify({'success': False}), 500
    
    if request.method == 'GET':
        try:
            cfg = db.config.find_one({'key': 'unidade'}) or {}
            return jsonify({'success': True, 'config': convert_objectid(cfg)})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # POST
    data = request.json
    try:
        db.config.update_one({'key': 'unidade'}, {'$set': data}, upsert=True)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== INIT DB =====
def init_db():
    """Inicializa banco"""
    if db is None:
        logger.warning("⚠️ DB não disponível")
        return
    
    logger.info("🔧 Initializing DB...")
    
    # Admin user
    if db.users.count_documents({}) == 0:
        db.users.insert_one({
            'name': 'Administrador',
            'username': 'admin',
            'email': 'admin@bioma.com',
            'telefone': '',
            'password': generate_password_hash('admin123'),
            'role': 'admin',
            'theme': 'light',
            'verified': True,
            'created_at': datetime.now()
        })
        logger.info("✅ Admin: admin/admin123")
    
    # Serviços padrão
    if db.servicos.count_documents({}) == 0:
        services = [
            ('Hidratação', 'Tratamento', [50, 60, 80, 100, 120, 150]),
            ('Corte', 'Cabelo', [40, 50, 60, 80, 100, 120])
        ]
        
        tamanhos = ['Kids', 'Masculino', 'Curto', 'Médio', 'Longo', 'Extra Longo']
        
        for nome, cat, precos in services:
            for tam, preco in zip(tamanhos, precos):
                db.servicos.insert_one({
                    'nome': nome,
                    'sku': f"{nome.upper()}-{tam.upper()}",
                    'tamanho': tam,
                    'preco': preco,
                    'categoria': cat,
                    'duracao': 60,
                    'ativo': True,
                    'created_at': datetime.now()
                })
        
        logger.info(f"✅ {len(services) * 6} service SKUs")
    
    # Índices
    try:
        db.users.create_index([('username', ASCENDING)], unique=True)
        db.users.create_index([('email', ASCENDING)], unique=True)
        db.clientes.create_index([('cpf', ASCENDING)])
        db.orcamentos.create_index([('numero', ASCENDING)], unique=True)
        logger.info("✅ Indexes created")
    except:
        pass
    
    logger.info("🎉 DB init complete!")

# ===== ERROR HANDLERS =====
@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'message': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"❌ 500: {e}")
    return jsonify({'success': False, 'message': 'Internal error'}), 500

# ===== RUN =====
if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🌳 BIOMA UBERABA v3.4 FINAL - SISTEMA COMPLETO")
    print("=" * 80)
    
    init_db()
    
    is_production = os.getenv('FLASK_ENV') == 'production'
    base_url = 'https://bioma-system2.onrender.com' if is_production else 'http://localhost:5000'
    
    print(f"\n🚀 Servidor: {base_url}")
    print(f"👤 Login: admin / admin123")
    
    if db is not None:
        try:
            db.command('ping')
            print(f"💾 MongoDB: ✅ CONECTADO")
        except:
            print(f"💾 MongoDB: ❌ ERRO")
    else:
        print(f"💾 MongoDB: ❌ NÃO CONECTADO")
    
    if os.getenv('MAILERSEND_API_KEY'):
        print(f"📧 MailerSend: ✅ CONFIGURADO")
    else:
        print(f"📧 MailerSend: ⚠️  NÃO CONFIGURADO")
    
    print("\n" + "=" * 80)
    print(f"🕐 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"👨‍💻 Dev: @juanmarco1999")
    print("=" * 80 + "\n")
    
    port = int(os.environ.get('PORT', 5000))
    
    app.run(
        debug=False,
        host='0.0.0.0',
        port=port,
        threaded=True
    )