#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA UBERABA v3.2 - Sistema Ultra Profissional COMPLETO
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
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle

# ===== LOGGING DETALHADO =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

load_dotenv()

# ===== FLASK CONFIG =====
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'bioma-2025-v3-2-ultra-secure-key-complete')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = '/tmp'

CORS(app, supports_credentials=True)

# ===== MONGODB CONNECTION COM VERIFICAÇÃO EXPLÍCITA =====
def get_db():
    """Conecta ao MongoDB com verificação explícita"""
    try:
        username = urllib.parse.quote_plus(os.getenv('MONGO_USERNAME', ''))
        password = urllib.parse.quote_plus(os.getenv('MONGO_PASSWORD', ''))
        cluster = os.getenv('MONGO_CLUSTER', '')
        
        if not all([username, password, cluster]):
            logger.error("❌ MongoDB credentials missing in .env")
            return None
        
        uri = f"mongodb+srv://{username}:{password}@{cluster}/bioma_db?retryWrites=true&w=majority&appName=Juan-Analytics-DBServer"
        
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        
        # CORREÇÃO CRÍTICA: Teste de conexão EXPLÍCITO
        client.admin.command('ping')
        
        db_instance = client.bioma_db
        logger.info("✅ MongoDB Connected Successfully")
        return db_instance
        
    except Exception as e:
        logger.error(f"❌ MongoDB Connection Failed: {e}")
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
    """Decorator para rotas que precisam autenticação"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning(f"🚫 Unauthorized access attempt: {request.endpoint}")
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

# ===== EMAIL & SMS COM VERIFICAÇÃO 2FA =====
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
        logger.info(f"📧 Enviando email para: {to}")
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
            return {'success': True, 'message': 'Email enviado'}
        else:
            logger.error(f"❌ Email falhou: {r.status_code} - {r.text}")
            return {'success': False, 'message': f'Erro {r.status_code}'}
    except Exception as e:
        logger.error(f"❌ Email exception: {e}")
        return {'success': False, 'message': str(e)}

def send_sms(phone, message):
    """Envia SMS via MailerSend"""
    api_key = os.getenv('MAILERSEND_API_KEY')
    if not api_key:
        logger.warning("⚠️ SMS not configured")
        return {'success': False}
    
    # Formatar número para padrão internacional
    formatted_phone = phone
    if not phone.startswith('+'):
        # Remove caracteres especiais
        clean_phone = ''.join(filter(str.isdigit, phone))
        # Adiciona +55 se brasileiro
        if len(clean_phone) == 11 or len(clean_phone) == 10:
            formatted_phone = f'+55{clean_phone}'
        else:
            formatted_phone = f'+{clean_phone}'
    
    data = {
        "from": "BIOMA",
        "to": [formatted_phone],
        "text": message
    }
    
    try:
        r = requests.post(
            "https://api.mailersend.com/v1/sms",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json=data,
            timeout=10
        )
        
        if r.status_code == 202:
            logger.info(f"📱 SMS sent to: {phone}")
            return {'success': True}
        else:
            logger.warning(f"⚠️ SMS failed: {r.status_code}")
            return {'success': False}
    except Exception as e:
        logger.error(f"❌ SMS exception: {e}")
        return {'success': False}

# ===== ROUTES =====
@app.route('/')
def index():
    """Página inicial"""
    logger.info(f"🌐 Index accessed from {request.remote_addr}")
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    db_status = 'connected' if db is not None else 'disconnected'
    
    # Testar ping se conectado
    if db is not None:
        try:
            db.command('ping')
        except:
            db_status = 'error'
    
    return jsonify({
        'status': 'healthy',
        'time': datetime.now().isoformat(),
        'database': db_status,
        'version': '3.2.0'
    }), 200

# ===== AUTENTICAÇÃO COM 2FA =====
@app.route('/api/register', methods=['POST'])
def register():
    """Registro de novo usuário com código de verificação"""
    data = request.json
    logger.info(f"👤 Register attempt: {data.get('username')}")
    
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    # Verificar se usuário já existe
    if db.users.find_one({'$or': [
        {'username': data['username']},
        {'email': data['email']}
    ]}):
        logger.warning(f"⚠️ User already exists: {data.get('username')}")
        return jsonify({'success': False, 'message': 'Usuário ou email já cadastrado'})
    
    # Gerar código de verificação de 6 dígitos
    verification_code = str(random.randint(100000, 999999))
    
    # Criar usuário NÃO verificado
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
        logger.info(f"✅ User created (unverified): {data['username']}")
        
        # Enviar código por email
        email_result = send_email(
            data['email'],
            data['name'],
            '🔐 Código de Verificação BIOMA',
            f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px;">
                <div style="background: white; padding: 40px; border-radius: 15px; text-align: center;">
                    <h1 style="color: #7C3AED; font-size: 2.5rem; margin-bottom: 20px;">🌳 BIOMA UBERABA</h1>
                    <h2 style="color: #1F2937; margin-bottom: 30px;">Bem-vindo, {data['name']}!</h2>
                    <p style="font-size: 1.1rem; color: #6B7280; margin-bottom: 30px;">
                        Seu código de verificação é:
                    </p>
                    <div style="background: linear-gradient(135deg, #7C3AED, #EC4899); color: white; font-size: 3rem; font-weight: 900; padding: 30px; border-radius: 15px; letter-spacing: 10px; margin: 30px 0;">
                        {verification_code}
                    </div>
                    <p style="color: #9CA3AF; font-size: 0.9rem; margin-top: 30px;">
                        Este código expira em 24 horas.
                    </p>
                    <p style="color: #EF4444; font-size: 0.85rem; margin-top: 15px;">
                        ⚠️ Não compartilhe este código com ninguém!
                    </p>
                </div>
            </div>
            """
        )
        
        # Enviar código por SMS se tiver telefone
        if data.get('telefone'):
            sms_result = send_sms(
                data['telefone'],
                f"BIOMA: Seu codigo de verificacao e {verification_code}. Valido por 24h. Nao compartilhe!"
            )
            logger.info(f"📱 SMS sent: {sms_result.get('success', False)}")
        
        logger.info(f"📧 Email sent: {email_result.get('success', False)}")
        
        return jsonify({
            'success': True,
            'message': 'Conta criada! Verifique seu email/SMS para o código de verificação.',
            'verification_required': True
        })
        
    except Exception as e:
        logger.error(f"❌ Register error: {e}")
        return jsonify({'success': False, 'message': f'Erro ao criar conta: {str(e)}'}), 500

