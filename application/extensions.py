#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA UBERABA v3.7 - Extensões e Inicializações
Desenvolvedor: Juan Marco (@juanmarco1999)
"""

import os
import logging
from pymongo import MongoClient

logger = logging.getLogger(__name__)

# Database instance (será inicializada no __init__.py)
db = None

# Cache simples para requisições GET
request_cache = {}


def get_from_cache(key):
    """Buscar do cache se ainda válido"""
    from time import time
    from flask import current_app

    ttl = current_app.config.get('CACHE_TTL', 60)

    if key in request_cache:
        data, timestamp = request_cache[key]
        if time() - timestamp < ttl:
            return data
        else:
            del request_cache[key]
    return None


def set_in_cache(key, data):
    """Salvar no cache"""
    from time import time
    request_cache[key] = (data, time())


def init_db(app):
    """Inicializar conexão MongoDB"""
    global db
    import urllib.parse

    try:
        username = urllib.parse.quote_plus(app.config['MONGO_USERNAME'])
        password = urllib.parse.quote_plus(app.config['MONGO_PASSWORD'])
        cluster = app.config['MONGO_CLUSTER']

        if not all([username, password, cluster]):
            logger.error("❌ MongoDB credentials missing")
            return None

        uri = f"mongodb+srv://{username}:{password}@{cluster}/bioma_db?retryWrites=true&w=majority&appName=Juan-Analytics-DBServer"

        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=app.config['MONGO_TIMEOUT'],
            connectTimeoutMS=app.config['MONGO_TIMEOUT'],
            socketTimeoutMS=app.config['MONGO_TIMEOUT'],
            maxPoolSize=app.config['MONGO_MAX_POOL_SIZE'],
            minPoolSize=app.config['MONGO_MIN_POOL_SIZE'],
            maxIdleTimeMS=30000
        )

        # Ping para testar conexão
        client.admin.command('ping')
        db = client.bioma_db
        logger.info("✅ MongoDB Connected")

        # Criar índices estratégicos (Seção 4 do PDF)
        create_strategic_indexes()

        return db
    except Exception as e:
        logger.error(f"❌ MongoDB Failed: {e}")
        return None


def create_strategic_indexes():
    """Criar índices estratégicos no MongoDB (Seção 4 do PDF - Regra ESR)"""
    if db is None:
        return

    try:
        logger.info("📊 Criando índices estratégicos...")

        # Índices para CLIENTES (busca rápida + ordenação)
        db.clientes.create_index([("cpf", 1)], unique=True, background=True)
        db.clientes.create_index([("nome", 1)], background=True)
        db.clientes.create_index([("email", 1)], background=True)
        db.clientes.create_index([("telefone", 1)], background=True)
        # Índice composto para busca global (ESR: Equality, Sort, Range)
        db.clientes.create_index([("nome", 1), ("cpf", 1), ("email", 1)], background=True)

        # Índices para AGENDAMENTOS (queries temporais + profissional)
        db.agendamentos.create_index([("data", -1)], background=True)
        db.agendamentos.create_index([("profissional_id", 1), ("data", -1)], background=True)
        db.agendamentos.create_index([("status", 1), ("data", -1)], background=True)
        # Índice composto para detecção de conflitos
        db.agendamentos.create_index([("profissional_id", 1), ("data", 1), ("horario", 1)], background=True)

        # Índices para ORÇAMENTOS (status + temporal)
        db.orcamentos.create_index([("status", 1), ("created_at", -1)], background=True)
        db.orcamentos.create_index([("cliente_id", 1), ("created_at", -1)], background=True)

        # Índices para PRODUTOS/ESTOQUE (busca + estoque baixo)
        db.produtos.create_index([("nome", 1)], background=True)
        db.produtos.create_index([("sku", 1)], background=True)
        db.produtos.create_index([("estoque_atual", 1)], background=True)  # Para alertas
        db.produtos.create_index([("categoria", 1), ("estoque_atual", 1)], background=True)

        # Índices para MOVIMENTAÇÕES DE ESTOQUE
        db.estoque_movimentacoes.create_index([("tipo", 1), ("created_at", -1)], background=True)
        db.estoque_movimentacoes.create_index([("produto_id", 1), ("created_at", -1)], background=True)

        # Índices para FINANCEIRO
        db.despesas.create_index([("data_vencimento", -1)], background=True)
        db.despesas.create_index([("status", 1), ("data_vencimento", -1)], background=True)

        # Índices para AUDITORIA (temporal)
        db.auditoria.create_index([("timestamp", -1)], background=True)
        db.auditoria.create_index([("usuario_id", 1), ("timestamp", -1)], background=True)

        logger.info("✅ Índices estratégicos criados com sucesso")

    except Exception as e:
        logger.warning(f"⚠️ Erro ao criar índices: {e}")
