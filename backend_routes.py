#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BACKEND ROUTES OTIMIZADO - v4.1
Arquivo para deploy no Render com otimizações de memória
"""

from application.api.routes import bp
from flask import jsonify
import logging

logger = logging.getLogger(__name__)

# Override de rotas pesadas para economizar memória

@bp.route('/api/stream', methods=['GET'])
def stream_optimized():
    """SSE otimizado - retorna resposta simples sem streaming"""
    return jsonify({'status': 'ok', 'message': 'SSE disabled for memory optimization'}), 200


@bp.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats_optimized():
    """Dashboard stats simplificado"""
    try:
        return jsonify({
            'success': True,
            'total_clientes': 0,
            'orcamentos_mes': 0,
            'faturamento_mes': 0,
            'servicos_mes': 0,
            'produtos_vendidos': 0,
            'agendamentos_hoje': 0
        })
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return jsonify({'success': False}), 500


# Registrar otimizações
def register_optimizations(app):
    """
    Registrar otimizações para economizar memória
    """
    # Desabilitar cache de queries
    app.config['MONGODB_SETTINGS'] = {
        'connect': False,  # Lazy connection
        'serverSelectionTimeoutMS': 5000,
        'connectTimeoutMS': 5000
    }

    # Limitar tamanho de request
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max

    # Configurações de produção
    app.config.update(
        SEND_FILE_MAX_AGE_DEFAULT=300,  # Cache de 5 minutos
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

    logger.info("✅ Otimizações de memória aplicadas")