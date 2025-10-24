#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA - Backend Routes
Rotas otimizadas do backend com Blueprint
"""

from flask import Blueprint, request, jsonify, session, current_app
from bson import ObjectId
from datetime import datetime, timedelta
from functools import wraps
import logging

# Criar Blueprint
api = Blueprint('api', __name__)

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

# ==================== ROTAS DE DASHBOARD ====================

@api.route('/api/dashboard', methods=['GET'])
@login_required
def get_dashboard():
    """Retorna dados do dashboard"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Contar agendamentos de hoje
        agendamentos_hoje = db.agendamentos.count_documents({
            'data': {'$gte': hoje}
        })

        # Contar clientes ativos
        clientes_ativos = db.clientes.count_documents({
            'status': 'ativo'
        })

        # Faturamento do mês
        inicio_mes = hoje.replace(day=1)
        faturamento = db.financeiro.aggregate([
            {
                '$match': {
                    'tipo': 'receita',
                    'data': {'$gte': inicio_mes}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total': {'$sum': '$valor'}
                }
            }
        ])
        faturamento_total = list(faturamento)
        faturamento_valor = faturamento_total[0]['total'] if faturamento_total else 0

        # Serviços realizados no mês
        servicos_mes = db.agendamentos.count_documents({
            'data': {'$gte': inicio_mes},
            'status': 'concluido'
        })

        return jsonify({
            'agendamentos': agendamentos_hoje,
            'clientes': clientes_ativos,
            'faturamento': float(faturamento_valor),
            'servicos': servicos_mes
        })

    except Exception as e:
        logger.error(f"Erro ao buscar dashboard: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ROTAS DE AGENDAMENTOS ====================

@api.route('/api/agendamentos', methods=['GET'])
@login_required
def get_agendamentos():
    """Listar agendamentos"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        skip = (page - 1) * limit

        agendamentos = list(db.agendamentos.find().sort('data', -1).skip(skip).limit(limit))
        total = db.agendamentos.count_documents({})

        return jsonify({
            'agendamentos': convert_objectid(agendamentos),
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })

    except Exception as e:
        logger.error(f"Erro ao buscar agendamentos: {e}")
        return jsonify({'error': str(e)}), 500

@api.route('/api/agendamentos', methods=['POST'])
@login_required
def create_agendamento():
    """Criar novo agendamento"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        data = request.json
        data['created_at'] = datetime.now()
        data['updated_at'] = datetime.now()

        result = db.agendamentos.insert_one(data)

        return jsonify({
            'success': True,
            'id': str(result.inserted_id)
        })

    except Exception as e:
        logger.error(f"Erro ao criar agendamento: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ROTAS DE CLIENTES ====================

@api.route('/api/clientes', methods=['GET'])
@login_required
def get_clientes():
    """Listar clientes"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        skip = (page - 1) * limit

        clientes = list(db.clientes.find().sort('nome', 1).skip(skip).limit(limit))
        total = db.clientes.count_documents({})

        return jsonify({
            'clientes': convert_objectid(clientes),
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })

    except Exception as e:
        logger.error(f"Erro ao buscar clientes: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ROTAS DE SERVIÇOS ====================

@api.route('/api/servicos', methods=['GET'])
@login_required
def get_servicos():
    """Listar serviços"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        skip = (page - 1) * limit

        servicos = list(db.servicos.find().sort('nome', 1).skip(skip).limit(limit))
        total = db.servicos.count_documents({})

        return jsonify({
            'servicos': convert_objectid(servicos),
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })

    except Exception as e:
        logger.error(f"Erro ao buscar serviços: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ROTAS DE PRODUTOS ====================

@api.route('/api/produtos', methods=['GET'])
@login_required
def get_produtos():
    """Listar produtos"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        skip = (page - 1) * limit

        produtos = list(db.produtos.find().sort('nome', 1).skip(skip).limit(limit))
        total = db.produtos.count_documents({})

        return jsonify({
            'produtos': convert_objectid(produtos),
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })

    except Exception as e:
        logger.error(f"Erro ao buscar produtos: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ROTAS FINANCEIRAS ====================

@api.route('/api/financeiro/resumo', methods=['GET'])
@login_required
def get_financeiro_resumo():
    """Retorna resumo financeiro"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Receitas
        receitas = db.financeiro.aggregate([
            {
                '$match': {
                    'tipo': 'receita',
                    'data': {'$gte': inicio_mes}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total': {'$sum': '$valor'}
                }
            }
        ])
        receitas_total = list(receitas)
        receitas_valor = receitas_total[0]['total'] if receitas_total else 0

        # Despesas
        despesas = db.financeiro.aggregate([
            {
                '$match': {
                    'tipo': 'despesa',
                    'data': {'$gte': inicio_mes}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total': {'$sum': '$valor'}
                }
            }
        ])
        despesas_total = list(despesas)
        despesas_valor = despesas_total[0]['total'] if despesas_total else 0

        return jsonify({
            'receitas': float(receitas_valor),
            'despesas': float(despesas_valor),
            'saldo': float(receitas_valor - despesas_valor)
        })

    except Exception as e:
        logger.error(f"Erro ao buscar resumo financeiro: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ROTAS DE ESTOQUE ====================

@api.route('/api/estoque', methods=['GET'])
@login_required
def get_estoque():
    """Listar produtos em estoque"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'error': 'Banco de dados não conectado'}), 500

        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        skip = (page - 1) * limit

        produtos = list(db.produtos.find().sort('nome', 1).skip(skip).limit(limit))
        total = db.produtos.count_documents({})

        # Calcular estatísticas
        total_produtos = db.produtos.count_documents({})
        produtos_em_falta = db.produtos.count_documents({
            '$expr': {'$lte': ['$estoque_atual', '$estoque_minimo']}
        })

        valor_total = db.produtos.aggregate([
            {
                '$project': {
                    'valor': {'$multiply': ['$preco', '$estoque_atual']}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total': {'$sum': '$valor'}
                }
            }
        ])
        valor_total_list = list(valor_total)
        valor_total_estoque = valor_total_list[0]['total'] if valor_total_list else 0

        return jsonify({
            'produtos': convert_objectid(produtos),
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            },
            'resumo': {
                'totalProdutos': total_produtos,
                'produtosEmFalta': produtos_em_falta,
                'valorTotal': float(valor_total_estoque)
            }
        })

    except Exception as e:
        logger.error(f"Erro ao buscar estoque: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== HEALTH CHECK ====================

@api.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    try:
        db = get_db()
        if db:
            # Testar conexão
            db.command('ping')
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'degraded',
                'database': 'disconnected',
                'timestamp': datetime.now().isoformat()
            }), 503
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

logger.info("Blueprint 'api' (backend_routes) criado com sucesso")
