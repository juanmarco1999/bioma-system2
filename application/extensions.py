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

# ========== SISTEMA DE CACHE v7.2 AVANÇADO ==========
from time import time
from functools import wraps
import hashlib
import json

# Cache com TTL por chave
request_cache = {}

class CacheManager:
    """Gerenciador de cache avançado com TTL configurável"""

    @staticmethod
    def get(key, ttl=60):
        """Buscar do cache se ainda válido"""
        if key in request_cache:
            data, timestamp, cache_ttl = request_cache[key]
            if time() - timestamp < cache_ttl:
                logger.debug(f"Cache HIT: {key} (age: {int(time() - timestamp)}s)")
                return data
            else:
                del request_cache[key]
                logger.debug(f"Cache EXPIRED: {key}")
        return None

    @staticmethod
    def set(key, data, ttl=60):
        """Salvar no cache com TTL específico"""
        request_cache[key] = (data, time(), ttl)
        logger.debug(f"Cache SET: {key} (ttl: {ttl}s)")

    @staticmethod
    def invalidate(pattern=None):
        """Invalidar cache por padrão"""
        if pattern is None:
            count = len(request_cache)
            request_cache.clear()
            logger.info(f"Cache CLEARED: {count} entradas removidas")
        else:
            removed = 0
            keys_to_remove = [k for k in request_cache.keys() if pattern in k]
            for key in keys_to_remove:
                del request_cache[key]
                removed += 1
            if removed > 0:
                logger.info(f"Cache INVALIDATED: {removed} entradas com padrão '{pattern}'")

    @staticmethod
    def get_cache_key(endpoint, args=None):
        """Gera chave de cache única baseada em endpoint e argumentos"""
        if args:
            args_str = json.dumps(args, sort_keys=True)
            hash_suffix = hashlib.md5(args_str.encode()).hexdigest()[:8]
            return f"{endpoint}:{hash_suffix}"
        return endpoint

# Funções legadas (compatibilidade)
def get_from_cache(key):
    """Buscar do cache se ainda válido (função legada)"""
    return CacheManager.get(key)

def set_in_cache(key, data):
    """Salvar no cache (função legada)"""
    CacheManager.set(key, data)


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
        # Índice único de CPF com nome específico e sparse=True para evitar conflitos
        # sparse=True permite documentos sem CPF (útil para clientes sem CPF cadastrado)
        try:
            db.clientes.create_index(
                [("cpf", 1)],
                unique=True,
                background=True,
                sparse=True,
                name="cpf_unique_idx"
            )
        except Exception as idx_error:
            # Se índice já existe, não é erro crítico
            logger.warning(f"⚠️ Índice CPF já existe ou erro: {idx_error}")

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

        # Índices para ORÇAMENTOS (status + temporal) v7.2 OTIMIZADO
        db.orcamentos.create_index([("status", 1)], background=True)  # Sozinho - MUITO usado
        db.orcamentos.create_index([("cliente_cpf", 1)], background=True)  # CRÍTICO - N+1 query fix
        db.orcamentos.create_index([("created_at", -1)], background=True)  # Ordenação
        db.orcamentos.create_index([("status", 1), ("created_at", -1)], background=True)  # Compound
        db.orcamentos.create_index([("cliente_id", 1), ("created_at", -1)], background=True)

        # Índices para PRODUTOS/ESTOQUE (busca + estoque baixo) v7.2 OTIMIZADO
        db.produtos.create_index([("status", 1)], background=True)  # CRÍTICO - muito usado
        db.produtos.create_index([("nome", 1)], background=True)
        db.produtos.create_index([("sku", 1)], background=True)
        db.produtos.create_index([("estoque", 1)], background=True)  # Para alertas (estoque baixo)
        db.produtos.create_index([("estoque_atual", 1)], background=True)  # Fallback
        db.produtos.create_index([("categoria", 1), ("estoque", 1)], background=True)

        # Índices para SERVICOS v7.2
        db.servicos.create_index([("categoria", 1)], background=True)
        db.servicos.create_index([("nome", 1)], background=True)

        # Índices para PROFISSIONAIS v7.2
        db.profissionais.create_index([("ativo", 1)], background=True)
        db.profissionais.create_index([("nome", 1)], background=True)

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
