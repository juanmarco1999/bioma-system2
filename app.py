#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA UBERABA v3.7 COMPLETO - Sistema Ultra Profissional
Desenvolvedor: Juan Marco (@juanmarco1999)
Email: 180147064@aluno.unb.br
Data: 2025-10-05 21:57:49 UTC
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
from io import BytesIO
import csv
import json
import re
import requests
import logging
import random
from functools import lru_cache
from time import time

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
app.secret_key = os.getenv('SECRET_KEY', 'bioma-2025-v3-7-ultra-secure-key-final-definitivo-completo')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = '/tmp'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

CORS(app, supports_credentials=True)
# ---- Cookie/CORS robustez para desenvolvimento cross-origin ----
FRONTEND_ORIGIN = os.getenv('FRONTEND_ORIGIN')  # ex: http://127.0.0.1:5500 ou http://localhost:5173
if os.getenv('CROSS_SITE_DEV','0') == '1':
    # Para permitir cookies em requisições XHR cross-site durante desenvolvimento
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = False  # Em produção use True (HTTPS)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    try:
        # Ajusta CORS para refletir a origem do front
        from flask_cors import CORS
        if FRONTEND_ORIGIN:
            CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": FRONTEND_ORIGIN}})
        else:
            CORS(app, supports_credentials=True)
    except Exception as _e:
        pass


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
        # Melhorado: timeouts mais curtos para evitar travamentos
        client = MongoClient(
            uri, 
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
            socketTimeoutMS=3000,
            maxPoolSize=10,
            minPoolSize=1,
            maxIdleTimeMS=30000
        )
        # Ping para testar conexão
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

def get_assistente_details(assistente_id, assistente_tipo=None):
    """Recupera os dados do assistente a partir do ID informado.

    O assistente pode estar na coleção de profissionais ou na coleção dedicada
    de assistentes. O campo assistente_tipo permite definir explicitamente a
    prioridade de busca e garante compatibilidade com registros antigos que
    armazenavam apenas o ID do profissional.
    """
    if not assistente_id or db is None:
        return None

    def _find_in_profissionais(doc_id):
        try:
            return db.profissionais.find_one({'_id': ObjectId(doc_id)})
        except Exception:
            return None

    def _find_in_assistentes(doc_id):
        try:
            return db.assistentes.find_one({'_id': ObjectId(doc_id)})
        except Exception:
            return None

    lookup_order = []
    if assistente_tipo == 'assistente':
        lookup_order = [_find_in_assistentes, _find_in_profissionais]
    elif assistente_tipo == 'profissional':
        lookup_order = [_find_in_profissionais, _find_in_assistentes]
    else:
        lookup_order = [_find_in_profissionais, _find_in_assistentes]

    for finder in lookup_order:
        registro = finder(assistente_id)
        if registro:
            dados = convert_objectid(registro)
            dados['tipo_origem'] = 'assistente' if finder is _find_in_assistentes else 'profissional'
            return dados
    return None

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

def clear_cache(prefix=None):
    """Limpar cache completo ou apenas prefixos específicos"""
    global request_cache
    if prefix:
        keys_to_delete = [k for k in request_cache.keys() if k.startswith(prefix)]
        for k in keys_to_delete:
            del request_cache[k]
    else:
        request_cache.clear()

def registrar_auditoria(acao, entidade, entidade_id, dados_antes=None, dados_depois=None):
    """Registrar ação de auditoria no sistema"""
    if db is None:
        return
    
    try:
        usuario_id = session.get('user_id')
        username = session.get('username', 'sistema')
        
        registro = {
            'usuario_id': usuario_id,
            'username': username,
            'acao': acao,  # 'criar', 'editar', 'deletar', 'aprovar', 'rejeitar'
            'entidade': entidade,  # 'cliente', 'produto', 'orcamento', etc
            'entidade_id': entidade_id,
            'dados_antes': dados_antes,
            'dados_depois': dados_depois,
            'timestamp': datetime.now(),
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        }
        
        db.auditoria.insert_one(registro)
        logger.info(f"Auditoria: {username} - {acao} {entidade} {entidade_id}")
    except Exception as e:
        logger.error(f"Erro ao registrar auditoria: {e}")

