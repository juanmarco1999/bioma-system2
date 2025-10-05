#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      BIOMA UBERABA v3.0 - ULTRA AVANÇADO                     ║
║           Sistema Completo: Gestão + Agendamento + CRM + Estoque             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Desenvolvedor: Juan Marco (@juanmarco1999)                                  ║
║  Email: 180147064@aluno.unb.br                                               ║
║  Data: 2025-10-05 15:40:00 UTC                                               ║
║  Versão: 3.0.0 - CORREÇÕES TOTAIS + 4 NOVAS FUNCIONALIDADES                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ===== IMPORTS =====
from flask import Flask, render_template, request, jsonify, session, send_file
from flask_cors import CORS
from flask_talisman import Talisman
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
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle

# ===== LOGGING AVANÇADO =====
logging.basicConfig(
    level=logging.DEBUG,  # Mudado para DEBUG para mais detalhes
    format='%(asctime)s [%(levelname)s] %(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

load_dotenv()
logger.info("🔧 Variáveis de ambiente carregadas")

# ===== CONFIGURAÇÃO FLASK =====
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'bioma-2025-v3-ultra-secure')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

logger.info(f"🌐 Ambiente: {os.getenv('FLASK_ENV', 'development')}")

# ===== SEGURANÇA =====
if os.getenv('FLASK_ENV') == 'production':
    logger.info("🔒 Ativando SSL/HTTPS")
    csp = {
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'", 'cdn.jsdelivr.net', 'cdnjs.cloudflare.com'],
        'style-src': ["'self'", "'unsafe-inline'", 'cdn.jsdelivr.net', 'fonts.googleapis.com'],
        'font-src': ["'self'", 'fonts.gstatic.com', 'cdn.jsdelivr.net'],
        'img-src': ["'self'", 'data:', 'https:'],
    }
    Talisman(app, force_https=True, strict_transport_security=True, content_security_policy=csp)

CORS(app, supports_credentials=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ===== MONGODB =====
def get_db():
    try:
        u = urllib.parse.quote_plus(os.getenv('MONGO_USERNAME', ''))
        p = urllib.parse.quote_plus(os.getenv('MONGO_PASSWORD', ''))
        c = os.getenv('MONGO_CLUSTER', '')
        
        if not all([u, p, c]):
            logger.error("❌ Credenciais MongoDB ausentes")
            return None
        
        uri = f"mongodb+srv://{u}:{p}@{c}/bioma_db?retryWrites=true&w=majority"
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.server_info()
        
        logger.info("✅ MongoDB CONECTADO")
        return client.bioma_db
    except Exception as e:
        logger.error(f"❌ MongoDB FALHOU: {e}")
        return None

db = get_db()

# ===== HELPER: CONVERTER OBJECTID =====
def convert_objectid(obj):
    """Converte ObjectId e datetime recursivamente"""
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

# ===== DECORATOR LOGIN =====
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning(f"🚫 Acesso negado: {request.endpoint}")
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

# ===== EMAIL E SMS =====
def send_email(to, name, subj, html, pdf=None):
    key = os.getenv('MAILERSEND_API_KEY')
    if not key:
        logger.warning("⚠️ MailerSend API Key ausente")
        return {'success': False}
    
    data = {
        "from": {"email": os.getenv('MAILERSEND_FROM_EMAIL', 'noreply@bioma.com'), "name": "BIOMA Uberaba"},
        "to": [{"email": to, "name": name}],
        "subject": subj,
        "html": html
    }
    
    if pdf:
        import base64
        data['attachments'] = [{"filename": pdf['filename'], "content": base64.b64encode(pdf['content']).decode()}]
    
    try:
        r = requests.post("https://api.mailersend.com/v1/email",
                         headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
                         json=data, timeout=10)
        if r.status_code == 202:
            logger.info(f"📧 Email enviado: {to}")
            return {'success': True}
        logger.error(f"❌ Email falhou: {r.status_code}")
        return {'success': False}
    except Exception as e:
        logger.error(f"❌ Exception email: {e}")
        return {'success': False}

def send_sms(num, msg):
    key = os.getenv('MAILERSEND_API_KEY')
    if not key:
        return {'success': False}
    
    n = '+55' + ''.join(filter(str.isdigit, num)) if not num.startswith('+') else num
    
    try:
        r = requests.post("https://api.mailersend.com/v1/sms",
                         headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
                         json={"from": "BIOMA", "to": [n], "text": msg}, timeout=10)
        if r.status_code == 202:
            logger.info(f"📱 SMS enviado: {num}")
            return {'success': True}
        return {'success': False}
    except:
        return {'success': False}

# ===== ROTAS BÁSICAS =====
@app.route('/')
def index():
    logger.info(f"🌐 Acesso index - IP: {request.remote_addr}")
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'time': datetime.now().isoformat(), 'database': 'connected' if db else 'disconnected'}), 200

@app.route('/api/system/status')
@login_required
def system_status():
    logger.info("📊 Verificando status")
    
    # CORREÇÃO: Testar MongoDB de verdade
    mongo_ok = False
    mongo_msg = 'Desconectado'
    try:
        if db:
            db.command('ping')
            mongo_ok = True
            mongo_msg = 'Conectado e operacional'
            logger.info("✅ MongoDB ping OK")
    except Exception as e:
        logger.error(f"❌ MongoDB ping FALHOU: {e}")
        mongo_msg = f'Erro: {str(e)}'
    
    status = {
        'mongodb': {
            'operational': mongo_ok,
            'message': mongo_msg,
            'last_check': datetime.now().isoformat()
        },
        'mailersend': {
            'operational': bool(os.getenv('MAILERSEND_API_KEY')),
            'message': 'Configurado' if os.getenv('MAILERSEND_API_KEY') else 'API Key ausente'
        },
        'server': {
            'time': datetime.now().isoformat(),
            'environment': os.getenv('FLASK_ENV', 'development'),
            'version': '3.0.0'
        }
    }
    
    logger.info(f"📊 Status retornado: MongoDB={mongo_ok}")
    return jsonify({'success': True, 'status': status})

# ===== AUTENTICAÇÃO =====
@app.route('/api/register', methods=['POST'])
def register():
    d = request.json
    logger.info(f"👤 Registro: {d.get('username')}")
    
    if db.users.find_one({'$or': [{'username': d['username']}, {'email': d['email']}]}):
        logger.warning(f"⚠️ Usuário já existe: {d.get('username')}")
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
    logger.info(f"🔐 Login: {d.get('username')}")
    
    u = db.users.find_one({'$or': [{'username': d['username']}, {'email': d['username']}]})
    
    if u and check_password_hash(u['password'], d['password']):
        session.permanent = True
        session['user_id'] = str(u['_id'])
        session['username'] = u['username']
        
        logger.info(f"✅ Login OK: {u['username']}")
        
        return jsonify({
            'success': True,
            'user': {
                'id': str(u['_id']),
                'name': u['name'],
                'username': u['username'],
                'theme': u.get('theme', 'light')
            }
        })
    
    logger.warning(f"❌ Login FALHOU: {d.get('username')}")
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
        except:
            pass
    return jsonify({'success': False})

@app.route('/api/update-theme', methods=['POST'])
@login_required
def update_theme():
    theme = request.json['theme']
    db.users.update_one({'_id': ObjectId(session['user_id'])}, {'$set': {'theme': theme}})
    logger.info(f"🎨 Tema: {theme}")
    return jsonify({'success': True})

