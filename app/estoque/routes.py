#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Estoque Routes
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

from app.estoque import bp
from app.decorators import login_required, permission_required, get_user_permissions
from app.utils import convert_objectid, allowed_file, registrar_auditoria
from app.extensions import db as get_db, get_from_cache, set_in_cache

logger = logging.getLogger(__name__)

@bp.route('/api/estoque/entrada', methods=['POST'])
@login_required
def registrar_entrada_estoque():
    '''Registrar uma nova entrada de estoque que deve ser aprovada.'''
    if db is None:
        return jsonify({'success': False}), 500

    data = request.json or {}
    try:
        produto_id = data.get('produto_id')
        if not produto_id:
            return jsonify({'success': False, 'message': 'Produto obrigatorio'}), 400

        produto = db.produtos.find_one({'_id': ObjectId(produto_id)})
        if not produto:
            return jsonify({'success': False, 'message': 'Produto nao encontrado'}), 404

        quantidade = int(data.get('quantidade', 0))
        if quantidade <= 0:
            return jsonify({'success': False, 'message': 'Quantidade invalida'}), 400

        entrada_data = {
            'produto_id': ObjectId(produto_id),
            'produto_nome': produto.get('nome'),
            'quantidade': quantidade,
            'fornecedor': data.get('fornecedor', ''),
            'motivo': data.get('motivo', 'Entrada manual'),
            'nota_fiscal': data.get('nota_fiscal', ''),
            'previsao_chegada': data.get('previsao_chegada'),
            'status': 'Pendente',
            'usuario': session.get('username', 'sistema'),
            'data': datetime.now(),
            'updated_at': datetime.now()
        }

        db.estoque_entradas_pendentes.insert_one(entrada_data)
        logger.info(f"Entrada de estoque registrada para produto {produto_id}")
        return jsonify({'success': True, 'message': 'Entrada registrada e aguardando aprovacao'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Quantidade deve ser numerica'}), 400
    except Exception as e:
        logger.error(f"Erro ao registrar entrada: {e}")
        return jsonify({'success': False, 'message': 'Erro interno ao registrar entrada'}), 500


@bp.route('/api/estoque/entrada/pendentes', methods=['GET'])


@bp.route('/api/estoque/entrada/<id>', methods=['PUT'])
@login_required
def atualizar_entrada_estoque(id):
    '''Atualizar uma entrada pendente antes da aprovacao.'''
    if db is None:
        return jsonify({'success': False}), 500

    data = request.json or {}
    try:
        entrada = db.estoque_entradas_pendentes.find_one({'_id': ObjectId(id)})
        if not entrada:
            return jsonify({'success': False, 'message': 'Entrada nao encontrada'}), 404
        if entrada.get('status') != 'Pendente':
            return jsonify({'success': False, 'message': 'Entrada ja processada'}), 400

        campos_atualizar = {}
        for campo in ['quantidade', 'fornecedor', 'motivo', 'nota_fiscal', 'previsao_chegada']:
            if campo in data:
                campos_atualizar[campo] = data[campo]

        if 'quantidade' in campos_atualizar:
            try:
                campos_atualizar['quantidade'] = int(campos_atualizar['quantidade'])
                if campos_atualizar['quantidade'] <= 0:
                    return jsonify({'success': False, 'message': 'Quantidade invalida'}), 400
            except ValueError:
                return jsonify({'success': False, 'message': 'Quantidade deve ser numerica'}), 400

        if not campos_atualizar:
            return jsonify({'success': False, 'message': 'Nenhum dado para atualizar'}), 400

        campos_atualizar['updated_at'] = datetime.now()
        db.estoque_entradas_pendentes.update_one({'_id': ObjectId(id)}, {'$set': campos_atualizar})
        logger.info(f"Entrada de estoque {id} atualizada")
        return jsonify({'success': True, 'message': 'Entrada atualizada com sucesso'})
    except Exception as e:
        logger.error(f"Erro ao atualizar entrada: {e}")
        return jsonify({'success': False, 'message': 'Erro ao atualizar entrada'}), 500


@bp.route('/api/estoque/entrada/<id>/aprovar', methods=['POST'])


@bp.route('/api/estoque/entrada/<id>/rejeitar', methods=['POST'])
@login_required
def rejeitar_entrada_estoque(id):
    '''Rejeitar uma entrada pendente de estoque.'''
    if db is None:
        return jsonify({'success': False}), 500

    data = request.json or {}
    try:
        entrada = db.estoque_entradas_pendentes.find_one({'_id': ObjectId(id)})
        if not entrada:
            return jsonify({'success': False, 'message': 'Entrada nao encontrada'}), 404
        if entrada.get('status') != 'Pendente':
            return jsonify({'success': False, 'message': 'Entrada ja processada'}), 400

        motivo = data.get('motivo', '').strip() or 'Rejeitada sem motivo informado'
        db.estoque_entradas_pendentes.update_one({
            '_id': ObjectId(id)
        }, {
            '$set': {'status': 'Rejeitado', 'motivo_rejeicao': motivo, 'rejeitado_em': datetime.now(), 'rejeitado_por': session.get('username')}})

        logger.info(f"Entrada de estoque {id} rejeitada")
        return jsonify({'success': True, 'message': 'Entrada rejeitada'})
    except Exception as e:
        logger.error(f"Erro ao rejeitar entrada: {e}")
        return jsonify({'success': False, 'message': 'Erro ao rejeitar entrada'}), 500


@bp.route('/api/estoque/alerta')


@bp.route('/api/estoque/movimentacao', methods=['POST'])
@login_required
def estoque_movimentacao():
    if db is None:
        return jsonify({'success': False}), 500
    data = request.json
    try:
        produto = db.produtos.find_one({'_id': ObjectId(data['produto_id'])})
        if not produto:
            return jsonify({'success': False})
        qtd = int(data['quantidade'])
        tipo = data['tipo']
        novo_estoque = produto.get('estoque', 0)
        if tipo == 'entrada':
            novo_estoque += qtd
        else:
            novo_estoque -= qtd
        db.produtos.update_one({'_id': ObjectId(data['produto_id'])}, {'$set': {'estoque': novo_estoque}})
        db.estoque_movimentacoes.insert_one({'produto_id': ObjectId(data['produto_id']), 'tipo': tipo, 'quantidade': qtd, 'motivo': data.get('motivo', ''), 'usuario': session.get('username'), 'data': datetime.now()})
        return jsonify({'success': True})
    except:
        return jsonify({'success': False}), 500

@bp.route('/api/estoque/movimentacoes', methods=['GET'])


@bp.route('/api/estoque/saida', methods=['POST'])
@login_required
def registrar_saida_estoque():
    """Registrar saída de estoque"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    data = request.json or {}
    try:
        produto_id = data.get('produto_id')
        quantidade = int(data.get('quantidade', 0))
        motivo = data.get('motivo', '')
        
        if not produto_id or quantidade <= 0:
            return jsonify({'success': False, 'message': 'Dados inválidos'}), 400
        
        # Verificar se produto existe
        produto = db.produtos.find_one({'_id': ObjectId(produto_id)})
        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
        
        # Verificar estoque disponível
        estoque_atual = produto.get('estoque', 0)
        if estoque_atual < quantidade:
            return jsonify({
                'success': False, 
                'message': f'Estoque insuficiente. Disponível: {estoque_atual}'
            }), 400
        
        # Atualizar estoque
        novo_estoque = estoque_atual - quantidade
        db.produtos.update_one(
            {'_id': ObjectId(produto_id)},
            {'$set': {'estoque': novo_estoque, 'updated_at': datetime.now()}}
        )
        
        # Registrar movimentação
        movimentacao = {
            'produto_id': ObjectId(produto_id),
            'produto_nome': produto.get('nome'),
            'tipo': 'saida',
            'quantidade': quantidade,
            'motivo': motivo,
            'usuario': session.get('username', 'Desconhecido'),
            'data': datetime.now()
        }
        db.estoque_movimentacoes.insert_one(movimentacao)
        
        return jsonify({
            'success': True,
            'message': 'Saída registrada com sucesso',
            'estoque_atual': novo_estoque
        })
        
    except Exception as e:
        logger.error(f"Erro ao registrar saída: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/api/estoque/relatorio', methods=['GET'])


@bp.route('/api/estoque/produtos/entrada', methods=['POST'])
@login_required
def registrar_entrada_produto():
    """Registra entrada de produto que precisa ser aprovada"""
    try:
        data = request.get_json()
        
        produto = db.produtos.find_one({'_id': ObjectId(data.get('produto_id'))})
        if not produto:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
        
        entrada = {
            'produto_id': ObjectId(data.get('produto_id')),
            'produto_nome': produto.get('nome'),
            'quantidade': data.get('quantidade'),
            'fornecedor': data.get('fornecedor'),
            'motivo': data.get('motivo'),
            'usuario': session.get('user', {}).get('name', 'Desconhecido'),
            'status': 'pendente',
            'data_solicitacao': datetime.now(),
            'data_processamento': None
        }
        
        result = db.estoque_pendencias.insert_one(entrada)
        entrada['_id'] = str(result.inserted_id)
        
        return jsonify({'success': True, 'entrada': entrada, 'message': 'Entrada registrada. Aguardando aprovação.'})
    except Exception as e:
        logger.error(f"Erro ao registrar entrada: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 9. Aprovar Entrada de Produto
@bp.route('/api/estoque/produtos/aprovar/<id>', methods=['POST'])


@bp.route('/api/estoque/produtos/rejeitar/<id>', methods=['POST'])
@login_required
def rejeitar_entrada_produto(id):
    """Rejeita entrada de produto"""
    try:
        db.estoque_pendencias.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'status': 'rejeitado', 'data_processamento': datetime.now()}}
        )
        
        return jsonify({'success': True, 'message': 'Entrada rejeitada'})
    except Exception as e:
        logger.error(f"Erro ao rejeitar entrada: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# 11. Listar Entradas Pendentes
@bp.route('/api/estoque/produtos/pendentes', methods=['GET'])


@bp.route('/api/estoque/visao-geral', methods=['GET'])
@login_required
def estoque_visao_geral():
    """Retorna visão geral do estoque com estatísticas"""
    try:
        # Buscar todos os produtos ativos
        produtos = list(db.produtos.find({'status': 'Ativo'}))
        
        total_produtos = len(produtos)
        valor_total_estoque = 0
        alertas_estoque = 0
        
        produtos_formatados = []
        
        for p in produtos:
            estoque_atual = int(p.get('estoque', 0))
            estoque_minimo = int(p.get('estoque_minimo', 0))
            preco = float(p.get('preco', 0))
            valor_total = estoque_atual * preco
            
            valor_total_estoque += valor_total
            
            # Verificar alertas
            if estoque_atual <= estoque_minimo * 1.5:
                alertas_estoque += 1
            
            # Determinar status
            if estoque_atual <= estoque_minimo:
                nivel = 'Crítico'
            elif estoque_atual < estoque_minimo * 1.5:
                nivel = 'Baixo'
            else:
                nivel = 'Normal'
            
            produtos_formatados.append({
                'id': str(p['_id']),
                'nome': p.get('nome', 'Sem nome'),
                'marca': p.get('marca', 'Sem marca'),
                'estoque_atual': estoque_atual,
                'estoque_minimo': estoque_minimo,
                'preco_unitario': preco,
                'valor_total': round(valor_total, 2),
                'nivel': nivel
            })
        
        # Buscar movimentações do mês atual
        inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        movimentacoes_mes = db.estoque_movimentacoes.count_documents({
            'data': {'$gte': inicio_mes}
        })
        
        resultado = {
            'estatisticas': {
                'total_produtos': total_produtos,
                'valor_estoque': round(valor_total_estoque, 2),
                'alertas': alertas_estoque,
                'movimentacoes_mes': movimentacoes_mes
            },
            'produtos': produtos_formatados
        }
        
        logger.info(f"📊 Visão Geral - {total_produtos} produtos, R$ {valor_total_estoque:.2f}, {alertas_estoque} alertas")
        return jsonify({'success': True, 'data': resultado})
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar visão geral do estoque: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/estoque/alertas', methods=['GET'])


@bp.route('/api/estoque/relatorio', methods=['GET'])
@login_required
def gerar_relatorio_estoque():
    """Gera relatório de estoque personalizado"""
    try:
        tipo = request.args.get('tipo', 'movimentacoes')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Converter datas
        if data_inicio:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        else:
            data_inicio = datetime.now() - timedelta(days=30)
        
        if data_fim:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            data_fim = data_fim.replace(hour=23, minute=59, second=59)
        else:
            data_fim = datetime.now()
        
        resultado = {}
        
        if tipo == 'movimentacoes':
            # Relatório de movimentações
            movimentacoes = list(db.estoque_movimentacoes.find({
                'data': {'$gte': data_inicio, '$lte': data_fim}
            }).sort('data', DESCENDING))
            
            entradas = 0
            saidas = 0
            movs_formatadas = []
            
            for m in movimentacoes:
                produto = db.produtos.find_one({'_id': ObjectId(m['produto_id'])})
                produto_nome = produto.get('nome', 'Desconhecido') if produto else 'Desconhecido'
                
                responsavel_nome = 'Sistema'
                if m.get('responsavel_id'):
                    responsavel = db.profissionais.find_one({'_id': ObjectId(m['responsavel_id'])})
                    if not responsavel:
                        responsavel = db.assistentes.find_one({'_id': ObjectId(m['responsavel_id'])})
                    if responsavel:
                        responsavel_nome = responsavel.get('nome', 'Desconhecido')
                
                tipo_mov = m.get('tipo', 'Entrada')
                quantidade = int(m.get('quantidade', 0))
                
                if tipo_mov == 'Entrada':
                    entradas += quantidade
                else:
                    saidas += quantidade
                
                movs_formatadas.append({
                    'data': m['data'].strftime('%d/%m/%Y %H:%M'),
                    'tipo': tipo_mov,
                    'produto': produto_nome,
                    'quantidade': quantidade,
                    'motivo': m.get('motivo', ''),
                    'responsavel': responsavel_nome
                })
            
            resultado = {
                'tipo': 'movimentacoes',
                'periodo': {
                    'inicio': data_inicio.strftime('%d/%m/%Y'),
                    'fim': data_fim.strftime('%d/%m/%Y')
                },
                'resumo': {
                    'total_movimentacoes': len(movimentacoes),
                    'total_entradas': entradas,
                    'total_saidas': saidas,
                    'saldo': entradas - saidas
                },
                'movimentacoes': movs_formatadas
            }
            
        elif tipo == 'posicao':
            # Relatório de posição de estoque
            produtos = list(db.produtos.find({'status': 'Ativo'}))
            
            produtos_formatados = []
            for p in produtos:
                produtos_formatados.append({
                    'nome': p.get('nome', 'Sem nome'),
                    'marca': p.get('marca', 'Sem marca'),
                    'estoque_atual': int(p.get('estoque', 0)),
                    'estoque_minimo': int(p.get('estoque_minimo', 0)),
                    'status': 'Normal' if int(p.get('estoque', 0)) > int(p.get('estoque_minimo', 0)) * 1.5 else ('Baixo' if int(p.get('estoque', 0)) > int(p.get('estoque_minimo', 0)) else 'Crítico')
                })
            
            resultado = {
                'tipo': 'posicao',
                'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'total_produtos': len(produtos),
                'produtos': produtos_formatados
            }
            
        elif tipo == 'valorizado':
            # Relatório de estoque valorizado
            produtos = list(db.produtos.find({'status': 'Ativo'}))
            
            valor_total = 0
            produtos_formatados = []
            
            for p in produtos:
                estoque = int(p.get('estoque', 0))
                preco = float(p.get('preco', 0))
                valor = estoque * preco
                valor_total += valor
                
                produtos_formatados.append({
                    'nome': p.get('nome', 'Sem nome'),
                    'marca': p.get('marca', 'Sem marca'),
                    'estoque': estoque,
                    'preco_unitario': preco,
                    'valor_total': round(valor, 2)
                })
            
            # Ordenar por valor total
            produtos_formatados.sort(key=lambda x: x['valor_total'], reverse=True)
            
            resultado = {
                'tipo': 'valorizado',
                'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'valor_total_estoque': round(valor_total, 2),
                'total_produtos': len(produtos),
                'produtos': produtos_formatados
            }
            
        elif tipo == 'criticos':
            # Relatório de produtos críticos
            produtos = list(db.produtos.find({'status': 'Ativo'}))
            
            criticos = []
            atencao = []
            
            for p in produtos:
                estoque_atual = int(p.get('estoque', 0))
                estoque_minimo = int(p.get('estoque_minimo', 0))
                
                if estoque_atual <= estoque_minimo:
                    criticos.append({
                        'nome': p.get('nome', 'Sem nome'),
                        'marca': p.get('marca', 'Sem marca'),
                        'estoque_atual': estoque_atual,
                        'estoque_minimo': estoque_minimo,
                        'diferenca': estoque_atual - estoque_minimo,
                        'nivel': 'Crítico'
                    })
                elif estoque_atual < estoque_minimo * 1.5:
                    atencao.append({
                        'nome': p.get('nome', 'Sem nome'),
                        'marca': p.get('marca', 'Sem marca'),
                        'estoque_atual': estoque_atual,
                        'estoque_minimo': estoque_minimo,
                        'diferenca': estoque_atual - estoque_minimo,
                        'nivel': 'Atenção'
                    })
            
            resultado = {
                'tipo': 'criticos',
                'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'total_criticos': len(criticos),
                'total_atencao': len(atencao),
                'produtos_criticos': criticos,
                'produtos_atencao': atencao
            }
        
        logger.info(f"📄 Relatório gerado: {tipo} ({data_inicio.strftime('%d/%m/%Y')} - {data_fim.strftime('%d/%m/%Y')})")
        return jsonify({'success': True, 'relatorio': resultado})
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar relatório de estoque: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== FIM ENDPOINTS SUB-TABS ====================


# ==================== ROTAS ADMINISTRATIVAS ====================

@bp.route('/api/admin/reset-database', methods=['POST'])
