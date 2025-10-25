#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA UBERABA v3.7 - Decoradores de Autenticação e Permissões
Desenvolvedor: Juan Marco (@juanmarco1999)
"""

from functools import wraps
from flask import session, request, jsonify
import logging

logger = logging.getLogger(__name__)


def login_required(f):
    """Decorator para rotas que requerem autenticação"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning(f"🚫 Unauthorized: {request.endpoint}")
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


def permission_required(*allowed_roles):
    """
    Decorator para verificar permissões do usuário

    Uso:
        @permission_required('Admin')
        @permission_required('Admin', 'Gestão')

    Tipos de acesso disponíveis:
        - Admin: Acesso total ao sistema
        - Gestão: Acesso gerencial (sem configurações críticas)
        - Profissional: Acesso limitado (agenda, atendimentos, prontuários)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                logger.warning(f"🚫 Unauthorized access attempt: {request.endpoint}")
                return jsonify({
                    'success': False,
                    'message': 'Acesso não autorizado. Faça login.'
                }), 401

            # Buscar tipo de acesso do usuário
            user_tipo_acesso = session.get('tipo_acesso', 'Profissional')

            # Verificar se o tipo de acesso do usuário está entre os permitidos
            if user_tipo_acesso not in allowed_roles:
                logger.warning(
                    f"🚫 Forbidden: {session.get('username')} ({user_tipo_acesso}) "
                    f"tried to access {request.endpoint}"
                )
                return jsonify({
                    'success': False,
                    'message': f'Acesso negado. Esta funcionalidade requer permissão de: {", ".join(allowed_roles)}'
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_user_permissions():
    """Retorna as permissões do usuário atual"""
    from application.extensions import db

    if 'user_id' not in session or db is None:
        return {
            'tipo_acesso': 'Visitante',
            'permissoes': []
        }

    user_tipo_acesso = session.get('tipo_acesso', 'Profissional')

    # Mapa de permissões por tipo de acesso
    permissions_map = {
        'Admin': [
            'clientes', 'agendamentos', 'fila', 'profissionais',
            'assistentes', 'servicos', 'produtos', 'estoque',
            'orcamento', 'prontuario', 'clube', 'importar',
            'relatorios', 'financeiro', 'sistema', 'auditoria', 'configuracoes'
        ],
        'Gestão': [
            'clientes', 'agendamentos', 'fila', 'profissionais',
            'assistentes', 'servicos', 'produtos', 'estoque',
            'orcamento', 'prontuario', 'clube', 'importar',
            'relatorios', 'financeiro'
        ],
        'Profissional': [
            'clientes', 'agendamentos', 'fila',
            'orcamento', 'prontuario'
        ]
    }

    return {
        'tipo_acesso': user_tipo_acesso,
        'permissoes': permissions_map.get(user_tipo_acesso, [])
    }