# ===== CLIENTES (COM CRM) =====
@app.route('/api/clientes', methods=['GET', 'POST'])
@login_required
def clientes():
    if request.method == 'GET':
        logger.info("📋 Listando clientes")
        try:
            clientes_list = list(db.clientes.find({}).sort('nome', 1))
            
            # ENRIQUECER COM DADOS CRM
            for cliente in clientes_list:
                cliente_id = cliente['_id']
                
                # Total gasto
                total_gasto = sum(
                    o.get('total_final', 0) 
                    for o in db.orcamentos.find({'cliente_cpf': cliente.get('cpf'), 'status': 'Aprovado'})
                )
                cliente['total_gasto'] = total_gasto
                
                # Última visita
                ultimo_orc = db.orcamentos.find_one(
                    {'cliente_cpf': cliente.get('cpf')}, 
                    sort=[('created_at', DESCENDING)]
                )
                cliente['ultima_visita'] = ultimo_orc['created_at'] if ultimo_orc else None
                
                # Total de visitas
                cliente['total_visitas'] = db.orcamentos.count_documents({'cliente_cpf': cliente.get('cpf')})
            
            result = convert_objectid(clientes_list)
            logger.info(f"✅ {len(result)} clientes carregados")
            return jsonify({'success': True, 'clientes': result})
        except Exception as e:
            logger.error(f"❌ Erro listar clientes: {e}", exc_info=True)
            return jsonify({'success': False, 'message': str(e)})
    
    # POST
    d = request.json
    logger.info(f"➕ Salvando cliente: {d.get('nome')}")
    
    try:
        existing = db.clientes.find_one({'cpf': d['cpf']})
        
        cliente_data = {
            **d,
            'updated_at': datetime.now()
        }
        
        if existing:
            db.clientes.update_one({'cpf': d['cpf']}, {'$set': cliente_data})
            logger.info(f"✅ Cliente atualizado: {d['nome']}")
        else:
            cliente_data['created_at'] = datetime.now()
            cliente_data['tags'] = []  # Para CRM
            cliente_data['notas'] = []  # Para CRM
            db.clientes.insert_one(cliente_data)
            logger.info(f"✅ Cliente criado: {d['nome']}")
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Erro salvar cliente: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/clientes/<id>', methods=['DELETE'])
@login_required
def delete_cliente(id):
    logger.info(f"🗑️ Deletando cliente: {id}")
    try:
        result = db.clientes.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            logger.info(f"✅ Cliente deletado: {id}")
            return jsonify({'success': True})
        logger.warning(f"⚠️ Cliente não encontrado: {id}")
        return jsonify({'success': False, 'message': 'Cliente não encontrado'})
    except Exception as e:
        logger.error(f"❌ Erro deletar cliente: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/clientes/buscar')
@login_required
def buscar_clientes():
    termo = request.args.get('termo', '')
    logger.info(f"🔍 Buscando clientes: {termo}")
    try:
        regex = {'$regex': termo, '$options': 'i'}
        clientes = list(db.clientes.find({'$or': [{'nome': regex}, {'cpf': regex}]}).limit(10))
        result = convert_objectid(clientes)
        logger.info(f"✅ {len(result)} clientes encontrados")
        return jsonify({'success': True, 'clientes': result})
    except Exception as e:
        logger.error(f"❌ Erro buscar clientes: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

# ===== CRM: ADICIONAR NOTA =====
@app.route('/api/clientes/<id>/nota', methods=['POST'])
@login_required
def add_nota_cliente(id):
    d = request.json
    logger.info(f"📝 Adicionando nota ao cliente: {id}")
    
    try:
        nota = {
            'texto': d['texto'],
            'usuario': session.get('username'),
            'data': datetime.now()
        }
        
        db.clientes.update_one(
            {'_id': ObjectId(id)},
            {'$push': {'notas': nota}}
        )
        
        logger.info(f"✅ Nota adicionada")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Erro adicionar nota: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

# ===== CRM: ADICIONAR TAG =====
@app.route('/api/clientes/<id>/tag', methods=['POST'])
@login_required
def add_tag_cliente(id):
    d = request.json
    logger.info(f"🏷️ Adicionando tag ao cliente: {id}")
    
    try:
        db.clientes.update_one(
            {'_id': ObjectId(id)},
            {'$addToSet': {'tags': d['tag']}}  # addToSet evita duplicatas
        )
        
        logger.info(f"✅ Tag adicionada: {d['tag']}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Erro adicionar tag: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})
    
# ===== PROFISSIONAIS =====
@app.route('/api/profissionais', methods=['GET', 'POST'])
@login_required
def profissionais():
    if request.method == 'GET':
        logger.info("📋 Listando profissionais")
        try:
            profs_list = list(db.profissionais.find({}).sort('nome', 1))
            result = convert_objectid(profs_list)
            logger.info(f"✅ {len(result)} profissionais encontrados")
            return jsonify({'success': True, 'profissionais': result})
        except Exception as e:
            logger.error(f"❌ Erro listar profissionais: {e}", exc_info=True)
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
        logger.error(f"❌ Erro salvar profissional: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/profissionais/<id>', methods=['DELETE'])
@login_required
def delete_profissional(id):
    logger.info(f"🗑️ Deletando profissional: {id}")
    try:
        result = db.profissionais.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            logger.info(f"✅ Profissional deletado")
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Profissional não encontrado'})
    except Exception as e:
        logger.error(f"❌ Erro deletar profissional: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

# ===== SERVIÇOS =====
@app.route('/api/servicos', methods=['GET', 'POST'])
@login_required
def servicos():
    if request.method == 'GET':
        logger.info("📋 Listando serviços")
        try:
            servs_list = list(db.servicos.find({}).sort('nome', 1))
            result = convert_objectid(servs_list)
            logger.info(f"✅ {len(result)} serviços encontrados")
            return jsonify({'success': True, 'servicos': result})
        except Exception as e:
            logger.error(f"❌ Erro listar serviços: {e}", exc_info=True)
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
                'duracao': int(d.get('duracao', 60)),  # NOVO: duração em minutos para agendamento
                'ativo': True,
                'created_at': datetime.now()
            })
            count += 1
        
        logger.info(f"✅ Serviço criado: {d['nome']} ({count} SKUs)")
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        logger.error(f"❌ Erro salvar serviço: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/servicos/<id>', methods=['DELETE'])
@login_required
def delete_servico(id):
    logger.info(f"🗑️ Deletando serviço: {id}")
    try:
        result = db.servicos.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            logger.info(f"✅ Serviço deletado")
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Serviço não encontrado'})
    except Exception as e:
        logger.error(f"❌ Erro deletar serviço: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/servicos/buscar')
@login_required
def buscar_servicos():
    termo = request.args.get('termo', '')
    logger.info(f"🔍 Buscando serviços: {termo}")
    try:
        regex = {'$regex': termo, '$options': 'i'}
        servicos = list(db.servicos.find({'nome': regex}).limit(20))
        result = convert_objectid(servicos)
        logger.info(f"✅ {len(result)} serviços encontrados")
        return jsonify({'success': True, 'servicos': result})
    except Exception as e:
        logger.error(f"❌ Erro buscar serviços: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

# ===== PRODUTOS COM GESTÃO DE ESTOQUE =====
@app.route('/api/produtos', methods=['GET', 'POST'])
@login_required
def produtos():
    if request.method == 'GET':
        logger.info("📋 Listando produtos")
        try:
            prods_list = list(db.produtos.find({}).sort('nome', 1))
            result = convert_objectid(prods_list)
            logger.info(f"✅ {len(result)} produtos encontrados")
            return jsonify({'success': True, 'produtos': result})
        except Exception as e:
            logger.error(f"❌ Erro listar produtos: {e}", exc_info=True)
            return jsonify({'success': False, 'message': str(e)})
    
    # POST
    d = request.json
    logger.info(f"➕ Cadastrando produto: {d.get('nome')}")
    try:
        produto_id = db.produtos.insert_one({
            'nome': d['nome'],
            'marca': d.get('marca', ''),
            'sku': d.get('sku', ''),
            'preco': float(d.get('preco', 0)),
            'custo': float(d.get('custo', 0)),
            'estoque': int(d.get('estoque', 0)),
            'estoque_minimo': int(d.get('estoque_minimo', 5)),  # NOVO: alerta de estoque
            'categoria': d.get('categoria', 'Produto'),
            'ativo': True,
            'created_at': datetime.now()
        }).inserted_id
        
        # REGISTRAR MOVIMENTAÇÃO INICIAL DE ESTOQUE
        if int(d.get('estoque', 0)) > 0:
            db.estoque_movimentacoes.insert_one({
                'produto_id': produto_id,
                'tipo': 'entrada',
                'quantidade': int(d.get('estoque', 0)),
                'motivo': 'Cadastro inicial',
                'custo_unitario': float(d.get('custo', 0)),
                'usuario': session.get('username'),
                'data': datetime.now()
            })
        
        logger.info(f"✅ Produto criado: {d['nome']}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Erro salvar produto: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/produtos/<id>', methods=['DELETE'])
@login_required
def delete_produto(id):
    logger.info(f"🗑️ Deletando produto: {id}")
    try:
        result = db.produtos.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            logger.info(f"✅ Produto deletado")
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Produto não encontrado'})
    except Exception as e:
        logger.error(f"❌ Erro deletar produto: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/produtos/buscar')
@login_required
def buscar_produtos():
    termo = request.args.get('termo', '')
    logger.info(f"🔍 Buscando produtos: {termo}")
    try:
        regex = {'$regex': termo, '$options': 'i'}
        produtos = list(db.produtos.find({'nome': regex}).limit(20))
        result = convert_objectid(produtos)
        logger.info(f"✅ {len(result)} produtos encontrados")
        return jsonify({'success': True, 'produtos': result})
    except Exception as e:
        logger.error(f"❌ Erro buscar produtos: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

# ===== GESTÃO DE ESTOQUE - MOVIMENTAÇÕES =====
@app.route('/api/estoque/movimentacao', methods=['POST'])
@login_required
def movimentacao_estoque():
    """Registra entrada/saída de estoque"""
    d = request.json
    logger.info(f"📦 Movimentação estoque: {d.get('tipo')}")
    
    try:
        produto_id = ObjectId(d['produto_id'])
        tipo = d['tipo']  # 'entrada' ou 'saida'
        quantidade = int(d['quantidade'])
        
        # Buscar produto
        produto = db.produtos.find_one({'_id': produto_id})
        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'})
        
        # Calcular novo estoque
        estoque_atual = produto.get('estoque', 0)
        
        if tipo == 'entrada':
            novo_estoque = estoque_atual + quantidade
        elif tipo == 'saida':
            if quantidade > estoque_atual:
                return jsonify({'success': False, 'message': 'Estoque insuficiente'})
            novo_estoque = estoque_atual - quantidade
        else:
            return jsonify({'success': False, 'message': 'Tipo inválido'})
        
        # Atualizar produto
        db.produtos.update_one(
            {'_id': produto_id},
            {'$set': {'estoque': novo_estoque, 'updated_at': datetime.now()}}
        )
        
        # Registrar movimentação
        db.estoque_movimentacoes.insert_one({
            'produto_id': produto_id,
            'tipo': tipo,
            'quantidade': quantidade,
            'estoque_anterior': estoque_atual,
            'estoque_novo': novo_estoque,
            'motivo': d.get('motivo', ''),
            'fornecedor_id': ObjectId(d['fornecedor_id']) if d.get('fornecedor_id') else None,
            'custo_unitario': float(d.get('custo_unitario', 0)),
            'usuario': session.get('username'),
            'data': datetime.now()
        })
        
        logger.info(f"✅ Movimentação registrada: {tipo} {quantidade}un")
        return jsonify({'success': True, 'novo_estoque': novo_estoque})
        
    except Exception as e:
        logger.error(f"❌ Erro movimentação estoque: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/estoque/historico/<produto_id>')
@login_required
def historico_estoque(produto_id):
    """Retorna histórico de movimentações de um produto"""
    logger.info(f"📊 Histórico estoque: {produto_id}")
    try:
        movimentacoes = list(db.estoque_movimentacoes.find(
            {'produto_id': ObjectId(produto_id)}
        ).sort('data', DESCENDING).limit(50))
        
        result = convert_objectid(movimentacoes)
        logger.info(f"✅ {len(result)} movimentações encontradas")
        return jsonify({'success': True, 'movimentacoes': result})
    except Exception as e:
        logger.error(f"❌ Erro histórico estoque: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/estoque/alerta')
@login_required
def alerta_estoque():
    """Retorna produtos com estoque abaixo do mínimo"""
    logger.info("⚠️ Verificando alertas de estoque")
    try:
        produtos_baixo = list(db.produtos.find({
            '$expr': {'$lte': ['$estoque', '$estoque_minimo']}
        }).sort('estoque', ASCENDING))
        
        result = convert_objectid(produtos_baixo)
        logger.info(f"✅ {len(result)} produtos com estoque baixo")
        return jsonify({'success': True, 'produtos': result})
    except Exception as e:
        logger.error(f"❌ Erro alerta estoque: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

# ===== SISTEMA DE AGENDAMENTO =====
@app.route('/api/agendamentos', methods=['GET', 'POST'])
@login_required
def agendamentos():
    if request.method == 'GET':
        logger.info("📅 Listando agendamentos")
        try:
            # Filtros opcionais
            data_inicio = request.args.get('data_inicio')
            data_fim = request.args.get('data_fim')
            profissional_id = request.args.get('profissional_id')
            status = request.args.get('status')
            
            query = {}
            
            if data_inicio and data_fim:
                query['data'] = {
                    '$gte': datetime.fromisoformat(data_inicio),
                    '$lte': datetime.fromisoformat(data_fim)
                }
            
            if profissional_id:
                query['profissional_id'] = ObjectId(profissional_id)
            
            if status:
                query['status'] = status
            
            agendamentos_list = list(db.agendamentos.find(query).sort('data', ASCENDING))
            
            # Enriquecer com dados
            for agend in agendamentos_list:
                # Buscar cliente
                cliente = db.clientes.find_one({'_id': ObjectId(agend['cliente_id'])})
                agend['cliente_nome'] = cliente['nome'] if cliente else 'N/A'
                
                # Buscar profissional
                prof = db.profissionais.find_one({'_id': ObjectId(agend['profissional_id'])})
                agend['profissional_nome'] = prof['nome'] if prof else 'N/A'
                
                # Buscar serviço
                servico = db.servicos.find_one({'_id': ObjectId(agend['servico_id'])})
                agend['servico_nome'] = f"{servico['nome']} - {servico['tamanho']}" if servico else 'N/A'
            
            result = convert_objectid(agendamentos_list)
            logger.info(f"✅ {len(result)} agendamentos encontrados")
            return jsonify({'success': True, 'agendamentos': result})
            
        except Exception as e:
            logger.error(f"❌ Erro listar agendamentos: {e}", exc_info=True)
            return jsonify({'success': False, 'message': str(e)})
    
    # POST - Criar agendamento
    d = request.json
    logger.info(f"➕ Criando agendamento")
    
    try:
        # Validar disponibilidade
        data_agendamento = datetime.fromisoformat(d['data'])
        horario = d['horario']  # "14:00"
        duracao = int(d.get('duracao', 60))  # minutos
        
        # Converter para datetime completo
        hora, minuto = map(int, horario.split(':'))
        data_hora_inicio = data_agendamento.replace(hour=hora, minute=minuto)
        data_hora_fim = data_hora_inicio + timedelta(minutes=duracao)
        
        # Verificar conflitos
        conflito = db.agendamentos.find_one({
            'profissional_id': ObjectId(d['profissional_id']),
            'status': {'$in': ['confirmado', 'em_andamento']},
            '$or': [
                {
                    'data_hora_inicio': {'$lt': data_hora_fim},
                    'data_hora_fim': {'$gt': data_hora_inicio}
                }
            ]
        })
        
        if conflito:
            logger.warning("⚠️ Conflito de horário detectado")
            return jsonify({'success': False, 'message': 'Horário já ocupado'})
        
        # Criar agendamento
        agendamento_id = db.agendamentos.insert_one({
            'cliente_id': ObjectId(d['cliente_id']),
            'profissional_id': ObjectId(d['profissional_id']),
            'servico_id': ObjectId(d['servico_id']),
            'data': data_agendamento,
            'horario': horario,
            'data_hora_inicio': data_hora_inicio,
            'data_hora_fim': data_hora_fim,
            'duracao': duracao,
            'status': 'confirmado',
            'observacoes': d.get('observacoes', ''),
            'lembrete_enviado': False,
            'created_at': datetime.now(),
            'created_by': session.get('username')
        }).inserted_id
        
        # Enviar SMS de confirmação
        cliente = db.clientes.find_one({'_id': ObjectId(d['cliente_id'])})
        if cliente and cliente.get('telefone'):
            send_sms(
                cliente['telefone'],
                f"BIOMA: Agendamento confirmado para {data_agendamento.strftime('%d/%m')} às {horario}. Até lá!"
            )
        
        logger.info(f"✅ Agendamento criado: {agendamento_id}")
        return jsonify({'success': True, 'id': str(agendamento_id)})
        
    except Exception as e:
        logger.error(f"❌ Erro criar agendamento: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/agendamentos/<id>', methods=['DELETE', 'PUT'])
@login_required
def manage_agendamento(id):
    if request.method == 'DELETE':
        logger.info(f"🗑️ Cancelando agendamento: {id}")
        try:
            # Marcar como cancelado ao invés de deletar
            result = db.agendamentos.update_one(
                {'_id': ObjectId(id)},
                {'$set': {'status': 'cancelado', 'cancelado_em': datetime.now()}}
            )
            
            if result.modified_count > 0:
                # Notificar cliente
                agend = db.agendamentos.find_one({'_id': ObjectId(id)})
                cliente = db.clientes.find_one({'_id': ObjectId(agend['cliente_id'])})
                
                if cliente and cliente.get('telefone'):
                    send_sms(
                        cliente['telefone'],
                        f"BIOMA: Seu agendamento para {agend['horario']} foi cancelado. Entre em contato para reagendar."
                    )
                
                logger.info(f"✅ Agendamento cancelado")
                return jsonify({'success': True})
            
            return jsonify({'success': False, 'message': 'Agendamento não encontrado'})
        except Exception as e:
            logger.error(f"❌ Erro cancelar agendamento: {e}", exc_info=True)
            return jsonify({'success': False, 'message': str(e)})
    
    # PUT - Atualizar status
    if request.method == 'PUT':
        d = request.json
        logger.info(f"🔄 Atualizando agendamento: {id}")
        try:
            db.agendamentos.update_one(
                {'_id': ObjectId(id)},
                {'$set': {'status': d['status'], 'updated_at': datetime.now()}}
            )
            logger.info(f"✅ Status atualizado: {d['status']}")
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"❌ Erro atualizar agendamento: {e}", exc_info=True)
            return jsonify({'success': False, 'message': str(e)})

@app.route('/api/agendamentos/disponibilidade')
@login_required
def disponibilidade_agendamento():
    """Retorna horários disponíveis para um profissional em uma data"""
    profissional_id = request.args.get('profissional_id')
    data = request.args.get('data')  # YYYY-MM-DD
    
    logger.info(f"🔍 Verificando disponibilidade: {data}")
    
    try:
        data_obj = datetime.fromisoformat(data)
        
        # Horários de funcionamento (08:00 às 20:00)
        horarios_disponiveis = []
        
        for hora in range(8, 20):
            for minuto in [0, 30]:
                horario = f"{hora:02d}:{minuto:02d}"
                data_hora = data_obj.replace(hour=hora, minute=minuto)
                
                # Verificar se está ocupado
                ocupado = db.agendamentos.find_one({
                    'profissional_id': ObjectId(profissional_id),
                    'data_hora_inicio': {'$lte': data_hora},
                    'data_hora_fim': {'$gt': data_hora},
                    'status': {'$in': ['confirmado', 'em_andamento']}
                })
                
                if not ocupado:
                    horarios_disponiveis.append(horario)
        
        logger.info(f"✅ {len(horarios_disponiveis)} horários disponíveis")
        return jsonify({'success': True, 'horarios': horarios_disponiveis})
        
    except Exception as e:
        logger.error(f"❌ Erro verificar disponibilidade: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

# ===== RELATÓRIOS GERENCIAIS =====
@app.route('/api/relatorios/faturamento')
@login_required
def relatorio_faturamento():
    """Relatório de faturamento por período"""
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    logger.info(f"📊 Relatório faturamento: {data_inicio} a {data_fim}")
    
    try:
        query = {'status': 'Aprovado'}
        
        if data_inicio and data_fim:
            query['created_at'] = {
                '$gte': datetime.fromisoformat(data_inicio),
                '$lte': datetime.fromisoformat(data_fim)
            }
        
        orcamentos = list(db.orcamentos.find(query))
        
        # Calcular métricas
        total_faturamento = sum(o.get('total_final', 0) for o in orcamentos)
        total_orcamentos = len(orcamentos)
        ticket_medio = total_faturamento / total_orcamentos if total_orcamentos > 0 else 0
        
        # Faturamento por dia
        faturamento_diario = {}
        for orc in orcamentos:
            data_key = orc['created_at'].strftime('%Y-%m-%d')
            if data_key not in faturamento_diario:
                faturamento_diario[data_key] = 0
            faturamento_diario[data_key] += orc.get('total_final', 0)
        
        # Faturamento por forma de pagamento
        faturamento_pagamento = {}
        for orc in orcamentos:
            tipo_pag = orc.get('pagamento', {}).get('tipo', 'Não informado')
            if tipo_pag not in faturamento_pagamento:
                faturamento_pagamento[tipo_pag] = 0
            faturamento_pagamento[tipo_pag] += orc.get('total_final', 0)
        
        relatorio = {
            'total_faturamento': total_faturamento,
            'total_orcamentos': total_orcamentos,
            'ticket_medio': ticket_medio,
            'faturamento_diario': faturamento_diario,
            'faturamento_por_pagamento': faturamento_pagamento
        }
        
        logger.info(f"✅ Relatório gerado: R$ {total_faturamento:.2f}")
        return jsonify({'success': True, 'relatorio': relatorio})
        
    except Exception as e:
        logger.error(f"❌ Erro relatório faturamento: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/relatorios/servicos-populares')
@login_required
def relatorio_servicos_populares():
    """Top 10 serviços mais vendidos"""
    logger.info("📊 Relatório serviços populares")
    
    try:
        # Agregar todos os serviços de todos os orçamentos
        servicos_vendidos = {}
        
        orcamentos = db.orcamentos.find({'status': 'Aprovado'})
        
        for orc in orcamentos:
            for servico in orc.get('servicos', []):
                nome = servico['nome']
                if nome not in servicos_vendidos:
                    servicos_vendidos[nome] = {'quantidade': 0, 'faturamento': 0}
                
                servicos_vendidos[nome]['quantidade'] += servico.get('qtd', 1)
                servicos_vendidos[nome]['faturamento'] += servico.get('total', 0)
        
        # Ordenar por quantidade
        top_servicos = sorted(
            [{'nome': k, **v} for k, v in servicos_vendidos.items()],
            key=lambda x: x['quantidade'],
            reverse=True
        )[:10]
        
        logger.info(f"✅ Top 10 serviços gerado")
        return jsonify({'success': True, 'servicos': top_servicos})
        
    except Exception as e:
        logger.error(f"❌ Erro relatório serviços: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/relatorios/comissoes')
@login_required
def relatorio_comissoes():
    """Relatório de comissões dos profissionais"""
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    logger.info(f"📊 Relatório comissões")
    
    try:
        # Buscar agendamentos concluídos
        query = {'status': 'concluido'}
        
        if data_inicio and data_fim:
            query['data'] = {
                '$gte': datetime.fromisoformat(data_inicio),
                '$lte': datetime.fromisoformat(data_fim)
            }
        
        agendamentos = list(db.agendamentos.find(query))
        
        comissoes = {}
        
        for agend in agendamentos:
            prof_id = str(agend['profissional_id'])
            
            if prof_id not in comissoes:
                prof = db.profissionais.find_one({'_id': agend['profissional_id']})
                comissoes[prof_id] = {
                    'profissional': prof['nome'] if prof else 'N/A',
                    'comissao_perc': prof.get('comissao_perc', 0) if prof else 0,
                    'total_servicos': 0,
                    'total_faturamento': 0,
                    'total_comissao': 0
                }
            
            # Buscar serviço para pegar valor
            servico = db.servicos.find_one({'_id': agend['servico_id']})
            valor_servico = servico.get('preco', 0) if servico else 0
            
            comissoes[prof_id]['total_servicos'] += 1
            comissoes[prof_id]['total_faturamento'] += valor_servico
            comissoes[prof_id]['total_comissao'] += valor_servico * (comissoes[prof_id]['comissao_perc'] / 100)
        
        resultado = list(comissoes.values())
        
        logger.info(f"✅ Relatório comissões gerado: {len(resultado)} profissionais")
        return jsonify({'success': True, 'comissoes': resultado})
        
    except Exception as e:
        logger.error(f"❌ Erro relatório comissões: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})
# ===== ORÇAMENTOS =====
@app.route('/api/orcamentos', methods=['GET', 'POST'])
@login_required
def orcamentos():
    if request.method == 'GET':
        logger.info("📋 Listando orçamentos")
        try:
            status = request.args.get('status')
            query = {'status': status} if status else {}
            orcs_list = list(db.orcamentos.find(query).sort('created_at', DESCENDING))
            result = convert_objectid(orcs_list)
            logger.info(f"✅ {len(result)} orçamentos encontrados")
            return jsonify({'success': True, 'orcamentos': result})
        except Exception as e:
            logger.error(f"❌ Erro listar orçamentos: {e}", exc_info=True)
            return jsonify({'success': False, 'message': str(e)})
    
    # POST
    d = request.json
    logger.info(f"➕ Criando orçamento: {d.get('cliente_nome')}")
    
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
        subtotal = sum(s['total'] for s in d.get('servicos', [])) + sum(p['total'] for p in d.get('produtos', []))
        desconto_valor = subtotal * (d.get('desconto_global', 0) / 100)
        total_com_desconto = subtotal - desconto_valor
        cashback_valor = total_com_desconto * (d.get('cashback_perc', 0) / 100)
        
        # Gerar número
        ultimo = db.orcamentos.find_one(sort=[('numero', DESCENDING)])
        numero = (ultimo['numero'] + 1) if ultimo and 'numero' in ultimo else 1
        
        # Salvar orçamento
        orc_id = db.orcamentos.insert_one({
            'numero': numero,
            'cliente_cpf': d['cliente_cpf'],
            'cliente_nome': d['cliente_nome'],
            'cliente_email': d.get('cliente_email', ''),
            'cliente_telefone': d.get('cliente_telefone', ''),
            'servicos': d.get('servicos', []),
            'produtos': d.get('produtos', []),
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
        
        # ATUALIZAR ESTOQUE SE TIVER PRODUTOS
        for produto in d.get('produtos', []):
            if 'id' in produto:
                prod = db.produtos.find_one({'_id': ObjectId(produto['id'])})
                if prod:
                    novo_estoque = prod.get('estoque', 0) - produto.get('qtd', 1)
                    db.produtos.update_one(
                        {'_id': ObjectId(produto['id'])},
                        {'$set': {'estoque': novo_estoque}}
                    )
                    
                    # Registrar saída de estoque
                    db.estoque_movimentacoes.insert_one({
                        'produto_id': ObjectId(produto['id']),
                        'tipo': 'saida',
                        'quantidade': produto.get('qtd', 1),
                        'motivo': f"Orçamento #{numero}",
                        'usuario': session.get('username'),
                        'data': datetime.now()
                    })
        
        # Se aprovado, gerar PDF e enviar
        if d.get('status') == 'Aprovado':
            logger.info(f"📄 Gerando PDF contrato #{numero}")
            orc = db.orcamentos.find_one({'_id': orc_id})
            pdf_bytes = gerar_contrato_pdf(orc)
            
            if d.get('cliente_email'):
                logger.info(f"📧 Enviando email para {d['cliente_email']}")
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
        logger.error(f"❌ Erro criar orçamento: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/orcamentos/<id>', methods=['DELETE'])
@login_required
def delete_orcamento(id):
    logger.info(f"🗑️ Deletando orçamento: {id}")
    try:
        result = db.orcamentos.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            logger.info(f"✅ Orçamento deletado")
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Orçamento não encontrado'})
    except Exception as e:
        logger.error(f"❌ Erro deletar orçamento: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

# ===== CONTRATOS =====
@app.route('/api/contratos')
@login_required
def contratos():
    logger.info("📋 Listando contratos")
    try:
        contratos_list = list(db.orcamentos.find({'status': 'Aprovado'}).sort('created_at', DESCENDING))
        result = convert_objectid(contratos_list)
        logger.info(f"✅ {len(result)} contratos encontrados")
        return jsonify({'success': True, 'contratos': result})
    except Exception as e:
        logger.error(f"❌ Erro listar contratos: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

# ===== DASHBOARD =====
@app.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    logger.info("📊 Carregando dashboard")
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
            })
        }
        
        logger.info(f"✅ Stats: {stats['total_orcamentos']} orçamentos, R$ {stats['faturamento']:.2f}")
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        logger.error(f"❌ Erro dashboard: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

# ===== FILA =====
@app.route('/api/fila', methods=['GET', 'POST'])
@login_required
def fila():
    if request.method == 'GET':
        logger.info("📋 Listando fila")
        try:
            fila_list = list(db.fila_atendimento.find({'status': {'$in': ['aguardando', 'atendendo']}}).sort('created_at', ASCENDING))
            result = convert_objectid(fila_list)
            logger.info(f"✅ {len(result)} pessoas na fila")
            return jsonify({'success': True, 'fila': result})
        except Exception as e:
            logger.error(f"❌ Erro listar fila: {e}", exc_info=True)
            return jsonify({'success': False, 'message': str(e)})
    
    # POST
    d = request.json
    logger.info(f"➕ Adicionando à fila: {d.get('cliente_nome')}")
    try:
        total = db.fila_atendimento.count_documents({'status': {'$in': ['aguardando', 'atendendo']}})
        
        db.fila_atendimento.insert_one({
            'cliente_nome': d['cliente_nome'],
            'cliente_telefone': d['cliente_telefone'],
            'servico': d.get('servico', ''),
            'profissional': d.get('profissional', ''),
            'posicao': total + 1,
            'status': 'aguardando',
            'created_at': datetime.now()
        })
        
        logger.info(f"✅ Adicionado à fila posição {total + 1}")
        
        if d.get('cliente_telefone'):
            send_sms(d['cliente_telefone'], f"BIOMA: Você está na posição {total + 1} da fila!")
        
        return jsonify({'success': True, 'posicao': total + 1})
    except Exception as e:
        logger.error(f"❌ Erro adicionar fila: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/fila/chamar/<id>', methods=['POST'])
@login_required
def chamar_fila(id):
    logger.info(f"📢 Chamando fila: {id}")
    try:
        item = db.fila_atendimento.find_one({'_id': ObjectId(id)})
        if item:
            db.fila_atendimento.update_one({'_id': ObjectId(id)}, {'$set': {'status': 'atendendo', 'chamado_at': datetime.now()}})
            logger.info(f"✅ Cliente chamado: {item.get('cliente_nome')}")
            if item.get('cliente_telefone'):
                send_sms(item['cliente_telefone'], f"BIOMA: {item['cliente_nome']}, é sua vez!")
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Item não encontrado'})
    except Exception as e:
        logger.error(f"❌ Erro chamar fila: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/fila/finalizar/<id>', methods=['POST'])
@login_required
def finalizar_fila(id):
    logger.info(f"✅ Finalizando fila: {id}")
    try:
        db.fila_atendimento.update_one({'_id': ObjectId(id)}, {'$set': {'status': 'finalizado', 'finalizado_at': datetime.now()}})
        logger.info(f"✅ Atendimento finalizado")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Erro finalizar fila: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/fila/<id>', methods=['DELETE'])
@login_required
def delete_fila(id):
    logger.info(f"🗑️ Deletando fila: {id}")
    try:
        result = db.fila_atendimento.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            logger.info(f"✅ Fila deletada")
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Item não encontrado'})
    except Exception as e:
        logger.error(f"❌ Erro deletar fila: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

# ===== CONFIGURAÇÕES =====
@app.route('/api/config', methods=['GET', 'POST'])
@login_required
def config():
    if request.method == 'GET':
        logger.info("📋 Carregando config")
        try:
            cfg = db.config.find_one({'key': 'unidade'}) or {}
            result = convert_objectid(cfg)
            return jsonify({'success': True, 'config': result})
        except Exception as e:
            logger.error(f"❌ Erro carregar config: {e}", exc_info=True)
            return jsonify({'success': False, 'message': str(e)})
    
    # POST
    d = request.json
    logger.info("💾 Salvando config")
    try:
        db.config.update_one({'key': 'unidade'}, {'$set': d}, upsert=True)
        logger.info("✅ Config salva")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"❌ Erro salvar config: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

# ===== CEP =====
@app.route('/api/cep/<cep>')
@login_required
def buscar_cep(cep):
    logger.info(f"📍 Buscando CEP: {cep}")
    try:
        r = requests.get(f'https://viacep.com.br/ws/{cep}/json/', timeout=5)
        data = r.json()
        if 'erro' not in data:
            logger.info(f"✅ CEP encontrado: {data.get('localidade')}")
            return jsonify({'success': True, 'endereco': {
                'logradouro': data.get('logradouro', ''),
                'bairro': data.get('bairro', ''),
                'cidade': data.get('localidade', ''),
                'estado': data.get('uf', '')
            }})
        return jsonify({'success': False, 'message': 'CEP não encontrado'})
    except Exception as e:
        logger.error(f"❌ Erro CEP: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

# ===== IMPORTAÇÃO CSV/XLSX ULTRA ROBUSTA =====
@app.route('/api/importar', methods=['POST'])
@login_required
def importar():
    logger.info("📤 Iniciando importação")
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'})
    
    f = request.files['file']
    t = request.form.get('tipo', 'produtos')
    
    if not f.filename:
        return jsonify({'success': False, 'message': 'Arquivo inválido'})
    
    ext = f.filename.rsplit('.', 1)[1].lower() if '.' in f.filename else ''
    
    if ext not in ['csv', 'xlsx', 'xls']:
        return jsonify({'success': False, 'message': 'Apenas CSV ou XLSX'})
    
    logger.info(f"📄 Importando {ext.upper()} - Tipo: {t}")
    
    try:
        fn = secure_filename(f.filename)
        fp = os.path.join(app.config['UPLOAD_FOLDER'], fn)
        f.save(fp)
        
        cs = 0  # sucesso
        ce = 0  # erro
        rows = []
        erros_detalhados = []
        
        # LER ARQUIVO
        if ext == 'csv':
            logger.info("🔄 Lendo CSV...")
            encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(fp, 'r', encoding=encoding) as csvfile:
                        reader = csv.DictReader(csvfile)
                        rows = list(reader)
                        logger.info(f"✅ CSV lido com {encoding} - {len(rows)} linhas")
                        break
                except UnicodeDecodeError:
                    continue
            
            if not rows:
                return jsonify({'success': False, 'message': 'Erro ler CSV - encoding não suportado'})
        else:
            logger.info("🔄 Lendo XLSX...")
            from openpyxl import load_workbook
            wb = load_workbook(fp, read_only=True, data_only=True)
            ws = wb.active
            headers = [str(c.value).strip().lower() if c.value else '' for c in next(ws.iter_rows(min_row=1, max_row=1))]
            logger.info(f"📋 Headers: {headers}")
            
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
            logger.info(f"✅ XLSX lido - {len(rows)} linhas")
        
        logger.info(f"🔄 Processando {len(rows)} linhas para {t}...")
        
        # PROCESSAR PRODUTOS
        if t == 'produtos':
            logger.info("📦 Processando PRODUTOS...")
            
            for idx, row in enumerate(rows, 1):
                try:
                    r = {k.lower().strip(): v for k, v in row.items() if k and v is not None}
                    
                    # VALIDAÇÃO: Linha vazia
                    if not r or all(not v for v in r.values()):
                        logger.debug(f"⚠️ Linha {idx}: Vazia - ignorada")
                        continue
                    
                    # NOME
                    nome = None
                    for col in ['nome', 'produto', 'name', 'descricao', 'descrição']:
                        if col in r and r[col] and str(r[col]).strip() and str(r[col]).strip().lower() not in ['none', '-', '']:
                            nome = str(r[col]).strip()
                            break
                    
                    if not nome or len(nome) < 2:
                        erros_detalhados.append(f"Linha {idx}: Nome inválido ou ausente")
                        logger.debug(f"⚠️ Linha {idx}: Nome inválido - {r}")
                        ce += 1
                        continue
                    
                    # MARCA
                    marca = ''
                    for col in ['marca', 'brand']:
                        if col in r and r[col] and str(r[col]).strip().lower() not in ['none', '-', '']:
                            marca = str(r[col]).strip()
                            break
                    
                    # SKU
                    sku = ''
                    for col in ['sku', 'codigo', 'código', 'code']:
                        if col in r and r[col] and str(r[col]).strip().lower() not in ['none', '-', '']:
                            sku = str(r[col]).strip()
                            break
                    if not sku:
                        sku = f"PROD-{cs+1}"
                    
                    # PREÇO (CORREÇÃO: Aceitar vírgula e ponto)
                    preco = 0.0
                    for col in ['preco', 'preço', 'price', 'valor']:
                        if col in r and r[col]:
                            try:
                                val = str(r[col])
                                # Remover R$, espaços
                                val = val.replace('R$', '').replace('r$', '').strip()
                                # Se tem vírgula e ponto, assumir formato BR (1.234,56)
                                if ',' in val and '.' in val:
                                    val = val.replace('.', '').replace(',', '.')
                                # Se só tem vírgula, assumir decimal BR (12,50)
                                elif ',' in val:
                                    val = val.replace(',', '.')
                                # Remover tudo exceto dígitos e ponto
                                val = ''.join(c for c in val if c.isdigit() or c == '.')
                                if val:
                                    preco = float(val)
                                    break
                            except Exception as ep:
                                logger.debug(f"⚠️ Linha {idx}: Erro converter preço '{r[col]}': {ep}")
                                continue
                    
                    # VALIDAÇÃO: Preço obrigatório
                    if preco <= 0:
                        erros_detalhados.append(f"Linha {idx}: Preço inválido ou zero")
                        logger.debug(f"⚠️ Linha {idx}: Preço inválido - {r}")
                        ce += 1
                        continue
                    
                    # CUSTO
                    custo = 0.0
                    for col in ['custo', 'cost']:
                        if col in r and r[col]:
                            try:
                                val = str(r[col])
                                val = val.replace('R$', '').replace('r$', '').strip()
                                if ',' in val and '.' in val:
                                    val = val.replace('.', '').replace(',', '.')
                                elif ',' in val:
                                    val = val.replace(',', '.')
                                val = ''.join(c for c in val if c.isdigit() or c == '.')
                                if val:
                                    custo = float(val)
                                    break
                            except:
                                continue
                    
                    # ESTOQUE
                    estoque = 0
                    for col in ['estoque', 'quantidade', 'qtd']:
                        if col in r and r[col]:
                            try:
                                estoque = int(float(r[col]))
                                break
                            except:
                                continue
                    
                    # CATEGORIA
                    categoria = 'Produto'
                    for col in ['categoria', 'category']:
                        if col in r and r[col] and str(r[col]).strip().lower() not in ['none', '-', '']:
                            categoria = str(r[col]).strip().title()
                            break
                    
                    # INSERIR
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
                    cs += 1
                    logger.info(f"✅ Produto {cs}: {nome} - R$ {preco:.2f}")
                    
                except Exception as e:
                    erros_detalhados.append(f"Linha {idx}: {str(e)}")
                    logger.error(f"❌ Erro linha {idx}: {e}", exc_info=True)
                    ce += 1
        
        # PROCESSAR SERVIÇOS
        else:
            logger.info("✂️ Processando SERVIÇOS...")
            
            for idx, row in enumerate(rows, 1):
                try:
                    r = {k.lower().strip(): v for k, v in row.items() if k and v is not None}
                    
                    # Linha vazia
                    if not r or all(not v for v in r.values()):
                        continue
                    
                    # NOME
                    nome = None
                    for col in ['nome', 'servico', 'serviço', 'service']:
                        if col in r and r[col] and str(r[col]).strip():
                            nome = re.sub(r'^\d+', '', str(r[col])).strip()
                            break
                    
                    if not nome or len(nome) < 2:
                        erros_detalhados.append(f"Linha {idx}: Nome inválido")
                        ce += 1
                        continue
                    
                    # CATEGORIA
                    categoria = 'Serviço'
                    for col in ['categoria', 'category']:
                        if col in r and r[col]:
                            categoria = str(r[col]).strip().title()
                            break
                    
                    # PREÇOS POR TAMANHO
                    tamanhos_map = {
                        'kids': ['kids', 'kid', 'infantil', 'crianca', 'criança'],
                        'masculino': ['masculino', 'male', 'masc'],
                        'curto': ['curto', 'short'],
                        'medio': ['medio', 'médio', 'medium'],
                        'longo': ['longo', 'long'],
                        'extra_longo': ['extra_longo', 'extra longo', 'xl', 'extralongo']
                    }
                    
                    servicos_criados = 0
                    for tam_key, aliases in tamanhos_map.items():
                        for alias in aliases:
                            if alias in r and r[alias]:
                                try:
                                    val = str(r[alias])
                                    val = val.replace('R$', '').replace('r$', '').strip()
                                    if ',' in val and '.' in val:
                                        val = val.replace('.', '').replace(',', '.')
                                    elif ',' in val:
                                        val = val.replace(',', '.')
                                    val = ''.join(c for c in val if c.isdigit() or c == '.')
                                    if val:
                                        preco = float(val)
                                        if preco > 0:
                                            tam_nome = tam_key.replace('_', ' ').title()
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
                                            servicos_criados += 1
                                            logger.info(f"✅ Serviço: {nome} - {tam_nome} - R$ {preco:.2f}")
                                        break
                                except Exception as ep:
                                    logger.debug(f"⚠️ Erro processar preço {alias}: {ep}")
                                    continue
                    
                    if servicos_criados > 0:
                        cs += 1
                    else:
                        erros_detalhados.append(f"Linha {idx}: Nenhum preço válido encontrado")
                        ce += 1
                    
                except Exception as e:
                    erros_detalhados.append(f"Linha {idx}: {str(e)}")
                    logger.error(f"❌ Erro linha {idx}: {e}", exc_info=True)
                    ce += 1
        
        # Remover arquivo
        os.remove(fp)
        logger.info(f"🗑️ Arquivo temporário removido")
        
        msg = f'{cs} registros importados com sucesso!'
        if ce > 0:
            msg += f' ({ce} linhas com erro foram ignoradas)'
        
        logger.info(f"🎉 Importação concluída: {cs} sucesso, {ce} erros")
        
        return jsonify({
            'success': True,
            'message': msg,
            'count_success': cs,
            'count_error': ce,
            'erros_detalhados': erros_detalhados[:10]  # Primeiros 10 erros
        })
        
    except Exception as e:
        logger.error(f"❌ Erro geral importação: {e}", exc_info=True)
        if os.path.exists(fp):
            os.remove(fp)
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

# ===== DOWNLOAD TEMPLATE =====
@app.route('/api/template/download/<tipo>')
@login_required
def download_template(tipo):
    logger.info(f"📥 Download template: {tipo}")
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    if tipo == 'produtos':
        writer.writerow(['nome', 'marca', 'sku', 'preco', 'custo', 'estoque', 'categoria'])
        writer.writerow(['Shampoo 500ml', 'Loreal', 'SHAMP-500', '49,90', '20,00', '50', 'SHAMPOO'])
        writer.writerow(['Condicionador 400ml', 'Pantene', 'COND-400', '39.90', '15.00', '30', 'CONDICIONADOR'])
    else:
        writer.writerow(['nome', 'categoria', 'kids', 'masculino', 'curto', 'medio', 'longo', 'extra_longo'])
        writer.writerow(['Hidratação', 'Tratamento', '50', '60', '80', '100', '120', '150'])
        writer.writerow(['Corte', 'Cabelo', '40,00', '50', '60', '80', '100', '120'])
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'template_{tipo}.csv'
    )
# ===== GERAÇÃO DE PDF PROFISSIONAL =====
def gerar_contrato_pdf(orc):
    """Gera PDF do contrato igual ao modelo fornecido"""
    logger.info(f"📄 Gerando PDF contrato #{orc.get('numero')}")
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    
    # CABEÇALHO
    c.setFillColor(HexColor('#7C3AED'))
    c.setFont('Helvetica-Bold', 28)
    c.drawRightString(w - 2*cm, h - 2*cm, 'BIOMA')
    
    c.setFillColor(black)
    c.setFont('Helvetica-Bold', 16)
    c.drawCentredString(w/2, h - 3*cm, 'CONTRATO DE PRESTAÇÃO DE SERVIÇOS')
    
    c.setFont('Helvetica', 10)
    c.drawCentredString(w/2, h - 3.7*cm, 'Pelo presente Instrumento Particular e na melhor forma de direito, as partes abaixo qualificadas:')
    
    c.setStrokeColor(HexColor('#7C3AED'))
    c.setLineWidth(2)
    c.line(2*cm, h - 4.2*cm, w - 2*cm, h - 4.2*cm)
    
    y = h - 5*cm
    
    # PARTES
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
    
    # ALERGIAS
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
    
    # TABELA SERVIÇOS
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(w/2, y, 'SERVIÇOS')
    y -= 0.6*cm
    
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
    
    # TOTAIS
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
    
    # UTILIZAÇÃO
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(w/2, y, 'UTILIZAÇÃO')
    y -= 0.5*cm
    c.drawCentredString(w/2, y, 'PRAZO PARA UTILIZAÇÃO')
    y -= 0.5*cm
    c.setFont('Helvetica', 9)
    c.drawCentredString(w/2, y, '03 mês(es) contados da assinatura deste Contrato.')
    y -= 1*cm
    
    # PAGAMENTO
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(w/2, y, 'VALOR E FORMA DE PAGAMENTO')
    y -= 0.6*cm
    c.setFont('Helvetica', 9)
    c.drawString(2*cm, y, f"VALOR TOTAL: R$ {orc.get('total_final', 0):.2f}")
    y -= 0.5*cm
    c.drawString(2*cm, y, f"FORMA DE PAGAMENTO: {orc.get('pagamento', {}).get('tipo', 'Pix')}")
    y -= 1*cm
    
    # DISPOSIÇÕES
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(w/2, y, 'DISPOSIÇÕES GERAIS')
    y -= 0.5*cm
    c.setFont('Helvetica', 8)
    c.drawString(2*cm, y, 'Pelo presente instrumento particular, as "Partes" resolvem celebrar o presente "Contrato", de acordo com as cláusulas e condições a seguir.')
    y -= 0.5*cm
    
    clausulas = [
        "1. O Contrato tem por objeto a prestação de serviços acima descritos, pela Contratada à Contratante, mediante agendamento prévio.",
        "2. A Contratante declara estar ciente que (i) os serviços têm caráter pessoal e não são transferíveis.",
        "3. Os serviços deverão ser utilizados em conformidade com o prazo acima indicado à Contratante."
    ]
    
    for clausula in clausulas:
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
    
    # ASSINATURAS
    meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 
             'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
    agora = datetime.now()
    data_extenso = f"UBERABA, {agora.day} de {meses[agora.month - 1]} de {agora.year}"
    
    c.setFont('Helvetica', 9)
    c.drawCentredString(w/2, y, data_extenso)
    y -= 1.5*cm
    
    c.setLineWidth(1)
    c.line(3*cm, y, 8.5*cm, y)
    c.line(11*cm, y, 17*cm, y)
    y -= 0.4*cm
    
    c.setFont('Helvetica-Bold', 8)
    c.drawCentredString(5.75*cm, y, f"CONTRATANTE: {orc.get('cliente_nome', 'N/A')}")
    c.drawCentredString(14*cm, y, f"CONTRATADA: BIOMA UBERABA - {cfg.get('cnpj', '49.470.937/0001-10')}")
    
    # RODAPÉ
    c.setFont('Helvetica', 7)
    c.setFillColor(HexColor('#6B7280'))
    c.drawCentredString(w/2, 1.5*cm, f"Contrato #{orc.get('numero')} | BIOMA UBERABA | {cfg.get('telefone', '34 99235-5890')} | {cfg.get('email', 'biomauberaba@gmail.com')}")
    
    c.save()
    buffer.seek(0)
    
    logger.info(f"✅ PDF gerado: contrato #{orc.get('numero')}")
    return buffer.getvalue()

# ===== ROTA DOWNLOAD PDF =====
@app.route('/api/gerar-contrato-pdf/<id>')
@login_required
def gerar_contrato_pdf_route(id):
    logger.info(f"📥 Download PDF: {id}")
    try:
        orc = db.orcamentos.find_one({'_id': ObjectId(id)})
        if not orc:
            logger.warning(f"⚠️ Orçamento não encontrado: {id}")
            return "Orçamento não encontrado", 404
        
        pdf_bytes = gerar_contrato_pdf(orc)
        
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'contrato_bioma_{orc["numero"]}.pdf'
        )
    except Exception as e:
        logger.error(f"❌ Erro gerar PDF: {e}", exc_info=True)
        return f"Erro: {str(e)}", 500

# ===== DEBUG =====
@app.route('/api/debug/test-db')
@login_required
def test_db():
    logger.info("🔬 Debug banco de dados")
    try:
        db.command('ping')
        
        counts = {
            'clientes': db.clientes.count_documents({}),
            'servicos': db.servicos.count_documents({}),
            'produtos': db.produtos.count_documents({}),
            'orcamentos': db.orcamentos.count_documents({}),
            'profissionais': db.profissionais.count_documents({}),
            'fila': db.fila_atendimento.count_documents({}),
            'agendamentos': db.agendamentos.count_documents({})
        }
        
        samples = {
            'cliente': convert_objectid(db.clientes.find_one()),
            'servico': convert_objectid(db.servicos.find_one()),
            'produto': convert_objectid(db.produtos.find_one())
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
        logger.error(f"❌ Erro debug: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)})

# ===== INICIALIZAÇÃO =====
def init_db():
    """Inicializa banco com dados padrão"""
    if db is None:
        logger.warning("⚠️ DB não disponível")
        return
    
    logger.info("🔧 Inicializando banco...")
    
    # Admin
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
        logger.info("✅ Admin criado: admin/admin123")
    
    # Serviços
    if db.servicos.count_documents({}) == 0:
        servicos = [
            ('Hidratação', 'Tratamento', 50, 60, 80, 100, 120, 150),
            ('Corte Feminino', 'Cabelo', 40, 50, 60, 80, 100, 120),
            ('Corte Masculino', 'Cabelo', 30, 40, 50, 60, 70, 80)
        ]
        
        for nome, cat, kids, masc, curto, medio, longo, xl in servicos:
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
        logger.info("✅ Serviços criados (18 SKUs)")
    
    # Produto
    if db.produtos.count_documents({}) == 0:
        db.produtos.insert_one({
            'nome': 'Shampoo 500ml',
            'marca': 'BIOMA',
            'sku': 'SHAMP-500',
            'preco': 49.90,
            'custo': 20.00,
            'estoque': 50,
            'estoque_minimo': 5,
            'categoria': 'SHAMPOO',
            'ativo': True,
            'created_at': datetime.now()
        })
        logger.info("✅ Produto criado")
    
    # Profissional
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
        logger.info("✅ Profissional criado")
    
    # Config
    if db.config.count_documents({}) == 0:
        db.config.insert_one({
            'key': 'unidade',
            'nome': 'BIOMA UBERABA',
            'cnpj': '49.470.937/0001-10',
            'endereco': 'Av. Santos Dumont 3110 - Santa Maria - Uberaba/MG - CEP 38050-400',
            'telefone': '34 99235-5890',
            'email': 'biomauberaba@gmail.com'
        })
        logger.info("✅ Config criada")
    
    # Índices para performance
    try:
        db.clientes.create_index([('cpf', ASCENDING)], unique=True, sparse=True)
        db.orcamentos.create_index([('numero', ASCENDING)], unique=True)
        db.agendamentos.create_index([('data', ASCENDING), ('profissional_id', ASCENDING)])
        db.produtos.create_index([('sku', ASCENDING)])
        logger.info("✅ Índices criados")
    except Exception as e:
        logger.warning(f"⚠️ Erro criar índices: {e}")
    
    logger.info("🎉 Banco inicializado!")

# ===== EXECUÇÃO =====
if __name__ == '__main__':
    print("\n" + "="*80)
    print("🌳 BIOMA UBERABA v3.0 - ULTRA AVANÇADO")
    print("="*80)
    
    init_db()
    
    is_prod = os.getenv('FLASK_ENV') == 'production'
    url = 'https://bioma-system2.onrender.com' if is_prod else 'http://localhost:5000'
    
    print(f"🚀 URL: {url}")
    print(f"🔒 HTTPS: {'✅ ATIVO' if is_prod else '⚠️  Local'}")
    print(f"👤 Login: admin / admin123")
    print(f"📧 Email: {'✅ OK' if os.getenv('MAILERSEND_API_KEY') else '⚠️  OFF'}")
    print(f"💾 MongoDB: {'✅ CONECTADO' if db else '❌ OFFLINE'}")
    print(f"📊 Logs: ✅ DEBUG MODE")
    print("="*80)
    print("✨ NOVAS FUNCIONALIDADES v3.0:")
    print("  📅 Sistema de Agendamento")
    print("  📦 Gestão de Estoque Completa")
    print("  📊 Relatórios Gerenciais")
    print("  👥 CRM Básico (Notas + Tags)")
    print("="*80)
    print(f"🕐 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"👨‍💻 Dev: @juanmarco1999")
    print(f"📧 Email: 180147064@aluno.unb.br")
    print("="*80 + "\n")
    
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"🚀 Iniciando servidor Flask porta {port}")
    
    app.run(
        debug=False,
        host='0.0.0.0',
        port=port,
        threaded=True
    )