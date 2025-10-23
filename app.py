#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA UBERABA v3.8 - VERSÃO CORRIGIDA E MELHORADA
Sistema Ultra Profissional com Correções e Novas Funcionalidades
Desenvolvedor: Juan Marco (@juanmarco1999)
Data de Atualização: 2025-10-22
"""

from flask import Flask, render_template, request, jsonify, session, send_file, redirect, url_for
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
import base64
from PIL import Image

# Importações para PDF e Excel
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import cm
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# ==================== CACHE SYSTEM ====================
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

# ==================== FLASK APP CONFIGURATION ====================
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'bioma-2025-v3-8-ultra-secure-key-corrigido')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['UPLOAD_FOLDER'] = '/tmp'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# CORS configuration
CORS(app, supports_credentials=True)
FRONTEND_ORIGIN = os.getenv('FRONTEND_ORIGIN')
if os.getenv('CROSS_SITE_DEV', '0') == '1':
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    if FRONTEND_ORIGIN:
        CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": FRONTEND_ORIGIN}})

# ==================== MONGODB CONNECTION ====================
def get_mongo_client():
    """Estabelece conexão com MongoDB"""
    try:
        username = urllib.parse.quote_plus(os.getenv('MONGO_USERNAME', ''))
        password = urllib.parse.quote_plus(os.getenv('MONGO_PASSWORD', ''))
        cluster = os.getenv('MONGO_CLUSTER', '')
        
        if not all([username, password, cluster]):
            logger.error("❌ Credenciais MongoDB não configuradas")
            return None
        
        mongo_uri = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority"
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.server_info()
        logger.info("✅ MongoDB conectado com sucesso")
        return client['bioma_db']
    except Exception as e:
        logger.error(f"❌ Erro ao conectar MongoDB: {e}")
        return None

db = get_mongo_client()

# ==================== PERFIS DE ACESSO ====================
PERFIS_ACESSO = {
    'admin': {
        'nome': 'Administrador',
        'permissoes': ['*'],  # Acesso total
        'descricao': 'Acesso completo ao sistema'
    },
    'gestao': {
        'nome': 'Gestão',
        'permissoes': [
            'visualizar_relatorios',
            'visualizar_financeiro',
            'gerenciar_clientes',
            'gerenciar_profissionais',
            'gerenciar_servicos',
            'gerenciar_produtos',
            'gerenciar_estoque',
            'aprovar_orcamentos',
            'gerenciar_contratos'
        ],
        'descricao': 'Acesso a gestão e relatórios'
    },
    'profissional': {
        'nome': 'Profissional',
        'permissoes': [
            'visualizar_agenda',
            'gerenciar_agenda',
            'visualizar_clientes',
            'criar_orcamentos',
            'visualizar_comissoes',
            'atualizar_fila'
        ],
        'descricao': 'Acesso para profissionais'
    }
}

def verificar_permissao(permissao_necessaria):
    """Decorator para verificar permissões de acesso"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'success': False, 'message': 'Não autenticado'}), 401
            
            user_id = session.get('user_id')
            try:
                usuario = db.usuarios.find_one({'_id': ObjectId(user_id)})
                if not usuario:
                    return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
                
                perfil = usuario.get('perfil', 'profissional')
                permissoes = PERFIS_ACESSO.get(perfil, {}).get('permissoes', [])
                
                # Admin tem acesso total
                if '*' in permissoes or permissao_necessaria in permissoes:
                    return f(*args, **kwargs)
                
                return jsonify({
                    'success': False,
                    'message': f'Permissão negada. Você precisa de: {permissao_necessaria}'
                }), 403
                
            except Exception as e:
                logger.error(f"Erro ao verificar permissão: {e}")
                return jsonify({'success': False, 'message': str(e)}), 500
        
        return decorated_function
    return decorator

# ==================== HELPER FUNCTIONS ====================
def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def processar_imagem(file, max_size=(800, 800)):
    """Processa e otimiza imagem"""
    try:
        img = Image.open(file)
        
        # Converter para RGB se necessário
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Redimensionar mantendo aspect ratio
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Salvar em BytesIO
        output = BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        
        return output
    except Exception as e:
        logger.error(f"Erro ao processar imagem: {e}")
        return None

def formatar_telefone(numero):
    """Formata número de telefone para WhatsApp"""
    # Remove caracteres não numéricos
    numero = re.sub(r'[^0-9]', '', numero)
    
    # Adiciona código do país se não tiver
    if len(numero) == 11:  # Celular brasileiro
        numero = '55' + numero
    elif len(numero) == 10:  # Fixo brasileiro
        numero = '55' + numero
    
    return numero

def gerar_link_whatsapp(numero, mensagem=''):
    """Gera link para WhatsApp"""
    numero_formatado = formatar_telefone(numero)
    mensagem_encoded = urllib.parse.quote(mensagem)
    return f"https://wa.me/{numero_formatado}?text={mensagem_encoded}"

