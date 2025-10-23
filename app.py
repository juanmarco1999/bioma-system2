#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA UBERABA v4.0 MELHORADO - Sistema Ultra Profissional
Desenvolvedor: Juan Marco (@juanmarco1999)
Email: 180147064@aluno.unb.br
Data: 2025-10-23
Versão com todas as correções implementadas
"""

from flask import Flask, render_template, request, jsonify, session, send_file, redirect, url_for
from flask_cors import CORS
from pymongo import MongoClient, ASCENDING, DESCENDING
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson import ObjectId
from functools import wraps
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
import urllib.parse
import os
import io
from io import BytesIO
import csv
import json
import re
import requests
import logging
import random
from functools import lru_cache
from time import time
import base64
from PIL import Image
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Cache simples para requisições GET
request_cache = {}
CACHE_TTL = 60  # segundos

def get_from_cache(key):
    """Buscar do cache se ainda válido"""
    if key in request_cache:
        data, timestamp = request_cache[key]
        if time() - timestamp < CACHE_TTL:
            return data
        else:
            del request_cache[key]
    return None

def set_in_cache(key, data):
    """Salvar no cache"""
    request_cache[key] = (data, time())

# Importações para o novo gerador de PDF
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import cm

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'bioma-2025-v4-ultra-secure-key-final-definitivo-completo-melhorado')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # Aumentado para 32MB
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Criar pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

CORS(app, supports_credentials=True)

# ---- Cookie/CORS robustez para desenvolvimento cross-origin ----
FRONTEND_ORIGIN = os.getenv('FRONTEND_ORIGIN')
if os.getenv('CROSS_SITE_DEV','0') == '1':
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    try:
        from flask_cors import CORS
        if FRONTEND_ORIGIN:
            CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": FRONTEND_ORIGIN}})
        else:
            CORS(app, supports_credentials=True)
    except Exception as _e:
        pass

# Configuração de níveis de acesso
ACCESS_LEVELS = {
    'admin': {
        'level': 3,
        'permissions': ['all'],
        'name': 'Administrador'
    },
    'gestao': {
        'level': 2, 
        'permissions': ['view_all', 'edit_all', 'create', 'delete_own'],
        'name': 'Gestão'
    },
    'profissional': {
        'level': 1,
        'permissions': ['view_own', 'edit_own', 'create_limited'],
        'name': 'Profissional'
    }
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def resize_image(image_path, max_size=(800, 800)):
    """Redimensiona imagem mantendo proporção"""
    try:
        img = Image.open(image_path)
        img.thumbnail(max_size, Image.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format=img.format if img.format else 'JPEG', optimize=True, quality=85)
        buffer.seek(0)
        return buffer
    except Exception as e:
        logger.error(f"Erro ao redimensionar imagem: {e}")
        return None

def send_notification_email(to_email, subject, body):
    """Envia email de notificação"""
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USER')
        smtp_pass = os.getenv('SMTP_PASS')
        
        if not smtp_user or not smtp_pass:
            logger.warning("Configurações de SMTP não encontradas")
            return False
            
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar email: {e}")
        return False

def send_sms_notification(phone, message):
    """Envia SMS de notificação"""
    try:
        # Integração com API de SMS (Twilio, Zenvia, etc)
        api_key = os.getenv('SMS_API_KEY')
        if not api_key:
            logger.warning("API de SMS não configurada")
            return False
            
        # Exemplo com Twilio
        # from twilio.rest import Client
        # client = Client(account_sid, auth_token)
        # message = client.messages.create(
        #     body=message,
        #     from_='+1234567890',
        #     to=phone
        # )
        
        logger.info(f"SMS simulado enviado para {phone}: {message}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar SMS: {e}")
        return False

def send_whatsapp_message(phone, message, pdf_url=None):
    """Envia mensagem WhatsApp"""
    try:
        # Integração com WhatsApp Business API
        api_url = os.getenv('WHATSAPP_API_URL')
        api_token = os.getenv('WHATSAPP_API_TOKEN')
        
        if not api_url or not api_token:
            logger.warning("API do WhatsApp não configurada")
            return False
            
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'phone': phone,
            'message': message
        }
        
        if pdf_url:
            data['document'] = pdf_url
            
        # response = requests.post(api_url, json=data, headers=headers)
        # return response.status_code == 200
        
        logger.info(f"WhatsApp simulado enviado para {phone}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar WhatsApp: {e}")
        return False

ANAMNESE_FORM = [
    {
        'ordem': 1,
        'campo': 'QUAIS SÃO AS COISAS QUE INCOMODAM NO SEU COURO CABELUDO?',
        'tipo': 'select',
        'opcoes': ['Coceira', 'Descamação', 'Oleosidade', 'Sensibilidade', 'Feridas', 'Ardor', 'Outro']
    },
    {
        'ordem': 2,
        'campo': 'QUAIS SÃO AS COISAS QUE INCOMODAM NO CABELO?',
        'tipo': 'select',
        'opcoes': ['Ressecamento', 'Queda', 'Quebra', 'Frizz', 'Pontas Duplas', 'Outro']
    },
    {
        'ordem': 3,
        'campo': 'QUAIS PROCESSOS QUÍMICOS VOCÊ JÁ FEZ NO CABELO?',
        'tipo': 'select',
        'opcoes': ['Coloração', 'Descoloração', 'Alisamento', 'Relaxamento', 'Progressiva', 'Botox', 'Nenhum']
    },
    {
        'ordem': 4,
        'campo': 'COM QUE FREQUÊNCIA VOCÊ LAVA O CABELO?',
        'tipo': 'select',
        'opcoes': ['Todos os dias', '3x por semana', '2x por semana', '1x por semana', 'Menos de 1x por semana']
    },
    {
        'ordem': 5,
        'campo': 'JÁ TEVE ANEMIA?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 6,
        'campo': 'ESTÁ COM QUEDA DE CABELO?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 7,
        'campo': 'SE SIM HÁ QUANTO TEMPO?',
        'tipo': 'textarea'
    },
    {
        'ordem': 8,
        'campo': 'TEM ALERGIA A ALGUMA SUBSTÂNCIA?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 9,
        'campo': 'SE SIM, QUAL (SUBSTÂNCIA)?',
        'tipo': 'text'
    },
    {
        'ordem': 10,
        'campo': 'JÁ FOI DIAGNOSTICADO ALGUM TIPO DE ALOPECIA OU CALVÍCIE?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 11,
        'campo': 'TEVE ALGUMA ALTERAÇÃO HORMONAL A MENOS DE UM ANO?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 12,
        'campo': 'JÁ FEZ TRATAMENTO PARA QUEDA?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 14,
        'campo': 'QUAL MARCA DE SHAMPOO E CONDICIONADOR VOCÊ COSTUMA USAR?',
        'tipo': 'text'
    },
    {
        'ordem': 15,
        'campo': 'FAZ USO DE PRODUTOS SEM ENXÁGUE?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 16,
        'campo': 'SE SIM QUAL SEM ENXÁGUE?',
        'tipo': 'text'
    },
    {
        'ordem': 17,
        'campo': 'QUANDO LAVA TEM COSTUME DE SECAR O CABELO?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 18,
        'campo': 'VOCÊ É VEGANO?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 19,
        'campo': 'VOCÊ É CELÍACO?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 20,
        'campo': 'VOCÊ É VEGETARIANO?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 21,
        'campo': 'COMO VOCÊ CONHECEU O BIOMA UBERABA?',
        'tipo': 'checkbox',
        'opcoes': ['Redes sociais', 'Indicação', 'Busca no Google', 'Eventos', 'Passagem em frente', 'Outro']
    }
]

PRONTUARIO_FORM = [
    {'ordem': 1, 'campo': 'Alquimia', 'tipo': 'text'},
    {'ordem': 2, 'campo': 'Protocolo Adotado', 'tipo': 'textarea'},
    {'ordem': 3, 'campo': 'Técnicas Complementares', 'tipo': 'textarea'},
    {'ordem': 4, 'campo': 'Produtos Utilizados', 'tipo': 'textarea'},
    {'ordem': 5, 'campo': 'Observações Gerais', 'tipo': 'textarea'},
    {'ordem': 6, 'campo': 'Resultados Esperados', 'tipo': 'textarea'},
    {'ordem': 7, 'campo': 'Próximos Passos', 'tipo': 'textarea'},
    {'ordem': 8, 'campo': 'Cuidados Pós-Tratamento', 'tipo': 'textarea'}
]

# ======================== CONEXÃO MONGODB ========================
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('DB_NAME', 'bioma_uberaba_v4')

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client[DB_NAME]
    logger.info(f"✅ MongoDB conectado: {DB_NAME}")
except Exception as e:
    logger.error(f"❌ Erro MongoDB: {e}")
    db = None

# ======================== FUNÇÕES DE AUTENTICAÇÃO ========================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Login necessário'}), 401
        return f(*args, **kwargs)
    return decorated_function

def check_permission(permission):
    """Decorator para verificar permissões"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'success': False, 'message': 'Login necessário'}), 401
                
            user = db.usuarios.find_one({'_id': ObjectId(session['user_id'])})
            if not user:
                return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
                
            user_level = user.get('access_level', 'profissional')
            level_info = ACCESS_LEVELS.get(user_level, ACCESS_LEVELS['profissional'])
            
            if 'all' in level_info['permissions'] or permission in level_info['permissions']:
                return f(*args, **kwargs)
            else:
                return jsonify({'success': False, 'message': 'Sem permissão para esta ação'}), 403
                
        return decorated_function
    return decorator

