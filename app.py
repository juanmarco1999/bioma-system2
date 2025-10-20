#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA UBERABA v3.7 COMPLETO - Sistema Ultra Profissional
Desenvolvedor: Juan Marco (@juanmarco1999)
Email: 180147064@aluno.unb.br
Data: 2025-10-05 21:57:49 UTC
"""

from flask import Flask, render_template, request, jsonify, session, send_file, Response
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
app.secret_key = os.getenv('SECRET_KEY', 'bioma-2025-v3-7-ultra-secure-key-final-definitivo-completo')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = '/tmp'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

CORS(app, supports_credentials=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

ANAMNESE_FORM = [
    {
        'ordem': 1,
        'campo': 'QUAIS SÃO AS COISAS QUE INCOMODAM NO SEU COURO CABELUDO?',
        'tipo': 'select',
        'opcoes': ['Coceira', 'Descamação', 'Oleosidade', 'Sensibilidade', 'Feridas', 'Ardor', 'Outro']
    },
    {
        'ordem': 2,
        'campo': 'QUAIS SÃO AS COISAS QUE INCOMODAM NO COURO CABELUDO?',
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
    {'ordem': 5, 'campo': 'Valor Cobrado', 'tipo': 'text'},
    {'ordem': 6, 'campo': 'Observações Durante o Atendimento', 'tipo': 'textarea'},
    {'ordem': 7, 'campo': 'Vendas', 'tipo': 'text'}
]

def default_form_state(definition):
    return {item['campo']: '' for item in definition}

def get_db():
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

def convert_objectid(obj):
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
            logger.warning(f"🚫 Unauthorized: {request.endpoint}")
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def send_email(to, name, subject, html_content, pdf=None):
    api_key = os.getenv('MAILERSEND_API_KEY')
    from_email = os.getenv('MAILERSEND_FROM_EMAIL')
    from_name = os.getenv('MAILERSEND_FROM_NAME', 'BIOMA Uberaba')
    
    if not api_key or not from_email:
        logger.warning("⚠️ MailerSend não configurado")
        return {'success': False, 'message': 'Email não configurado'}
    
    data = {"from": {"email": from_email, "name": from_name}, "to": [{"email": to, "name": name}], "subject": subject, "html": html_content}
    
    if pdf:
        import base64
        data['attachments'] = [{"filename": pdf['filename'], "content": base64.b64encode(pdf['content']).decode(), "disposition": "attachment"}]
    
    try:
        logger.info(f"📧 Enviando para: {to}")
        r = requests.post("https://api.mailersend.com/v1/email", headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}, json=data, timeout=10)
        if r.status_code == 202:
            logger.info(f"✅ Email enviado: {to}")
            return {'success': True}
        else:
            logger.error(f"❌ Email falhou: {r.status_code}")
            return {'success': False}
    except Exception as e:
        logger.error(f"❌ Email exception: {e}")
        return {'success': False}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    db_status = 'connected' if db is not None else 'disconnected'
    if db is not None:
        try:
            db.command('ping')
        except:
            db_status = 'error'
    return jsonify({'status': 'healthy', 'time': datetime.now().isoformat(), 'database': db_status, 'version': '3.7.0'}), 200

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    logger.info(f"🔐 Login attempt: {data.get('username')}")
    
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        user = db.users.find_one({'$or': [{'username': data['username']}, {'email': data['username']}]})
        
        if user and check_password_hash(user['password'], data['password']):
            session.permanent = True
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['role'] = user.get('role', 'admin')
            
            logger.info(f"✅ Login SUCCESS: {user['username']} (role: {session['role']})")
            
            return jsonify({
                'success': True,
                'user': {
                    'id': str(user['_id']),
                    'name': user['name'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user.get('role', 'admin'),
                    'theme': user.get('theme', 'light')
                }
            })
        
        logger.warning(f"❌ Login FAILED: {data.get('username')}")
        return jsonify({'success': False, 'message': 'Usuário ou senha inválidos'})
        
    except Exception as e:
        logger.error(f"❌ Login ERROR: {e}")
        return jsonify({'success': False, 'message': 'Erro no servidor'}), 500

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    logger.info(f"👤 Register attempt: {data.get('username')}")
    
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        if db.users.find_one({'$or': [{'username': data['username']}, {'email': data['email']}]}):
            return jsonify({'success': False, 'message': 'Usuário ou email já existe'})
        
        user_data = {
            'name': data['name'],
            'username': data['username'],
            'email': data['email'],
            'telefone': data.get('telefone', ''),
            'password': generate_password_hash(data['password']),
            'role': 'admin',
            'theme': 'light',
            'created_at': datetime.now()
        }
        
        db.users.insert_one(user_data)
        logger.info(f"✅ User registered: {data['username']} with ADMIN role")
        
        return jsonify({'success': True, 'message': 'Conta criada com sucesso! Faça login.'})
        
    except Exception as e:
        logger.error(f"❌ Register ERROR: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    username = session.get('username', 'Unknown')
    session.clear()
    logger.info(f"🚪 Logout: {username}")
    return jsonify({'success': True})

@app.route('/api/current-user')
def current_user():
    if 'user_id' in session and db is not None:
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
                        'role': user.get('role', 'admin'),
                        'theme': user.get('theme', 'light')
                    }
                })
        except Exception as e:
            logger.error(f"❌ Current user error: {e}")
    return jsonify({'success': False})

@app.route('/api/update-theme', methods=['POST'])
@login_required
def update_theme():
    if db is None:
        return jsonify({'success': False}), 500
    try:
        db.users.update_one({'_id': ObjectId(session['user_id'])}, {'$set': {'theme': request.json['theme']}})
        return jsonify({'success': True})
    except:
        return jsonify({'success': False}), 500

@app.route('/api/system/status')
@login_required
def system_status():
    mongo_ok = False
    mongo_msg = 'Desconectado'
    try:
        if db is not None:
            db.command('ping')
            mongo_ok = True
            mongo_msg = 'Conectado'
    except Exception as e:
        mongo_msg = f'Erro: {str(e)[:100]}'
    
    return jsonify({
        'success': True,
        'status': {
            'mongodb': {'operational': mongo_ok, 'message': mongo_msg, 'last_check': datetime.now().isoformat()},
            'mailersend': {'operational': bool(os.getenv('MAILERSEND_API_KEY')), 'message': 'Configurado' if bool(os.getenv('MAILERSEND_API_KEY')) else 'Não configurado'},
            'server': {'time': datetime.now().isoformat(), 'version': '3.7.0'}
        }
    })

@app.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        hoje_inicio = datetime.now().replace(hour=0, minute=0, second=0)
        hoje_fim = datetime.now().replace(hour=23, minute=59, second=59)
        
        agendamentos_hoje = 0
        if 'agendamentos' in db.list_collection_names():
            agendamentos_hoje = db.agendamentos.count_documents({'data': {'$gte': hoje_inicio, '$lte': hoje_fim}})
        
        stats = {
            'total_orcamentos': db.orcamentos.count_documents({}),
            'total_clientes': db.clientes.count_documents({}),
            'total_servicos': db.servicos.count_documents({}),
            'faturamento': sum(o.get('total_final', 0) for o in db.orcamentos.find({'status': 'Aprovado'})),
            'agendamentos_hoje': agendamentos_hoje
        }
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        logger.error(f"❌ Dashboard stats error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clientes', methods=['GET', 'POST'])
@login_required
def clientes():
    if db is None:
        return jsonify({'success': False}), 500
    
    if request.method == 'GET':
        try:
            clientes_list = list(db.clientes.find({}).sort('nome', ASCENDING))
            for cliente in clientes_list:
                cliente_cpf = cliente.get('cpf')
                cliente['total_gasto'] = sum(o.get('total_final', 0) for o in db.orcamentos.find({'cliente_cpf': cliente_cpf, 'status': 'Aprovado'}))
                ultimo_orc = db.orcamentos.find_one({'cliente_cpf': cliente_cpf}, sort=[('created_at', DESCENDING)])
                cliente['ultima_visita'] = ultimo_orc['created_at'] if ultimo_orc else None
                cliente['total_visitas'] = db.orcamentos.count_documents({'cliente_cpf': cliente_cpf})
            return jsonify({'success': True, 'clientes': convert_objectid(clientes_list)})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    data = request.json
    try:
        existing = db.clientes.find_one({'cpf': data['cpf']})
        cliente_data = {'nome': data['nome'], 'cpf': data['cpf'], 'email': data.get('email', ''), 'telefone': data.get('telefone', ''), 'updated_at': datetime.now()}
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
    if db is None:
        return jsonify({'success': False}), 500
    try:
        result = db.clientes.delete_one({'_id': ObjectId(id)})
        return jsonify({'success': result.deleted_count > 0})
    except:
        return jsonify({'success': False}), 500

@app.route('/api/clientes/<id>', methods=['GET'])
@login_required
def get_cliente(id):
    """Visualizar um cliente específico"""
    if db is None:
        return jsonify({'success': False}), 500
    try:
        cliente = db.clientes.find_one({'_id': ObjectId(id)})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
        
        # Adicionar estatísticas
        cliente_cpf = cliente.get('cpf')
        cliente['total_gasto'] = sum(o.get('total_final', 0) for o in db.orcamentos.find({'cliente_cpf': cliente_cpf, 'status': 'Aprovado'}))
        ultimo_orc = db.orcamentos.find_one({'cliente_cpf': cliente_cpf}, sort=[('created_at', DESCENDING)])
        cliente['ultima_visita'] = ultimo_orc['created_at'] if ultimo_orc else None
        cliente['total_visitas'] = db.orcamentos.count_documents({'cliente_cpf': cliente_cpf})
        
        return jsonify({'success': True, 'cliente': convert_objectid(cliente)})
    except Exception as e:
        logger.error(f"Erro ao buscar cliente: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clientes/<id>', methods=['PUT'])
@login_required
def update_cliente(id):
    """Editar um cliente existente"""
    if db is None:
        return jsonify({'success': False}), 500
    
    data = request.json
    try:
        cliente_existente = db.clientes.find_one({'_id': ObjectId(id)})
        if not cliente_existente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
        
        # Verificar se o CPF já existe em outro cliente
        if data.get('cpf') != cliente_existente.get('cpf'):
            cpf_duplicado = db.clientes.find_one({'cpf': data['cpf'], '_id': {'$ne': ObjectId(id)}})
            if cpf_duplicado:
                return jsonify({'success': False, 'message': 'CPF já cadastrado em outro cliente'}), 400
        
        anamnese_respostas = data.get('anamnese')
        prontuario_respostas = data.get('prontuario')
        if anamnese_respostas is None:
            anamnese_respostas = cliente_existente.get('anamnese', default_form_state(ANAMNESE_FORM))
        if prontuario_respostas is None:
            prontuario_respostas = cliente_existente.get('prontuario', default_form_state(PRONTUARIO_FORM))

        update_data = {
            'nome': data.get('nome', cliente_existente.get('nome')),
            'cpf': data.get('cpf', cliente_existente.get('cpf')),
            'email': data.get('email', cliente_existente.get('email', '')),
            'telefone': data.get('telefone', cliente_existente.get('telefone', '')),
            'endereco': data.get('endereco', cliente_existente.get('endereco', '')),
            'data_nascimento': data.get('data_nascimento', cliente_existente.get('data_nascimento', '')),
            'genero': data.get('genero', cliente_existente.get('genero', '')),
            'estado_civil': data.get('estado_civil', cliente_existente.get('estado_civil', '')),
            'profissao': data.get('profissao', cliente_existente.get('profissao', '')),
            'instagram': data.get('instagram', cliente_existente.get('instagram', '')),
            'indicacao': data.get('indicacao', cliente_existente.get('indicacao', '')),
            'preferencias': data.get('preferencias', cliente_existente.get('preferencias', '')),
            'restricoes': data.get('restricoes', cliente_existente.get('restricoes', '')),
            'tipo_cabelo': data.get('tipo_cabelo', cliente_existente.get('tipo_cabelo', '')),
            'historico_tratamentos': data.get('historico_tratamentos', cliente_existente.get('historico_tratamentos', '')),
            'observacoes': data.get('observacoes', cliente_existente.get('observacoes', '')),
            'anamnese': anamnese_respostas if isinstance(anamnese_respostas, dict) else cliente_existente.get('anamnese', default_form_state(ANAMNESE_FORM)),
            'prontuario': prontuario_respostas if isinstance(prontuario_respostas, dict) else cliente_existente.get('prontuario', default_form_state(PRONTUARIO_FORM)),
            'updated_at': datetime.now()
        }
        
        db.clientes.update_one({'_id': ObjectId(id)}, {'$set': update_data})
        logger.info(f"✅ Cliente atualizado: {update_data['nome']}")
        
        return jsonify({'success': True, 'message': 'Cliente atualizado com sucesso'})
    except Exception as e:
        logger.error(f"Erro ao atualizar cliente: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clientes/buscar')
@login_required
def buscar_clientes():
    if db is None:
        return jsonify({'success': False}), 500
    termo = request.args.get('termo', '').strip()
    try:
        regex = {'$regex': termo, '$options': 'i'}
        clientes = list(db.clientes.find({
            '$or': [
                {'nome': regex},
                {'cpf': regex},
                {'email': regex},
                {'telefone': regex}
            ]
        }).sort('nome', ASCENDING).limit(50))
        
        # Adicionar informação completa formatada
        for c in clientes:
            c['display_name'] = f"{c.get('nome', '')} - CPF: {c.get('cpf', '')}"
        
        return jsonify({'success': True, 'clientes': convert_objectid(clientes)})
    except Exception as e:
        logger.error(f"Erro ao buscar clientes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profissionais', methods=['GET', 'POST'])
@login_required
def profissionais():
    if db is None:
        return jsonify({'success': False}), 500
    
    if request.method == 'GET':
        try:
            profs = list(db.profissionais.find({}).sort('nome', ASCENDING))
            return jsonify({'success': True, 'profissionais': convert_objectid(profs)})
        except:
            return jsonify({'success': False}), 500
    
    data = request.json
    try:
        profissional_data = {
            'nome': data['nome'],
            'cpf': data['cpf'],
            'email': data.get('email', ''),
            'telefone': data.get('telefone', ''),
            'especialidade': data.get('especialidade', ''),
            'comissao_perc': float(data.get('comissao_perc', 0)),
            'foto_url': data.get('foto_url', ''),
            'assistente_id': data.get('assistente_id', None),
            'comissao_assistente_perc': float(data.get('comissao_assistente_perc', 0)),
            'ativo': True,
            'created_at': datetime.now()
        }
        db.profissionais.insert_one(profissional_data)
        return jsonify({'success': True})
    except:
        return jsonify({'success': False}), 500

@app.route('/api/profissionais/<id>', methods=['DELETE'])
@login_required
def delete_profissional(id):
    if db is None:
        return jsonify({'success': False}), 500
    try:
        result = db.profissionais.delete_one({'_id': ObjectId(id)})
        return jsonify({'success': result.deleted_count > 0})
    except:
        return jsonify({'success': False}), 500

@app.route('/api/profissionais/<id>', methods=['GET'])
@login_required
def get_profissional(id):
    """Visualizar um profissional específico com estatísticas completas"""
    if db is None:
        return jsonify({'success': False}), 500
    try:
        profissional = db.profissionais.find_one({'_id': ObjectId(id)})
        if not profissional:
            return jsonify({'success': False, 'message': 'Profissional não encontrado'}), 404
        
        # Buscar orçamentos relacionados ao profissional
        orcamentos_prof = list(db.orcamentos.find({
            'servicos.profissional_id': str(profissional['_id'])
        }))
        
        # Calcular estatísticas
        total_comissao = 0
        servicos_realizados = 0
        assistente = None
        
        # Buscar assistente se existir
        if profissional.get('assistente_id'):
            assistente = db.profissionais.find_one({'_id': ObjectId(profissional['assistente_id'])})
        
        for orc in orcamentos_prof:
            if orc.get('status') == 'Aprovado':
                for servico in orc.get('servicos', []):
                    if servico.get('profissional_id') == str(profissional['_id']):
                        servicos_realizados += 1
                        comissao_valor = servico.get('total', 0) * (profissional.get('comissao_perc', 0) / 100)
                        total_comissao += comissao_valor
        
        profissional['estatisticas'] = {
            'total_comissao': total_comissao,
            'servicos_realizados': servicos_realizados,
            'total_orcamentos': len(orcamentos_prof)
        }
        
        if assistente:
            profissional['assistente'] = convert_objectid(assistente)
        
        return jsonify({'success': True, 'profissional': convert_objectid(profissional)})
    except Exception as e:
        logger.error(f"Erro ao buscar profissional: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profissionais/<id>', methods=['PUT'])
@login_required
def update_profissional(id):
    """Editar um profissional existente"""
    if db is None:
        return jsonify({'success': False}), 500
    
    data = request.json
    try:
        profissional_existente = db.profissionais.find_one({'_id': ObjectId(id)})
        if not profissional_existente:
            return jsonify({'success': False, 'message': 'Profissional não encontrado'}), 404
        
        # Verificar se o CPF já existe em outro profissional
        if data.get('cpf') != profissional_existente.get('cpf'):
            cpf_duplicado = db.profissionais.find_one({'cpf': data['cpf'], '_id': {'$ne': ObjectId(id)}})
            if cpf_duplicado:
                return jsonify({'success': False, 'message': 'CPF já cadastrado em outro profissional'}), 400
        
        update_data = {
            'nome': data.get('nome', profissional_existente.get('nome')),
            'cpf': data.get('cpf', profissional_existente.get('cpf')),
            'email': data.get('email', profissional_existente.get('email', '')),
            'telefone': data.get('telefone', profissional_existente.get('telefone', '')),
            'especialidade': data.get('especialidade', profissional_existente.get('especialidade', '')),
            'comissao_perc': float(data.get('comissao_perc', profissional_existente.get('comissao_perc', 0))),
            'foto_url': data.get('foto_url', profissional_existente.get('foto_url', '')),
            'assistente_id': data.get('assistente_id', profissional_existente.get('assistente_id', None)),
            'comissao_assistente_perc': float(data.get('comissao_assistente_perc', profissional_existente.get('comissao_assistente_perc', 0))),
            'ativo': data.get('ativo', profissional_existente.get('ativo', True)),
            'updated_at': datetime.now()
        }
        
        db.profissionais.update_one({'_id': ObjectId(id)}, {'$set': update_data})
        logger.info(f"✅ Profissional atualizado: {update_data['nome']}")
        
        return jsonify({'success': True, 'message': 'Profissional atualizado com sucesso'})
    except Exception as e:
        logger.error(f"Erro ao atualizar profissional: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/servicos', methods=['GET', 'POST'])
@login_required
def servicos():
    if db is None:
        return jsonify({'success': False}), 500
    
    if request.method == 'GET':
        try:
            servs = list(db.servicos.find({}).sort('nome', ASCENDING))
            return jsonify({'success': True, 'servicos': convert_objectid(servs)})
        except:
            return jsonify({'success': False}), 500
    
    data = request.json
    try:
        tamanhos = {'Kids': data.get('preco_kids', 0), 'Masculino': data.get('preco_masculino', 0), 'Curto': data.get('preco_curto', 0), 'Médio': data.get('preco_medio', 0), 'Longo': data.get('preco_longo', 0), 'Extra Longo': data.get('preco_extra_longo', 0)}
        count = 0
        for tam, preco in tamanhos.items():
            preco_float = float(preco) if preco else 0
            if preco_float > 0:
                db.servicos.insert_one({'nome': data['nome'], 'sku': f"{data['nome'].upper().replace(' ', '-')}-{tam.upper().replace(' ', '-')}", 'tamanho': tam, 'preco': preco_float, 'categoria': data.get('categoria', 'Serviço'), 'duracao': int(data.get('duracao', 60)), 'ativo': True, 'created_at': datetime.now()})
                count += 1
        return jsonify({'success': True, 'count': count})
    except:
        return jsonify({'success': False}), 500

@app.route('/api/servicos/<id>', methods=['DELETE'])
@login_required
def delete_servico(id):
    if db is None:
        return jsonify({'success': False}), 500
    try:
        result = db.servicos.delete_one({'_id': ObjectId(id)})
        return jsonify({'success': result.deleted_count > 0})
    except:
        return jsonify({'success': False}), 500

@app.route('/api/servicos/<id>', methods=['GET'])
@login_required
def get_servico(id):
    """Visualizar um serviço específico"""
    if db is None:
        return jsonify({'success': False}), 500
    try:
        servico = db.servicos.find_one({'_id': ObjectId(id)})
        if not servico:
            return jsonify({'success': False, 'message': 'Serviço não encontrado'}), 404
        return jsonify({'success': True, 'servico': convert_objectid(servico)})
    except Exception as e:
        logger.error(f"Erro ao buscar serviço: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/servicos/<id>', methods=['PUT'])
@login_required
def update_servico(id):
    """Editar um serviço existente"""
    if db is None:
        return jsonify({'success': False}), 500
    
    data = request.json
    try:
        servico_existente = db.servicos.find_one({'_id': ObjectId(id)})
        if not servico_existente:
            return jsonify({'success': False, 'message': 'Serviço não encontrado'}), 404
        
        update_data = {
            'nome': data.get('nome', servico_existente.get('nome')),
            'sku': data.get('sku', servico_existente.get('sku')),
            'tamanho': data.get('tamanho', servico_existente.get('tamanho')),
            'preco': float(data.get('preco', servico_existente.get('preco', 0))),
            'categoria': data.get('categoria', servico_existente.get('categoria', 'Serviço')),
            'duracao': int(data.get('duracao', servico_existente.get('duracao', 60))),
            'ativo': data.get('ativo', servico_existente.get('ativo', True)),
            'updated_at': datetime.now()
        }
        
        db.servicos.update_one({'_id': ObjectId(id)}, {'$set': update_data})
        logger.info(f"✅ Serviço atualizado: {update_data['nome']}")
        
        return jsonify({'success': True, 'message': 'Serviço atualizado com sucesso'})
    except Exception as e:
        logger.error(f"Erro ao atualizar serviço: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/servicos/buscar')
@login_required
def buscar_servicos():
    if db is None:
        return jsonify({'success': False}), 500
    termo = request.args.get('termo', '').strip()
    try:
        # Busca mais abrangente: por nome, tamanho ou SKU
        regex = {'$regex': termo, '$options': 'i'}
        servicos = list(db.servicos.find({
            '$or': [
                {'nome': regex},
                {'tamanho': regex},
                {'sku': regex}
            ],
            'ativo': True
        }).sort([('nome', ASCENDING), ('tamanho', ASCENDING)]).limit(50))
        
        # Adicionar informação completa formatada para exibição
        for s in servicos:
            s['display_name'] = f"{s.get('nome', '')} - {s.get('tamanho', '')} (R$ {s.get('preco', 0):.2f})"
        
        return jsonify({'success': True, 'servicos': convert_objectid(servicos)})
    except Exception as e:
        logger.error(f"Erro ao buscar serviços: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profissionais/buscar')
@login_required
def buscar_profissionais():
    """Buscar profissionais com sugestões de preenchimento"""
    if db is None:
        return jsonify({'success': False}), 500
    termo = request.args.get('termo', '').strip()
    try:
        regex = {'$regex': termo, '$options': 'i'}
        profissionais = list(db.profissionais.find({
            '$or': [
                {'nome': regex},
                {'cpf': regex},
                {'especialidade': regex}
            ],
            'ativo': True
        }).sort('nome', ASCENDING).limit(50))
        
        for p in profissionais:
            p['display_name'] = f"{p.get('nome', '')} - {p.get('especialidade', 'Profissional')}"
        
        return jsonify({'success': True, 'profissionais': convert_objectid(profissionais)})
    except Exception as e:
        logger.error(f"Erro ao buscar profissionais: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/produtos', methods=['GET', 'POST'])
@login_required
def produtos():
    if db is None:
        return jsonify({'success': False}), 500
    
    if request.method == 'GET':
        try:
            prods = list(db.produtos.find({}).sort('nome', ASCENDING))
            return jsonify({'success': True, 'produtos': convert_objectid(prods)})
        except:
            return jsonify({'success': False}), 500
    
    data = request.json
    try:
        produto_id = db.produtos.insert_one({'nome': data['nome'], 'marca': data.get('marca', ''), 'sku': data.get('sku', f"PROD-{datetime.now().timestamp()}"), 'preco': float(data.get('preco', 0)), 'custo': float(data.get('custo', 0)), 'estoque': int(data.get('estoque', 0)), 'estoque_minimo': int(data.get('estoque_minimo', 5)), 'categoria': data.get('categoria', 'Produto'), 'ativo': True, 'created_at': datetime.now()}).inserted_id
        if int(data.get('estoque', 0)) > 0:
            db.estoque_movimentacoes.insert_one({'produto_id': produto_id, 'tipo': 'entrada', 'quantidade': int(data.get('estoque', 0)), 'motivo': 'Cadastro inicial', 'usuario': session.get('username', 'system'), 'data': datetime.now()})
        return jsonify({'success': True})
    except:
        return jsonify({'success': False}), 500

@app.route('/api/produtos/<id>', methods=['DELETE'])
@login_required
def delete_produto(id):
    if db is None:
        return jsonify({'success': False}), 500
    try:
        result = db.produtos.delete_one({'_id': ObjectId(id)})
        return jsonify({'success': result.deleted_count > 0})
    except:
        return jsonify({'success': False}), 500

@app.route('/api/produtos/<id>', methods=['GET'])
@login_required
def get_produto(id):
    """Visualizar um produto específico"""
    if db is None:
        return jsonify({'success': False}), 500
    try:
        produto = db.produtos.find_one({'_id': ObjectId(id)})
        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
        return jsonify({'success': True, 'produto': convert_objectid(produto)})
    except Exception as e:
        logger.error(f"Erro ao buscar produto: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/produtos/<id>', methods=['PUT'])
@login_required
def update_produto(id):
    """Editar um produto existente"""
    if db is None:
        return jsonify({'success': False}), 500
    
    data = request.json
    try:
        produto_existente = db.produtos.find_one({'_id': ObjectId(id)})
        if not produto_existente:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
        
        # Verificar se o SKU já existe em outro produto
        if data.get('sku') != produto_existente.get('sku'):
            sku_duplicado = db.produtos.find_one({'sku': data['sku'], '_id': {'$ne': ObjectId(id)}})
            if sku_duplicado:
                return jsonify({'success': False, 'message': 'SKU já cadastrado em outro produto'}), 400
        
        update_data = {
            'nome': data.get('nome', produto_existente.get('nome')),
            'marca': data.get('marca', produto_existente.get('marca', '')),
            'sku': data.get('sku', produto_existente.get('sku')),
            'preco': float(data.get('preco', produto_existente.get('preco', 0))),
            'custo': float(data.get('custo', produto_existente.get('custo', 0))),
            'estoque': int(data.get('estoque', produto_existente.get('estoque', 0))),
            'estoque_minimo': int(data.get('estoque_minimo', produto_existente.get('estoque_minimo', 5))),
            'categoria': data.get('categoria', produto_existente.get('categoria', 'Produto')),
            'ativo': data.get('ativo', produto_existente.get('ativo', True)),
            'updated_at': datetime.now()
        }
        
        db.produtos.update_one({'_id': ObjectId(id)}, {'$set': update_data})
        logger.info(f"✅ Produto atualizado: {update_data['nome']}")
        
        return jsonify({'success': True, 'message': 'Produto atualizado com sucesso'})
    except Exception as e:
        logger.error(f"Erro ao atualizar produto: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/produtos/buscar')
@login_required
def buscar_produtos():
    if db is None:
        return jsonify({'success': False}), 500
    termo = request.args.get('termo', '').strip()
    try:
        regex = {'$regex': termo, '$options': 'i'}
        produtos = list(db.produtos.find({
            '$or': [
                {'nome': regex},
                {'marca': regex},
                {'sku': regex}
            ],
            'ativo': True
        }).sort('nome', ASCENDING).limit(50))
        
        # Adicionar informação completa formatada para exibição
        for p in produtos:
            marca = p.get('marca', '')
            p['display_name'] = f"{p.get('nome', '')} {('- ' + marca) if marca else ''} (R$ {p.get('preco', 0):.2f})"
        
        return jsonify({'success': True, 'produtos': convert_objectid(produtos)})
    except Exception as e:
        logger.error(f"Erro ao buscar produtos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/movimentacoes', methods=['GET'])
@login_required
def get_movimentacoes_estoque():
    """Listar todas as movimentações de estoque"""
    if db is None:
        return jsonify({'success': False}), 500
    try:
        movimentacoes = list(db.estoque_movimentacoes.find({}).sort('data', DESCENDING).limit(100))
        
        # Enriquecer com dados do produto
        for mov in movimentacoes:
            if mov.get('produto_id'):
                produto = db.produtos.find_one({'_id': ObjectId(mov['produto_id'])})
                if produto:
                    mov['produto_nome'] = produto.get('nome', 'N/A')
                    mov['produto_sku'] = produto.get('sku', 'N/A')
        
        return jsonify({'success': True, 'movimentacoes': convert_objectid(movimentacoes)})
    except Exception as e:
        logger.error(f"Erro ao buscar movimentações: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/entrada', methods=['POST'])
@login_required
def entrada_estoque():
    """Registrar entrada de estoque (com aprovação pendente)"""
    if db is None:
        return jsonify({'success': False}), 500
    
    data = request.json
    try:
        entrada_data = {
            'produto_id': ObjectId(data['produto_id']),
            'quantidade': int(data['quantidade']),
            'custo_unitario': float(data.get('custo_unitario', 0)),
            'fornecedor': data.get('fornecedor', ''),
            'nota_fiscal': data.get('nota_fiscal', ''),
            'motivo': data.get('motivo', 'Compra de estoque'),
            'status': 'Pendente',
            'usuario': session.get('username', 'system'),
            'data': datetime.now()
        }
        
        entrada_id = db.estoque_entradas_pendentes.insert_one(entrada_data).inserted_id
        logger.info(f"✅ Entrada de estoque registrada (pendente): Produto {data['produto_id']}")

        
        return jsonify({'success': True, 'message': 'Entrada registrada! Aguardando aprovação.', 'id': str(entrada_id)})
    except Exception as e:
        logger.error(f"Erro ao registrar entrada: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/entrada/pendentes', methods=['GET'])
@login_required
def get_entradas_pendentes():
    """Listar entradas de estoque pendentes de aprovação"""
    if db is None:
        return jsonify({'success': False}), 500
    try:
        entradas = list(db.estoque_entradas_pendentes.find({'status': 'Pendente'}).sort('data', DESCENDING))
        
        # Enriquecer com dados do produto
        for entrada in entradas:
            if entrada.get('produto_id'):
                produto = db.produtos.find_one({'_id': ObjectId(entrada['produto_id'])})
                if produto:
                    entrada['produto_nome'] = produto.get('nome', 'N/A')
                    entrada['produto_sku'] = produto.get('sku', 'N/A')
                    entrada['estoque_atual'] = produto.get('estoque', 0)
        
        return jsonify({'success': True, 'entradas': convert_objectid(entradas)})
    except Exception as e:
        logger.error(f"Erro ao buscar entradas pendentes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/entrada/<id>/aprovar', methods=['POST'])
@login_required
def aprovar_entrada_estoque(id):
    """Aprovar uma entrada de estoque pendente"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        entrada = db.estoque_entradas_pendentes.find_one({'_id': ObjectId(id)})
        if not entrada:
            return jsonify({'success': False, 'message': 'Entrada não encontrada'}), 404
        
        if entrada.get('status') != 'Pendente':
            return jsonify({'success': False, 'message': 'Entrada já foi processada'}), 400
        
        # Atualizar estoque do produto
        produto = db.produtos.find_one({'_id': ObjectId(entrada['produto_id'])})
        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
        
        novo_estoque = produto.get('estoque', 0) + entrada['quantidade']
        db.produtos.update_one(
            {'_id': ObjectId(entrada['produto_id'])},
            {'$set': {'estoque': novo_estoque, 'updated_at': datetime.now()}}
        )
        
        # Registrar movimentação
        db.estoque_movimentacoes.insert_one({
            'produto_id': entrada['produto_id'],
            'tipo': 'entrada',
            'quantidade': entrada['quantidade'],
            'motivo': f"{entrada.get('motivo', 'Entrada aprovada')} (NF: {entrada.get('nota_fiscal', 'N/A')})",
            'usuario': session.get('username', 'system'),
            'data': datetime.now()
        })
        
        # Atualizar status da entrada
        db.estoque_entradas_pendentes.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'status': 'Aprovado', 'aprovado_por': session.get('username'), 'aprovado_em': datetime.now()}}
        )
        
        logger.info(f"✅ Entrada de estoque aprovada: {id}")
        return jsonify({'success': True, 'message': 'Entrada aprovada com sucesso!'})
        
    except Exception as e:
        logger.error(f"Erro ao aprovar entrada: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/entrada/<id>/rejeitar', methods=['POST'])
@login_required
def rejeitar_entrada_estoque(id):
    """Rejeitar uma entrada de estoque pendente"""
    if db is None:
        return jsonify({'success': False}), 500
    
    data = request.json
    try:
        entrada = db.estoque_entradas_pendentes.find_one({'_id': ObjectId(id)})
        if not entrada:
            return jsonify({'success': False, 'message': 'Entrada não encontrada'}), 404
        
        if entrada.get('status') != 'Pendente':
            return jsonify({'success': False, 'message': 'Entrada já foi processada'}), 400
        
        # Atualizar status da entrada
        db.estoque_entradas_pendentes.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'status': 'Rejeitado',
                'rejeitado_por': session.get('username'),
                'rejeitado_em': datetime.now(),
                'motivo_rejeicao': data.get('motivo', 'Não especificado')
            }}
        )
        
        logger.info(f"❌ Entrada de estoque rejeitada: {id}")
        return jsonify({'success': True, 'message': 'Entrada rejeitada com sucesso!'})
        
    except Exception as e:
        logger.error(f"Erro ao rejeitar entrada: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/saida', methods=['POST'])
@login_required
def saida_estoque():
    """Registrar saída manual de estoque"""
    if db is None:
        return jsonify({'success': False}), 500
    
    data = request.json
    try:
        produto = db.produtos.find_one({'_id': ObjectId(data['produto_id'])})
        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
        
        quantidade = int(data['quantidade'])
        estoque_atual = produto.get('estoque', 0)
        
        if quantidade > estoque_atual:
            return jsonify({'success': False, 'message': 'Quantidade maior que o estoque disponível'}), 400
        
        novo_estoque = estoque_atual - quantidade
        db.produtos.update_one(
            {'_id': ObjectId(data['produto_id'])},
            {'$set': {'estoque': novo_estoque, 'updated_at': datetime.now()}}
        )
        
        # Registrar movimentação
        db.estoque_movimentacoes.insert_one({
            'produto_id': ObjectId(data['produto_id']),
            'tipo': 'saida',
            'quantidade': quantidade,
            'motivo': data.get('motivo', 'Saída manual'),
            'usuario': session.get('username', 'system'),
            'data': datetime.now()
        })
        
        logger.info(f"✅ Saída de estoque registrada: Produto {data['produto_id']}")

        return jsonify({'success': True, 'message': 'Saída registrada com sucesso!'})
        
    except Exception as e:
        logger.error(f"Erro ao registrar saída: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/alertas', methods=['GET'])
@login_required
def alertas_estoque():
    """Listar produtos com estoque baixo"""
    if db is None:
        return jsonify({'success': False}), 500
    try:
        # Buscar produtos onde estoque <= estoque_minimo
        produtos_baixo_estoque = list(db.produtos.find({
            '$expr': {'$lte': ['$estoque', '$estoque_minimo']},
            'ativo': True
        }).sort('estoque', ASCENDING))
        
        alertas = []
        for produto in produtos_baixo_estoque:
            alertas.append({
                'produto_id': str(produto['_id']),
                'nome': produto.get('nome', 'N/A'),
                'sku': produto.get('sku', 'N/A'),
                'estoque_atual': produto.get('estoque', 0),
                'estoque_minimo': produto.get('estoque_minimo', 5),
                'diferenca': produto.get('estoque_minimo', 5) - produto.get('estoque', 0),
                'status': 'CRÍTICO' if produto.get('estoque', 0) == 0 else 'BAIXO'
            })
        
        return jsonify({'success': True, 'alertas': alertas, 'total': len(alertas)})
    except Exception as e:
        logger.error(f"Erro ao buscar alertas de estoque: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/relatorio', methods=['GET'])
@login_required
def relatorio_estoque():
    """Relatório completo de estoque"""
    if db is None:
        return jsonify({'success': False}), 500
    try:
        produtos = list(db.produtos.find({'ativo': True}))
        
        total_valor_estoque = sum(p.get('estoque', 0) * p.get('custo', 0) for p in produtos)
        total_valor_venda = sum(p.get('estoque', 0) * p.get('preco', 0) for p in produtos)
        total_produtos = len(produtos)
        produtos_zerados = len([p for p in produtos if p.get('estoque', 0) == 0])
        produtos_baixo_estoque = len([p for p in produtos if p.get('estoque', 0) <= p.get('estoque_minimo', 5)])
        
        relatorio = {
            'total_produtos': total_produtos,
            'produtos_zerados': produtos_zerados,
            'produtos_baixo_estoque': produtos_baixo_estoque,
            'valor_total_custo': total_valor_estoque,
            'valor_total_venda': total_valor_venda,
            'margem_potencial': total_valor_venda - total_valor_estoque
        }
        
        return jsonify({'success': True, 'relatorio': relatorio})
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de estoque: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/orcamentos', methods=['GET', 'POST'])
@login_required
def orcamentos():
    if db is None:
        return jsonify({'success': False}), 500
    
    if request.method == 'GET':
        try:
            orcs = list(db.orcamentos.find({}).sort('created_at', DESCENDING))
            return jsonify({'success': True, 'orcamentos': convert_objectid(orcs)})
        except:
            return jsonify({'success': False}), 500
    
    data = request.json
    try:
        db.clientes.update_one({'cpf': data['cliente_cpf']}, {'$set': {'cpf': data['cliente_cpf'], 'nome': data['cliente_nome'], 'email': data.get('cliente_email', ''), 'telefone': data.get('cliente_telefone', ''), 'updated_at': datetime.now()}}, upsert=True)
        
        subtotal = sum(s['total'] for s in data.get('servicos', [])) + sum(p['total'] for p in data.get('produtos', []))
        desconto_global = float(data.get('desconto_global', 0))
        desconto_valor = subtotal * (desconto_global / 100)
        total_com_desconto = subtotal - desconto_valor
        cashback_perc = float(data.get('cashback_perc', 0))
        cashback_valor = total_com_desconto * (cashback_perc / 100)
        
        ultimo = db.orcamentos.find_one(sort=[('numero', DESCENDING)])
        numero = (ultimo['numero'] + 1) if ultimo and 'numero' in ultimo else 1
        
        orc_id = db.orcamentos.insert_one({'numero': numero, 'cliente_cpf': data['cliente_cpf'], 'cliente_nome': data['cliente_nome'], 'cliente_email': data.get('cliente_email', ''), 'cliente_telefone': data.get('cliente_telefone', ''), 'servicos': data.get('servicos', []), 'produtos': data.get('produtos', []), 'subtotal': subtotal, 'desconto_global': desconto_global, 'desconto_valor': desconto_valor, 'total_com_desconto': total_com_desconto, 'cashback_perc': cashback_perc, 'cashback_valor': cashback_valor, 'total_final': total_com_desconto, 'pagamento': data.get('pagamento', {}), 'status': data.get('status', 'Pendente'), 'created_at': datetime.now(), 'user_id': session['user_id']}).inserted_id
        
        for produto in data.get('produtos', []):
            if 'id' in produto:
                prod = db.produtos.find_one({'_id': ObjectId(produto['id'])})
                if prod:
                    novo_estoque = prod.get('estoque', 0) - produto.get('qtd', 1)
                    db.produtos.update_one({'_id': ObjectId(produto['id'])}, {'$set': {'estoque': novo_estoque}})
                    db.estoque_movimentacoes.insert_one({'produto_id': ObjectId(produto['id']), 'tipo': 'saida', 'quantidade': produto.get('qtd', 1), 'motivo': f"Orçamento #{numero}", 'usuario': session.get('username'), 'data': datetime.now()})
        
        if data.get('status') == 'Aprovado' and data.get('cliente_email'):
            send_email(data['cliente_email'], data['cliente_nome'], f'✅ Contrato BIOMA #{numero}', f'<div style="font-family: Arial; padding: 40px; background: #f9fafb;"><div style="background: white; padding: 40px; border-radius: 15px;"><h1 style="color: #10B981;">✅ Contrato Aprovado!</h1><h2>Olá {data["cliente_nome"]},</h2><p>Contrato <strong>#{numero}</strong> aprovado!</p><h3 style="color: #7C3AED;">Total: R$ {total_com_desconto:.2f}</h3><p>Cashback: R$ {cashback_valor:.2f}</p><p>Pagamento: {data.get("pagamento", {}).get("tipo", "N/A")}</p><p style="margin-top: 30px;">Obrigado!</p><p><strong>BIOMA Uberaba</strong></p></div></div>')
        
        return jsonify({'success': True, 'numero': numero, 'id': str(orc_id)})
    except Exception as e:
        logger.error(f"❌ Orçamento error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/orcamentos/<id>', methods=['DELETE'])
@login_required
def delete_orcamento(id):
    if db is None:
        return jsonify({'success': False}), 500
    try:
        result = db.orcamentos.delete_one({'_id': ObjectId(id)})
        return jsonify({'success': result.deleted_count > 0})
    except:
        return jsonify({'success': False}), 500

@app.route('/api/orcamentos/<id>', methods=['GET'])
@login_required
def get_orcamento(id):
    """Visualizar um orçamento específico"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    try:
        orcamento = db.orcamentos.find_one({'_id': ObjectId(id)})
        if not orcamento:
            return jsonify({'success': False, 'message': 'Orçamento não encontrado'}), 404
        return jsonify({'success': True, 'orcamento': convert_objectid(orcamento)})
    except Exception as e:
        logger.error(f"Erro ao buscar orçamento: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/orcamentos/<id>', methods=['PUT'])
@login_required
def update_orcamento(id):
    """Editar um orçamento existente"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    data = request.json
    try:
        # Verificar se o orçamento existe
        orcamento_existente = db.orcamentos.find_one({'_id': ObjectId(id)})
        if not orcamento_existente:
            return jsonify({'success': False, 'message': 'Orçamento não encontrado'}), 404
        
        # Atualizar cliente se fornecido
        if data.get('cliente_cpf'):
            db.clientes.update_one(
                {'cpf': data['cliente_cpf']},
                {'$set': {
                    'cpf': data['cliente_cpf'],
                    'nome': data.get('cliente_nome', ''),
                    'email': data.get('cliente_email', ''),
                    'telefone': data.get('cliente_telefone', ''),
                    'updated_at': datetime.now()
                }},
                upsert=True
            )
        
        # Recalcular valores
        subtotal = sum(s.get('total', 0) for s in data.get('servicos', [])) + sum(p.get('total', 0) for p in data.get('produtos', []))
        desconto_global = float(data.get('desconto_global', 0))
        desconto_valor = subtotal * (desconto_global / 100)
        total_com_desconto = subtotal - desconto_valor
        cashback_perc = float(data.get('cashback_perc', 0))
        cashback_valor = total_com_desconto * (cashback_perc / 100)
        
        # Atualizar orçamento
        update_data = {
            'cliente_cpf': data.get('cliente_cpf', orcamento_existente.get('cliente_cpf')),
            'cliente_nome': data.get('cliente_nome', orcamento_existente.get('cliente_nome')),
            'cliente_email': data.get('cliente_email', orcamento_existente.get('cliente_email')),
            'cliente_telefone': data.get('cliente_telefone', orcamento_existente.get('cliente_telefone')),
            'servicos': data.get('servicos', orcamento_existente.get('servicos', [])),
            'produtos': data.get('produtos', orcamento_existente.get('produtos', [])),
            'subtotal': subtotal,
            'desconto_global': desconto_global,
            'desconto_valor': desconto_valor,
            'total_com_desconto': total_com_desconto,
            'cashback_perc': cashback_perc,
            'cashback_valor': cashback_valor,
            'total_final': total_com_desconto,
            'pagamento': data.get('pagamento', orcamento_existente.get('pagamento', {})),
            'status': data.get('status', orcamento_existente.get('status', 'Pendente')),
            'updated_at': datetime.now()
        }
        
        db.orcamentos.update_one({'_id': ObjectId(id)}, {'$set': update_data})
        
        logger.info(f"✅ Orçamento #{orcamento_existente.get('numero')} atualizado")
        return jsonify({'success': True, 'message': 'Orçamento atualizado com sucesso'})
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar orçamento: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/upload/imagem', methods=['POST'])
@login_required
def upload_imagem():
    """Upload de imagem (foto de perfil ou logo)"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        import base64
        data = request.json
        
        if not data.get('image_data'):
            return jsonify({'success': False, 'message': 'Imagem não fornecida'}), 400
        
        # Extrair dados da imagem base64
        image_data = data['image_data']
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decodificar e salvar
        image_bytes = base64.b64decode(image_data)
        tipo = data.get('tipo', 'profissional')  # profissional ou logo
        filename = f"{tipo}_{datetime.now().timestamp()}.png"
        
        # Salvar no banco de dados como base64 (simplificado)
        db.imagens.insert_one({
            'tipo': tipo,
            'filename': filename,
            'data': image_data,
            'uploaded_by': session.get('username'),
            'uploaded_at': datetime.now()
        })
        
        logger.info(f"✅ Imagem uploaded: {filename}")
        return jsonify({
            'success': True,
            'url': f'/api/imagem/{filename}',
            'filename': filename,
            'data_url': f'data:image/png;base64,{image_data}'
        })
        
    except Exception as e:
        logger.error(f"Erro ao fazer upload de imagem: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/imagem/<filename>')
def get_imagem(filename):
    """Recuperar uma imagem"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        import base64
        imagem = db.imagens.find_one({'filename': filename})
        if not imagem:
            return jsonify({'success': False, 'message': 'Imagem não encontrada'}), 404
        
        # Retornar a imagem como base64
        return jsonify({'success': True, 'data': imagem['data']})
    except Exception as e:
        logger.error(f"Erro ao recuperar imagem: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/busca/global')
@login_required
def busca_global():
    """Busca global em todo o sistema"""
    if db is None:
        return jsonify({'success': False}), 500
    
    termo = request.args.get('termo', '').strip()
    if len(termo) < 2:
        return jsonify({'success': True, 'resultados': []})
    
    try:
        regex = {'$regex': termo, '$options': 'i'}
        resultados = {
            'clientes': [],
            'produtos': [],
            'servicos': [],
            'profissionais': [],
            'orcamentos': []
        }
        
        # Buscar clientes
        clientes = list(db.clientes.find({
            '$or': [
                {'nome': regex},
                {'cpf': regex},
                {'email': regex}
            ]
        }).limit(5))
        for c in clientes:
            resultados['clientes'].append({
                'id': str(c['_id']),
                'tipo': 'Cliente',
                'nome': c.get('nome', ''),
                'detalhe': f"CPF: {c.get('cpf', '')}"
            })
        
        # Buscar produtos
        produtos = list(db.produtos.find({
            '$or': [
                {'nome': regex},
                {'sku': regex},
                {'marca': regex}
            ],
            'ativo': True
        }).limit(5))
        for p in produtos:
            resultados['produtos'].append({
                'id': str(p['_id']),
                'tipo': 'Produto',
                'nome': p.get('nome', ''),
                'detalhe': f"SKU: {p.get('sku', '')} - R$ {p.get('preco', 0):.2f}"
            })
        
        # Buscar serviços
        servicos = list(db.servicos.find({
            '$or': [
                {'nome': regex},
                {'sku': regex}
            ],
            'ativo': True
        }).limit(5))
        for s in servicos:
            resultados['servicos'].append({
                'id': str(s['_id']),
                'tipo': 'Serviço',
                'nome': s.get('nome', ''),
                'detalhe': f"{s.get('tamanho', '')} - R$ {s.get('preco', 0):.2f}"
            })
        
        # Buscar profissionais
        profissionais = list(db.profissionais.find({
            '$or': [
                {'nome': regex},
                {'cpf': regex}
            ],
            'ativo': True
        }).limit(5))
        for p in profissionais:
            resultados['profissionais'].append({
                'id': str(p['_id']),
                'tipo': 'Profissional',
                'nome': p.get('nome', ''),
                'detalhe': p.get('especialidade', 'Profissional')
            })
        
        # Buscar orçamentos (por número ou nome do cliente)
        orcamentos = list(db.orcamentos.find({
            '$or': [
                {'cliente_nome': regex},
                {'numero': {'$regex': str(termo), '$options': 'i'}}
            ]
        }).sort('created_at', DESCENDING).limit(5))
        for o in orcamentos:
            resultados['orcamentos'].append({
                'id': str(o['_id']),
                'tipo': 'Orçamento',
                'nome': f"#{o.get('numero', '')} - {o.get('cliente_nome', '')}",
                'detalhe': f"R$ {o.get('total_final', 0):.2f} - {o.get('status', 'Pendente')}"
            })
        
        return jsonify({'success': True, 'resultados': resultados})
    except Exception as e:
        logger.error(f"Erro na busca global: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/comissao/calcular', methods=['POST'])
@login_required
def calcular_comissao():
    """Calcular comissões de profissional e assistente para um orçamento"""
    if db is None:
        return jsonify({'success': False}), 500
    
    data = request.json
    try:
        orcamento_id = data.get('orcamento_id')
        if not orcamento_id:
            return jsonify({'success': False, 'message': 'ID do orçamento não fornecido'}), 400
        
        orcamento = db.orcamentos.find_one({'_id': ObjectId(orcamento_id)})
        if not orcamento:
            return jsonify({'success': False, 'message': 'Orçamento não encontrado'}), 404
        
        comissoes = []
        total_comissoes = 0
        
        for servico in orcamento.get('servicos', []):
            if servico.get('profissional_id'):
                profissional = db.profissionais.find_one({'_id': ObjectId(servico['profissional_id'])})
                if profissional:
                    valor_servico = servico.get('total', 0)
                    comissao_perc = profissional.get('comissao_perc', 0)
                    comissao_valor = valor_servico * (comissao_perc / 100)
                    
                    comissao_info = {
                        'profissional_id': str(profissional['_id']),
                        'profissional_nome': profissional.get('nome', ''),
                        'servico': servico.get('nome', ''),
                        'valor_servico': valor_servico,
                        'comissao_perc': comissao_perc,
                        'comissao_valor': comissao_valor
                    }
                    
                    # Calcular comissão do assistente (se existir)
                    if profissional.get('assistente_id'):
                        assistente = db.profissionais.find_one({'_id': ObjectId(profissional['assistente_id'])})
                        if assistente:
                            comissao_assistente_perc = profissional.get('comissao_assistente_perc', 0)
                            # Assistente ganha X% da comissão do profissional
                            comissao_assistente_valor = comissao_valor * (comissao_assistente_perc / 100)
                            
                            comissao_info['assistente'] = {
                                'assistente_id': str(assistente['_id']),
                                'assistente_nome': assistente.get('nome', ''),
                                'comissao_perc': comissao_assistente_perc,
                                'comissao_valor': comissao_assistente_valor
                            }
                            
                            total_comissoes += comissao_assistente_valor
                    
                    comissoes.append(comissao_info)
                    total_comissoes += comissao_valor
        
        return jsonify({
            'success': True,
            'orcamento_numero': orcamento.get('numero'),
            'comissoes': comissoes,
            'total_comissoes': total_comissoes
        })
        
    except Exception as e:
        logger.error(f"Erro ao calcular comissões: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/assistentes', methods=['GET', 'POST'])
@login_required
def assistentes():
    """Gerenciar assistentes (que podem não ser profissionais ativos)"""
    if db is None:
        return jsonify({'success': False}), 500
    
    if request.method == 'GET':
        try:
            # Listar todos os assistentes
            assistentes_list = list(db.assistentes.find({}).sort('nome', ASCENDING))
            return jsonify({'success': True, 'assistentes': convert_objectid(assistentes_list)})
        except:
            return jsonify({'success': False}), 500
    
    data = request.json
    try:
        assistente_data = {
            'nome': data['nome'],
            'cpf': data.get('cpf', ''),
            'email': data.get('email', ''),
            'telefone': data.get('telefone', ''),
            'ativo': True,
            'created_at': datetime.now()
        }
        db.assistentes.insert_one(assistente_data)
        return jsonify({'success': True})
    except:
        return jsonify({'success': False}), 500

@app.route('/api/assistentes/<id>', methods=['DELETE'])
@login_required
def delete_assistente(id):
    if db is None:
        return jsonify({'success': False}), 500
    try:
        result = db.assistentes.delete_one({'_id': ObjectId(id)})
        return jsonify({'success': result.deleted_count > 0})
    except:
        return jsonify({'success': False}), 500

# --- INÍCIO DA SEÇÃO MODIFICADA ---
class GradientHeader(Flowable):
    """Um cabeçalho com fundo em gradiente."""
    def __init__(self, width, text):
        Flowable.__init__(self)
        self.width = width
        self.text = text
        self.height = 1.5*cm

    def draw(self):
        c = self.canv
        c.saveState()
        start_color = HexColor('#7C3AED')
        end_color = HexColor('#EC4899')
        steps = 100
        for i in range(steps):
            ratio = i / float(steps)
            r = start_color.red * (1 - ratio) + end_color.red * ratio
            g = start_color.green * (1 - ratio) + end_color.green * ratio
            b = start_color.blue * (1 - ratio) + end_color.blue * ratio
            c.setFillColorRGB(r, g, b)
            c.rect((self.width / steps) * i, 0, self.width / steps, self.height, stroke=0, fill=1)
        c.setFont('Helvetica-Bold', 36)
        c.setFillColor(white)
        c.drawCentredString(self.width / 2, self.height / 2 - (0.5*cm), self.text)
        c.restoreState()

class HRFlowable(Flowable):
    """Linha horizontal com cor customizada."""
    def __init__(self, width, thickness=1, color=black):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.color = color

    def draw(self):
        self.canv.saveState()
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)
        self.canv.restoreState()

def format_date_pt_br(dt):
    """Formata a data para Português-BR manualmente para evitar problemas de locale."""
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    return f"{dt.day} de {meses[dt.month - 1]} de {dt.year}"

@app.route('/api/orcamento/<id>/pdf')
@login_required
def gerar_pdf_orcamento(id):
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    try:
        orcamento = db.orcamentos.find_one({'_id': ObjectId(id)})
        if not orcamento:
            return jsonify({'success': False, 'message': 'Orçamento não encontrado'}), 404

        buffer = io.BytesIO()
        doc_width, doc_height = A4
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=1.5*cm, bottomMargin=2.5*cm)

        COLOR_PRIMARY = HexColor('#7C3AED')
        COLOR_SECONDARY = HexColor('#6B7280')
        COLOR_LIGHT_BG = HexColor('#F9FAFB')
        COLOR_WHITE = HexColor('#FFFFFF')
        
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='MainTitle', fontName='Helvetica-Bold', fontSize=20, textColor=COLOR_PRIMARY, spaceAfter=18))
        styles.add(ParagraphStyle(name='SubTitle', fontName='Helvetica', fontSize=10, textColor=COLOR_SECONDARY, spaceAfter=24))
        styles.add(ParagraphStyle(name='SectionTitle', fontName='Helvetica-Bold', fontSize=10, textColor=white))
        styles.add(ParagraphStyle(name='Body', fontName='Helvetica', fontSize=9, leading=14))
        styles.add(ParagraphStyle(name='BodyRight', fontName='Helvetica', fontSize=9, leading=14, alignment=TA_RIGHT))
        styles.add(ParagraphStyle(name='Clause', fontName='Helvetica', fontSize=8, leading=14, alignment=TA_JUSTIFY, leftIndent=12))
        styles.add(ParagraphStyle(name='Signature', fontName='Helvetica', fontSize=9, alignment=TA_CENTER))

        story = []
        
        story.append(GradientHeader(doc_width - 4*cm, "BIOMA"))
        story.append(Spacer(1, 1.5*cm))
        story.append(Paragraph("Contrato de Prestação de Serviços", styles['MainTitle']))
        story.append(Paragraph(
            "Pelo presente instrumento particular, as 'Partes' resolvem celebrar o presente 'Contrato', de acordo com as cláusulas e condições a seguir.", 
            styles['SubTitle']
        ))

        data_contrato = orcamento.get('created_at', datetime.now())
        info_data = [
            [Paragraph('<b>NÚMERO DO CONTRATO</b>', styles['Body']), Paragraph(f"#{orcamento.get('numero', 'N/A')}", styles['Body'])],
            [Paragraph('<b>DATA DE EMISSÃO</b>', styles['Body']), Paragraph(format_date_pt_br(data_contrato), styles['Body'])]
        ]
        story.append(Table(info_data, colWidths=[5*cm, '*'], style=[('VALIGN', (0,0), (-1,-1), 'TOP')]))
        story.append(Spacer(1, 1*cm))

        story.append(HRFlowable(doc_width - 4*cm, color=HexColor('#E5E7EB'), thickness=1))
        story.append(Spacer(1, 1*cm))

        contratante_details = f"""
            <b>Nome:</b> {orcamento.get('cliente_nome', 'N/A')}<br/>
            <b>CPF:</b> {orcamento.get('cliente_cpf', 'N/A')}<br/>
            <b>Telefone:</b> {orcamento.get('cliente_telefone', 'N/A')}<br/>
            <b>E-mail:</b> {orcamento.get('cliente_email', 'N/A')}
        """
        contratada_details = f"""
            <b>Razão Social:</b> BIOMA UBERABA<br/>
            <b>CNPJ:</b> 49.470.937/0001-10<br/>
            <b>Endereço:</b> Av. Santos Dumont 3110, Santa Maria, Uberaba/MG<br/>
            <b>Contato:</b> (34) 99235-5890
        """
        partes_data = [
            [Paragraph('<b>CONTRATANTE</b>', styles['Body']), Paragraph('<b>CONTRATADA</b>', styles['Body'])],
            [Paragraph(contratante_details, styles['Body']), Paragraph(contratada_details, styles['Body'])]
        ]
        partes_table = Table(partes_data, colWidths=['*', '*'], hAlign='LEFT')
        partes_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'), ('LINEBELOW', (0,0), (-1,0), 1, COLOR_PRIMARY),
            ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ]))
        story.append(partes_table)
        story.append(Spacer(1, 1.5*cm))

        story.append(Paragraph("SERVIÇOS E PRODUTOS CONTRATADOS", styles['MainTitle']))
        table_header = [Paragraph(c, styles['SectionTitle']) for c in ['Item', 'Descrição', 'Qtd', 'Vl. Unit.', 'Total']]
        items_data = [table_header]
        all_items = orcamento.get('servicos', []) + orcamento.get('produtos', [])
        
        table_style_commands = [
            ('BACKGROUND', (0,0), (-1,0), COLOR_PRIMARY), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 10), ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('GRID', (0,0), (-1,-1), 1, COLOR_PRIMARY),
            ('ALIGN', (2,1), (-1,-1), 'RIGHT'), # Alinha colunas numéricas à direita
            ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]

        for i, item in enumerate(all_items):
            desc = f"{item.get('nome', '')} {item.get('tamanho', '')}".strip() if 'servico' in item.get('id', '') else f"{item.get('nome', '')} {item.get('marca', '')}".strip()
            items_data.append([
                Paragraph(str(i+1), styles['Body']), Paragraph(desc, styles['Body']),
                Paragraph(str(item.get('qtd', 1)), styles['BodyRight']), 
                Paragraph(f"R$ {item.get('preco_unit', 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), styles['BodyRight']),
                Paragraph(f"R$ {item.get('total', 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), styles['BodyRight']),
            ])
            # Adiciona estilo de zebra (cores alternadas)
            if i % 2 == 0:
                table_style_commands.append(('BACKGROUND', (0, i + 1), (-1, i + 1), COLOR_LIGHT_BG))
            else:
                table_style_commands.append(('BACKGROUND', (0, i + 1), (-1, i + 1), COLOR_WHITE))

        items_table = Table(items_data, colWidths=[1.5*cm, '*', 1.5*cm, 3*cm, 3*cm], repeatRows=1)
        items_table.setStyle(TableStyle(table_style_commands))
        story.append(items_table)
        story.append(Spacer(1, 1*cm))

        subtotal = orcamento.get('subtotal', 0)
        desconto = orcamento.get('desconto_valor', 0)
        total = orcamento.get('total_final', 0)
        pag_tipo = orcamento.get('pagamento', {}).get('tipo', 'Não especificado')
        
        valores_data = [
            [Paragraph('Subtotal:', styles['Body']), Paragraph(f'R$ {subtotal:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."), styles['BodyRight'])],
            [Paragraph('Desconto Global:', styles['Body']), Paragraph(f'R$ {desconto:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."), styles['BodyRight'])],
            ['', HRFlowable(8*cm, color=COLOR_PRIMARY, thickness=1.5)],
            [Paragraph('<b>Valor Total a Pagar:</b>', styles['Body']), Paragraph(f'<b>R$ {total:,.2f}</b>'.replace(",", "X").replace(".", ",").replace("X", "."), styles['BodyRight'])],
            [Paragraph('Forma de Pagamento:', styles['Body']), Paragraph(pag_tipo, styles['BodyRight'])],
        ]
        
        # Tabela para alinhar o bloco de valores à direita
        container_valores = Table([[Table(valores_data, colWidths=[4*cm, 4*cm])]], colWidths=[doc_width-4*cm])
        container_valores.setStyle(TableStyle([('ALIGN', (0,0), (0,0), 'RIGHT')]))
        story.append(container_valores)
        story.append(Spacer(1, 1.5*cm))

        story.append(Paragraph("DISPOSIÇÕES GERAIS E CLÁUSULAS", styles['MainTitle']))
        clausulas = [
            "O Contrato tem por objeto a prestação de serviços acima descritos, pela Contratada à Contratante, mediante agendamento prévio. A Contratada utilizará produtos com ingredientes naturais para a saúde dos cabelos, de alta qualidade, que serão manipulados dentro das normas de higiene e limpeza exigidas pela Vigilância Sanitária.",
            "A Contratante declara e está ciente que (i) os serviços têm caráter pessoal e são intransferíveis; (ii) só poderá alterar os Serviços contratados com a anuência da Contratada e desde que a utilização seja no prazo originalmente contratado; (iii) não tem nenhum impedimento médico e/ou alergias que impeçam de realizar os serviços contratados; (iv) escolheu os tratamentos de acordo com o seu tipo de cabelo; (v) concorda em realizar os tratamentos com a frequência indicada pela Contratada; e (vi) o resultado pretendido depende do respeito à frequência indicada pela Contratada.",
            "Os serviços deverão ser utilizados em conformidade com o prazo de 18 (dezoito) meses e a Contratante está ciente de que não haverá prorrogação do prazo previsto para a utilização dos serviços, ou seja, ao final de 18 (dezoito) meses, o Contrato será extinto e a Contratante não terá direito ao reembolso de tratamentos não realizados no prazo contratual.",
            "A Contratante poderá desistir dos serviços no prazo de até 90 (noventa) dias a contar da assinatura deste Contrato e, neste caso, está de acordo com a restituição do valor equivalente a 80% (oitenta por cento) dos tratamentos não realizados, no prazo de até 5 (cinco) dias úteis da desistência. Eventuais descontos ou promoções nos valores dos serviços e/ou tratamentos não serão reembolsáveis.",
            "No caso de devolução de valor pago por cartão de crédito, o cancelamento será efetuado junto à administradora do seu cartão e o estorno poderá ocorrer em até 2 (duas) faturas posteriores de acordo com procedimentos internos da operadora do cartão de crédito, ou outro prazo definido pela administradora do cartão de crédito, ou, a exclusivo arbítrio da Contratada, mediante transferência direta do valor equivalente ao reembolso.",
            "Na hipótese de responsabilidade civil da Contratada, independentemente da natureza do dano, fica desde já limitada a responsabilidade da Contratada ao valor máximo equivalente a 2 (duas) sessões de tratamento dos serviços.",
            "No caso de alergias decorrentes dos produtos utilizados pela Contratada, a Contratante poderá optar pela suspensão dos serviços com a retomada após o reestabelecimento de sua saúde, ou pela concessão de crédito do valor remanescente em outros serviços junto à Contratada. A Contratada não é responsável por qualquer perda, independentemente do valor, incluindo danos diretos, indiretos, à imagem, lucros cessantes e/ou morais que se tornem exigíveis em decorrência de eventual alergia.",
            "As Partes se comprometem a tratar apenas os dados pessoais estritamente necessários para atingir as finalidades específicas do objeto do Contrato, em cumprimento ao disposto na Lei nº 13.709/2018 (\"LGPD\") e na regulamentação aplicável.",
            "Fica eleito o Foro da Comarca de UBERABA, Estado de MINAS GERAIS, como o competente para dirimir as dúvidas e controvérsias decorrentes do presente Contrato, com renúncia a qualquer outro, por mais privilegiado que seja.",
            "Este Contrato poderá ser assinado e entregue eletronicamente e terá a mesma validade e efeitos de um documento original com assinaturas físicas."
        ]
        for i, clausula in enumerate(clausulas):
            story.append(Paragraph(f"<b>{i+1}.</b> {clausula}", styles['Clause']))
            story.append(Spacer(1, 0.4*cm))
        
        story.append(PageBreak())
        story.append(Paragraph("ASSINATURAS", styles['MainTitle']))
        story.append(Spacer(1, 4*cm))

        assinatura_contratante = Paragraph("________________________________________<br/><b>CONTRATANTE</b><br/>" + orcamento.get('cliente_nome', 'N/A'), styles['Signature'])
        assinatura_contratada = Paragraph("________________________________________<br/><b>CONTRATADA</b><br/>BIOMA UBERABA", styles['Signature'])
        
        assinaturas_table = Table([[assinatura_contratante, assinatura_contratada]], colWidths=['*', '*'])
        story.append(assinaturas_table)
        
        def on_each_page(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(COLOR_SECONDARY)
            page_num = canvas.getPageNumber()
            canvas.drawCentredString(doc_width/2, 1.5*cm, f"Página {page_num} | Contrato BIOMA Uberaba")
            canvas.restoreState()

        doc.build(story, onFirstPage=on_each_page, onLaterPages=on_each_page)
        
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'contrato_bioma_{orcamento.get("numero")}.pdf')
        
    except Exception as e:
        logger.error(f"❌ PDF error: {e}")
        return jsonify({'success': False, 'message': f'Erro interno ao gerar PDF: {e}'}), 500

# --- FIM DA SEÇÃO MODIFICADA ---


@app.route('/api/contratos')
@login_required
def contratos():
    if db is None:
        return jsonify({'success': False}), 500
    try:
        contratos_list = list(db.orcamentos.find({'status': 'Aprovado'}).sort('created_at', DESCENDING))
        return jsonify({'success': True, 'contratos': convert_objectid(contratos_list)})
    except:
        return jsonify({'success': False}), 500

@app.route('/api/agendamentos', methods=['GET', 'POST'])
@login_required
def agendamentos():
    if db is None:
        return jsonify({'success': False}), 500
    if request.method == 'GET':
        try:
            agora = datetime.now()
            agends = list(db.agendamentos.find({'data': {'$gte': agora}}).sort('data', ASCENDING).limit(10))
            return jsonify({'success': True, 'agendamentos': convert_objectid(agends)})
        except:
            return jsonify({'success': False}), 500
    data = request.json
    try:
        data_agendamento = datetime.fromisoformat(data['data'].replace('Z', '+00:00'))
        agend_id = db.agendamentos.insert_one({'cliente_id': data.get('cliente_id'), 'cliente_nome': data.get('cliente_nome'), 'cliente_telefone': data.get('cliente_telefone'), 'profissional_id': data.get('profissional_id'), 'profissional_nome': data.get('profissional_nome'), 'servico_id': data.get('servico_id'), 'servico_nome': data.get('servico_nome'), 'data': data_agendamento, 'horario': data['horario'], 'status': 'confirmado', 'created_at': datetime.now()}).inserted_id
        return jsonify({'success': True, 'id': str(agend_id)})
    except:
        return jsonify({'success': False}), 500

@app.route('/api/agendamentos/horarios-disponiveis', methods=['GET'])
@login_required
def horarios_disponiveis():
    """Verificar horários disponíveis para uma data específica"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        data_str = request.args.get('data')
        profissional_id = request.args.get('profissional_id')
        
        if not data_str:
            return jsonify({'success': False, 'message': 'Data não fornecida'}), 400
        
        # Converter a data
        data = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
        data_inicio = data.replace(hour=0, minute=0, second=0)
        data_fim = data.replace(hour=23, minute=59, second=59)
        
        # Buscar agendamentos do dia
        query = {'data': {'$gte': data_inicio, '$lte': data_fim}}
        if profissional_id:
            query['profissional_id'] = profissional_id
        
        agendamentos = list(db.agendamentos.find(query))
        horarios_ocupados = [a.get('horario') for a in agendamentos if a.get('horario')]
        
        # Gerar horários disponíveis (08:00 - 18:00)
        horarios_todos = []
        for hora in range(8, 18):
            for minuto in [0, 30]:
                horarios_todos.append(f"{hora:02d}:{minuto:02d}")
        
        horarios_disponiveis = [h for h in horarios_todos if h not in horarios_ocupados]
        
        return jsonify({
            'success': True,
            'horarios_disponiveis': horarios_disponiveis,
            'horarios_ocupados': horarios_ocupados,
            'total_slots': len(horarios_todos),
            'slots_disponiveis': len(horarios_disponiveis)
        })
    except Exception as e:
        logger.error(f"Erro ao buscar horários disponíveis: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/agendamentos/mapa-calor', methods=['GET'])
@login_required
def mapa_calor_agendamentos():
    """Gerar mapa de calor de agendamentos e orçamentos"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        # Últimos 30 dias
        data_inicio = datetime.now() - timedelta(days=30)
        data_fim = datetime.now()
        
        # Buscar agendamentos
        agendamentos = list(db.agendamentos.find({
            'created_at': {'$gte': data_inicio, '$lte': data_fim}
        }))
        
        # Buscar orçamentos
        orcamentos = list(db.orcamentos.find({
            'created_at': {'$gte': data_inicio, '$lte': data_fim}
        }))
        
        # Agrupar por dia
        mapa_calor = {}
        
        for agend in agendamentos:
            data_agend = agend.get('created_at', datetime.now())
            dia = data_agend.strftime('%Y-%m-%d')
            if dia not in mapa_calor:
                mapa_calor[dia] = {'agendamentos': 0, 'orcamentos': 0, 'total': 0}
            mapa_calor[dia]['agendamentos'] += 1
            mapa_calor[dia]['total'] += 1
        
        for orc in orcamentos:
            data_orc = orc.get('created_at', datetime.now())
            dia = data_orc.strftime('%Y-%m-%d')
            if dia not in mapa_calor:
                mapa_calor[dia] = {'agendamentos': 0, 'orcamentos': 0, 'total': 0}
            mapa_calor[dia]['orcamentos'] += 1
            mapa_calor[dia]['total'] += 1
        
        # Converter para lista ordenada
        mapa_lista = [
            {
                'data': dia,
                'agendamentos': dados['agendamentos'],
                'orcamentos': dados['orcamentos'],
                'total': dados['total']
            }
            for dia, dados in sorted(mapa_calor.items())
        ]
        
        return jsonify({'success': True, 'mapa_calor': mapa_lista})
    except Exception as e:
        logger.error(f"Erro ao gerar mapa de calor: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/agendamentos/<id>', methods=['DELETE'])
@login_required
def delete_agendamento(id):
    """Deletar um agendamento"""
    if db is None:
        return jsonify({'success': False}), 500
    try:
        result = db.agendamentos.delete_one({'_id': ObjectId(id)})
        return jsonify({'success': result.deleted_count > 0})
    except:
        return jsonify({'success': False}), 500

@app.route('/api/fila', methods=['GET', 'POST'])
@login_required
def fila():
    if db is None:
        return jsonify({'success': False}), 500
    if request.method == 'GET':
        try:
            fila_list = list(db.fila_atendimento.find({'status': {'$in': ['aguardando', 'atendendo']}}).sort('created_at', ASCENDING))
            return jsonify({'success': True, 'fila': convert_objectid(fila_list)})
        except:
            return jsonify({'success': False}), 500
    data = request.json
    try:
        total = db.fila_atendimento.count_documents({'status': {'$in': ['aguardando', 'atendendo']}})
        db.fila_atendimento.insert_one({'cliente_nome': data['cliente_nome'], 'cliente_telefone': data['cliente_telefone'], 'servico': data.get('servico', ''), 'profissional': data.get('profissional', ''), 'posicao': total + 1, 'status': 'aguardando', 'created_at': datetime.now()})
        return jsonify({'success': True, 'posicao': total + 1})
    except:
        return jsonify({'success': False}), 500

@app.route('/api/fila/<id>', methods=['DELETE'])
@login_required
def delete_fila(id):
    if db is None:
        return jsonify({'success': False}), 500
    try:
        result = db.fila_atendimento.delete_one({'_id': ObjectId(id)})
        return jsonify({'success': result.deleted_count > 0})
    except:
        return jsonify({'success': False}), 500

@app.route('/api/estoque/alerta')
@login_required
def estoque_alerta():
    if db is None:
        return jsonify({'success': False}), 500
    try:
        produtos = list(db.produtos.find({'$expr': {'$lte': ['$estoque', '$estoque_minimo']}}))
        return jsonify({'success': True, 'produtos': convert_objectid(produtos)})
    except:
        return jsonify({'success': False}), 500

@app.route('/api/estoque/movimentacao', methods=['POST'])
@login_required
def estoque_movimentacao():
    if db is None:
        return jsonify({'success': False}), 500
    data = request.json
    try:
        produto = db.produtos.find_one({'_id': ObjectId(data['produto_id'])})
        if not produto:
            return jsonify({'success': False})
        qtd = int(data['quantidade'])
        tipo = data['tipo']
        novo_estoque = produto.get('estoque', 0)
        if tipo == 'entrada':
            novo_estoque += qtd
        else:
            novo_estoque -= qtd
        db.produtos.update_one({'_id': ObjectId(data['produto_id'])}, {'$set': {'estoque': novo_estoque}})
        db.estoque_movimentacoes.insert_one({'produto_id': ObjectId(data['produto_id']), 'tipo': tipo, 'quantidade': qtd, 'motivo': data.get('motivo', ''), 'usuario': session.get('username'), 'data': datetime.now()})
        return jsonify({'success': True})
    except:
        return jsonify({'success': False}), 500

@app.route('/api/importar', methods=['POST'])
@login_required
def importar():
    if db is None:
        return jsonify({'success': False}), 500
    if 'file' not in request.files:
        return jsonify({'success': False}), 400
    file = request.files['file']
    tipo = request.form.get('tipo', 'produtos')
    if not file.filename:
        return jsonify({'success': False}), 400
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in ['csv', 'xlsx', 'xls']:
        return jsonify({'success': False}), 400
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        count_success = 0
        count_error = 0
        rows = []
        if ext == 'csv':
            encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as csvfile:
                        rows = list(csv.DictReader(csvfile))
                        break
                except:
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
        if tipo == 'produtos':
            for idx, row in enumerate(rows, 1):
                try:
                    r = {k.lower().strip(): v for k, v in row.items() if k and v is not None}
                    if not r or all(not v for v in r.values()):
                        continue
                    nome = None
                    for col in ['nome', 'produto', 'name']:
                        if col in r and r[col]:
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
                    for col in ['sku', 'codigo']:
                        if col in r and r[col]:
                            sku = str(r[col]).strip()
                            break
                    preco = 0.0
                    for col in ['preco', 'preço', 'price', 'valor']:
                        if col in r and r[col]:
                            try:
                                val = str(r[col]).replace('R$', '').strip()
                                if ',' in val:
                                    val = val.replace(',', '.')
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
                    db.produtos.insert_one({'nome': nome, 'marca': marca, 'sku': sku, 'preco': preco, 'custo': custo, 'estoque': estoque, 'estoque_minimo': 5, 'categoria': categoria, 'ativo': True, 'created_at': datetime.now()})
                    count_success += 1
                except:
                    count_error += 1
        elif tipo == 'servicos':
            # Importação de serviços
            for idx, row in enumerate(rows, 1):
                try:
                    r = {k.lower().strip(): v for k, v in row.items() if k and v is not None}
                    if not r or all(not v for v in r.values()):
                        continue
                    
                    # Nome do serviço
                    nome = None
                    for col in ['nome', 'servico', 'name']:
                        if col in r and r[col]:
                            nome = str(r[col]).strip()
                            break
                    if not nome or len(nome) < 2:
                        count_error += 1
                        continue
                    
                    # Categoria
                    categoria = 'Serviço'
                    for col in ['categoria', 'category']:
                        if col in r and r[col]:
                            categoria = str(r[col]).strip().title()
                            break
                    
                    # Preços por tamanho
                    tamanhos_map = {
                        'kids': ['kids', 'crianca', 'infantil'],
                        'masculino': ['masculino', 'male', 'homem'],
                        'curto': ['curto', 'short'],
                        'medio': ['medio', 'médio', 'medium'],
                        'longo': ['longo', 'long'],
                        'extra_longo': ['extra_longo', 'extra longo', 'extralongo', 'extralong']
                    }
                    
                    tamanhos_precos = {}
                    for tamanho_key, col_aliases in tamanhos_map.items():
                        preco = 0.0
                        for col_alias in col_aliases:
                            if col_alias in r and r[col_alias]:
                                try:
                                    val = str(r[col_alias]).replace('R$', '').strip()
                                    if ',' in val:
                                        val = val.replace(',', '.')
                                    preco = float(val)
                                    break
                                except:
                                    continue
                        if preco > 0:
                            tamanhos_precos[tamanho_key] = preco
                    
                    # Se não há nenhum preço válido, erro
                    if not tamanhos_precos:
                        count_error += 1
                        continue
                    
                    # Criar um serviço para cada tamanho com preço definido
                    tamanhos_labels = {
                        'kids': 'Kids',
                        'masculino': 'Masculino',
                        'curto': 'Curto',
                        'medio': 'Médio',
                        'longo': 'Longo',
                        'extra_longo': 'Extra Longo'
                    }
                    
                    for tamanho_key, preco in tamanhos_precos.items():
                        tamanho_label = tamanhos_labels.get(tamanho_key, tamanho_key.title())
                        sku = f"{nome.upper().replace(' ', '-')}-{tamanho_label.upper().replace(' ', '-')}"
                        
                        db.servicos.insert_one({
                            'nome': nome,
                            'sku': sku,
                            'tamanho': tamanho_label,
                            'preco': preco,
                            'categoria': categoria,
                            'duracao': 60,
                            'ativo': True,
                            'created_at': datetime.now()
                        })
                    
                    count_success += 1
                except Exception as e:
                    logger.error(f"Erro ao importar serviço: {e}")
                    count_error += 1
        if os.path.exists(filepath):
            os.remove(filepath)

        return jsonify({'success': True, 'message': f'{count_success} importados!', 'count_success': count_success, 'count_error': count_error})
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'success': False}), 500

@app.route('/api/template/download/<tipo>')
@login_required
def download_template(tipo):
    wb = Workbook()
    ws = wb.active
    header_fill = PatternFill(start_color='7C3AED', end_color='7C3AED', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True, size=12)
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
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
        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            ws.column_dimensions[col].width = 15
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f'template_{tipo}_bioma.xlsx')

@app.route('/api/config', methods=['GET', 'POST'])
@login_required
def config():
    if db is None:
        return jsonify({'success': False}), 500
    if request.method == 'GET':
        try:
            cfg = db.config.find_one({'key': 'unidade'}) or {}
            return jsonify({'success': True, 'config': convert_objectid(cfg)})
        except:
            return jsonify({'success': False}), 500
    data = request.json
    try:
        # Atualizar configurações incluindo logo_url
        config_data = {
            'key': 'unidade',
            'nome_empresa': data.get('nome_empresa', 'BIOMA UBERABA'),
            'logo_url': data.get('logo_url', ''),
            'logo_login_url': data.get('logo_login_url', ''),
            'endereco': data.get('endereco', ''),
            'telefone': data.get('telefone', ''),
            'email': data.get('email', ''),
            'cnpj': data.get('cnpj', ''),
            'cor_primaria': data.get('cor_primaria', '#7C3AED'),
            'cor_secundaria': data.get('cor_secundaria', '#EC4899'),
            'updated_at': datetime.now()
        }
        
        db.config.update_one({'key': 'unidade'}, {'$set': config_data}, upsert=True)
        logger.info("✅ Configurações atualizadas")
        return jsonify({'success': True, 'message': 'Configurações salvas com sucesso!'})
    except Exception as e:
        logger.error(f"Erro ao salvar configurações: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
        return jsonify({'success': False}), 500

@app.route('/api/relatorios/completo', methods=['GET'])
@login_required
def relatorio_completo():
    """Relatório completo com todas as estatísticas do sistema"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        periodo = request.args.get('periodo', '30')  # Padrão 30 dias
        dias = int(periodo)
        data_inicio = datetime.now() - timedelta(days=dias)
        
        # === ESTATÍSTICAS GERAIS ===
        total_clientes = db.clientes.count_documents({})
        total_produtos = db.produtos.count_documents({'ativo': True})
        total_servicos = db.servicos.count_documents({'ativo': True})
        total_profissionais = db.profissionais.count_documents({'ativo': True})
        
        # === FATURAMENTO ===
        orcamentos_aprovados = list(db.orcamentos.find({
            'status': 'Aprovado',
            'created_at': {'$gte': data_inicio}
        }))
        
        faturamento_total = sum(o.get('total_final', 0) for o in orcamentos_aprovados)
        faturamento_servicos = sum(
            sum(s.get('total', 0) for s in o.get('servicos', []))
            for o in orcamentos_aprovados
        )
        faturamento_produtos = sum(
            sum(p.get('total', 0) for p in o.get('produtos', []))
            for o in orcamentos_aprovados
        )
        
        # === VENDAS ===
        total_orcamentos = db.orcamentos.count_documents({
            'created_at': {'$gte': data_inicio}
        })
        orcamentos_aprovados_count = len(orcamentos_aprovados)
        orcamentos_pendentes = db.orcamentos.count_documents({
            'status': 'Pendente',
            'created_at': {'$gte': data_inicio}
        })
        taxa_conversao = (orcamentos_aprovados_count / total_orcamentos * 100) if total_orcamentos > 0 else 0
        ticket_medio = faturamento_total / orcamentos_aprovados_count if orcamentos_aprovados_count > 0 else 0
        
        # === ESTOQUE ===
        produtos = list(db.produtos.find({'ativo': True}))
        estoque_total_valor_custo = sum(p.get('estoque', 0) * p.get('custo', 0) for p in produtos)
        estoque_total_valor_venda = sum(p.get('estoque', 0) * p.get('preco', 0) for p in produtos)
        produtos_zerados = len([p for p in produtos if p.get('estoque', 0) == 0])
        produtos_baixo_estoque = len([p for p in produtos if p.get('estoque', 0) <= p.get('estoque_minimo', 5) and p.get('estoque', 0) > 0])
        produtos_criticos = len([p for p in produtos if p.get('estoque', 0) == 0])
        
        # === CLIENTES ===
        novos_clientes = db.clientes.count_documents({
            'created_at': {'$gte': data_inicio}
        })
        
        # Top 10 clientes por gasto
        pipeline_clientes = [
            {'$match': {'status': 'Aprovado', 'created_at': {'$gte': data_inicio}}},
            {'$group': {
                '_id': '$cliente_cpf',
                'total_gasto': {'$sum': '$total_final'},
                'total_compras': {'$sum': 1},
                'cliente_nome': {'$first': '$cliente_nome'}
            }},
            {'$sort': {'total_gasto': -1}},
            {'$limit': 10}
        ]
        top_clientes = list(db.orcamentos.aggregate(pipeline_clientes))
        
        # === PRODUTOS MAIS VENDIDOS ===
        produtos_vendidos = {}
        for orc in orcamentos_aprovados:
            for prod in orc.get('produtos', []):
                prod_id = prod.get('id')
                if prod_id:
                    if prod_id not in produtos_vendidos:
                        produtos_vendidos[prod_id] = {
                            'nome': prod.get('nome', 'N/A'),
                            'quantidade': 0,
                            'faturamento': 0
                        }
                    produtos_vendidos[prod_id]['quantidade'] += prod.get('qtd', 1)
                    produtos_vendidos[prod_id]['faturamento'] += prod.get('total', 0)
        
        top_produtos = sorted(
            [{'id': k, **v} for k, v in produtos_vendidos.items()],
            key=lambda x: x['faturamento'],
            reverse=True
        )[:10]
        
        # === SERVIÇOS MAIS REALIZADOS ===
        servicos_realizados = {}
        for orc in orcamentos_aprovados:
            for serv in orc.get('servicos', []):
                serv_id = serv.get('id')
                if serv_id:
                    if serv_id not in servicos_realizados:
                        servicos_realizados[serv_id] = {
                            'nome': serv.get('nome', 'N/A'),
                            'tamanho': serv.get('tamanho', ''),
                            'quantidade': 0,
                            'faturamento': 0
                        }
                    servicos_realizados[serv_id]['quantidade'] += 1
                    servicos_realizados[serv_id]['faturamento'] += serv.get('total', 0)
        
        top_servicos = sorted(
            [{'id': k, **v} for k, v in servicos_realizados.items()],
            key=lambda x: x['faturamento'],
            reverse=True
        )[:10]
        
        # === FATURAMENTO POR DIA (para gráficos) ===
        faturamento_por_dia = {}
        for orc in orcamentos_aprovados:
            data = orc.get('created_at', datetime.now())
            dia = data.strftime('%Y-%m-%d')
            if dia not in faturamento_por_dia:
                faturamento_por_dia[dia] = 0
            faturamento_por_dia[dia] += orc.get('total_final', 0)
        
        faturamento_timeline = [
            {'data': dia, 'valor': valor}
            for dia, valor in sorted(faturamento_por_dia.items())
        ]
        
        # === PROFISSIONAIS COM MELHOR DESEMPENHO ===
        desempenho_profissionais = {}
        for orc in orcamentos_aprovados:
            for serv in orc.get('servicos', []):
                prof_id = serv.get('profissional_id')
                if prof_id:
                    if prof_id not in desempenho_profissionais:
                        prof = db.profissionais.find_one({'_id': ObjectId(prof_id)})
                        nome = prof.get('nome', 'N/A') if prof else 'N/A'
                        desempenho_profissionais[prof_id] = {
                            'nome': nome,
                            'servicos_realizados': 0,
                            'faturamento': 0
                        }
                    desempenho_profissionais[prof_id]['servicos_realizados'] += 1
                    desempenho_profissionais[prof_id]['faturamento'] += serv.get('total', 0)
        
        top_profissionais = sorted(
            [{'id': k, **v} for k, v in desempenho_profissionais.items()],
            key=lambda x: x['faturamento'],
            reverse=True
        )[:10]
        
        relatorio = {
            'periodo': f'Últimos {dias} dias',
            'data_inicio': data_inicio.isoformat(),
            'data_fim': datetime.now().isoformat(),
            
            'geral': {
                'total_clientes': total_clientes,
                'total_produtos': total_produtos,
                'total_servicos': total_servicos,
                'total_profissionais': total_profissionais,
                'novos_clientes': novos_clientes
            },
            
            'faturamento': {
                'total': faturamento_total,
                'servicos': faturamento_servicos,
                'produtos': faturamento_produtos,
                'timeline': faturamento_timeline
            },
            
            'vendas': {
                'total_orcamentos': total_orcamentos,
                'aprovados': orcamentos_aprovados_count,
                'pendentes': orcamentos_pendentes,
                'taxa_conversao': taxa_conversao,
                'ticket_medio': ticket_medio
            },
            
            'estoque': {
                'valor_total_custo': estoque_total_valor_custo,
                'valor_total_venda': estoque_total_valor_venda,
                'margem_potencial': estoque_total_valor_venda - estoque_total_valor_custo,
                'produtos_zerados': produtos_zerados,
                'produtos_baixo_estoque': produtos_baixo_estoque,
                'produtos_criticos': produtos_criticos
            },
            
            'rankings': {
                'top_clientes': convert_objectid(top_clientes),
                'top_produtos': top_produtos,
                'top_servicos': top_servicos,
                'top_profissionais': top_profissionais
            }
        }
        
        return jsonify({'success': True, 'relatorio': relatorio})
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

def init_db():
    if db is None:
        logger.warning("⚠️ DB não disponível para inicialização")
        return
    logger.info("🔧 Initializing DB...")
    if db.users.count_documents({}) == 0:
        db.users.insert_one({'name': 'Administrador', 'username': 'admin', 'email': 'admin@bioma.com', 'telefone': '', 'password': generate_password_hash('admin123'), 'role': 'admin', 'theme': 'light', 'created_at': datetime.now()})
        logger.info("✅ Admin user created: admin/admin123 (role: admin)")
    if db.servicos.count_documents({}) == 0:
        services = [('Hidratação', 'Tratamento', [50, 60, 80, 100, 120, 150]), ('Corte', 'Cabelo', [40, 50, 60, 80, 100, 120])]
        tamanhos = ['Kids', 'Masculino', 'Curto', 'Médio', 'Longo', 'Extra Longo']
        for nome, cat, precos in services:
            for tam, preco in zip(tamanhos, precos):
                db.servicos.insert_one({'nome': nome, 'sku': f"{nome.upper()}-{tam.upper()}", 'tamanho': tam, 'preco': preco, 'categoria': cat, 'duracao': 60, 'ativo': True, 'created_at': datetime.now()})
        logger.info(f"✅ {len(services) * 6} service SKUs created")
    try:
        db.users.create_index([('username', ASCENDING)], unique=True)
        db.users.create_index([('email', ASCENDING)], unique=True)
        db.clientes.create_index([('cpf', ASCENDING)])
        db.orcamentos.create_index([('numero', ASCENDING)], unique=True)
        logger.info("✅ Database indexes created")
    except Exception as e:
        logger.warning(f"⚠️ Index creation warning: {e}")
    logger.info("🎉 DB initialization complete!")

@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'message': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"❌ 500 Internal Error: {e}")
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🌳 BIOMA UBERABA v3.7 COMPLETO E DEFINITIVO")
    print("=" * 80)
    init_db()
    is_production = os.getenv('FLASK_ENV') == 'production'
    base_url = 'https://bioma-system2.onrender.com' if is_production else 'http://localhost:5000'
    print(f"\n🚀 Servidor: {base_url}")
    print(f"👤 Login Padrão: admin / admin123")
    print(f"🔑 TODOS os novos usuários têm privilégios de ADMIN automaticamente")
    if db is not None:
        try:
            db.command('ping')
            print(f"💾 MongoDB: ✅ CONECTADO")
        except:
            print(f"💾 MongoDB: ❌ ERRO DE CONEXÃO")
    else:
        print(f"💾 MongoDB: ❌ NÃO CONECTADO")
    if os.getenv('MAILERSEND_API_KEY'):
        print(f"📧 MailerSend: ✅ CONFIGURADO")
    else:
        print(f"📧 MailerSend: ⚠️  NÃO CONFIGURADO")
    print("\n" + "=" * 80)
    print(f"🕐 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"👨‍💻 Desenvolvedor: @juanmarco1999")
    print(f"📧 Contato: 180147064@aluno.unb.br")
    print("=" * 80 + "\n")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)


# ======= SSE (Server-Sent Events) =======
import queue, json
class EventBroadcaster:
    def __init__(self):
        self.subscribers = []  # SimpleQueue per client
    def subscribe(self):
        q = queue.SimpleQueue()
        self.subscribers.append(q)
        return q
    def publish(self, channel, payload):
        msg = json.dumps({'channel': channel, 'payload': payload, 'ts': datetime.utcnow().isoformat()})
        for q in list(self.subscribers):
            try:
                q.put_nowait(msg)
            except Exception:
                pass

broadcaster = EventBroadcaster()

def notify(channel, payload):
    try:
        broadcaster.publish(channel, payload)
    except Exception as e:
        logger.warning(f'notify error: {e}')

@app.route('/api/stream')
@login_required
def sse_stream():
    def gen():
        q = broadcaster.subscribe()
        # greet
        yield "data: " + json.dumps({'channel':'hello','payload':'ok'}) + "\\n\\n"
        while True:
            data = q.get()  # blocking
            yield "data: " + data + "\\n\\n"
    return Response(gen(), mimetype='text/event-stream')


@app.route('/api/estoque/exportar')
@login_required
def estoque_exportar():
    """Exporta itens ou movimentações do estoque em Excel.
Parâmetros:
- tipo=movimentacoes -> exporta log, senão exporta itens
"""
    try:
        tipo = request.args.get('tipo','itens')
        wb = Workbook()
        ws = wb.active
        if tipo == 'movimentacoes':
            ws.title = 'Movimentações'
            ws.append(['Data','Tipo','Produto','SKU','Quantidade','Valor Unitário','Usuário','Observações'])
            cur = db.estoque_movimentacoes.find({}).sort('data', DESCENDING)
            for m in cur:
                # buscar produto
                prod = None
                if m.get('produto_id'):
                    prod = db.produtos.find_one({'_id': ObjectId(m['produto_id'])})
                ws.append([
                    (m.get('data') or datetime.now()).strftime('%Y-%m-%d %H:%M'),
                    m.get('tipo','-'),
                    (prod or {}).get('nome',''),
                    (prod or {}).get('sku',''),
                    int(m.get('quantidade',0) or 0),
                    float(m.get('valor_unitario',0) or 0),
                    m.get('usuario',''),
                    m.get('observacoes','')
                ])
            fn = f"estoque_mov_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        else:
            ws.title = 'Estoque'
            ws.append(['Nome','Marca','SKU','Categoria','Custo (R$)','Preço (R$)','Estoque','Mínimo','Criado em'])
            cur = db.produtos.find({'ativo': True}).sort('nome', ASCENDING)
            for pdoc in cur:
                ws.append([
                    pdoc.get('nome',''),
                    pdoc.get('marca',''),
                    pdoc.get('sku',''),
                    pdoc.get('categoria',''),
                    float(pdoc.get('custo',0) or 0),
                    float(pdoc.get('preco',0) or 0),
                    int(pdoc.get('estoque',0) or 0),
                    int(pdoc.get('estoque_minimo',0) or 0),
                    (pdoc.get('created_at') or datetime.now()).strftime('%Y-%m-%d')
                ])
            fn = f"estoque_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        bio = io.BytesIO()
        wb.save(bio); bio.seek(0)
        return send_file(bio, as_attachment=True, download_name=fn, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        logger.exception("Erro ao exportar estoque")
        return jsonify({'success': False, 'message': str(e)}), 500


def _pdf_doc(buffer, title):
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Hdr', parent=styles['Heading1'], alignment=TA_CENTER, textColor=HexColor('#111827')))
    styles.add(ParagraphStyle(name='TblHdr', parent=styles['Normal'], alignment=TA_LEFT, textColor=HexColor('#374151')))
    return doc, styles

@app.route('/api/estoque/movimentacoes/pdf')
@login_required
def estoque_movimentacoes_pdf():
    try:
        di = request.args.get('data_inicio'); df = request.args.get('data_fim'); tipo = request.args.get('tipo')
        q = {}
        if di or df:
            di_dt = datetime.fromisoformat(di) if di else datetime.now()-timedelta(days=3650)
            df_dt = datetime.fromisoformat(df) if df else datetime.now()
            q['data'] = {'$gte': di_dt, '$lte': df_dt}
        if tipo in ('entrada','saida'):
            q['tipo'] = tipo
        rows = []
        for m in db.estoque_movimentacoes.find(q).sort('data', DESCENDING):
            prod = db.produtos.find_one({'_id': ObjectId(m.get('produto_id'))}) if m.get('produto_id') else {}
            rows.append([
                (m.get('data') or datetime.now()).strftime('%Y-%m-%d %H:%M'),
                m.get('tipo','-'),
                prod.get('nome',''),
                prod.get('sku',''),
                int(m.get('quantidade',0) or 0),
                f"R$ {float(m.get('valor_unitario',0) or 0):.2f}",
                m.get('usuario',''),
                m.get('observacoes','')
            ])
        buf = io.BytesIO()
        doc, styles = _pdf_doc(buf, "Movimentações de Estoque")
        story = [Paragraph("Movimentações de Estoque", styles['Hdr']), Spacer(1,12)]
        data = [['Data','Tipo','Produto','SKU','Qtd','Valor Unit.','Usuário','Obs.']] + rows
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0), HexColor('#EEF2FF')),
                                   ('TEXTCOLOR',(0,0),(-1,0), HexColor('#111827')),
                                   ('GRID',(0,0),(-1,-1),0.25, HexColor('#E5E7EB')),
                                   ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]))
        story += [table]
        doc.build(story)
        buf.seek(0)
        return send_file(buf, as_attachment=True, download_name='movimentacoes_estoque.pdf', mimetype='application/pdf')
    except Exception as e:
        logger.exception("Erro PDF movimentações")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/clientes/lista/pdf')
@login_required
def clientes_lista_pdf():
    try:
        q = (request.args.get('q') or '').strip()
        filtro = {}
        if q:
            filtro['$or'] = [{'nome': {'$regex': q, '$options': 'i'}},
                             {'email': {'$regex': q, '$options': 'i'}},
                             {'telefone': {'$regex': q, '$options': 'i'}}]
        rows = []
        for c in db.clientes.find(filtro).sort('nome', ASCENDING):
            rows.append([c.get('nome',''), c.get('cpf',''), c.get('email',''), c.get('telefone',''),
                         c.get('genero',''), c.get('data_nascimento','')])
        buf = io.BytesIO()
        doc, styles = _pdf_doc(buf, "Lista de Clientes")
        story = [Paragraph("Lista de Clientes", styles['Hdr']), Spacer(1,12)]
        data = [['Nome','CPF','E-mail','Telefone','Gênero','Nascimento']] + rows
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0), HexColor('#EEF2FF')),
                                   ('GRID',(0,0),(-1,-1),0.25, HexColor('#E5E7EB')),
                                   ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]))
        story += [table]
        doc.build(story)
        buf.seek(0)
        return send_file(buf, as_attachment=True, download_name='clientes.pdf', mimetype='application/pdf')
    except Exception as e:
        logger.exception("Erro PDF clientes")
        return jsonify({'success': False, 'message': str(e)}), 500


def _calc_comissoes(di, df):
    prof_index = {str(p['_id']): p for p in db.profissionais.find({})}
    totais = {}
    cur = db.orcamentos.find({'status':'Aprovado', 'created_at': {'$gte': di, '$lte': df}})
    for orc in cur:
        for s in orc.get('servicos', []):
            val = float(s.get('total', s.get('preco', 0)) or 0)
            pid = str(s.get('profissional_id') or '')
            perc = 0.0
            if pid and pid in prof_index:
                perc = float(prof_index[pid].get('comissao_perc', 0) or 0)
            com = val * (perc/100.0)
            if pid not in totais:
                totais[pid] = {'valor_servicos': 0.0, 'comissao': 0.0}
            totais[pid]['valor_servicos'] += val
            totais[pid]['comissao'] += com
    out = []
    for pid, info in totais.items():
        nome = prof_index.get(pid, {}).get('nome', '—')
        out.append([nome, f"R$ {info['valor_servicos']:.2f}", f"R$ {info['comissao']:.2f}"])
    return out

@app.route('/api/profissionais/comissoes/pdf')
@login_required
def prof_comissoes_pdf():
    try:
        di = request.args.get('data_inicio'); df = request.args.get('data_fim')
        di_dt = datetime.fromisoformat(di) if di else datetime.now()-timedelta(days=30)
        df_dt = datetime.fromisoformat(df) if df else datetime.now()
        rows = _calc_comissoes(di_dt, df_dt)
        buf = io.BytesIO()
        doc, styles = _pdf_doc(buf, "Comissões por Profissional")
        story = [Paragraph("Comissões por Profissional", styles['Hdr']), Spacer(1,12)]
        data = [['Profissional','Valor em Serviços','Comissão (R$)']] + rows
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0), HexColor('#EEF2FF')),
                                   ('GRID',(0,0),(-1,-1),0.25, HexColor('#E5E7EB')),
                                   ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]))
        story += [table]
        doc.build(story)
        buf.seek(0)
        return send_file(buf, as_attachment=True, download_name='comissoes_profissionais.pdf', mimetype='application/pdf')
    except Exception as e:
        logger.exception("Erro PDF comissões")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/agendamentos/disponibilidade')
@login_required
def ag_disponibilidade():
    prof_id = request.args.get('profissional_id'); data = request.args.get('data')
    if not (prof_id and data):
        return jsonify({'success': False, 'message': 'profissional_id e data são obrigatórios'}), 400
    y,m,d = [int(x) for x in data.split('-')]
    inicio, fim, passo = 8, 20, 15
    slots = []
    dt = datetime(y,m,d, inicio, 0)
    end = datetime(y,m,d, fim, 0)
    while dt < end:
        slots.append(dt.strftime('%H:%M'))
        dt += timedelta(minutes=passo)
    ags = list(db.agendamentos.find({'profissional_id': prof_id, 'data': data}))
    ocupados = set([a.get('hora') for a in ags if a.get('hora')])
    res = [{'hora': h, 'status': ('ocupado' if h in ocupados else 'livre')} for h in slots]
    return jsonify({'success': True, 'profissional_id': prof_id, 'data': data, 'slots': res})


@app.route('/api/agendamentos/heatmap')
@login_required
def ag_heatmap():
    try:
        dias = int(request.args.get('dias', 60))
    except:
        dias = 60
    fim = datetime.utcnow()
    ini = fim - timedelta(days=dias)
    def agg(col, field='created_at'):
        pipe = [
            {'$match': {field: {'$gte': ini, '$lte': fim}}},
            {'$group': {'_id': {'$dateToString': {'format':'%Y-%m-%d', 'date': f'${field}'}}, 'count': {'$sum': 1}}},
            {'$sort': {'_id': 1}}
        ]
        try:
            return {x['_id']: x['count'] for x in db[col].aggregate(pipe)}
        except Exception:
            return {}
    a = agg('agendamentos','created_at')
    o = agg('orcamentos','created_at')
    v = agg('vendas','created_at') if 'vendas' in db.list_collection_names() else {}
    keys = sorted(set(list(a.keys())+list(o.keys())+list(v.keys())))
    out = [{'data': k, 'agendamentos': a.get(k,0), 'orcamentos': o.get(k,0), 'vendas': v.get(k,0)} for k in keys]
    return jsonify({'success': True, 'heatmap': out})


@app.route('/api/relatorios/completo.xlsx')
@login_required
def relatorio_completo_xlsx():
    try:
        # Reusa a lógica do JSON para obter estatísticas
        periodo = request.args.get('periodo', '30')
        dias = int(periodo)
        data_inicio = datetime.now() - timedelta(days=dias)
        # KPIs simples
        total_clientes = db.clientes.count_documents({})
        total_produtos = db.produtos.count_documents({'ativo': True})
        total_servicos = db.servicos.count_documents({'ativo': True})
        total_profissionais = db.profissionais.count_documents({'ativo': True})
        wb = Workbook()
        ws = wb.active; ws.title = "Resumo"
        ws.append(['Métrica','Valor'])
        ws.append(['Total de clientes', total_clientes])
        ws.append(['Total de produtos ativos', total_produtos])
        ws.append(['Total de serviços ativos', total_servicos])
        ws.append(['Total de profissionais ativos', total_profissionais])
        # Aprovados por período
        ws2 = wb.create_sheet("Orçamentos Aprovados")
        ws2.append(['Número','Cliente','Data','Total (R$)','Status'])
        for o in db.orcamentos.find({'status':'Aprovado','created_at':{'$gte': data_inicio}}).sort('created_at', DESCENDING):
            ws2.append([o.get('numero',''), o.get('cliente_nome',''), (o.get('created_at') or datetime.now()).strftime('%Y-%m-%d'), float(o.get('total_final',0) or 0), o.get('status','')])
        bio = io.BytesIO(); wb.save(bio); bio.seek(0)
        return send_file(bio, as_attachment=True, download_name='relatorio_completo.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        logger.exception("Erro Excel relatorio completo")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/notify', methods=['POST'])
@login_required
def admin_notify():
    try:
        data = request.json or {}
        channel = data.get('channel','events')
        payload = data.get('payload',{})
        notify(channel, payload)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
