#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Produtos Routes
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

from app.produtos import bp
from app.decorators import login_required, permission_required, get_user_permissions
from app.utils import convert_objectid, allowed_file, registrar_auditoria
from app.extensions import db as get_db, get_from_cache, set_in_cache

logger = logging.getLogger(__name__)

@bp.route('/api/produtos/baixo-estoque', methods=['GET'])
@login_required
def produtos_baixo_estoque():
    """Retorna produtos com estoque baixo e estatísticas"""
    try:
        # Buscar todos os produtos ativos
        produtos = list(db.produtos.find({'status': 'Ativo'}))
        
        criticos = []
        atencao = []
        normais = []
        
        for p in produtos:
            estoque_atual = int(p.get('estoque', 0))
            estoque_minimo = int(p.get('estoque_minimo', 0))
            
            diferenca = estoque_atual - estoque_minimo
            
            produto_formatado = {
                'id': str(p['_id']),
                'nome': p.get('nome', 'Sem nome'),
                'marca': p.get('marca', 'Sem marca'),
                'estoque_atual': estoque_atual,
                'estoque_minimo': estoque_minimo,
                'diferenca': diferenca,
                'preco': float(p.get('preco', 0))
            }
            
            # Classificar por nível de estoque
            if estoque_atual <= estoque_minimo:
                produto_formatado['nivel'] = 'Crítico'
                criticos.append(produto_formatado)
            elif estoque_atual < estoque_minimo * 1.5:
                produto_formatado['nivel'] = 'Atenção'
                atencao.append(produto_formatado)
            else:
                produto_formatado['nivel'] = 'Normal'
                normais.append(produto_formatado)
        
        resultado = {
            'estatisticas': {
                'criticos': len(criticos),
                'atencao': len(atencao),
                'normais': len(normais)
            },
            'produtos': criticos + atencao  # Retorna apenas os que precisam atenção
        }
        
        logger.info(f"⚠️ Estoque - Críticos: {len(criticos)}, Atenção: {len(atencao)}, Normais: {len(normais)}")
        return jsonify({'success': True, 'data': resultado})
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar produtos com baixo estoque: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/produtos/<id>', methods=['PUT'])