@app.route('/api/verify', methods=['POST'])
def verify():
    """Verifica código de ativação"""
    data = request.json
    username = data.get('username')
    code = data.get('code')
    
    logger.info(f"🔐 Verification attempt: {username}")
    
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    user = db.users.find_one({'username': username})
    
    if not user:
        return jsonify({'success': False, 'message': 'Usuário não encontrado'})
    
    if user.get('verified'):
        return jsonify({'success': False, 'message': 'Conta já verificada'})
    
    # Verificar se código expirou
    if 'verification_code_expires' in user:
        if datetime.now() > user['verification_code_expires']:
            return jsonify({'success': False, 'message': 'Código expirado. Solicite um novo.'})
    
    # Verificar código
    if user.get('verification_code') == code:
        db.users.update_one(
            {'username': username},
            {
                '$set': {'verified': True},
                '$unset': {'verification_code': '', 'verification_code_expires': ''}
            }
        )
        logger.info(f"✅ User verified: {username}")
        
        # Enviar email de boas-vindas
        send_email(
            user['email'],
            user['name'],
            '✅ Conta Ativada - BIOMA Uberaba',
            f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #10B981;">✅ Conta Ativada com Sucesso!</h1>
                <p>Olá <strong>{user['name']}</strong>,</p>
                <p>Sua conta foi verificada e ativada com sucesso!</p>
                <p>Você já pode fazer login no sistema BIOMA Uberaba.</p>
                <p style="margin-top: 30px;">Bem-vindo! 🎉</p>
            </div>
            """
        )
        
        return jsonify({'success': True, 'message': 'Conta verificada com sucesso! Faça login.'})
    else:
        return jsonify({'success': False, 'message': 'Código inválido'})

@app.route('/api/resend-verification', methods=['POST'])
def resend_verification():
    """Reenvia código de verificação"""
    data = request.json
    username = data.get('username')
    
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    user = db.users.find_one({'username': username})
    
    if not user:
        return jsonify({'success': False, 'message': 'Usuário não encontrado'})
    
    if user.get('verified'):
        return jsonify({'success': False, 'message': 'Conta já verificada'})
    
    # Gerar novo código
    verification_code = str(random.randint(100000, 999999))
    
    db.users.update_one(
        {'username': username},
        {
            '$set': {
                'verification_code': verification_code,
                'verification_code_expires': datetime.now() + timedelta(hours=24)
            }
        }
    )
    
    # Reenviar email
    send_email(
        user['email'],
        user['name'],
        '🔐 Novo Código de Verificação BIOMA',
        f"<h2>Seu novo código é: <strong style='font-size:2rem;'>{verification_code}</strong></h2><p>Válido por 24 horas.</p>"
    )
    
    # Reenviar SMS se tiver telefone
    if user.get('telefone'):
        send_sms(user['telefone'], f"BIOMA: Novo codigo: {verification_code}")
    
    logger.info(f"📧 Verification code resent: {username}")
    
    return jsonify({'success': True, 'message': 'Novo código enviado!'})

@app.route('/api/login', methods=['POST'])
def login():
    """Login com notificação SMS"""
    data = request.json
    logger.info(f"🔐 Login attempt: {data.get('username')}")
    
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    user = db.users.find_one({
        '$or': [
            {'username': data['username']},
            {'email': data['username']}
        ]
    })
    
    if user and check_password_hash(user['password'], data['password']):
        
        # CORREÇÃO: Verificar se conta foi verificada
        if not user.get('verified', False):
            logger.warning(f"⚠️ Unverified user: {data.get('username')}")
            return jsonify({
                'success': False,
                'message': 'Conta não verificada. Verifique seu email/SMS.',
                'verification_required': True,
                'username': user['username']
            })
        
        # Login aprovado
        session.permanent = True
        session['user_id'] = str(user['_id'])
        session['username'] = user['username']
        
        logger.info(f"✅ Login successful: {user['username']}")
        
        # Enviar notificação de login por SMS
        if user.get('telefone'):
            hora_login = datetime.now().strftime('%d/%m às %H:%M')
            send_sms(
                user['telefone'],
                f"BIOMA: Login realizado em {hora_login}. Se nao foi voce, altere sua senha imediatamente!"
            )
            logger.info(f"📱 Login SMS notification sent")
        
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

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout"""
    username = session.get('username', 'Unknown')
    session.clear()
    logger.info(f"👋 Logout: {username}")
    return jsonify({'success': True})

@app.route('/api/current-user')
def current_user():
    """Retorna usuário logado"""
    if 'user_id' in session:
        if db is None:
            return jsonify({'success': False, 'message': 'Database offline'})
        
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
        except Exception as e:
            logger.error(f"❌ Current user error: {e}")
    
    return jsonify({'success': False})

@app.route('/api/update-theme', methods=['POST'])
@login_required
def update_theme():
    """Atualiza tema do usuário"""
    if db is None:
        return jsonify({'success': False}), 500
    
    theme = request.json['theme']
    db.users.update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$set': {'theme': theme}}
    )
    logger.info(f"🎨 Theme updated: {theme} - {session.get('username')}")
    return jsonify({'success': True})

