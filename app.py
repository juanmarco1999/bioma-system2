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

@app.route('/api/clientes/buscar')
@login_required
def buscar_clientes():
    if db is None:
        return jsonify({'success': False}), 500
    termo = request.args.get('termo', '')
    try:
        regex = {'$regex': termo, '$options': 'i'}
        clientes = list(db.clientes.find({'$or': [{'nome': regex}, {'cpf': regex}]}).limit(10))
        return jsonify({'success': True, 'clientes': convert_objectid(clientes)})
    except:
        return jsonify({'success': False}), 500

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
        db.profissionais.insert_one({'nome': data['nome'], 'cpf': data['cpf'], 'email': data.get('email', ''), 'telefone': data.get('telefone', ''), 'especialidade': data.get('especialidade', ''), 'comissao_perc': float(data.get('comissao_perc', 0)), 'ativo': True, 'created_at': datetime.now()})
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

@app.route('/api/servicos/buscar')
@login_required
def buscar_servicos():
    if db is None:
        return jsonify({'success': False}), 500
    termo = request.args.get('termo', '')
    try:
        servicos = list(db.servicos.find({'nome': {'$regex': termo, '$options': 'i'}}).limit(20))
        return jsonify({'success': True, 'servicos': convert_objectid(servicos)})
    except:
        return jsonify({'success': False}), 500

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

@app.route('/api/produtos/buscar')
@login_required
def buscar_produtos():
    if db is None:
        return jsonify({'success': False}), 500
    termo = request.args.get('termo', '')
    try:
        produtos = list(db.produtos.find({'nome': {'$regex': termo, '$options': 'i'}}).limit(20))
        return jsonify({'success': True, 'produtos': convert_objectid(produtos)})
    except:
        return jsonify({'success': False}), 500

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