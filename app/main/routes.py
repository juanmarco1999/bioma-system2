#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Main Routes
Rotas principais: index, health
"""

from flask import render_template, jsonify, current_app
from datetime import datetime
from app.main import bp
from app.extensions import db as get_db
import logging

logger = logging.getLogger(__name__)


@bp.route('/')
def index():
    """Página inicial do sistema"""
    return render_template('index.html')


@bp.route('/health')
def health():
    """Health check endpoint para monitoramento"""
    db = current_app.config.get('DB_CONNECTION')
    db_status = 'connected' if db is not None else 'disconnected'

    if db is not None:
        try:
            db.command('ping')
        except Exception as e:
            db_status = 'error'
            logger.error(f"Health check DB ping failed: {e}")

    return jsonify({
        'status': 'healthy',
        'time': datetime.now().isoformat(),
        'database': db_status,
        'version': '3.7.0'
    }), 200
