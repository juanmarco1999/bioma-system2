#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA - Backend Routes Complete
Rotas adicionais e complementares
"""

from flask import Blueprint, request, jsonify, session, current_app
from bson import ObjectId
from datetime import datetime, timedelta
from functools import wraps
import logging

# Criar Blueprint
api_complete = Blueprint('api_complete', __name__)

logger = logging.getLogger(__name__)

def convert_objectid(obj):
    """Converter ObjectId para string recursivamente"""
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
    """Decorator para verificar autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_db():
    """Obter conexão com o banco de dados"""
    return current_app.config.get('DB_CONNECTION')

# ==================== ROTAS DE PROFISSIONAIS ====================

@api_complete.route('/api/profissionais', methods=['GET'])
@login_required
def get_profissionais():
    """Listar profissionais"""
    try:
        db = get_db()
        if not db:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        skip = (page - 1) * limit

        profissionais = list(db.profissionais.find().sort('nome', 1).skip(skip).limit(limit))
        total = db.profissionais.count_documents({})

        return jsonify({
            'profissionais': convert_objectid(profissionais),
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })

    except Exception as e:
        logger.error(f"Erro ao buscar profissionais: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ROTAS DE ORÇAMENTOS ====================

@api_complete.route('/api/orcamentos', methods=['GET'])
@login_required
def get_orcamentos():
    """Listar orçamentos"""
    try:
        db = get_db()
        if not db:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        skip = (page - 1) * limit

        orcamentos = list(db.orcamentos.find().sort('data', -1).skip(skip).limit(limit))
        total = db.orcamentos.count_documents({})

        return jsonify({
            'orcamentos': convert_objectid(orcamentos),
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })

    except Exception as e:
        logger.error(f"Erro ao buscar orçamentos: {e}")
        return jsonify({'error': str(e)}), 500

@api_complete.route('/api/orcamentos', methods=['POST'])
@login_required
def create_orcamento():
    """Criar novo orçamento"""
    try:
        db = get_db()
        if not db:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        data = request.json
        data['created_at'] = datetime.now()
        data['updated_at'] = datetime.now()
        data['status'] = 'pendente'

        result = db.orcamentos.insert_one(data)

        return jsonify({
            'success': True,
            'id': str(result.inserted_id)
        })

    except Exception as e:
        logger.error(f"Erro ao criar orçamento: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ROTAS DE CONTRATOS ====================

@api_complete.route('/api/contratos', methods=['GET'])
@login_required
def get_contratos():
    """Listar contratos"""
    try:
        db = get_db()
        if not db:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        skip = (page - 1) * limit

        contratos = list(db.contratos.find().sort('data', -1).skip(skip).limit(limit))
        total = db.contratos.count_documents({})

        return jsonify({
            'contratos': convert_objectid(contratos),
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })

    except Exception as e:
        logger.error(f"Erro ao buscar contratos: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ROTAS DE ANAMNESE ====================

@api_complete.route('/api/cliente/<id>/anamnese', methods=['GET'])
@login_required
def get_anamnese(id):
    """Buscar anamnese do cliente"""
    try:
        db = get_db()
        if not db:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        anamneses = list(db.anamneses.find({'cliente_id': id}).sort('data', -1))

        return jsonify({
            'anamneses': convert_objectid(anamneses)
        })

    except Exception as e:
        logger.error(f"Erro ao buscar anamnese: {e}")
        return jsonify({'error': str(e)}), 500

@api_complete.route('/api/cliente/<id>/anamnese', methods=['POST'])
@login_required
def create_anamnese(id):
    """Criar nova anamnese"""
    try:
        db = get_db()
        if not db:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        data = request.json
        data['cliente_id'] = id
        data['data'] = datetime.now()
        data['profissional_id'] = session.get('user_id')

        result = db.anamneses.insert_one(data)

        return jsonify({
            'success': True,
            'id': str(result.inserted_id)
        })

    except Exception as e:
        logger.error(f"Erro ao criar anamnese: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ROTAS DE PRONTUÁRIO ====================

@api_complete.route('/api/cliente/<id>/prontuario', methods=['GET'])
@login_required
def get_prontuario(id):
    """Buscar prontuário do cliente"""
    try:
        db = get_db()
        if not db:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        prontuarios = list(db.prontuarios.find({'cliente_id': id}).sort('data', -1))

        return jsonify({
            'prontuarios': convert_objectid(prontuarios)
        })

    except Exception as e:
        logger.error(f"Erro ao buscar prontuário: {e}")
        return jsonify({'error': str(e)}), 500

@api_complete.route('/api/cliente/<id>/prontuario', methods=['POST'])
@login_required
def create_prontuario(id):
    """Criar novo prontuário"""
    try:
        db = get_db()
        if not db:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        data = request.json
        data['cliente_id'] = id
        data['data'] = datetime.now()
        data['profissional_id'] = session.get('user_id')

        result = db.prontuarios.insert_one(data)

        return jsonify({
            'success': True,
            'id': str(result.inserted_id)
        })

    except Exception as e:
        logger.error(f"Erro ao criar prontuário: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ROTAS DE AUDITORIA ====================

@api_complete.route('/api/auditoria', methods=['GET'])
@login_required
def get_auditoria():
    """Listar registros de auditoria"""
    try:
        db = get_db()
        if not db:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        skip = (page - 1) * limit

        auditorias = list(db.auditoria.find().sort('data', -1).skip(skip).limit(limit))
        total = db.auditoria.count_documents({})

        return jsonify({
            'auditorias': convert_objectid(auditorias),
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })

    except Exception as e:
        logger.error(f"Erro ao buscar auditoria: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ROTAS DE NOTIFICAÇÕES ====================

@api_complete.route('/api/notificacoes', methods=['GET'])
@login_required
def get_notificacoes():
    """Listar notificações do usuário"""
    try:
        db = get_db()
        if not db:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        user_id = session.get('user_id')
        notificacoes = list(db.notificacoes.find({
            'usuario_id': user_id,
            'lida': False
        }).sort('data', -1).limit(10))

        return jsonify({
            'notificacoes': convert_objectid(notificacoes)
        })

    except Exception as e:
        logger.error(f"Erro ao buscar notificações: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ROTAS DE CONFIGURAÇÕES ====================

@api_complete.route('/api/configuracoes', methods=['GET'])
@login_required
def get_configuracoes():
    """Buscar configurações do sistema"""
    try:
        db = get_db()
        if not db:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        config = db.configuracoes.find_one({'tipo': 'sistema'})

        if config:
            return jsonify(convert_objectid(config))
        else:
            return jsonify({
                'tipo': 'sistema',
                'dados': {}
            })

    except Exception as e:
        logger.error(f"Erro ao buscar configurações: {e}")
        return jsonify({'error': str(e)}), 500

@api_complete.route('/api/configuracoes', methods=['PUT'])
@login_required
def update_configuracoes():
    """Atualizar configurações do sistema"""
    try:
        db = get_db()
        if not db:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        data = request.json

        result = db.configuracoes.update_one(
            {'tipo': 'sistema'},
            {'$set': data},
            upsert=True
        )

        return jsonify({
            'success': True,
            'modified': result.modified_count
        })

    except Exception as e:
        logger.error(f"Erro ao atualizar configurações: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== RELATÓRIOS ====================

@api_complete.route('/api/relatorios/faturamento', methods=['GET'])
@login_required
def relatorio_faturamento():
    """Relatório de faturamento"""
    try:
        db = get_db()
        if not db:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        # Parâmetros
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')

        if data_inicio:
            data_inicio = datetime.fromisoformat(data_inicio)
        else:
            data_inicio = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if data_fim:
            data_fim = datetime.fromisoformat(data_fim)
        else:
            data_fim = datetime.now()

        # Faturamento por dia
        pipeline = [
            {
                '$match': {
                    'tipo': 'receita',
                    'data': {'$gte': data_inicio, '$lte': data_fim}
                }
            },
            {
                '$group': {
                    '_id': {
                        '$dateToString': {'format': '%Y-%m-%d', 'date': '$data'}
                    },
                    'total': {'$sum': '$valor'}
                }
            },
            {
                '$sort': {'_id': 1}
            }
        ]

        faturamento = list(db.financeiro.aggregate(pipeline))

        return jsonify({
            'faturamento': faturamento
        })

    except Exception as e:
        logger.error(f"Erro ao gerar relatório de faturamento: {e}")
        return jsonify({'error': str(e)}), 500

logger.info("Blueprint 'api_complete' (backend_routes_complete) criado com sucesso")
