#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA UBERABA v4.1 COMPLETO - Sistema Ultra Profissional
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
app.secret_key = os.getenv('SECRET_KEY', 'bioma-2025-v4-1-ultra-secure-key-final-definitivo-completo')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = '/tmp'

CORS(app, supports_credentials=True)

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
    return jsonify({'status': 'healthy', 'time': datetime.now().isoformat(), 'database': db_status, 'version': '4.1'}), 200

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
            'server': {'time': datetime.now().isoformat(), 'version': '4.1'}
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
        
        update_data = {
            'nome': data.get('nome', cliente_existente.get('nome')),
            'cpf': data.get('cpf', cliente_existente.get('cpf')),
            'email': data.get('email', cliente_existente.get('email', '')),
            'telefone': data.get('telefone', cliente_existente.get('telefone', '')),
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
        # Sistema de multicomissão: profissional principal + assistentes
        assistentes = data.get('assistentes', [])
        # Validar assistentes (cada assistente tem id, nome e comissao_perc_sobre_profissional)
        assistentes_processados = []
        for assistente in assistentes:
            if assistente.get('id') and assistente.get('comissao_perc_sobre_profissional'):
                assistentes_processados.append({
                    'id': assistente['id'],
                    'nome': assistente.get('nome', ''),
                    'comissao_perc_sobre_profissional': float(assistente['comissao_perc_sobre_profissional'])
                })

        db.profissionais.insert_one({
            'nome': data['nome'],
            'cpf': data['cpf'],
            'email': data.get('email', ''),
            'telefone': data.get('telefone', ''),
            'especialidade': data.get('especialidade', ''),
            'comissao_perc': float(data.get('comissao_perc', 0)),
            'assistentes': assistentes_processados,
            'foto_url': data.get('foto_url', ''),
            'ativo': True,
            'created_at': datetime.now()
        })
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Erro ao criar profissional: {e}")
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
    """Visualizar um profissional específico"""
    if db is None:
        return jsonify({'success': False}), 500
    try:
        profissional = db.profissionais.find_one({'_id': ObjectId(id)})
        if not profissional:
            return jsonify({'success': False, 'message': 'Profissional não encontrado'}), 404
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
        
        # Processar assistentes para multicomissão
        assistentes = data.get('assistentes', profissional_existente.get('assistentes', []))
        assistentes_processados = []
        for assistente in assistentes:
            if isinstance(assistente, dict) and assistente.get('id') and assistente.get('comissao_perc_sobre_profissional'):
                assistentes_processados.append({
                    'id': assistente['id'],
                    'nome': assistente.get('nome', ''),
                    'comissao_perc_sobre_profissional': float(assistente['comissao_perc_sobre_profissional'])
                })

        update_data = {
            'nome': data.get('nome', profissional_existente.get('nome')),
            'cpf': data.get('cpf', profissional_existente.get('cpf')),
            'email': data.get('email', profissional_existente.get('email', '')),
            'telefone': data.get('telefone', profissional_existente.get('telefone', '')),
            'especialidade': data.get('especialidade', profissional_existente.get('especialidade', '')),
            'comissao_perc': float(data.get('comissao_perc', profissional_existente.get('comissao_perc', 0))),
            'assistentes': assistentes_processados,
            'foto_url': data.get('foto_url', profissional_existente.get('foto_url', '')),
            'ativo': data.get('ativo', profissional_existente.get('ativo', True)),
            'updated_at': datetime.now()
        }
        
        db.profissionais.update_one({'_id': ObjectId(id)}, {'$set': update_data})
        logger.info(f"✅ Profissional atualizado: {update_data['nome']}")
        
        return jsonify({'success': True, 'message': 'Profissional atualizado com sucesso'})
    except Exception as e:
        logger.error(f"Erro ao atualizar profissional: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profissionais/buscar')
@login_required
def buscar_profissionais():
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

        # Adicionar informação completa formatada
        for p in profissionais:
            p['display_name'] = f"{p.get('nome', '')} - {p.get('especialidade', '')} (Comissão: {p.get('comissao_perc', 0)}%)"

        return jsonify({'success': True, 'profissionais': convert_objectid(profissionais)})
    except Exception as e:
        logger.error(f"Erro ao buscar profissionais: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profissionais/<id>/upload-foto', methods=['POST'])
@login_required
def upload_foto_profissional(id):
    """Upload de foto para profissional"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500

    if 'foto' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhuma foto enviada'}), 400

    foto = request.files['foto']
    if not foto.filename:
        return jsonify({'success': False, 'message': 'Nome de arquivo inválido'}), 400

    try:
        import base64
        # Ler o arquivo e converter para base64
        foto_data = foto.read()
        foto_base64 = base64.b64encode(foto_data).decode('utf-8')

        # Obter o tipo MIME
        content_type = foto.content_type or 'image/jpeg'

        # Criar data URL
        foto_url = f"data:{content_type};base64,{foto_base64}"

        # Atualizar profissional
        result = db.profissionais.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'foto_url': foto_url, 'updated_at': datetime.now()}}
        )

        if result.modified_count > 0:
            return jsonify({'success': True, 'foto_url': foto_url})
        else:
            return jsonify({'success': False, 'message': 'Profissional não encontrado'}), 404

    except Exception as e:
        logger.error(f"Erro ao fazer upload de foto: {e}")
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
            return jsonify({'success': False, 'message': 'Produto não encontrado'})

        qtd = int(data['quantidade'])
        tipo = data['tipo']
        aprovar_automatico = data.get('aprovar_automatico', False)

        # Criar movimentação com status pendente ou aprovado
        status = 'aprovado' if aprovar_automatico else 'pendente'

        movimentacao_data = {
            'produto_id': ObjectId(data['produto_id']),
            'tipo': tipo,
            'quantidade': qtd,
            'motivo': data.get('motivo', ''),
            'usuario': session.get('username'),
            'data': datetime.now(),
            'status': status
        }

        # Se for aprovação automática, atualizar estoque imediatamente
        if aprovar_automatico:
            novo_estoque = produto.get('estoque', 0)
            if tipo == 'entrada':
                novo_estoque += qtd
            else:
                novo_estoque -= qtd
                if novo_estoque < 0:
                    return jsonify({'success': False, 'message': 'Estoque insuficiente'})

            db.produtos.update_one(
                {'_id': ObjectId(data['produto_id'])},
                {'$set': {'estoque': novo_estoque, 'updated_at': datetime.now()}}
            )

            movimentacao_data['aprovado_por'] = session.get('username')
            movimentacao_data['aprovado_em'] = datetime.now()

        db.estoque_movimentacoes.insert_one(movimentacao_data)

        return jsonify({'success': True, 'status': status})
    except Exception as e:
        logger.error(f"Erro na movimentação de estoque: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/movimentacoes')
@login_required
def estoque_movimentacoes():
    """Retorna todas as movimentações de estoque com informações do produto"""
    if db is None:
        return jsonify({'success': False}), 500
    try:
        movimentacoes = list(db.estoque_movimentacoes.find({}).sort('data', DESCENDING).limit(100))

        # Enriquecer com dados do produto
        for mov in movimentacoes:
            if 'produto_id' in mov:
                produto = db.produtos.find_one({'_id': mov['produto_id']})
                if produto:
                    mov['produto_nome'] = produto.get('nome', 'Desconhecido')
                    mov['produto_marca'] = produto.get('marca', '')

        return jsonify({'success': True, 'movimentacoes': convert_objectid(movimentacoes)})
    except Exception as e:
        logger.error(f"Erro ao buscar movimentações: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/stats')
@login_required
def estoque_stats():
    """Retorna estatísticas do estoque"""
    if db is None:
        return jsonify({'success': False}), 500
    try:
        total_produtos = db.produtos.count_documents({'ativo': True})
        produtos_baixo = db.produtos.count_documents({'$expr': {'$lte': ['$estoque', '$estoque_minimo']}, 'ativo': True})
        produtos_zerados = db.produtos.count_documents({'estoque': 0, 'ativo': True})

        # Valor total em estoque
        pipeline = [
            {'$match': {'ativo': True}},
            {'$group': {'_id': None, 'total': {'$sum': {'$multiply': ['$estoque', '$preco']}}}}
        ]
        valor_result = list(db.produtos.aggregate(pipeline))
        valor_total = valor_result[0]['total'] if valor_result else 0

        # Movimentações pendentes
        pendentes = db.estoque_movimentacoes.count_documents({'status': 'pendente'})

        return jsonify({
            'success': True,
            'stats': {
                'total_produtos': total_produtos,
                'produtos_baixo': produtos_baixo,
                'produtos_zerados': produtos_zerados,
                'valor_total_estoque': valor_total,
                'movimentacoes_pendentes': pendentes
            }
        })
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas de estoque: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/aprovar/<movimentacao_id>', methods=['POST'])
@login_required
def aprovar_movimentacao(movimentacao_id):
    """Aprovar uma movimentação de estoque"""
    if db is None:
        return jsonify({'success': False}), 500

    try:
        movimentacao = db.estoque_movimentacoes.find_one({'_id': ObjectId(movimentacao_id)})
        if not movimentacao:
            return jsonify({'success': False, 'message': 'Movimentação não encontrada'}), 404

        if movimentacao.get('status') != 'pendente':
            return jsonify({'success': False, 'message': 'Movimentação já foi processada'}), 400

        # Atualizar estoque do produto
        produto = db.produtos.find_one({'_id': movimentacao['produto_id']})
        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404

        novo_estoque = produto.get('estoque', 0)
        if movimentacao['tipo'] == 'entrada':
            novo_estoque += movimentacao['quantidade']
        else:
            novo_estoque -= movimentacao['quantidade']
            if novo_estoque < 0:
                return jsonify({'success': False, 'message': 'Estoque insuficiente'}), 400

        # Atualizar produto e movimentação
        db.produtos.update_one(
            {'_id': movimentacao['produto_id']},
            {'$set': {'estoque': novo_estoque, 'updated_at': datetime.now()}}
        )

        db.estoque_movimentacoes.update_one(
            {'_id': ObjectId(movimentacao_id)},
            {'$set': {
                'status': 'aprovado',
                'aprovado_por': session.get('username'),
                'aprovado_em': datetime.now()
            }}
        )

        logger.info(f"✅ Movimentação {movimentacao_id} aprovada por {session.get('username')}")
        return jsonify({'success': True, 'novo_estoque': novo_estoque})

    except Exception as e:
        logger.error(f"Erro ao aprovar movimentação: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/reprovar/<movimentacao_id>', methods=['POST'])
@login_required
def reprovar_movimentacao(movimentacao_id):
    """Reprovar uma movimentação de estoque"""
    if db is None:
        return jsonify({'success': False}), 500

    try:
        data = request.json or {}
        motivo = data.get('motivo', 'Sem motivo especificado')

        movimentacao = db.estoque_movimentacoes.find_one({'_id': ObjectId(movimentacao_id)})
        if not movimentacao:
            return jsonify({'success': False, 'message': 'Movimentação não encontrada'}), 404

        if movimentacao.get('status') != 'pendente':
            return jsonify({'success': False, 'message': 'Movimentação já foi processada'}), 400

        db.estoque_movimentacoes.update_one(
            {'_id': ObjectId(movimentacao_id)},
            {'$set': {
                'status': 'reprovado',
                'reprovado_por': session.get('username'),
                'reprovado_em': datetime.now(),
                'motivo_reprovacao': motivo
            }}
        )

        logger.info(f"❌ Movimentação {movimentacao_id} reprovada por {session.get('username')}")
        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Erro ao reprovar movimentação: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/aprovar-todos', methods=['POST'])
@login_required
def aprovar_todas_movimentacoes():
    """Aprovar todas as movimentações pendentes"""
    if db is None:
        return jsonify({'success': False}), 500

    try:
        movimentacoes = list(db.estoque_movimentacoes.find({'status': 'pendente'}))
        aprovadas = 0
        erros = 0

        for mov in movimentacoes:
            try:
                produto = db.produtos.find_one({'_id': mov['produto_id']})
                if not produto:
                    erros += 1
                    continue

                novo_estoque = produto.get('estoque', 0)
                if mov['tipo'] == 'entrada':
                    novo_estoque += mov['quantidade']
                else:
                    novo_estoque -= mov['quantidade']
                    if novo_estoque < 0:
                        erros += 1
                        continue

                db.produtos.update_one(
                    {'_id': mov['produto_id']},
                    {'$set': {'estoque': novo_estoque, 'updated_at': datetime.now()}}
                )

                db.estoque_movimentacoes.update_one(
                    {'_id': mov['_id']},
                    {'$set': {
                        'status': 'aprovado',
                        'aprovado_por': session.get('username'),
                        'aprovado_em': datetime.now()
                    }}
                )
                aprovadas += 1

            except Exception as e:
                logger.error(f"Erro ao aprovar movimentação {mov['_id']}: {e}")
                erros += 1

        logger.info(f"✅ {aprovadas} movimentações aprovadas em massa por {session.get('username')}")
        return jsonify({'success': True, 'aprovadas': aprovadas, 'erros': erros})

    except Exception as e:
        logger.error(f"Erro ao aprovar todas movimentações: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/reprovar-todos', methods=['POST'])
@login_required
def reprovar_todas_movimentacoes():
    """Reprovar todas as movimentações pendentes"""
    if db is None:
        return jsonify({'success': False}), 500

    try:
        data = request.json or {}
        motivo = data.get('motivo', 'Reprovação em massa')

        result = db.estoque_movimentacoes.update_many(
            {'status': 'pendente'},
            {'$set': {
                'status': 'reprovado',
                'reprovado_por': session.get('username'),
                'reprovado_em': datetime.now(),
                'motivo_reprovacao': motivo
            }}
        )

        logger.info(f"❌ {result.modified_count} movimentações reprovadas em massa por {session.get('username')}")
        return jsonify({'success': True, 'reprovadas': result.modified_count})

    except Exception as e:
        logger.error(f"Erro ao reprovar todas movimentações: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/produtos-criticos')
@login_required
def produtos_criticos():
    """Retorna produtos com estoque crítico (<=30% do mínimo)"""
    if db is None:
        return jsonify({'success': False}), 500

    try:
        pipeline = [
            {'$match': {'ativo': True}},
            {'$addFields': {
                'percentual_estoque': {
                    '$cond': [
                        {'$eq': ['$estoque_minimo', 0]},
                        100,
                        {'$multiply': [{'$divide': ['$estoque', '$estoque_minimo']}, 100]}
                    ]
                }
            }},
            {'$match': {'percentual_estoque': {'$lte': 30}}},
            {'$sort': {'percentual_estoque': 1}}
        ]

        produtos = list(db.produtos.aggregate(pipeline))
        return jsonify({'success': True, 'produtos': convert_objectid(produtos)})

    except Exception as e:
        logger.error(f"Erro ao buscar produtos críticos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/ajustar', methods=['POST'])
@login_required
def ajustar_estoque():
    """Ajustar estoque de um produto (inventário)"""
    if db is None:
        return jsonify({'success': False}), 500

    data = request.json
    try:
        produto_id = data.get('produto_id')
        estoque_real = int(data.get('estoque_real', 0))
        motivo = data.get('motivo', 'Ajuste de inventário')

        produto = db.produtos.find_one({'_id': ObjectId(produto_id)})
        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404

        estoque_atual = produto.get('estoque', 0)
        diferenca = estoque_real - estoque_atual

        # Atualizar estoque
        db.produtos.update_one(
            {'_id': ObjectId(produto_id)},
            {'$set': {'estoque': estoque_real, 'updated_at': datetime.now()}}
        )

        # Registrar ajuste
        tipo_ajuste = 'entrada' if diferenca > 0 else 'saida'
        db.estoque_movimentacoes.insert_one({
            'produto_id': ObjectId(produto_id),
            'tipo': tipo_ajuste,
            'quantidade': abs(diferenca),
            'motivo': f"AJUSTE: {motivo} (Anterior: {estoque_atual}, Real: {estoque_real})",
            'usuario': session.get('username'),
            'data': datetime.now(),
            'status': 'aprovado',  # Ajustes são aprovados automaticamente
            'aprovado_por': session.get('username'),
            'aprovado_em': datetime.now(),
            'tipo_movimentacao': 'ajuste_inventario'
        })

        logger.info(f"📊 Ajuste de estoque: {produto.get('nome')} de {estoque_atual} para {estoque_real}")
        return jsonify({'success': True, 'diferenca': diferenca})

    except Exception as e:
        logger.error(f"Erro ao ajustar estoque: {e}")
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
            # Importação de serviços corrigida
            for idx, row in enumerate(rows, 1):
                try:
                    r = {k.lower().strip(): v for k, v in row.items() if k and v is not None}
                    if not r or all(not v for v in r.values()):
                        continue

                    # Obter nome do serviço
                    nome = None
                    for col in ['nome', 'servico', 'name', 'serviço']:
                        if col in r and r[col]:
                            nome = str(r[col]).strip()
                            break
                    if not nome or len(nome) < 2:
                        count_error += 1
                        continue

                    # Obter categoria
                    categoria = 'Serviço'
                    for col in ['categoria', 'category']:
                        if col in r and r[col]:
                            categoria = str(r[col]).strip()
                            break

                    # Processar tamanhos e preços
                    tamanhos_map = {
                        'kids': 'Kids',
                        'masculino': 'Masculino',
                        'curto': 'Curto',
                        'medio': 'Médio',
                        'médio': 'Médio',
                        'longo': 'Longo',
                        'extra_longo': 'Extra Longo',
                        'extralongo': 'Extra Longo'
                    }

                    servicos_criados = 0
                    for col_name, tamanho_display in tamanhos_map.items():
                        if col_name in r and r[col_name]:
                            try:
                                preco_str = str(r[col_name]).replace('R$', '').strip()
                                if ',' in preco_str:
                                    preco_str = preco_str.replace(',', '.')
                                preco = float(preco_str)

                                if preco > 0:
                                    sku = f"{nome.upper().replace(' ', '-')}-{tamanho_display.upper().replace(' ', '-')}"
                                    db.servicos.insert_one({
                                        'nome': nome,
                                        'sku': sku,
                                        'tamanho': tamanho_display,
                                        'preco': preco,
                                        'categoria': categoria,
                                        'duracao': 60,
                                        'ativo': True,
                                        'created_at': datetime.now()
                                    })
                                    servicos_criados += 1
                            except Exception as e:
                                logger.error(f"Erro ao processar tamanho {col_name}: {e}")
                                continue

                    if servicos_criados > 0:
                        count_success += servicos_criados
                    else:
                        count_error += 1

                except Exception as e:
                    logger.error(f"Erro ao importar serviço linha {idx}: {e}")
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
        db.config.update_one({'key': 'unidade'}, {'$set': data}, upsert=True)
        return jsonify({'success': True})
    except:
        return jsonify({'success': False}), 500

# === NOVAS ROTAS PARA MELHORIAS ===

@app.route('/api/config/logo', methods=['POST'])
@login_required
def upload_logo():
    """Upload de logo da empresa (Melhoria #11)"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500

    if 'logo' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum logo enviado'}), 400

    logo = request.files['logo']
    if not logo.filename:
        return jsonify({'success': False, 'message': 'Nome de arquivo inválido'}), 400

    try:
        import base64
        logo_data = logo.read()
        logo_base64 = base64.b64encode(logo_data).decode('utf-8')
        content_type = logo.content_type or 'image/png'
        logo_url = f"data:{content_type};base64,{logo_base64}"

        db.config.update_one(
            {'key': 'unidade'},
            {'$set': {'logo_url': logo_url, 'updated_at': datetime.now()}},
            upsert=True
        )

        logger.info("✅ Logo da empresa atualizado")
        return jsonify({'success': True, 'logo_url': logo_url})
    except Exception as e:
        logger.error(f"Erro ao fazer upload de logo: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/comissoes/calcular', methods=['POST'])
@login_required
def calcular_comissoes():
    """Calcular comissões de profissionais e assistentes (Melhoria #1 e #10)"""
    if db is None:
        return jsonify({'success': False}), 500

    data = request.json
    orcamento_id = data.get('orcamento_id')

    try:
        orcamento = db.orcamentos.find_one({'_id': ObjectId(orcamento_id)})
        if not orcamento:
            return jsonify({'success': False, 'message': 'Orçamento não encontrado'}), 404

        total_orcamento = orcamento.get('total_final', 0)
        comissoes_detalhadas = []

        # Processar cada serviço do orçamento
        for servico in orcamento.get('servicos', []):
            profissional_id = servico.get('profissional_id')
            if not profissional_id:
                continue

            profissional = db.profissionais.find_one({'_id': ObjectId(profissional_id)})
            if not profissional:
                continue

            # Calcular comissão do profissional principal
            comissao_perc = profissional.get('comissao_perc', 0)
            valor_servico = servico.get('total', 0)
            comissao_profissional = valor_servico * (comissao_perc / 100)

            comissao_info = {
                'profissional_id': str(profissional_id),
                'profissional_nome': profissional.get('nome'),
                'profissional_foto': profissional.get('foto_url', ''),
                'servico_nome': servico.get('nome'),
                'valor_servico': valor_servico,
                'comissao_perc': comissao_perc,
                'comissao_valor': comissao_profissional,
                'assistentes': []
            }

            # Processar assistentes (comissão sobre comissão do profissional)
            for assistente in profissional.get('assistentes', []):
                assistente_id = assistente.get('id')
                assistente_comissao_perc = assistente.get('comissao_perc_sobre_profissional', 0)

                # Comissão do assistente é X% da comissão do profissional
                comissao_assistente = comissao_profissional * (assistente_comissao_perc / 100)

                comissao_info['assistentes'].append({
                    'assistente_id': assistente_id,
                    'assistente_nome': assistente.get('nome'),
                    'comissao_perc_sobre_profissional': assistente_comissao_perc,
                    'comissao_valor': comissao_assistente
                })

            comissoes_detalhadas.append(comissao_info)

        # Salvar comissões calculadas no orçamento
        db.orcamentos.update_one(
            {'_id': ObjectId(orcamento_id)},
            {'$set': {'comissoes_calculadas': comissoes_detalhadas, 'comissoes_updated_at': datetime.now()}}
        )

        return jsonify({'success': True, 'comissoes': comissoes_detalhadas})
    except Exception as e:
        logger.error(f"Erro ao calcular comissões: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profissionais/<id>/stats')
@login_required
def profissional_stats(id):
    """Estatísticas detalhadas do profissional (Melhoria #10)"""
    if db is None:
        return jsonify({'success': False}), 500

    try:
        profissional = db.profissionais.find_one({'_id': ObjectId(id)})
        if not profissional:
            return jsonify({'success': False, 'message': 'Profissional não encontrado'}), 404

        # Buscar todos os orçamentos com serviços do profissional
        orcamentos = list(db.orcamentos.find({'status': 'Aprovado'}))

        total_comissoes = 0
        total_servicos = 0
        total_faturamento_gerado = 0

        for orc in orcamentos:
            for servico in orc.get('servicos', []):
                if servico.get('profissional_id') == str(id):
                    total_servicos += 1
                    valor_servico = servico.get('total', 0)
                    total_faturamento_gerado += valor_servico
                    comissao = valor_servico * (profissional.get('comissao_perc', 0) / 100)
                    total_comissoes += comissao

        stats = {
            'total_comissoes': total_comissoes,
            'total_servicos': total_servicos,
            'total_faturamento_gerado': total_faturamento_gerado,
            'comissao_perc': profissional.get('comissao_perc', 0),
            'ticket_medio': total_faturamento_gerado / total_servicos if total_servicos > 0 else 0,
            'assistentes': profissional.get('assistentes', [])
        }

        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas do profissional: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/assistentes', methods=['GET', 'POST'])
@login_required
def assistentes():
    """Gerenciar assistentes independentes (Melhoria #1 e #10)"""
    if db is None:
        return jsonify({'success': False}), 500

    if request.method == 'GET':
        try:
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
            'foto_url': data.get('foto_url', ''),
            'ativo': True,
            'created_at': datetime.now()
        }
        db.assistentes.insert_one(assistente_data)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Erro ao criar assistente: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/busca/global')
@login_required
def busca_global():
    """Busca global no sistema (Melhoria #3 e #13)"""
    if db is None:
        return jsonify({'success': False}), 500

    termo = request.args.get('termo', '').strip()
    if len(termo) < 2:
        return jsonify({'success': True, 'resultados': []})

    try:
        regex = {'$regex': termo, '$options': 'i'}
        resultados = {
            'clientes': [],
            'profissionais': [],
            'servicos': [],
            'produtos': [],
            'orcamentos': []
        }

        # Buscar clientes
        clientes = list(db.clientes.find({
            '$or': [{'nome': regex}, {'cpf': regex}, {'email': regex}, {'telefone': regex}]
        }).limit(5))
        for c in clientes:
            resultados['clientes'].append({
                'id': str(c['_id']),
                'tipo': 'cliente',
                'titulo': c.get('nome', ''),
                'subtitulo': f"CPF: {c.get('cpf', '')}",
                'icone': 'bi-person'
            })

        # Buscar profissionais
        profissionais = list(db.profissionais.find({
            '$or': [{'nome': regex}, {'cpf': regex}, {'especialidade': regex}],
            'ativo': True
        }).limit(5))
        for p in profissionais:
            resultados['profissionais'].append({
                'id': str(p['_id']),
                'tipo': 'profissional',
                'titulo': p.get('nome', ''),
                'subtitulo': p.get('especialidade', ''),
                'icone': 'bi-person-workspace',
                'foto': p.get('foto_url', '')
            })

        # Buscar serviços
        servicos = list(db.servicos.find({
            '$or': [{'nome': regex}, {'tamanho': regex}, {'sku': regex}],
            'ativo': True
        }).limit(5))
        for s in servicos:
            resultados['servicos'].append({
                'id': str(s['_id']),
                'tipo': 'servico',
                'titulo': f"{s.get('nome', '')} - {s.get('tamanho', '')}",
                'subtitulo': f"R$ {s.get('preco', 0):.2f}",
                'icone': 'bi-scissors'
            })

        # Buscar produtos
        produtos = list(db.produtos.find({
            '$or': [{'nome': regex}, {'marca': regex}, {'sku': regex}],
            'ativo': True
        }).limit(5))
        for p in produtos:
            resultados['produtos'].append({
                'id': str(p['_id']),
                'tipo': 'produto',
                'titulo': p.get('nome', ''),
                'subtitulo': f"{p.get('marca', '')} - Estoque: {p.get('estoque', 0)}",
                'icone': 'bi-box-seam'
            })

        # Buscar orçamentos
        try:
            numero_busca = int(termo)
            orcamentos = list(db.orcamentos.find({'numero': numero_busca}).limit(5))
        except:
            orcamentos = list(db.orcamentos.find({'cliente_nome': regex}).limit(5))

        for o in orcamentos:
            resultados['orcamentos'].append({
                'id': str(o['_id']),
                'tipo': 'orcamento',
                'titulo': f"Orçamento #{o.get('numero', '')}",
                'subtitulo': f"{o.get('cliente_nome', '')} - R$ {o.get('total_final', 0):.2f}",
                'icone': 'bi-file-earmark-text'
            })

        return jsonify({'success': True, 'resultados': resultados})
    except Exception as e:
        logger.error(f"Erro na busca global: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/agendamentos/calendario')
@login_required
def agendamentos_calendario():
    """Dados do calendário de agendamentos (Melhoria #9)"""
    if db is None:
        return jsonify({'success': False}), 500

    try:
        mes = int(request.args.get('mes', datetime.now().month))
        ano = int(request.args.get('ano', datetime.now().year))

        # Primeiro e último dia do mês
        primeiro_dia = datetime(ano, mes, 1)
        if mes == 12:
            ultimo_dia = datetime(ano + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = datetime(ano, mes + 1, 1) - timedelta(days=1)

        # Buscar todos os agendamentos do mês
        agendamentos = list(db.agendamentos.find({
            'data': {'$gte': primeiro_dia, '$lte': ultimo_dia}
        }))

        # Buscar orçamentos criados no mês para o mapa de calor
        orcamentos = list(db.orcamentos.find({
            'created_at': {'$gte': primeiro_dia, '$lte': ultimo_dia}
        }))

        # Organizar por dia
        calendario_data = {}
        for agend in agendamentos:
            dia = agend['data'].day
            if dia not in calendario_data:
                calendario_data[dia] = {'agendamentos': [], 'total': 0}
            calendario_data[dia]['agendamentos'].append(agend.get('horario', ''))
            calendario_data[dia]['total'] += 1

        # Adicionar dados de orcamentos para mapa de calor
        mapa_calor = {}
        for orc in orcamentos:
            dia = orc['created_at'].day
            if dia not in mapa_calor:
                mapa_calor[dia] = {'orcamentos': 0, 'valor': 0}
            mapa_calor[dia]['orcamentos'] += 1
            mapa_calor[dia]['valor'] += orc.get('total_final', 0)

        return jsonify({
            'success': True,
            'calendario': calendario_data,
            'mapa_calor': mapa_calor,
            'mes': mes,
            'ano': ano
        })
    except Exception as e:
        logger.error(f"Erro ao buscar calendário: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/relatorios/graficos')
@login_required
def relatorios_graficos():
    """Dados para gráficos avançados (Melhoria #8)"""
    if db is None:
        return jsonify({'success': False}), 500

    try:
        # Últimos 30 dias
        data_inicio = datetime.now() - timedelta(days=30)

        # Faturamento por dia
        pipeline_faturamento = [
            {'$match': {'status': 'Aprovado', 'created_at': {'$gte': data_inicio}}},
            {'$group': {
                '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$created_at'}},
                'total': {'$sum': '$total_final'},
                'quantidade': {'$sum': 1}
            }},
            {'$sort': {'_id': 1}}
        ]
        faturamento_diario = list(db.orcamentos.aggregate(pipeline_faturamento))

        # Produtos mais vendidos
        pipeline_produtos = [
            {'$match': {'status': 'Aprovado', 'created_at': {'$gte': data_inicio}}},
            {'$unwind': '$produtos'},
            {'$group': {
                '_id': '$produtos.nome',
                'quantidade': {'$sum': '$produtos.qtd'},
                'valor': {'$sum': '$produtos.total'}
            }},
            {'$sort': {'quantidade': -1}},
            {'$limit': 10}
        ]
        produtos_vendidos = list(db.orcamentos.aggregate(pipeline_produtos))

        # Serviços mais vendidos
        pipeline_servicos = [
            {'$match': {'status': 'Aprovado', 'created_at': {'$gte': data_inicio}}},
            {'$unwind': '$servicos'},
            {'$group': {
                '_id': '$servicos.nome',
                'quantidade': {'$sum': 1},
                'valor': {'$sum': '$servicos.total'}
            }},
            {'$sort': {'quantidade': -1}},
            {'$limit': 10}
        ]
        servicos_vendidos = list(db.orcamentos.aggregate(pipeline_servicos))

        # Estoque baixo
        produtos_baixo_estoque = list(db.produtos.find({
            '$expr': {'$lte': ['$estoque', '$estoque_minimo']},
            'ativo': True
        }).limit(10))

        # Top clientes
        pipeline_clientes = [
            {'$match': {'status': 'Aprovado'}},
            {'$group': {
                '_id': '$cliente_cpf',
                'nome': {'$first': '$cliente_nome'},
                'total_gasto': {'$sum': '$total_final'},
                'visitas': {'$sum': 1}
            }},
            {'$sort': {'total_gasto': -1}},
            {'$limit': 10}
        ]
        top_clientes = list(db.orcamentos.aggregate(pipeline_clientes))

        return jsonify({
            'success': True,
            'graficos': {
                'faturamento_diario': faturamento_diario,
                'produtos_vendidos': produtos_vendidos,
                'servicos_vendidos': servicos_vendidos,
                'produtos_baixo_estoque': convert_objectid(produtos_baixo_estoque),
                'top_clientes': top_clientes
            }
        })
    except Exception as e:
        logger.error(f"Erro ao buscar dados de relatórios: {e}")
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
    print("🌳 BIOMA UBERABA v4.1 COMPLETO E DEFINITIVO")
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