# ===== SYSTEM STATUS =====
@app.route('/api/system/status')
@login_required
def system_status():
    """Status do sistema com verificação REAL"""
    logger.info("📊 System status check")
    
    mongo_ok = False
    mongo_msg = 'Desconectado'
    last_check = datetime.now().isoformat()
    
    try:
        # CORREÇÃO CRÍTICA: Verificação explícita com None
        if db is not None:
            db.command('ping')
            mongo_ok = True
            mongo_msg = 'Conectado e operacional'
            logger.info("✅ MongoDB ping successful")
        else:
            mongo_msg = 'Banco de dados não inicializado'
            logger.warning("⚠️ MongoDB is None")
    except Exception as e:
        logger.error(f"❌ MongoDB ping failed: {e}")
        mongo_msg = f'Erro: {str(e)[:100]}'
    
    mailersend_ok = bool(os.getenv('MAILERSEND_API_KEY'))
    
    return jsonify({
        'success': True,
        'status': {
            'mongodb': {
                'operational': mongo_ok,
                'message': mongo_msg,
                'last_check': last_check
            },
            'mailersend': {
                'operational': mailersend_ok,
                'message': 'Configurado e ativo' if mailersend_ok else 'API Key não configurada'
            },
            'server': {
                'time': datetime.now().isoformat(),
                'environment': os.getenv('FLASK_ENV', 'development'),
                'version': '3.2.0'
            }
        }
    })