# ==================== AUTHENTICATION DECORATOR ====================
def login_required(f):
    """Decorator para rotas que requerem autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Sessão expirada'}), 401
        return f(*args, **kwargs)
    return decorated_function

# ==================== INIT DATABASE ====================
def init_db():
    """Inicializa banco de dados com índices e dados padrão"""
    if db is None:
        logger.error("❌ Banco de dados não conectado")
        return
    
    try:
        # Criar índices
        db.usuarios.create_index([('email', ASCENDING)], unique=True)
        db.clientes.create_index([('telefone', ASCENDING)])
        db.clientes.create_index([('nome', ASCENDING)])
        db.profissionais.create_index([('nome', ASCENDING)])
        db.servicos.create_index([('nome', ASCENDING)])
        db.produtos.create_index([('nome', ASCENDING)])
        db.orcamentos.create_index([('numero', ASCENDING)], unique=True)
        db.contratos.create_index([('numero', ASCENDING)], unique=True)
        db.agendamentos.create_index([('data', ASCENDING)])
        
        # Criar usuário admin padrão se não existir
        if db.usuarios.count_documents({}) == 0:
            admin_user = {
                'email': 'admin',
                'senha': generate_password_hash('admin123'),
                'nome': 'Administrador',
                'perfil': 'admin',
                'data_criacao': datetime.now(),
                'ativo': True
            }
            db.usuarios.insert_one(admin_user)
            logger.info("✅ Usuário admin criado")
        
        logger.info("✅ Banco de dados inicializado")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco: {e}")

# ==================== AUTHENTICATION ROUTES ====================
@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    """Login de usuário"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        senha = data.get('senha', '')
        
        if not email or not senha:
            return jsonify({'success': False, 'message': 'Email e senha são obrigatórios'}), 400
        
        usuario = db.usuarios.find_one({'email': email})
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        if not usuario.get('ativo', True):
            return jsonify({'success': False, 'message': 'Usuário inativo'}), 403
        
        if not check_password_hash(usuario['senha'], senha):
            return jsonify({'success': False, 'message': 'Senha incorreta'}), 401
        
        # Criar sessão
        session.permanent = True
        session['user_id'] = str(usuario['_id'])
        session['user_email'] = usuario['email']
        session['user_nome'] = usuario.get('nome', 'Usuário')
        session['user_perfil'] = usuario.get('perfil', 'profissional')
        
        # Atualizar último acesso
        db.usuarios.update_one(
            {'_id': usuario['_id']},
            {'$set': {'ultimo_acesso': datetime.now()}}
        )
        
        logger.info(f"✅ Login realizado: {email}")
        return jsonify({
            'success': True,
            'message': 'Login realizado com sucesso',
            'user': {
                'id': str(usuario['_id']),
                'nome': usuario.get('nome', 'Usuário'),
                'email': usuario['email'],
                'perfil': usuario.get('perfil', 'profissional'),
                'perfil_nome': PERFIS_ACESSO.get(usuario.get('perfil', 'profissional'), {}).get('nome', 'Profissional')
            }
        })
    except Exception as e:
        logger.error(f"❌ Erro no login: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    """Registro de novo usuário"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        senha = data.get('senha', '')
        nome = data.get('nome', '').strip()
        perfil = data.get('perfil', 'profissional')
        
        if not all([email, senha, nome]):
            return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios'}), 400
        
        if perfil not in PERFIS_ACESSO:
            return jsonify({'success': False, 'message': 'Perfil inválido'}), 400
        
        # Verificar se email já existe
        if db.usuarios.find_one({'email': email}):
            return jsonify({'success': False, 'message': 'Email já cadastrado'}), 409
        
        # Criar novo usuário
        novo_usuario = {
            'email': email,
            'senha': generate_password_hash(senha),
            'nome': nome,
            'perfil': perfil,
            'data_criacao': datetime.now(),
            'ativo': True
        }
        
        result = db.usuarios.insert_one(novo_usuario)
        
        logger.info(f"✅ Novo usuário registrado: {email}")
        return jsonify({
            'success': True,
            'message': 'Usuário registrado com sucesso',
            'user_id': str(result.inserted_id)
        })
    except Exception as e:
        logger.error(f"❌ Erro no registro: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    """Logout de usuário"""
    email = session.get('user_email', 'Desconhecido')
    session.clear()
    logger.info(f"✅ Logout realizado: {email}")
    return jsonify({'success': True, 'message': 'Logout realizado com sucesso'})

@app.route('/api/check-session', methods=['GET'])
def check_session():
    """Verifica sessão ativa"""
    if 'user_id' in session:
        try:
            usuario = db.usuarios.find_one({'_id': ObjectId(session['user_id'])})
            if usuario and usuario.get('ativo', True):
                return jsonify({
                    'success': True,
                    'authenticated': True,
                    'user': {
                        'id': str(usuario['_id']),
                        'nome': usuario.get('nome', 'Usuário'),
                        'email': usuario['email'],
                        'perfil': usuario.get('perfil', 'profissional'),
                        'perfil_nome': PERFIS_ACESSO.get(usuario.get('perfil', 'profissional'), {}).get('nome', 'Profissional')
                    }
                })
        except:
            pass
    
    return jsonify({'success': False, 'authenticated': False})

# ==================== PERFIL ROUTES ====================
@app.route('/api/perfil', methods=['GET'])
@login_required
def get_perfil():
    """Obtém dados do perfil do usuário"""
    try:
        usuario = db.usuarios.find_one({'_id': ObjectId(session['user_id'])})
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        perfil_info = {
            'id': str(usuario['_id']),
            'nome': usuario.get('nome', ''),
            'email': usuario['email'],
            'perfil': usuario.get('perfil', 'profissional'),
            'perfil_nome': PERFIS_ACESSO.get(usuario.get('perfil', 'profissional'), {}).get('nome', 'Profissional'),
            'perfil_descricao': PERFIS_ACESSO.get(usuario.get('perfil', 'profissional'), {}).get('descricao', ''),
            'permissoes': PERFIS_ACESSO.get(usuario.get('perfil', 'profissional'), {}).get('permissoes', []),
            'foto': usuario.get('foto', ''),
            'telefone': usuario.get('telefone', ''),
            'data_criacao': usuario.get('data_criacao', datetime.now()).strftime('%d/%m/%Y'),
            'ultimo_acesso': usuario.get('ultimo_acesso', datetime.now()).strftime('%d/%m/%Y %H:%M')
        }
        
        return jsonify({'success': True, 'perfil': perfil_info})
    except Exception as e:
        logger.error(f"❌ Erro ao buscar perfil: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/perfil', methods=['PUT'])
@login_required
def update_perfil():
    """Atualiza dados do perfil"""
    try:
        data = request.get_json()
        usuario_id = ObjectId(session['user_id'])
        
        update_data = {}
        if 'nome' in data:
            update_data['nome'] = data['nome'].strip()
        if 'telefone' in data:
            update_data['telefone'] = data['telefone'].strip()
        if 'senha_atual' in data and 'senha_nova' in data:
            # Verificar senha atual
            usuario = db.usuarios.find_one({'_id': usuario_id})
            if not check_password_hash(usuario['senha'], data['senha_atual']):
                return jsonify({'success': False, 'message': 'Senha atual incorreta'}), 400
            update_data['senha'] = generate_password_hash(data['senha_nova'])
        
        if update_data:
            db.usuarios.update_one(
                {'_id': usuario_id},
                {'$set': update_data}
            )
            logger.info(f"✅ Perfil atualizado: {session['user_email']}")
            return jsonify({'success': True, 'message': 'Perfil atualizado com sucesso'})
        
        return jsonify({'success': False, 'message': 'Nenhum dado para atualizar'}), 400
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar perfil: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/perfil/foto', methods=['POST'])
@login_required
def upload_foto_perfil():
    """Upload de foto de perfil"""
    try:
        if 'foto' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['foto']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Tipo de arquivo não permitido'}), 400
        
        # Processar imagem
        imagem_processada = processar_imagem(file, max_size=(400, 400))
        if not imagem_processada:
            return jsonify({'success': False, 'message': 'Erro ao processar imagem'}), 500
        
        # Converter para base64
        foto_base64 = base64.b64encode(imagem_processada.getvalue()).decode('utf-8')
        foto_data_uri = f"data:image/jpeg;base64,{foto_base64}"
        
        # Salvar no banco
        db.usuarios.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': {'foto': foto_data_uri}}
        )
        
        logger.info(f"✅ Foto de perfil atualizada: {session['user_email']}")
        return jsonify({
            'success': True,
            'message': 'Foto atualizada com sucesso',
            'foto': foto_data_uri
        })
    except Exception as e:
        logger.error(f"❌ Erro ao fazer upload da foto: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/perfis-disponiveis', methods=['GET'])
@login_required
def get_perfis_disponiveis():
    """Lista perfis de acesso disponíveis"""
    try:
        perfis = []
        for key, value in PERFIS_ACESSO.items():
            perfis.append({
                'id': key,
                'nome': value['nome'],
                'descricao': value['descricao'],
                'permissoes': value['permissoes'] if value['permissoes'] != ['*'] else ['Acesso Total']
            })
        
        return jsonify({'success': True, 'perfis': perfis})
    except Exception as e:
        logger.error(f"❌ Erro ao listar perfis: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
# ==================== CLIENTES ROUTES ====================

@app.route('/api/clientes', methods=['GET'])
@login_required
def get_clientes():
    """Lista todos os clientes com filtros e paginação"""
    try:
        # Parâmetros de busca e filtro
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')
        
        # Montar query
        query = {}
        if search:
            query['$or'] = [
                {'nome': {'$regex': search, '$options': 'i'}},
                {'telefone': {'$regex': search, '$options': 'i'}},
                {'email': {'$regex': search, '$options': 'i'}}
            ]
        
        if status:
            query['status'] = status
        
        # Cache key
        cache_key = f"clientes_{page}_{limit}_{search}_{status}"
        cached_data = get_from_cache(cache_key)
        if cached_data:
            return jsonify(cached_data)
        
        # Contar total
        total = db.clientes.count_documents(query)
        
        # Buscar clientes
        skip = (page - 1) * limit
        clientes = list(db.clientes.find(query).sort('nome', ASCENDING).skip(skip).limit(limit))
        
        # Formatar dados
        clientes_formatados = []
        for c in clientes:
            # Calcular total faturado
            orcamentos_aprovados = db.orcamentos.find({
                'cliente_id': str(c['_id']),
                'status': 'Aprovado'
            })
            total_faturado = sum([float(o.get('total', 0)) for o in orcamentos_aprovados])
            
            # Contar visitas
            total_visitas = db.agendamentos.count_documents({
                'cliente_id': str(c['_id']),
                'status': 'Concluído'
            })
            
            # Último atendimento
            ultimo_atendimento = db.agendamentos.find_one(
                {'cliente_id': str(c['_id']), 'status': 'Concluído'},
                sort=[('data', DESCENDING)]
            )
            
            cliente_info = {
                'id': str(c['_id']),
                'nome': c.get('nome', ''),
                'telefone': c.get('telefone', ''),
                'email': c.get('email', ''),
                'data_nascimento': c.get('data_nascimento', ''),
                'sexo': c.get('sexo', ''),
                'endereco': c.get('endereco', {}),
                'status': c.get('status', 'Ativo'),
                'como_conheceu': c.get('como_conheceu', ''),
                'data_cadastro': c.get('data_cadastro', datetime.now()).strftime('%d/%m/%Y'),
                'total_faturado': round(total_faturado, 2),
                'total_visitas': total_visitas,
                'ultimo_atendimento': ultimo_atendimento['data'].strftime('%d/%m/%Y') if ultimo_atendimento else 'Nunca',
                'observacoes': c.get('observacoes', ''),
                'anamnese': c.get('anamnese', {})
            }
            clientes_formatados.append(cliente_info)
        
        response = {
            'success': True,
            'data': clientes_formatados,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }
        
        # Salvar no cache
        set_in_cache(cache_key, response)
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"❌ Erro ao buscar clientes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clientes/<cliente_id>', methods=['GET'])
@login_required
def get_cliente(cliente_id):
    """Obtém detalhes de um cliente específico"""
    try:
        cliente = db.clientes.find_one({'_id': ObjectId(cliente_id)})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
        
        # Histórico de atendimentos
        atendimentos = list(db.agendamentos.find({
            'cliente_id': cliente_id,
            'status': 'Concluído'
        }).sort('data', DESCENDING).limit(10))
        
        atendimentos_formatados = []
        for a in atendimentos:
            profissional = db.profissionais.find_one({'_id': ObjectId(a['profissional_id'])})
            servico = db.servicos.find_one({'_id': ObjectId(a['servico_id'])})
            
            atendimentos_formatados.append({
                'data': a['data'].strftime('%d/%m/%Y %H:%M'),
                'profissional': profissional.get('nome', 'Desconhecido') if profissional else 'Desconhecido',
                'servico': servico.get('nome', 'Desconhecido') if servico else 'Desconhecido',
                'valor': float(a.get('valor', 0))
            })
        
        # Orçamentos do cliente
        orcamentos = list(db.orcamentos.find({
            'cliente_id': cliente_id
        }).sort('data_criacao', DESCENDING).limit(5))
        
        orcamentos_formatados = []
        for o in orcamentos:
            orcamentos_formatados.append({
                'numero': o.get('numero', ''),
                'data': o.get('data_criacao', datetime.now()).strftime('%d/%m/%Y'),
                'total': float(o.get('total', 0)),
                'status': o.get('status', 'Pendente')
            })
        
        # Produtos e serviços mais utilizados
        pipeline_servicos = [
            {'$match': {'cliente_id': cliente_id, 'status': 'Concluído'}},
            {'$group': {
                '_id': '$servico_id',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ]
        servicos_mais_usados = list(db.agendamentos.aggregate(pipeline_servicos))
        servicos_info = []
        for s in servicos_mais_usados:
            servico = db.servicos.find_one({'_id': ObjectId(s['_id'])})
            if servico:
                servicos_info.append({
                    'nome': servico.get('nome', 'Desconhecido'),
                    'quantidade': s['count']
                })
        
        cliente_detalhado = {
            'id': str(cliente['_id']),
            'nome': cliente.get('nome', ''),
            'telefone': cliente.get('telefone', ''),
            'email': cliente.get('email', ''),
            'data_nascimento': cliente.get('data_nascimento', ''),
            'sexo': cliente.get('sexo', ''),
            'endereco': cliente.get('endereco', {}),
            'status': cliente.get('status', 'Ativo'),
            'como_conheceu': cliente.get('como_conheceu', ''),
            'data_cadastro': cliente.get('data_cadastro', datetime.now()).strftime('%d/%m/%Y'),
            'observacoes': cliente.get('observacoes', ''),
            'anamnese': cliente.get('anamnese', {}),
            'foto': cliente.get('foto', ''),
            'historico_atendimentos': atendimentos_formatados,
            'orcamentos': orcamentos_formatados,
            'servicos_preferidos': servicos_info,
            'link_whatsapp': gerar_link_whatsapp(cliente.get('telefone', ''), f"Olá {cliente.get('nome', '')}! Equipe BIOMA Uberaba.")
        }
        
        return jsonify({'success': True, 'cliente': cliente_detalhado})
    except Exception as e:
        logger.error(f"❌ Erro ao buscar cliente: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clientes', methods=['POST'])
@login_required
@verificar_permissao('gerenciar_clientes')
def create_cliente():
    """Cria novo cliente"""
    try:
        data = request.get_json()
        
        # Validações
        if not data.get('nome'):
            return jsonify({'success': False, 'message': 'Nome é obrigatório'}), 400
        
        if not data.get('telefone'):
            return jsonify({'success': False, 'message': 'Telefone é obrigatório'}), 400
        
        # Verificar se telefone já existe
        if db.clientes.find_one({'telefone': data['telefone']}):
            return jsonify({'success': False, 'message': 'Telefone já cadastrado'}), 409
        
        novo_cliente = {
            'nome': data['nome'].strip(),
            'telefone': data['telefone'].strip(),
            'email': data.get('email', '').strip(),
            'data_nascimento': data.get('data_nascimento', ''),
            'sexo': data.get('sexo', ''),
            'endereco': {
                'rua': data.get('endereco_rua', ''),
                'numero': data.get('endereco_numero', ''),
                'complemento': data.get('endereco_complemento', ''),
                'bairro': data.get('endereco_bairro', ''),
                'cidade': data.get('endereco_cidade', ''),
                'estado': data.get('endereco_estado', ''),
                'cep': data.get('endereco_cep', '')
            },
            'status': 'Ativo',
            'como_conheceu': data.get('como_conheceu', ''),
            'observacoes': data.get('observacoes', ''),
            'anamnese': data.get('anamnese', {}),
            'data_cadastro': datetime.now(),
            'criado_por': session['user_id']
        }
        
        result = db.clientes.insert_one(novo_cliente)
        
        logger.info(f"✅ Cliente criado: {data['nome']}")
        return jsonify({
            'success': True,
            'message': 'Cliente criado com sucesso',
            'cliente_id': str(result.inserted_id)
        })
    except Exception as e:
        logger.error(f"❌ Erro ao criar cliente: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clientes/<cliente_id>', methods=['PUT'])
@login_required
@verificar_permissao('gerenciar_clientes')
def update_cliente(cliente_id):
    """Atualiza dados do cliente"""
    try:
        data = request.get_json()
        
        update_data = {}
        if 'nome' in data:
            update_data['nome'] = data['nome'].strip()
        if 'telefone' in data:
            # Verificar se telefone já existe em outro cliente
            existing = db.clientes.find_one({
                'telefone': data['telefone'],
                '_id': {'$ne': ObjectId(cliente_id)}
            })
            if existing:
                return jsonify({'success': False, 'message': 'Telefone já cadastrado'}), 409
            update_data['telefone'] = data['telefone'].strip()
        if 'email' in data:
            update_data['email'] = data['email'].strip()
        if 'data_nascimento' in data:
            update_data['data_nascimento'] = data['data_nascimento']
        if 'sexo' in data:
            update_data['sexo'] = data['sexo']
        if 'status' in data:
            update_data['status'] = data['status']
        if 'como_conheceu' in data:
            update_data['como_conheceu'] = data['como_conheceu']
        if 'observacoes' in data:
            update_data['observacoes'] = data['observacoes']
        if 'anamnese' in data:
            update_data['anamnese'] = data['anamnese']
        
        # Atualizar endereço
        if any(key.startswith('endereco_') for key in data.keys()):
            endereco = {}
            if 'endereco_rua' in data:
                endereco['rua'] = data['endereco_rua']
            if 'endereco_numero' in data:
                endereco['numero'] = data['endereco_numero']
            if 'endereco_complemento' in data:
                endereco['complemento'] = data['endereco_complemento']
            if 'endereco_bairro' in data:
                endereco['bairro'] = data['endereco_bairro']
            if 'endereco_cidade' in data:
                endereco['cidade'] = data['endereco_cidade']
            if 'endereco_estado' in data:
                endereco['estado'] = data['endereco_estado']
            if 'endereco_cep' in data:
                endereco['cep'] = data['endereco_cep']
            if endereco:
                update_data['endereco'] = endereco
        
        if update_data:
            update_data['atualizado_em'] = datetime.now()
            update_data['atualizado_por'] = session['user_id']
            
            db.clientes.update_one(
                {'_id': ObjectId(cliente_id)},
                {'$set': update_data}
            )
            
            logger.info(f"✅ Cliente atualizado: {cliente_id}")
            return jsonify({'success': True, 'message': 'Cliente atualizado com sucesso'})
        
        return jsonify({'success': False, 'message': 'Nenhum dado para atualizar'}), 400
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar cliente: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clientes/<cliente_id>', methods=['DELETE'])
@login_required
@verificar_permissao('gerenciar_clientes')
def delete_cliente(cliente_id):
    """Deleta (inativa) um cliente"""
    try:
        # Ao invés de deletar, apenas inativa
        db.clientes.update_one(
            {'_id': ObjectId(cliente_id)},
            {'$set': {
                'status': 'Inativo',
                'inativado_em': datetime.now(),
                'inativado_por': session['user_id']
            }}
        )
        
        logger.info(f"✅ Cliente inativado: {cliente_id}")
        return jsonify({'success': True, 'message': 'Cliente inativado com sucesso'})
    except Exception as e:
        logger.error(f"❌ Erro ao inativar cliente: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clientes/<cliente_id>/foto', methods=['POST'])
@login_required
@verificar_permissao('gerenciar_clientes')
def upload_foto_cliente(cliente_id):
    """Upload de foto do cliente"""
    try:
        if 'foto' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['foto']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Tipo de arquivo não permitido'}), 400
        
        # Processar imagem
        imagem_processada = processar_imagem(file, max_size=(600, 600))
        if not imagem_processada:
            return jsonify({'success': False, 'message': 'Erro ao processar imagem'}), 500
        
        # Converter para base64
        foto_base64 = base64.b64encode(imagem_processada.getvalue()).decode('utf-8')
        foto_data_uri = f"data:image/jpeg;base64,{foto_base64}"
        
        # Salvar no banco
        db.clientes.update_one(
            {'_id': ObjectId(cliente_id)},
            {'$set': {'foto': foto_data_uri}}
        )
        
        logger.info(f"✅ Foto do cliente atualizada: {cliente_id}")
        return jsonify({
            'success': True,
            'message': 'Foto atualizada com sucesso',
            'foto': foto_data_uri
        })
    except Exception as e:
        logger.error(f"❌ Erro ao fazer upload da foto: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clientes/aniversariantes', methods=['GET'])
@login_required
def get_clientes_aniversariantes():
    """Lista clientes aniversariantes do mês"""
    try:
        mes = int(request.args.get('mes', datetime.now().month))
        
        # Buscar clientes
        clientes = list(db.clientes.find({'status': 'Ativo'}))
        
        aniversariantes = []
        for c in clientes:
            if c.get('data_nascimento'):
                try:
                    data_nasc = datetime.strptime(c['data_nascimento'], '%Y-%m-%d')
                    if data_nasc.month == mes:
                        aniversariantes.append({
                            'id': str(c['_id']),
                            'nome': c.get('nome', ''),
                            'telefone': c.get('telefone', ''),
                            'data_nascimento': c['data_nascimento'],
                            'dia': data_nasc.day,
                            'link_whatsapp': gerar_link_whatsapp(
                                c.get('telefone', ''),
                                f"🎉 Feliz Aniversário, {c.get('nome', '')}! Equipe BIOMA Uberaba deseja muitas felicidades! 🎂"
                            )
                        })
                except:
                    continue
        
        # Ordenar por dia
        aniversariantes.sort(key=lambda x: x['dia'])
        
        return jsonify({
            'success': True,
            'aniversariantes': aniversariantes,
            'total': len(aniversariantes)
        })
    except Exception as e:
        logger.error(f"❌ Erro ao buscar aniversariantes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clientes/estatisticas', methods=['GET'])
@login_required
def get_estatisticas_clientes():
    """Estatísticas de clientes"""
    try:
        # Total de clientes
        total_clientes = db.clientes.count_documents({'status': 'Ativo'})
        
        # Novos clientes no mês
        inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        novos_mes = db.clientes.count_documents({
            'status': 'Ativo',
            'data_cadastro': {'$gte': inicio_mes}
        })
        
        # Clientes inativos
        inativos = db.clientes.count_documents({'status': 'Inativo'})
        
        # Distribuição por sexo
        pipeline_sexo = [
            {'$match': {'status': 'Ativo'}},
            {'$group': {
                '_id': '$sexo',
                'count': {'$sum': 1}
            }}
        ]
        dist_sexo = list(db.clientes.aggregate(pipeline_sexo))
        
        # Distribuição por como conheceu
        pipeline_conheceu = [
            {'$match': {'status': 'Ativo', 'como_conheceu': {'$ne': ''}}},
            {'$group': {
                '_id': '$como_conheceu',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ]
        dist_conheceu = list(db.clientes.aggregate(pipeline_conheceu))
        
        # Top clientes por faturamento
        top_clientes = []
        clientes = list(db.clientes.find({'status': 'Ativo'}).limit(100))
        for c in clientes:
            orcamentos_aprovados = db.orcamentos.find({
                'cliente_id': str(c['_id']),
                'status': 'Aprovado'
            })
            total = sum([float(o.get('total', 0)) for o in orcamentos_aprovados])
            if total > 0:
                top_clientes.append({
                    'nome': c.get('nome', ''),
                    'total_faturado': round(total, 2)
                })
        
        top_clientes.sort(key=lambda x: x['total_faturado'], reverse=True)
        top_clientes = top_clientes[:10]
        
        return jsonify({
            'success': True,
            'estatisticas': {
                'total_clientes': total_clientes,
                'novos_mes': novos_mes,
                'inativos': inativos,
                'distribuicao_sexo': dist_sexo,
                'distribuicao_conheceu': dist_conheceu,
                'top_clientes': top_clientes
            }
        })
    except Exception as e:
        logger.error(f"❌ Erro ao buscar estatísticas: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
# ==================== PROFISSIONAIS ROUTES ====================

@app.route('/api/profissionais', methods=['GET'])
@login_required
def get_profissionais():
    """Lista todos os profissionais com filtros"""
    try:
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')
        equipe = request.args.get('equipe', '')
        
        # Montar query
        query = {}
        if search:
            query['$or'] = [
                {'nome': {'$regex': search, '$options': 'i'}},
                {'telefone': {'$regex': search, '$options': 'i'}},
                {'especialidade': {'$regex': search, '$options': 'i'}}
            ]
        
        if status:
            query['status'] = status
        if equipe:
            query['equipe'] = equipe
        
        # Buscar profissionais
        profissionais = list(db.profissionais.find(query).sort('nome', ASCENDING))
        
        profissionais_formatados = []
        for p in profissionais:
            # Estatísticas do profissional
            total_atendimentos = db.agendamentos.count_documents({
                'profissional_id': str(p['_id']),
                'status': 'Concluído'
            })
            
            # Comissões do mês atual
            inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0)
            comissoes_mes = list(db.comissoes.find({
                'profissional_id': str(p['_id']),
                'data': {'$gte': inicio_mes}
            }))
            total_comissoes = sum([float(c.get('valor', 0)) for c in comissoes_mes])
            
            prof_info = {
                'id': str(p['_id']),
                'nome': p.get('nome', ''),
                'telefone': p.get('telefone', ''),
                'email': p.get('email', ''),
                'especialidade': p.get('especialidade', ''),
                'equipe': p.get('equipe', ''),
                'status': p.get('status', 'Ativo'),
                'foto': p.get('foto', ''),
                'comissao_percentual': float(p.get('comissao_percentual', 0)),
                'data_cadastro': p.get('data_cadastro', datetime.now()).strftime('%d/%m/%Y'),
                'total_atendimentos': total_atendimentos,
                'comissoes_mes': round(total_comissoes, 2),
                'horario_trabalho': p.get('horario_trabalho', {}),
                'dias_trabalho': p.get('dias_trabalho', [])
            }
            profissionais_formatados.append(prof_info)
        
        return jsonify({
            'success': True,
            'profissionais': profissionais_formatados,
            'total': len(profissionais_formatados)
        })
    except Exception as e:
        logger.error(f"❌ Erro ao buscar profissionais: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profissionais/<profissional_id>', methods=['GET'])
@login_required
def get_profissional(profissional_id):
    """Obtém detalhes de um profissional específico"""
    try:
        profissional = db.profissionais.find_one({'_id': ObjectId(profissional_id)})
        if not profissional:
            return jsonify({'success': False, 'message': 'Profissional não encontrado'}), 404
        
        # Estatísticas detalhadas
        total_atendimentos = db.agendamentos.count_documents({
            'profissional_id': profissional_id,
            'status': 'Concluído'
        })
        
        # Atendimentos por mês (últimos 6 meses)
        meses = []
        for i in range(5, -1, -1):
            data_ref = datetime.now() - timedelta(days=30*i)
            inicio = data_ref.replace(day=1, hour=0, minute=0, second=0)
            if i > 0:
                fim = (data_ref.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            else:
                fim = datetime.now()
            
            count = db.agendamentos.count_documents({
                'profissional_id': profissional_id,
                'status': 'Concluído',
                'data': {'$gte': inicio, '$lte': fim}
            })
            
            meses.append({
                'mes': inicio.strftime('%b/%y'),
                'atendimentos': count
            })
        
        # Comissões dos últimos 12 meses
        comissoes_12m = []
        total_comissoes_12m = 0
        for i in range(11, -1, -1):
            data_ref = datetime.now() - timedelta(days=30*i)
            inicio = data_ref.replace(day=1, hour=0, minute=0, second=0)
            if i > 0:
                fim = (data_ref.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            else:
                fim = datetime.now()
            
            comissoes = list(db.comissoes.find({
                'profissional_id': profissional_id,
                'data': {'$gte': inicio, '$lte': fim}
            }))
            
            total_mes = sum([float(c.get('valor', 0)) for c in comissoes])
            total_comissoes_12m += total_mes
            
            comissoes_12m.append({
                'mes': inicio.strftime('%b/%y'),
                'valor': round(total_mes, 2)
            })
        
        # Serviços mais realizados
        pipeline_servicos = [
            {'$match': {
                'profissional_id': profissional_id,
                'status': 'Concluído'
            }},
            {'$group': {
                '_id': '$servico_id',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ]
        servicos_top = list(db.agendamentos.aggregate(pipeline_servicos))
        servicos_info = []
        for s in servicos_top:
            servico = db.servicos.find_one({'_id': ObjectId(s['_id'])})
            if servico:
                servicos_info.append({
                    'nome': servico.get('nome', 'Desconhecido'),
                    'quantidade': s['count']
                })
        
        # Avaliação média
        avaliacoes = list(db.avaliacoes.find({'profissional_id': profissional_id}))
        if avaliacoes:
            media_avaliacao = sum([a.get('nota', 0) for a in avaliacoes]) / len(avaliacoes)
        else:
            media_avaliacao = 0
        
        profissional_detalhado = {
            'id': str(profissional['_id']),
            'nome': profissional.get('nome', ''),
            'telefone': profissional.get('telefone', ''),
            'email': profissional.get('email', ''),
            'especialidade': profissional.get('especialidade', ''),
            'equipe': profissional.get('equipe', ''),
            'status': profissional.get('status', 'Ativo'),
            'foto': profissional.get('foto', ''),
            'comissao_percentual': float(profissional.get('comissao_percentual', 0)),
            'data_cadastro': profissional.get('data_cadastro', datetime.now()).strftime('%d/%m/%Y'),
            'horario_trabalho': profissional.get('horario_trabalho', {}),
            'dias_trabalho': profissional.get('dias_trabalho', []),
            'observacoes': profissional.get('observacoes', ''),
            'estatisticas': {
                'total_atendimentos': total_atendimentos,
                'atendimentos_6m': meses,
                'comissoes_12m': comissoes_12m,
                'total_comissoes_12m': round(total_comissoes_12m, 2),
                'servicos_top': servicos_info,
                'avaliacao_media': round(media_avaliacao, 1),
                'total_avaliacoes': len(avaliacoes)
            }
        }
        
        return jsonify({'success': True, 'profissional': profissional_detalhado})
    except Exception as e:
        logger.error(f"❌ Erro ao buscar profissional: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profissionais', methods=['POST'])
@login_required
@verificar_permissao('gerenciar_profissionais')
def create_profissional():
    """Cria novo profissional"""
    try:
        data = request.get_json()
        
        if not data.get('nome'):
            return jsonify({'success': False, 'message': 'Nome é obrigatório'}), 400
        
        if not data.get('telefone'):
            return jsonify({'success': False, 'message': 'Telefone é obrigatório'}), 400
        
        # Verificar se telefone já existe
        if db.profissionais.find_one({'telefone': data['telefone']}):
            return jsonify({'success': False, 'message': 'Telefone já cadastrado'}), 409
        
        novo_profissional = {
            'nome': data['nome'].strip(),
            'telefone': data['telefone'].strip(),
            'email': data.get('email', '').strip(),
            'especialidade': data.get('especialidade', ''),
            'equipe': data.get('equipe', ''),
            'status': 'Ativo',
            'comissao_percentual': float(data.get('comissao_percentual', 10)),
            'horario_trabalho': data.get('horario_trabalho', {
                'inicio': '09:00',
                'fim': '18:00'
            }),
            'dias_trabalho': data.get('dias_trabalho', ['seg', 'ter', 'qua', 'qui', 'sex']),
            'observacoes': data.get('observacoes', ''),
            'data_cadastro': datetime.now(),
            'criado_por': session['user_id']
        }
        
        result = db.profissionais.insert_one(novo_profissional)
        
        logger.info(f"✅ Profissional criado: {data['nome']}")
        return jsonify({
            'success': True,
            'message': 'Profissional criado com sucesso',
            'profissional_id': str(result.inserted_id)
        })
    except Exception as e:
        logger.error(f"❌ Erro ao criar profissional: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profissionais/<profissional_id>', methods=['PUT'])
@login_required
@verificar_permissao('gerenciar_profissionais')
def update_profissional(profissional_id):
    """Atualiza dados do profissional"""
    try:
        data = request.get_json()
        
        update_data = {}
        campos_permitidos = [
            'nome', 'telefone', 'email', 'especialidade', 'equipe',
            'status', 'comissao_percentual', 'horario_trabalho',
            'dias_trabalho', 'observacoes'
        ]
        
        for campo in campos_permitidos:
            if campo in data:
                if campo == 'comissao_percentual':
                    update_data[campo] = float(data[campo])
                else:
                    update_data[campo] = data[campo]
        
        if 'telefone' in update_data:
            # Verificar se telefone já existe em outro profissional
            existing = db.profissionais.find_one({
                'telefone': update_data['telefone'],
                '_id': {'$ne': ObjectId(profissional_id)}
            })
            if existing:
                return jsonify({'success': False, 'message': 'Telefone já cadastrado'}), 409
        
        if update_data:
            update_data['atualizado_em'] = datetime.now()
            update_data['atualizado_por'] = session['user_id']
            
            db.profissionais.update_one(
                {'_id': ObjectId(profissional_id)},
                {'$set': update_data}
            )
            
            logger.info(f"✅ Profissional atualizado: {profissional_id}")
            return jsonify({'success': True, 'message': 'Profissional atualizado com sucesso'})
        
        return jsonify({'success': False, 'message': 'Nenhum dado para atualizar'}), 400
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar profissional: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profissionais/<profissional_id>', methods=['DELETE'])
@login_required
@verificar_permissao('gerenciar_profissionais')
def delete_profissional(profissional_id):
    """Deleta (inativa) um profissional"""
    try:
        db.profissionais.update_one(
            {'_id': ObjectId(profissional_id)},
            {'$set': {
                'status': 'Inativo',
                'inativado_em': datetime.now(),
                'inativado_por': session['user_id']
            }}
        )
        
        logger.info(f"✅ Profissional inativado: {profissional_id}")
        return jsonify({'success': True, 'message': 'Profissional inativado com sucesso'})
    except Exception as e:
        logger.error(f"❌ Erro ao inativar profissional: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profissionais/<profissional_id>/foto', methods=['POST'])
@login_required
@verificar_permissao('gerenciar_profissionais')
def upload_foto_profissional(profissional_id):
    """Upload de foto do profissional"""
    try:
        if 'foto' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['foto']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Tipo de arquivo não permitido'}), 400
        
        # Processar imagem - formato circular/perfil
        imagem_processada = processar_imagem(file, max_size=(400, 400))
        if not imagem_processada:
            return jsonify({'success': False, 'message': 'Erro ao processar imagem'}), 500
        
        # Converter para base64
        foto_base64 = base64.b64encode(imagem_processada.getvalue()).decode('utf-8')
        foto_data_uri = f"data:image/jpeg;base64,{foto_base64}"
        
        # Salvar no banco
        db.profissionais.update_one(
            {'_id': ObjectId(profissional_id)},
            {'$set': {
                'foto': foto_data_uri,
                'foto_atualizada_em': datetime.now()
            }}
        )
        
        logger.info(f"✅ Foto do profissional atualizada: {profissional_id}")
        return jsonify({
            'success': True,
            'message': 'Foto atualizada com sucesso',
            'foto': foto_data_uri
        })
    except Exception as e:
        logger.error(f"❌ Erro ao fazer upload da foto: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profissionais/estatisticas', methods=['GET'])
@login_required
def get_estatisticas_profissionais():
    """Estatísticas gerais dos profissionais"""
    try:
        # Total de profissionais ativos
        total_ativos = db.profissionais.count_documents({'status': 'Ativo'})
        
        # Ranking de atendimentos (mês atual)
        inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        
        profissionais = list(db.profissionais.find({'status': 'Ativo'}))
        ranking = []
        
        for p in profissionais:
            total_atendimentos = db.agendamentos.count_documents({
                'profissional_id': str(p['_id']),
                'status': 'Concluído',
                'data': {'$gte': inicio_mes}
            })
            
            comissoes = list(db.comissoes.find({
                'profissional_id': str(p['_id']),
                'data': {'$gte': inicio_mes}
            }))
            total_comissoes = sum([float(c.get('valor', 0)) for c in comissoes])
            
            if total_atendimentos > 0:
                ranking.append({
                    'nome': p.get('nome', ''),
                    'foto': p.get('foto', ''),
                    'atendimentos': total_atendimentos,
                    'comissoes': round(total_comissoes, 2)
                })
        
        # Ordenar por atendimentos
        ranking.sort(key=lambda x: x['atendimentos'], reverse=True)
        
        return jsonify({
            'success': True,
            'estatisticas': {
                'total_ativos': total_ativos,
                'ranking_mes': ranking[:10]
            }
        })
    except Exception as e:
        logger.error(f"❌ Erro ao buscar estatísticas: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/equipes', methods=['GET'])
@login_required
def get_equipes():
    """Lista todas as equipes disponíveis"""
    try:
        equipes = db.profissionais.distinct('equipe', {'equipe': {'$ne': ''}})
        return jsonify({
            'success': True,
            'equipes': sorted(equipes)
        })
    except Exception as e:
        logger.error(f"❌ Erro ao buscar equipes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
# ==================== SERVIÇOS ROUTES ====================

@app.route('/api/servicos', methods=['GET'])
@login_required
def get_servicos():
    """Lista todos os serviços"""
    try:
        search = request.args.get('search', '').strip()
        status = request.args.get('status', 'Ativo')
        categoria = request.args.get('categoria', '')
        
        query = {'status': status} if status else {}
        
        if search:
            query['nome'] = {'$regex': search, '$options': 'i'}
        
        if categoria:
            query['categoria'] = categoria
        
        servicos = list(db.servicos.find(query).sort('nome', ASCENDING))
        
        servicos_formatados = []
        for s in servicos:
            # Contar quantas vezes foi realizado
            total_realizacoes = db.agendamentos.count_documents({
                'servico_id': str(s['_id']),
                'status': 'Concluído'
            })
            
            servicos_formatados.append({
                'id': str(s['_id']),
                'nome': s.get('nome', ''),
                'descricao': s.get('descricao', ''),
                'categoria': s.get('categoria', ''),
                'preco': float(s.get('preco', 0)),
                'duracao': int(s.get('duracao', 60)),
                'status': s.get('status', 'Ativo'),
                'total_realizacoes': total_realizacoes
            })
        
        return jsonify({
            'success': True,
            'servicos': servicos_formatados,
            'total': len(servicos_formatados)
        })
    except Exception as e:
        logger.error(f"❌ Erro ao buscar serviços: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/servicos/<servico_id>', methods=['GET'])
@login_required
def get_servico(servico_id):
    """Obtém detalhes de um serviço"""
    try:
        servico = db.servicos.find_one({'_id': ObjectId(servico_id)})
        if not servico:
            return jsonify({'success': False, 'message': 'Serviço não encontrado'}), 404
        
        # Estatísticas
        total_realizacoes = db.agendamentos.count_documents({
            'servico_id': servico_id,
            'status': 'Concluído'
        })
        
        # Profissionais que realizam este serviço
        agendamentos = list(db.agendamentos.find({
            'servico_id': servico_id,
            'status': 'Concluído'
        }).limit(100))
        
        profissionais_ids = list(set([a['profissional_id'] for a in agendamentos]))
        profissionais = []
        for prof_id in profissionais_ids:
            prof = db.profissionais.find_one({'_id': ObjectId(prof_id)})
            if prof:
                count = len([a for a in agendamentos if a['profissional_id'] == prof_id])
                profissionais.append({
                    'nome': prof.get('nome', ''),
                    'foto': prof.get('foto', ''),
                    'quantidade': count
                })
        
        profissionais.sort(key=lambda x: x['quantidade'], reverse=True)
        
        servico_detalhado = {
            'id': str(servico['_id']),
            'nome': servico.get('nome', ''),
            'descricao': servico.get('descricao', ''),
            'categoria': servico.get('categoria', ''),
            'preco': float(servico.get('preco', 0)),
            'duracao': int(servico.get('duracao', 60)),
            'status': servico.get('status', 'Ativo'),
            'total_realizacoes': total_realizacoes,
            'profissionais': profissionais[:5]
        }
        
        return jsonify({'success': True, 'servico': servico_detalhado})
    except Exception as e:
        logger.error(f"❌ Erro ao buscar serviço: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/servicos', methods=['POST'])
@login_required
@verificar_permissao('gerenciar_servicos')
def create_servico():
    """Cria novo serviço"""
    try:
        data = request.get_json()
        
        if not data.get('nome'):
            return jsonify({'success': False, 'message': 'Nome é obrigatório'}), 400
        
        if not data.get('preco'):
            return jsonify({'success': False, 'message': 'Preço é obrigatório'}), 400
        
        novo_servico = {
            'nome': data['nome'].strip(),
            'descricao': data.get('descricao', ''),
            'categoria': data.get('categoria', ''),
            'preco': float(data['preco']),
            'duracao': int(data.get('duracao', 60)),
            'status': 'Ativo',
            'data_cadastro': datetime.now(),
            'criado_por': session['user_id']
        }
        
        result = db.servicos.insert_one(novo_servico)
        
        logger.info(f"✅ Serviço criado: {data['nome']}")
        return jsonify({
            'success': True,
            'message': 'Serviço criado com sucesso',
            'servico_id': str(result.inserted_id)
        })
    except Exception as e:
        logger.error(f"❌ Erro ao criar serviço: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/servicos/<servico_id>', methods=['PUT'])
@login_required
@verificar_permissao('gerenciar_servicos')
def update_servico(servico_id):
    """Atualiza serviço"""
    try:
        data = request.get_json()
        
        update_data = {}
        if 'nome' in data:
            update_data['nome'] = data['nome'].strip()
        if 'descricao' in data:
            update_data['descricao'] = data['descricao']
        if 'categoria' in data:
            update_data['categoria'] = data['categoria']
        if 'preco' in data:
            update_data['preco'] = float(data['preco'])
        if 'duracao' in data:
            update_data['duracao'] = int(data['duracao'])
        if 'status' in data:
            update_data['status'] = data['status']
        
        if update_data:
            update_data['atualizado_em'] = datetime.now()
            db.servicos.update_one(
                {'_id': ObjectId(servico_id)},
                {'$set': update_data}
            )
            
            logger.info(f"✅ Serviço atualizado: {servico_id}")
            return jsonify({'success': True, 'message': 'Serviço atualizado com sucesso'})
        
        return jsonify({'success': False, 'message': 'Nenhum dado para atualizar'}), 400
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar serviço: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/servicos/<servico_id>', methods=['DELETE'])
@login_required
@verificar_permissao('gerenciar_servicos')
def delete_servico(servico_id):
    """Deleta (inativa) um serviço"""
    try:
        db.servicos.update_one(
            {'_id': ObjectId(servico_id)},
            {'$set': {'status': 'Inativo', 'inativado_em': datetime.now()}}
        )
        
        logger.info(f"✅ Serviço inativado: {servico_id}")
        return jsonify({'success': True, 'message': 'Serviço inativado com sucesso'})
    except Exception as e:
        logger.error(f"❌ Erro ao inativar serviço: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/categorias-servicos', methods=['GET'])
@login_required
def get_categorias_servicos():
    """Lista categorias de serviços"""
    try:
        categorias = db.servicos.distinct('categoria', {'categoria': {'$ne': ''}})
        return jsonify({
            'success': True,
            'categorias': sorted(categorias)
        })
    except Exception as e:
        logger.error(f"❌ Erro ao buscar categorias: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== PRODUTOS ROUTES ====================

@app.route('/api/produtos', methods=['GET'])
@login_required
def get_produtos():
    """Lista todos os produtos"""
    try:
        search = request.args.get('search', '').strip()
        status = request.args.get('status', 'Ativo')
        marca = request.args.get('marca', '')
        
        query = {'status': status} if status else {}
        
        if search:
            query['$or'] = [
                {'nome': {'$regex': search, '$options': 'i'}},
                {'marca': {'$regex': search, '$options': 'i'}}
            ]
        
        if marca:
            query['marca'] = marca
        
        produtos = list(db.produtos.find(query).sort('nome', ASCENDING))
        
        produtos_formatados = []
        for p in produtos:
            # Status do estoque
            estoque_atual = int(p.get('estoque', 0))
            estoque_minimo = int(p.get('estoque_minimo', 0))
            
            if estoque_atual <= estoque_minimo:
                status_estoque = 'Crítico'
            elif estoque_atual < estoque_minimo * 1.5:
                status_estoque = 'Baixo'
            else:
                status_estoque = 'Normal'
            
            produtos_formatados.append({
                'id': str(p['_id']),
                'nome': p.get('nome', ''),
                'descricao': p.get('descricao', ''),
                'marca': p.get('marca', ''),
                'preco': float(p.get('preco', 0)),
                'estoque': estoque_atual,
                'estoque_minimo': estoque_minimo,
                'status_estoque': status_estoque,
                'status': p.get('status', 'Ativo'),
                'unidade': p.get('unidade', 'un')
            })
        
        return jsonify({
            'success': True,
            'produtos': produtos_formatados,
            'total': len(produtos_formatados)
        })
    except Exception as e:
        logger.error(f"❌ Erro ao buscar produtos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/produtos/<produto_id>', methods=['GET'])
@login_required
def get_produto(produto_id):
    """Obtém detalhes de um produto"""
    try:
        produto = db.produtos.find_one({'_id': ObjectId(produto_id)})
        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
        
        # Histórico de movimentações (últimas 20)
        movimentacoes = list(db.estoque_movimentacoes.find({
            'produto_id': produto_id
        }).sort('data', DESCENDING).limit(20))
        
        movimentacoes_formatadas = []
        for m in movimentacoes:
            responsavel_nome = 'Sistema'
            if m.get('responsavel_id'):
                responsavel = db.usuarios.find_one({'_id': ObjectId(m['responsavel_id'])})
                if responsavel:
                    responsavel_nome = responsavel.get('nome', 'Desconhecido')
            
            movimentacoes_formatadas.append({
                'data': m['data'].strftime('%d/%m/%Y %H:%M'),
                'tipo': m.get('tipo', 'Entrada'),
                'quantidade': int(m.get('quantidade', 0)),
                'motivo': m.get('motivo', ''),
                'responsavel': responsavel_nome
            })
        
        produto_detalhado = {
            'id': str(produto['_id']),
            'nome': produto.get('nome', ''),
            'descricao': produto.get('descricao', ''),
            'marca': produto.get('marca', ''),
            'preco': float(produto.get('preco', 0)),
            'estoque': int(produto.get('estoque', 0)),
            'estoque_minimo': int(produto.get('estoque_minimo', 0)),
            'status': produto.get('status', 'Ativo'),
            'unidade': produto.get('unidade', 'un'),
            'movimentacoes': movimentacoes_formatadas
        }
        
        return jsonify({'success': True, 'produto': produto_detalhado})
    except Exception as e:
        logger.error(f"❌ Erro ao buscar produto: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/produtos', methods=['POST'])
@login_required
@verificar_permissao('gerenciar_produtos')
def create_produto():
    """Cria novo produto"""
    try:
        data = request.get_json()
        
        if not data.get('nome'):
            return jsonify({'success': False, 'message': 'Nome é obrigatório'}), 400
        
        if not data.get('preco'):
            return jsonify({'success': False, 'message': 'Preço é obrigatório'}), 400
        
        novo_produto = {
            'nome': data['nome'].strip(),
            'descricao': data.get('descricao', ''),
            'marca': data.get('marca', ''),
            'preco': float(data['preco']),
            'estoque': int(data.get('estoque', 0)),
            'estoque_minimo': int(data.get('estoque_minimo', 5)),
            'unidade': data.get('unidade', 'un'),
            'status': 'Ativo',
            'data_cadastro': datetime.now(),
            'criado_por': session['user_id']
        }
        
        result = db.produtos.insert_one(novo_produto)
        
        # Registrar entrada inicial no estoque
        if int(data.get('estoque', 0)) > 0:
            db.estoque_movimentacoes.insert_one({
                'produto_id': str(result.inserted_id),
                'tipo': 'Entrada',
                'quantidade': int(data.get('estoque', 0)),
                'motivo': 'Cadastro inicial',
                'data': datetime.now(),
                'responsavel_id': session['user_id']
            })
        
        logger.info(f"✅ Produto criado: {data['nome']}")
        return jsonify({
            'success': True,
            'message': 'Produto criado com sucesso',
            'produto_id': str(result.inserted_id)
        })
    except Exception as e:
        logger.error(f"❌ Erro ao criar produto: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/produtos/<produto_id>', methods=['PUT'])
@login_required
@verificar_permissao('gerenciar_produtos')
def update_produto(produto_id):
    """Atualiza produto"""
    try:
        data = request.get_json()
        
        update_data = {}
        if 'nome' in data:
            update_data['nome'] = data['nome'].strip()
        if 'descricao' in data:
            update_data['descricao'] = data['descricao']
        if 'marca' in data:
            update_data['marca'] = data['marca']
        if 'preco' in data:
            update_data['preco'] = float(data['preco'])
        if 'estoque_minimo' in data:
            update_data['estoque_minimo'] = int(data['estoque_minimo'])
        if 'unidade' in data:
            update_data['unidade'] = data['unidade']
        if 'status' in data:
            update_data['status'] = data['status']
        
        # Estoque não deve ser atualizado diretamente, apenas via movimentações
        if 'estoque' in data:
            return jsonify({
                'success': False,
                'message': 'Use a rota de movimentação de estoque para ajustar quantidades'
            }), 400
        
        if update_data:
            update_data['atualizado_em'] = datetime.now()
            db.produtos.update_one(
                {'_id': ObjectId(produto_id)},
                {'$set': update_data}
            )
            
            logger.info(f"✅ Produto atualizado: {produto_id}")
            return jsonify({'success': True, 'message': 'Produto atualizado com sucesso'})
        
        return jsonify({'success': False, 'message': 'Nenhum dado para atualizar'}), 400
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar produto: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/produtos/<produto_id>', methods=['DELETE'])
@login_required
@verificar_permissao('gerenciar_produtos')
def delete_produto(produto_id):
    """Deleta (inativa) um produto"""
    try:
        db.produtos.update_one(
            {'_id': ObjectId(produto_id)},
            {'$set': {'status': 'Inativo', 'inativado_em': datetime.now()}}
        )
        
        logger.info(f"✅ Produto inativado: {produto_id}")
        return jsonify({'success': True, 'message': 'Produto inativado com sucesso'})
    except Exception as e:
        logger.error(f"❌ Erro ao inativar produto: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/marcas-produtos', methods=['GET'])
@login_required
def get_marcas_produtos():
    """Lista marcas de produtos"""
    try:
        marcas = db.produtos.distinct('marca', {'marca': {'$ne': ''}})
        return jsonify({
            'success': True,
            'marcas': sorted(marcas)
        })
    except Exception as e:
        logger.error(f"❌ Erro ao buscar marcas: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
# ==================== ESTOQUE ROUTES - CORRIGIDO ====================

@app.route('/api/estoque/movimentar', methods=['POST'])
@login_required
@verificar_permissao('gerenciar_estoque')
def movimentar_estoque():
    """Movimenta estoque (entrada ou saída)"""
    try:
        data = request.get_json()
        
        produto_id = data.get('produto_id')
        tipo = data.get('tipo')  # 'Entrada' ou 'Saída'
        quantidade = int(data.get('quantidade', 0))
        motivo = data.get('motivo', '')
        
        if not all([produto_id, tipo, quantidade]):
            return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
        
        if tipo not in ['Entrada', 'Saída']:
            return jsonify({'success': False, 'message': 'Tipo inválido'}), 400
        
        if quantidade <= 0:
            return jsonify({'success': False, 'message': 'Quantidade deve ser positiva'}), 400
        
        # Buscar produto
        produto = db.produtos.find_one({'_id': ObjectId(produto_id)})
        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
        
        estoque_atual = int(produto.get('estoque', 0))
        
        # Calcular novo estoque
        if tipo == 'Entrada':
            novo_estoque = estoque_atual + quantidade
        else:  # Saída
            if estoque_atual < quantidade:
                return jsonify({
                    'success': False,
                    'message': f'Estoque insuficiente. Disponível: {estoque_atual}'
                }), 400
            novo_estoque = estoque_atual - quantidade
        
        # Atualizar estoque
        db.produtos.update_one(
            {'_id': ObjectId(produto_id)},
            {'$set': {'estoque': novo_estoque}}
        )
        
        # Registrar movimentação
        db.estoque_movimentacoes.insert_one({
            'produto_id': produto_id,
            'tipo': tipo,
            'quantidade': quantidade,
            'estoque_anterior': estoque_atual,
            'estoque_novo': novo_estoque,
            'motivo': motivo,
            'data': datetime.now(),
            'responsavel_id': session['user_id']
        })
        
        logger.info(f"✅ Estoque movimentado: {tipo} - {quantidade} - {produto.get('nome', '')}")
        return jsonify({
            'success': True,
            'message': 'Movimentação registrada com sucesso',
            'estoque_novo': novo_estoque
        })
    except Exception as e:
        logger.error(f"❌ Erro ao movimentar estoque: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/movimentacoes', methods=['GET'])
@login_required
def get_movimentacoes_estoque():
    """Lista movimentações de estoque com paginação"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        produto_id = request.args.get('produto_id', '')
        tipo = request.args.get('tipo', '')
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        
        # Montar query
        query = {}
        if produto_id:
            query['produto_id'] = produto_id
        if tipo:
            query['tipo'] = tipo
        
        # Filtro de data
        if data_inicio or data_fim:
            query['data'] = {}
            if data_inicio:
                query['data']['$gte'] = datetime.strptime(data_inicio, '%Y-%m-%d')
            if data_fim:
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
                query['data']['$lte'] = data_fim_dt.replace(hour=23, minute=59, second=59)
        
        # Contar total
        total = db.estoque_movimentacoes.count_documents(query)
        
        # Buscar movimentações
        skip = (page - 1) * limit
        movimentacoes = list(
            db.estoque_movimentacoes.find(query)
            .sort('data', DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        
        movimentacoes_formatadas = []
        for m in movimentacoes:
            # Buscar produto
            produto = db.produtos.find_one({'_id': ObjectId(m['produto_id'])})
            produto_nome = produto.get('nome', 'Desconhecido') if produto else 'Produto removido'
            
            # Buscar responsável
            responsavel_nome = 'Sistema'
            if m.get('responsavel_id'):
                responsavel = db.usuarios.find_one({'_id': ObjectId(m['responsavel_id'])})
                if responsavel:
                    responsavel_nome = responsavel.get('nome', 'Desconhecido')
            
            movimentacoes_formatadas.append({
                'id': str(m['_id']),
                'data': m['data'].strftime('%d/%m/%Y %H:%M'),
                'tipo': m.get('tipo', 'Entrada'),
                'produto': produto_nome,
                'produto_id': m['produto_id'],
                'quantidade': int(m.get('quantidade', 0)),
                'estoque_anterior': int(m.get('estoque_anterior', 0)),
                'estoque_novo': int(m.get('estoque_novo', 0)),
                'motivo': m.get('motivo', ''),
                'responsavel': responsavel_nome
            })
        
        return jsonify({
            'success': True,
            'movimentacoes': movimentacoes_formatadas,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })
    except Exception as e:
        logger.error(f"❌ Erro ao buscar movimentações: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/alertas', methods=['GET'])
@login_required
def get_alertas_estoque():
    """Obtém alertas de estoque baixo/crítico"""
    try:
        produtos = list(db.produtos.find({'status': 'Ativo'}))
        
        criticos = []
        baixos = []
        
        for p in produtos:
            estoque_atual = int(p.get('estoque', 0))
            estoque_minimo = int(p.get('estoque_minimo', 0))
            
            if estoque_atual <= estoque_minimo:
                criticos.append({
                    'id': str(p['_id']),
                    'nome': p.get('nome', ''),
                    'marca': p.get('marca', ''),
                    'estoque_atual': estoque_atual,
                    'estoque_minimo': estoque_minimo,
                    'diferenca': estoque_atual - estoque_minimo,
                    'nivel': 'Crítico'
                })
            elif estoque_atual < estoque_minimo * 1.5:
                baixos.append({
                    'id': str(p['_id']),
                    'nome': p.get('nome', ''),
                    'marca': p.get('marca', ''),
                    'estoque_atual': estoque_atual,
                    'estoque_minimo': estoque_minimo,
                    'diferenca': estoque_atual - estoque_minimo,
                    'nivel': 'Baixo'
                })
        
        return jsonify({
            'success': True,
            'alertas': {
                'criticos': criticos,
                'baixos': baixos,
                'total_criticos': len(criticos),
                'total_baixos': len(baixos)
            }
        })
    except Exception as e:
        logger.error(f"❌ Erro ao buscar alertas: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/relatorio', methods=['GET'])
@login_required
def relatorio_estoque():
    """Gera relatório de estoque"""
    try:
        tipo = request.args.get('tipo', 'posicao')  # posicao, movimentacoes, valorizado, criticos
        
        if tipo == 'posicao':
            # Relatório de posição atual
            produtos = list(db.produtos.find({'status': 'Ativo'}).sort('nome', ASCENDING))
            
            produtos_info = []
            for p in produtos:
                estoque_atual = int(p.get('estoque', 0))
                estoque_minimo = int(p.get('estoque_minimo', 0))
                
                if estoque_atual <= estoque_minimo:
                    status = 'Crítico'
                elif estoque_atual < estoque_minimo * 1.5:
                    status = 'Baixo'
                else:
                    status = 'Normal'
                
                produtos_info.append({
                    'nome': p.get('nome', ''),
                    'marca': p.get('marca', ''),
                    'estoque_atual': estoque_atual,
                    'estoque_minimo': estoque_minimo,
                    'unidade': p.get('unidade', 'un'),
                    'status': status
                })
            
            return jsonify({
                'success': True,
                'relatorio': {
                    'tipo': 'posicao',
                    'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
                    'total_produtos': len(produtos),
                    'produtos': produtos_info
                }
            })
        
        elif tipo == 'valorizado':
            # Relatório valorizado
            produtos = list(db.produtos.find({'status': 'Ativo'}))
            
            valor_total = 0
            produtos_info = []
            
            for p in produtos:
                estoque = int(p.get('estoque', 0))
                preco = float(p.get('preco', 0))
                valor = estoque * preco
                valor_total += valor
                
                produtos_info.append({
                    'nome': p.get('nome', ''),
                    'marca': p.get('marca', ''),
                    'estoque': estoque,
                    'preco_unitario': round(preco, 2),
                    'valor_total': round(valor, 2)
                })
            
            # Ordenar por valor
            produtos_info.sort(key=lambda x: x['valor_total'], reverse=True)
            
            return jsonify({
                'success': True,
                'relatorio': {
                    'tipo': 'valorizado',
                    'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
                    'valor_total_estoque': round(valor_total, 2),
                    'total_produtos': len(produtos),
                    'produtos': produtos_info
                }
            })
        
        elif tipo == 'movimentacoes':
            # Relatório de movimentações
            data_inicio = request.args.get('data_inicio', '')
            data_fim = request.args.get('data_fim', '')
            
            query = {}
            if data_inicio:
                query['data'] = {'$gte': datetime.strptime(data_inicio, '%Y-%m-%d')}
            if data_fim:
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
                if 'data' not in query:
                    query['data'] = {}
                query['data']['$lte'] = data_fim_dt.replace(hour=23, minute=59, second=59)
            
            movimentacoes = list(db.estoque_movimentacoes.find(query).sort('data', DESCENDING))
            
            total_entradas = 0
            total_saidas = 0
            movs_info = []
            
            for m in movimentacoes:
                produto = db.produtos.find_one({'_id': ObjectId(m['produto_id'])})
                produto_nome = produto.get('nome', 'Desconhecido') if produto else 'Produto removido'
                
                tipo_mov = m.get('tipo', 'Entrada')
                quantidade = int(m.get('quantidade', 0))
                
                if tipo_mov == 'Entrada':
                    total_entradas += quantidade
                else:
                    total_saidas += quantidade
                
                movs_info.append({
                    'data': m['data'].strftime('%d/%m/%Y %H:%M'),
                    'tipo': tipo_mov,
                    'produto': produto_nome,
                    'quantidade': quantidade,
                    'motivo': m.get('motivo', '')
                })
            
            return jsonify({
                'success': True,
                'relatorio': {
                    'tipo': 'movimentacoes',
                    'periodo': {
                        'inicio': data_inicio if data_inicio else 'Todas',
                        'fim': data_fim if data_fim else 'Todas'
                    },
                    'resumo': {
                        'total_movimentacoes': len(movimentacoes),
                        'total_entradas': total_entradas,
                        'total_saidas': total_saidas,
                        'saldo': total_entradas - total_saidas
                    },
                    'movimentacoes': movs_info[:100]  # Limitar para não sobrecarregar
                }
            })
        
        else:
            return jsonify({'success': False, 'message': 'Tipo de relatório inválido'}), 400
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar relatório: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/estoque/dashboard', methods=['GET'])
@login_required
def dashboard_estoque():
    """Dashboard com estatísticas do estoque"""
    try:
        # Total de produtos
        total_produtos = db.produtos.count_documents({'status': 'Ativo'})
        
        # Produtos com estoque crítico
        produtos = list(db.produtos.find({'status': 'Ativo'}))
        criticos = 0
        baixos = 0
        valor_total = 0
        
        for p in produtos:
            estoque_atual = int(p.get('estoque', 0))
            estoque_minimo = int(p.get('estoque_minimo', 0))
            preco = float(p.get('preco', 0))
            
            if estoque_atual <= estoque_minimo:
                criticos += 1
            elif estoque_atual < estoque_minimo * 1.5:
                baixos += 1
            
            valor_total += estoque_atual * preco
        
        # Movimentações do mês
        inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        movs_mes = list(db.estoque_movimentacoes.find({'data': {'$gte': inicio_mes}}))
        
        entradas_mes = sum([int(m.get('quantidade', 0)) for m in movs_mes if m.get('tipo') == 'Entrada'])
        saidas_mes = sum([int(m.get('quantidade', 0)) for m in movs_mes if m.get('tipo') == 'Saída'])
        
        return jsonify({
            'success': True,
            'dashboard': {
                'total_produtos': total_produtos,
                'produtos_criticos': criticos,
                'produtos_baixos': baixos,
                'valor_total_estoque': round(valor_total, 2),
                'movimentacoes_mes': {
                    'entradas': entradas_mes,
                    'saidas': saidas_mes,
                    'saldo': entradas_mes - saidas_mes
                }
            }
        })
    except Exception as e:
        logger.error(f"❌ Erro ao gerar dashboard: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
# ==================== AGENDAMENTOS ROUTES - CORRIGIDO ====================

@app.route('/api/agendamentos', methods=['GET'])
@login_required
def get_agendamentos():
    """Lista agendamentos com paginação e filtros - CORRIGIDO"""
    try:
        # Parâmetros
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)  # Máximo 100
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        profissional_id = request.args.get('profissional_id', '')
        status = request.args.get('status', '')
        
        # Cache key
        cache_key = f"agendamentos_{page}_{limit}_{data_inicio}_{data_fim}_{profissional_id}_{status}"
        cached_data = get_from_cache(cache_key)
        if cached_data:
            return jsonify(cached_data)
        
        # Montar query
        query = {}
        if data_inicio or data_fim:
            query['data'] = {}
            if data_inicio:
                query['data']['$gte'] = datetime.strptime(data_inicio, '%Y-%m-%d')
            if data_fim:
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
                query['data']['$lte'] = data_fim_dt.replace(hour=23, minute=59, second=59)
        
        if profissional_id:
            query['profissional_id'] = profissional_id
        if status:
            query['status'] = status
        
        # Contar total
        total = db.agendamentos.count_documents(query)
        
        # Buscar agendamentos
        skip = (page - 1) * limit
        agendamentos = list(
            db.agendamentos.find(query)
            .sort('data', DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        
        agendamentos_formatados = []
        for a in agendamentos:
            # Buscar cliente
            cliente = db.clientes.find_one({'_id': ObjectId(a.get('cliente_id', ''))})
            # Buscar profissional
            profissional = db.profissionais.find_one({'_id': ObjectId(a.get('profissional_id', ''))})
            # Buscar serviço
            servico = db.servicos.find_one({'_id': ObjectId(a.get('servico_id', ''))})
            
            agendamentos_formatados.append({
                'id': str(a['_id']),
                'data': a['data'].strftime('%d/%m/%Y'),
                'hora': a['data'].strftime('%H:%M'),
                'cliente': cliente.get('nome', 'Desconhecido') if cliente else 'Cliente removido',
                'cliente_id': a.get('cliente_id', ''),
                'cliente_telefone': cliente.get('telefone', '') if cliente else '',
                'profissional': profissional.get('nome', 'Desconhecido') if profissional else 'Profissional removido',
                'profissional_id': a.get('profissional_id', ''),
                'servico': servico.get('nome', 'Desconhecido') if servico else 'Serviço removido',
                'servico_id': a.get('servico_id', ''),
                'status': a.get('status', 'Agendado'),
                'valor': float(a.get('valor', 0)),
                'observacoes': a.get('observacoes', '')
            })
        
        response = {
            'success': True,
            'agendamentos': agendamentos_formatados,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }
        
        # Salvar no cache
        set_in_cache(cache_key, response)
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"❌ Erro ao buscar agendamentos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/agendamentos/calendario', methods=['GET'])
@login_required
def get_calendario_agendamentos():
    """Retorna agendamentos em formato de calendário"""
    try:
        # Parâmetros
        mes = int(request.args.get('mes', datetime.now().month))
        ano = int(request.args.get('ano', datetime.now().year))
        profissional_id = request.args.get('profissional_id', '')
        
        # Calcular início e fim do mês
        inicio_mes = datetime(ano, mes, 1, 0, 0, 0)
        if mes == 12:
            fim_mes = datetime(ano + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
        else:
            fim_mes = datetime(ano, mes + 1, 1, 0, 0, 0) - timedelta(seconds=1)
        
        # Query
        query = {
            'data': {'$gte': inicio_mes, '$lte': fim_mes}
        }
        if profissional_id:
            query['profissional_id'] = profissional_id
        
        # Buscar agendamentos
        agendamentos = list(db.agendamentos.find(query))
        
        # Formatar para calendário
        eventos = []
        for a in agendamentos:
            cliente = db.clientes.find_one({'_id': ObjectId(a.get('cliente_id', ''))})
            servico = db.servicos.find_one({'_id': ObjectId(a.get('servico_id', ''))})
            
            eventos.append({
                'id': str(a['_id']),
                'title': f"{cliente.get('nome', 'Cliente') if cliente else 'Cliente'} - {servico.get('nome', 'Serviço') if servico else 'Serviço'}",
                'start': a['data'].isoformat(),
                'end': (a['data'] + timedelta(minutes=servico.get('duracao', 60) if servico else 60)).isoformat(),
                'status': a.get('status', 'Agendado'),
                'cliente_id': a.get('cliente_id', ''),
                'profissional_id': a.get('profissional_id', ''),
                'servico_id': a.get('servico_id', '')
            })
        
        return jsonify({
            'success': True,
            'eventos': eventos
        })
    except Exception as e:
        logger.error(f"❌ Erro ao buscar calendário: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/agendamentos/disponibilidade', methods=['GET'])
@login_required
def get_disponibilidade():
    """Verifica horários disponíveis de um profissional"""
    try:
        profissional_id = request.args.get('profissional_id')
        data = request.args.get('data')  # formato: YYYY-MM-DD
        servico_id = request.args.get('servico_id')
        
        if not all([profissional_id, data, servico_id]):
            return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
        
        # Buscar profissional e serviço
        profissional = db.profissionais.find_one({'_id': ObjectId(profissional_id)})
        servico = db.servicos.find_one({'_id': ObjectId(servico_id)})
        
        if not profissional or not servico:
            return jsonify({'success': False, 'message': 'Profissional ou serviço não encontrado'}), 404
        
        # Horário de trabalho do profissional
        horario_trabalho = profissional.get('horario_trabalho', {'inicio': '09:00', 'fim': '18:00'})
        inicio_trabalho = datetime.strptime(f"{data} {horario_trabalho['inicio']}", '%Y-%m-%d %H:%M')
        fim_trabalho = datetime.strptime(f"{data} {horario_trabalho['fim']}", '%Y-%m-%d %H:%M')
        
        # Duração do serviço
        duracao = servico.get('duracao', 60)
        
        # Buscar agendamentos existentes
        data_dt = datetime.strptime(data, '%Y-%m-%d')
        inicio_dia = data_dt.replace(hour=0, minute=0, second=0)
        fim_dia = data_dt.replace(hour=23, minute=59, second=59)
        
        agendamentos_existentes = list(db.agendamentos.find({
            'profissional_id': profissional_id,
            'data': {'$gte': inicio_dia, '$lte': fim_dia},
            'status': {'$in': ['Agendado', 'Em Andamento']}
        }).sort('data', ASCENDING))
        
        # Gerar slots disponíveis
        slots_disponiveis = []
        horario_atual = inicio_trabalho
        
        while horario_atual < fim_trabalho:
            fim_slot = horario_atual + timedelta(minutes=duracao)
            
            # Verificar se o slot está disponível
            disponivel = True
            for agendamento in agendamentos_existentes:
                inicio_agendamento = agendamento['data']
                # Buscar duração do serviço agendado
                servico_agendado = db.servicos.find_one({'_id': ObjectId(agendamento.get('servico_id', ''))})
                duracao_agendada = servico_agendado.get('duracao', 60) if servico_agendado else 60
                fim_agendamento = inicio_agendamento + timedelta(minutes=duracao_agendada)
                
                # Verificar sobreposição
                if not (fim_slot <= inicio_agendamento or horario_atual >= fim_agendamento):
                    disponivel = False
                    break
            
            if disponivel and fim_slot <= fim_trabalho:
                slots_disponiveis.append({
                    'horario': horario_atual.strftime('%H:%M'),
                    'disponivel': True
                })
            
            horario_atual += timedelta(minutes=30)  # Incremento de 30 minutos
        
        return jsonify({
            'success': True,
            'data': data,
            'profissional': profissional.get('nome', ''),
            'servico': servico.get('nome', ''),
            'duracao': duracao,
            'slots': slots_disponiveis
        })
    except Exception as e:
        logger.error(f"❌ Erro ao verificar disponibilidade: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/agendamentos', methods=['POST'])
@login_required
@verificar_permissao('gerenciar_agenda')
def create_agendamento():
    """Cria novo agendamento"""
    try:
        data_req = request.get_json()
        
        # Validações
        required_fields = ['cliente_id', 'profissional_id', 'servico_id', 'data', 'hora']
        for field in required_fields:
            if not data_req.get(field):
                return jsonify({'success': False, 'message': f'{field} é obrigatório'}), 400
        
        # Combinar data e hora
        data_hora = datetime.strptime(f"{data_req['data']} {data_req['hora']}", '%Y-%m-%d %H:%M')
        
        # Buscar serviço para pegar o preço
        servico = db.servicos.find_one({'_id': ObjectId(data_req['servico_id'])})
        if not servico:
            return jsonify({'success': False, 'message': 'Serviço não encontrado'}), 404
        
        novo_agendamento = {
            'cliente_id': data_req['cliente_id'],
            'profissional_id': data_req['profissional_id'],
            'servico_id': data_req['servico_id'],
            'data': data_hora,
            'status': 'Agendado',
            'valor': float(servico.get('preco', 0)),
            'observacoes': data_req.get('observacoes', ''),
            'data_criacao': datetime.now(),
            'criado_por': session['user_id']
        }
        
        result = db.agendamentos.insert_one(novo_agendamento)
        
        # Enviar notificação ao cliente
        cliente = db.clientes.find_one({'_id': ObjectId(data_req['cliente_id'])})
        if cliente and cliente.get('telefone'):
            mensagem = f"Olá {cliente.get('nome', '')}! Seu atendimento está agendado para {data_req['data']} às {data_req['hora']}. Equipe BIOMA Uberaba."
            # Aqui você pode integrar com API de SMS/WhatsApp
        
        logger.info(f"✅ Agendamento criado: {data_req['data']} {data_req['hora']}")
        return jsonify({
            'success': True,
            'message': 'Agendamento criado com sucesso',
            'agendamento_id': str(result.inserted_id)
        })
    except Exception as e:
        logger.error(f"❌ Erro ao criar agendamento: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/agendamentos/<agendamento_id>/status', methods=['PUT'])
@login_required
def update_status_agendamento(agendamento_id):
    """Atualiza status do agendamento"""
    try:
        data = request.get_json()
        novo_status = data.get('status')
        
        if novo_status not in ['Agendado', 'Em Andamento', 'Concluído', 'Cancelado']:
            return jsonify({'success': False, 'message': 'Status inválido'}), 400
        
        db.agendamentos.update_one(
            {'_id': ObjectId(agendamento_id)},
            {'$set': {
                'status': novo_status,
                'atualizado_em': datetime.now(),
                'atualizado_por': session['user_id']
            }}
        )
        
        # Se concluído, calcular comissão
        if novo_status == 'Concluído':
            agendamento = db.agendamentos.find_one({'_id': ObjectId(agendamento_id)})
            if agendamento:
                profissional = db.profissionais.find_one({'_id': ObjectId(agendamento['profissional_id'])})
                if profissional:
                    percentual = float(profissional.get('comissao_percentual', 10))
                    valor = float(agendamento.get('valor', 0))
                    valor_comissao = valor * (percentual / 100)
                    
                    # Registrar comissão
                    db.comissoes.insert_one({
                        'profissional_id': agendamento['profissional_id'],
                        'agendamento_id': str(agendamento['_id']),
                        'valor': valor_comissao,
                        'percentual': percentual,
                        'valor_servico': valor,
                        'data': datetime.now(),
                        'status': 'Pendente'
                    })
        
        logger.info(f"✅ Status do agendamento atualizado: {agendamento_id} -> {novo_status}")
        return jsonify({'success': True, 'message': 'Status atualizado com sucesso'})
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar status: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== FINANCEIRO ROUTES - NOVO MÓDULO COMPLETO ====================

@app.route('/api/financeiro/dashboard', methods=['GET'])
@login_required
@verificar_permissao('visualizar_financeiro')
def dashboard_financeiro():
    """Dashboard financeiro com resumo do mês"""
    try:
        # Período (padrão: mês atual)
        mes = int(request.args.get('mes', datetime.now().month))
        ano = int(request.args.get('ano', datetime.now().year))
        
        inicio_mes = datetime(ano, mes, 1, 0, 0, 0)
        if mes == 12:
            fim_mes = datetime(ano + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
        else:
            fim_mes = datetime(ano, mes + 1, 1, 0, 0, 0) - timedelta(seconds=1)
        
        # RECEITAS
        # Orçamentos aprovados
        orcamentos_aprovados = list(db.orcamentos.find({
            'status': 'Aprovado',
            'data_criacao': {'$gte': inicio_mes, '$lte': fim_mes}
        }))
        receita_orcamentos = sum([float(o.get('total', 0)) for o in orcamentos_aprovados])
        
        # Agendamentos concluídos
        agendamentos_concluidos = list(db.agendamentos.find({
            'status': 'Concluído',
            'data': {'$gte': inicio_mes, '$lte': fim_mes}
        }))
        receita_agendamentos = sum([float(a.get('valor', 0)) for a in agendamentos_concluidos])
        
        receita_total = receita_orcamentos + receita_agendamentos
        
        # DESPESAS
        despesas = list(db.despesas.find({
            'data': {'$gte': inicio_mes, '$lte': fim_mes}
        }))
        despesa_total = sum([float(d.get('valor', 0)) for d in despesas])
        
        # COMISSÕES
        comissoes = list(db.comissoes.find({
            'data': {'$gte': inicio_mes, '$lte': fim_mes}
        }))
        comissoes_total = sum([float(c.get('valor', 0)) for c in comissoes])
        comissoes_pendentes = sum([float(c.get('valor', 0)) for c in comissoes if c.get('status') == 'Pendente'])
        comissoes_pagas = sum([float(c.get('valor', 0)) for c in comissoes if c.get('status') == 'Paga'])
        
        # LUCRO
        lucro_bruto = receita_total
        lucro_liquido = receita_total - despesa_total - comissoes_total
        
        return jsonify({
            'success': True,
            'dashboard': {
                'periodo': {
                    'mes': mes,
                    'ano': ano,
                    'descricao': f"{['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'][mes-1]}/{ano}"
                },
                'receitas': {
                    'total': round(receita_total, 2),
                    'orcamentos': round(receita_orcamentos, 2),
                    'agendamentos': round(receita_agendamentos, 2)
                },
                'despesas': {
                    'total': round(despesa_total, 2)
                },
                'comissoes': {
                    'total': round(comissoes_total, 2),
                    'pendentes': round(comissoes_pendentes, 2),
                    'pagas': round(comissoes_pagas, 2)
                },
                'lucro': {
                    'bruto': round(lucro_bruto, 2),
                    'liquido': round(lucro_liquido, 2)
                }
            }
        })
    except Exception as e:
        logger.error(f"❌ Erro no dashboard financeiro: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/financeiro/despesas', methods=['GET'])
@login_required
@verificar_permissao('visualizar_financeiro')
def get_despesas():
    """Lista despesas com filtros"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        categoria = request.args.get('categoria', '')
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        
        query = {}
        if categoria:
            query['categoria'] = categoria
        
        if data_inicio or data_fim:
            query['data'] = {}
            if data_inicio:
                query['data']['$gte'] = datetime.strptime(data_inicio, '%Y-%m-%d')
            if data_fim:
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
                query['data']['$lte'] = data_fim_dt.replace(hour=23, minute=59, second=59)
        
        total = db.despesas.count_documents(query)
        skip = (page - 1) * limit
        
        despesas = list(
            db.despesas.find(query)
            .sort('data', DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        
        despesas_formatadas = []
        for d in despesas:
            despesas_formatadas.append({
                'id': str(d['_id']),
                'descricao': d.get('descricao', ''),
                'categoria': d.get('categoria', ''),
                'valor': float(d.get('valor', 0)),
                'data': d['data'].strftime('%d/%m/%Y'),
                'forma_pagamento': d.get('forma_pagamento', ''),
                'observacoes': d.get('observacoes', '')
            })
        
        return jsonify({
            'success': True,
            'despesas': despesas_formatadas,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })
    except Exception as e:
        logger.error(f"❌ Erro ao buscar despesas: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/financeiro/despesas', methods=['POST'])
@login_required
@verificar_permissao('visualizar_financeiro')
def create_despesa():
    """Registra nova despesa"""
    try:
        data = request.get_json()
        
        if not all([data.get('descricao'), data.get('valor'), data.get('data')]):
            return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
        
        nova_despesa = {
            'descricao': data['descricao'],
            'categoria': data.get('categoria', 'Outros'),
            'valor': float(data['valor']),
            'data': datetime.strptime(data['data'], '%Y-%m-%d'),
            'forma_pagamento': data.get('forma_pagamento', ''),
            'observacoes': data.get('observacoes', ''),
            'criada_em': datetime.now(),
            'criada_por': session['user_id']
        }
        
        result = db.despesas.insert_one(nova_despesa)
        
        logger.info(f"✅ Despesa registrada: {data['descricao']} - R$ {data['valor']}")
        return jsonify({
            'success': True,
            'message': 'Despesa registrada com sucesso',
            'despesa_id': str(result.inserted_id)
        })
    except Exception as e:
        logger.error(f"❌ Erro ao registrar despesa: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/financeiro/comissoes', methods=['GET'])
@login_required
@verificar_permissao('visualizar_comissoes')
def get_comissoes():
    """Lista comissões com filtros"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        profissional_id = request.args.get('profissional_id', '')
        status = request.args.get('status', '')
        mes = request.args.get('mes', '')
        ano = request.args.get('ano', '')
        
        query = {}
        if profissional_id:
            query['profissional_id'] = profissional_id
        if status:
            query['status'] = status
        
        if mes and ano:
            inicio = datetime(int(ano), int(mes), 1, 0, 0, 0)
            if int(mes) == 12:
                fim = datetime(int(ano) + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
            else:
                fim = datetime(int(ano), int(mes) + 1, 1, 0, 0, 0) - timedelta(seconds=1)
            query['data'] = {'$gte': inicio, '$lte': fim}
        
        total = db.comissoes.count_documents(query)
        skip = (page - 1) * limit
        
        comissoes = list(
            db.comissoes.find(query)
            .sort('data', DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        
        comissoes_formatadas = []
        for c in comissoes:
            profissional = db.profissionais.find_one({'_id': ObjectId(c['profissional_id'])})
            
            comissoes_formatadas.append({
                'id': str(c['_id']),
                'profissional': profissional.get('nome', 'Desconhecido') if profissional else 'Desconhecido',
                'profissional_id': c['profissional_id'],
                'valor': float(c.get('valor', 0)),
                'percentual': float(c.get('percentual', 0)),
                'valor_servico': float(c.get('valor_servico', 0)),
                'data': c['data'].strftime('%d/%m/%Y'),
                'status': c.get('status', 'Pendente'),
                'data_pagamento': c['data_pagamento'].strftime('%d/%m/%Y') if c.get('data_pagamento') else None
            })
        
        return jsonify({
            'success': True,
            'comissoes': comissoes_formatadas,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })
    except Exception as e:
        logger.error(f"❌ Erro ao buscar comissões: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/financeiro/comissoes/<comissao_id>/pagar', methods=['POST'])
@login_required
@verificar_permissao('visualizar_financeiro')
def pagar_comissao(comissao_id):
    """Marca comissão como paga"""
    try:
        db.comissoes.update_one(
            {'_id': ObjectId(comissao_id)},
            {'$set': {
                'status': 'Paga',
                'data_pagamento': datetime.now(),
                'paga_por': session['user_id']
            }}
        )
        
        logger.info(f"✅ Comissão paga: {comissao_id}")
        return jsonify({'success': True, 'message': 'Comissão marcada como paga'})
    except Exception as e:
        logger.error(f"❌ Erro ao pagar comissão: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/financeiro/relatorio', methods=['GET'])
@login_required
@verificar_permissao('visualizar_financeiro')
def relatorio_financeiro():
    """Relatório financeiro completo (DRE simplificado)"""
    try:
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        
        if not data_inicio or not data_fim:
            # Padrão: últimos 12 meses
            fim = datetime.now()
            inicio = fim - timedelta(days=365)
        else:
            inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            fim = datetime.strptime(data_fim, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        
        # Receitas por mês
        pipeline_receitas = [
            {'$match': {
                'status': 'Aprovado',
                'data_criacao': {'$gte': inicio, '$lte': fim}
            }},
            {'$group': {
                '_id': {
                    'mes': {'$month': '$data_criacao'},
                    'ano': {'$year': '$data_criacao'}
                },
                'total': {'$sum': '$total'}
            }},
            {'$sort': {'_id.ano': 1, '_id.mes': 1}}
        ]
        receitas_mes = list(db.orcamentos.aggregate(pipeline_receitas))
        
        # Despesas por mês
        pipeline_despesas = [
            {'$match': {'data': {'$gte': inicio, '$lte': fim}}},
            {'$group': {
                '_id': {
                    'mes': {'$month': '$data'},
                    'ano': {'$year': '$data'}
                },
                'total': {'$sum': '$valor'}
            }},
            {'$sort': {'_id.ano': 1, '_id.mes': 1}}
        ]
        despesas_mes = list(db.despesas.aggregate(pipeline_despesas))
        
        # Comissões por mês
        pipeline_comissoes = [
            {'$match': {'data': {'$gte': inicio, '$lte': fim}}},
            {'$group': {
                '_id': {
                    'mes': {'$month': '$data'},
                    'ano': {'$year': '$data'}
                },
                'total': {'$sum': '$valor'}
            }},
            {'$sort': {'_id.ano': 1, '_id.mes': 1}}
        ]
        comissoes_mes = list(db.comissoes.aggregate(pipeline_comissoes))
        
        # Consolidar dados
        meses_info = []
        for r in receitas_mes:
            mes = r['_id']['mes']
            ano = r['_id']['ano']
            
            # Buscar despesa do mês
            despesa = next((d['total'] for d in despesas_mes if d['_id']['mes'] == mes and d['_id']['ano'] == ano), 0)
            # Buscar comissão do mês
            comissao = next((c['total'] for c in comissoes_mes if c['_id']['mes'] == mes and c['_id']['ano'] == ano), 0)
            
            receita = float(r['total'])
            lucro_liquido = receita - despesa - comissao
            
            meses_info.append({
                'mes': f"{['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'][mes-1]}/{ano}",
                'receita': round(receita, 2),
                'despesas': round(despesa, 2),
                'comissoes': round(comissao, 2),
                'lucro_liquido': round(lucro_liquido, 2)
            })
        
        # Totais
        total_receitas = sum([m['receita'] for m in meses_info])
        total_despesas = sum([m['despesas'] for m in meses_info])
        total_comissoes = sum([m['comissoes'] for m in meses_info])
        total_lucro = total_receitas - total_despesas - total_comissoes
        
        return jsonify({
            'success': True,
            'relatorio': {
                'periodo': {
                    'inicio': inicio.strftime('%d/%m/%Y'),
                    'fim': fim.strftime('%d/%m/%Y')
                },
                'por_mes': meses_info,
                'totais': {
                    'receitas': round(total_receitas, 2),
                    'despesas': round(total_despesas, 2),
                    'comissoes': round(total_comissoes, 2),
                    'lucro_liquido': round(total_lucro, 2)
                }
            }
        })
    except Exception as e:
        logger.error(f"❌ Erro ao gerar relatório financeiro: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
# ==================== ORÇAMENTOS ROUTES COM IMPRESSÃO E WHATSAPP ====================

@app.route('/api/orcamentos', methods=['GET'])
@login_required
def get_orcamentos():
    """Lista orçamentos com filtros"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        status = request.args.get('status', '')
        search = request.args.get('search', '')
        
        query = {}
        if status:
            query['status'] = status
        if search:
            query['$or'] = [
                {'numero': {'$regex': search, '$options': 'i'}},
                {'cliente_nome': {'$regex': search, '$options': 'i'}}
            ]
        
        total = db.orcamentos.count_documents(query)
        skip = (page - 1) * limit
        
        orcamentos = list(
            db.orcamentos.find(query)
            .sort('data_criacao', DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        
        orcamentos_formatados = []
        for o in orcamentos:
            orcamentos_formatados.append({
                'id': str(o['_id']),
                'numero': o.get('numero', ''),
                'cliente_nome': o.get('cliente_nome', ''),
                'cliente_id': o.get('cliente_id', ''),
                'data_criacao': o['data_criacao'].strftime('%d/%m/%Y'),
                'total': float(o.get('total', 0)),
                'status': o.get('status', 'Pendente')
            })
        
        return jsonify({
            'success': True,
            'orcamentos': orcamentos_formatados,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })
    except Exception as e:
        logger.error(f"❌ Erro ao buscar orçamentos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/orcamentos/<orcamento_id>/whatsapp', methods=['GET'])
@login_required
def enviar_orcamento_whatsapp(orcamento_id):
    """Gera link WhatsApp para enviar orçamento"""
    try:
        orcamento = db.orcamentos.find_one({'_id': ObjectId(orcamento_id)})
        if not orcamento:
            return jsonify({'success': False, 'message': 'Orçamento não encontrado'}), 404
        
        cliente = db.clientes.find_one({'_id': ObjectId(orcamento.get('cliente_id', ''))})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
        
        # Montar mensagem
        mensagem = f"""🌳 *BIOMA Uberaba - Orçamento #{orcamento.get('numero', '')}*

Olá {cliente.get('nome', '')}!

Segue o orçamento solicitado:

"""
        
        # Adicionar produtos
        produtos = orcamento.get('produtos', [])
        if produtos:
            mensagem += "*Produtos:*\n"
            for p in produtos:
                mensagem += f"• {p.get('nome', '')} - {p.get('quantidade', 1)}x - R$ {float(p.get('preco', 0)):.2f}\n"
            mensagem += "\n"
        
        mensagem += f"*Total: R$ {float(orcamento.get('total', 0)):.2f}*\n\n"
        mensagem += f"Desconto: {float(orcamento.get('desconto_percentual', 0)):.1f}%\n"
        mensagem += f"Forma de pagamento: {orcamento.get('forma_pagamento', 'À vista')}\n\n"
        mensagem += "Estamos à disposição!\n"
        mensagem += "Equipe BIOMA Uberaba 🌿"
        
        link = gerar_link_whatsapp(cliente.get('telefone', ''), mensagem)
        
        return jsonify({
            'success': True,
            'link_whatsapp': link
        })
    except Exception as e:
        logger.error(f"❌ Erro ao gerar link WhatsApp: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== FILA ROUTES MELHORADA ====================

@app.route('/api/fila', methods=['GET'])
@login_required
def get_fila():
    """Lista clientes na fila"""
    try:
        data_hoje = datetime.now().replace(hour=0, minute=0, second=0)
        
        fila = list(db.fila.find({
            'data': {'$gte': data_hoje},
            'status': {'$in': ['Aguardando', 'Em Atendimento']}
        }).sort('posicao', ASCENDING))
        
        fila_formatada = []
        for f in fila:
            cliente = db.clientes.find_one({'_id': ObjectId(f['cliente_id'])})
            profissional = db.profissionais.find_one({'_id': ObjectId(f.get('profissional_id', ''))}) if f.get('profissional_id') else None
            
            fila_formatada.append({
                'id': str(f['_id']),
                'posicao': f.get('posicao', 0),
                'cliente': cliente.get('nome', 'Desconhecido') if cliente else 'Desconhecido',
                'cliente_telefone': cliente.get('telefone', '') if cliente else '',
                'profissional': profissional.get('nome', 'Sem profissional') if profissional else 'Sem profissional',
                'status': f.get('status', 'Aguardando'),
                'hora_chegada': f['data'].strftime('%H:%M'),
                'tempo_espera': int((datetime.now() - f['data']).total_seconds() / 60)
            })
        
        return jsonify({
            'success': True,
            'fila': fila_formatada,
            'total': len(fila_formatada)
        })
    except Exception as e:
        logger.error(f"❌ Erro ao buscar fila: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/fila/notificar/<fila_id>', methods=['POST'])
@login_required
def notificar_cliente_fila(fila_id):
    """Notifica cliente sobre posição na fila"""
    try:
        item_fila = db.fila.find_one({'_id': ObjectId(fila_id)})
        if not item_fila:
            return jsonify({'success': False, 'message': 'Item não encontrado'}), 404
        
        cliente = db.clientes.find_one({'_id': ObjectId(item_fila['cliente_id'])})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
        
        posicao = item_fila.get('posicao', 0)
        
        if posicao == 1:
            mensagem = f"Olá {cliente.get('nome', '')}! Você é o próximo da fila. Seu atendimento será iniciado em instantes. Equipe BIOMA Uberaba."
        else:
            mensagem = f"Olá {cliente.get('nome', '')}! Você está na posição {posicao} da fila. Aguarde, logo será atendido. Equipe BIOMA Uberaba."
        
        link = gerar_link_whatsapp(cliente.get('telefone', ''), mensagem)
        
        return jsonify({
            'success': True,
            'message': 'Notificação preparada',
            'link_whatsapp': link
        })
    except Exception as e:
        logger.error(f"❌ Erro ao notificar cliente: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== RELATÓRIOS CORRIGIDOS ====================

@app.route('/api/relatorios/mapa-calor', methods=['GET'])
@login_required
def mapa_calor():
    """Mapa de calor de atendimentos - CORRIGIDO"""
    try:
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        
        if not data_inicio or not data_fim:
            return jsonify({'success': False, 'message': 'Período obrigatório'}), 400
        
        inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        fim = datetime.strptime(data_fim, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        
        # Buscar agendamentos
        agendamentos = list(db.agendamentos.find({
            'data': {'$gte': inicio, '$lte': fim},
            'status': 'Concluído'
        }))
        
        # Inicializar mapa
        mapa = {}
        dias_semana = ['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM']
        
        for dia in dias_semana:
            mapa[dia] = {}
            for hora in range(8, 22):  # 08:00 às 21:00
                mapa[dia][f"{hora:02d}:00"] = 0
        
        # Preencher mapa
        for a in agendamentos:
            dia_semana = dias_semana[a['data'].weekday()]
            hora = f"{a['data'].hour:02d}:00"
            if hora in mapa[dia_semana]:
                mapa[dia_semana][hora] += 1
        
        return jsonify({
            'success': True,
            'mapa_calor': mapa
        })
    except Exception as e:
        logger.error(f"❌ Erro ao gerar mapa de calor: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== CONFIGURAÇÕES ====================

@app.route('/api/configuracoes/logo', methods=['POST'])
@login_required
@verificar_permissao('*')
def upload_logo():
    """Upload da logo do estabelecimento"""
    try:
        if 'logo' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['logo']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Tipo de arquivo não permitido'}), 400
        
        # Processar logo - tamanho específico para header
        imagem_processada = processar_imagem(file, max_size=(300, 100))
        if not imagem_processada:
            return jsonify({'success': False, 'message': 'Erro ao processar imagem'}), 500
        
        # Converter para base64
        logo_base64 = base64.b64encode(imagem_processada.getvalue()).decode('utf-8')
        logo_data_uri = f"data:image/jpeg;base64,{logo_base64}"
        
        # Salvar nas configurações
        db.configuracoes.update_one(
            {'tipo': 'geral'},
            {'$set': {'logo': logo_data_uri, 'logo_atualizada_em': datetime.now()}},
            upsert=True
        )
        
        logger.info(f"✅ Logo atualizada")
        return jsonify({
            'success': True,
            'message': 'Logo atualizada com sucesso',
            'logo': logo_data_uri
        })
    except Exception as e:
        logger.error(f"❌ Erro ao fazer upload da logo: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== SISTEMA/STATUS ====================

@app.route('/api/sistema/status', methods=['GET'])
@login_required
def status_sistema():
    """Status do sistema"""
    try:
        # Testar conexão MongoDB
        db.command('ping')
        mongodb_status = 'OK'
    except:
        mongodb_status = 'ERRO'
    
    # Estatísticas gerais
    total_usuarios = db.usuarios.count_documents({})
    total_clientes = db.clientes.count_documents({'status': 'Ativo'})
    total_profissionais = db.profissionais.count_documents({'status': 'Ativo'})
    total_agendamentos_hoje = db.agendamentos.count_documents({
        'data': {
            '$gte': datetime.now().replace(hour=0, minute=0, second=0),
            '$lte': datetime.now().replace(hour=23, minute=59, second=59)
        }
    })
    
    return jsonify({
        'success': True,
        'status': {
            'sistema': 'Online',
            'versao': '3.8',
            'mongodb': mongodb_status,
            'estatisticas': {
                'usuarios': total_usuarios,
                'clientes': total_clientes,
                'profissionais': total_profissionais,
                'agendamentos_hoje': total_agendamentos_hoje
            },
            'servidor_data_hora': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }
    })

# ==================== MAIN ====================

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🌳 BIOMA UBERABA v3.8 - BACKEND CORRIGIDO E MELHORADO")
    print("=" * 80)
    
    # Inicializar banco
    init_db()
    
    # Verificar ambiente
    is_production = os.getenv('FLASK_ENV') == 'production'
    base_url = 'https://bioma-system2.onrender.com' if is_production else 'http://localhost:5000'
    
    print(f"\n🚀 Servidor: {base_url}")
    print(f"👤 Login Padrão: admin / admin123")
    
    # Status MongoDB
    if db is not None:
        try:
            db.command('ping')
            print(f"💾 MongoDB: ✅ CONECTADO")
        except:
            print(f"💾 MongoDB: ❌ ERRO DE CONEXÃO")
    else:
        print(f"💾 MongoDB: ❌ NÃO CONECTADO")
    
    # Status Email
    if os.getenv('MAILERSEND_API_KEY'):
        print(f"📧 MailerSend: ✅ CONFIGURADO")
    else:
        print(f"📧 MailerSend: ⚠️  NÃO CONFIGURADO")
    
    print("\n" + "=" * 80)
    print(f"🕐 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 Correções: Carregamento infinito, Perfis de acesso, Financeiro")
    print(f"👨‍💻 Desenvolvedor: @juanmarco1999")
    print("=" * 80 + "\n")
    
    # Iniciar servidor
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=not is_production, host='0.0.0.0', port=port, threaded=True)