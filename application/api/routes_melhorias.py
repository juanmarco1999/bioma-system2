#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Rotas de Melhorias
APIs Críticas: Comissões, Financeiro, Notificações, etc.
"""

from flask import Blueprint, request, jsonify, send_file
from bson import ObjectId
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import logging
import os
import urllib.parse
from io import BytesIO

logger = logging.getLogger(__name__)

# Criar novo blueprint para melhorias
bp = Blueprint('melhorias', __name__)

# Importar db do módulo principal
from application.api.routes import get_db

# ============================================================================
# API DE COMISSÕES (CRÍTICO - Carregamento Infinito)
# ============================================================================

@bp.route('/api/comissoes/pendentes')
def get_comissoes_pendentes():
    """Buscar comissões pendentes de pagamento"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'success': False, 'message': 'Database offline'}), 500

        # Aggregation para buscar orçamentos aprovados com comissões não pagas
        pipeline = [
            {
                '$match': {
                    'status': 'aprovado',
                    '$or': [
                        {'comissao_paga': {'$exists': False}},
                        {'comissao_paga': False}
                    ]
                }
            },
            {
                '$lookup': {
                    'from': 'profissionais',
                    'localField': 'profissional_id',
                    'foreignField': '_id',
                    'as': 'profissional_info'
                }
            },
            {
                '$unwind': {
                    'path': '$profissional_info',
                    'preserveNullAndEmptyArrays': True
                }
            },
            {
                '$project': {
                    '_id': 1,
                    'numero': 1,
                    'created_at': 1,
                    'valor_total': 1,
                    'profissional_nome': {'$ifNull': ['$profissional_info.nome', 'Não especificado']},
                    'profissional_comissao': {'$ifNull': ['$profissional_info.comissao_percentual', 10]},
                    'valor_comissao': {
                        '$multiply': [
                            '$valor_total',
                            {'$divide': [{'$ifNull': ['$profissional_info.comissao_percentual', 10]}, 100]}
                        ]
                    }
                }
            },
            {'$sort': {'created_at': -1}}
        ]

        comissoes = list(db.orcamentos.aggregate(pipeline))

        # Converter ObjectId para string
        for com in comissoes:
            com['_id'] = str(com['_id'])

        return jsonify({
            'success': True,
            'comissoes': comissoes,
            'total': len(comissoes),
            'total_valor': sum(c['valor_comissao'] for c in comissoes)
        })

    except Exception as e:
        logger.error(f"Erro ao buscar comissões pendentes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/comissoes/pagas')
def get_comissoes_pagas():
    """Buscar comissões já pagas"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'success': False, 'message': 'Database offline'}), 500

        # Buscar comissões pagas
        pipeline = [
            {
                '$match': {
                    'status': 'aprovado',
                    'comissao_paga': True
                }
            },
            {
                '$lookup': {
                    'from': 'profissionais',
                    'localField': 'profissional_id',
                    'foreignField': '_id',
                    'as': 'profissional_info'
                }
            },
            {
                '$unwind': {
                    'path': '$profissional_info',
                    'preserveNullAndEmptyArrays': True
                }
            },
            {
                '$project': {
                    '_id': 1,
                    'numero': 1,
                    'created_at': 1,
                    'comissao_data_pagamento': 1,
                    'valor_total': 1,
                    'profissional_nome': {'$ifNull': ['$profissional_info.nome', 'Não especificado']},
                    'profissional_comissao': {'$ifNull': ['$profissional_info.comissao_percentual', 10]},
                    'valor_comissao': {
                        '$multiply': [
                            '$valor_total',
                            {'$divide': [{'$ifNull': ['$profissional_info.comissao_percentual', 10]}, 100]}
                        ]
                    }
                }
            },
            {'$sort': {'comissao_data_pagamento': -1}}
        ]

        comissoes = list(db.orcamentos.aggregate(pipeline))

        for com in comissoes:
            com['_id'] = str(com['_id'])

        return jsonify({
            'success': True,
            'comissoes': comissoes,
            'total': len(comissoes)
        })

    except Exception as e:
        logger.error(f"Erro ao buscar comissões pagas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/comissoes/<orcamento_id>/pagar', methods=['POST'])
def pagar_comissao(orcamento_id):
    """Marcar comissão como paga"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'success': False, 'message': 'Database offline'}), 500

        result = db.orcamentos.update_one(
            {'_id': ObjectId(orcamento_id)},
            {
                '$set': {
                    'comissao_paga': True,
                    'comissao_data_pagamento': datetime.now()
                }
            }
        )

        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Comissão marcada como paga'})
        else:
            return jsonify({'success': False, 'message': 'Orçamento não encontrado'})

    except Exception as e:
        logger.error(f"Erro ao pagar comissão: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# API DE FINANCEIRO (CRÍTICO - Carregamento Infinito)
# ============================================================================

@bp.route('/api/financeiro/resumo')
def get_financeiro_resumo():
    """Resumo financeiro geral"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'success': False, 'message': 'Database offline'}), 500

        # Data atual
        hoje = datetime.now()
        inicio_mes = datetime(hoje.year, hoje.month, 1)

        # Receitas do mês (orçamentos aprovados)
        receitas_mes = db.orcamentos.aggregate([
            {
                '$match': {
                    'status': 'aprovado',
                    'created_at': {'$gte': inicio_mes}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total': {'$sum': '$valor_total'}
                }
            }
        ])
        receitas_mes_valor = next(receitas_mes, {}).get('total', 0)

        # Despesas do mês
        despesas_mes = db.despesas.aggregate([
            {
                '$match': {
                    'data_vencimento': {'$gte': inicio_mes}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total': {'$sum': '$valor'}
                }
            }
        ])
        despesas_mes_valor = next(despesas_mes, {}).get('total', 0)

        # Contas a receber
        contas_receber = db.orcamentos.aggregate([
            {
                '$match': {
                    'status': 'aprovado',
                    '$or': [
                        {'pago': {'$exists': False}},
                        {'pago': False}
                    ]
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total': {'$sum': '$valor_total'}
                }
            }
        ])
        contas_receber_valor = next(contas_receber, {}).get('total', 0)

        # Contas a pagar
        contas_pagar = db.despesas.aggregate([
            {
                '$match': {
                    'status': {'$ne': 'pago'}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total': {'$sum': '$valor'}
                }
            }
        ])
        contas_pagar_valor = next(contas_pagar, {}).get('total', 0)

        return jsonify({
            'success': True,
            'resumo': {
                'receitas_mes': receitas_mes_valor,
                'despesas_mes': despesas_mes_valor,
                'saldo_mes': receitas_mes_valor - despesas_mes_valor,
                'contas_receber': contas_receber_valor,
                'contas_pagar': contas_pagar_valor,
                'saldo_geral': contas_receber_valor - contas_pagar_valor
            }
        })

    except Exception as e:
        logger.error(f"Erro ao buscar resumo financeiro: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/financeiro/receitas')
def get_receitas():
    """Listar receitas (orçamentos aprovados)"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'success': False, 'message': 'Database offline'}), 500

        receitas = list(db.orcamentos.find(
            {'status': 'aprovado'}
        ).sort('created_at', -1).limit(100))

        for rec in receitas:
            rec['_id'] = str(rec['_id'])

        return jsonify({'success': True, 'receitas': receitas})

    except Exception as e:
        logger.error(f"Erro ao buscar receitas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/financeiro/despesas')
def get_despesas():
    """Listar despesas"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'success': False, 'message': 'Database offline'}), 500

        despesas = list(db.despesas.find().sort('data_vencimento', -1).limit(100))

        for desp in despesas:
            desp['_id'] = str(desp['_id'])

        return jsonify({'success': True, 'despesas': despesas})

    except Exception as e:
        logger.error(f"Erro ao buscar despesas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/financeiro/fluxo-caixa')
def get_fluxo_caixa():
    """Fluxo de caixa mensal"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'success': False, 'message': 'Database offline'}), 500

        # Últimos 12 meses
        hoje = datetime.now()
        meses = []

        for i in range(12):
            mes_ref = hoje - timedelta(days=30 * i)
            inicio = datetime(mes_ref.year, mes_ref.month, 1)

            # Próximo mês
            if mes_ref.month == 12:
                fim = datetime(mes_ref.year + 1, 1, 1)
            else:
                fim = datetime(mes_ref.year, mes_ref.month + 1, 1)

            # Receitas do mês
            receitas = db.orcamentos.aggregate([
                {'$match': {'status': 'aprovado', 'created_at': {'$gte': inicio, '$lt': fim}}},
                {'$group': {'_id': None, 'total': {'$sum': '$valor_total'}}}
            ])
            receitas_valor = next(receitas, {}).get('total', 0)

            # Despesas do mês
            despesas = db.despesas.aggregate([
                {'$match': {'data_vencimento': {'$gte': inicio, '$lt': fim}}},
                {'$group': {'_id': None, 'total': {'$sum': '$valor'}}}
            ])
            despesas_valor = next(despesas, {}).get('total', 0)

            meses.insert(0, {
                'mes': inicio.strftime('%b/%y'),
                'receitas': receitas_valor,
                'despesas': despesas_valor,
                'saldo': receitas_valor - despesas_valor
            })

        return jsonify({'success': True, 'fluxo': meses})

    except Exception as e:
        logger.error(f"Erro ao buscar fluxo de caixa: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# API DE AGENDAMENTOS (CORREÇÃO - Dados "Desconhecido")
# ============================================================================

@bp.route('/api/agendamentos/mes')
def get_agendamentos_mes():
    """Buscar agendamentos do mês com dados completos"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'success': False, 'message': 'Database offline'}), 500

        hoje = datetime.now()
        inicio_mes = datetime(hoje.year, hoje.month, 1)

        if hoje.month == 12:
            fim_mes = datetime(hoje.year + 1, 1, 1)
        else:
            fim_mes = datetime(hoje.year, hoje.month + 1, 1)

        # Aggregation para popular dados relacionados
        pipeline = [
            {
                '$match': {
                    'data': {'$gte': inicio_mes, '$lt': fim_mes}
                }
            },
            {
                '$lookup': {
                    'from': 'clientes',
                    'localField': 'cliente_id',
                    'foreignField': '_id',
                    'as': 'cliente'
                }
            },
            {
                '$lookup': {
                    'from': 'profissionais',
                    'localField': 'profissional_id',
                    'foreignField': '_id',
                    'as': 'profissional'
                }
            },
            {
                '$lookup': {
                    'from': 'servicos',
                    'localField': 'servico_id',
                    'foreignField': '_id',
                    'as': 'servico'
                }
            },
            {
                '$unwind': {
                    'path': '$cliente',
                    'preserveNullAndEmptyArrays': True
                }
            },
            {
                '$unwind': {
                    'path': '$profissional',
                    'preserveNullAndEmptyArrays': True
                }
            },
            {
                '$unwind': {
                    'path': '$servico',
                    'preserveNullAndEmptyArrays': True
                }
            },
            {
                '$project': {
                    '_id': 1,
                    'data': 1,
                    'horario': 1,
                    'status': 1,
                    'cliente_nome': {'$ifNull': ['$cliente.nome', 'Desconhecido']},
                    'profissional_nome': {'$ifNull': ['$profissional.nome', 'Desconhecido']},
                    'servico_nome': {'$ifNull': ['$servico.nome', 'Desconhecido']}
                }
            },
            {'$sort': {'data': 1, 'horario': 1}}
        ]

        agendamentos = list(db.agendamentos.aggregate(pipeline))

        for ag in agendamentos:
            ag['_id'] = str(ag['_id'])

        return jsonify({'success': True, 'agendamentos': agendamentos})

    except Exception as e:
        logger.error(f"Erro ao buscar agendamentos do mês: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# API DE NOTIFICAÇÕES (E-mail + WhatsApp)
# ============================================================================

@bp.route('/api/notificacoes/email/<tipo>/<item_id>', methods=['POST'])
def enviar_email_notificacao(tipo, item_id):
    """Enviar notificação por e-mail (MailerSend)"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'success': False, 'message': 'Database offline'}), 500

        # TODO: Implementar integração com MailerSend
        # Por enquanto, retornar sucesso simulado

        logger.info(f"📧 E-mail simulado: {tipo} #{item_id}")

        return jsonify({
            'success': True,
            'message': 'E-mail enviado com sucesso (simulado)',
            'tipo': tipo,
            'item_id': item_id
        })

    except Exception as e:
        logger.error(f"Erro ao enviar e-mail: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/notificacoes/whatsapp/<tipo>/<item_id>', methods=['POST'])
def enviar_whatsapp_notificacao(tipo, item_id):
    """Gerar link de WhatsApp"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'success': False, 'message': 'Database offline'}), 500

        # Buscar dados do item
        item = None
        if tipo == 'orcamento':
            item = db.orcamentos.find_one({'_id': ObjectId(item_id)})
        elif tipo == 'agendamento':
            item = db.agendamentos.find_one({'_id': ObjectId(item_id)})

        if not item:
            return jsonify({'success': False, 'message': 'Item não encontrado'})

        # Buscar telefone do cliente
        cliente = None
        if 'cliente_id' in item:
            cliente = db.clientes.find_one({'_id': item['cliente_id']})

        telefone = cliente.get('telefone', '') if cliente else ''

        # Remover formatação do telefone
        telefone = telefone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')

        # Gerar mensagem
        if tipo == 'orcamento':
            mensagem = f"Olá! Seu orçamento #{item.get('numero', item_id)} no valor de R$ {item.get('valor_total', 0):.2f} está disponível. Acesse nosso sistema para mais detalhes."
        elif tipo == 'agendamento':
            mensagem = f"Olá! Confirmamos seu agendamento para {item.get('data', 'data a definir')} às {item.get('horario', 'horário a definir')}. Aguardamos você!"
        else:
            mensagem = "Olá! Você tem uma nova notificação do BIOMA Uberaba."

        # URL encode da mensagem
        mensagem_encoded = urllib.parse.quote(mensagem)

        # Gerar link do WhatsApp
        whatsapp_url = f"https://wa.me/{telefone}?text={mensagem_encoded}"

        logger.info(f"📱 WhatsApp link gerado: {tipo} #{item_id}")

        return jsonify({
            'success': True,
            'url': whatsapp_url,
            'message': 'Link do WhatsApp gerado com sucesso',
            'tipo': tipo,
            'item_id': item_id
        })

    except Exception as e:
        logger.error(f"Erro ao gerar link WhatsApp: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# API DE CLIENTES - FATURAMENTO (CRÍTICO)
# ============================================================================

@bp.route('/api/clientes/<cliente_id>/faturamento')
def get_cliente_faturamento(cliente_id):
    """Buscar faturamento do cliente"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'success': False, 'message': 'Database offline'}), 500

        # Agregar orçamentos aprovados do cliente
        pipeline = [
            {
                '$match': {
                    'cliente_id': ObjectId(cliente_id),
                    'status': 'aprovado'
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total_faturado': {'$sum': '$valor_total'},
                    'quantidade_orcamentos': {'$sum': 1},
                    'ticket_medio': {'$avg': '$valor_total'}
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'total_faturado': 1,
                    'quantidade_orcamentos': 1,
                    'ticket_medio': {'$round': ['$ticket_medio', 2]}
                }
            }
        ]

        resultado = list(db.orcamentos.aggregate(pipeline))

        if resultado:
            faturamento = resultado[0]
        else:
            faturamento = {
                'total_faturado': 0,
                'quantidade_orcamentos': 0,
                'ticket_medio': 0
            }

        return jsonify({'success': True, 'faturamento': faturamento})

    except Exception as e:
        logger.error(f"Erro ao buscar faturamento do cliente: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# API DE ESTOQUE - EXPORTAR EXCEL (CORREÇÃO)
# ============================================================================

@bp.route('/api/estoque/exportar/excel')
def exportar_estoque_excel():
    """Exportar estoque para Excel"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'success': False, 'message': 'Database offline'}), 500

        # Buscar produtos
        produtos = list(db.produtos.find())

        if not produtos:
            return jsonify({'success': False, 'message': 'Nenhum produto encontrado'})

        # Criar Excel com openpyxl
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment

            wb = Workbook()
            ws = wb.active
            ws.title = "Estoque"

            # Cabeçalho
            headers = ['SKU', 'Nome', 'Categoria', 'Estoque Atual', 'Estoque Mínimo', 'Preço Custo', 'Preço Venda', 'Status']
            ws.append(headers)

            # Estilizar cabeçalho
            header_fill = PatternFill(start_color="7C3AED", end_color="7C3AED", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF")

            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")

            # Dados
            for prod in produtos:
                ws.append([
                    prod.get('sku', ''),
                    prod.get('nome', ''),
                    prod.get('categoria', ''),
                    prod.get('estoque_atual', 0),
                    prod.get('estoque_minimo', 0),
                    prod.get('preco_custo', 0),
                    prod.get('preco_venda', 0),
                    'Ativo' if prod.get('ativo', True) else 'Inativo'
                ])

            # Ajustar largura das colunas
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width

            # Salvar em memória
            output = BytesIO()
            wb.save(output)
            output.seek(0)

            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'estoque_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )

        except ImportError:
            # Se openpyxl não estiver instalado, usar CSV
            import csv
            from io import StringIO

            output = StringIO()
            writer = csv.writer(output)

            writer.writerow(['SKU', 'Nome', 'Categoria', 'Estoque Atual', 'Estoque Mínimo', 'Preço Custo', 'Preço Venda', 'Status'])

            for prod in produtos:
                writer.writerow([
                    prod.get('sku', ''),
                    prod.get('nome', ''),
                    prod.get('categoria', ''),
                    prod.get('estoque_atual', 0),
                    prod.get('estoque_minimo', 0),
                    prod.get('preco_custo', 0),
                    prod.get('preco_venda', 0),
                    'Ativo' if prod.get('ativo', True) else 'Inativo'
                ])

            mem = BytesIO()
            mem.write(output.getvalue().encode('utf-8-sig'))
            mem.seek(0)

            return send_file(
                mem,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'estoque_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )

    except Exception as e:
        logger.error(f"Erro ao exportar estoque: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# API - ATIVAR/DESATIVAR TODOS PRODUTOS/SERVIÇOS
# ============================================================================

@bp.route('/api/produtos/toggle-todos', methods=['POST'])
def toggle_todos_produtos():
    """Ativar/desativar todos os produtos"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'success': False, 'message': 'Database offline'}), 500

        ativo = request.json.get('ativo', True)

        result = db.produtos.update_many(
            {},
            {'$set': {'ativo': ativo}}
        )

        logger.info(f"{'Ativados' if ativo else 'Desativados'} {result.modified_count} produtos")

        return jsonify({
            'success': True,
            'count': result.modified_count,
            'message': f"{result.modified_count} produtos {'ativados' if ativo else 'desativados'}"
        })

    except Exception as e:
        logger.error(f"Erro ao toggle produtos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/servicos/toggle-todos', methods=['POST'])
def toggle_todos_servicos():
    """Ativar/desativar todos os serviços"""
    try:
        db = get_db()
        if db is None:
            return jsonify({'success': False, 'message': 'Database offline'}), 500

        ativo = request.json.get('ativo', True)

        result = db.servicos.update_many(
            {},
            {'$set': {'ativo': ativo}}
        )

        logger.info(f"{'Ativados' if ativo else 'Desativados'} {result.modified_count} serviços")

        return jsonify({
            'success': True,
            'count': result.modified_count,
            'message': f"{result.modified_count} serviços {'ativados' if ativo else 'desativados'}"
        })

    except Exception as e:
        logger.error(f"Erro ao toggle serviços: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


logger.info("✅ Rotas de melhorias carregadas com sucesso")
