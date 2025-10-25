#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Profissionais Routes
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

from app.profissionais import bp
from app.decorators import login_required, permission_required, get_user_permissions
from app.utils import convert_objectid, allowed_file, registrar_auditoria
from app.extensions import db as get_db, get_from_cache, set_in_cache

logger = logging.getLogger(__name__)

@bp.route('/api/profissionais', methods=['GET', 'POST'])
@login_required
def profissionais():
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    if request.method == 'GET':
        cache_key = 'profissionais_list'
        cached = get_from_cache(cache_key)
        if cached:
            return jsonify(cached)
        
        try:
            profs = list(db.profissionais.find({}).sort('nome', ASCENDING).limit(500))

            # Agregar métricas de avaliação para exibição rápida na lista
            avaliacoes_map = {}
            try:
                stats_pipeline = [
                    {'$group': {
                        '_id': '$profissional_id',
                        'media': {'$avg': '$nota'},
                        'total': {'$sum': 1}
                    }}
                ]
                for stat in db.profissionais_avaliacoes.aggregate(stats_pipeline):
                    avaliacoes_map[stat['_id']] = {
                        'media': round(stat.get('media', 0), 2),
                        'total': stat.get('total', 0)
                    }
            except Exception as agg_error:
                logger.debug(f"Falha ao agregar avaliações de profissionais: {agg_error}")

            for prof in profs:
                assistente_info = get_assistente_details(
                    prof.get('assistente_id'),
                    prof.get('assistente_tipo')
                )
                if assistente_info:
                    prof['assistente'] = {
                        'id': assistente_info.get('_id'),
                        'nome': assistente_info.get('nome'),
                        'tipo': assistente_info.get('tipo_origem'),
                        'foto_url': assistente_info.get('foto_url', '')
                    }
                # Avaliações agregadas
                stat = avaliacoes_map.get(str(prof.get('_id')))
                if stat:
                    prof['avaliacao_media'] = stat['media']
                    prof['avaliacoes_total'] = stat['total']
                else:
                    prof['avaliacao_media'] = 0
                    prof['avaliacoes_total'] = 0

            result = {'success': True, 'profissionais': convert_objectid(profs)}
            set_in_cache(cache_key, result)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Erro ao listar profissionais: {e}")
            return jsonify({'success': False, 'message': 'Erro ao carregar profissionais'}), 500
    
    data = request.json
    try:
        assistente_id = data.get('assistente_id') or None
        assistente_tipo = data.get('assistente_tipo')
        if assistente_id:
            assistente_id = str(assistente_id)
        if assistente_tipo not in {'profissional', 'assistente', None}:
            assistente_tipo = None

        profissional_data = {
            'nome': data['nome'],
            'cpf': data['cpf'],
            'email': data.get('email', ''),
            'telefone': data.get('telefone', ''),
            'especialidade': data.get('especialidade', ''),
            'comissao_perc': float(data.get('comissao_perc', 0)),
            'foto_url': data.get('foto_url', ''),
            'assistente_id': assistente_id,
            'assistente_tipo': assistente_tipo if assistente_id else None,
            'comissao_assistente_perc': float(data.get('comissao_assistente_perc', 0)),
            'ativo': True,
            'created_at': datetime.now()
        }
        db.profissionais.insert_one(profissional_data)
        logger.info(f"✅ Profissional cadastrado: {profissional_data['nome']}")
        return jsonify({'success': True, 'message': 'Profissional cadastrado com sucesso'})
    except Exception as e:
        logger.error(f"Erro ao cadastrar profissional: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/api/profissionais/<id>', methods=['DELETE'])


@bp.route('/api/profissionais/<id>', methods=['GET'])
@login_required
def get_profissional(id):
    """Visualizar um profissional especifico com estatisticas completas"""
    if db is None:
        return jsonify({'success': False}), 500
    try:
        profissional = db.profissionais.find_one({'_id': ObjectId(id)})
        if not profissional:
            return jsonify({'success': False, 'message': 'Profissional nao encontrado'}), 404

        profissional_id_str = str(profissional['_id'])

        orcamentos_prof = list(db.orcamentos.find({
            'servicos.profissional_id': profissional_id_str
        }))

        total_comissao = 0.0
        total_comissao_assistente = 0.0
        servicos_realizados = 0
        orcamentos_aprovados = 0
        desempenho_mensal = {}
        multicomissao_detalhes = []

        assistente_info = get_assistente_details(
            profissional.get('assistente_id'),
            profissional.get('assistente_tipo')
        )

        comissao_prof_perc = float(profissional.get('comissao_perc', 0))
        comissao_assistente_padrao = float(profissional.get('comissao_assistente_perc', 0))

        for orc in orcamentos_prof:
            data_orc = orc.get('created_at', datetime.now())
            mes_key = data_orc.strftime('%Y-%m') if isinstance(data_orc, datetime) else 'desconhecido'
            if mes_key not in desempenho_mensal:
                desempenho_mensal[mes_key] = {
                    'mes': mes_key,
                    'comissao_profissional': 0.0,
                    'comissao_assistente': 0.0,
                    'servicos': 0,
                    'faturamento': 0.0
                }

            if orc.get('status') == 'Aprovado':
                orcamentos_aprovados += 1
                desempenho_mensal[mes_key]['faturamento'] += orc.get('total_final', 0)

            for servico in orc.get('servicos', []):
                if servico.get('profissional_id') != profissional_id_str:
                    continue

                quantidade = servico.get('qtd', 1) or 1
                valor_servico = servico.get('total', 0) or 0
                servicos_realizados += quantidade

                comissao_valor = valor_servico * (comissao_prof_perc / 100)
                total_comissao += comissao_valor
                desempenho_mensal[mes_key]['comissao_profissional'] += comissao_valor
                desempenho_mensal[mes_key]['servicos'] += quantidade

                assistente_item = None
                assistente_perc = servico.get('assistente_comissao_perc')
                assistente_servico = servico.get('assistente_servico') or servico.get('nome')

                if servico.get('assistente_id'):
                    assistente_item = get_assistente_details(
                        servico.get('assistente_id'),
                        servico.get('assistente_tipo')
                    )
                    if assistente_perc is None:
                        assistente_perc = servico.get('assistente_comissao_perc', comissao_assistente_padrao)
                elif assistente_info:
                    assistente_item = assistente_info
                    if assistente_perc is None:
                        assistente_perc = comissao_assistente_padrao

                comissao_assistente_valor = 0.0
                if assistente_item and assistente_perc:
                    assistente_perc = float(assistente_perc)
                    comissao_assistente_valor = comissao_valor * (assistente_perc / 100)
                    total_comissao_assistente += comissao_assistente_valor
                    desempenho_mensal[mes_key]['comissao_assistente'] += comissao_assistente_valor

                multicomissao_detalhes.append({
                    'orcamento_id': str(orc['_id']),
                    'orcamento_numero': orc.get('numero'),
                    'cliente': orc.get('cliente_nome'),
                    'status': orc.get('status'),
                    'data': data_orc.isoformat() if isinstance(data_orc, datetime) else data_orc,
                    'servico': servico.get('nome'),
                    'valor_servico': valor_servico,
                    'comissao_profissional': comissao_valor,
                    'comissao_assistente': comissao_assistente_valor,
                    'assistente_nome': assistente_item.get('nome') if assistente_item else None,
                    'assistente_tipo': assistente_item.get('tipo_origem') if assistente_item else None,
                    'descricao': f"Profissional {profissional.get('nome')} - {servico.get('nome')}" + (
                        f" | Assistente {assistente_item.get('nome')} - {assistente_servico}" if assistente_item else ''
                    )
                })

        desempenho_ordenado = sorted(desempenho_mensal.items())
        grafico_labels = [item[0] for item in desempenho_ordenado]
        grafico_dados_prof = [round(item[1]['comissao_profissional'], 2) for item in desempenho_ordenado]
        grafico_dados_assist = [round(item[1]['comissao_assistente'], 2) for item in desempenho_ordenado]
        grafico_servicos = [item[1]['servicos'] for item in desempenho_ordenado]

        avaliacoes = []
        try:
            avaliacoes = list(db.profissionais_avaliacoes.find(
                {'profissional_id': profissional_id_str}
            ).sort('created_at', DESCENDING).limit(20))
        except Exception as avaliacao_error:
            logger.debug(f"Falha ao carregar avaliacoes do profissional {id}: {avaliacao_error}")

        if assistente_info:
            profissional['assistente'] = assistente_info

        profissional['estatisticas'] = {
            'total_comissao': round(total_comissao, 2),
            'total_comissao_assistente': round(total_comissao_assistente, 2),
            'servicos_realizados': servicos_realizados,
            'total_orcamentos': len(orcamentos_prof),
            'orcamentos_aprovados': orcamentos_aprovados,
            'comissao_media': round(total_comissao / servicos_realizados, 2) if servicos_realizados else 0
        }

        profissional['desempenho'] = {
            'labels': grafico_labels,
            'comissao_profissional': grafico_dados_prof,
            'comissao_assistente': grafico_dados_assist,
            'servicos': grafico_servicos
        }

        profissional['multicomissao'] = multicomissao_detalhes
        profissional['avaliacoes'] = convert_objectid(avaliacoes)

        return jsonify({'success': True, 'profissional': convert_objectid(profissional)})
    except Exception as e:
        logger.error(f"Erro ao buscar profissional: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/api/comissao/calcular', methods=['POST'])


@bp.route('/api/profissionais/<id>/avaliacoes', methods=['GET', 'POST'])
@login_required
def profissional_avaliacoes(id):
    """Registrar e listar avaliacoes de profissionais."""
    if db is None:
        return jsonify({'success': False}), 500

    try:
        ObjectId(id)
    except Exception:
        return jsonify({'success': False, 'message': 'ID de profissional invalido'}), 400

    if request.method == 'GET':
        try:
            avaliacoes = list(db.profissionais_avaliacoes.find(
                {'profissional_id': id}
            ).sort('created_at', DESCENDING).limit(50))
            return jsonify({'success': True, 'avaliacoes': convert_objectid(avaliacoes)})
        except Exception as e:
            logger.error(f"Erro ao listar avaliacoes: {e}")
            return jsonify({'success': False, 'message': 'Erro ao listar avaliacoes'}), 500

    data = request.json or {}
    try:
        nota = float(data.get('nota', 0))
        nota = max(0, min(5, nota))
        avaliacao = {
            'profissional_id': id,
            'nota': nota,
            'comentario': data.get('comentario', '').strip(),
            'autor': data.get('autor', session.get('username', 'anonimo')),
            'created_at': datetime.now()
        }
        db.profissionais_avaliacoes.insert_one(avaliacao)
        clear_cache('profissionais_list')
        return jsonify({'success': True, 'avaliacao': convert_objectid(avaliacao)})
    except Exception as e:
        logger.error(f"Erro ao registrar avaliacao: {e}")
        return jsonify({'success': False, 'message': 'Erro ao registrar avaliacao'}), 500


@bp.route('/api/profissionais/<id>/upload-foto', methods=['POST'])


@bp.route('/api/comissoes/historico', methods=['GET'])
@login_required
def historico_comissoes():
    """Lista histórico de comissões calculadas"""
    try:
        historico = list(db.comissoes_historico.find().sort('data_calculo', DESCENDING).limit(50))
        
        for item in historico:
            item['_id'] = str(item['_id'])
            item['orcamento_id'] = str(item.get('orcamento_id'))
            item['profissional_id'] = str(item.get('profissional_id'))
            if item.get('assistente_id'):
                item['assistente_id'] = str(item['assistente_id'])
            
            # Buscar nomes
            prof = db.profissionais.find_one({'_id': ObjectId(item['profissional_id'])})
            if prof:
                item['profissional_nome'] = prof.get('nome')
            
            if item.get('assistente_id'):
                asst = db.assistentes.find_one({'_id': ObjectId(item['assistente_id'])})
                if asst:
                    item['assistente_nome'] = asst.get('nome')
        
        return jsonify({'success': True, 'historico': historico})
    except Exception as e:
        logger.error(f"Erro ao buscar histórico: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 7. Cadastrar Assistente Independente
@bp.route('/api/assistentes/cadastrar-independente', methods=['POST'])


@bp.route('/api/profissionais/<id>/comissoes', methods=['GET'])
@login_required
def get_comissoes_profissional(id):
    """Obter estatísticas de comissões de um profissional"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        # Filtros opcionais
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        status = request.args.get('status')
        
        # Query base
        query = {'profissional_id': ObjectId(id)}
        
        # Aplicar filtros
        if data_inicio or data_fim:
            date_filter = {}
            if data_inicio:
                date_filter['$gte'] = datetime.fromisoformat(data_inicio)
            if data_fim:
                date_filter['$lte'] = datetime.fromisoformat(data_fim)
            query['data_registro'] = date_filter
        
        if status:
            query['status_orcamento'] = status
        
        # Buscar histórico de comissões
        comissoes = list(db.comissoes_historico.find(query).sort('data_registro', DESCENDING))
        
        # Calcular estatísticas
        total_comissoes = sum(c.get('comissao_valor', 0) for c in comissoes)
        total_orcamentos = len(set(str(c.get('orcamento_id')) for c in comissoes))
        media_comissao = total_comissoes / total_orcamentos if total_orcamentos > 0 else 0
        
        # Agrupar por mês
        comissoes_por_mes = {}
        for comissao in comissoes:
            data = comissao.get('data_registro')
            if data and isinstance(data, datetime):
                mes_ano = data.strftime('%Y-%m')
                if mes_ano not in comissoes_por_mes:
                    comissoes_por_mes[mes_ano] = {'valor': 0, 'quantidade': 0}
                comissoes_por_mes[mes_ano]['valor'] += comissao.get('comissao_valor', 0)
                comissoes_por_mes[mes_ano]['quantidade'] += 1
        
        # Converter para formato de resposta
        for c in comissoes:
            c['_id'] = str(c['_id'])
            c['orcamento_id'] = str(c['orcamento_id'])
            c['profissional_id'] = str(c['profissional_id'])
            if 'data_registro' in c and isinstance(c['data_registro'], datetime):
                c['data_registro'] = c['data_registro'].isoformat()
        
        # Buscar dados do profissional
        profissional = db.profissionais.find_one({'_id': ObjectId(id)})
        if not profissional:
            profissional = db.assistentes.find_one({'_id': ObjectId(id)})
        
        resultado = {
            'profissional': {
                'id': id,
                'nome': profissional.get('nome') if profissional else 'Desconhecido',
                'foto': profissional.get('foto') if profissional else None
            },
            'estatisticas': {
                'total_comissoes': round(total_comissoes, 2),
                'total_orcamentos': total_orcamentos,
                'media_comissao': round(media_comissao, 2),
                'comissoes_por_mes': comissoes_por_mes
            },
            'historico': comissoes
        }
        
        logger.info(f"📊 Estatísticas de comissões do profissional {id}: R$ {total_comissoes:.2f}")
        return jsonify({'success': True, 'data': resultado})
        
    except Exception as e:
        logger.error(f"❌ Erro em get_comissoes_profissional: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== FIM DAS NOVAS FUNCIONALIDADES ====================

# ==================== ENDPOINTS PARA SUB-TABS - PRODUTOS ====================

@bp.route('/api/produtos', methods=['GET'])
