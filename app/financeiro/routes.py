#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Financeiro Routes
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

from app.financeiro import bp
from app.decorators import login_required, permission_required, get_user_permissions
from app.utils import convert_objectid, allowed_file, registrar_auditoria
from app.extensions import db as get_db, get_from_cache, set_in_cache

logger = logging.getLogger(__name__)

@bp.route('/api/financeiro/dashboard', methods=['GET'])
@login_required
@permission_required('Admin', 'Gestão')
def financeiro_dashboard():
    """Dashboard financeiro com comissões, despesas e lucro (Admin/Gestão)"""
    if db is None:
        return jsonify({'success': False}), 500

    try:
        # Filtros opcionais
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')

        # Query base
        query = {}
        if data_inicio and data_fim:
            query['created_at'] = {
                '$gte': datetime.fromisoformat(data_inicio),
                '$lte': datetime.fromisoformat(data_fim)
            }

        # Total de receitas (orçamentos aprovados)
        orcamentos_aprovados = list(db.orcamentos.find({**query, 'status': 'Aprovado'}))
        receita_total = sum(o.get('total_final', 0) for o in orcamentos_aprovados)

        # Total de comissões
        comissoes_total = sum(o.get('total_comissoes', 0) for o in orcamentos_aprovados)

        # Total de despesas
        despesas = list(db.despesas.find(query))
        despesas_total = sum(d.get('valor', 0) for d in despesas)

        # Lucro líquido
        lucro_liquido = receita_total - comissoes_total - despesas_total

        # Comissões por profissional
        comissoes_por_profissional = {}
        for orcamento in orcamentos_aprovados:
            for prof in orcamento.get('profissionais_vinculados', []):
                prof_id = str(prof.get('profissional_id', ''))
                prof_nome = prof.get('nome', 'N/A')
                comissao_valor = prof.get('comissao_valor', 0)

                if prof_id not in comissoes_por_profissional:
                    comissoes_por_profissional[prof_id] = {
                        'nome': prof_nome,
                        'total': 0,
                        'quantidade': 0
                    }

                comissoes_por_profissional[prof_id]['total'] += comissao_valor
                comissoes_por_profissional[prof_id]['quantidade'] += 1

        # Despesas por categoria
        despesas_por_categoria = {}
        for despesa in despesas:
            categoria = despesa.get('categoria', 'Outros')
            if categoria not in despesas_por_categoria:
                despesas_por_categoria[categoria] = 0
            despesas_por_categoria[categoria] += despesa.get('valor', 0)

        return jsonify({
            'success': True,
            'financeiro': {
                'receita_total': receita_total,
                'comissoes_total': comissoes_total,
                'despesas_total': despesas_total,
                'lucro_liquido': lucro_liquido,
                'margem_lucro_perc': (lucro_liquido / receita_total * 100) if receita_total > 0 else 0,
                'comissoes_por_profissional': list(comissoes_por_profissional.values()),
                'despesas_por_categoria': despesas_por_categoria,
                'total_orcamentos': len(orcamentos_aprovados),
                'ticket_medio': receita_total / len(orcamentos_aprovados) if orcamentos_aprovados else 0
            }
        })

    except Exception as e:
        logger.error(f"Erro no dashboard financeiro: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/financeiro/despesas', methods=['GET', 'POST'])


@bp.route('/api/financeiro/despesas/<id>', methods=['PUT', 'DELETE'])
@login_required
@permission_required('Admin')
def handle_despesa(id):
    """Atualizar ou deletar despesa (Admin only)"""
    if db is None:
        return jsonify({'success': False}), 500

    try:
        if request.method == 'PUT':
            data = request.json
            update_data = {
                'descricao': data.get('descricao'),
                'categoria': data.get('categoria'),
                'valor': float(data.get('valor', 0)),
                'data': datetime.fromisoformat(data.get('data')) if data.get('data') else None,
                'forma_pagamento': data.get('forma_pagamento'),
                'observacoes': data.get('observacoes', ''),
                'updated_at': datetime.now(),
                'updated_by': session.get('username', 'sistema')
            }

            # Remover campos None
            update_data = {k: v for k, v in update_data.items() if v is not None}

            db.despesas.update_one({'_id': ObjectId(id)}, {'$set': update_data})
            logger.info(f"✅ Despesa {id} atualizada")
            return jsonify({'success': True, 'message': 'Despesa atualizada com sucesso'})

        elif request.method == 'DELETE':
            db.despesas.delete_one({'_id': ObjectId(id)})
            logger.info(f"🗑️ Despesa {id} deletada")
            return jsonify({'success': True, 'message': 'Despesa deletada com sucesso'})

    except Exception as e:
        logger.error(f"Erro ao manipular despesa: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/financeiro/relatorio', methods=['GET'])


@bp.route('/api/financeiro/receitas', methods=['GET'])
@login_required
@permission_required('Admin', 'Gestão')
def financeiro_receitas():
    """Listar receitas - orçamentos aprovados (Admin/Gestão)"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500

    try:
        # Filtros opcionais
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        cliente_id = request.args.get('cliente_id')

        # Query base para orçamentos aprovados
        query = {'status': 'Aprovado'}

        # Aplicar filtros
        if data_inicio and data_fim:
            query['created_at'] = {
                '$gte': datetime.fromisoformat(data_inicio),
                '$lte': datetime.fromisoformat(data_fim)
            }

        if cliente_id:
            query['cliente_id'] = cliente_id

        # Buscar orçamentos aprovados
        orcamentos = list(db.orcamentos.find(query).sort('created_at', DESCENDING))

        # Formatar receitas
        receitas = []
        total = 0
        for orc in orcamentos:
            valor = orc.get('total_final', 0)
            total += valor

            receitas.append({
                '_id': str(orc['_id']),
                'cliente_nome': orc.get('cliente_nome', 'N/A'),
                'cliente_cpf': orc.get('cliente_cpf', 'N/A'),
                'data': orc.get('created_at', datetime.now()).strftime('%Y-%m-%d') if isinstance(orc.get('created_at'), datetime) else orc.get('data', 'N/A'),
                'valor': valor,
                'forma_pagamento': orc.get('forma_pagamento', 'N/A'),
                'status': orc.get('status', 'N/A'),
                'observacoes': orc.get('observacoes', '')
            })

        logger.info(f"✅ Listadas {len(receitas)} receitas - Total: R$ {total:.2f}")
        return jsonify({
            'success': True,
            'receitas': receitas,
            'total': round(total, 2),
            'quantidade': len(receitas)
        })

    except Exception as e:
        logger.error(f"Erro ao listar receitas: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/financeiro/comissoes', methods=['GET'])
