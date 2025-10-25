#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Relatorios Routes
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

from app.relatorios import bp
from app.decorators import login_required, permission_required, get_user_permissions
from app.utils import convert_objectid, allowed_file, registrar_auditoria
from app.extensions import db as get_db, get_from_cache, set_in_cache

logger = logging.getLogger(__name__)

@bp.route('/api/relatorios/mapa-calor', methods=['GET'])
@login_required
def mapa_calor():
    """Retorna dados melhorados para mapa de calor de movimentação (Diretriz #5)"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500

    try:
        # Parâmetros configuráveis
        dias = int(request.args.get('dias', 90))
        incluir_faturamento = request.args.get('faturamento', 'true').lower() == 'true'
        incluir_clientes = request.args.get('clientes', 'true').lower() == 'true'

        # Período
        data_inicio = datetime.now() - timedelta(days=dias)
        data_fim = datetime.now()

        # Pipeline de agregação otimizado
        pipeline_base = [
            {'$match': {'created_at': {'$gte': data_inicio, '$lte': data_fim}}},
            {'$group': {
                '_id': {
                    '$dateToString': {'format': '%Y-%m-%d', 'date': '$created_at'}
                },
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id': 1}}
        ]

        # Buscar dados de diferentes collections
        agendamentos_data = list(db.agendamentos.aggregate(pipeline_base))
        orcamentos_data = list(db.orcamentos.aggregate(pipeline_base))

        # Pipeline com faturamento para orçamentos aprovados
        pipeline_faturamento = [
            {'$match': {
                'created_at': {'$gte': data_inicio, '$lte': data_fim},
                'status': 'Aprovado'
            }},
            {'$group': {
                '_id': {
                    '$dateToString': {'format': '%Y-%m-%d', 'date': '$created_at'}
                },
                'faturamento': {'$sum': '$total_final'},
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id': 1}}
        ]

        faturamento_data = list(db.orcamentos.aggregate(pipeline_faturamento)) if incluir_faturamento else []

        # Pipeline para novos clientes
        pipeline_clientes = [
            {'$match': {'created_at': {'$gte': data_inicio, '$lte': data_fim}}},
            {'$group': {
                '_id': {
                    '$dateToString': {'format': '%Y-%m-%d', 'date': '$created_at'}
                },
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id': 1}}
        ]

        clientes_data = list(db.clientes.aggregate(pipeline_clientes)) if incluir_clientes else []

        # Combinar todos os dados em um mapa por dia
        dias_map = {}

        # Inicializar todos os dias do período
        current_date = data_inicio
        while current_date <= data_fim:
            dia_str = current_date.strftime('%Y-%m-%d')
            dias_map[dia_str] = {
                'data': dia_str,
                'agendamentos': 0,
                'orcamentos': 0,
                'faturamento': 0,
                'novos_clientes': 0,
                'intensidade_total': 0
            }
            current_date += timedelta(days=1)

        # Preencher agendamentos
        for item in agendamentos_data:
            dia = item['_id']
            if dia in dias_map:
                dias_map[dia]['agendamentos'] = item['count']
                dias_map[dia]['intensidade_total'] += item['count']

        # Preencher orçamentos
        for item in orcamentos_data:
            dia = item['_id']
            if dia in dias_map:
                dias_map[dia]['orcamentos'] = item['count']
                dias_map[dia]['intensidade_total'] += item['count']

        # Preencher faturamento
        for item in faturamento_data:
            dia = item['_id']
            if dia in dias_map:
                dias_map[dia]['faturamento'] = round(item['faturamento'], 2)
                # Adicionar peso ao faturamento para intensidade
                dias_map[dia]['intensidade_total'] += item['count'] * 2  # Peso maior para vendas

        # Preencher novos clientes
        for item in clientes_data:
            dia = item['_id']
            if dia in dias_map:
                dias_map[dia]['novos_clientes'] = item['count']
                dias_map[dia]['intensidade_total'] += item['count']

        # Converter para lista ordenada
        dados = sorted(dias_map.values(), key=lambda x: x['data'])

        # Calcular estatísticas gerais
        total_agendamentos = sum(d['agendamentos'] for d in dados)
        total_orcamentos = sum(d['orcamentos'] for d in dados)
        total_faturamento = sum(d['faturamento'] for d in dados)
        total_clientes = sum(d['novos_clientes'] for d in dados)

        # Dia mais movimentado
        dia_mais_movimentado = max(dados, key=lambda x: x['intensidade_total']) if dados else None
        dia_maior_faturamento = max(dados, key=lambda x: x['faturamento']) if dados and incluir_faturamento else None

        return jsonify({
            'success': True,
            'dados': dados,
            'periodo': {
                'inicio': data_inicio.strftime('%Y-%m-%d'),
                'fim': data_fim.strftime('%Y-%m-%d'),
                'total_dias': dias
            },
            'estatisticas': {
                'total_agendamentos': total_agendamentos,
                'total_orcamentos': total_orcamentos,
                'total_faturamento': total_faturamento,
                'total_novos_clientes': total_clientes,
                'media_diaria_agendamentos': round(total_agendamentos / dias, 2) if dias > 0 else 0,
                'dia_mais_movimentado': dia_mais_movimentado,
                'dia_maior_faturamento': dia_maior_faturamento
            }
        })

    except Exception as e:
        logger.error(f"Erro ao gerar mapa de calor: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================================
# NOVOS ENDPOINTS PARA GRÁFICOS AVANÇADOS (Roadmap Section V - Relatórios)
# ============================================================================

@bp.route('/api/relatorios/vendas-por-mes', methods=['GET'])


@bp.route('/api/relatorios/servicos-top', methods=['GET'])
@login_required
@permission_required('Admin', 'Gestão')
def relatorio_servicos_top():
    """Top serviços por faturamento e quantidade (Admin/Gestão)"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500

    try:
        # Parâmetros
        dias = int(request.args.get('dias', 90))
        limite = int(request.args.get('limite', 10))
        data_inicio = datetime.now() - timedelta(days=dias)

        # Buscar orçamentos aprovados
        orcamentos = list(db.orcamentos.find({
            'status': 'Aprovado',
            'created_at': {'$gte': data_inicio}
        }))

        # Agregar serviços
        servicos_map = {}
        for orc in orcamentos:
            for serv in orc.get('servicos', []):
                serv_id = serv.get('id')
                if serv_id:
                    if serv_id not in servicos_map:
                        servicos_map[serv_id] = {
                            'nome': serv.get('nome', 'N/A'),
                            'quantidade': 0,
                            'faturamento': 0
                        }
                    servicos_map[serv_id]['quantidade'] += serv.get('qtd', 1)
                    servicos_map[serv_id]['faturamento'] += serv.get('total', 0)

        # Ordenar por faturamento
        servicos_ranking = sorted(
            servicos_map.values(),
            key=lambda x: x['faturamento'],
            reverse=True
        )[:limite]

        # Formatar para Chart.js (horizontal bar chart)
        labels = [s['nome'] for s in servicos_ranking]
        faturamento = [round(s['faturamento'], 2) for s in servicos_ranking]
        quantidade = [s['quantidade'] for s in servicos_ranking]

        return jsonify({
            'success': True,
            'chart_data': {
                'labels': labels,
                'datasets': [
                    {
                        'label': 'Faturamento (R$)',
                        'data': faturamento,
                        'backgroundColor': 'rgba(255, 159, 64, 0.7)',
                        'borderColor': 'rgba(255, 159, 64, 1)',
                        'borderWidth': 1
                    }
                ]
            },
            'quantidade_execucoes': quantidade,
            'total_servicos': len(servicos_map),
            'faturamento_total': round(sum(s['faturamento'] for s in servicos_map.values()), 2)
        })

    except Exception as e:
        logger.error(f"Erro ao gerar relatório de top serviços: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/relatorios/profissionais-desempenho', methods=['GET'])


@bp.route('/api/relatorios/produtos-top', methods=['GET'])
@login_required
@permission_required('Admin', 'Gestão')
def relatorio_produtos_top():
    """Top produtos por faturamento e quantidade vendida (Admin/Gestão)"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500

    try:
        # Parâmetros
        dias = int(request.args.get('dias', 90))
        limite = int(request.args.get('limite', 10))
        data_inicio = datetime.now() - timedelta(days=dias)

        # Buscar orçamentos aprovados
        orcamentos = list(db.orcamentos.find({
            'status': 'Aprovado',
            'created_at': {'$gte': data_inicio}
        }))

        # Agregar produtos
        produtos_map = {}
        for orc in orcamentos:
            for prod in orc.get('produtos', []):
                prod_id = prod.get('id')
                if prod_id:
                    if prod_id not in produtos_map:
                        produtos_map[prod_id] = {
                            'nome': prod.get('nome', 'N/A'),
                            'quantidade': 0,
                            'faturamento': 0
                        }
                    produtos_map[prod_id]['quantidade'] += prod.get('qtd', 1)
                    produtos_map[prod_id]['faturamento'] += prod.get('total', 0)

        # Ordenar por faturamento
        produtos_ranking = sorted(
            produtos_map.values(),
            key=lambda x: x['faturamento'],
            reverse=True
        )[:limite]

        # Formatar para Chart.js
        labels = [p['nome'] for p in produtos_ranking]
        faturamento = [round(p['faturamento'], 2) for p in produtos_ranking]
        quantidade = [p['quantidade'] for p in produtos_ranking]

        return jsonify({
            'success': True,
            'chart_data': {
                'labels': labels,
                'datasets': [
                    {
                        'label': 'Faturamento (R$)',
                        'data': faturamento,
                        'backgroundColor': 'rgba(255, 99, 132, 0.7)',
                        'borderColor': 'rgba(255, 99, 132, 1)',
                        'borderWidth': 1
                    }
                ]
            },
            'quantidade_vendida': quantidade,
            'total_produtos': len(produtos_map),
            'faturamento_total': round(sum(p['faturamento'] for p in produtos_map.values()), 2)
        })

    except Exception as e:
        logger.error(f"Erro ao gerar relatório de top produtos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/relatorios/taxa-conversao', methods=['GET'])
