#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Clientes Routes
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

from app.clientes import bp
from app.decorators import login_required, permission_required, get_user_permissions
from app.utils import convert_objectid, allowed_file, registrar_auditoria
from app.extensions import db as get_db, get_from_cache, set_in_cache

logger = logging.getLogger(__name__)

@bp.route('/api/clientes', methods=['GET', 'POST'])
@login_required
def clientes():
    if db is None:
        return jsonify({'success': False}), 500

    if request.method == 'GET':
        try:
            # ==================== PERFORMANCE OPTIMIZATION ====================
            # Implement pagination to prevent loading thousands of records at once
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 50, type=int)
            skip = (page - 1) * per_page

            # Get total count for pagination metadata
            total_count = db.clientes.count_documents({})
            total_pages = (total_count + per_page - 1) // per_page

            # Use projection to only return needed fields (reduces data transfer)
            projection = {
                'nome': 1,
                'cpf': 1,
                'email': 1,
                'telefone': 1,
                'total_faturado': 1,  # Denormalized field
                'ultima_visita': 1,    # Denormalized field
                'total_visitas': 1,    # Denormalized field
                'created_at': 1
            }

            clientes_list = list(
                db.clientes.find({}, projection)
                .sort('nome', ASCENDING)
                .skip(skip)
                .limit(per_page)
            )

            # If denormalized fields don't exist, calculate and store them
            # This is a one-time migration for existing records
            for cliente in clientes_list:
                cliente_cpf = cliente.get('cpf')

                if 'total_faturado' not in cliente:
                    # Calculate and denormalize
                    total_faturado = sum(
                        o.get('total_final', 0)
                        for o in db.orcamentos.find(
                            {'cliente_cpf': cliente_cpf, 'status': 'Aprovado'},
                            {'total_final': 1}
                        )
                    )
                    ultimo_orc = db.orcamentos.find_one(
                        {'cliente_cpf': cliente_cpf},
                        sort=[('created_at', DESCENDING)],
                        projection={'created_at': 1}
                    )
                    ultima_visita = ultimo_orc['created_at'] if ultimo_orc else None
                    total_visitas = db.orcamentos.count_documents({'cliente_cpf': cliente_cpf})

                    # Store denormalized values for future queries
                    db.clientes.update_one(
                        {'_id': cliente['_id']},
                        {'$set': {
                            'total_faturado': total_faturado,
                            'ultima_visita': ultima_visita,
                            'total_visitas': total_visitas
                        }}
                    )

                    cliente['total_faturado'] = total_faturado
                    cliente['ultima_visita'] = ultima_visita
                    cliente['total_visitas'] = total_visitas

                # Maintain backwards compatibility
                cliente['total_gasto'] = cliente.get('total_faturado', 0)

            return jsonify({
                'success': True,
                'clientes': convert_objectid(clientes_list),
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_count': total_count,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            })
        except Exception as e:
            logger.error(f"❌ Error loading clientes: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    data = request.json
    try:
        existing = db.clientes.find_one({'cpf': data['cpf']})
        cliente_data = {'nome': data['nome'], 'cpf': data['cpf'], 'email': data.get('email', ''), 'telefone': data.get('telefone', ''), 'updated_at': datetime.now()}
        if existing:
            db.clientes.update_one({'cpf': data['cpf']}, {'$set': cliente_data})
        else:
            cliente_data['created_at'] = datetime.now()
            db.clientes.insert_one(cliente_data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/api/clientes/<id>', methods=['DELETE'])


@bp.route('/api/clientes/<id>', methods=['GET'])
@login_required
def get_cliente(id):
    """Visualizar um cliente específico"""
    if db is None:
        return jsonify({'success': False}), 500
    try:
        cliente = db.clientes.find_one({'_id': ObjectId(id)})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
        
        # Adicionar estatísticas
        cliente_cpf = cliente.get('cpf')
        # ALTERADO: total_gasto -> total_faturado (Diretriz #11)
        cliente['total_faturado'] = sum(o.get('total_final', 0) for o in db.orcamentos.find({'cliente_cpf': cliente_cpf, 'status': 'Aprovado'}))
        cliente['total_gasto'] = cliente['total_faturado']  # Mantém compatibilidade
        ultimo_orc = db.orcamentos.find_one({'cliente_cpf': cliente_cpf}, sort=[('created_at', DESCENDING)])
        cliente['ultima_visita'] = ultimo_orc['created_at'] if ultimo_orc else None
        cliente['total_visitas'] = db.orcamentos.count_documents({'cliente_cpf': cliente_cpf})
        
        return jsonify({'success': True, 'cliente': convert_objectid(cliente)})
    except Exception as e:
        logger.error(f"Erro ao buscar cliente: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/api/clientes/<id>', methods=['PUT'])


@bp.route('/api/clientes/buscar')
@login_required
def buscar_clientes():
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    termo = request.args.get('termo', '').strip()
    cache_key = f"clientes_busca_{termo}"
    
    # Tentar buscar do cache primeiro
    cached = get_from_cache(cache_key)
    if cached:
        return jsonify(cached)
    
    try:
        regex = {'$regex': termo, '$options': 'i'}
        clientes = list(db.clientes.find({
            '$or': [
                {'nome': regex},
                {'cpf': regex},
                {'email': regex},
                {'telefone': regex}
            ]
        }).sort('nome', ASCENDING).limit(50))
        
        # Adicionar informação completa formatada
        for c in clientes:
            c['display_name'] = f"{c.get('nome', '')} - CPF: {c.get('cpf', '')}"
        
        result = {'success': True, 'clientes': convert_objectid(clientes)}
        set_in_cache(cache_key, result)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Erro ao buscar clientes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/api/busca/global', methods=['GET'])


@bp.route('/api/clientes/<id>/faturamento', methods=['GET'])
@login_required
def faturamento_cliente(id):
    """Retorna faturamento total de um cliente"""
    try:
        pipeline = [
            {'$match': {'cliente_id': ObjectId(id), 'status': 'aprovado'}},
            {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
        ]
        
        resultado = list(db.orcamentos.aggregate(pipeline))
        total = resultado[0]['total'] if resultado else 0
        
        return jsonify({'success': True, 'faturamento_total': round(total, 2)})
    except Exception as e:
        logger.error(f"Erro ao calcular faturamento: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 16. Anamnese do Cliente (GET/PUT)
@bp.route('/api/clientes/<id>/anamnese', methods=['GET', 'PUT'])


@bp.route('/api/clientes/<id>/prontuario', methods=['GET', 'PUT'])
@login_required
def prontuario_cliente(id):
    """Gerencia prontuário do cliente"""
    try:
        if request.method == 'GET':
            cliente = db.clientes.find_one({'_id': ObjectId(id)})
            if not cliente:
                return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
            
            prontuario = cliente.get('prontuario', [])
            return jsonify({'success': True, 'prontuario': prontuario})
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            # Adicionar novo registro ao prontuário
            db.clientes.update_one(
                {'_id': ObjectId(id)},
                {'$push': {'prontuario': {
                    'data': datetime.now(),
                    'procedimento': data.get('procedimento'),
                    'observacoes': data.get('observacoes'),
                    'profissional': data.get('profissional')
                }}}
            )
            
            return jsonify({'success': True, 'message': 'Registro adicionado ao prontuário'})
    except Exception as e:
        logger.error(f"Erro no prontuário: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 18. Gerar PDF Resumo do Cliente
@bp.route('/api/clientes/<id>/resumo-pdf', methods=['GET'])


@bp.route('/api/clientes/<cpf>/anamnese', methods=['GET', 'POST'])
@login_required
def handle_anamnese(cpf):
    """Gerenciar histórico de anamneses de um cliente"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        # Buscar cliente
        cliente = db.clientes.find_one({'cpf': cpf})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
        
        if request.method == 'GET':
            # Listar histórico de anamneses
            anamneses = list(db.anamneses.find({'cliente_cpf': cpf}).sort('data_cadastro', DESCENDING))
            
            for anamnese in anamneses:
                anamnese['_id'] = str(anamnese['_id'])
                if 'data_cadastro' in anamnese and isinstance(anamnese['data_cadastro'], datetime):
                    anamnese['data_cadastro'] = anamnese['data_cadastro'].isoformat()
            
            logger.info(f"📋 Listando {len(anamneses)} anamneses do cliente {cpf}")
            return jsonify({
                'success': True,
                'cliente': {
                    'cpf': cliente.get('cpf'),
                    'nome': cliente.get('nome')
                },
                'anamneses': anamneses
            })
        
        elif request.method == 'POST':
            # Criar nova anamnese
            data = request.json
            logger.info(f"📝 Criando anamnese para cliente {cpf}")
            
            anamnese = {
                'cliente_cpf': cpf,
                'cliente_nome': cliente.get('nome'),
                'respostas': data.get('respostas', {}),
                'observacoes': data.get('observacoes', ''),
                'data_cadastro': datetime.now(),
                'cadastrado_por': session.get('username'),
                'versao': db.anamneses.count_documents({'cliente_cpf': cpf}) + 1
            }
            
            result = db.anamneses.insert_one(anamnese)
            anamnese['_id'] = str(result.inserted_id)
            anamnese['data_cadastro'] = anamnese['data_cadastro'].isoformat()
            
            # Atualizar campo anamnese_atualizada no cliente
            db.clientes.update_one(
                {'cpf': cpf},
                {'$set': {'anamnese_atualizada': datetime.now()}}
            )
            
            logger.info(f"✅ Anamnese v{anamnese['versao']} criada para {cpf}")
            return jsonify({'success': True, 'anamnese': anamnese})
            
    except Exception as e:
        logger.error(f"❌ Erro em handle_anamnese: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/api/clientes/<cpf>/anamnese/<id>', methods=['GET', 'DELETE'])


@bp.route('/api/clientes/<cpf>/prontuario', methods=['GET', 'POST'])
@login_required
def handle_prontuario(cpf):
    """Gerenciar histórico de prontuários de um cliente"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        # Buscar cliente
        cliente = db.clientes.find_one({'cpf': cpf})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
        
        if request.method == 'GET':
            # Listar histórico de prontuários
            prontuarios = list(db.prontuarios.find({'cliente_cpf': cpf}).sort('data_atendimento', DESCENDING))
            
            for pront in prontuarios:
                pront['_id'] = str(pront['_id'])
                if 'data_atendimento' in pront and isinstance(pront['data_atendimento'], datetime):
                    pront['data_atendimento'] = pront['data_atendimento'].isoformat()
                if 'data_cadastro' in pront and isinstance(pront['data_cadastro'], datetime):
                    pront['data_cadastro'] = pront['data_cadastro'].isoformat()
            
            logger.info(f"📋 Listando {len(prontuarios)} prontuários do cliente {cpf}")
            return jsonify({
                'success': True,
                'cliente': {
                    'cpf': cliente.get('cpf'),
                    'nome': cliente.get('nome')
                },
                'prontuarios': prontuarios
            })
        
        elif request.method == 'POST':
            # Criar novo prontuário
            data = request.json
            logger.info(f"📝 Criando prontuário para cliente {cpf}")
            
            prontuario = {
                'cliente_cpf': cpf,
                'cliente_nome': cliente.get('nome'),
                'data_atendimento': datetime.fromisoformat(data.get('data_atendimento', datetime.now().isoformat())),
                'profissional': data.get('profissional', ''),
                'procedimento': data.get('procedimento', ''),
                'produtos_utilizados': data.get('produtos_utilizados', []),
                'observacoes': data.get('observacoes', ''),
                'fotos_antes': data.get('fotos_antes', []),
                'fotos_depois': data.get('fotos_depois', []),
                'proxima_sessao': data.get('proxima_sessao', ''),
                'data_cadastro': datetime.now(),
                'cadastrado_por': session.get('username')
            }
            
            result = db.prontuarios.insert_one(prontuario)
            prontuario['_id'] = str(result.inserted_id)
            prontuario['data_atendimento'] = prontuario['data_atendimento'].isoformat()
            prontuario['data_cadastro'] = prontuario['data_cadastro'].isoformat()
            
            # Atualizar campo prontuario_atualizado no cliente
            db.clientes.update_one(
                {'cpf': cpf},
                {'$set': {'prontuario_atualizado': datetime.now()}}
            )
            
            logger.info(f"✅ Prontuário criado para {cpf}")
            return jsonify({'success': True, 'prontuario': prontuario})
            
    except Exception as e:
        logger.error(f"❌ Erro em handle_prontuario: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/api/clientes/<cpf>/prontuario/<id>', methods=['GET', 'PUT', 'DELETE'])


@bp.route('/api/clientes/<cpf>/historico-completo', methods=['GET'])
@login_required
def historico_completo_cliente(cpf):
    """Obter histórico completo de anamnese e prontuários de um cliente (COM PAGINAÇÃO - Roadmap #11)"""
    if db is None:
        return jsonify({'success': False}), 500

    try:
        # Parâmetros de paginação (Roadmap Section V - Clientes #11)
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 25))  # 25 itens por página por padrão
        skip = (page - 1) * limit

        # Buscar cliente
        cliente = db.clientes.find_one({'cpf': cpf})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404

        # PAGINAÇÃO: Buscar anamneses com limit e skip
        anamneses_query = db.anamneses.find({'cliente_cpf': cpf}).sort('data_cadastro', DESCENDING)
        total_anamneses = db.anamneses.count_documents({'cliente_cpf': cpf})
        anamneses_paginadas = list(anamneses_query.skip(skip).limit(limit))

        # PAGINAÇÃO: Buscar prontuários com limit e skip
        prontuarios_query = db.prontuarios.find({'cliente_cpf': cpf}).sort('data_atendimento', DESCENDING)
        total_prontuarios = db.prontuarios.count_documents({'cliente_cpf': cpf})
        prontuarios_paginados = list(prontuarios_query.skip(skip).limit(limit))

        # PAGINAÇÃO: Buscar orçamentos/contratos com limit e skip
        orcamentos_query = db.orcamentos.find({'cliente_cpf': cpf}).sort('created_at', DESCENDING)
        total_orcamentos = db.orcamentos.count_documents({'cliente_cpf': cpf})
        orcamentos_paginados = list(orcamentos_query.skip(skip).limit(limit))

        # Calcular estatísticas (usa totais, não paginados)
        total_atendimentos = total_prontuarios
        total_gasto = sum(
            o.get('total_final', 0)
            for o in db.orcamentos.find({'cliente_cpf': cpf, 'status': 'Aprovado'})
        )

        # Buscar último atendimento (sempre o primeiro resultado ordenado)
        ultimo_prontuario = db.prontuarios.find_one(
            {'cliente_cpf': cpf},
            sort=[('data_atendimento', DESCENDING)]
        )
        ultimo_atendimento = ultimo_prontuario.get('data_atendimento') if ultimo_prontuario else None

        historico = {
            'cliente': {
                'nome': cliente.get('nome'),
                'cpf': cliente.get('cpf'),
                'telefone': cliente.get('telefone'),
                'email': cliente.get('email'),
                'data_nascimento': cliente.get('data_nascimento')
            },
            'estatisticas': {
                'total_atendimentos': total_atendimentos,
                'total_faturado': total_gasto,
                'total_orcamentos': total_orcamentos,
                'ultimo_atendimento': ultimo_atendimento.isoformat() if isinstance(ultimo_atendimento, datetime) else ultimo_atendimento
            },
            'anamneses': convert_objectid(anamneses_paginadas),
            'prontuarios': convert_objectid(prontuarios_paginados),
            'orcamentos': convert_objectid(orcamentos_paginados),
            'paginacao': {
                'page': page,
                'limit': limit,
                'total_anamneses': total_anamneses,
                'total_prontuarios': total_prontuarios,
                'total_orcamentos': total_orcamentos,
                'total_paginas_anamneses': (total_anamneses + limit - 1) // limit,
                'total_paginas_prontuarios': (total_prontuarios + limit - 1) // limit,
                'total_paginas_orcamentos': (total_orcamentos + limit - 1) // limit,
                'tem_proxima': skip + limit < max(total_anamneses, total_prontuarios, total_orcamentos),
                'tem_anterior': page > 1
            }
        }

        return jsonify({'success': True, 'historico': historico})

    except Exception as e:
        logger.error(f"Erro ao buscar histórico completo: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/clientes/<cpf>/prontuario/<id>/pdf', methods=['GET'])


@bp.route('/api/clientes/<cpf>/historico-completo/pdf', methods=['GET'])
@login_required
def gerar_pdf_historico_completo(cpf):
    """Gerar PDF do histórico completo do cliente (Diretriz #21)"""
    if db is None:
        return jsonify({'success': False}), 500

    try:
        cliente = db.clientes.find_one({'cpf': cpf})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404

        prontuarios = list(db.prontuarios.find({'cliente_cpf': cpf}).sort('data_atendimento', DESCENDING))
        orcamentos = list(db.orcamentos.find({'cliente_cpf': cpf, 'status': 'Aprovado'}).sort('created_at', DESCENDING))

        # Criar buffer para o PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        # Título
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=TA_CENTER)
        elements.append(Paragraph(f"HISTÓRICO COMPLETO - {cliente.get('nome', 'Cliente')}", title_style))
        elements.append(Spacer(1, 0.5*cm))

        # Estatísticas
        total_atendimentos = len(prontuarios)
        total_faturado = sum(o.get('total_final', 0) for o in orcamentos)

        estatisticas_data = [
            ['Total de Atendimentos:', str(total_atendimentos)],
            ['Total Faturado:', f"R$ {total_faturado:.2f}"],
            ['Última Visita:', prontuarios[0].get('data_atendimento').strftime('%d/%m/%Y') if prontuarios and isinstance(prontuarios[0].get('data_atendimento'), datetime) else 'N/A']
        ]
        estatisticas_table = Table(estatisticas_data, colWidths=[8*cm, 8*cm])
        estatisticas_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#e8f5e9')),
            ('GRID', (0, 0), (-1, -1), 0.5, black),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        elements.append(estatisticas_table)
        elements.append(Spacer(1, 0.5*cm))

        # Histórico de prontuários
        if prontuarios:
            elements.append(Paragraph('<b>HISTÓRICO DE ATENDIMENTOS</b>', styles['Heading2']))
            for prontuario in prontuarios[:10]:  # Limitar aos 10 mais recentes
                data_atend = prontuario.get('data_atendimento')
                if isinstance(data_atend, datetime):
                    data_atend = data_atend.strftime('%d/%m/%Y')

                elements.append(Paragraph(f"<b>{data_atend}</b> - {prontuario.get('procedimento', 'Procedimento não especificado')}", styles['Normal']))
                if prontuario.get('profissional'):
                    elements.append(Paragraph(f"Profissional: {prontuario.get('profissional')}", styles['Normal']))
                if prontuario.get('observacoes'):
                    elements.append(Paragraph(f"Obs: {prontuario.get('observacoes')[:150]}...", styles['Normal']))
                elements.append(Spacer(1, 0.2*cm))

        # Gerar PDF
        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"historico_completo_{cliente.get('nome', 'cliente')}.pdf"
        )

    except Exception as e:
        logger.error(f"Erro ao gerar PDF de histórico completo: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/clientes/<cpf>/historico-completo/whatsapp', methods=['GET'])