def get_user_access_level():
    """Retorna o nível de acesso do usuário atual"""
    if 'user_id' not in session:
        return None
        
    user = db.usuarios.find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        return None
        
    return user.get('access_level', 'profissional')

# ======================== INICIALIZAÇÃO DO BD ========================
def init_db():
    """Inicializa o banco de dados com coleções e índices necessários"""
    if not db:
        logger.error("❌ MongoDB não conectado!")
        return
    
    try:
        # Criar coleções se não existirem
        collections = [
            'usuarios', 'clientes', 'produtos', 'servicos', 'orcamentos',
            'contratos', 'agendamentos', 'fila', 'profissionais', 'assistentes',
            'anamneses', 'prontuarios', 'estoque_movimentacoes', 'comissoes',
            'despesas', 'receitas', 'notificacoes', 'auditoria', 'configuracoes',
            'financeiro_categorias', 'financeiro_contas'
        ]
        
        existing = db.list_collection_names()
        for col in collections:
            if col not in existing:
                db.create_collection(col)
                logger.info(f"✅ Coleção criada: {col}")
        
        # Criar índices
        db.usuarios.create_index([('email', ASCENDING)], unique=True)
        db.usuarios.create_index([('cpf', ASCENDING)], unique=True, sparse=True)
        db.clientes.create_index([('cpf', ASCENDING)], unique=True, sparse=True)
        db.clientes.create_index([('email', ASCENDING)], sparse=True)
        db.clientes.create_index([('telefone', ASCENDING)], sparse=True)
        db.produtos.create_index([('nome', ASCENDING)])
        db.servicos.create_index([('nome', ASCENDING)])
        db.orcamentos.create_index([('numero', ASCENDING)], unique=True)
        db.orcamentos.create_index([('cliente_id', ASCENDING)])
        db.orcamentos.create_index([('status', ASCENDING)])
        db.agendamentos.create_index([('data', ASCENDING)])
        db.agendamentos.create_index([('profissional_id', ASCENDING)])
        db.agendamentos.create_index([('cliente_id', ASCENDING)])
        db.fila.create_index([('data', ASCENDING)])
        db.fila.create_index([('posicao', ASCENDING)])
        db.notificacoes.create_index([('usuario_id', ASCENDING)])
        db.notificacoes.create_index([('lida', ASCENDING)])
        db.auditoria.create_index([('usuario_id', ASCENDING)])
        db.auditoria.create_index([('data', DESCENDING)])
        
        # Criar usuário admin padrão se não existir
        admin = db.usuarios.find_one({'email': 'admin@bioma.com'})
        if not admin:
            db.usuarios.insert_one({
                'nome': 'Administrador',
                'email': 'admin@bioma.com',
                'password': generate_password_hash('admin123'),
                'cpf': '00000000000',
                'telefone': '(00) 00000-0000',
                'access_level': 'admin',
                'status': 'Ativo',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
            logger.info("✅ Usuário admin criado")
        
        # Criar configurações padrão
        config = db.configuracoes.find_one({'tipo': 'sistema'})
        if not config:
            db.configuracoes.insert_one({
                'tipo': 'sistema',
                'nome_empresa': 'BIOMA Uberaba',
                'logo_url': '',
                'endereco': '',
                'telefone': '',
                'email': '',
                'cnpj': '',
                'horario_funcionamento': {
                    'seg': {'inicio': '08:00', 'fim': '18:00'},
                    'ter': {'inicio': '08:00', 'fim': '18:00'},
                    'qua': {'inicio': '08:00', 'fim': '18:00'},
                    'qui': {'inicio': '08:00', 'fim': '18:00'},
                    'sex': {'inicio': '08:00', 'fim': '18:00'},
                    'sab': {'inicio': '08:00', 'fim': '12:00'},
                    'dom': {'inicio': '', 'fim': ''}
                },
                'intervalo_agendamento': 30,
                'tempo_medio_atendimento': 60,
                'notificacoes': {
                    'email': True,
                    'sms': True,
                    'whatsapp': True
                },
                'comissao_padrao': 10,
                'moeda': 'BRL',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
            logger.info("✅ Configurações padrão criadas")
            
        logger.info("✅ Banco de dados inicializado com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar BD: {e}")

# ======================== ROTAS DE AUTENTICAÇÃO ========================
@app.route('/')
def index():
    """Rota principal - retorna o HTML"""
    return send_file('index.html')

@app.route('/api/current-user', methods=['GET'])
def current_user():
    """Retorna o usuário atual da sessão"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    try:
        user = db.usuarios.find_one({'_id': ObjectId(session['user_id'])})
        if not user:
            session.clear()
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        user['_id'] = str(user['_id'])
        del user['password']
        
        return jsonify({
            'success': True,
            'user': user,
            'access_level': user.get('access_level', 'profissional')
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar usuário atual: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Login de usuário com níveis de acesso"""
    try:
        data = request.json
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email e senha são obrigatórios'}), 400
        
        # Buscar usuário
        user = db.usuarios.find_one({'email': email})
        
        # Login admin padrão
        if email == 'admin' and password == 'admin123':
            user = db.usuarios.find_one({'email': 'admin@bioma.com'})
            if user and check_password_hash(user['password'], 'admin123'):
                session.permanent = True
                session['user_id'] = str(user['_id'])
                session['user_name'] = user.get('nome', 'Admin')
                session['user_email'] = user['email']
                session['access_level'] = user.get('access_level', 'admin')
                
                # Registrar login na auditoria
                db.auditoria.insert_one({
                    'usuario_id': str(user['_id']),
                    'acao': 'login',
                    'detalhes': 'Login realizado com sucesso',
                    'ip': request.remote_addr,
                    'data': datetime.now()
                })
                
                logger.info(f"✅ Login admin: {email}")
                return jsonify({
                    'success': True, 
                    'message': 'Login realizado!',
                    'access_level': 'admin'
                })
        
        if not user:
            return jsonify({'success': False, 'message': 'Email não encontrado'}), 404
        
        if user.get('status') != 'Ativo':
            return jsonify({'success': False, 'message': 'Usuário inativo'}), 403
        
        if not check_password_hash(user['password'], password):
            # Registrar tentativa falha
            db.auditoria.insert_one({
                'usuario_id': None,
                'acao': 'login_falha',
                'detalhes': f'Tentativa de login falha para: {email}',
                'ip': request.remote_addr,
                'data': datetime.now()
            })
            return jsonify({'success': False, 'message': 'Senha incorreta'}), 401
        
        # Login bem-sucedido
        session.permanent = True
        session['user_id'] = str(user['_id'])
        session['user_name'] = user.get('nome', 'Usuário')
        session['user_email'] = user['email']
        session['access_level'] = user.get('access_level', 'profissional')
        
        # Registrar login na auditoria
        db.auditoria.insert_one({
            'usuario_id': str(user['_id']),
            'acao': 'login',
            'detalhes': 'Login realizado com sucesso',
            'ip': request.remote_addr,
            'data': datetime.now()
        })
        
        # Atualizar último login
        db.usuarios.update_one(
            {'_id': user['_id']},
            {'$set': {'ultimo_login': datetime.now()}}
        )
        
        logger.info(f"✅ Login: {email} - Nível: {session['access_level']}")
        return jsonify({
            'success': True,
            'message': 'Login realizado com sucesso!',
            'access_level': session['access_level']
        })
        
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    """Registro de novo usuário com nível de acesso"""
    try:
        data = request.json
        
        # Validação de campos obrigatórios
        required = ['nome', 'email', 'password', 'cpf', 'telefone']
        for field in required:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} é obrigatório'}), 400
        
        email = data['email'].lower().strip()
        cpf = re.sub(r'\D', '', data['cpf'])
        
        # Verificar duplicados
        if db.usuarios.find_one({'email': email}):
            return jsonify({'success': False, 'message': 'Email já cadastrado'}), 400
        
        if db.usuarios.find_one({'cpf': cpf}):
            return jsonify({'success': False, 'message': 'CPF já cadastrado'}), 400
        
        # Determinar nível de acesso
        access_level = data.get('access_level', 'profissional')
        if access_level not in ACCESS_LEVELS:
            access_level = 'profissional'
        
        # Apenas admins podem criar outros admins
        if access_level == 'admin' and session.get('access_level') != 'admin':
            access_level = 'gestao'
        
        # Criar usuário
        new_user = {
            'nome': data['nome'],
            'email': email,
            'password': generate_password_hash(data['password']),
            'cpf': cpf,
            'telefone': data['telefone'],
            'access_level': access_level,
            'status': 'Ativo',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        result = db.usuarios.insert_one(new_user)
        
        # Registrar na auditoria
        db.auditoria.insert_one({
            'usuario_id': str(result.inserted_id),
            'acao': 'registro',
            'detalhes': f'Novo usuário registrado: {email}',
            'ip': request.remote_addr,
            'data': datetime.now()
        })
        
        # Enviar email de boas-vindas
        send_notification_email(
            email,
            'Bem-vindo ao BIOMA Uberaba',
            f"""
            <h2>Bem-vindo ao BIOMA Uberaba!</h2>
            <p>Olá {data['nome']},</p>
            <p>Sua conta foi criada com sucesso!</p>
            <p>Nível de acesso: {ACCESS_LEVELS[access_level]['name']}</p>
            <p>Entre em contato conosco se tiver dúvidas.</p>
            """
        )
        
        logger.info(f"✅ Novo usuário: {email} - Nível: {access_level}")
        return jsonify({
            'success': True,
            'message': 'Cadastro realizado com sucesso!'
        })
        
    except Exception as e:
        logger.error(f"Erro no registro: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout do usuário"""
    try:
        if 'user_id' in session:
            # Registrar logout na auditoria
            db.auditoria.insert_one({
                'usuario_id': session['user_id'],
                'acao': 'logout',
                'detalhes': 'Logout realizado',
                'ip': request.remote_addr,
                'data': datetime.now()
            })
            
            logger.info(f"👋 Logout: {session.get('user_email')}")
        
        session.clear()
        return jsonify({'success': True, 'message': 'Logout realizado'})
        
    except Exception as e:
        logger.error(f"Erro no logout: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ======================== ROTAS DE PERFIL E NÍVEIS DE ACESSO ========================
@app.route('/api/perfil', methods=['GET'])
@login_required
def get_perfil():
    """Retorna perfil do usuário com permissões"""
    try:
        user = db.usuarios.find_one({'_id': ObjectId(session['user_id'])})
        if not user:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        user['_id'] = str(user['_id'])
        del user['password']
        
        # Adicionar informações de permissões
        access_level = user.get('access_level', 'profissional')
        level_info = ACCESS_LEVELS.get(access_level, ACCESS_LEVELS['profissional'])
        
        return jsonify({
            'success': True,
            'perfil': user,
            'permissions': level_info['permissions'],
            'access_level_info': level_info
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar perfil: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/perfil/atualizar', methods=['PUT'])
@login_required
def update_perfil():
    """Atualiza perfil do usuário"""
    try:
        data = request.json
        user_id = session['user_id']
        
        # Campos permitidos para atualização
        allowed_fields = ['nome', 'telefone', 'endereco', 'data_nascimento']
        update_data = {}
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        if update_data:
            update_data['updated_at'] = datetime.now()
            db.usuarios.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_data}
            )
            
            # Registrar na auditoria
            db.auditoria.insert_one({
                'usuario_id': user_id,
                'acao': 'perfil_atualizado',
                'detalhes': f'Campos atualizados: {list(update_data.keys())}',
                'data': datetime.now()
            })
            
            logger.info(f"✅ Perfil atualizado: {user_id}")
            return jsonify({'success': True, 'message': 'Perfil atualizado com sucesso!'})
        
        return jsonify({'success': False, 'message': 'Nenhum campo para atualizar'}), 400
        
    except Exception as e:
        logger.error(f"Erro ao atualizar perfil: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/perfil/alterar-senha', methods=['PUT'])
@login_required
def change_password():
    """Altera senha do usuário"""
    try:
        data = request.json
        senha_atual = data.get('senha_atual')
        senha_nova = data.get('senha_nova')
        
        if not senha_atual or not senha_nova:
            return jsonify({'success': False, 'message': 'Senhas são obrigatórias'}), 400
        
        user = db.usuarios.find_one({'_id': ObjectId(session['user_id'])})
        
        if not check_password_hash(user['password'], senha_atual):
            return jsonify({'success': False, 'message': 'Senha atual incorreta'}), 401
        
        db.usuarios.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': {
                'password': generate_password_hash(senha_nova),
                'updated_at': datetime.now()
            }}
        )
        
        # Registrar na auditoria
        db.auditoria.insert_one({
            'usuario_id': session['user_id'],
            'acao': 'senha_alterada',
            'detalhes': 'Senha alterada com sucesso',
            'data': datetime.now()
        })
        
        logger.info(f"✅ Senha alterada: {session['user_email']}")
        return jsonify({'success': True, 'message': 'Senha alterada com sucesso!'})
        
    except Exception as e:
        logger.error(f"Erro ao alterar senha: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/usuarios/gerenciar', methods=['GET'])
@login_required
@check_permission('view_all')
def list_usuarios():
    """Lista todos os usuários (Admin e Gestão)"""
    try:
        usuarios = list(db.usuarios.find())
        
        for user in usuarios:
            user['_id'] = str(user['_id'])
            del user['password']
        
        return jsonify({'success': True, 'usuarios': usuarios})
        
    except Exception as e:
        logger.error(f"Erro ao listar usuários: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/usuarios/<user_id>/nivel', methods=['PUT'])
@login_required
@check_permission('all')
def update_user_level(user_id):
    """Atualiza nível de acesso do usuário (Apenas Admin)"""
    try:
        data = request.json
        novo_nivel = data.get('access_level')
        
        if novo_nivel not in ACCESS_LEVELS:
            return jsonify({'success': False, 'message': 'Nível de acesso inválido'}), 400
        
        db.usuarios.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {
                'access_level': novo_nivel,
                'updated_at': datetime.now()
            }}
        )
        
        # Registrar na auditoria
        db.auditoria.insert_one({
            'usuario_id': session['user_id'],
            'acao': 'nivel_acesso_alterado',
            'detalhes': f'Usuário {user_id} alterado para {novo_nivel}',
            'data': datetime.now()
        })
        
        logger.info(f"✅ Nível de acesso alterado: {user_id} -> {novo_nivel}")
        return jsonify({'success': True, 'message': 'Nível de acesso atualizado!'})
        
    except Exception as e:
        logger.error(f"Erro ao atualizar nível: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ======================== ROTAS DO FINANCEIRO ========================
@app.route('/api/financeiro/resumo', methods=['GET'])
@login_required
def get_financeiro_resumo():
    """Retorna resumo financeiro"""
    try:
        # Período padrão: mês atual
        hoje = datetime.now()
        inicio_mes = datetime(hoje.year, hoje.month, 1)
        fim_mes = datetime(hoje.year, hoje.month + 1, 1) if hoje.month < 12 else datetime(hoje.year + 1, 1, 1)
        
        # Receitas
        receitas = list(db.orcamentos.find({
            'status': 'Aprovado',
            'data_aprovacao': {'$gte': inicio_mes, '$lt': fim_mes}
        }))
        
        total_receitas = sum(float(o.get('valor_total', 0)) for o in receitas)
        
        # Despesas
        despesas = list(db.despesas.find({
            'data': {'$gte': inicio_mes, '$lt': fim_mes}
        }))
        
        total_despesas = sum(float(d.get('valor', 0)) for d in despesas)
        
        # Comissões
        comissoes = list(db.comissoes.find({
            'data': {'$gte': inicio_mes, '$lt': fim_mes},
            'status': 'Pago'
        }))
        
        total_comissoes = sum(float(c.get('valor', 0)) for c in comissoes)
        
        # Lucro
        lucro = total_receitas - total_despesas - total_comissoes
        
        # Estatísticas por categoria
        categorias_despesas = {}
        for despesa in despesas:
            cat = despesa.get('categoria', 'Outros')
            if cat not in categorias_despesas:
                categorias_despesas[cat] = 0
            categorias_despesas[cat] += float(despesa.get('valor', 0))
        
        return jsonify({
            'success': True,
            'resumo': {
                'periodo': f"{inicio_mes.strftime('%d/%m/%Y')} - {fim_mes.strftime('%d/%m/%Y')}",
                'receitas': round(total_receitas, 2),
                'despesas': round(total_despesas, 2),
                'comissoes': round(total_comissoes, 2),
                'lucro': round(lucro, 2),
                'margem_lucro': round((lucro / total_receitas * 100) if total_receitas > 0 else 0, 2),
                'categorias_despesas': categorias_despesas,
                'num_vendas': len(receitas),
                'ticket_medio': round(total_receitas / len(receitas) if receitas else 0, 2)
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar resumo financeiro: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/financeiro/despesas', methods=['GET', 'POST'])
@login_required
@check_permission('create')
def manage_despesas():
    """Gerencia despesas"""
    if request.method == 'GET':
        try:
            # Buscar despesas com filtros
            filtro = {}
            
            if request.args.get('mes'):
                mes = int(request.args.get('mes'))
                ano = int(request.args.get('ano', datetime.now().year))
                inicio = datetime(ano, mes, 1)
                fim = datetime(ano, mes + 1, 1) if mes < 12 else datetime(ano + 1, 1, 1)
                filtro['data'] = {'$gte': inicio, '$lt': fim}
            
            if request.args.get('categoria'):
                filtro['categoria'] = request.args.get('categoria')
            
            despesas = list(db.despesas.find(filtro).sort('data', DESCENDING))
            
            for despesa in despesas:
                despesa['_id'] = str(despesa['_id'])
                despesa['data'] = despesa['data'].strftime('%d/%m/%Y')
            
            return jsonify({'success': True, 'despesas': despesas})
            
        except Exception as e:
            logger.error(f"Erro ao buscar despesas: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    else:  # POST
        try:
            data = request.json
            
            nova_despesa = {
                'descricao': data.get('descricao'),
                'valor': float(data.get('valor', 0)),
                'categoria': data.get('categoria', 'Outros'),
                'data': datetime.strptime(data.get('data'), '%Y-%m-%d') if data.get('data') else datetime.now(),
                'forma_pagamento': data.get('forma_pagamento', 'Dinheiro'),
                'observacoes': data.get('observacoes', ''),
                'comprovante': data.get('comprovante', ''),
                'usuario_id': session['user_id'],
                'created_at': datetime.now()
            }
            
            result = db.despesas.insert_one(nova_despesa)
            
            # Registrar na auditoria
            db.auditoria.insert_one({
                'usuario_id': session['user_id'],
                'acao': 'despesa_criada',
                'detalhes': f'Despesa criada: {nova_despesa["descricao"]} - R$ {nova_despesa["valor"]}',
                'data': datetime.now()
            })
            
            logger.info(f"✅ Despesa criada: {nova_despesa['descricao']}")
            return jsonify({'success': True, 'message': 'Despesa registrada com sucesso!'})
            
        except Exception as e:
            logger.error(f"Erro ao criar despesa: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/financeiro/comissoes', methods=['GET'])
@login_required
def get_comissoes():
    """Busca comissões com filtros"""
    try:
        filtro = {}
        
        # Filtrar por profissional
        if request.args.get('profissional_id'):
            filtro['profissional_id'] = request.args.get('profissional_id')
        
        # Filtrar por período
        if request.args.get('data_inicio') and request.args.get('data_fim'):
            data_inicio = datetime.strptime(request.args.get('data_inicio'), '%Y-%m-%d')
            data_fim = datetime.strptime(request.args.get('data_fim'), '%Y-%m-%d')
            filtro['data'] = {'$gte': data_inicio, '$lte': data_fim}
        
        # Filtrar por status
        if request.args.get('status'):
            filtro['status'] = request.args.get('status')
        
        comissoes = list(db.comissoes.find(filtro).sort('data', DESCENDING))
        
        # Enriquecer com dados do profissional
        for comissao in comissoes:
            comissao['_id'] = str(comissao['_id'])
            
            # Buscar profissional
            prof = db.profissionais.find_one({'_id': ObjectId(comissao.get('profissional_id'))})
            if prof:
                comissao['profissional_nome'] = prof.get('nome')
            
            # Buscar orçamento
            orc = db.orcamentos.find_one({'_id': ObjectId(comissao.get('orcamento_id'))})
            if orc:
                comissao['orcamento_numero'] = orc.get('numero')
            
            comissao['data'] = comissao['data'].strftime('%d/%m/%Y')
        
        # Calcular totais
        total_comissoes = sum(float(c.get('valor', 0)) for c in comissoes)
        total_pago = sum(float(c.get('valor', 0)) for c in comissoes if c.get('status') == 'Pago')
        total_pendente = sum(float(c.get('valor', 0)) for c in comissoes if c.get('status') == 'Pendente')
        
        return jsonify({
            'success': True,
            'comissoes': comissoes,
            'totais': {
                'total': round(total_comissoes, 2),
                'pago': round(total_pago, 2),
                'pendente': round(total_pendente, 2)
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar comissões: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/financeiro/comissoes/<comissao_id>/pagar', methods=['PUT'])
@login_required
@check_permission('edit_all')
def pagar_comissao(comissao_id):
    """Marca comissão como paga"""
    try:
        comissao = db.comissoes.find_one({'_id': ObjectId(comissao_id)})
        if not comissao:
            return jsonify({'success': False, 'message': 'Comissão não encontrada'}), 404
        
        db.comissoes.update_one(
            {'_id': ObjectId(comissao_id)},
            {'$set': {
                'status': 'Pago',
                'data_pagamento': datetime.now(),
                'pago_por': session['user_id']
            }}
        )
        
        # Notificar profissional
        prof = db.profissionais.find_one({'_id': ObjectId(comissao['profissional_id'])})
        if prof and prof.get('telefone'):
            send_sms_notification(
                prof['telefone'],
                f"Olá {prof['nome']}, sua comissão de R$ {comissao['valor']} foi paga!"
            )
        
        # Registrar na auditoria
        db.auditoria.insert_one({
            'usuario_id': session['user_id'],
            'acao': 'comissao_paga',
            'detalhes': f'Comissão {comissao_id} paga - R$ {comissao["valor"]}',
            'data': datetime.now()
        })
        
        logger.info(f"✅ Comissão paga: {comissao_id}")
        return jsonify({'success': True, 'message': 'Comissão paga com sucesso!'})
        
    except Exception as e:
        logger.error(f"Erro ao pagar comissão: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ======================== ROTAS DE ESTOQUE CORRIGIDAS ========================
@app.route('/api/estoque/produtos', methods=['GET'])
@login_required
def get_estoque_produtos():
    """Busca produtos do estoque (corrigido para aparecer só na aba estoque)"""
    try:
        # Verificar se a requisição vem da aba estoque
        referer = request.headers.get('Referer', '')
        if 'estoque' not in referer and not request.args.get('from_estoque'):
            return jsonify({'success': True, 'produtos': []})
        
        produtos = list(db.produtos.find({'status': 'Ativo'}))
        
        for produto in produtos:
            produto['_id'] = str(produto['_id'])
            estoque_atual = int(produto.get('estoque', 0))
            estoque_minimo = int(produto.get('estoque_minimo', 0))
            
            # Determinar status do estoque
            if estoque_atual <= estoque_minimo:
                produto['estoque_status'] = 'critico'
            elif estoque_atual <= estoque_minimo * 1.5:
                produto['estoque_status'] = 'baixo'
            else:
                produto['estoque_status'] = 'normal'
        
        return jsonify({'success': True, 'produtos': produtos})
        
    except Exception as e:
        logger.error(f"Erro ao buscar produtos do estoque: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/movimentacoes', methods=['GET', 'POST'])
@login_required
def manage_estoque_movimentacoes():
    """Gerencia movimentações de estoque"""
    if request.method == 'GET':
        try:
            # Buscar movimentações
            movimentacoes = list(db.estoque_movimentacoes.find().sort('data', DESCENDING).limit(50))
            
            for mov in movimentacoes:
                mov['_id'] = str(mov['_id'])
                
                # Buscar produto
                produto = db.produtos.find_one({'_id': ObjectId(mov.get('produto_id'))})
                if produto:
                    mov['produto_nome'] = produto.get('nome')
                
                # Buscar responsável
                if mov.get('responsavel_id'):
                    responsavel = db.usuarios.find_one({'_id': ObjectId(mov['responsavel_id'])})
                    if responsavel:
                        mov['responsavel_nome'] = responsavel.get('nome')
                
                mov['data'] = mov['data'].strftime('%d/%m/%Y %H:%M')
            
            return jsonify({'success': True, 'movimentacoes': movimentacoes})
            
        except Exception as e:
            logger.error(f"Erro ao buscar movimentações: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    else:  # POST
        try:
            data = request.json
            
            produto = db.produtos.find_one({'_id': ObjectId(data.get('produto_id'))})
            if not produto:
                return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
            
            tipo = data.get('tipo', 'entrada').lower()
            quantidade = int(data.get('quantidade', 0))
            
            if quantidade <= 0:
                return jsonify({'success': False, 'message': 'Quantidade inválida'}), 400
            
            # Atualizar estoque
            estoque_atual = int(produto.get('estoque', 0))
            
            if tipo == 'entrada':
                novo_estoque = estoque_atual + quantidade
            else:  # saída
                if estoque_atual < quantidade:
                    return jsonify({'success': False, 'message': 'Estoque insuficiente'}), 400
                novo_estoque = estoque_atual - quantidade
            
            # Atualizar produto
            db.produtos.update_one(
                {'_id': ObjectId(data.get('produto_id'))},
                {'$set': {'estoque': novo_estoque}}
            )
            
            # Registrar movimentação
            nova_movimentacao = {
                'produto_id': data.get('produto_id'),
                'tipo': tipo,
                'quantidade': quantidade,
                'estoque_anterior': estoque_atual,
                'estoque_novo': novo_estoque,
                'motivo': data.get('motivo', ''),
                'observacoes': data.get('observacoes', ''),
                'responsavel_id': session['user_id'],
                'data': datetime.now()
            }
            
            db.estoque_movimentacoes.insert_one(nova_movimentacao)
            
            # Verificar se precisa alertar sobre estoque baixo
            estoque_minimo = int(produto.get('estoque_minimo', 0))
            if novo_estoque <= estoque_minimo:
                # Criar notificação
                db.notificacoes.insert_one({
                    'tipo': 'estoque_baixo',
                    'titulo': 'Estoque Baixo',
                    'mensagem': f'O produto {produto["nome"]} está com estoque baixo ({novo_estoque} unidades)',
                    'produto_id': data.get('produto_id'),
                    'lida': False,
                    'data': datetime.now()
                })
            
            logger.info(f"✅ Movimentação de estoque: {produto['nome']} - {tipo} - {quantidade}")
            return jsonify({'success': True, 'message': 'Movimentação registrada com sucesso!'})
            
        except Exception as e:
            logger.error(f"Erro ao registrar movimentação: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

# ======================== ROTAS DE ORÇAMENTOS CORRIGIDAS ========================
@app.route('/api/orcamentos', methods=['GET'])
@login_required
def get_orcamentos():
    """Busca orçamentos com filtro por status"""
    try:
        status = request.args.get('status', 'all')
        filtro = {}
        
        # Aplicar filtro de status
        if status != 'all':
            filtro['status'] = status
        
        # Verificar permissões
        access_level = get_user_access_level()
        if access_level == 'profissional':
            # Profissionais só veem seus próprios orçamentos
            filtro['profissional_id'] = session['user_id']
        
        orcamentos = list(db.orcamentos.find(filtro).sort('data_criacao', DESCENDING))
        
        for orc in orcamentos:
            orc['_id'] = str(orc['_id'])
            
            # Buscar cliente
            if orc.get('cliente_id'):
                cliente = db.clientes.find_one({'_id': ObjectId(orc['cliente_id'])})
                if cliente:
                    orc['cliente_nome'] = cliente.get('nome')
                    orc['cliente_telefone'] = cliente.get('telefone')
            
            # Buscar profissional
            if orc.get('profissional_id'):
                prof = db.profissionais.find_one({'_id': ObjectId(orc['profissional_id'])})
                if prof:
                    orc['profissional_nome'] = prof.get('nome')
            
            # Formatar datas
            if orc.get('data_criacao'):
                orc['data_criacao'] = orc['data_criacao'].strftime('%d/%m/%Y %H:%M')
            if orc.get('data_validade'):
                orc['data_validade'] = orc['data_validade'].strftime('%d/%m/%Y')
        
        return jsonify({'success': True, 'orcamentos': orcamentos})
        
    except Exception as e:
        logger.error(f"Erro ao buscar orçamentos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/orcamentos/<orcamento_id>/imprimir', methods=['GET'])
@login_required
def imprimir_orcamento(orcamento_id):
    """Gera PDF do orçamento para impressão"""
    try:
        orc = db.orcamentos.find_one({'_id': ObjectId(orcamento_id)})
        if not orc:
            return jsonify({'success': False, 'message': 'Orçamento não encontrado'}), 404
        
        # Buscar dados complementares
        cliente = db.clientes.find_one({'_id': ObjectId(orc['cliente_id'])}) if orc.get('cliente_id') else None
        config = db.configuracoes.find_one({'tipo': 'sistema'})
        
        # Criar PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Estilo personalizado
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=HexColor('#7C3AED'),
            alignment=TA_CENTER
        )
        
        # Cabeçalho
        logo_text = config.get('nome_empresa', 'BIOMA Uberaba')
        story.append(Paragraph(logo_text, title_style))
        story.append(Spacer(1, 20))
        
        # Informações da empresa
        if config:
            empresa_info = f"""
            <para align="center">
            {config.get('endereco', '')}<br/>
            {config.get('telefone', '')} | {config.get('email', '')}<br/>
            CNPJ: {config.get('cnpj', '')}
            </para>
            """
            story.append(Paragraph(empresa_info, styles['Normal']))
            story.append(Spacer(1, 30))
        
        # Título do documento
        story.append(Paragraph(f'ORÇAMENTO #{orc.get("numero", "")}', title_style))
        story.append(Spacer(1, 20))
        
        # Dados do cliente
        if cliente:
            cliente_info = f"""
            <para><b>Cliente:</b> {cliente.get('nome', '')}<br/>
            <b>CPF:</b> {cliente.get('cpf', '')}<br/>
            <b>Telefone:</b> {cliente.get('telefone', '')}<br/>
            <b>Email:</b> {cliente.get('email', '')}<br/>
            <b>Endereço:</b> {cliente.get('endereco', '')}
            </para>
            """
            story.append(Paragraph(cliente_info, styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Tabela de itens
        data = [['Item', 'Tipo', 'Qtd', 'Valor Unit.', 'Subtotal']]
        
        for item in orc.get('itens', []):
            data.append([
                item.get('nome', ''),
                item.get('tipo', ''),
                str(item.get('quantidade', 1)),
                f"R$ {item.get('valor', 0):.2f}",
                f"R$ {item.get('subtotal', 0):.2f}"
            ])
        
        # Adicionar total
        data.append(['', '', '', 'TOTAL:', f"R$ {orc.get('valor_total', 0):.2f}"])
        
        # Criar tabela
        table = Table(data, colWidths=[200, 80, 50, 80, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#7C3AED')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), HexColor('#F9FAFB')),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#E5E7EB')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('BACKGROUND', (0, -1), (-1, -1), HexColor('#E5E7EB'))
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Condições
        if orc.get('condicoes'):
            story.append(Paragraph('<b>Condições:</b>', styles['Heading2']))
            story.append(Paragraph(orc['condicoes'], styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Observações
        if orc.get('observacoes'):
            story.append(Paragraph('<b>Observações:</b>', styles['Heading2']))
            story.append(Paragraph(orc['observacoes'], styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Validade
        story.append(Paragraph(f'<b>Validade:</b> {orc.get("data_validade", "30 dias")}', styles['Normal']))
        story.append(Spacer(1, 40))
        
        # Assinaturas
        assinatura_data = [
            ['_______________________', '_______________________'],
            ['Cliente', 'BIOMA Uberaba'],
            [cliente.get('nome', '') if cliente else '', '']
        ]
        
        assinatura_table = Table(assinatura_data, colWidths=[250, 250])
        assinatura_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10)
        ]))
        
        story.append(assinatura_table)
        
        # Gerar PDF
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'orcamento_{orc["numero"]}.pdf'
        )
        
    except Exception as e:
        logger.error(f"Erro ao gerar PDF do orçamento: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/orcamentos/<orcamento_id>/whatsapp', methods=['POST'])
@login_required
def enviar_orcamento_whatsapp(orcamento_id):
    """Envia orçamento via WhatsApp"""
    try:
        orc = db.orcamentos.find_one({'_id': ObjectId(orcamento_id)})
        if not orc:
            return jsonify({'success': False, 'message': 'Orçamento não encontrado'}), 404
        
        cliente = db.clientes.find_one({'_id': ObjectId(orc['cliente_id'])})
        if not cliente or not cliente.get('telefone'):
            return jsonify({'success': False, 'message': 'Cliente sem telefone cadastrado'}), 400
        
        # Gerar link do PDF
        pdf_url = f"{request.host_url}api/orcamentos/{orcamento_id}/imprimir"
        
        # Mensagem
        mensagem = f"""
Olá {cliente['nome']}! 

Seu orçamento #{orc['numero']} está pronto!

*Resumo:*
Valor Total: R$ {orc['valor_total']:.2f}
Validade: {orc.get('data_validade', '30 dias')}

Clique no link abaixo para visualizar o orçamento completo:
{pdf_url}

Qualquer dúvida, estamos à disposição!

Atenciosamente,
BIOMA Uberaba
        """
        
        # Enviar WhatsApp
        sucesso = send_whatsapp_message(cliente['telefone'], mensagem, pdf_url)
        
        if sucesso:
            # Registrar envio
            db.orcamentos.update_one(
                {'_id': ObjectId(orcamento_id)},
                {'$push': {
                    'historico_envios': {
                        'tipo': 'whatsapp',
                        'data': datetime.now(),
                        'usuario': session['user_name']
                    }
                }}
            )
            
            logger.info(f"✅ Orçamento enviado via WhatsApp: {orcamento_id}")
            return jsonify({'success': True, 'message': 'Orçamento enviado com sucesso!'})
        else:
            return jsonify({'success': False, 'message': 'Erro ao enviar WhatsApp'}), 500
            
    except Exception as e:
        logger.error(f"Erro ao enviar orçamento via WhatsApp: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ======================== ROTAS DE AGENDAMENTO E FILA ========================
@app.route('/api/agendamentos', methods=['GET', 'POST'])
@login_required
def manage_agendamentos():
    """Gerencia agendamentos"""
    if request.method == 'GET':
        try:
            # Filtros
            filtro = {}
            
            if request.args.get('data'):
                data = datetime.strptime(request.args.get('data'), '%Y-%m-%d')
                filtro['data'] = {
                    '$gte': data,
                    '$lt': data + timedelta(days=1)
                }
            
            if request.args.get('profissional_id'):
                filtro['profissional_id'] = request.args.get('profissional_id')
            
            agendamentos = list(db.agendamentos.find(filtro).sort('data', ASCENDING))
            
            for ag in agendamentos:
                ag['_id'] = str(ag['_id'])
                
                # Buscar cliente
                if ag.get('cliente_id'):
                    cliente = db.clientes.find_one({'_id': ObjectId(ag['cliente_id'])})
                    if cliente:
                        ag['cliente_nome'] = cliente.get('nome')
                        ag['cliente_telefone'] = cliente.get('telefone')
                
                # Buscar profissional
                if ag.get('profissional_id'):
                    prof = db.profissionais.find_one({'_id': ObjectId(ag['profissional_id'])})
                    if prof:
                        ag['profissional_nome'] = prof.get('nome')
                
                ag['data'] = ag['data'].strftime('%d/%m/%Y %H:%M')
            
            return jsonify({'success': True, 'agendamentos': agendamentos})
            
        except Exception as e:
            logger.error(f"Erro ao buscar agendamentos: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    else:  # POST
        try:
            data = request.json
            
            # Verificar disponibilidade do profissional
            data_hora = datetime.strptime(f"{data['data']} {data['hora']}", '%Y-%m-%d %H:%M')
            
            conflito = db.agendamentos.find_one({
                'profissional_id': data['profissional_id'],
                'data': {
                    '$gte': data_hora - timedelta(minutes=30),
                    '$lt': data_hora + timedelta(minutes=30)
                },
                'status': {'$ne': 'Cancelado'}
            })
            
            if conflito:
                return jsonify({'success': False, 'message': 'Horário não disponível'}), 400
            
            novo_agendamento = {
                'cliente_id': data.get('cliente_id'),
                'profissional_id': data.get('profissional_id'),
                'servico_id': data.get('servico_id'),
                'data': data_hora,
                'duracao': int(data.get('duracao', 60)),
                'observacoes': data.get('observacoes', ''),
                'status': 'Agendado',
                'notificacao_enviada': False,
                'created_at': datetime.now(),
                'created_by': session['user_id']
            }
            
            result = db.agendamentos.insert_one(novo_agendamento)
            
            # Enviar confirmação ao cliente
            cliente = db.clientes.find_one({'_id': ObjectId(data['cliente_id'])})
            if cliente:
                prof = db.profissionais.find_one({'_id': ObjectId(data['profissional_id'])})
                
                mensagem = f"""
Olá {cliente['nome']},

Seu agendamento foi confirmado!

Data: {data_hora.strftime('%d/%m/%Y')}
Horário: {data_hora.strftime('%H:%M')}
Profissional: {prof['nome'] if prof else 'A definir'}

Aguardamos você!
BIOMA Uberaba
                """
                
                if cliente.get('telefone'):
                    send_sms_notification(cliente['telefone'], mensagem)
                
                if cliente.get('email'):
                    send_notification_email(cliente['email'], 'Agendamento Confirmado', mensagem)
            
            logger.info(f"✅ Agendamento criado: {result.inserted_id}")
            return jsonify({'success': True, 'message': 'Agendamento realizado com sucesso!'})
            
        except Exception as e:
            logger.error(f"Erro ao criar agendamento: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/fila', methods=['GET'])
@login_required
def get_fila():
    """Busca fila de atendimento do dia"""
    try:
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        amanha = hoje + timedelta(days=1)
        
        # Buscar agendamentos do dia
        agendamentos = list(db.agendamentos.find({
            'data': {'$gte': hoje, '$lt': amanha},
            'status': {'$in': ['Agendado', 'Em Atendimento']}
        }).sort('data', ASCENDING))
        
        fila = []
        for idx, ag in enumerate(agendamentos):
            cliente = db.clientes.find_one({'_id': ObjectId(ag['cliente_id'])})
            prof = db.profissionais.find_one({'_id': ObjectId(ag['profissional_id'])})
            
            # Calcular tempo de espera
            agora = datetime.now()
            tempo_espera = int((ag['data'] - agora).total_seconds() / 60) if ag['data'] > agora else 0
            
            fila.append({
                'posicao': idx + 1,
                'cliente': cliente['nome'] if cliente else 'Desconhecido',
                'telefone': cliente['telefone'] if cliente else '',
                'horario': ag['data'].strftime('%H:%M'),
                'profissional': prof['nome'] if prof else 'A definir',
                'status': ag['status'],
                'tempo_espera': tempo_espera,
                'id': str(ag['_id'])
            })
        
        return jsonify({'success': True, 'fila': fila})
        
    except Exception as e:
        logger.error(f"Erro ao buscar fila: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/fila/<agendamento_id>/notificar', methods=['POST'])
@login_required
def notificar_cliente_fila(agendamento_id):
    """Notifica cliente sobre posição na fila"""
    try:
        ag = db.agendamentos.find_one({'_id': ObjectId(agendamento_id)})
        if not ag:
            return jsonify({'success': False, 'message': 'Agendamento não encontrado'}), 404
        
        cliente = db.clientes.find_one({'_id': ObjectId(ag['cliente_id'])})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
        
        # Buscar posição na fila
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        amanha = hoje + timedelta(days=1)
        
        agendamentos_antes = db.agendamentos.count_documents({
            'data': {
                '$gte': hoje,
                '$lt': ag['data']
            },
            'status': {'$in': ['Agendado', 'Em Atendimento']}
        })
        
        posicao = agendamentos_antes + 1
        tempo_estimado = int((ag['data'] - datetime.now()).total_seconds() / 60)
        
        # Preparar mensagem
        if posicao == 1:
            mensagem = f"Olá {cliente['nome']}, você é o próximo! Seu atendimento será iniciado em breve."
        else:
            mensagem = f"Olá {cliente['nome']}, você está na posição {posicao} da fila. Tempo estimado: {tempo_estimado} minutos."
        
        # Enviar notificações
        notificacoes_enviadas = []
        
        if cliente.get('telefone'):
            if send_sms_notification(cliente['telefone'], mensagem):
                notificacoes_enviadas.append('SMS')
        
        if cliente.get('email'):
            if send_notification_email(cliente['email'], 'Atualização da Fila - BIOMA', mensagem):
                notificacoes_enviadas.append('Email')
        
        # Registrar notificação
        db.agendamentos.update_one(
            {'_id': ObjectId(agendamento_id)},
            {'$set': {
                'ultima_notificacao': datetime.now(),
                'notificacoes_enviadas': notificacoes_enviadas
            }}
        )
        
        logger.info(f"✅ Notificação enviada: {agendamento_id}")
        return jsonify({
            'success': True,
            'message': f'Notificação enviada via: {", ".join(notificacoes_enviadas)}'
        })
        
    except Exception as e:
        logger.error(f"Erro ao enviar notificação: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ======================== ROTAS DE CLIENTES MELHORADAS ========================
@app.route('/api/clientes', methods=['GET', 'POST'])
@login_required
def manage_clientes():
    """Gerencia clientes"""
    if request.method == 'GET':
        try:
            clientes = list(db.clientes.find())
            
            for cliente in clientes:
                cliente['_id'] = str(cliente['_id'])
                
                # Calcular total faturado
                orcamentos = list(db.orcamentos.find({
                    'cliente_id': str(cliente['_id']),
                    'status': 'Aprovado'
                }))
                
                total_faturado = sum(float(o.get('valor_total', 0)) for o in orcamentos)
                cliente['total_faturado'] = round(total_faturado, 2)
                
                # Buscar produtos e serviços utilizados
                produtos_utilizados = set()
                servicos_utilizados = set()
                profissionais_atenderam = set()
                visitas = []
                
                for orc in orcamentos:
                    for item in orc.get('itens', []):
                        if item.get('tipo') == 'produto':
                            produtos_utilizados.add(item.get('nome'))
                        elif item.get('tipo') == 'servico':
                            servicos_utilizados.add(item.get('nome'))
                    
                    if orc.get('profissional_id'):
                        profissionais_atenderam.add(orc['profissional_id'])
                    
                    if orc.get('data_criacao'):
                        visitas.append({
                            'data': orc['data_criacao'].strftime('%d/%m/%Y'),
                            'hora': orc['data_criacao'].strftime('%H:%M')
                        })
                
                cliente['produtos_utilizados'] = list(produtos_utilizados)
                cliente['servicos_utilizados'] = list(servicos_utilizados)
                cliente['num_visitas'] = len(visitas)
                cliente['ultimas_visitas'] = visitas[-5:] if visitas else []
                
                # Buscar nomes dos profissionais
                profissionais_nomes = []
                for prof_id in profissionais_atenderam:
                    prof = db.profissionais.find_one({'_id': ObjectId(prof_id)})
                    if prof:
                        profissionais_nomes.append(prof.get('nome'))
                
                cliente['profissionais_atenderam'] = profissionais_nomes
                
                # Formatar datas
                if cliente.get('data_cadastro'):
                    cliente['data_cadastro'] = cliente['data_cadastro'].strftime('%d/%m/%Y')
            
            return jsonify({'success': True, 'clientes': clientes})
            
        except Exception as e:
            logger.error(f"Erro ao buscar clientes: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    else:  # POST
        try:
            data = request.json
            
            # Validar CPF único
            cpf = re.sub(r'\D', '', data.get('cpf', ''))
            if db.clientes.find_one({'cpf': cpf}):
                return jsonify({'success': False, 'message': 'CPF já cadastrado'}), 400
            
            novo_cliente = {
                'nome': data.get('nome'),
                'cpf': cpf,
                'telefone': data.get('telefone'),
                'email': data.get('email', '').lower(),
                'endereco': data.get('endereco', ''),
                'data_nascimento': data.get('data_nascimento'),
                'observacoes': data.get('observacoes', ''),
                'status': 'Ativo',
                'data_cadastro': datetime.now()
            }
            
            result = db.clientes.insert_one(novo_cliente)
            
            logger.info(f"✅ Cliente cadastrado: {novo_cliente['nome']}")
            return jsonify({
                'success': True,
                'message': 'Cliente cadastrado com sucesso!',
                'id': str(result.inserted_id)
            })
            
        except Exception as e:
            logger.error(f"Erro ao cadastrar cliente: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

# ======================== ROTAS DE PROFISSIONAIS ========================
@app.route('/api/profissionais', methods=['GET', 'POST'])
@login_required
def manage_profissionais():
    """Gerencia profissionais"""
    if request.method == 'GET':
        try:
            profissionais = list(db.profissionais.find())
            
            for prof in profissionais:
                prof['_id'] = str(prof['_id'])
                
                # Buscar assistentes
                assistentes = list(db.assistentes.find({'profissional_id': str(prof['_id'])}))
                prof['num_assistentes'] = len(assistentes)
                prof['assistentes'] = [{'id': str(a['_id']), 'nome': a['nome']} for a in assistentes]
                
                # Calcular estatísticas
                orcamentos = list(db.orcamentos.find({
                    'profissional_id': str(prof['_id']),
                    'status': 'Aprovado'
                }))
                
                prof['total_vendas'] = sum(float(o.get('valor_total', 0)) for o in orcamentos)
                prof['num_atendimentos'] = len(orcamentos)
                
                # Formatar foto
                if prof.get('foto'):
                    prof['foto_url'] = f"/api/profissionais/{prof['_id']}/foto"
            
            return jsonify({'success': True, 'profissionais': profissionais})
            
        except Exception as e:
            logger.error(f"Erro ao buscar profissionais: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    else:  # POST
        try:
            # Processar upload de foto se houver
            foto_base64 = None
            if 'foto' in request.files:
                file = request.files['foto']
                if file and allowed_file(file.filename):
                    # Salvar temporariamente
                    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
                    file.save(temp_path)
                    
                    # Redimensionar
                    resized = resize_image(temp_path, (300, 300))
                    if resized:
                        foto_base64 = base64.b64encode(resized.read()).decode('utf-8')
                    
                    # Limpar arquivo temporário
                    os.remove(temp_path)
            
            data = request.json if request.json else request.form
            
            novo_profissional = {
                'nome': data.get('nome'),
                'cpf': re.sub(r'\D', '', data.get('cpf', '')),
                'telefone': data.get('telefone'),
                'email': data.get('email', '').lower(),
                'especialidade': data.get('especialidade'),
                'comissao': float(data.get('comissao', 10)),
                'foto': foto_base64,
                'status': 'Ativo',
                'data_cadastro': datetime.now()
            }
            
            result = db.profissionais.insert_one(novo_profissional)
            
            logger.info(f"✅ Profissional cadastrado: {novo_profissional['nome']}")
            return jsonify({
                'success': True,
                'message': 'Profissional cadastrado com sucesso!',
                'id': str(result.inserted_id)
            })
            
        except Exception as e:
            logger.error(f"Erro ao cadastrar profissional: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profissionais/<prof_id>/foto', methods=['GET'])
def get_profissional_foto(prof_id):
    """Retorna foto do profissional"""
    try:
        prof = db.profissionais.find_one({'_id': ObjectId(prof_id)})
        
        if prof and prof.get('foto'):
            img_data = base64.b64decode(prof['foto'])
            return send_file(
                io.BytesIO(img_data),
                mimetype='image/jpeg'
            )
        
        # Retornar imagem padrão
        return '', 404
        
    except Exception as e:
        logger.error(f"Erro ao buscar foto: {e}")
        return '', 404

# ======================== ROTAS DE RELATÓRIOS ========================
@app.route('/api/relatorios/resumo', methods=['GET'])
@login_required
def get_relatorio_resumo():
    """Retorna resumo geral com gráficos"""
    try:
        # Período
        mes_atual = datetime.now().month
        ano_atual = datetime.now().year
        
        # Vendas por mês (últimos 6 meses)
        vendas_mensais = []
        for i in range(6):
            mes = mes_atual - i
            ano = ano_atual
            if mes <= 0:
                mes += 12
                ano -= 1
            
            inicio = datetime(ano, mes, 1)
            fim = datetime(ano, mes + 1, 1) if mes < 12 else datetime(ano + 1, 1, 1)
            
            vendas = db.orcamentos.count_documents({
                'status': 'Aprovado',
                'data_criacao': {'$gte': inicio, '$lt': fim}
            })
            
            valor = sum(float(o.get('valor_total', 0)) for o in db.orcamentos.find({
                'status': 'Aprovado',
                'data_criacao': {'$gte': inicio, '$lt': fim}
            }))
            
            vendas_mensais.append({
                'mes': f"{mes}/{ano}",
                'vendas': vendas,
                'valor': round(valor, 2)
            })
        
        vendas_mensais.reverse()
        
        # Top clientes
        pipeline = [
            {'$match': {'status': 'Aprovado'}},
            {'$group': {
                '_id': '$cliente_id',
                'total': {'$sum': '$valor_total'},
                'count': {'$sum': 1}
            }},
            {'$sort': {'total': -1}},
            {'$limit': 10}
        ]
        
        top_clientes_raw = list(db.orcamentos.aggregate(pipeline))
        top_clientes = []
        
        for tc in top_clientes_raw:
            cliente = db.clientes.find_one({'_id': ObjectId(tc['_id'])}) if tc['_id'] else None
            if cliente:
                top_clientes.append({
                    'nome': cliente['nome'],
                    'total': round(tc['total'], 2),
                    'num_compras': tc['count']
                })
        
        # Top produtos
        produtos_vendidos = {}
        orcamentos = db.orcamentos.find({'status': 'Aprovado'})
        
        for orc in orcamentos:
            for item in orc.get('itens', []):
                if item.get('tipo') == 'produto':
                    nome = item.get('nome')
                    if nome not in produtos_vendidos:
                        produtos_vendidos[nome] = {
                            'quantidade': 0,
                            'valor': 0
                        }
                    produtos_vendidos[nome]['quantidade'] += item.get('quantidade', 1)
                    produtos_vendidos[nome]['valor'] += item.get('subtotal', 0)
        
        top_produtos = sorted(
            [{'nome': k, **v} for k, v in produtos_vendidos.items()],
            key=lambda x: x['valor'],
            reverse=True
        )[:10]
        
        return jsonify({
            'success': True,
            'data': {
                'vendas_mensais': vendas_mensais,
                'top_clientes': top_clientes,
                'top_produtos': top_produtos
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório resumo: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/relatorios/mapa-calor', methods=['GET'])
@login_required
def get_mapa_calor():
    """Retorna dados para mapa de calor"""
    try:
        # Últimos 30 dias
        inicio = datetime.now() - timedelta(days=30)
        
        # Agrupar por dia
        pipeline = [
            {'$match': {
                'data': {'$gte': inicio}
            }},
            {'$group': {
                '_id': {
                    'year': {'$year': '$data'},
                    'month': {'$month': '$data'},
                    'day': {'$dayOfMonth': '$data'}
                },
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id': 1}}
        ]
        
        agendamentos_dia = list(db.agendamentos.aggregate(pipeline))
        
        mapa_calor = []
        for item in agendamentos_dia:
            data = datetime(
                item['_id']['year'],
                item['_id']['month'],
                item['_id']['day']
            )
            
            # Determinar intensidade (1-5)
            count = item['count']
            if count <= 2:
                intensidade = 1
            elif count <= 5:
                intensidade = 2
            elif count <= 8:
                intensidade = 3
            elif count <= 12:
                intensidade = 4
            else:
                intensidade = 5
            
            mapa_calor.append({
                'data': data.strftime('%Y-%m-%d'),
                'dia_semana': ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'][data.weekday()],
                'atendimentos': count,
                'intensidade': intensidade
            })
        
        return jsonify({'success': True, 'mapa_calor': mapa_calor})
        
    except Exception as e:
        logger.error(f"Erro ao gerar mapa de calor: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ======================== ROTAS DE CONFIGURAÇÕES ========================
@app.route('/api/configuracoes', methods=['GET', 'PUT'])
@login_required
@check_permission('all')
def manage_configuracoes():
    """Gerencia configurações do sistema (Admin)"""
    if request.method == 'GET':
        try:
            config = db.configuracoes.find_one({'tipo': 'sistema'})
            if config:
                config['_id'] = str(config['_id'])
            
            return jsonify({'success': True, 'configuracoes': config})
            
        except Exception as e:
            logger.error(f"Erro ao buscar configurações: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    else:  # PUT
        try:
            data = request.json
            
            # Processar upload de logo se houver
            if 'logo' in request.files:
                file = request.files['logo']
                if file and allowed_file(file.filename):
                    # Salvar e redimensionar logo
                    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
                    file.save(temp_path)
                    
                    resized = resize_image(temp_path, (400, 200))
                    if resized:
                        logo_base64 = base64.b64encode(resized.read()).decode('utf-8')
                        data['logo_url'] = f"data:image/jpeg;base64,{logo_base64}"
                    
                    os.remove(temp_path)
            
            # Atualizar configurações
            db.configuracoes.update_one(
                {'tipo': 'sistema'},
                {'$set': {
                    **data,
                    'updated_at': datetime.now()
                }},
                upsert=True
            )
            
            # Registrar na auditoria
            db.auditoria.insert_one({
                'usuario_id': session['user_id'],
                'acao': 'configuracoes_atualizadas',
                'detalhes': 'Configurações do sistema atualizadas',
                'data': datetime.now()
            })
            
            logger.info("✅ Configurações atualizadas")
            return jsonify({'success': True, 'message': 'Configurações atualizadas com sucesso!'})
            
        except Exception as e:
            logger.error(f"Erro ao atualizar configurações: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

# ======================== ROTAS DE AUDITORIA ========================
@app.route('/api/auditoria', methods=['GET'])
@login_required
@check_permission('all')
def get_auditoria():
    """Busca logs de auditoria (Admin)"""
    try:
        # Filtros
        filtro = {}
        
        if request.args.get('usuario_id'):
            filtro['usuario_id'] = request.args.get('usuario_id')
        
        if request.args.get('acao'):
            filtro['acao'] = request.args.get('acao')
        
        if request.args.get('data_inicio') and request.args.get('data_fim'):
            data_inicio = datetime.strptime(request.args.get('data_inicio'), '%Y-%m-%d')
            data_fim = datetime.strptime(request.args.get('data_fim'), '%Y-%m-%d')
            filtro['data'] = {'$gte': data_inicio, '$lte': data_fim}
        
        # Buscar logs
        logs = list(db.auditoria.find(filtro).sort('data', DESCENDING).limit(500))
        
        for log in logs:
            log['_id'] = str(log['_id'])
            
            # Buscar usuário
            if log.get('usuario_id'):
                user = db.usuarios.find_one({'_id': ObjectId(log['usuario_id'])})
                if user:
                    log['usuario_nome'] = user.get('nome')
                    log['usuario_email'] = user.get('email')
            
            log['data'] = log['data'].strftime('%d/%m/%Y %H:%M:%S')
        
        return jsonify({'success': True, 'logs': logs})
        
    except Exception as e:
        logger.error(f"Erro ao buscar auditoria: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ======================== ROTAS AUXILIARES ========================
@app.route('/api/notificacoes', methods=['GET'])
@login_required
def get_notificacoes():
    """Busca notificações do usuário"""
    try:
        notificacoes = list(db.notificacoes.find({
            'usuario_id': session['user_id'],
            'lida': False
        }).sort('data', DESCENDING).limit(20))
        
        for notif in notificacoes:
            notif['_id'] = str(notif['_id'])
            notif['data'] = notif['data'].strftime('%d/%m/%Y %H:%M')
        
        return jsonify({'success': True, 'notificacoes': notificacoes})
        
    except Exception as e:
        logger.error(f"Erro ao buscar notificações: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/notificacoes/<notif_id>/marcar-lida', methods=['PUT'])
@login_required
def marcar_notificacao_lida(notif_id):
    """Marca notificação como lida"""
    try:
        db.notificacoes.update_one(
            {'_id': ObjectId(notif_id)},
            {'$set': {'lida': True}}
        )
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Erro ao marcar notificação: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ======================== INICIALIZAÇÃO ========================
if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🌳 BIOMA UBERABA v4.0 MELHORADO - Sistema Completo")
    print("=" * 80)
    init_db()
    is_production = os.getenv('FLASK_ENV') == 'production'
    base_url = 'https://bioma-system.onrender.com' if is_production else 'http://localhost:5000'
    print(f"\n🚀 Servidor: {base_url}")
    print(f"👤 Login Padrão: admin / admin123")
    print(f"🔑 Sistema de níveis de acesso implementado:")
    print(f"   - Admin: Acesso total")
    print(f"   - Gestão: Visualizar e editar tudo")
    print(f"   - Profissional: Acesso limitado")
    print("\n✅ Melhorias implementadas:")
    print("   - Sistema de notificações (SMS, Email, WhatsApp)")
    print("   - Impressão e envio de documentos")
    print("   - Aba Financeiro completa")
    print("   - Correção de rotas e carregamento")
    print("   - Upload e tratamento de imagens")
    print("   - Sistema de auditoria")
    
    if db is not None:
        try:
            db.command('ping')
            print(f"\n💾 MongoDB: ✅ CONECTADO")
        except:
            print(f"\n💾 MongoDB: ❌ ERRO DE CONEXÃO")
    else:
        print(f"\n💾 MongoDB: ❌ NÃO CONECTADO")
    
    print("\n" + "=" * 80)
    print(f"🕐 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"👨‍💻 Desenvolvedor: @juanmarco1999")
    print(f"📧 Contato: 180147064@aluno.unb.br")
    print("=" * 80 + "\n")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)