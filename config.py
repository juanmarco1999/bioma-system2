#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA UBERABA v3.7 - Configurações Centralizadas
Desenvolvedor: Juan Marco (@juanmarco1999)
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuração base do Flask"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'bioma-2025-v3-7-ultra-secure-key-final-definitivo-completo')
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # Upload
    UPLOAD_FOLDER = '/tmp'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # MongoDB
    MONGO_USERNAME = os.getenv('MONGO_USERNAME', '')
    MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', '')
    MONGO_CLUSTER = os.getenv('MONGO_CLUSTER', '')
    MONGO_TIMEOUT = 30000  # 30s - Aumentado para produção
    MONGO_MAX_POOL_SIZE = 50  # Aumentado para suportar mais conexões simultâneas
    MONGO_MIN_POOL_SIZE = 5  # Aumentado para manter pool aquecido

    # Cache
    CACHE_TTL = 60  # segundos

    # Celery (para tarefas assíncronas)
    CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # CORS
    FRONTEND_ORIGIN = os.getenv('FRONTEND_ORIGIN', None)
    CROSS_SITE_DEV = os.getenv('CROSS_SITE_DEV', '0') == '1'


class DevelopmentConfig(Config):
    """Configuração de desenvolvimento"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Configuração de produção"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Lax'


# Mapear ambientes
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