# ===== DASHBOARD =====
@app.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    """Estatísticas do dashboard"""
    logger.info("📊 Loading dashboard stats")
    
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        # CORREÇÃO: Agendamentos hoje
        hoje_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        hoje_fim = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
        
        agendamentos_hoje = 0
        if 'agendamentos' in db.list_collection_names():
            agendamentos_hoje = db.agendamentos.count_documents({
                'data': {
                    '$gte': hoje_inicio,
                    '$lte': hoje_fim
                },
                'status': {'$in': ['confirmado', 'em_andamento']}
            })
        
        stats = {
            'total_orcamentos': db.orcamentos.count_documents({}),
            'total_clientes': db.clientes.count_documents({}),
            'total_servicos': db.servicos.count_documents({'ativo': True}),
            'faturamento': sum(
                o.get('total_final', 0) 
                for o in db.orcamentos.find({'status': 'Aprovado'})
            ),
            'produtos_estoque_baixo': db.produtos.count_documents({
                '$expr': {'$lte': ['$estoque', '$estoque_minimo']}
            }),
            'agendamentos_hoje': agendamentos_hoje
        }
        
        logger.info(f"✅ Stats: {stats['total_orcamentos']} orçamentos, R$ {stats['faturamento']:.2f}")
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        logger.error(f"❌ Dashboard error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    
    
# ===== CLIENTES =====
@app.route('/api/clientes', methods=['GET', 'POST'])
@login_required
def clientes():
    """CRUD de clientes"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    if request.method == 'GET':
        logger.info("📋 Loading clients")
        try:
            clientes_list = list(db.clientes.find({}).sort('nome', ASCENDING))
            
            # Enriquecer com dados CRM
            for cliente in clientes_list:
                cliente_cpf = cliente.get('cpf')
                
                # Total gasto
                total_gasto = sum(
                    o.get('total_final', 0)
                    for o in db.orcamentos.find({
                        'cliente_cpf': cliente_cpf,
                        'status': 'Aprovado'
                    })
                )
                cliente['total_gasto'] = total_gasto
                
                # Última visita
                ultimo_orc = db.orcamentos.find_one(
                    {'cliente_cpf': cliente_cpf},
                    sort=[('created_at', DESCENDING)]
                )
                cliente['ultima_visita'] = ultimo_orc['created_at'] if ultimo_orc else None
                
                # Total de visitas
                cliente['total_visitas'] = db.orcamentos.count_documents({'cliente_cpf': cliente_cpf})
            
            result = convert_objectid(clientes_list)
            logger.info(f"✅ {len(result)} clients loaded")
            return jsonify({'success': True, 'clientes': result})
            
        except Exception as e:
            logger.error(f"❌ Error loading clients: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # POST - Criar/Atualizar cliente
    data = request.json
    logger.info(f"➕ Saving client: {data.get('nome')}")
    
    try:
        existing = db.clientes.find_one({'cpf': data['cpf']})
        
        cliente_data = {
            'nome': data['nome'],
            'cpf': data['cpf'],
            'email': data.get('email', ''),
            'telefone': data.get('telefone', ''),
            'endereco': data.get('endereco', ''),
            'tags': data.get('tags', []),
            'notas': data.get('notas', []),
            'updated_at': datetime.now()
        }
        
        if existing:
            db.clientes.update_one(
                {'cpf': data['cpf']},
                {'$set': cliente_data}
            )
            logger.info(f"✅ Client updated: {data['nome']}")
        else:
            cliente_data['created_at'] = datetime.now()
            db.clientes.insert_one(cliente_data)
            logger.info(f"✅ Client created: {data['nome']}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"❌ Error saving client: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clientes/<id>', methods=['DELETE'])
@login_required
def delete_cliente(id):
    """Deleta cliente"""
    if db is None:
        return jsonify({'success': False}), 500
    
    logger.info(f"🗑️ Deleting client: {id}")
    try:
        result = db.clientes.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            logger.info("✅ Client deleted")
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Cliente não encontrado'})
    except Exception as e:
        logger.error(f"❌ Delete error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clientes/buscar')
@login_required
def buscar_clientes():
    """Busca clientes por nome ou CPF"""
    if db is None:
        return jsonify({'success': False}), 500
    
    termo = request.args.get('termo', '')
    logger.info(f"🔍 Searching clients: {termo}")
    
    try:
        regex = {'$regex': termo, '$options': 'i'}
        clientes = list(db.clientes.find({
            '$or': [
                {'nome': regex},
                {'cpf': regex}
            ]
        }).limit(10))
        
        result = convert_objectid(clientes)
        return jsonify({'success': True, 'clientes': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== PROFISSIONAIS =====
@app.route('/api/profissionais', methods=['GET', 'POST'])
@login_required
def profissionais():
    """CRUD de profissionais"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    if request.method == 'GET':
        logger.info("📋 Loading professionals")
        try:
            profs = list(db.profissionais.find({}).sort('nome', ASCENDING))
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
        logger.info(f"✅ Professional created: {data['nome']}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Error saving professional: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profissionais/<id>', methods=['DELETE'])
@login_required
def delete_profissional(id):
    """Deleta profissional"""
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
    """CRUD de serviços"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    if request.method == 'GET':
        logger.info("📋 Loading services")
        try:
            servs = list(db.servicos.find({}).sort('nome', ASCENDING))
            result = convert_objectid(servs)
            logger.info(f"✅ {len(result)} services loaded")
            return jsonify({'success': True, 'servicos': result})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # POST - Criar serviço com múltiplos tamanhos
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
        
        logger.info(f"✅ Service created: {count} SKUs")
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        logger.error(f"❌ Error creating service: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/servicos/<id>', methods=['DELETE'])
@login_required
def delete_servico(id):
    """Deleta serviço"""
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
    """Busca serviços por nome"""
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
    """CRUD de produtos"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    if request.method == 'GET':
        logger.info("📋 Loading products")
        try:
            prods = list(db.produtos.find({}).sort('nome', ASCENDING))
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
            'sku': data.get('sku', f"PROD-{datetime.now().timestamp()}"),
            'preco': float(data.get('preco', 0)),
            'custo': float(data.get('custo', 0)),
            'estoque': int(data.get('estoque', 0)),
            'estoque_minimo': int(data.get('estoque_minimo', 5)),
            'categoria': data.get('categoria', 'Produto'),
            'ativo': True,
            'created_at': datetime.now()
        }).inserted_id
        
        # Registrar movimentação de estoque inicial
        if int(data.get('estoque', 0)) > 0:
            db.estoque_movimentacoes.insert_one({
                'produto_id': produto_id,
                'tipo': 'entrada',
                'quantidade': int(data.get('estoque', 0)),
                'motivo': 'Cadastro inicial',
                'custo_unitario': float(data.get('custo', 0)),
                'usuario': session.get('username', 'system'),
                'data': datetime.now()
            })
        
        logger.info(f"✅ Product created: {data['nome']}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Error creating product: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/produtos/<id>', methods=['DELETE'])
@login_required
def delete_produto(id):
    """Deleta produto"""
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
    """Busca produtos por nome"""
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
    """CRUD de orçamentos"""
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
    
    # POST - Criar orçamento
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
        subtotal = sum(s['total'] for s in data.get('servicos', [])) + \
                   sum(p['total'] for p in data.get('produtos', []))
        
        desconto_global = float(data.get('desconto_global', 0))
        desconto_valor = subtotal * (desconto_global / 100)
        total_com_desconto = subtotal - desconto_valor
        
        cashback_perc = float(data.get('cashback_perc', 0))
        cashback_valor = total_com_desconto * (cashback_perc / 100)
        
        # Gerar número sequencial
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
        
        logger.info(f"✅ Budget #{numero} created")
        
        # Atualizar estoque dos produtos vendidos
        for produto in data.get('produtos', []):
            if 'id' in produto:
                prod = db.produtos.find_one({'_id': ObjectId(produto['id'])})
                if prod:
                    novo_estoque = prod.get('estoque', 0) - produto.get('qtd', 1)
                    db.produtos.update_one(
                        {'_id': ObjectId(produto['id'])},
                        {'$set': {'estoque': novo_estoque}}
                    )
                    
                    # Registrar movimentação
                    db.estoque_movimentacoes.insert_one({
                        'produto_id': ObjectId(produto['id']),
                        'tipo': 'saida',
                        'quantidade': produto.get('qtd', 1),
                        'motivo': f"Orçamento #{numero}",
                        'usuario': session.get('username'),
                        'data': datetime.now()
                    })
        
        # Se aprovado, enviar email/SMS
        if data.get('status') == 'Aprovado':
            if data.get('cliente_email'):
                send_email(
                    data['cliente_email'],
                    data['cliente_nome'],
                    f'✅ Contrato BIOMA #{numero} Aprovado',
                    f"""
                    <div style="font-family: Arial, sans-serif; padding: 20px;">
                        <h1 style="color: #10B981;">✅ Contrato Aprovado!</h1>
                        <h2>Olá {data['cliente_nome']},</h2>
                        <p>Seu contrato <strong>#{numero}</strong> foi aprovado com sucesso!</p>
                        <h3 style="color: #7C3AED;">Valor Total: R$ {total_com_desconto:.2f}</h3>
                        <p>Cashback: R$ {cashback_valor:.2f}</p>
                        <p>Forma de pagamento: {data.get('pagamento', {}).get('tipo', 'N/A')}</p>
                        <p style="margin-top: 30px;">Obrigado pela preferência!</p>
                        <p><strong>BIOMA Uberaba</strong></p>
                    </div>
                    """
                )
            
            if data.get('cliente_telefone'):
                send_sms(
                    data['cliente_telefone'],
                    f"BIOMA: Contrato #{numero} aprovado! Total: R$ {total_com_desconto:.2f}. Cashback: R$ {cashback_valor:.2f}"
                )
        
        return jsonify({
            'success': True,
            'numero': numero,
            'id': str(orc_id)
        })
        
    except Exception as e:
        logger.error(f"❌ Error creating budget: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/orcamentos/<id>', methods=['DELETE'])
@login_required
def delete_orcamento(id):
    """Deleta orçamento"""
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
    """Lista contratos aprovados"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        contratos_list = list(db.orcamentos.find({'status': 'Aprovado'}).sort('created_at', DESCENDING))
        result = convert_objectid(contratos_list)
        return jsonify({'success': True, 'contratos': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== FILA DE ATENDIMENTO =====
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
            result = convert_objectid(fila_list)
            return jsonify({'success': True, 'fila': result})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # POST - Adicionar à fila
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
        
        # Enviar SMS com posição
        if data.get('cliente_telefone'):
            send_sms(
                data['cliente_telefone'],
                f"BIOMA: Voce esta na posicao {total + 1} da fila! Aguarde ser chamado."
            )
        
        logger.info(f"✅ Added to queue: {data['cliente_nome']} - Position {total + 1}")
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
        if result.deleted_count > 0:
            return jsonify({'success': True})
        return jsonify({'success': False})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

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
        result = convert_objectid(produtos)
        return jsonify({'success': True, 'produtos': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/movimentacao', methods=['POST'])
@login_required
def estoque_movimentacao():
    """Registra movimentação de estoque"""
    if db is None:
        return jsonify({'success': False}), 500
    
    data = request.json
    try:
        produto = db.produtos.find_one({'_id': ObjectId(data['produto_id'])})
        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'})
        
        qtd = int(data['quantidade'])
        tipo = data['tipo']
        
        # Atualizar estoque
        novo_estoque = produto.get('estoque', 0)
        if tipo == 'entrada':
            novo_estoque += qtd
        else:
            novo_estoque -= qtd
        
        db.produtos.update_one(
            {'_id': ObjectId(data['produto_id'])},
            {'$set': {'estoque': novo_estoque}}
        )
        
        # Registrar movimentação
        db.estoque_movimentacoes.insert_one({
            'produto_id': ObjectId(data['produto_id']),
            'tipo': tipo,
            'quantidade': qtd,
            'motivo': data.get('motivo', ''),
            'usuario': session.get('username'),
            'data': datetime.now()
        })
        
        logger.info(f"✅ Stock movement: {tipo} - {qtd} units")
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== IMPORTAÇÃO CSV ULTRA ROBUSTA =====
@app.route('/api/importar', methods=['POST'])
@login_required
def importar():
    """Importa CSV/XLSX com parser ultra flexível"""
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
        return jsonify({'success': False, 'message': 'Apenas CSV ou XLSX permitidos'})
    
    logger.info(f"📤 Importing {ext.upper()} - Type: {tipo}")
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        count_success = 0
        count_error = 0
        erros_detalhados = []
        rows = []
        
        # Ler arquivo com múltiplas encodings
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
                except Exception as e:
                    logger.error(f"❌ CSV read error: {e}")
                    continue
        else:
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
                logger.info(f"✅ XLSX read - {len(rows)} rows")
            except Exception as e:
                logger.error(f"❌ XLSX read error: {e}")
                return jsonify({'success': False, 'message': f'Erro ao ler XLSX: {str(e)}'})
        
        # Processar PRODUTOS
        if tipo == 'produtos':
            for idx, row in enumerate(rows, 1):
                try:
                    r = {k.lower().strip(): v for k, v in row.items() if k and v is not None}
                    
                    # Ignorar linhas vazias
                    if not r or all(not v for v in r.values()):
                        continue
                    
                    # Nome (obrigatório)
                    nome = None
                    for col in ['nome', 'produto', 'name', 'product']:
                        if col in r and r[col] and str(r[col]).strip():
                            nome = str(r[col]).strip()
                            break
                    
                    if not nome or len(nome) < 2:
                        erros_detalhados.append(f"Linha {idx}: Nome inválido ou vazio")
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
                    
                    # Preço (obrigatório) - Parser ultra flexível
                    preco = 0.0
                    for col in ['preco', 'preço', 'price', 'valor', 'value']:
                        if col in r and r[col]:
                            try:
                                val = str(r[col]).replace('R$', '').replace('r$', '').strip()
                                # Detectar formato
                                if ',' in val and '.' in val:
                                    # 1.234,56 → 1234.56
                                    val = val.replace('.', '').replace(',', '.')
                                elif ',' in val:
                                    # 49,90 → 49.90
                                    val = val.replace(',', '.')
                                # Limpar caracteres
                                val = ''.join(c for c in val if c.isdigit() or c == '.')
                                if val:
                                    preco = float(val)
                                    break
                            except:
                                continue
                    
                    if preco <= 0:
                        erros_detalhados.append(f"Linha {idx}: Preço inválido ({nome})")
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
                    
                    # Inserir produto
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
                    logger.error(f"❌ Row {idx} error: {e}")
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
                    
                    # Processar tamanhos
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
                        erros_detalhados.append(f"Linha {idx}: Nenhum preço válido ({nome})")
                        count_error += 1
                    
                except Exception as e:
                    erros_detalhados.append(f"Linha {idx}: {str(e)}")
                    logger.error(f"❌ Row {idx} error: {e}")
                    count_error += 1
        
        # Remover arquivo temporário
        if os.path.exists(filepath):
            os.remove(filepath)
        
        logger.info(f"🎉 Import complete: {count_success} success, {count_error} errors")
        
        return jsonify({
            'success': True,
            'message': f'{count_success} registros importados!',
            'count_success': count_success,
            'count_error': count_error,
            'erros_detalhados': erros_detalhados[:10]  # Primeiros 10 erros
        })
        
    except Exception as e:
        logger.error(f"❌ Import error: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@app.route('/api/template/download/<tipo>')
@login_required
def download_template(tipo):
    """Download template XLSX profissional"""
    wb = Workbook()
    ws = wb.active
    
    # Estilos
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
        
        # Aplicar estilo ao header
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border
        
        # Exemplos
        ws.append(['Shampoo 500ml', 'Loreal', 'SHAMP-500', 49.90, 20.00, 50, 'SHAMPOO'])
        ws.append(['Condicionador 500ml', 'Loreal', 'COND-500', 49.90, 20.00, 50, 'CONDICIONADOR'])
        ws.append(['Máscara Hidratante 250g', 'Kerastase', 'MASK-250', 89.90, 35.00, 30, 'TRATAMENTO'])
        
        # Ajustar largura das colunas
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 12
        ws.column_dimensions['F'].width = 12
        ws.column_dimensions['G'].width = 18
        
    else:  # servicos
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
        ws.append(['Escova', 'Cabelo', 35, 45, 55, 70, 85, 100])
        
        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            ws.column_dimensions[col].width = 15
    
    # Salvar
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
    """Configurações da unidade"""
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
        logger.info(f"✅ Config updated by {session.get('username')}")
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== GERAÇÃO DE PDF PARA CONTRATOS =====
@app.route('/api/orcamento/<id>/pdf')
@login_required
def gerar_pdf_orcamento(id):
    """Gera PDF do contrato EXATAMENTE conforme modelo"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        orcamento = db.orcamentos.find_one({'_id': ObjectId(id)})
        if not orcamento:
            return jsonify({'success': False, 'message': 'Orçamento não encontrado'}), 404
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # HEADER COM LOGO
        p.setFillColor(HexColor('#7C3AED'))
        p.setFont("Helvetica-Bold", 28)
        p.drawString(50, height - 60, "BIOMA UBERABA")
        
        p.setFillColor(black)
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 80, "Av. Santos Dumont 3110 - Santa Maria - Uberaba/MG")
        p.drawString(50, height - 95, "Tel: (34) 99235-5890 | Email: biomauberaba@gmail.com")
        
        # LINHA SEPARADORA
        p.setStrokeColor(HexColor('#7C3AED'))
        p.setLineWidth(2)
        p.line(50, height - 110, width - 50, height - 110)
        
        # TÍTULO CONTRATO
        p.setFillColor(HexColor('#7C3AED'))
        p.setFont("Helvetica-Bold", 20)
        p.drawString(50, height - 145, f"CONTRATO #{orcamento.get('numero', 'N/A')}")
        
        # LINHA ABAIXO DO TÍTULO
        p.setStrokeColor(HexColor('#7C3AED'))
        p.setLineWidth(1)
        p.line(50, height - 155, width - 50, height - 155)
        
        # DADOS DO CLIENTE
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
            
            # TABELA DE SERVIÇOS COM COR ROXA
            data_servicos = [
                ['Serviço', 'Tamanho', 'Qtd', 'Valor Unit.', 'Total']
            ]
            
            for s in orcamento.get('servicos', []):
                data_servicos.append([
                    s.get('nome', ''),
                    s.get('tamanho', ''),
                    str(s.get('qtd', 1)),
                    f"R$ {s.get('preco_unit', 0):.2f}",
                    f"R$ {s.get('total', 0):.2f}"
                ])
            
            table_servicos = Table(data_servicos, colWidths=[200, 80, 50, 80, 80])
            table_servicos.setStyle(TableStyle([
                # HEADER ROXO
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#7C3AED')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                # CORPO
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#F3F4F6')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#E5E7EB')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F9FAFB')])
            ]))
            
            table_servicos.wrapOn(p, width, height)
            table_servicos.drawOn(p, 50, y - len(data_servicos) * 22)
            y -= len(data_servicos) * 22 + 30
        
        # PRODUTOS (SE HOUVER)
        if orcamento.get('produtos') and y > 250:
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, y, "PRODUTOS")
            y -= 25
            
            data_produtos = [
                ['Produto', 'Marca', 'Qtd', 'Valor Unit.', 'Total']
            ]
            
            for prod in orcamento.get('produtos', []):
                data_produtos.append([
                    prod.get('nome', ''),
                    prod.get('marca', ''),
                    str(prod.get('qtd', 1)),
                    f"R$ {prod.get('preco_unit', 0):.2f}",
                    f"R$ {prod.get('total', 0):.2f}"
                ])
            
            table_produtos = Table(data_produtos, colWidths=[200, 80, 50, 80, 80])
            table_produtos.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#7C3AED')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#F3F4F6')),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#E5E7EB')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F9FAFB')])
            ]))
            
            table_produtos.wrapOn(p, width, height)
            table_produtos.drawOn(p, 50, y - len(data_produtos) * 22)
            y -= len(data_produtos) * 22 + 30
        
        # TOTAL
        if y < 180:
            p.showPage()
            y = height - 50
        
        total_final = orcamento.get('total_final', 0)
        
        p.setFont("Helvetica-Bold", 18)
        p.setFillColor(HexColor('#7C3AED'))
        p.drawString(width - 250, y, f"TOTAL: R$ {total_final:.2f}")
        y -= 25
        
        # FORMA DE PAGAMENTO
        p.setFont("Helvetica", 11)
        p.setFillColor(black)
        pagamento = orcamento.get('pagamento', {}).get('tipo', 'N/A')
        p.drawString(50, y, f"Forma de pagamento: {pagamento}")
        
        # RODAPÉ
        p.line(50, 80, width - 50, 80)
        p.setFont("Helvetica", 8)
        p.drawString(50, 65, f"Data de emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        p.drawString(50, 50, "BIOMA Uberaba - CNPJ: 49.470.937/0001-10")
        
        # ASSINATURA (SE APROVADO)
        if orcamento.get('status') == 'Aprovado':
            p.setFont("Helvetica", 10)
            p.line(50, 135, 250, 135)
            p.drawString(50, 120, "Assinatura do Cliente")
            
            p.line(width - 250, 135, width - 50, 135)
            p.drawString(width - 250, 120, "BIOMA Uberaba")
        
        p.save()
        buffer.seek(0)
        
        logger.info(f"✅ PDF gerado: Contrato #{orcamento.get('numero')}")
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'contrato_bioma_{orcamento.get("numero")}.pdf'
        )
        
    except Exception as e:
        logger.error(f"❌ Erro PDF: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== AGENDAMENTOS =====
@app.route('/api/agendamentos', methods=['GET', 'POST'])
@login_required
def agendamentos():
    """CRUD de agendamentos"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    if request.method == 'GET':
        try:
            agends = list(db.agendamentos.find({}).sort('data', ASCENDING))
            result = convert_objectid(agends)
            return jsonify({'success': True, 'agendamentos': result})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # POST
    data = request.json
    try:
        db.agendamentos.insert_one({
            'cliente_id': data.get('cliente_id'),
            'profissional_id': data.get('profissional_id'),
            'servico_id': data.get('servico_id'),
            'data': datetime.fromisoformat(data['data']),
            'horario': data['horario'],
            'status': 'confirmado',
            'created_at': datetime.now()
        })
        
        logger.info(f"✅ Appointment created: {data.get('data')} {data.get('horario')}")
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== RELATÓRIOS =====
@app.route('/api/relatorios/faturamento')
@login_required
def relatorio_faturamento():
    """Relatório de faturamento por período"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        data_inicio = request.args.get('inicio')
        data_fim = request.args.get('fim')
        
        query = {'status': 'Aprovado'}
        if data_inicio and data_fim:
            query['created_at'] = {
                '$gte': datetime.fromisoformat(data_inicio),
                '$lte': datetime.fromisoformat(data_fim)
            }
        
        orcamentos = list(db.orcamentos.find(query))
        
        total = sum(o.get('total_final', 0) for o in orcamentos)
        total_cashback = sum(o.get('cashback_valor', 0) for o in orcamentos)
        
        return jsonify({
            'success': True,
            'total': total,
            'total_cashback': total_cashback,
            'quantidade': len(orcamentos)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/relatorios/servicos')
@login_required
def relatorio_servicos():
    """Top serviços mais vendidos"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        # Agregar serviços de todos os orçamentos
        pipeline = [
            {'$match': {'status': 'Aprovado'}},
            {'$unwind': '$servicos'},
            {'$group': {
                '_id': '$servicos.nome',
                'total': {'$sum': '$servicos.total'},
                'quantidade': {'$sum': '$servicos.qtd'}
            }},
            {'$sort': {'total': -1}},
            {'$limit': 10}
        ]
        
        result = list(db.orcamentos.aggregate(pipeline))
        
        return jsonify({
            'success': True,
            'servicos': convert_objectid(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== INICIALIZAÇÃO DO BANCO =====
def init_db():
    """Inicializa banco de dados com dados padrão"""
    if db is None:
        logger.warning("⚠️ Database not available for initialization")
        return
    
    logger.info("🔧 Initializing database...")
    
    # Criar usuário admin se não existir
    if db.users.count_documents({}) == 0:
        db.users.insert_one({
            'name': 'Administrador',
            'username': 'admin',
            'email': 'admin@bioma.com',
            'telefone': '',
            'password': generate_password_hash('admin123'),
            'role': 'admin',
            'theme': 'light',
            'verified': True,  # Admin já verificado
            'created_at': datetime.now()
        })
        logger.info("✅ Admin user created: admin/admin123")
    
    # Criar serviços padrão se não existir
    if db.servicos.count_documents({}) == 0:
        services = [
            ('Hidratação', 'Tratamento', [50, 60, 80, 100, 120, 150]),
            ('Corte Feminino', 'Cabelo', [40, 50, 60, 80, 100, 120]),
            ('Corte Masculino', 'Cabelo', [30, 40, 50, 60, 70, 80]),
            ('Escova', 'Cabelo', [35, 45, 55, 70, 85, 100]),
            ('Coloração', 'Tratamento', [80, 100, 120, 150, 180, 220])
        ]
        
        tamanhos = ['Kids', 'Masculino', 'Curto', 'Médio', 'Longo', 'Extra Longo']
        
        for nome, cat, precos in services:
            for tam, preco in zip(tamanhos, precos):
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
        
        logger.info(f"✅ {len(services) * 6} service SKUs created")
    
    # Criar produtos padrão se não existir
    if db.produtos.count_documents({}) == 0:
        produtos = [
            ('Shampoo 500ml', 'Loreal', 49.90, 20.00, 50),
            ('Condicionador 500ml', 'Loreal', 49.90, 20.00, 50),
            ('Máscara Hidratante 250g', 'Kerastase', 89.90, 35.00, 30),
            ('Óleo Reparador 100ml', 'Moroccan Oil', 129.90, 50.00, 25),
            ('Leave-in 200ml', 'Tresemmé', 39.90, 15.00, 60)
        ]
        
        for nome, marca, preco, custo, estoque in produtos:
            db.produtos.insert_one({
                'nome': nome,
                'marca': marca,
                'sku': f"PROD-{nome[:3].upper()}-{int(preco)}",
                'preco': preco,
                'custo': custo,
                'estoque': estoque,
                'estoque_minimo': 10,
                'categoria': 'Produtos Capilares',
                'ativo': True,
                'created_at': datetime.now()
            })
        
        logger.info(f"✅ {len(produtos)} products created")
    
    # Criar índices para performance
    try:
        db.users.create_index([('username', ASCENDING)], unique=True)
        db.users.create_index([('email', ASCENDING)], unique=True)
        db.clientes.create_index([('cpf', ASCENDING)])
        db.orcamentos.create_index([('numero', ASCENDING)], unique=True)
        db.orcamentos.create_index([('created_at', DESCENDING)])
        logger.info("✅ Database indexes created")
    except Exception as e:
        logger.warning(f"⚠️ Index creation warning: {e}")
    
    logger.info("🎉 Database initialization complete!")

# ===== ERROR HANDLERS =====
@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"❌ Internal error: {e}")
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({'success': False, 'message': 'Arquivo muito grande (máx 16MB)'}), 413

# ===== RUN APPLICATION =====
if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🌳 BIOMA UBERABA v3.2 - SISTEMA ULTRA PROFISSIONAL COMPLETO")
    print("=" * 80)
    
    # Inicializar banco de dados
    init_db()
    
    # Configurações do ambiente
    is_production = os.getenv('FLASK_ENV') == 'production'
    base_url = 'https://bioma-system2.onrender.com' if is_production else 'http://localhost:5000'
    
    print(f"\n🚀 Servidor: {base_url}")
    print(f"🔒 HTTPS: {'✅ ATIVO (Produção)' if is_production else '⚠️  Desabilitado (Local)'}")
    print(f"👤 Login Padrão: admin / admin123")
    
    # Status do MongoDB
    if db is not None:
        try:
            db.command('ping')
            print(f"💾 MongoDB: ✅ CONECTADO")
            print(f"📊 Coleções: {', '.join(db.list_collection_names()[:5])}...")
        except:
            print(f"💾 MongoDB: ❌ ERRO DE PING")
    else:
        print(f"💾 MongoDB: ❌ NÃO CONECTADO")
    
    # Status do MailerSend
    if os.getenv('MAILERSEND_API_KEY'):
        print(f"📧 MailerSend: ✅ CONFIGURADO")
    else:
        print(f"📧 MailerSend: ⚠️  NÃO CONFIGURADO")
    
    print("\n" + "=" * 80)
    print(f"🕐 Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"👨‍💻 Desenvolvedor: @juanmarco1999")
    print(f"📧 Email: 180147064@aluno.unb.br")
    print("=" * 80 + "\n")
    
    # Determinar porta
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"🚀 Starting Flask server on port {port}")
    
    # Rodar aplicação
    app.run(
        debug=False,
        host='0.0.0.0',
        port=port,
        threaded=True
    )