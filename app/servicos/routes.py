#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Servicos Routes
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

from app.servicos import bp
from app.decorators import login_required, permission_required, get_user_permissions
from app.utils import convert_objectid, allowed_file, registrar_auditoria
from app.extensions import db as get_db, get_from_cache, set_in_cache

logger = logging.getLogger(__name__)

@bp.route('/api/servicos/<id>/editar', methods=['PUT'])
@login_required
def editar_servico(id):
    """Edita informações de um serviço"""
    try:
        data = request.get_json()
        
        update_data = {}
        if 'nome' in data:
            update_data['nome'] = data['nome']
        if 'preco' in data:
            update_data['preco'] = float(data['preco'])
        if 'duracao' in data:
            update_data['duracao'] = int(data['duracao'])
        if 'categoria' in data:
            update_data['categoria'] = data['categoria']
        if 'tamanho' in data:
            update_data['tamanho'] = data['tamanho']
        
        if not update_data:
            return jsonify({'success': False, 'message': 'Nenhum dado para atualizar'}), 400
        
        result = db.servicos.update_one(
            {'_id': ObjectId(id)},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Serviço atualizado com sucesso'})
        return jsonify({'success': False, 'message': 'Nenhuma alteração realizada'}), 400
    except Exception as e:
        logger.error(f"Erro ao editar serviço: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 14. Editar Produto
@bp.route('/api/produtos/<id>/editar', methods=['PUT'])


@bp.route('/api/servicos', methods=['GET'])
@login_required
def listar_servicos():
    """Lista serviços com filtro opcional por status"""
    try:
        status = request.args.get('status')
        categoria = request.args.get('categoria')
        
        query = {}
        if status:
            query['status'] = status
        if categoria and categoria != 'Todas':
            query['categoria'] = categoria
        
        servicos = list(db.servicos.find(query).sort('nome', ASCENDING))
        
        # Formatar resposta
        resultado = []
        for s in servicos:
            resultado.append({
                'id': str(s['_id']),
                'nome': s.get('nome', 'Sem nome'),
                'categoria': s.get('categoria', 'Geral'),
                'tamanho': s.get('tamanho', 'Médio'),
                'preco': float(s.get('preco', 0)),
                'duracao': int(s.get('duracao', 60)),
                'status': s.get('status', 'Ativo')
            })
        
        logger.info(f"✂️ Serviços listados: {len(resultado)} (status: {status or 'todos'})")
        return jsonify({'success': True, 'servicos': resultado})
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar serviços: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/servicos/<id>', methods=['PUT'])
