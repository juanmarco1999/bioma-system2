#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Authentication Routes
Rotas de autenticação: login, logout, register, current-user, permissions
"""

from flask import request, jsonify, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime
import logging

from app.auth import bp
from app.decorators import login_required, get_user_permissions

logger = logging.getLogger(__name__)


@bp.route('/login', methods=['POST'])
def login():
    """Login de usuário"""
    data = request.json
    db = current_app.config.get('DB_CONNECTION')

    logger.info(f"🔐 Login attempt: {data.get('username')}")

    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500

    try:
        user = db.users.find_one({
            '$or': [
                {'username': data['username']},
                {'email': data['username']}
            ]
        })

        if user and check_password_hash(user['password'], data['password']):
            session.permanent = True
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['role'] = user.get('role', 'admin')
            session['tipo_acesso'] = user.get('tipo_acesso', 'Admin')

            logger.info(
                f"✅ Login SUCCESS: {user['username']} "
                f"(role: {session['role']}, tipo: {session['tipo_acesso']})"
            )

            return jsonify({
                'success': True,
                'user': {
                    'id': str(user['_id']),
                    'name': user['name'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user.get('role', 'admin'),
                    'tipo_acesso': user.get('tipo_acesso', 'Admin'),
                    'theme': user.get('theme', 'light')
                }
            })

        logger.warning(f"❌ Login FAILED: {data.get('username')}")
        return jsonify({'success': False, 'message': 'Usuário ou senha inválidos'})

    except Exception as e:
        logger.error(f"❌ Login ERROR: {e}")
        return jsonify({'success': False, 'message': 'Erro no servidor'}), 500


@bp.route('/register', methods=['POST'])
def register():
    """Registro de novo usuário"""
    data = request.json
    db = current_app.config.get('DB_CONNECTION')

    logger.info(f"👤 Register attempt: {data.get('username')}")

    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500

    try:
        if db.users.find_one({'$or': [{'username': data['username']}, {'email': data['email']}]}):
            return jsonify({'success': False, 'message': 'Usuário ou email já existe'})

        user_data = {
            'name': data['name'],
            'username': data['username'],
            'email': data['email'],
            'telefone': data.get('telefone', ''),
            'password': generate_password_hash(data['password']),
            'role': 'admin',
            'tipo_acesso': data.get('tipo_acesso', 'Admin'),
            'theme': 'light',
            'created_at': datetime.now()
        }

        db.users.insert_one(user_data)
        logger.info(
            f"✅ User registered: {data['username']} "
            f"with ADMIN role and {user_data['tipo_acesso']} access"
        )

        return jsonify({'success': True, 'message': 'Conta criada com sucesso! Faça login.'})

    except Exception as e:
        logger.error(f"❌ Register ERROR: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/logout', methods=['POST'])
def logout():
    """Logout de usuário"""
    username = session.get('username', 'Unknown')
    session.clear()
    logger.info(f"🚪 Logout: {username}")
    return jsonify({'success': True})


@bp.route('/current-user')
def current_user():
    """Obter dados do usuário atual"""
    db = current_app.config.get('DB_CONNECTION')

    if 'user_id' in session and db is not None:
        try:
            user = db.users.find_one({'_id': ObjectId(session['user_id'])})
            if user:
                permissions_data = get_user_permissions()

                return jsonify({
                    'success': True,
                    'user': {
                        'id': str(user['_id']),
                        'name': user['name'],
                        'username': user['username'],
                        'email': user['email'],
                        'role': user.get('role', 'admin'),
                        'tipo_acesso': user.get('tipo_acesso', 'Admin'),
                        'theme': user.get('theme', 'light'),
                        'permissions': permissions_data.get('permissoes', [])
                    }
                })
        except Exception as e:
            logger.error(f"❌ Current user error: {e}")

    return jsonify({'success': False})


@bp.route('/permissions')
@login_required
def get_permissions_route():
    """Retorna as permissões do usuário atual"""
    permissions_data = get_user_permissions()

    if permissions_data:
        return jsonify({
            'success': True,
            'tipo_acesso': permissions_data['tipo_acesso'],
            'permissions': permissions_data['permissoes']
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Não foi possível obter permissões'
        }), 500


@bp.route('/update-theme', methods=['POST'])
@login_required
def update_theme():
    """Atualizar tema do usuário"""
    db = current_app.config.get('DB_CONNECTION')

    if db is None:
        return jsonify({'success': False}), 500

    try:
        db.users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': {'theme': request.json['theme']}}
        )
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating theme: {e}")
        return jsonify({'success': False}), 500
