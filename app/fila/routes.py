#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Fila Routes
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

from app.fila import bp
from app.decorators import login_required, permission_required, get_user_permissions
from app.utils import convert_objectid, allowed_file, registrar_auditoria
from app.extensions import db as get_db, get_from_cache, set_in_cache

logger = logging.getLogger(__name__)

@bp.route('/api/fila/<id>', methods=['DELETE'])
@login_required
def delete_fila(id):
    if db is None:
        return jsonify({'success': False}), 500
    try:
        result = db.fila_atendimento.delete_one({'_id': ObjectId(id)})
        return jsonify({'success': result.deleted_count > 0})
    except:
        return jsonify({'success': False}), 500


# ==================== NOTIFICAÇÕES INTELIGENTES PARA FILA (Diretriz #10) ====================

@bp.route('/api/fila/<id>/notificar', methods=['POST'])


@bp.route('/api/fila/notificar-todos', methods=['POST'])
@login_required
def notificar_todos_fila():
    """Notificar todos os clientes na fila sobre sua posição"""
    if db is None:
        return jsonify({'success': False}), 500

    try:
        data = request.json
        tipo_notificacao = data.get('tipo', 'whatsapp')

        # Buscar todos na fila aguardando
        clientes_fila = list(db.fila_atendimento.find({'status': 'aguardando'}).sort('posicao', ASCENDING))

        notificacoes_criadas = []
        for cliente in clientes_fila:
            posicao = cliente.get('posicao', 0)
            cliente_nome = cliente.get('cliente_nome', 'Cliente')
            servico = cliente.get('servico', 'atendimento')
            telefone = cliente.get('cliente_telefone', '').replace('(', '').replace(')', '').replace('-', '').replace(' ', '')

            # Mensagem personalizada pela posição
            if posicao == 1:
                mensagem = f"🌿 BIOMA: {cliente_nome}, é sua vez! Dirija-se ao atendimento para {servico}. Obrigado!"
            elif posicao <= 3:
                mensagem = f"🌿 BIOMA: {cliente_nome}, você está próximo! Posição {posicao} na fila. Prepare-se!"
            else:
                mensagem = f"🌿 BIOMA: {cliente_nome}, você está na posição {posicao}. Aguarde, em breve será sua vez!"

            notificacao = {
                'fila_id': cliente['_id'],
                'cliente_nome': cliente_nome,
                'cliente_telefone': telefone,
                'tipo': tipo_notificacao,
                'mensagem': mensagem,
                'posicao': posicao,
                'status': 'preparada',
                'created_at': datetime.now(),
                'sent_by': session.get('username', 'sistema')
            }

            result = db.notificacoes.insert_one(notificacao)
            notificacoes_criadas.append(str(result.inserted_id))

        logger.info(f"✅ {len(notificacoes_criadas)} notificações preparadas para a fila")

        return jsonify({
            'success': True,
            'message': f'{len(notificacoes_criadas)} notificações preparadas',
            'total': len(notificacoes_criadas)
        })

    except Exception as e:
        logger.error(f"Erro ao notificar fila: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/notificacoes', methods=['GET'])