@app.before_request
def before_request_handler():
    """Limpar cache relevante antes de operações de escrita"""
    if request.method in ['POST', 'PUT', 'DELETE']:
        # Limpar cache relacionado ao endpoint
        if 'servicos' in request.path:
            clear_cache('servicos_')
        elif 'produtos' in request.path:
            clear_cache('produtos_')
        elif 'profissionais' in request.path:
            clear_cache('profissionais_')
        elif 'clientes' in request.path:
            clear_cache('clientes_')

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
        logger.error(f"Erro ao buscar stats: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/dashboard/stats/realtime')
@login_required
def dashboard_stats_realtime():
    """Estatísticas em tempo real com métricas avançadas"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        agora = datetime.now()
        hoje_inicio = agora.replace(hour=0, minute=0, second=0, microsecond=0)
        semana_inicio = agora - timedelta(days=7)
        mes_inicio = agora - timedelta(days=30)
        
        # Estatísticas básicas
        total_clientes = db.clientes.count_documents({})
        total_profissionais = db.profissionais.count_documents({})
        total_produtos = db.produtos.count_documents({})
        total_servicos = db.servicos.count_documents({})
        
        # Orçamentos
        total_orcamentos = db.orcamentos.count_documents({})
        orcamentos_pendentes = db.orcamentos.count_documents({'status': 'Pendente'})
        orcamentos_aprovados = db.orcamentos.count_documents({'status': 'Aprovado'})
        
        # Faturamento
        faturamento_total = sum(o.get('total_final', 0) for o in db.orcamentos.find({'status': 'Aprovado'}))
        faturamento_mes = sum(o.get('total_final', 0) for o in db.orcamentos.find({
            'status': 'Aprovado',
            'data_criacao': {'$gte': mes_inicio}
        }))
        faturamento_hoje = sum(o.get('total_final', 0) for o in db.orcamentos.find({
            'status': 'Aprovado',
            'data_criacao': {'$gte': hoje_inicio}
        }))
        
        # Agendamentos
        agendamentos_hoje = 0
        agendamentos_semana = 0
        if 'agendamentos' in db.list_collection_names():
            agendamentos_hoje = db.agendamentos.count_documents({
                'data': {'$gte': hoje_inicio, '$lte': agora}
            })
            agendamentos_semana = db.agendamentos.count_documents({
                'data': {'$gte': semana_inicio}
            })
        
        # Estoque
        produtos_baixo_estoque = db.produtos.count_documents({
            '$expr': {'$lt': ['$estoque', '$estoque_minimo']}
        })
        produtos_sem_estoque = db.produtos.count_documents({'estoque': 0})
        valor_estoque = sum(p.get('preco', 0) * p.get('estoque', 0) 
                           for p in db.produtos.find({}))
        
        # Pendências
        entradas_pendentes = 0
        if 'estoque_pendencias' in db.list_collection_names():
            entradas_pendentes = db.estoque_pendencias.count_documents({'status': 'pendente'})
        
        # Comissões do mês
        comissoes_mes = 0
        if 'comissoes_historico' in db.list_collection_names():
            comissoes_mes = sum(c.get('valor_total', 0) for c in db.comissoes_historico.find({
                'data': {'$gte': mes_inicio}
            }))
        
        # Clientes novos (últimos 30 dias)
        clientes_novos = db.clientes.count_documents({
            'data_cadastro': {'$gte': mes_inicio}
        })
        
        return jsonify({
            'success': True,
            'timestamp': agora.isoformat(),
            'stats': {
                'totais': {
                    'clientes': total_clientes,
                    'profissionais': total_profissionais,
                    'produtos': total_produtos,
                    'servicos': total_servicos,
                    'orcamentos': total_orcamentos
                },
                'orcamentos': {
                    'pendentes': orcamentos_pendentes,
                    'aprovados': orcamentos_aprovados,
                    'taxa_aprovacao': round((orcamentos_aprovados / total_orcamentos * 100) if total_orcamentos > 0 else 0, 2)
                },
                'faturamento': {
                    'total': round(faturamento_total, 2),
                    'mes': round(faturamento_mes, 2),
                    'hoje': round(faturamento_hoje, 2),
                    'ticket_medio': round(faturamento_total / orcamentos_aprovados if orcamentos_aprovados > 0 else 0, 2)
                },
                'agendamentos': {
                    'hoje': agendamentos_hoje,
                    'semana': agendamentos_semana
                },
                'estoque': {
                    'valor_total': round(valor_estoque, 2),
                    'baixo_estoque': produtos_baixo_estoque,
                    'sem_estoque': produtos_sem_estoque,
                    'alerta': produtos_baixo_estoque > 0 or produtos_sem_estoque > 0
                },
                'pendencias': {
                    'entradas_estoque': entradas_pendentes,
                    'orcamentos': orcamentos_pendentes,
                    'total': entradas_pendentes + orcamentos_pendentes
                },
                'crescimento': {
                    'clientes_novos_mes': clientes_novos,
                    'comissoes_mes': round(comissoes_mes, 2)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar estatísticas em tempo real: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
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
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    termo = request.args.get('termo', '').strip()
    cache_key = f"clientes_busca_{termo}"
    
    # Tentar buscar do cache primeiro
    cached = get_from_cache(cache_key)
    if cached:
        return jsonify(cached)
    
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
        
        result = {'success': True, 'clientes': convert_objectid(clientes)}
        set_in_cache(cache_key, result)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Erro ao buscar clientes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/busca/global', methods=['GET'])
@login_required
def busca_global():
    """Busca global em múltiplas collections"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    termo = request.args.get('termo', '').strip()
    
    if not termo or len(termo) < 2:
        return jsonify({'success': True, 'resultados': {'clientes': [], 'profissionais': [], 'produtos': [], 'servicos': []}})
    
    cache_key = f"busca_global_{termo}"
    cached = get_from_cache(cache_key)
    if cached:
        return jsonify(cached)
    
    try:
        regex = {'$regex': termo, '$options': 'i'}
        
        # Buscar em clientes
        clientes = list(db.clientes.find({
            '$or': [
                {'nome': regex},
                {'cpf': regex},
                {'email': regex},
                {'telefone': regex}
            ]
        }).limit(10))
        
        # Buscar em profissionais
        profissionais = list(db.profissionais.find({
            '$or': [
                {'nome': regex},
                {'cpf': regex},
                {'email': regex},
                {'especialidade': regex}
            ]
        }).limit(10))
        
        # Buscar em produtos
        produtos = list(db.produtos.find({
            '$or': [
                {'nome': regex},
                {'marca': regex},
                {'sku': regex}
            ]
        }).limit(10))
        
        # Buscar em serviços
        servicos = list(db.servicos.find({
            '$or': [
                {'nome': regex},
                {'categoria': regex}
            ]
        }).limit(10))
        
        result = {
            'success': True,
            'resultados': {
                'clientes': convert_objectid(clientes),
                'profissionais': convert_objectid(profissionais),
                'produtos': convert_objectid(produtos),
                'servicos': convert_objectid(servicos)
            },
            'total': len(clientes) + len(profissionais) + len(produtos) + len(servicos)
        }
        
        set_in_cache(cache_key, result)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erro na busca global: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profissionais', methods=['GET', 'POST'])
@login_required
def profissionais():
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    if request.method == 'GET':
        cache_key = 'profissionais_list'
        cached = get_from_cache(cache_key)
        if cached:
            return jsonify(cached)
        
        try:
            profs = list(db.profissionais.find({}).sort('nome', ASCENDING).limit(500))

            # Agregar métricas de avaliação para exibição rápida na lista
            avaliacoes_map = {}
            try:
                stats_pipeline = [
                    {'$group': {
                        '_id': '$profissional_id',
                        'media': {'$avg': '$nota'},
                        'total': {'$sum': 1}
                    }}
                ]
                for stat in db.profissionais_avaliacoes.aggregate(stats_pipeline):
                    avaliacoes_map[stat['_id']] = {
                        'media': round(stat.get('media', 0), 2),
                        'total': stat.get('total', 0)
                    }
            except Exception as agg_error:
                logger.debug(f"Falha ao agregar avaliações de profissionais: {agg_error}")

            for prof in profs:
                assistente_info = get_assistente_details(
                    prof.get('assistente_id'),
                    prof.get('assistente_tipo')
                )
                if assistente_info:
                    prof['assistente'] = {
                        'id': assistente_info.get('_id'),
                        'nome': assistente_info.get('nome'),
                        'tipo': assistente_info.get('tipo_origem'),
                        'foto_url': assistente_info.get('foto_url', '')
                    }
                # Avaliações agregadas
                stat = avaliacoes_map.get(str(prof.get('_id')))
                if stat:
                    prof['avaliacao_media'] = stat['media']
                    prof['avaliacoes_total'] = stat['total']
                else:
                    prof['avaliacao_media'] = 0
                    prof['avaliacoes_total'] = 0

            result = {'success': True, 'profissionais': convert_objectid(profs)}
            set_in_cache(cache_key, result)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Erro ao listar profissionais: {e}")
            return jsonify({'success': False, 'message': 'Erro ao carregar profissionais'}), 500
    
    data = request.json
    try:
        assistente_id = data.get('assistente_id') or None
        assistente_tipo = data.get('assistente_tipo')
        if assistente_id:
            assistente_id = str(assistente_id)
        if assistente_tipo not in {'profissional', 'assistente', None}:
            assistente_tipo = None

        profissional_data = {
            'nome': data['nome'],
            'cpf': data['cpf'],
            'email': data.get('email', ''),
            'telefone': data.get('telefone', ''),
            'especialidade': data.get('especialidade', ''),
            'comissao_perc': float(data.get('comissao_perc', 0)),
            'foto_url': data.get('foto_url', ''),
            'assistente_id': assistente_id,
            'assistente_tipo': assistente_tipo if assistente_id else None,
            'comissao_assistente_perc': float(data.get('comissao_assistente_perc', 0)),
            'ativo': True,
            'created_at': datetime.now()
        }
        db.profissionais.insert_one(profissional_data)
        logger.info(f"✅ Profissional cadastrado: {profissional_data['nome']}")
        return jsonify({'success': True, 'message': 'Profissional cadastrado com sucesso'})
    except Exception as e:
        logger.error(f"Erro ao cadastrar profissional: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

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
    """Visualizar um profissional especifico com estatisticas completas"""
    if db is None:
        return jsonify({'success': False}), 500
    try:
        profissional = db.profissionais.find_one({'_id': ObjectId(id)})
        if not profissional:
            return jsonify({'success': False, 'message': 'Profissional nao encontrado'}), 404

        profissional_id_str = str(profissional['_id'])

        orcamentos_prof = list(db.orcamentos.find({
            'servicos.profissional_id': profissional_id_str
        }))

        total_comissao = 0.0
        total_comissao_assistente = 0.0
        servicos_realizados = 0
        orcamentos_aprovados = 0
        desempenho_mensal = {}
        multicomissao_detalhes = []

        assistente_info = get_assistente_details(
            profissional.get('assistente_id'),
            profissional.get('assistente_tipo')
        )

        comissao_prof_perc = float(profissional.get('comissao_perc', 0))
        comissao_assistente_padrao = float(profissional.get('comissao_assistente_perc', 0))

        for orc in orcamentos_prof:
            data_orc = orc.get('created_at', datetime.now())
            mes_key = data_orc.strftime('%Y-%m') if isinstance(data_orc, datetime) else 'desconhecido'
            if mes_key not in desempenho_mensal:
                desempenho_mensal[mes_key] = {
                    'mes': mes_key,
                    'comissao_profissional': 0.0,
                    'comissao_assistente': 0.0,
                    'servicos': 0,
                    'faturamento': 0.0
                }

            if orc.get('status') == 'Aprovado':
                orcamentos_aprovados += 1
                desempenho_mensal[mes_key]['faturamento'] += orc.get('total_final', 0)

            for servico in orc.get('servicos', []):
                if servico.get('profissional_id') != profissional_id_str:
                    continue

                quantidade = servico.get('qtd', 1) or 1
                valor_servico = servico.get('total', 0) or 0
                servicos_realizados += quantidade

                comissao_valor = valor_servico * (comissao_prof_perc / 100)
                total_comissao += comissao_valor
                desempenho_mensal[mes_key]['comissao_profissional'] += comissao_valor
                desempenho_mensal[mes_key]['servicos'] += quantidade

                assistente_item = None
                assistente_perc = servico.get('assistente_comissao_perc')
                assistente_servico = servico.get('assistente_servico') or servico.get('nome')

                if servico.get('assistente_id'):
                    assistente_item = get_assistente_details(
                        servico.get('assistente_id'),
                        servico.get('assistente_tipo')
                    )
                    if assistente_perc is None:
                        assistente_perc = servico.get('assistente_comissao_perc', comissao_assistente_padrao)
                elif assistente_info:
                    assistente_item = assistente_info
                    if assistente_perc is None:
                        assistente_perc = comissao_assistente_padrao

                comissao_assistente_valor = 0.0
                if assistente_item and assistente_perc:
                    assistente_perc = float(assistente_perc)
                    comissao_assistente_valor = comissao_valor * (assistente_perc / 100)
                    total_comissao_assistente += comissao_assistente_valor
                    desempenho_mensal[mes_key]['comissao_assistente'] += comissao_assistente_valor

                multicomissao_detalhes.append({
                    'orcamento_id': str(orc['_id']),
                    'orcamento_numero': orc.get('numero'),
                    'cliente': orc.get('cliente_nome'),
                    'status': orc.get('status'),
                    'data': data_orc.isoformat() if isinstance(data_orc, datetime) else data_orc,
                    'servico': servico.get('nome'),
                    'valor_servico': valor_servico,
                    'comissao_profissional': comissao_valor,
                    'comissao_assistente': comissao_assistente_valor,
                    'assistente_nome': assistente_item.get('nome') if assistente_item else None,
                    'assistente_tipo': assistente_item.get('tipo_origem') if assistente_item else None,
                    'descricao': f"Profissional {profissional.get('nome')} - {servico.get('nome')}" + (
                        f" | Assistente {assistente_item.get('nome')} - {assistente_servico}" if assistente_item else ''
                    )
                })

        desempenho_ordenado = sorted(desempenho_mensal.items())
        grafico_labels = [item[0] for item in desempenho_ordenado]
        grafico_dados_prof = [round(item[1]['comissao_profissional'], 2) for item in desempenho_ordenado]
        grafico_dados_assist = [round(item[1]['comissao_assistente'], 2) for item in desempenho_ordenado]
        grafico_servicos = [item[1]['servicos'] for item in desempenho_ordenado]

        avaliacoes = []
        try:
            avaliacoes = list(db.profissionais_avaliacoes.find(
                {'profissional_id': profissional_id_str}
            ).sort('created_at', DESCENDING).limit(20))
        except Exception as avaliacao_error:
            logger.debug(f"Falha ao carregar avaliacoes do profissional {id}: {avaliacao_error}")

        if assistente_info:
            profissional['assistente'] = assistente_info

        profissional['estatisticas'] = {
            'total_comissao': round(total_comissao, 2),
            'total_comissao_assistente': round(total_comissao_assistente, 2),
            'servicos_realizados': servicos_realizados,
            'total_orcamentos': len(orcamentos_prof),
            'orcamentos_aprovados': orcamentos_aprovados,
            'comissao_media': round(total_comissao / servicos_realizados, 2) if servicos_realizados else 0
        }

        profissional['desempenho'] = {
            'labels': grafico_labels,
            'comissao_profissional': grafico_dados_prof,
            'comissao_assistente': grafico_dados_assist,
            'servicos': grafico_servicos
        }

        profissional['multicomissao'] = multicomissao_detalhes
        profissional['avaliacoes'] = convert_objectid(avaliacoes)

        return jsonify({'success': True, 'profissional': convert_objectid(profissional)})
    except Exception as e:
        logger.error(f"Erro ao buscar profissional: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/comissao/calcular', methods=['POST'])
@login_required
def calcular_comissao():
    """Calcular comissoes de profissional e assistente para um orcamento"""
    if db is None:
        return jsonify({'success': False}), 500

    data = request.json or {}
    try:
        orcamento_id = data.get('orcamento_id')
        if not orcamento_id:
            return jsonify({'success': False, 'message': 'ID do orcamento nao fornecido'}), 400

        orcamento = db.orcamentos.find_one({'_id': ObjectId(orcamento_id)})
        if not orcamento:
            return jsonify({'success': False, 'message': 'Orcamento nao encontrado'}), 404

        comissoes = []
        total_comissoes = 0.0

        for servico in orcamento.get('servicos', []):
            profissional_id = servico.get('profissional_id')
            if not profissional_id:
                continue

            profissional = db.profissionais.find_one({'_id': ObjectId(profissional_id)})
            if not profissional:
                continue

            valor_servico = servico.get('total', 0) or 0
            comissao_perc = float(profissional.get('comissao_perc', 0))
            comissao_valor = valor_servico * (comissao_perc / 100)

            comissao_info = {
                'profissional_id': str(profissional['_id']),
                'profissional_nome': profissional.get('nome', ''),
                'servico': servico.get('nome', ''),
                'valor_servico': valor_servico,
                'comissao_perc': comissao_perc,
                'comissao_valor': comissao_valor
            }

            assistente_info = None
            assistente_perc = servico.get('assistente_comissao_perc')
            assistente_servico = servico.get('assistente_servico') or servico.get('nome')

            if servico.get('assistente_id'):
                assistente_info = get_assistente_details(
                    servico.get('assistente_id'),
                    servico.get('assistente_tipo')
                )
                if assistente_perc is None:
                    assistente_perc = servico.get('assistente_comissao_perc', profissional.get('comissao_assistente_perc', 0))
            else:
                assistente_info = get_assistente_details(
                    profissional.get('assistente_id'),
                    profissional.get('assistente_tipo')
                )
                if assistente_perc is None:
                    assistente_perc = profissional.get('comissao_assistente_perc', 0)

            if assistente_info and assistente_perc:
                assistente_perc = float(assistente_perc)
                comissao_assistente_valor = comissao_valor * (assistente_perc / 100)
                comissao_info['assistente'] = {
                    'assistente_id': assistente_info.get('_id'),
                    'assistente_nome': assistente_info.get('nome', ''),
                    'assistente_tipo': assistente_info.get('tipo_origem'),
                    'comissao_perc': assistente_perc,
                    'comissao_valor': comissao_assistente_valor,
                    'servico': assistente_servico
                }
                total_comissoes += comissao_assistente_valor

            comissao_info['descricao'] = f"Profissional {profissional.get('nome')} - {servico.get('nome')}"
            if assistente_info:
                comissao_info['descricao'] += f" | Assistente {assistente_info.get('nome', '')} - {assistente_servico}"

            comissoes.append(comissao_info)
            total_comissoes += comissao_valor

        return jsonify({
            'success': True,
            'orcamento_numero': orcamento.get('numero'),
            'comissoes': comissoes,
            'total_comissoes': total_comissoes
        })

    except Exception as e:
        logger.error(f"Erro ao calcular comissoes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/profissionais/<id>/avaliacoes', methods=['GET', 'POST'])
@login_required
def profissional_avaliacoes(id):
    """Registrar e listar avaliacoes de profissionais."""
    if db is None:
        return jsonify({'success': False}), 500

    try:
        ObjectId(id)
    except Exception:
        return jsonify({'success': False, 'message': 'ID de profissional invalido'}), 400

    if request.method == 'GET':
        try:
            avaliacoes = list(db.profissionais_avaliacoes.find(
                {'profissional_id': id}
            ).sort('created_at', DESCENDING).limit(50))
            return jsonify({'success': True, 'avaliacoes': convert_objectid(avaliacoes)})
        except Exception as e:
            logger.error(f"Erro ao listar avaliacoes: {e}")
            return jsonify({'success': False, 'message': 'Erro ao listar avaliacoes'}), 500

    data = request.json or {}
    try:
        nota = float(data.get('nota', 0))
        nota = max(0, min(5, nota))
        avaliacao = {
            'profissional_id': id,
            'nota': nota,
            'comentario': data.get('comentario', '').strip(),
            'autor': data.get('autor', session.get('username', 'anonimo')),
            'created_at': datetime.now()
        }
        db.profissionais_avaliacoes.insert_one(avaliacao)
        clear_cache('profissionais_list')
        return jsonify({'success': True, 'avaliacao': convert_objectid(avaliacao)})
    except Exception as e:
        logger.error(f"Erro ao registrar avaliacao: {e}")
        return jsonify({'success': False, 'message': 'Erro ao registrar avaliacao'}), 500


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

@app.route('/api/estoque/entrada', methods=['POST'])
@login_required
def registrar_entrada_estoque():
    '''Registrar uma nova entrada de estoque que deve ser aprovada.'''
    if db is None:
        return jsonify({'success': False}), 500

    data = request.json or {}
    try:
        produto_id = data.get('produto_id')
        if not produto_id:
            return jsonify({'success': False, 'message': 'Produto obrigatorio'}), 400

        produto = db.produtos.find_one({'_id': ObjectId(produto_id)})
        if not produto:
            return jsonify({'success': False, 'message': 'Produto nao encontrado'}), 404

        quantidade = int(data.get('quantidade', 0))
        if quantidade <= 0:
            return jsonify({'success': False, 'message': 'Quantidade invalida'}), 400

        entrada_data = {
            'produto_id': ObjectId(produto_id),
            'produto_nome': produto.get('nome'),
            'quantidade': quantidade,
            'fornecedor': data.get('fornecedor', ''),
            'motivo': data.get('motivo', 'Entrada manual'),
            'nota_fiscal': data.get('nota_fiscal', ''),
            'previsao_chegada': data.get('previsao_chegada'),
            'status': 'Pendente',
            'usuario': session.get('username', 'sistema'),
            'data': datetime.now(),
            'updated_at': datetime.now()
        }

        db.estoque_entradas_pendentes.insert_one(entrada_data)
        logger.info(f"Entrada de estoque registrada para produto {produto_id}")
        return jsonify({'success': True, 'message': 'Entrada registrada e aguardando aprovacao'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Quantidade deve ser numerica'}), 400
    except Exception as e:
        logger.error(f"Erro ao registrar entrada: {e}")
        return jsonify({'success': False, 'message': 'Erro interno ao registrar entrada'}), 500


@app.route('/api/estoque/entrada/pendentes', methods=['GET'])
@login_required
def estoque_entradas_pendentes():
    '''Listar entradas de estoque pendentes de aprovacao.'''
    if db is None:
        return jsonify({'success': False}), 500

    try:
        entradas = list(db.estoque_entradas_pendentes.find({'status': 'Pendente'}).sort('data', DESCENDING))
        for entrada in entradas:
            produto = db.produtos.find_one({'_id': entrada['produto_id']})
            if produto:
                entrada['estoque_atual'] = produto.get('estoque', 0)
        return jsonify({'success': True, 'entradas': convert_objectid(entradas)})
    except Exception as e:
        logger.error(f"Erro ao listar pendencias de estoque: {e}")
        return jsonify({'success': False, 'message': 'Erro ao listar entradas pendentes'}), 500


@app.route('/api/estoque/entrada/<id>', methods=['PUT'])
@login_required
def atualizar_entrada_estoque(id):
    '''Atualizar uma entrada pendente antes da aprovacao.'''
    if db is None:
        return jsonify({'success': False}), 500

    data = request.json or {}
    try:
        entrada = db.estoque_entradas_pendentes.find_one({'_id': ObjectId(id)})
        if not entrada:
            return jsonify({'success': False, 'message': 'Entrada nao encontrada'}), 404
        if entrada.get('status') != 'Pendente':
            return jsonify({'success': False, 'message': 'Entrada ja processada'}), 400

        campos_atualizar = {}
        for campo in ['quantidade', 'fornecedor', 'motivo', 'nota_fiscal', 'previsao_chegada']:
            if campo in data:
                campos_atualizar[campo] = data[campo]

        if 'quantidade' in campos_atualizar:
            try:
                campos_atualizar['quantidade'] = int(campos_atualizar['quantidade'])
                if campos_atualizar['quantidade'] <= 0:
                    return jsonify({'success': False, 'message': 'Quantidade invalida'}), 400
            except ValueError:
                return jsonify({'success': False, 'message': 'Quantidade deve ser numerica'}), 400

        if not campos_atualizar:
            return jsonify({'success': False, 'message': 'Nenhum dado para atualizar'}), 400

        campos_atualizar['updated_at'] = datetime.now()
        db.estoque_entradas_pendentes.update_one({'_id': ObjectId(id)}, {'$set': campos_atualizar})
        logger.info(f"Entrada de estoque {id} atualizada")
        return jsonify({'success': True, 'message': 'Entrada atualizada com sucesso'})
    except Exception as e:
        logger.error(f"Erro ao atualizar entrada: {e}")
        return jsonify({'success': False, 'message': 'Erro ao atualizar entrada'}), 500


@app.route('/api/estoque/entrada/<id>/aprovar', methods=['POST'])
@login_required
def aprovar_entrada_estoque(id):
    '''Aprovar uma entrada de estoque pendente.'''
    if db is None:
        return jsonify({'success': False}), 500

    try:
        entrada = db.estoque_entradas_pendentes.find_one({'_id': ObjectId(id)})
        if not entrada:
            return jsonify({'success': False, 'message': 'Entrada nao encontrada'}), 404
        if entrada.get('status') != 'Pendente':
            return jsonify({'success': False, 'message': 'Entrada ja processada'}), 400

        produto = db.produtos.find_one({'_id': entrada['produto_id']})
        if not produto:
            return jsonify({'success': False, 'message': 'Produto nao encontrado para entrada'}), 404

        novo_estoque = produto.get('estoque', 0) + int(entrada.get('quantidade', 0))
        db.produtos.update_one({'_id': produto['_id']}, {'$set': {'estoque': novo_estoque, 'updated_at': datetime.now()}})

        db.estoque_movimentacoes.insert_one({
            'produto_id': produto['_id'],
            'tipo': 'entrada',
            'quantidade': int(entrada.get('quantidade', 0)),
            'motivo': entrada.get('motivo', 'Entrada aprovada'),
            'usuario': session.get('username', 'sistema'),
            'data': datetime.now()
        })

        db.estoque_entradas_pendentes.update_one({
            '_id': ObjectId(id)
        }, {
            '$set': {'status': 'Aprovado', 'aprovado_em': datetime.now(), 'aprovado_por': session.get('username')}
        })

        return jsonify({'success': True, 'message': 'Entrada aprovada e estoque atualizado'})
    except Exception as e:
        logger.error(f"Erro ao aprovar entrada: {e}")
        return jsonify({'success': False, 'message': 'Erro ao aprovar entrada'}), 500


@app.route('/api/estoque/entrada/<id>/rejeitar', methods=['POST'])
@login_required
def rejeitar_entrada_estoque(id):
    '''Rejeitar uma entrada pendente de estoque.'''
    if db is None:
        return jsonify({'success': False}), 500

    data = request.json or {}
    try:
        entrada = db.estoque_entradas_pendentes.find_one({'_id': ObjectId(id)})
        if not entrada:
            return jsonify({'success': False, 'message': 'Entrada nao encontrada'}), 404
        if entrada.get('status') != 'Pendente':
            return jsonify({'success': False, 'message': 'Entrada ja processada'}), 400

        motivo = data.get('motivo', '').strip() or 'Rejeitada sem motivo informado'
        db.estoque_entradas_pendentes.update_one({
            '_id': ObjectId(id)
        }, {
            '$set': {'status': 'Rejeitado', 'motivo_rejeicao': motivo, 'rejeitado_em': datetime.now(), 'rejeitado_por': session.get('username')}})

        logger.info(f"Entrada de estoque {id} rejeitada")
        return jsonify({'success': True, 'message': 'Entrada rejeitada'})
    except Exception as e:
        logger.error(f"Erro ao rejeitar entrada: {e}")
        return jsonify({'success': False, 'message': 'Erro ao rejeitar entrada'}), 500


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

@app.route('/api/estoque/movimentacoes', methods=['GET'])
@login_required
def listar_movimentacoes():
    """Listar movimentações de estoque com paginação e filtros"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        # Paginação
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        skip = (page - 1) * per_page
        
        # Filtros opcionais
        filtro = {}
        
        # Filtro por tipo de movimentação
        tipo = request.args.get('tipo')
        if tipo:
            filtro['tipo'] = tipo
        
        # Filtro por data (início)
        data_inicio = request.args.get('data_inicio')
        if data_inicio:
            try:
                filtro['data'] = {'$gte': datetime.fromisoformat(data_inicio)}
            except:
                pass
        
        # Filtro por data (fim)
        data_fim = request.args.get('data_fim')
        if data_fim:
            try:
                if 'data' in filtro:
                    filtro['data']['$lte'] = datetime.fromisoformat(data_fim)
                else:
                    filtro['data'] = {'$lte': datetime.fromisoformat(data_fim)}
            except:
                pass
        
        # Filtro por produto
        produto_id = request.args.get('produto_id')
        if produto_id:
            try:
                filtro['produto_id'] = ObjectId(produto_id)
            except:
                pass
        
        # Total de registros
        total = db.estoque_movimentacoes.count_documents(filtro)
        
        # Buscar movimentações com paginação
        movimentacoes = list(db.estoque_movimentacoes.find(filtro)
                            .sort('data', DESCENDING)
                            .skip(skip)
                            .limit(per_page))
        
        return jsonify({
            'success': True,
            'movimentacoes': convert_objectid(movimentacoes),
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
    except Exception as e:
        logger.error(f"Erro ao listar movimentações: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/saida', methods=['POST'])
@login_required
def registrar_saida_estoque():
    """Registrar saída de estoque"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    data = request.json or {}
    try:
        produto_id = data.get('produto_id')
        quantidade = int(data.get('quantidade', 0))
        motivo = data.get('motivo', '')
        
        if not produto_id or quantidade <= 0:
            return jsonify({'success': False, 'message': 'Dados inválidos'}), 400
        
        # Verificar se produto existe
        produto = db.produtos.find_one({'_id': ObjectId(produto_id)})
        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
        
        # Verificar estoque disponível
        estoque_atual = produto.get('estoque', 0)
        if estoque_atual < quantidade:
            return jsonify({
                'success': False, 
                'message': f'Estoque insuficiente. Disponível: {estoque_atual}'
            }), 400
        
        # Atualizar estoque
        novo_estoque = estoque_atual - quantidade
        db.produtos.update_one(
            {'_id': ObjectId(produto_id)},
            {'$set': {'estoque': novo_estoque, 'updated_at': datetime.now()}}
        )
        
        # Registrar movimentação
        movimentacao = {
            'produto_id': ObjectId(produto_id),
            'produto_nome': produto.get('nome'),
            'tipo': 'saida',
            'quantidade': quantidade,
            'motivo': motivo,
            'usuario': session.get('username', 'Desconhecido'),
            'data': datetime.now()
        }
        db.estoque_movimentacoes.insert_one(movimentacao)
        
        return jsonify({
            'success': True,
            'message': 'Saída registrada com sucesso',
            'estoque_atual': novo_estoque
        })
        
    except Exception as e:
        logger.error(f"Erro ao registrar saída: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/relatorio', methods=['GET'])
@login_required
def relatorio_estoque():
    """Gerar relatório completo de estoque com filtros e opção de export"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        # Filtros opcionais
        data_inicio_str = request.args.get('data_inicio')
        data_fim_str = request.args.get('data_fim')
        formato = request.args.get('formato', 'json')  # json ou excel
        
        # Total de produtos
        total_produtos = db.produtos.count_documents({})
        
        # Valor total do estoque
        produtos = list(db.produtos.find({}))
        valor_total = sum(p.get('preco', 0) * p.get('estoque', 0) for p in produtos)
        
        # Produtos com baixo estoque
        baixo_estoque = db.produtos.count_documents({
            '$expr': {'$lt': ['$estoque', '$estoque_minimo']}
        })
        
        # Produtos sem estoque
        sem_estoque = db.produtos.count_documents({'estoque': 0})
        
        # Filtro de data para movimentações
        filtro_data = {}
        if data_inicio_str:
            try:
                filtro_data['data'] = {'$gte': datetime.fromisoformat(data_inicio_str)}
            except:
                pass
        
        if data_fim_str:
            try:
                if 'data' in filtro_data:
                    filtro_data['data']['$lte'] = datetime.fromisoformat(data_fim_str)
                else:
                    filtro_data['data'] = {'$lte': datetime.fromisoformat(data_fim_str)}
            except:
                pass
        
        # Últimas movimentações (com filtro de data se aplicável)
        ultimas_movimentacoes = list(db.estoque_movimentacoes.find(filtro_data)
                                     .sort('data', DESCENDING)
                                     .limit(10))
        
        # Produtos mais movimentados (com filtro de data)
        if not filtro_data:
            filtro_data['data'] = {'$gte': datetime.now() - timedelta(days=30)}
        
        pipeline = [
            {'$match': filtro_data},
            {'$group': {
                '_id': '$produto_id',
                'total_movimentacoes': {'$sum': 1},
                'total_quantidade': {'$sum': '$quantidade'}
            }},
            {'$sort': {'total_movimentacoes': -1}},
            {'$limit': 5}
        ]
        mais_movimentados = list(db.estoque_movimentacoes.aggregate(pipeline))
        
        # Enriquecer com nomes dos produtos
        for item in mais_movimentados:
            produto = db.produtos.find_one({'_id': item['_id']})
            if produto:
                item['produto_nome'] = produto.get('nome')
        
        relatorio_data = {
            'total_produtos': total_produtos,
            'valor_total_estoque': round(valor_total, 2),
            'produtos_baixo_estoque': baixo_estoque,
            'produtos_sem_estoque': sem_estoque,
            'ultimas_movimentacoes': convert_objectid(ultimas_movimentacoes),
            'mais_movimentados': convert_objectid(mais_movimentados),
            'periodo': {
                'inicio': data_inicio_str,
                'fim': data_fim_str
            }
        }
        
        # Export para Excel
        if formato == 'excel':
            wb = Workbook()
            ws = wb.active
            ws.title = 'Relatório de Estoque'
            
            # Cabeçalho
            ws.append(['RELATÓRIO DE ESTOQUE'])
            ws.append([''])
            ws.append(['Total de Produtos', total_produtos])
            ws.append(['Valor Total Estoque', f'R$ {valor_total:.2f}'])
            ws.append(['Produtos Baixo Estoque', baixo_estoque])
            ws.append(['Produtos Sem Estoque', sem_estoque])
            ws.append([''])
            
            # Produtos mais movimentados
            ws.append(['PRODUTOS MAIS MOVIMENTADOS'])
            ws.append(['Produto', 'Total Movimentações', 'Quantidade Total'])
            for item in mais_movimentados:
                ws.append([
                    item.get('produto_nome', 'N/A'),
                    item.get('total_movimentacoes', 0),
                    item.get('total_quantidade', 0)
                ])
            
            # Salvar em buffer
            excel_buffer = BytesIO()
            wb.save(excel_buffer)
            excel_buffer.seek(0)
            
            return send_file(
                excel_buffer,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'relatorio_estoque_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
        
        # Retorno JSON padrão
        return jsonify({
            'success': True,
            'relatorio': relatorio_data
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

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


@app.route('/api/estoque/importar', methods=['POST'])
@login_required
def estoque_importar_alias():
    """Alias para importação de planilhas do estoque; reutiliza a rota /api/importar existente."""
    return importar()

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
        headers = ['nome','marca','sku','preco','custo','estoque','estoque_minimo','categoria']
    elif tipo == 'clientes':
        ws.title = 'Clientes BIOMA'
        headers = ['cpf','nome','email','telefone','genero','data_nascimento','endereco']
    elif tipo == 'profissionais':
        ws.title = 'Profissionais BIOMA'
        headers = ['cpf','nome','especialidade','email','telefone','comissao_perc','assistente_id','comissao_assistente_perc']
    else:
        # serviços (padrão)
        ws.title = 'Servicos BIOMA'
        headers = ['nome','tamanho','sku','preco','categoria','duracao_min']
    ws.append(headers)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = border
    # largura de colunas básica (A..I)
    for i, col in enumerate(['A','B','C','D','E','F','G','H','I'], start=1):
        try:
            ws.column_dimensions[col].width = 18
        except Exception:
            pass
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f'template_{tipo}_bioma.xlsx')



@app.route('/api/clientes/formularios', methods=['GET'])
@login_required
def clientes_formularios():
    """Retorna a configuração dos formulários de Anamnese e Prontuário para renderização dinâmica no front."""
    try:
        return jsonify({
            'success': True,
            'anamnese': ANAMNESE_FORM,
            'prontuario': PRONTUARIO_FORM
        })
    except Exception as e:
        logger.exception("Erro ao carregar formulários")
        return jsonify({'success': False, 'message': str(e)}), 500
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

@app.route('/api/auditoria', methods=['GET'])
@login_required
def consultar_auditoria():
    """Consultar logs de auditoria do sistema"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        # Paginação
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        skip = (page - 1) * per_page
        
        # Filtros
        filtro = {}
        
        # Filtro por usuário
        username = request.args.get('username')
        if username:
            filtro['username'] = {'$regex': username, '$options': 'i'}
        
        # Filtro por ação
        acao = request.args.get('acao')
        if acao:
            filtro['acao'] = acao
        
        # Filtro por entidade
        entidade = request.args.get('entidade')
        if entidade:
            filtro['entidade'] = entidade
        
        # Filtro por data
        data_inicio = request.args.get('data_inicio')
        if data_inicio:
            try:
                filtro['timestamp'] = {'$gte': datetime.fromisoformat(data_inicio)}
            except:
                pass
        
        data_fim = request.args.get('data_fim')
        if data_fim:
            try:
                if 'timestamp' in filtro:
                    filtro['timestamp']['$lte'] = datetime.fromisoformat(data_fim)
                else:
                    filtro['timestamp'] = {'$lte': datetime.fromisoformat(data_fim)}
            except:
                pass
        
        # Total de registros
        total = db.auditoria.count_documents(filtro)
        
        # Buscar registros
        registros = list(db.auditoria.find(filtro)
                        .sort('timestamp', DESCENDING)
                        .skip(skip)
                        .limit(per_page))
        
        # Estatísticas rápidas
        stats = {
            'total_acoes': total,
            'acoes_por_tipo': list(db.auditoria.aggregate([
                {'$match': filtro},
                {'$group': {'_id': '$acao', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}
            ])),
            'usuarios_ativos': list(db.auditoria.aggregate([
                {'$match': filtro},
                {'$group': {'_id': '$username', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}},
                {'$limit': 10}
            ]))
        }
        
        return jsonify({
            'success': True,
            'registros': convert_objectid(registros),
            'stats': stats,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao consultar auditoria: {e}")
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
        db.profissionais_avaliacoes.create_index([('profissional_id', ASCENDING), ('created_at', DESCENDING)])
        logger.info('Database indexes created')
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

# ==================== NOVAS FUNCIONALIDADES v3.7 ====================

# 1. Upload de Logo da Empresa
@app.route('/api/upload/logo', methods=['POST'])
@login_required
def upload_logo():
    """Upload de logo da empresa"""
    try:
        if 'logo' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['logo']
        tipo = request.form.get('tipo', 'principal')  # principal ou login
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Arquivo vazio'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"logo_{tipo}_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Salvar referência no banco
            db.uploads.insert_one({
                'tipo': f'logo_{tipo}',
                'filename': filename,
                'path': filepath,
                'url': f'/uploads/{filename}',
                'data_upload': datetime.now()
            })
            
            return jsonify({
                'success': True,
                'message': 'Logo enviado com sucesso',
                'url': f'/uploads/{filename}'
            })
        
        return jsonify({'success': False, 'message': 'Tipo de arquivo não permitido'}), 400
    except Exception as e:
        logger.error(f"Erro no upload de logo: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 1.1. Upload de Imagem (Alias para compatibilidade)
@app.route('/api/upload/imagem', methods=['POST'])
@login_required
def upload_imagem():
    """Alias para compatibilidade com frontend"""
    return upload_logo()

# 2. Obter Logo Configurado
@app.route('/api/config/logo', methods=['GET'])
def get_logo():
    """Obter URL do logo configurado"""
    try:
        tipo = request.args.get('tipo', 'principal')
        logo = db.uploads.find_one({'tipo': f'logo_{tipo}'}, sort=[('data_upload', DESCENDING)])
        
        if logo:
            return jsonify({'success': True, 'url': logo.get('url')})
        return jsonify({'success': True, 'url': None})
    except Exception as e:
        logger.error(f"Erro ao obter logo: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 3. Servir Arquivos Uploaded
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Servir arquivo uploaded"""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        return send_file(filepath)
    except Exception as e:
        logger.error(f"Erro ao servir arquivo: {e}")
        return jsonify({'success': False, 'message': 'Arquivo não encontrado'}), 404

# 4. Upload de Foto de Profissional
@app.route('/api/upload/foto-profissional', methods=['POST'])
@login_required
def upload_foto_profissional():
    """Upload de foto de perfil de profissional"""
    try:
        if 'foto' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['foto']
        profissional_id = request.form.get('profissional_id')
        
        if not profissional_id:
            return jsonify({'success': False, 'message': 'ID do profissional não fornecido'}), 400
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Arquivo vazio'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"prof_{profissional_id}_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            url = f'/uploads/{filename}'
            
            # Atualizar profissional com a foto
            db.profissionais.update_one(
                {'_id': ObjectId(profissional_id)},
                {'$set': {'foto': url}}
            )
            
            # Salvar referência no banco
            db.uploads.insert_one({
                'tipo': 'foto_profissional',
                'profissional_id': ObjectId(profissional_id),
                'filename': filename,
                'path': filepath,
                'url': url,
                'data_upload': datetime.now()
            })
            
            return jsonify({
                'success': True,
                'message': 'Foto enviada com sucesso',
                'url': url
            })
        
        return jsonify({'success': False, 'message': 'Tipo de arquivo não permitido'}), 400
    except Exception as e:
        logger.error(f"Erro no upload de foto: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 5. Calcular Comissões Multiníveis
@app.route('/api/comissoes/calcular-orcamento', methods=['POST'])
@login_required
def calcular_comissoes_orcamento():
    """Calcula comissões em cascata: profissional + assistente"""
    try:
        data = request.get_json()
        orcamento_id = data.get('orcamento_id')
        
        if not orcamento_id:
            return jsonify({'success': False, 'message': 'ID do orçamento não fornecido'}), 400
        
        orcamento = db.orcamentos.find_one({'_id': ObjectId(orcamento_id)})
        if not orcamento:
            return jsonify({'success': False, 'message': 'Orçamento não encontrado'}), 404
        
        # Buscar dados do profissional
        profissional = db.profissionais.find_one({'_id': ObjectId(orcamento.get('profissional_id'))})
        if not profissional:
            return jsonify({'success': False, 'message': 'Profissional não encontrado'}), 404
        
        # Calcular comissão do profissional
        valor_total = orcamento.get('total', 0)
        comissao_perc = profissional.get('comissao_perc', 10)
        comissao_profissional = valor_total * (comissao_perc / 100)
        
        resultado = {
            'orcamento_id': str(orcamento_id),
            'valor_total': valor_total,
            'profissional': {
                'id': str(profissional['_id']),
                'nome': profissional.get('nome'),
                'foto': profissional.get('foto'),
                'comissao_percentual': comissao_perc,
                'comissao_valor': round(comissao_profissional, 2)
            }
        }
        
        # Calcular comissão do assistente (10% da comissão do profissional)
        assistentes = profissional.get('assistentes', [])
        if assistentes:
            assistente_principal = assistentes[0]
            assistente_id = assistente_principal.get('_id') if isinstance(assistente_principal, dict) else assistente_principal
            
            assistente_doc = db.assistentes.find_one({'_id': ObjectId(assistente_id)})
            if assistente_doc:
                comissao_assistente = comissao_profissional * 0.1  # 10% da comissão do profissional
                resultado['assistente'] = {
                    'id': str(assistente_doc['_id']),
                    'nome': assistente_doc.get('nome'),
                    'foto': assistente_doc.get('foto'),
                    'comissao_percentual': 10,
                    'comissao_valor': round(comissao_assistente, 2)
                }
                resultado['total_comissoes'] = round(comissao_profissional + comissao_assistente, 2)
            else:
                resultado['total_comissoes'] = round(comissao_profissional, 2)
        else:
            resultado['total_comissoes'] = round(comissao_profissional, 2)
        
        # Salvar no histórico
        db.comissoes_historico.insert_one({
            'orcamento_id': ObjectId(orcamento_id),
            'profissional_id': ObjectId(profissional['_id']),
            'profissional_comissao': resultado['profissional']['comissao_valor'],
            'assistente_id': ObjectId(resultado['assistente']['id']) if 'assistente' in resultado else None,
            'assistente_comissao': resultado.get('assistente', {}).get('comissao_valor', 0),
            'total': resultado['total_comissoes'],
            'data_calculo': datetime.now()
        })
        
        return jsonify({'success': True, 'comissoes': resultado})
    except Exception as e:
        logger.error(f"Erro ao calcular comissões: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 6. Histórico de Comissões
@app.route('/api/comissoes/historico', methods=['GET'])
@login_required
def historico_comissoes():
    """Lista histórico de comissões calculadas"""
    try:
        historico = list(db.comissoes_historico.find().sort('data_calculo', DESCENDING).limit(50))
        
        for item in historico:
            item['_id'] = str(item['_id'])
            item['orcamento_id'] = str(item.get('orcamento_id'))
            item['profissional_id'] = str(item.get('profissional_id'))
            if item.get('assistente_id'):
                item['assistente_id'] = str(item['assistente_id'])
            
            # Buscar nomes
            prof = db.profissionais.find_one({'_id': ObjectId(item['profissional_id'])})
            if prof:
                item['profissional_nome'] = prof.get('nome')
            
            if item.get('assistente_id'):
                asst = db.assistentes.find_one({'_id': ObjectId(item['assistente_id'])})
                if asst:
                    item['assistente_nome'] = asst.get('nome')
        
        return jsonify({'success': True, 'historico': historico})
    except Exception as e:
        logger.error(f"Erro ao buscar histórico: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 7. Cadastrar Assistente Independente
@app.route('/api/assistentes/cadastrar-independente', methods=['POST'])
@login_required
def cadastrar_assistente_independente():
    """Cadastra assistente sem vínculo obrigatório com profissional"""
    try:
        data = request.get_json()
        
        assistente = {
            'nome': data.get('nome'),
            'cpf': data.get('cpf'),
            'telefone': data.get('telefone'),
            'email': data.get('email'),
            'profissional_id': None,  # Independente
            'ativo': True,
            'created_at': datetime.now()
        }
        
        result = db.assistentes.insert_one(assistente)
        assistente['_id'] = str(result.inserted_id)
        
        return jsonify({'success': True, 'assistente': assistente})
    except Exception as e:
        logger.error(f"Erro ao cadastrar assistente: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 8. Registrar Entrada de Produto (com aprovação)
@app.route('/api/estoque/produtos/entrada', methods=['POST'])
@login_required
def registrar_entrada_produto():
    """Registra entrada de produto que precisa ser aprovada"""
    try:
        data = request.get_json()
        
        produto = db.produtos.find_one({'_id': ObjectId(data.get('produto_id'))})
        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
        
        entrada = {
            'produto_id': ObjectId(data.get('produto_id')),
            'produto_nome': produto.get('nome'),
            'quantidade': data.get('quantidade'),
            'fornecedor': data.get('fornecedor'),
            'motivo': data.get('motivo'),
            'usuario': session.get('user', {}).get('name', 'Desconhecido'),
            'status': 'pendente',
            'data_solicitacao': datetime.now(),
            'data_processamento': None
        }
        
        result = db.estoque_pendencias.insert_one(entrada)
        entrada['_id'] = str(result.inserted_id)
        
        return jsonify({'success': True, 'entrada': entrada, 'message': 'Entrada registrada. Aguardando aprovação.'})
    except Exception as e:
        logger.error(f"Erro ao registrar entrada: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 9. Aprovar Entrada de Produto
@app.route('/api/estoque/produtos/aprovar/<id>', methods=['POST'])
@login_required
def aprovar_entrada_produto(id):
    """Aprova entrada de produto e atualiza estoque"""
    try:
        entrada = db.estoque_pendencias.find_one({'_id': ObjectId(id)})
        if not entrada:
            return jsonify({'success': False, 'message': 'Entrada não encontrada'}), 404
        
        # Atualizar status da entrada
        db.estoque_pendencias.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'status': 'aprovado', 'data_processamento': datetime.now()}}
        )
        
        # Atualizar estoque do produto
        db.produtos.update_one(
            {'_id': entrada['produto_id']},
            {'$inc': {'estoque': entrada['quantidade']}}
        )
        
        # Registrar movimentação
        db.estoque_movimentacoes.insert_one({
            'produto_id': entrada['produto_id'],
            'produto_nome': entrada['produto_nome'],
            'tipo': 'entrada',
            'quantidade': entrada['quantidade'],
            'motivo': f"Aprovação: {entrada.get('motivo', '')}",
            'usuario': session.get('user', {}).get('name'),
            'data': datetime.now()
        })
        
        return jsonify({'success': True, 'message': 'Entrada aprovada e estoque atualizado'})
    except Exception as e:
        logger.error(f"Erro ao aprovar entrada: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 10. Rejeitar Entrada de Produto
@app.route('/api/estoque/produtos/rejeitar/<id>', methods=['POST'])
@login_required
def rejeitar_entrada_produto(id):
    """Rejeita entrada de produto"""
    try:
        db.estoque_pendencias.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'status': 'rejeitado', 'data_processamento': datetime.now()}}
        )
        
        return jsonify({'success': True, 'message': 'Entrada rejeitada'})
    except Exception as e:
        logger.error(f"Erro ao rejeitar entrada: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 11. Listar Entradas Pendentes
@app.route('/api/estoque/produtos/pendentes', methods=['GET'])
@login_required
def listar_entradas_pendentes():
    """Lista entradas de produtos pendentes de aprovação"""
    try:
        pendentes = list(db.estoque_pendencias.find({'status': 'pendente'}).sort('data_solicitacao', DESCENDING))
        
        for item in pendentes:
            item['_id'] = str(item['_id'])
            item['produto_id'] = str(item.get('produto_id'))
        
        return jsonify({'success': True, 'entradas': pendentes})
    except Exception as e:
        logger.error(f"Erro ao listar pendentes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 12. Mapa de Calor
@app.route('/api/relatorios/mapa-calor', methods=['GET'])
@login_required
def mapa_calor():
    """Retorna dados para mapa de calor de movimentação"""
    try:
        # Últimos 90 dias
        data_inicio = datetime.now() - timedelta(days=90)
        
        # Agregar atendimentos por dia
        pipeline = [
            {'$match': {'created_at': {'$gte': data_inicio}}},
            {'$group': {
                '_id': {
                    '$dateToString': {'format': '%Y-%m-%d', 'date': '$created_at'}
                },
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id': 1}}
        ]
        
        # Buscar de múltiplas collections
        agendamentos = list(db.agendamentos.aggregate(pipeline))
        orcamentos = list(db.orcamentos.aggregate(pipeline))
        
        # Combinar resultados
        dias_map = {}
        for item in agendamentos + orcamentos:
            data = item['_id']
            if data in dias_map:
                dias_map[data] += item['count']
            else:
                dias_map[data] = item['count']
        
        # Formatar para array
        dados = [{'data': k, 'intensidade': v} for k, v in dias_map.items()]
        
        return jsonify({'success': True, 'dados': dados})
    except Exception as e:
        logger.error(f"Erro ao gerar mapa de calor: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 13. Editar Serviço
@app.route('/api/servicos/<id>/editar', methods=['PUT'])
@login_required
def editar_servico(id):
    """Edita informações de um serviço"""
    try:
        data = request.get_json()
        
        update_data = {}
        if 'nome' in data:
            update_data['nome'] = data['nome']
        if 'preco' in data:
            update_data['preco'] = float(data['preco'])
        if 'duracao' in data:
            update_data['duracao'] = int(data['duracao'])
        if 'categoria' in data:
            update_data['categoria'] = data['categoria']
        if 'tamanho' in data:
            update_data['tamanho'] = data['tamanho']
        
        if not update_data:
            return jsonify({'success': False, 'message': 'Nenhum dado para atualizar'}), 400
        
        result = db.servicos.update_one(
            {'_id': ObjectId(id)},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Serviço atualizado com sucesso'})
        return jsonify({'success': False, 'message': 'Nenhuma alteração realizada'}), 400
    except Exception as e:
        logger.error(f"Erro ao editar serviço: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 14. Editar Produto
@app.route('/api/produtos/<id>/editar', methods=['PUT'])
@login_required
def editar_produto(id):
    """Edita informações de um produto"""
    try:
        data = request.get_json()
        
        update_data = {}
        if 'nome' in data:
            update_data['nome'] = data['nome']
        if 'marca' in data:
            update_data['marca'] = data['marca']
        if 'preco' in data:
            update_data['preco'] = float(data['preco'])
        if 'estoque_minimo' in data:
            update_data['estoque_minimo'] = int(data['estoque_minimo'])
        if 'sku' in data:
            update_data['sku'] = data['sku']
        
        if not update_data:
            return jsonify({'success': False, 'message': 'Nenhum dado para atualizar'}), 400
        
        result = db.produtos.update_one(
            {'_id': ObjectId(id)},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Produto atualizado com sucesso'})
        return jsonify({'success': False, 'message': 'Nenhuma alteração realizada'}), 400
    except Exception as e:
        logger.error(f"Erro ao editar produto: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 15. Faturamento Total do Cliente
@app.route('/api/clientes/<id>/faturamento', methods=['GET'])
@login_required
def faturamento_cliente(id):
    """Retorna faturamento total de um cliente"""
    try:
        pipeline = [
            {'$match': {'cliente_id': ObjectId(id), 'status': 'aprovado'}},
            {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
        ]
        
        resultado = list(db.orcamentos.aggregate(pipeline))
        total = resultado[0]['total'] if resultado else 0
        
        return jsonify({'success': True, 'faturamento_total': round(total, 2)})
    except Exception as e:
        logger.error(f"Erro ao calcular faturamento: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 16. Anamnese do Cliente (GET/PUT)
@app.route('/api/clientes/<id>/anamnese', methods=['GET', 'PUT'])
@login_required
def anamnese_cliente(id):
    """Gerencia anamnese do cliente"""
    try:
        if request.method == 'GET':
            cliente = db.clientes.find_one({'_id': ObjectId(id)})
            if not cliente:
                return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
            
            anamnese = cliente.get('anamnese', {})
            return jsonify({'success': True, 'anamnese': anamnese})
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            db.clientes.update_one(
                {'_id': ObjectId(id)},
                {'$set': {'anamnese': data}}
            )
            
            return jsonify({'success': True, 'message': 'Anamnese salva com sucesso'})
    except Exception as e:
        logger.error(f"Erro na anamnese: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 17. Prontuário do Cliente (GET/PUT)
@app.route('/api/clientes/<id>/prontuario', methods=['GET', 'PUT'])
@login_required
def prontuario_cliente(id):
    """Gerencia prontuário do cliente"""
    try:
        if request.method == 'GET':
            cliente = db.clientes.find_one({'_id': ObjectId(id)})
            if not cliente:
                return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
            
            prontuario = cliente.get('prontuario', [])
            return jsonify({'success': True, 'prontuario': prontuario})
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            # Adicionar novo registro ao prontuário
            db.clientes.update_one(
                {'_id': ObjectId(id)},
                {'$push': {'prontuario': {
                    'data': datetime.now(),
                    'procedimento': data.get('procedimento'),
                    'observacoes': data.get('observacoes'),
                    'profissional': data.get('profissional')
                }}}
            )
            
            return jsonify({'success': True, 'message': 'Registro adicionado ao prontuário'})
    except Exception as e:
        logger.error(f"Erro no prontuário: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 18. Gerar PDF Resumo do Cliente
@app.route('/api/clientes/<id>/resumo-pdf', methods=['GET'])
@login_required
def resumo_pdf_cliente(id):
    """Gera PDF completo com todos os dados do cliente"""
    try:
        cliente = db.clientes.find_one({'_id': ObjectId(id)})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
        
        # Criar PDF em memória
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#7C3AED'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        elements.append(Paragraph('RESUMO DO CLIENTE', title_style))
        elements.append(Spacer(1, 20))
        
        # Dados pessoais
        elements.append(Paragraph('<b>DADOS PESSOAIS</b>', styles['Heading2']))
        dados = [
            ['Nome:', cliente.get('nome', '-')],
            ['CPF:', cliente.get('cpf', '-')],
            ['Telefone:', cliente.get('telefone', '-')],
            ['Email:', cliente.get('email', '-')],
        ]
        t = Table(dados, colWidths=[4*cm, 12*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#E5E7EB'))
        ]))
        elements.append(t)
        elements.append(Spacer(1, 20))
        
        # Anamnese
        anamnese = cliente.get('anamnese', {})
        if anamnese:
            elements.append(Paragraph('<b>ANAMNESE</b>', styles['Heading2']))
            for key, value in anamnese.items():
                elements.append(Paragraph(f'<b>{key}:</b> {value}', styles['Normal']))
            elements.append(Spacer(1, 20))
        
        # Prontuário
        prontuario = cliente.get('prontuario', [])
        if prontuario:
            elements.append(Paragraph('<b>PRONTUÁRIO</b>', styles['Heading2']))
            for registro in prontuario:
                elements.append(Paragraph(
                    f"<b>Data:</b> {registro.get('data', '-')} | "
                    f"<b>Procedimento:</b> {registro.get('procedimento', '-')}<br/>"
                    f"<b>Observações:</b> {registro.get('observacoes', '-')}",
                    styles['Normal']
                ))
                elements.append(Spacer(1, 10))
        
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'cliente_{cliente.get("nome", "resumo")}.pdf'
        )
    except Exception as e:
        logger.error(f"Erro ao gerar PDF: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== SISTEMA DE ANAMNESE E PRONTUÁRIO ====================

@app.route('/api/clientes/<cpf>/anamnese', methods=['GET', 'POST'])
@login_required
def handle_anamnese(cpf):
    """Gerenciar histórico de anamneses de um cliente"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        # Buscar cliente
        cliente = db.clientes.find_one({'cpf': cpf})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
        
        if request.method == 'GET':
            # Listar histórico de anamneses
            anamneses = list(db.anamneses.find({'cliente_cpf': cpf}).sort('data_cadastro', DESCENDING))
            
            for anamnese in anamneses:
                anamnese['_id'] = str(anamnese['_id'])
                if 'data_cadastro' in anamnese and isinstance(anamnese['data_cadastro'], datetime):
                    anamnese['data_cadastro'] = anamnese['data_cadastro'].isoformat()
            
            logger.info(f"📋 Listando {len(anamneses)} anamneses do cliente {cpf}")
            return jsonify({
                'success': True,
                'cliente': {
                    'cpf': cliente.get('cpf'),
                    'nome': cliente.get('nome')
                },
                'anamneses': anamneses
            })
        
        elif request.method == 'POST':
            # Criar nova anamnese
            data = request.json
            logger.info(f"📝 Criando anamnese para cliente {cpf}")
            
            anamnese = {
                'cliente_cpf': cpf,
                'cliente_nome': cliente.get('nome'),
                'respostas': data.get('respostas', {}),
                'observacoes': data.get('observacoes', ''),
                'data_cadastro': datetime.now(),
                'cadastrado_por': session.get('username'),
                'versao': db.anamneses.count_documents({'cliente_cpf': cpf}) + 1
            }
            
            result = db.anamneses.insert_one(anamnese)
            anamnese['_id'] = str(result.inserted_id)
            anamnese['data_cadastro'] = anamnese['data_cadastro'].isoformat()
            
            # Atualizar campo anamnese_atualizada no cliente
            db.clientes.update_one(
                {'cpf': cpf},
                {'$set': {'anamnese_atualizada': datetime.now()}}
            )
            
            logger.info(f"✅ Anamnese v{anamnese['versao']} criada para {cpf}")
            return jsonify({'success': True, 'anamnese': anamnese})
            
    except Exception as e:
        logger.error(f"❌ Erro em handle_anamnese: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clientes/<cpf>/anamnese/<id>', methods=['GET', 'DELETE'])
@login_required
def handle_anamnese_by_id(cpf, id):
    """Gerenciar anamnese específica"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        if request.method == 'GET':
            anamnese = db.anamneses.find_one({'_id': ObjectId(id), 'cliente_cpf': cpf})
            if not anamnese:
                return jsonify({'success': False, 'message': 'Anamnese não encontrada'}), 404
            
            anamnese['_id'] = str(anamnese['_id'])
            if 'data_cadastro' in anamnese and isinstance(anamnese['data_cadastro'], datetime):
                anamnese['data_cadastro'] = anamnese['data_cadastro'].isoformat()
            
            return jsonify({'success': True, 'anamnese': anamnese})
        
        elif request.method == 'DELETE':
            result = db.anamneses.delete_one({'_id': ObjectId(id), 'cliente_cpf': cpf})
            if result.deleted_count == 0:
                return jsonify({'success': False, 'message': 'Anamnese não encontrada'}), 404
            
            logger.info(f"🗑️ Anamnese {id} deletada")
            return jsonify({'success': True, 'message': 'Anamnese deletada com sucesso'})
            
    except Exception as e:
        logger.error(f"❌ Erro em handle_anamnese_by_id: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clientes/<cpf>/prontuario', methods=['GET', 'POST'])
@login_required
def handle_prontuario(cpf):
    """Gerenciar histórico de prontuários de um cliente"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        # Buscar cliente
        cliente = db.clientes.find_one({'cpf': cpf})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
        
        if request.method == 'GET':
            # Listar histórico de prontuários
            prontuarios = list(db.prontuarios.find({'cliente_cpf': cpf}).sort('data_atendimento', DESCENDING))
            
            for pront in prontuarios:
                pront['_id'] = str(pront['_id'])
                if 'data_atendimento' in pront and isinstance(pront['data_atendimento'], datetime):
                    pront['data_atendimento'] = pront['data_atendimento'].isoformat()
                if 'data_cadastro' in pront and isinstance(pront['data_cadastro'], datetime):
                    pront['data_cadastro'] = pront['data_cadastro'].isoformat()
            
            logger.info(f"📋 Listando {len(prontuarios)} prontuários do cliente {cpf}")
            return jsonify({
                'success': True,
                'cliente': {
                    'cpf': cliente.get('cpf'),
                    'nome': cliente.get('nome')
                },
                'prontuarios': prontuarios
            })
        
        elif request.method == 'POST':
            # Criar novo prontuário
            data = request.json
            logger.info(f"📝 Criando prontuário para cliente {cpf}")
            
            prontuario = {
                'cliente_cpf': cpf,
                'cliente_nome': cliente.get('nome'),
                'data_atendimento': datetime.fromisoformat(data.get('data_atendimento', datetime.now().isoformat())),
                'profissional': data.get('profissional', ''),
                'procedimento': data.get('procedimento', ''),
                'produtos_utilizados': data.get('produtos_utilizados', []),
                'observacoes': data.get('observacoes', ''),
                'fotos_antes': data.get('fotos_antes', []),
                'fotos_depois': data.get('fotos_depois', []),
                'proxima_sessao': data.get('proxima_sessao', ''),
                'data_cadastro': datetime.now(),
                'cadastrado_por': session.get('username')
            }
            
            result = db.prontuarios.insert_one(prontuario)
            prontuario['_id'] = str(result.inserted_id)
            prontuario['data_atendimento'] = prontuario['data_atendimento'].isoformat()
            prontuario['data_cadastro'] = prontuario['data_cadastro'].isoformat()
            
            # Atualizar campo prontuario_atualizado no cliente
            db.clientes.update_one(
                {'cpf': cpf},
                {'$set': {'prontuario_atualizado': datetime.now()}}
            )
            
            logger.info(f"✅ Prontuário criado para {cpf}")
            return jsonify({'success': True, 'prontuario': prontuario})
            
    except Exception as e:
        logger.error(f"❌ Erro em handle_prontuario: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clientes/<cpf>/prontuario/<id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def handle_prontuario_by_id(cpf, id):
    """Gerenciar prontuário específico"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        if request.method == 'GET':
            prontuario = db.prontuarios.find_one({'_id': ObjectId(id), 'cliente_cpf': cpf})
            if not prontuario:
                return jsonify({'success': False, 'message': 'Prontuário não encontrado'}), 404
            
            prontuario['_id'] = str(prontuario['_id'])
            if 'data_atendimento' in prontuario and isinstance(prontuario['data_atendimento'], datetime):
                prontuario['data_atendimento'] = prontuario['data_atendimento'].isoformat()
            if 'data_cadastro' in prontuario and isinstance(prontuario['data_cadastro'], datetime):
                prontuario['data_cadastro'] = prontuario['data_cadastro'].isoformat()
            
            return jsonify({'success': True, 'prontuario': prontuario})
        
        elif request.method == 'PUT':
            data = request.json
            logger.info(f"📝 Atualizando prontuário {id}")
            
            update_data = {
                'data_atendimento': datetime.fromisoformat(data.get('data_atendimento', datetime.now().isoformat())),
                'profissional': data.get('profissional', ''),
                'procedimento': data.get('procedimento', ''),
                'produtos_utilizados': data.get('produtos_utilizados', []),
                'observacoes': data.get('observacoes', ''),
                'fotos_antes': data.get('fotos_antes', []),
                'fotos_depois': data.get('fotos_depois', []),
                'proxima_sessao': data.get('proxima_sessao', ''),
                'atualizado_em': datetime.now(),
                'atualizado_por': session.get('username')
            }
            
            result = db.prontuarios.update_one(
                {'_id': ObjectId(id), 'cliente_cpf': cpf},
                {'$set': update_data}
            )
            
            if result.matched_count == 0:
                return jsonify({'success': False, 'message': 'Prontuário não encontrado'}), 404
            
            logger.info(f"✅ Prontuário {id} atualizado")
            return jsonify({'success': True, 'message': 'Prontuário atualizado com sucesso'})
        
        elif request.method == 'DELETE':
            result = db.prontuarios.delete_one({'_id': ObjectId(id), 'cliente_cpf': cpf})
            if result.deleted_count == 0:
                return jsonify({'success': False, 'message': 'Prontuário não encontrado'}), 404
            
            logger.info(f"🗑️ Prontuário {id} deletado")
            return jsonify({'success': True, 'message': 'Prontuário deletado com sucesso'})
            
    except Exception as e:
        logger.error(f"❌ Erro em handle_prontuario_by_id: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== SISTEMA DE MULTICOMISSÕES ====================

@app.route('/api/orcamentos', methods=['GET', 'POST'])
@login_required
def handle_orcamentos():
    """Gerenciar orçamentos com suporte a múltiplos profissionais"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        if request.method == 'GET':
            # Listar orçamentos
            orcamentos = list(db.orcamentos.find().sort('created_at', DESCENDING).limit(100))
            for orc in orcamentos:
                orc['_id'] = str(orc['_id'])
                if 'created_at' in orc and isinstance(orc['created_at'], datetime):
                    orc['created_at'] = orc['created_at'].isoformat()
                # Converter ObjectIds dos profissionais vinculados
                if 'profissionais_vinculados' in orc:
                    for prof in orc['profissionais_vinculados']:
                        if 'profissional_id' in prof and isinstance(prof['profissional_id'], ObjectId):
                            prof['profissional_id'] = str(prof['profissional_id'])
            
            logger.info(f"📊 Listando {len(orcamentos)} orçamentos")
            return jsonify({'success': True, 'orcamentos': orcamentos})
        
        elif request.method == 'POST':
            # Criar novo orçamento
            data = request.json
            logger.info(f"💼 Criando orçamento para cliente: {data.get('cliente_nome')}")
            
            # Processar profissionais vinculados
            profissionais_vinculados = data.get('profissionais_vinculados', [])
            for prof in profissionais_vinculados:
                if 'profissional_id' in prof and isinstance(prof['profissional_id'], str):
                    try:
                        prof['profissional_id'] = ObjectId(prof['profissional_id'])
                    except:
                        pass
            
            # Gerar número do orçamento
            ultimo_orc = db.orcamentos.find_one(sort=[('numero', DESCENDING)])
            proximo_numero = (ultimo_orc.get('numero', 0) + 1) if ultimo_orc else 1
            
            orcamento = {
                'numero': proximo_numero,
                'cliente_cpf': data.get('cliente_cpf'),
                'cliente_nome': data.get('cliente_nome'),
                'cliente_telefone': data.get('cliente_telefone'),
                'cliente_email': data.get('cliente_email'),
                'servicos': data.get('servicos', []),
                'produtos': data.get('produtos', []),
                'profissionais_vinculados': profissionais_vinculados,
                'total_servicos': data.get('total_servicos', 0),
                'total_produtos': data.get('total_produtos', 0),
                'desconto_perc': data.get('desconto_perc', 0),
                'desconto_valor': data.get('desconto_valor', 0),
                'total_final': data.get('total_final', 0),
                'total_comissoes': sum(p.get('comissao_valor', 0) for p in profissionais_vinculados),
                'forma_pagamento': data.get('forma_pagamento'),
                'observacoes': data.get('observacoes', ''),
                'status': data.get('status', 'Pendente'),
                'created_at': datetime.now(),
                'created_by': session.get('username')
            }
            
            result = db.orcamentos.insert_one(orcamento)
            orcamento['_id'] = str(result.inserted_id)
            
            # Registrar comissões no histórico
            if profissionais_vinculados:
                for prof in profissionais_vinculados:
                    db.comissoes_historico.insert_one({
                        'orcamento_id': result.inserted_id,
                        'profissional_id': prof.get('profissional_id'),
                        'nome': prof.get('nome'),
                        'tipo': prof.get('tipo'),
                        'comissao_perc': prof.get('comissao_perc'),
                        'comissao_valor': prof.get('comissao_valor'),
                        'valor_base': data.get('total_servicos', 0),
                        'status_orcamento': orcamento['status'],
                        'data_registro': datetime.now()
                    })
            
            logger.info(f"✅ Orçamento #{proximo_numero} criado com {len(profissionais_vinculados)} profissionais")
            return jsonify({'success': True, 'orcamento': orcamento, 'numero': proximo_numero})
            
    except Exception as e:
        logger.error(f"❌ Erro em handle_orcamentos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/orcamentos/<id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def handle_orcamento_by_id(id):
    """Gerenciar orçamento específico"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        if request.method == 'GET':
            orcamento = db.orcamentos.find_one({'_id': ObjectId(id)})
            if not orcamento:
                return jsonify({'success': False, 'message': 'Orçamento não encontrado'}), 404
            
            orcamento['_id'] = str(orcamento['_id'])
            if 'created_at' in orcamento and isinstance(orcamento['created_at'], datetime):
                orcamento['created_at'] = orcamento['created_at'].isoformat()
            
            return jsonify({'success': True, 'orcamento': orcamento})
        
        elif request.method == 'PUT':
            data = request.json
            logger.info(f"📝 Atualizando orçamento {id}")
            
            # Processar profissionais vinculados
            profissionais_vinculados = data.get('profissionais_vinculados', [])
            for prof in profissionais_vinculados:
                if 'profissional_id' in prof and isinstance(prof['profissional_id'], str):
                    try:
                        prof['profissional_id'] = ObjectId(prof['profissional_id'])
                    except:
                        pass
            
            update_data = {
                'cliente_cpf': data.get('cliente_cpf'),
                'cliente_nome': data.get('cliente_nome'),
                'cliente_telefone': data.get('cliente_telefone'),
                'cliente_email': data.get('cliente_email'),
                'servicos': data.get('servicos', []),
                'produtos': data.get('produtos', []),
                'profissionais_vinculados': profissionais_vinculados,
                'total_servicos': data.get('total_servicos', 0),
                'total_produtos': data.get('total_produtos', 0),
                'desconto_perc': data.get('desconto_perc', 0),
                'desconto_valor': data.get('desconto_valor', 0),
                'total_final': data.get('total_final', 0),
                'total_comissoes': sum(p.get('comissao_valor', 0) for p in profissionais_vinculados),
                'forma_pagamento': data.get('forma_pagamento'),
                'observacoes': data.get('observacoes', ''),
                'status': data.get('status', 'Pendente'),
                'updated_at': datetime.now(),
                'updated_by': session.get('username')
            }
            
            db.orcamentos.update_one({'_id': ObjectId(id)}, {'$set': update_data})
            
            # Atualizar histórico de comissões
            db.comissoes_historico.delete_many({'orcamento_id': ObjectId(id)})
            if profissionais_vinculados:
                for prof in profissionais_vinculados:
                    db.comissoes_historico.insert_one({
                        'orcamento_id': ObjectId(id),
                        'profissional_id': prof.get('profissional_id'),
                        'nome': prof.get('nome'),
                        'tipo': prof.get('tipo'),
                        'comissao_perc': prof.get('comissao_perc'),
                        'comissao_valor': prof.get('comissao_valor'),
                        'valor_base': data.get('total_servicos', 0),
                        'status_orcamento': update_data['status'],
                        'data_registro': datetime.now()
                    })
            
            logger.info(f"✅ Orçamento {id} atualizado")
            return jsonify({'success': True, 'message': 'Orçamento atualizado com sucesso'})
        
        elif request.method == 'DELETE':
            db.orcamentos.delete_one({'_id': ObjectId(id)})
            db.comissoes_historico.delete_many({'orcamento_id': ObjectId(id)})
            logger.info(f"🗑️ Orçamento {id} deletado")
            return jsonify({'success': True, 'message': 'Orçamento deletado com sucesso'})
            
    except Exception as e:
        logger.error(f"❌ Erro em handle_orcamento_by_id: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profissionais/<id>/comissoes', methods=['GET'])
@login_required
def get_comissoes_profissional(id):
    """Obter estatísticas de comissões de um profissional"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        # Filtros opcionais
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        status = request.args.get('status')
        
        # Query base
        query = {'profissional_id': ObjectId(id)}
        
        # Aplicar filtros
        if data_inicio or data_fim:
            date_filter = {}
            if data_inicio:
                date_filter['$gte'] = datetime.fromisoformat(data_inicio)
            if data_fim:
                date_filter['$lte'] = datetime.fromisoformat(data_fim)
            query['data_registro'] = date_filter
        
        if status:
            query['status_orcamento'] = status
        
        # Buscar histórico de comissões
        comissoes = list(db.comissoes_historico.find(query).sort('data_registro', DESCENDING))
        
        # Calcular estatísticas
        total_comissoes = sum(c.get('comissao_valor', 0) for c in comissoes)
        total_orcamentos = len(set(str(c.get('orcamento_id')) for c in comissoes))
        media_comissao = total_comissoes / total_orcamentos if total_orcamentos > 0 else 0
        
        # Agrupar por mês
        comissoes_por_mes = {}
        for comissao in comissoes:
            data = comissao.get('data_registro')
            if data and isinstance(data, datetime):
                mes_ano = data.strftime('%Y-%m')
                if mes_ano not in comissoes_por_mes:
                    comissoes_por_mes[mes_ano] = {'valor': 0, 'quantidade': 0}
                comissoes_por_mes[mes_ano]['valor'] += comissao.get('comissao_valor', 0)
                comissoes_por_mes[mes_ano]['quantidade'] += 1
        
        # Converter para formato de resposta
        for c in comissoes:
            c['_id'] = str(c['_id'])
            c['orcamento_id'] = str(c['orcamento_id'])
            c['profissional_id'] = str(c['profissional_id'])
            if 'data_registro' in c and isinstance(c['data_registro'], datetime):
                c['data_registro'] = c['data_registro'].isoformat()
        
        # Buscar dados do profissional
        profissional = db.profissionais.find_one({'_id': ObjectId(id)})
        if not profissional:
            profissional = db.assistentes.find_one({'_id': ObjectId(id)})
        
        resultado = {
            'profissional': {
                'id': id,
                'nome': profissional.get('nome') if profissional else 'Desconhecido',
                'foto': profissional.get('foto') if profissional else None
            },
            'estatisticas': {
                'total_comissoes': round(total_comissoes, 2),
                'total_orcamentos': total_orcamentos,
                'media_comissao': round(media_comissao, 2),
                'comissoes_por_mes': comissoes_por_mes
            },
            'historico': comissoes
        }
        
        logger.info(f"📊 Estatísticas de comissões do profissional {id}: R$ {total_comissoes:.2f}")
        return jsonify({'success': True, 'data': resultado})
        
    except Exception as e:
        logger.error(f"❌ Erro em get_comissoes_profissional: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== FIM DAS NOVAS FUNCIONALIDADES ====================

# ==================== ENDPOINTS PARA SUB-TABS - PRODUTOS ====================

@app.route('/api/produtos', methods=['GET'])
@login_required
def listar_produtos():
    """Lista produtos com filtro opcional por status"""
    try:
        status = request.args.get('status')
        
        query = {}
        if status:
            query['status'] = status
        
        produtos = list(db.produtos.find(query).sort('nome', ASCENDING))
        
        # Formatar resposta
        resultado = []
        for p in produtos:
            resultado.append({
                'id': str(p['_id']),
                'nome': p.get('nome', 'Sem nome'),
                'marca': p.get('marca', 'Sem marca'),
                'preco': float(p.get('preco', 0)),
                'estoque': int(p.get('estoque', 0)),
                'estoque_minimo': int(p.get('estoque_minimo', 0)),
                'status': p.get('status', 'Ativo'),
                'sku': p.get('sku', ''),
                'categoria': p.get('categoria', 'Geral')
            })
        
        logger.info(f"📦 Produtos listados: {len(resultado)} (status: {status or 'todos'})")
        return jsonify({'success': True, 'produtos': resultado})
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar produtos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/produtos/baixo-estoque', methods=['GET'])
@login_required
def produtos_baixo_estoque():
    """Retorna produtos com estoque baixo e estatísticas"""
    try:
        # Buscar todos os produtos ativos
        produtos = list(db.produtos.find({'status': 'Ativo'}))
        
        criticos = []
        atencao = []
        normais = []
        
        for p in produtos:
            estoque_atual = int(p.get('estoque', 0))
            estoque_minimo = int(p.get('estoque_minimo', 0))
            
            diferenca = estoque_atual - estoque_minimo
            
            produto_formatado = {
                'id': str(p['_id']),
                'nome': p.get('nome', 'Sem nome'),
                'marca': p.get('marca', 'Sem marca'),
                'estoque_atual': estoque_atual,
                'estoque_minimo': estoque_minimo,
                'diferenca': diferenca,
                'preco': float(p.get('preco', 0))
            }
            
            # Classificar por nível de estoque
            if estoque_atual <= estoque_minimo:
                produto_formatado['nivel'] = 'Crítico'
                criticos.append(produto_formatado)
            elif estoque_atual < estoque_minimo * 1.5:
                produto_formatado['nivel'] = 'Atenção'
                atencao.append(produto_formatado)
            else:
                produto_formatado['nivel'] = 'Normal'
                normais.append(produto_formatado)
        
        resultado = {
            'estatisticas': {
                'criticos': len(criticos),
                'atencao': len(atencao),
                'normais': len(normais)
            },
            'produtos': criticos + atencao  # Retorna apenas os que precisam atenção
        }
        
        logger.info(f"⚠️ Estoque - Críticos: {len(criticos)}, Atenção: {len(atencao)}, Normais: {len(normais)}")
        return jsonify({'success': True, 'data': resultado})
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar produtos com baixo estoque: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/produtos/<id>', methods=['PUT'])
@login_required
def atualizar_produto(id):
    """Atualiza produto (incluindo toggle de status)"""
    try:
        data = request.get_json()
        
        update_data = {}
        if 'nome' in data:
            update_data['nome'] = data['nome']
        if 'marca' in data:
            update_data['marca'] = data['marca']
        if 'preco' in data:
            update_data['preco'] = float(data['preco'])
        if 'estoque' in data:
            update_data['estoque'] = int(data['estoque'])
        if 'estoque_minimo' in data:
            update_data['estoque_minimo'] = int(data['estoque_minimo'])
        if 'status' in data:
            update_data['status'] = data['status']
        if 'sku' in data:
            update_data['sku'] = data['sku']
        if 'categoria' in data:
            update_data['categoria'] = data['categoria']
        
        if not update_data:
            return jsonify({'success': False, 'message': 'Nenhum dado para atualizar'}), 400
        
        result = db.produtos.update_one(
            {'_id': ObjectId(id)},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ Produto {id} atualizado: {update_data}")
            return jsonify({'success': True, 'message': 'Produto atualizado com sucesso'})
        
        return jsonify({'success': False, 'message': 'Nenhuma alteração realizada'}), 400
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar produto: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== ENDPOINTS PARA SUB-TABS - SERVIÇOS ====================

@app.route('/api/servicos', methods=['GET'])
@login_required
def listar_servicos():
    """Lista serviços com filtro opcional por status"""
    try:
        status = request.args.get('status')
        categoria = request.args.get('categoria')
        
        query = {}
        if status:
            query['status'] = status
        if categoria and categoria != 'Todas':
            query['categoria'] = categoria
        
        servicos = list(db.servicos.find(query).sort('nome', ASCENDING))
        
        # Formatar resposta
        resultado = []
        for s in servicos:
            resultado.append({
                'id': str(s['_id']),
                'nome': s.get('nome', 'Sem nome'),
                'categoria': s.get('categoria', 'Geral'),
                'tamanho': s.get('tamanho', 'Médio'),
                'preco': float(s.get('preco', 0)),
                'duracao': int(s.get('duracao', 60)),
                'status': s.get('status', 'Ativo')
            })
        
        logger.info(f"✂️ Serviços listados: {len(resultado)} (status: {status or 'todos'})")
        return jsonify({'success': True, 'servicos': resultado})
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar serviços: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/servicos/<id>', methods=['PUT'])
@login_required
def atualizar_servico(id):
    """Atualiza serviço (incluindo toggle de status)"""
    try:
        data = request.get_json()
        
        update_data = {}
        if 'nome' in data:
            update_data['nome'] = data['nome']
        if 'categoria' in data:
            update_data['categoria'] = data['categoria']
        if 'tamanho' in data:
            update_data['tamanho'] = data['tamanho']
        if 'preco' in data:
            update_data['preco'] = float(data['preco'])
        if 'duracao' in data:
            update_data['duracao'] = int(data['duracao'])
        if 'status' in data:
            update_data['status'] = data['status']
        
        if not update_data:
            return jsonify({'success': False, 'message': 'Nenhum dado para atualizar'}), 400
        
        result = db.servicos.update_one(
            {'_id': ObjectId(id)},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ Serviço {id} atualizado: {update_data}")
            return jsonify({'success': True, 'message': 'Serviço atualizado com sucesso'})
        
        return jsonify({'success': False, 'message': 'Nenhuma alteração realizada'}), 400
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar serviço: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== ENDPOINTS PARA SUB-TABS - ESTOQUE ====================

@app.route('/api/estoque/visao-geral', methods=['GET'])
@login_required
def estoque_visao_geral():
    """Retorna visão geral do estoque com estatísticas"""
    try:
        # Buscar todos os produtos ativos
        produtos = list(db.produtos.find({'status': 'Ativo'}))
        
        total_produtos = len(produtos)
        valor_total_estoque = 0
        alertas_estoque = 0
        
        produtos_formatados = []
        
        for p in produtos:
            estoque_atual = int(p.get('estoque', 0))
            estoque_minimo = int(p.get('estoque_minimo', 0))
            preco = float(p.get('preco', 0))
            valor_total = estoque_atual * preco
            
            valor_total_estoque += valor_total
            
            # Verificar alertas
            if estoque_atual <= estoque_minimo * 1.5:
                alertas_estoque += 1
            
            # Determinar status
            if estoque_atual <= estoque_minimo:
                nivel = 'Crítico'
            elif estoque_atual < estoque_minimo * 1.5:
                nivel = 'Baixo'
            else:
                nivel = 'Normal'
            
            produtos_formatados.append({
                'id': str(p['_id']),
                'nome': p.get('nome', 'Sem nome'),
                'marca': p.get('marca', 'Sem marca'),
                'estoque_atual': estoque_atual,
                'estoque_minimo': estoque_minimo,
                'preco_unitario': preco,
                'valor_total': round(valor_total, 2),
                'nivel': nivel
            })
        
        # Buscar movimentações do mês atual
        inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        movimentacoes_mes = db.estoque_movimentacoes.count_documents({
            'data': {'$gte': inicio_mes}
        })
        
        resultado = {
            'estatisticas': {
                'total_produtos': total_produtos,
                'valor_estoque': round(valor_total_estoque, 2),
                'alertas': alertas_estoque,
                'movimentacoes_mes': movimentacoes_mes
            },
            'produtos': produtos_formatados
        }
        
        logger.info(f"📊 Visão Geral - {total_produtos} produtos, R$ {valor_total_estoque:.2f}, {alertas_estoque} alertas")
        return jsonify({'success': True, 'data': resultado})
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar visão geral do estoque: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/estoque/alertas', methods=['GET'])
@login_required
def estoque_alertas():
    """Retorna alertas de estoque e últimas movimentações"""
    try:
        # Buscar produtos ativos
        produtos = list(db.produtos.find({'status': 'Ativo'}))
        
        criticos = []
        atencao = []
        normais = []
        
        for p in produtos:
            estoque_atual = int(p.get('estoque', 0))
            estoque_minimo = int(p.get('estoque_minimo', 0))
            diferenca = estoque_atual - estoque_minimo
            
            produto_info = {
                'id': str(p['_id']),
                'nome': p.get('nome', 'Sem nome'),
                'marca': p.get('marca', 'Sem marca'),
                'estoque_atual': estoque_atual,
                'estoque_minimo': estoque_minimo,
                'diferenca': diferenca
            }
            
            if estoque_atual <= estoque_minimo:
                produto_info['nivel'] = 'Crítico'
                criticos.append(produto_info)
            elif estoque_atual < estoque_minimo * 1.5:
                produto_info['nivel'] = 'Atenção'
                atencao.append(produto_info)
            else:
                normais.append(produto_info)
        
        # Buscar últimas 10 movimentações
        movimentacoes = list(db.estoque_movimentacoes.find().sort('data', DESCENDING).limit(10))
        
        movimentacoes_formatadas = []
        for m in movimentacoes:
            # Buscar nome do produto
            produto = db.produtos.find_one({'_id': ObjectId(m['produto_id'])})
            produto_nome = produto.get('nome', 'Desconhecido') if produto else 'Desconhecido'
            
            # Buscar nome do responsável
            responsavel_nome = 'Sistema'
            if m.get('responsavel_id'):
                responsavel = db.profissionais.find_one({'_id': ObjectId(m['responsavel_id'])})
                if not responsavel:
                    responsavel = db.assistentes.find_one({'_id': ObjectId(m['responsavel_id'])})
                if responsavel:
                    responsavel_nome = responsavel.get('nome', 'Desconhecido')
            
            movimentacoes_formatadas.append({
                'id': str(m['_id']),
                'data': m['data'].strftime('%d/%m/%Y'),
                'hora': m['data'].strftime('%H:%M'),
                'produto': produto_nome,
                'tipo': m.get('tipo', 'Entrada'),
                'quantidade': int(m.get('quantidade', 0)),
                'responsavel': responsavel_nome
            })
        
        resultado = {
            'estatisticas': {
                'criticos': len(criticos),
                'atencao': len(atencao),
                'normais': len(normais)
            },
            'produtos_baixo': criticos + atencao,
            'ultimas_movimentacoes': movimentacoes_formatadas
        }
        
        logger.info(f"⚠️ Alertas - Críticos: {len(criticos)}, Atenção: {len(atencao)}")
        return jsonify({'success': True, 'data': resultado})
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar alertas de estoque: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/estoque/relatorio', methods=['GET'])
@login_required
def gerar_relatorio_estoque():
    """Gera relatório de estoque personalizado"""
    try:
        tipo = request.args.get('tipo', 'movimentacoes')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Converter datas
        if data_inicio:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        else:
            data_inicio = datetime.now() - timedelta(days=30)
        
        if data_fim:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            data_fim = data_fim.replace(hour=23, minute=59, second=59)
        else:
            data_fim = datetime.now()
        
        resultado = {}
        
        if tipo == 'movimentacoes':
            # Relatório de movimentações
            movimentacoes = list(db.estoque_movimentacoes.find({
                'data': {'$gte': data_inicio, '$lte': data_fim}
            }).sort('data', DESCENDING))
            
            entradas = 0
            saidas = 0
            movs_formatadas = []
            
            for m in movimentacoes:
                produto = db.produtos.find_one({'_id': ObjectId(m['produto_id'])})
                produto_nome = produto.get('nome', 'Desconhecido') if produto else 'Desconhecido'
                
                responsavel_nome = 'Sistema'
                if m.get('responsavel_id'):
                    responsavel = db.profissionais.find_one({'_id': ObjectId(m['responsavel_id'])})
                    if not responsavel:
                        responsavel = db.assistentes.find_one({'_id': ObjectId(m['responsavel_id'])})
                    if responsavel:
                        responsavel_nome = responsavel.get('nome', 'Desconhecido')
                
                tipo_mov = m.get('tipo', 'Entrada')
                quantidade = int(m.get('quantidade', 0))
                
                if tipo_mov == 'Entrada':
                    entradas += quantidade
                else:
                    saidas += quantidade
                
                movs_formatadas.append({
                    'data': m['data'].strftime('%d/%m/%Y %H:%M'),
                    'tipo': tipo_mov,
                    'produto': produto_nome,
                    'quantidade': quantidade,
                    'motivo': m.get('motivo', ''),
                    'responsavel': responsavel_nome
                })
            
            resultado = {
                'tipo': 'movimentacoes',
                'periodo': {
                    'inicio': data_inicio.strftime('%d/%m/%Y'),
                    'fim': data_fim.strftime('%d/%m/%Y')
                },
                'resumo': {
                    'total_movimentacoes': len(movimentacoes),
                    'total_entradas': entradas,
                    'total_saidas': saidas,
                    'saldo': entradas - saidas
                },
                'movimentacoes': movs_formatadas
            }
            
        elif tipo == 'posicao':
            # Relatório de posição de estoque
            produtos = list(db.produtos.find({'status': 'Ativo'}))
            
            produtos_formatados = []
            for p in produtos:
                produtos_formatados.append({
                    'nome': p.get('nome', 'Sem nome'),
                    'marca': p.get('marca', 'Sem marca'),
                    'estoque_atual': int(p.get('estoque', 0)),
                    'estoque_minimo': int(p.get('estoque_minimo', 0)),
                    'status': 'Normal' if int(p.get('estoque', 0)) > int(p.get('estoque_minimo', 0)) * 1.5 else ('Baixo' if int(p.get('estoque', 0)) > int(p.get('estoque_minimo', 0)) else 'Crítico')
                })
            
            resultado = {
                'tipo': 'posicao',
                'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'total_produtos': len(produtos),
                'produtos': produtos_formatados
            }
            
        elif tipo == 'valorizado':
            # Relatório de estoque valorizado
            produtos = list(db.produtos.find({'status': 'Ativo'}))
            
            valor_total = 0
            produtos_formatados = []
            
            for p in produtos:
                estoque = int(p.get('estoque', 0))
                preco = float(p.get('preco', 0))
                valor = estoque * preco
                valor_total += valor
                
                produtos_formatados.append({
                    'nome': p.get('nome', 'Sem nome'),
                    'marca': p.get('marca', 'Sem marca'),
                    'estoque': estoque,
                    'preco_unitario': preco,
                    'valor_total': round(valor, 2)
                })
            
            # Ordenar por valor total
            produtos_formatados.sort(key=lambda x: x['valor_total'], reverse=True)
            
            resultado = {
                'tipo': 'valorizado',
                'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'valor_total_estoque': round(valor_total, 2),
                'total_produtos': len(produtos),
                'produtos': produtos_formatados
            }
            
        elif tipo == 'criticos':
            # Relatório de produtos críticos
            produtos = list(db.produtos.find({'status': 'Ativo'}))
            
            criticos = []
            atencao = []
            
            for p in produtos:
                estoque_atual = int(p.get('estoque', 0))
                estoque_minimo = int(p.get('estoque_minimo', 0))
                
                if estoque_atual <= estoque_minimo:
                    criticos.append({
                        'nome': p.get('nome', 'Sem nome'),
                        'marca': p.get('marca', 'Sem marca'),
                        'estoque_atual': estoque_atual,
                        'estoque_minimo': estoque_minimo,
                        'diferenca': estoque_atual - estoque_minimo,
                        'nivel': 'Crítico'
                    })
                elif estoque_atual < estoque_minimo * 1.5:
                    atencao.append({
                        'nome': p.get('nome', 'Sem nome'),
                        'marca': p.get('marca', 'Sem marca'),
                        'estoque_atual': estoque_atual,
                        'estoque_minimo': estoque_minimo,
                        'diferenca': estoque_atual - estoque_minimo,
                        'nivel': 'Atenção'
                    })
            
            resultado = {
                'tipo': 'criticos',
                'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'total_criticos': len(criticos),
                'total_atencao': len(atencao),
                'produtos_criticos': criticos,
                'produtos_atencao': atencao
            }
        
        logger.info(f"📄 Relatório gerado: {tipo} ({data_inicio.strftime('%d/%m/%Y')} - {data_fim.strftime('%d/%m/%Y')})")
        return jsonify({'success': True, 'relatorio': resultado})
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar relatório de estoque: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== FIM ENDPOINTS SUB-TABS ====================

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
