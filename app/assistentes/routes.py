#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Assistentes Routes
Auto-gerado pelo script de migração
"""

from flask import request, jsonify, session, current_app, send_file, render_template
from bson import ObjectId
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import logging
import io
import csv
import json

from app.assistentes import bp
from app.decorators import login_required, permission_required, get_user_permissions
from app.utils import convert_objectid, allowed_file, registrar_auditoria
from app.extensions import db as get_db, get_from_cache, set_in_cache

logger = logging.getLogger(__name__)

@bp.route('/api/assistentes', methods=['GET', 'POST'])
@login_required
def assistentes():
    """Gerenciar assistentes (que podem não ser profissionais ativos)"""
    if db is None:
        return jsonify({'success': False}), 500
    
    if request.method == 'GET':
        try:
            # Listar todos os assistentes
            assistentes_list = list(db.assistentes.find({}).sort('nome', ASCENDING))
            return jsonify({'success': True, 'assistentes': convert_objectid(assistentes_list)})
        except:
            return jsonify({'success': False}), 500
    
    data = request.json
    try:
        assistente_data = {
            'nome': data['nome'],
            'cpf': data.get('cpf', ''),
            'email': data.get('email', ''),
            'telefone': data.get('telefone', ''),
            'ativo': True,
            'created_at': datetime.now()
        }
        db.assistentes.insert_one(assistente_data)
        return jsonify({'success': True})
    except:
        return jsonify({'success': False}), 500

@bp.route('/api/assistentes/<id>', methods=['DELETE'])
