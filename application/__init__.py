#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA UBERABA v4.0 - Application Factory
Desenvolvedor: Juan Marco (@juanmarco1999)

Architecture Pattern: Application Factory + Flask Blueprints
Sistema consolidado e otimizado - Outubro 2025
"""

import os
import logging
from flask import Flask
from flask_cors import CORS
from config import config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """
    Application Factory Pattern

    Args:
        config_name: 'development', 'production' ou None (usa FLASK_ENV)

    Returns:
        Flask app instance configurada com todos os Blueprints
    """

    # Criar instância do Flask
    app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='../static',
        static_url_path='/static'
    )

    # Carregar configuração
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app.config.from_object(config[config_name])

    logger.info(f"🚀 Iniciando BIOMA v4.0 - Modo: {config_name}")

    # Configurar CORS
    if app.config['CROSS_SITE_DEV']:
        frontend_origin = app.config['FRONTEND_ORIGIN']
        if frontend_origin:
            CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": frontend_origin}})
            logger.info(f"🌐 CORS habilitado para: {frontend_origin}")
        else:
            CORS(app, supports_credentials=True)
            logger.info("🌐 CORS habilitado para todas as origens (DEV)")
    else:
        CORS(app, supports_credentials=True)

    # Inicializar MongoDB
    from application.extensions import init_db
    db = init_db(app)

    if db is None:
        logger.error("❌ Falha crítica: MongoDB não conectado")
        # Continua para permitir /health endpoint funcionar
    else:
        # Salvar DB no app.config para acesso dos blueprints
        app.config['DB_CONNECTION'] = db

    # Registrar Blueprints
    logger.info("📦 Registrando Blueprints...")

    # Blueprint principal com TODAS as rotas do sistema (consolidado)
    from application.api import bp as api_bp
    app.register_blueprint(api_bp)

    logger.info("✅ Blueprint API registrado (todas as rotas consolidadas)")
    logger.info("✅ Sistema consolidado e otimizado - BIOMA v4.0")
    logger.info("✅ Arquitetura modular com Application Factory Pattern")

    return app
