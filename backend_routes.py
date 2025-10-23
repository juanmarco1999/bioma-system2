from flask import Blueprint, request, jsonify, current_app, session
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import base64
from bson import ObjectId
from functools import wraps
import logging
from pymongo import ASCENDING, DESCENDING
from PIL import Image
import io

logger = logging.getLogger(__name__)
api = Blueprint('api', __name__)

# ==================== HELPER FUNCTIONS ====================

def get_db():
    """Obtém a conexão com o banco de dados do app atual"""
    return current_app.config.get('DB_CONNECTION')

def convert_objectid(data):
    """Converte ObjectId para string em dicionários e listas"""
    if isinstance(data, list):
        return [{**item, '_id': str(item['_id'])} if '_id' in item else item for item in data]
    elif isinstance(data, dict) and '_id' in data:
        return {**data, '_id': str(data['_id'])}
    return data

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})

# Rota para upload de logo
@api.route('/api/config/logo', methods=['POST'])
def upload_logo():
    if 'logo' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'})
    
    file = request.files['logo']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({
            'success': True,
            'logo_url': f'/uploads/{filename}',
            'message': 'Logo atualizado com sucesso'
        })
    return jsonify({'success': False, 'message': 'Tipo de arquivo não permitido'})

# Rota para editar produtos
@api.route('/api/produtos/<id>', methods=['PUT'])
def update_produto(id):
    data = request.json
    db = get_db()
    
    try:
        result = db.produtos.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'nome': data.get('nome'),
                'descricao': data.get('descricao'),
                'preco': float(data.get('preco', 0)),
                'estoque': int(data.get('estoque', 0)),
                'estoque_minimo': int(data.get('estoque_minimo', 0)),
                'categoria': data.get('categoria'),
                'marca': data.get('marca'),
                'updated_at': datetime.utcnow()
            }}
        )
        return jsonify({'success': True, 'message': 'Produto atualizado'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Rota para entradas no estoque
@api.route('/api/estoque/entrada', methods=['POST'])
def registrar_entrada():
    data = request.json
    db = get_db()
    
    try:
        produto_id = ObjectId(data['produto_id'])
        quantidade = int(data['quantidade'])
        
        # Registra a entrada
        entrada = {
            'produto_id': produto_id,
            'quantidade': quantidade,
            'tipo': 'entrada',
            'data': datetime.utcnow(),
            'responsavel_id': ObjectId(session.get('user_id')),
            'observacao': data.get('observacao', ''),
            'status': 'pendente'
        }
        db.estoque_movimentacoes.insert_one(entrada)
        
        return jsonify({'success': True, 'message': 'Entrada registrada'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Rota para aprovar/reprovar movimentações de estoque
@api.route('/api/estoque/movimentacao/<id>/status', methods=['PUT'])
def atualizar_status_movimentacao(id):
    data = request.json
    db = get_db()
    
    try:
        status = data['status']
        if status not in ['aprovado', 'reprovado']:
            return jsonify({'success': False, 'message': 'Status inválido'})
            
        mov = db.estoque_movimentacoes.find_one({'_id': ObjectId(id)})
        if not mov:
            return jsonify({'success': False, 'message': 'Movimentação não encontrada'})
            
        if status == 'aprovado':
            # Atualiza o estoque do produto
            db.produtos.update_one(
                {'_id': mov['produto_id']},
                {'$inc': {'estoque': mov['quantidade']}}
            )
            
        # Atualiza o status da movimentação
        db.estoque_movimentacoes.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'status': status,
                'aprovado_por': ObjectId(session.get('user_id')),
                'data_aprovacao': datetime.utcnow()
            }}
        )
        
        return jsonify({'success': True, 'message': f'Movimentação {status}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Rota para editar serviços
@api.route('/api/servicos/<id>', methods=['PUT'])
def update_servico(id):
    data = request.json
    db = get_db()
    
    try:
        result = db.servicos.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'nome': data.get('nome'),
                'descricao': data.get('descricao'),
                'preco': float(data.get('preco', 0)),
                'duracao': int(data.get('duracao', 60)),
                'categoria': data.get('categoria'),
                'updated_at': datetime.utcnow()
            }}
        )
        return jsonify({'success': True, 'message': 'Serviço atualizado'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Rota para atualizar dados do profissional incluindo foto
@api.route('/api/profissionais/<id>/foto', methods=['POST'])
def update_foto_profissional(id):
    if 'foto' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhuma foto enviada'})
        
    file = request.files['foto']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'})
        
    if file and allowed_file(file.filename):
        filename = f"prof_{id}_{secure_filename(file.filename)}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        db = get_db()
        db.profissionais.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'foto_url': f'/uploads/{filename}'}}
        )
        
        return jsonify({
            'success': True,
            'foto_url': f'/uploads/{filename}',
            'message': 'Foto atualizada com sucesso'
        })
    return jsonify({'success': False, 'message': 'Tipo de arquivo não permitido'})

# Rota para associar anamnese ao cliente
@api.route('/api/clientes/<id>/anamnese', methods=['POST'])
def adicionar_anamnese(id):
    data = request.json
    db = get_db()
    
    try:
        anamnese = {
            'cliente_id': ObjectId(id),
            'respostas': data['respostas'],
            'data': datetime.utcnow(),
            'created_by': ObjectId(session.get('user_id'))
        }
        
        result = db.anamneses.insert_one(anamnese)
        return jsonify({'success': True, 'message': 'Anamnese registrada'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Rota para pegar o histórico de faturamento do cliente
@api.route('/api/clientes/<id>/faturamento', methods=['GET'])
def get_faturamento_cliente(id):
    db = get_db()
    
    try:
        pipeline = [
            {'$match': {'cliente_id': ObjectId(id)}},
            {'$group': {
                '_id': None,
                'total': {'$sum': '$total_final'},
                'contagem': {'$sum': 1}
            }}
        ]
        
        result = list(db.orcamentos.aggregate(pipeline))
        
        if result:
            return jsonify({
                'success': True,
                'total': result[0]['total'],
                'quantidade_orcamentos': result[0]['contagem']
            })
        return jsonify({'success': True, 'total': 0, 'quantidade_orcamentos': 0})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ==================== SISTEMA DE PERFIS DE ACESSO ====================

@api.route('/api/perfil/tipo', methods=['GET'])
def get_tipo_perfil():
    """Retorna o tipo de perfil do usuário logado"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Não autorizado'}), 401

        db = get_db()
        user = db.usuarios.find_one({'_id': ObjectId(user_id)})

        if not user:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404

        tipo_perfil = user.get('tipo_perfil', 'Profissional')  # Default: Profissional

        return jsonify({
            'success': True,
            'tipo_perfil': tipo_perfil,
            'permissoes': get_permissoes_perfil(tipo_perfil)
        })
    except Exception as e:
        logger.error(f"Erro ao buscar tipo de perfil: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/perfil/atualizar-tipo', methods=['PUT'])
def atualizar_tipo_perfil():
    """Atualiza o tipo de perfil do usuário (apenas Admin)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Não autorizado'}), 401

        db = get_db()
        user_logado = db.usuarios.find_one({'_id': ObjectId(user_id)})

        # Verificar se é Admin
        if user_logado.get('tipo_perfil') != 'Admin':
            return jsonify({'success': False, 'message': 'Apenas administradores podem alterar perfis'}), 403

        data = request.json
        target_user_id = data.get('user_id')
        novo_tipo = data.get('tipo_perfil')

        if novo_tipo not in ['Admin', 'Gestão', 'Profissional']:
            return jsonify({'success': False, 'message': 'Tipo de perfil inválido'}), 400

        result = db.usuarios.update_one(
            {'_id': ObjectId(target_user_id)},
            {'$set': {'tipo_perfil': novo_tipo, 'updated_at': datetime.utcnow()}}
        )

        if result.modified_count > 0:
            logger.info(f"Perfil atualizado para {novo_tipo} - User ID: {target_user_id}")
            return jsonify({'success': True, 'message': 'Perfil atualizado com sucesso'})
        else:
            return jsonify({'success': False, 'message': 'Nenhuma alteração realizada'}), 400

    except Exception as e:
        logger.error(f"Erro ao atualizar tipo de perfil: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

def get_permissoes_perfil(tipo_perfil):
    """Retorna as permissões baseadas no tipo de perfil"""
    permissoes = {
        'Admin': {
            'ver_relatorios': True,
            'gerenciar_usuarios': True,
            'gerenciar_configuracoes': True,
            'gerenciar_financeiro': True,
            'gerenciar_estoque': True,
            'criar_orcamentos': True,
            'aprovar_orcamentos': True,
            'gerenciar_comissoes': True
        },
        'Gestão': {
            'ver_relatorios': True,
            'gerenciar_usuarios': False,
            'gerenciar_configuracoes': False,
            'gerenciar_financeiro': True,
            'gerenciar_estoque': True,
            'criar_orcamentos': True,
            'aprovar_orcamentos': True,
            'gerenciar_comissoes': True
        },
        'Profissional': {
            'ver_relatorios': False,
            'gerenciar_usuarios': False,
            'gerenciar_configuracoes': False,
            'gerenciar_financeiro': False,
            'gerenciar_estoque': False,
            'criar_orcamentos': True,
            'aprovar_orcamentos': False,
            'gerenciar_comissoes': False
        }
    }
    return permissoes.get(tipo_perfil, permissoes['Profissional'])

# ==================== FINANCEIRO ====================

@api.route('/api/financeiro/resumo', methods=['GET'])
def financeiro_resumo():
    """Retorna resumo financeiro com receitas, despesas e lucro"""
    try:
        db = get_db()

        # Filtros de data
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')

        # Se não especificado, usar mês atual
        if not data_inicio:
            data_inicio = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            data_inicio = datetime.fromisoformat(data_inicio)

        if not data_fim:
            data_fim = datetime.now()
        else:
            data_fim = datetime.fromisoformat(data_fim)

        # Calcular receitas (orçamentos aprovados)
        pipeline_receitas = [
            {
                '$match': {
                    'status': 'Aprovado',
                    'data_criacao': {'$gte': data_inicio, '$lte': data_fim}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total_receitas': {'$sum': '$total_final'},
                    'quantidade': {'$sum': 1}
                }
            }
        ]

        resultado_receitas = list(db.orcamentos.aggregate(pipeline_receitas))
        total_receitas = resultado_receitas[0]['total_receitas'] if resultado_receitas else 0
        qtd_orcamentos = resultado_receitas[0]['quantidade'] if resultado_receitas else 0

        # Calcular despesas
        pipeline_despesas = [
            {
                '$match': {
                    'data': {'$gte': data_inicio, '$lte': data_fim}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total_despesas': {'$sum': '$valor'},
                    'quantidade': {'$sum': 1}
                }
            }
        ]

        resultado_despesas = list(db.despesas.aggregate(pipeline_despesas))
        total_despesas = resultado_despesas[0]['total_despesas'] if resultado_despesas else 0
        qtd_despesas = resultado_despesas[0]['quantidade'] if resultado_despesas else 0

        # Calcular comissões a pagar
        pipeline_comissoes = [
            {
                '$match': {
                    'data_orcamento': {'$gte': data_inicio, '$lte': data_fim},
                    'status': 'pendente'
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total_comissoes': {'$sum': '$valor_comissao'}
                }
            }
        ]

        resultado_comissoes = list(db.comissoes.aggregate(pipeline_comissoes))
        total_comissoes = resultado_comissoes[0]['total_comissoes'] if resultado_comissoes else 0

        # Calcular lucro
        lucro_bruto = total_receitas - total_despesas
        lucro_liquido = lucro_bruto - total_comissoes

        return jsonify({
            'success': True,
            'data': {
                'receitas': {
                    'total': round(total_receitas, 2),
                    'quantidade': qtd_orcamentos
                },
                'despesas': {
                    'total': round(total_despesas, 2),
                    'quantidade': qtd_despesas
                },
                'comissoes': {
                    'total': round(total_comissoes, 2)
                },
                'lucro_bruto': round(lucro_bruto, 2),
                'lucro_liquido': round(lucro_liquido, 2),
                'margem_lucro': round((lucro_liquido / total_receitas * 100) if total_receitas > 0 else 0, 2)
            }
        })

    except Exception as e:
        logger.error(f"Erro ao buscar resumo financeiro: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/financeiro/despesas', methods=['GET'])
def listar_despesas():
    """Lista todas as despesas com paginação"""
    try:
        db = get_db()

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        skip = (page - 1) * per_page

        # Filtros
        filtro = {}

        data_inicio = request.args.get('data_inicio')
        if data_inicio:
            filtro['data'] = {'$gte': datetime.fromisoformat(data_inicio)}

        data_fim = request.args.get('data_fim')
        if data_fim:
            if 'data' in filtro:
                filtro['data']['$lte'] = datetime.fromisoformat(data_fim)
            else:
                filtro['data'] = {'$lte': datetime.fromisoformat(data_fim)}

        categoria = request.args.get('categoria')
        if categoria:
            filtro['categoria'] = categoria

        total = db.despesas.count_documents(filtro)
        despesas = list(db.despesas.find(filtro).sort('data', DESCENDING).skip(skip).limit(per_page))

        return jsonify({
            'success': True,
            'despesas': convert_objectid(despesas),
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })

    except Exception as e:
        logger.error(f"Erro ao listar despesas: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/financeiro/despesas', methods=['POST'])
def adicionar_despesa():
    """Adiciona uma nova despesa"""
    try:
        db = get_db()
        data = request.json

        despesa = {
            'descricao': data.get('descricao'),
            'categoria': data.get('categoria'),
            'valor': float(data.get('valor', 0)),
            'data': datetime.fromisoformat(data.get('data')) if data.get('data') else datetime.now(),
            'observacoes': data.get('observacoes', ''),
            'created_by': ObjectId(session.get('user_id')),
            'created_at': datetime.utcnow()
        }

        result = db.despesas.insert_one(despesa)
        logger.info(f"Despesa criada - ID: {result.inserted_id}, Valor: R$ {despesa['valor']}")

        return jsonify({
            'success': True,
            'message': 'Despesa adicionada com sucesso',
            'id': str(result.inserted_id)
        })

    except Exception as e:
        logger.error(f"Erro ao adicionar despesa: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== IMPRESSÃO E WHATSAPP ====================

@api.route('/api/orcamento/<id>/imprimir', methods=['GET'])
def preparar_impressao_orcamento(id):
    """Retorna dados formatados do orçamento para impressão"""
    try:
        db = get_db()
        orcamento = db.orcamentos.find_one({'_id': ObjectId(id)})

        if not orcamento:
            return jsonify({'success': False, 'message': 'Orçamento não encontrado'}), 404

        # Buscar dados do cliente
        cliente = db.clientes.find_one({'_id': orcamento.get('cliente_id')})

        # Formatar dados para impressão
        dados_impressao = {
            'numero': orcamento.get('numero'),
            'data': orcamento.get('data_criacao').strftime('%d/%m/%Y %H:%M') if orcamento.get('data_criacao') else '',
            'cliente': {
                'nome': cliente.get('nome') if cliente else orcamento.get('cliente_nome'),
                'cpf': cliente.get('cpf') if cliente else orcamento.get('cliente_cpf'),
                'telefone': cliente.get('telefone') if cliente else orcamento.get('cliente_telefone'),
                'email': cliente.get('email') if cliente else orcamento.get('cliente_email')
            },
            'servicos': orcamento.get('servicos', []),
            'produtos': orcamento.get('produtos', []),
            'profissionais': orcamento.get('profissionais', []),
            'subtotal_servicos': orcamento.get('subtotal_servicos', 0),
            'subtotal_produtos': orcamento.get('subtotal_produtos', 0),
            'desconto_total': orcamento.get('desconto_total', 0),
            'total_final': orcamento.get('total_final', 0),
            'observacoes': orcamento.get('observacoes', ''),
            'status': orcamento.get('status', 'Pendente')
        }

        return jsonify({'success': True, 'dados': dados_impressao})

    except Exception as e:
        logger.error(f"Erro ao preparar impressão de orçamento: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/orcamento/<id>/whatsapp', methods=['GET'])
def gerar_link_whatsapp_orcamento(id):
    """Gera link do WhatsApp com mensagem do orçamento"""
    try:
        db = get_db()
        orcamento = db.orcamentos.find_one({'_id': ObjectId(id)})

        if not orcamento:
            return jsonify({'success': False, 'message': 'Orçamento não encontrado'}), 404

        # Buscar dados do cliente
        cliente = db.clientes.find_one({'_id': orcamento.get('cliente_id')})

        if not cliente or not cliente.get('telefone'):
            return jsonify({'success': False, 'message': 'Cliente sem telefone cadastrado'}), 400

        # Formatar telefone (remover caracteres especiais)
        telefone = ''.join(filter(str.isdigit, cliente.get('telefone', '')))

        # Criar mensagem
        mensagem = f"""*BIOMA UBERABA - Orçamento #{orcamento.get('numero')}*

Olá {cliente.get('nome', '')}!

Segue o orçamento solicitado:

*Serviços:*
"""

        for servico in orcamento.get('servicos', []):
            mensagem += f"• {servico.get('nome')} - R$ {servico.get('preco_total', 0):.2f}\n"

        if orcamento.get('produtos'):
            mensagem += "\n*Produtos:*\n"
            for produto in orcamento.get('produtos', []):
                mensagem += f"• {produto.get('nome')} - R$ {produto.get('preco_total', 0):.2f}\n"

        mensagem += f"\n*TOTAL: R$ {orcamento.get('total_final', 0):.2f}*"

        # Gerar link WhatsApp
        link_whatsapp = f"https://wa.me/55{telefone}?text={mensagem}"

        return jsonify({
            'success': True,
            'link': link_whatsapp,
            'telefone': telefone
        })

    except Exception as e:
        logger.error(f"Erro ao gerar link WhatsApp: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/contrato/<id>/imprimir', methods=['GET'])
def preparar_impressao_contrato(id):
    """Retorna dados formatados do contrato para impressão"""
    try:
        db = get_db()
        contrato = db.contratos.find_one({'_id': ObjectId(id)})

        if not contrato:
            return jsonify({'success': False, 'message': 'Contrato não encontrado'}), 404

        # Buscar orçamento relacionado
        orcamento = db.orcamentos.find_one({'_id': contrato.get('orcamento_id')})

        # Buscar dados do cliente
        cliente = db.clientes.find_one({'_id': contrato.get('cliente_id')})

        dados_impressao = {
            'numero': contrato.get('numero'),
            'data': contrato.get('data_criacao').strftime('%d/%m/%Y') if contrato.get('data_criacao') else '',
            'cliente': convert_objectid(cliente) if cliente else {},
            'orcamento': convert_objectid(orcamento) if orcamento else {},
            'termos': contrato.get('termos', ''),
            'valor_total': contrato.get('valor_total', 0),
            'forma_pagamento': contrato.get('forma_pagamento', ''),
            'status': contrato.get('status', 'Ativo')
        }

        return jsonify({'success': True, 'dados': dados_impressao})

    except Exception as e:
        logger.error(f"Erro ao preparar impressão de contrato: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/contrato/<id>/whatsapp', methods=['GET'])
def gerar_link_whatsapp_contrato(id):
    """Gera link do WhatsApp com mensagem do contrato"""
    try:
        db = get_db()
        contrato = db.contratos.find_one({'_id': ObjectId(id)})

        if not contrato:
            return jsonify({'success': False, 'message': 'Contrato não encontrado'}), 404

        cliente = db.clientes.find_one({'_id': contrato.get('cliente_id')})

        if not cliente or not cliente.get('telefone'):
            return jsonify({'success': False, 'message': 'Cliente sem telefone cadastrado'}), 400

        telefone = ''.join(filter(str.isdigit, cliente.get('telefone', '')))

        mensagem = f"""*BIOMA UBERABA - Contrato #{contrato.get('numero')}*

Olá {cliente.get('nome', '')}!

Seu contrato foi gerado com sucesso.

*Valor Total:* R$ {contrato.get('valor_total', 0):.2f}
*Forma de Pagamento:* {contrato.get('forma_pagamento', 'A definir')}

Para mais detalhes, entre em contato conosco.

Obrigado!"""

        link_whatsapp = f"https://wa.me/55{telefone}?text={mensagem}"

        return jsonify({
            'success': True,
            'link': link_whatsapp,
            'telefone': telefone
        })

    except Exception as e:
        logger.error(f"Erro ao gerar link WhatsApp do contrato: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== NOTIFICAÇÕES INTELIGENTES - FILA ====================

@api.route('/api/fila/notificar', methods=['POST'])
def notificar_cliente_fila():
    """Envia notificação inteligente para cliente na fila"""
    try:
        db = get_db()
        data = request.json

        agendamento_id = data.get('agendamento_id')
        agendamento = db.agendamentos.find_one({'_id': ObjectId(agendamento_id)})

        if not agendamento:
            return jsonify({'success': False, 'message': 'Agendamento não encontrado'}), 404

        cliente = db.clientes.find_one({'_id': agendamento.get('cliente_id')})

        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404

        # Calcular posição na fila
        horario_agendamento = agendamento.get('horario')
        profissional_id = agendamento.get('profissional_id')

        # Contar quantos agendamentos estão antes
        agendamentos_anteriores = db.agendamentos.count_documents({
            'profissional_id': profissional_id,
            'horario': {'$lt': horario_agendamento},
            'status': {'$in': ['Aguardando', 'Em Atendimento']},
            'data': agendamento.get('data')
        })

        posicao_fila = agendamentos_anteriores + 1

        # Estimar tempo de espera (média de 45 minutos por atendimento)
        tempo_estimado = posicao_fila * 45

        # Determinar tipo de mensagem
        if posicao_fila == 1:
            mensagem = f"Olá {cliente.get('nome')}, equipe Bioma passa para confirmar seu atendimento que será iniciado às {horario_agendamento.strftime('%H:%M')}."
        else:
            mensagem = f"Olá {cliente.get('nome')}, você está na posição {posicao_fila} da fila. O seu atendimento será realizado em aproximadamente {tempo_estimado} minutos."

        # Registrar notificação
        notificacao = {
            'cliente_id': cliente['_id'],
            'agendamento_id': ObjectId(agendamento_id),
            'tipo': 'fila',
            'mensagem': mensagem,
            'posicao': posicao_fila,
            'tempo_estimado': tempo_estimado,
            'enviado_em': datetime.utcnow(),
            'status': 'enviado'
        }

        db.notificacoes.insert_one(notificacao)

        logger.info(f"Notificação enviada - Cliente: {cliente.get('nome')}, Posição: {posicao_fila}")

        return jsonify({
            'success': True,
            'message': 'Notificação enviada com sucesso',
            'dados': {
                'mensagem': mensagem,
                'posicao': posicao_fila,
                'tempo_estimado': tempo_estimado
            }
        })

    except Exception as e:
        logger.error(f"Erro ao notificar cliente na fila: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== TRATAMENTO DE IMAGENS ====================

def redimensionar_imagem(image_file, max_width=400, max_height=400):
    """Redimensiona imagem mantendo proporção"""
    try:
        img = Image.open(image_file)

        # Converter RGBA para RGB se necessário
        if img.mode == 'RGBA':
            img = img.convert('RGB')

        # Calcular nova dimensão mantendo proporção
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        # Salvar em buffer
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)

        return output

    except Exception as e:
        logger.error(f"Erro ao redimensionar imagem: {e}")
        raise

@api.route('/api/config/logo', methods=['POST'])
def upload_logo_tratado():
    """Upload de logo com tratamento de imagem"""
    try:
        if 'logo' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400

        file = request.files['logo']

        if file.filename == '':
            return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400

        if file and allowed_file(file.filename):
            # Redimensionar imagem
            img_redimensionada = redimensionar_imagem(file, max_width=300, max_height=120)

            filename = f"logo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

            with open(filepath, 'wb') as f:
                f.write(img_redimensionada.read())

            # Salvar no banco
            db = get_db()
            db.configuracoes.update_one(
                {'tipo': 'logo'},
                {'$set': {
                    'logo_url': f'/uploads/{filename}',
                    'updated_at': datetime.utcnow()
                }},
                upsert=True
            )

            logger.info(f"Logo atualizado: {filename}")

            return jsonify({
                'success': True,
                'logo_url': f'/uploads/{filename}',
                'message': 'Logo atualizado com sucesso'
            })

        return jsonify({'success': False, 'message': 'Tipo de arquivo não permitido'}), 400

    except Exception as e:
        logger.error(f"Erro ao fazer upload do logo: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/config/logo', methods=['GET'])
def get_logo():
    """Retorna o logo atual"""
    try:
        db = get_db()
        config = db.configuracoes.find_one({'tipo': 'logo'})

        if config and config.get('logo_url'):
            return jsonify({
                'success': True,
                'logo_url': config['logo_url']
            })
        else:
            return jsonify({
                'success': True,
                'logo_url': None
            })

    except Exception as e:
        logger.error(f"Erro ao buscar logo: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== ROTAS OTIMIZADAS PARA CLIENTES ====================

@api.route('/api/clientes/lista-otimizada', methods=['GET'])
def listar_clientes_otimizado():
    """Lista clientes com paginação e cache para evitar carregamento infinito"""
    try:
        db = get_db()

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        skip = (page - 1) * per_page

        # Filtro de busca
        search = request.args.get('search', '')
        filtro = {}

        if search:
            filtro['$or'] = [
                {'nome': {'$regex': search, '$options': 'i'}},
                {'cpf': {'$regex': search, '$options': 'i'}},
                {'email': {'$regex': search, '$options': 'i'}},
                {'telefone': {'$regex': search, '$options': 'i'}}
            ]

        total = db.clientes.count_documents(filtro)
        clientes = list(db.clientes.find(filtro)
                       .sort('nome', ASCENDING)
                       .skip(skip)
                       .limit(per_page))

        # Enriquecer dados com faturamento
        for cliente in clientes:
            # Buscar faturamento total
            pipeline = [
                {'$match': {'cliente_id': cliente['_id'], 'status': 'Aprovado'}},
                {'$group': {'_id': None, 'total': {'$sum': '$total_final'}, 'count': {'$sum': 1}}}
            ]
            result = list(db.orcamentos.aggregate(pipeline))
            cliente['faturamento_total'] = result[0]['total'] if result else 0
            cliente['total_orcamentos'] = result[0]['count'] if result else 0

        return jsonify({
            'success': True,
            'clientes': convert_objectid(clientes),
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })

    except Exception as e:
        logger.error(f"Erro ao listar clientes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/clientes/<id>/detalhes', methods=['GET'])
def detalhes_cliente(id):
    """Retorna detalhes completos do cliente incluindo histórico"""
    try:
        db = get_db()
        cliente = db.clientes.find_one({'_id': ObjectId(id)})

        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404

        # Buscar orçamentos do cliente
        orcamentos = list(db.orcamentos.find({'cliente_id': ObjectId(id)})
                         .sort('data_criacao', DESCENDING)
                         .limit(10))

        # Calcular estatísticas
        pipeline_stats = [
            {'$match': {'cliente_id': ObjectId(id), 'status': 'Aprovado'}},
            {'$group': {
                '_id': None,
                'total_gasto': {'$sum': '$total_final'},
                'ticket_medio': {'$avg': '$total_final'},
                'total_orcamentos': {'$sum': 1}
            }}
        ]

        stats = list(db.orcamentos.aggregate(pipeline_stats))
        estatisticas = stats[0] if stats else {
            'total_gasto': 0,
            'ticket_medio': 0,
            'total_orcamentos': 0
        }

        # Buscar produtos e serviços mais utilizados
        pipeline_servicos = [
            {'$match': {'cliente_id': ObjectId(id)}},
            {'$unwind': '$servicos'},
            {'$group': {
                '_id': '$servicos.nome',
                'quantidade': {'$sum': '$servicos.quantidade'}
            }},
            {'$sort': {'quantidade': -1}},
            {'$limit': 5}
        ]

        servicos_mais_usados = list(db.orcamentos.aggregate(pipeline_servicos))

        pipeline_produtos = [
            {'$match': {'cliente_id': ObjectId(id)}},
            {'$unwind': '$produtos'},
            {'$group': {
                '_id': '$produtos.nome',
                'quantidade': {'$sum': '$produtos.quantidade'}
            }},
            {'$sort': {'quantidade': -1}},
            {'$limit': 5}
        ]

        produtos_mais_usados = list(db.orcamentos.aggregate(pipeline_produtos))

        # Buscar profissionais que atenderam
        pipeline_profissionais = [
            {'$match': {'cliente_id': ObjectId(id)}},
            {'$unwind': '$profissionais'},
            {'$group': {
                '_id': '$profissionais.id',
                'nome': {'$first': '$profissionais.nome'},
                'atendimentos': {'$sum': 1}
            }},
            {'$sort': {'atendimentos': -1}}
        ]

        profissionais_atenderam = list(db.orcamentos.aggregate(pipeline_profissionais))

        # Buscar agendamentos
        agendamentos = list(db.agendamentos.find({'cliente_id': ObjectId(id)})
                           .sort('data', DESCENDING)
                           .limit(10))

        return jsonify({
            'success': True,
            'cliente': convert_objectid(cliente),
            'estatisticas': estatisticas,
            'orcamentos_recentes': convert_objectid(orcamentos),
            'servicos_mais_usados': servicos_mais_usados,
            'produtos_mais_usados': produtos_mais_usados,
            'profissionais': profissionais_atenderam,
            'agendamentos': convert_objectid(agendamentos)
        })

    except Exception as e:
        logger.error(f"Erro ao buscar detalhes do cliente: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== ROTAS OTIMIZADAS PARA PROFISSIONAIS ====================

@api.route('/api/profissionais/lista-otimizada', methods=['GET'])
def listar_profissionais_otimizado():
    """Lista profissionais com paginação e estatísticas"""
    try:
        db = get_db()

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        skip = (page - 1) * per_page

        search = request.args.get('search', '')
        filtro = {}

        if search:
            filtro['nome'] = {'$regex': search, '$options': 'i'}

        total = db.profissionais.count_documents(filtro)
        profissionais = list(db.profissionais.find(filtro)
                            .sort('nome', ASCENDING)
                            .skip(skip)
                            .limit(per_page))

        # Enriquecer com estatísticas
        for prof in profissionais:
            # Calcular comissões ganhas
            pipeline = [
                {'$match': {'profissional_id': prof['_id']}},
                {'$group': {
                    '_id': None,
                    'total_comissoes': {'$sum': '$valor_comissao'},
                    'atendimentos': {'$sum': 1}
                }}
            ]
            result = list(db.comissoes.aggregate(pipeline))
            prof['comissoes_total'] = result[0]['total_comissoes'] if result else 0
            prof['total_atendimentos'] = result[0]['atendimentos'] if result else 0

        return jsonify({
            'success': True,
            'profissionais': convert_objectid(profissionais),
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })

    except Exception as e:
        logger.error(f"Erro ao listar profissionais: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/profissionais/<id>/detalhes', methods=['GET'])
def detalhes_profissional(id):
    """Retorna detalhes completos do profissional"""
    try:
        db = get_db()
        profissional = db.profissionais.find_one({'_id': ObjectId(id)})

        if not profissional:
            return jsonify({'success': False, 'message': 'Profissional não encontrado'}), 404

        # Estatísticas de comissões
        pipeline_comissoes = [
            {'$match': {'profissional_id': ObjectId(id)}},
            {'$group': {
                '_id': None,
                'total_comissoes': {'$sum': '$valor_comissao'},
                'comissoes_pendentes': {
                    '$sum': {'$cond': [{'$eq': ['$status', 'pendente']}, '$valor_comissao', 0]}
                },
                'comissoes_pagas': {
                    '$sum': {'$cond': [{'$eq': ['$status', 'paga']}, '$valor_comissao', 0]}
                },
                'total_atendimentos': {'$sum': 1}
            }}
        ]

        stats_comissoes = list(db.comissoes.aggregate(pipeline_comissoes))
        comissoes = stats_comissoes[0] if stats_comissoes else {
            'total_comissoes': 0,
            'comissoes_pendentes': 0,
            'comissoes_pagas': 0,
            'total_atendimentos': 0
        }

        # Buscar agendamentos
        agendamentos = list(db.agendamentos.find({'profissional_id': ObjectId(id)})
                           .sort('data', DESCENDING)
                           .limit(10))

        # Avaliações (se existir)
        avaliacoes = list(db.avaliacoes.find({'profissional_id': ObjectId(id)})
                         .sort('data', DESCENDING)
                         .limit(10))

        media_avaliacoes = 0
        if avaliacoes:
            total_notas = sum([av.get('nota', 0) for av in avaliacoes])
            media_avaliacoes = total_notas / len(avaliacoes)

        return jsonify({
            'success': True,
            'profissional': convert_objectid(profissional),
            'comissoes': comissoes,
            'agendamentos': convert_objectid(agendamentos),
            'avaliacoes': convert_objectid(avaliacoes),
            'media_avaliacoes': round(media_avaliacoes, 2)
        })

    except Exception as e:
        logger.error(f"Erro ao buscar detalhes do profissional: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== ROTAS OTIMIZADAS PARA PRODUTOS E SERVIÇOS ====================

@api.route('/api/produtos/lista-otimizada', methods=['GET'])
def listar_produtos_otimizado():
    """Lista produtos com paginação e status de estoque"""
    try:
        db = get_db()

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        skip = (page - 1) * per_page

        search = request.args.get('search', '')
        filtro = {}

        if search:
            filtro['$or'] = [
                {'nome': {'$regex': search, '$options': 'i'}},
                {'marca': {'$regex': search, '$options': 'i'}},
                {'categoria': {'$regex': search, '$options': 'i'}}
            ]

        # Filtro de status de estoque
        status_estoque = request.args.get('status_estoque')
        if status_estoque == 'critico':
            filtro['$expr'] = {'$lte': ['$estoque', '$estoque_minimo']}
        elif status_estoque == 'baixo':
            filtro['$expr'] = {'$lte': ['$estoque', {'$multiply': ['$estoque_minimo', 1.5]}]}

        total = db.produtos.count_documents(filtro)
        produtos = list(db.produtos.find(filtro)
                       .sort('nome', ASCENDING)
                       .skip(skip)
                       .limit(per_page))

        # Adicionar status de estoque
        for produto in produtos:
            estoque_atual = produto.get('estoque', 0)
            estoque_minimo = produto.get('estoque_minimo', 0)

            if estoque_atual <= estoque_minimo:
                produto['nivel_estoque'] = 'Crítico'
            elif estoque_atual <= estoque_minimo * 1.5:
                produto['nivel_estoque'] = 'Baixo'
            else:
                produto['nivel_estoque'] = 'Normal'

        return jsonify({
            'success': True,
            'produtos': convert_objectid(produtos),
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })

    except Exception as e:
        logger.error(f"Erro ao listar produtos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/servicos/lista-otimizada', methods=['GET'])
def listar_servicos_otimizado():
    """Lista serviços com paginação"""
    try:
        db = get_db()

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        skip = (page - 1) * per_page

        search = request.args.get('search', '')
        filtro = {}

        if search:
            filtro['$or'] = [
                {'nome': {'$regex': search, '$options': 'i'}},
                {'categoria': {'$regex': search, '$options': 'i'}},
                {'descricao': {'$regex': search, '$options': 'i'}}
            ]

        total = db.servicos.count_documents(filtro)
        servicos = list(db.servicos.find(filtro)
                       .sort('nome', ASCENDING)
                       .skip(skip)
                       .limit(per_page))

        return jsonify({
            'success': True,
            'servicos': convert_objectid(servicos),
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })

    except Exception as e:
        logger.error(f"Erro ao listar serviços: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== ROTAS OTIMIZADAS PARA ESTOQUE ====================

@api.route('/api/estoque/visao-geral-otimizada', methods=['GET'])
def estoque_visao_geral_otimizada():
    """Retorna visão geral do estoque otimizada para evitar carregamento infinito"""
    try:
        db = get_db()

        # Usar agregação para calcular tudo de uma vez
        pipeline = [
            {
                '$match': {'status': {'$ne': 'Inativo'}}
            },
            {
                '$group': {
                    '_id': None,
                    'total_produtos': {'$sum': 1},
                    'valor_total': {
                        '$sum': {
                            '$multiply': ['$estoque', '$preco']
                        }
                    },
                    'criticos': {
                        '$sum': {
                            '$cond': [
                                {'$lte': ['$estoque', '$estoque_minimo']},
                                1,
                                0
                            ]
                        }
                    },
                    'baixo': {
                        '$sum': {
                            '$cond': [
                                {
                                    '$and': [
                                        {'$gt': ['$estoque', '$estoque_minimo']},
                                        {'$lte': ['$estoque', {'$multiply': ['$estoque_minimo', 1.5]}]}
                                    ]
                                },
                                1,
                                0
                            ]
                        }
                    }
                }
            }
        ]

        resultado = list(db.produtos.aggregate(pipeline))

        if resultado:
            stats = resultado[0]
            return jsonify({
                'success': True,
                'data': {
                    'total_produtos': stats.get('total_produtos', 0),
                    'valor_total_estoque': round(stats.get('valor_total', 0), 2),
                    'alertas_criticos': stats.get('criticos', 0),
                    'alertas_baixo': stats.get('baixo', 0)
                }
            })
        else:
            return jsonify({
                'success': True,
                'data': {
                    'total_produtos': 0,
                    'valor_total_estoque': 0,
                    'alertas_criticos': 0,
                    'alertas_baixo': 0
                }
            })

    except Exception as e:
        logger.error(f"Erro ao buscar visão geral do estoque: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/estoque/alertas-otimizado', methods=['GET'])
def estoque_alertas_otimizado():
    """Retorna alertas de estoque de forma otimizada"""
    try:
        db = get_db()

        # Buscar apenas produtos críticos e baixos
        criticos = list(db.produtos.find({
            '$expr': {'$lte': ['$estoque', '$estoque_minimo']},
            'status': {'$ne': 'Inativo'}
        }).limit(20))

        baixo = list(db.produtos.find({
            '$and': [
                {'$expr': {'$gt': ['$estoque', '$estoque_minimo']}},
                {'$expr': {'$lte': ['$estoque', {'$multiply': ['$estoque_minimo', 1.5]}]}},
                {'status': {'$ne': 'Inativo'}}
            ]
        }).limit(20))

        return jsonify({
            'success': True,
            'criticos': convert_objectid(criticos),
            'baixo': convert_objectid(baixo)
        })

    except Exception as e:
        logger.error(f"Erro ao buscar alertas de estoque: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== ROTAS OTIMIZADAS PARA AGENDAMENTOS ====================

@api.route('/api/agendamentos/lista-otimizada', methods=['GET'])
def listar_agendamentos_otimizado():
    """Lista agendamentos com paginação e filtros"""
    try:
        db = get_db()

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        skip = (page - 1) * per_page

        # Filtros
        filtro = {}

        data_inicio = request.args.get('data_inicio')
        if data_inicio:
            filtro['data'] = {'$gte': datetime.fromisoformat(data_inicio)}

        data_fim = request.args.get('data_fim')
        if data_fim:
            if 'data' in filtro:
                filtro['data']['$lte'] = datetime.fromisoformat(data_fim)
            else:
                filtro['data'] = {'$lte': datetime.fromisoformat(data_fim)}

        status = request.args.get('status')
        if status:
            filtro['status'] = status

        profissional_id = request.args.get('profissional_id')
        if profissional_id:
            filtro['profissional_id'] = ObjectId(profissional_id)

        total = db.agendamentos.count_documents(filtro)
        agendamentos = list(db.agendamentos.find(filtro)
                           .sort('data', DESCENDING)
                           .skip(skip)
                           .limit(per_page))

        # Enriquecer com dados de cliente e profissional
        for agend in agendamentos:
            if agend.get('cliente_id'):
                cliente = db.clientes.find_one({'_id': agend['cliente_id']}, {'nome': 1, 'telefone': 1})
                agend['cliente_nome'] = cliente.get('nome') if cliente else 'N/A'
                agend['cliente_telefone'] = cliente.get('telefone') if cliente else 'N/A'

            if agend.get('profissional_id'):
                prof = db.profissionais.find_one({'_id': agend['profissional_id']}, {'nome': 1})
                agend['profissional_nome'] = prof.get('nome') if prof else 'N/A'

        return jsonify({
            'success': True,
            'agendamentos': convert_objectid(agendamentos),
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })

    except Exception as e:
        logger.error(f"Erro ao listar agendamentos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/agendamentos/calendario', methods=['GET'])
def agendamentos_calendario():
    """Retorna agendamentos formatados para calendário"""
    try:
        db = get_db()

        # Buscar agendamentos do mês
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')

        if not data_inicio or not data_fim:
            # Usar mês atual
            hoje = datetime.now()
            data_inicio = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Último dia do mês
            if hoje.month == 12:
                data_fim = hoje.replace(year=hoje.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                data_fim = hoje.replace(month=hoje.month + 1, day=1) - timedelta(days=1)
        else:
            data_inicio = datetime.fromisoformat(data_inicio)
            data_fim = datetime.fromisoformat(data_fim)

        agendamentos = list(db.agendamentos.find({
            'data': {'$gte': data_inicio, '$lte': data_fim}
        }).sort('data', ASCENDING))

        # Formatar para calendário
        eventos = []
        for agend in agendamentos:
            cliente = db.clientes.find_one({'_id': agend.get('cliente_id')}, {'nome': 1})
            prof = db.profissionais.find_one({'_id': agend.get('profissional_id')}, {'nome': 1})

            eventos.append({
                'id': str(agend['_id']),
                'title': f"{cliente.get('nome') if cliente else 'Cliente'} - {prof.get('nome') if prof else 'Profissional'}",
                'start': agend.get('data').isoformat() if agend.get('data') else '',
                'status': agend.get('status', 'Aguardando'),
                'color': get_cor_status_agendamento(agend.get('status', 'Aguardando'))
            })

        return jsonify({
            'success': True,
            'eventos': eventos
        })

    except Exception as e:
        logger.error(f"Erro ao buscar agendamentos para calendário: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

def get_cor_status_agendamento(status):
    """Retorna cor baseada no status do agendamento"""
    cores = {
        'Aguardando': '#3B82F6',  # Azul
        'Confirmado': '#10B981',  # Verde
        'Em Atendimento': '#F59E0B',  # Amarelo
        'Concluído': '#6B7280',  # Cinza
        'Cancelado': '#EF4444'  # Vermelho
    }
    return cores.get(status, '#6B7280')

# ==================== ROTAS OTIMIZADAS PARA RELATÓRIOS ====================

@api.route('/api/relatorios/mapa-calor', methods=['GET'])
def mapa_calor_otimizado():
    """Retorna mapa de calor otimizado para evitar carregamento infinito"""
    try:
        db = get_db()

        # Filtros de data
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')

        if not data_inicio or not data_fim:
            # Usar últimos 30 dias
            hoje = datetime.now()
            data_fim = hoje
            data_inicio = hoje - timedelta(days=30)
        else:
            data_inicio = datetime.fromisoformat(data_inicio)
            data_fim = datetime.fromisoformat(data_fim)

        tipo = request.args.get('tipo', 'faturamento')  # faturamento ou agendamentos

        # Pipeline de agregação baseado no tipo
        if tipo == 'faturamento':
            pipeline = [
                {
                    '$match': {
                        'status': 'Aprovado',
                        'data_criacao': {'$gte': data_inicio, '$lte': data_fim}
                    }
                },
                {
                    '$group': {
                        '_id': {
                            'dia_semana': {'$dayOfWeek': '$data_criacao'},
                            'hora': {'$hour': '$data_criacao'}
                        },
                        'total': {'$sum': '$total_final'},
                        'quantidade': {'$sum': 1}
                    }
                },
                {
                    '$sort': {'_id.dia_semana': 1, '_id.hora': 1}
                }
            ]

            resultados = list(db.orcamentos.aggregate(pipeline))

        else:  # agendamentos
            pipeline = [
                {
                    '$match': {
                        'data': {'$gte': data_inicio, '$lte': data_fim}
                    }
                },
                {
                    '$group': {
                        '_id': {
                            'dia_semana': {'$dayOfWeek': '$data'},
                            'hora': {'$hour': '$data'}
                        },
                        'quantidade': {'$sum': 1}
                    }
                },
                {
                    '$sort': {'_id.dia_semana': 1, '_id.hora': 1}
                }
            ]

            resultados = list(db.agendamentos.aggregate(pipeline))

        # Formatar dados para o mapa de calor
        mapa = {}
        dias_semana = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']

        for resultado in resultados:
            dia = resultado['_id']['dia_semana'] - 1  # MongoDB usa 1-7, ajustar para 0-6
            hora = resultado['_id']['hora']
            dia_nome = dias_semana[dia]

            if dia_nome not in mapa:
                mapa[dia_nome] = {}

            if tipo == 'faturamento':
                mapa[dia_nome][hora] = {
                    'total': round(resultado['total'], 2),
                    'quantidade': resultado['quantidade']
                }
            else:
                mapa[dia_nome][hora] = {
                    'quantidade': resultado['quantidade']
                }

        return jsonify({
            'success': True,
            'tipo': tipo,
            'periodo': {
                'inicio': data_inicio.isoformat(),
                'fim': data_fim.isoformat()
            },
            'mapa': mapa
        })

    except Exception as e:
        logger.error(f"Erro ao gerar mapa de calor: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/relatorios/top-clientes', methods=['GET'])
def relatorio_top_clientes():
    """Retorna os top clientes por faturamento"""
    try:
        db = get_db()

        limit = int(request.args.get('limit', 10))

        # Filtros de data
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')

        match_filter = {'status': 'Aprovado'}

        if data_inicio:
            match_filter['data_criacao'] = {'$gte': datetime.fromisoformat(data_inicio)}

        if data_fim:
            if 'data_criacao' in match_filter:
                match_filter['data_criacao']['$lte'] = datetime.fromisoformat(data_fim)
            else:
                match_filter['data_criacao'] = {'$lte': datetime.fromisoformat(data_fim)}

        pipeline = [
            {'$match': match_filter},
            {
                '$group': {
                    '_id': '$cliente_id',
                    'total_gasto': {'$sum': '$total_final'},
                    'ticket_medio': {'$avg': '$total_final'},
                    'total_orcamentos': {'$sum': 1}
                }
            },
            {'$sort': {'total_gasto': -1}},
            {'$limit': limit}
        ]

        resultados = list(db.orcamentos.aggregate(pipeline))

        # Enriquecer com dados do cliente
        clientes_top = []
        for resultado in resultados:
            cliente = db.clientes.find_one({'_id': resultado['_id']})
            if cliente:
                clientes_top.append({
                    'id': str(cliente['_id']),
                    'nome': cliente.get('nome', 'N/A'),
                    'email': cliente.get('email', 'N/A'),
                    'telefone': cliente.get('telefone', 'N/A'),
                    'total_gasto': round(resultado['total_gasto'], 2),
                    'ticket_medio': round(resultado['ticket_medio'], 2),
                    'total_orcamentos': resultado['total_orcamentos']
                })

        return jsonify({
            'success': True,
            'clientes': clientes_top
        })

    except Exception as e:
        logger.error(f"Erro ao gerar relatório de top clientes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/relatorios/top-produtos', methods=['GET'])
def relatorio_top_produtos():
    """Retorna os top produtos mais vendidos"""
    try:
        db = get_db()

        limit = int(request.args.get('limit', 10))

        # Filtros de data
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')

        match_filter = {'status': 'Aprovado'}

        if data_inicio:
            match_filter['data_criacao'] = {'$gte': datetime.fromisoformat(data_inicio)}

        if data_fim:
            if 'data_criacao' in match_filter:
                match_filter['data_criacao']['$lte'] = datetime.fromisoformat(data_fim)
            else:
                match_filter['data_criacao'] = {'$lte': datetime.fromisoformat(data_fim)}

        pipeline = [
            {'$match': match_filter},
            {'$unwind': '$produtos'},
            {
                '$group': {
                    '_id': '$produtos.nome',
                    'quantidade_total': {'$sum': '$produtos.quantidade'},
                    'faturamento_total': {'$sum': '$produtos.preco_total'}
                }
            },
            {'$sort': {'faturamento_total': -1}},
            {'$limit': limit}
        ]

        resultados = list(db.orcamentos.aggregate(pipeline))

        produtos_top = []
        for resultado in resultados:
            produtos_top.append({
                'nome': resultado['_id'],
                'quantidade_total': resultado['quantidade_total'],
                'faturamento_total': round(resultado['faturamento_total'], 2)
            })

        return jsonify({
            'success': True,
            'produtos': produtos_top
        })

    except Exception as e:
        logger.error(f"Erro ao gerar relatório de top produtos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/relatorios/resumo-geral', methods=['GET'])
def relatorio_resumo_geral():
    """Retorna resumo geral do sistema"""
    try:
        db = get_db()

        # Filtros de data
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')

        if not data_inicio:
            # Usar mês atual
            hoje = datetime.now()
            data_inicio = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            data_fim = hoje
        else:
            data_inicio = datetime.fromisoformat(data_inicio)
            data_fim = datetime.fromisoformat(data_fim) if data_fim else datetime.now()

        # Estatísticas de orçamentos
        pipeline_orcamentos = [
            {
                '$match': {
                    'data_criacao': {'$gte': data_inicio, '$lte': data_fim}
                }
            },
            {
                '$group': {
                    '_id': '$status',
                    'quantidade': {'$sum': 1},
                    'valor_total': {'$sum': '$total_final'}
                }
            }
        ]

        orcamentos_stats = list(db.orcamentos.aggregate(pipeline_orcamentos))

        # Estatísticas de clientes
        total_clientes = db.clientes.count_documents({})
        novos_clientes = db.clientes.count_documents({
            'data_cadastro': {'$gte': data_inicio, '$lte': data_fim}
        })

        # Estatísticas de agendamentos
        total_agendamentos = db.agendamentos.count_documents({
            'data': {'$gte': data_inicio, '$lte': data_fim}
        })

        # Produtos em estoque
        produtos_total = db.produtos.count_documents({'status': {'$ne': 'Inativo'}})
        produtos_criticos = db.produtos.count_documents({
            '$expr': {'$lte': ['$estoque', '$estoque_minimo']}
        })

        return jsonify({
            'success': True,
            'periodo': {
                'inicio': data_inicio.isoformat(),
                'fim': data_fim.isoformat()
            },
            'orcamentos': orcamentos_stats,
            'clientes': {
                'total': total_clientes,
                'novos': novos_clientes
            },
            'agendamentos': {
                'total': total_agendamentos
            },
            'estoque': {
                'total_produtos': produtos_total,
                'produtos_criticos': produtos_criticos
            }
        })

    except Exception as e:
        logger.error(f"Erro ao gerar resumo geral: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== ROTAS PARA AUDITORIA ====================

@api.route('/api/auditoria/logs', methods=['GET'])
def logs_auditoria():
    """Retorna logs de auditoria com paginação"""
    try:
        db = get_db()

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        skip = (page - 1) * per_page

        # Filtros
        filtro = {}

        tipo_acao = request.args.get('tipo_acao')
        if tipo_acao:
            filtro['tipo_acao'] = tipo_acao

        usuario_id = request.args.get('usuario_id')
        if usuario_id:
            filtro['usuario_id'] = ObjectId(usuario_id)

        data_inicio = request.args.get('data_inicio')
        if data_inicio:
            filtro['data'] = {'$gte': datetime.fromisoformat(data_inicio)}

        data_fim = request.args.get('data_fim')
        if data_fim:
            if 'data' in filtro:
                filtro['data']['$lte'] = datetime.fromisoformat(data_fim)
            else:
                filtro['data'] = {'$lte': datetime.fromisoformat(data_fim)}

        total = db.auditoria.count_documents(filtro)
        logs = list(db.auditoria.find(filtro)
                   .sort('data', DESCENDING)
                   .skip(skip)
                   .limit(per_page))

        # Enriquecer com dados do usuário
        for log in logs:
            if log.get('usuario_id'):
                usuario = db.usuarios.find_one({'_id': log['usuario_id']}, {'nome': 1, 'username': 1})
                log['usuario_nome'] = usuario.get('nome') if usuario else 'N/A'
                log['usuario_username'] = usuario.get('username') if usuario else 'N/A'

        return jsonify({
            'success': True,
            'logs': convert_objectid(logs),
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })

    except Exception as e:
        logger.error(f"Erro ao buscar logs de auditoria: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== HELPER PARA CRIAR LOG DE AUDITORIA ====================

def criar_log_auditoria(tipo_acao, descricao, dados_adicionais=None):
    """Cria um log de auditoria no banco de dados"""
    try:
        db = get_db()
        log = {
            'tipo_acao': tipo_acao,
            'descricao': descricao,
            'usuario_id': ObjectId(session.get('user_id')) if session.get('user_id') else None,
            'dados_adicionais': dados_adicionais or {},
            'data': datetime.utcnow(),
            'ip': request.remote_addr if request else None
        }
        db.auditoria.insert_one(log)
        logger.info(f"Log de auditoria criado: {tipo_acao} - {descricao}")
    except Exception as e:
        logger.error(f"Erro ao criar log de auditoria: {e}")

# ==================== SISTEMA DE ENVIO DE E-MAIL ====================

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def enviar_email(destinatario, assunto, corpo_html, anexos=None):
    """
    Envia e-mail usando configurações do ambiente
    """
    try:
        # Configurações do e-mail
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        email_remetente = os.getenv('EMAIL_REMETENTE', '')
        email_senha = os.getenv('EMAIL_SENHA', '')

        if not email_remetente or not email_senha:
            logger.warning("Configurações de e-mail não encontradas")
            return False

        # Criar mensagem
        msg = MIMEMultipart('alternative')
        msg['From'] = email_remetente
        msg['To'] = destinatario
        msg['Subject'] = assunto

        # Corpo do e-mail
        parte_html = MIMEText(corpo_html, 'html')
        msg.attach(parte_html)

        # Anexos
        if anexos:
            for arquivo_path in anexos:
                if os.path.exists(arquivo_path):
                    with open(arquivo_path, 'rb') as arquivo:
                        parte = MIMEBase('application', 'octet-stream')
                        parte.set_payload(arquivo.read())
                        encoders.encode_base64(parte)
                        parte.add_header(
                            'Content-Disposition',
                            f'attachment; filename={os.path.basename(arquivo_path)}'
                        )
                        msg.attach(parte)

        # Enviar e-mail
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_remetente, email_senha)
            server.send_message(msg)

        logger.info(f"E-mail enviado para {destinatario}")
        return True

    except Exception as e:
        logger.error(f"Erro ao enviar e-mail: {e}")
        return False

@api.route('/api/email/enviar-orcamento/<id>', methods=['POST'])
def enviar_email_orcamento(id):
    """Envia orçamento por e-mail"""
    try:
        db = get_db()
        orcamento = db.orcamentos.find_one({'_id': ObjectId(id)})

        if not orcamento:
            return jsonify({'success': False, 'message': 'Orçamento não encontrado'}), 404

        cliente = db.clientes.find_one({'_id': orcamento.get('cliente_id')})

        if not cliente or not cliente.get('email'):
            return jsonify({'success': False, 'message': 'Cliente sem e-mail cadastrado'}), 400

        # Criar HTML do e-mail
        corpo_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #7C3AED, #EC4899); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .table th, .table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                .table th {{ background: #7C3AED; color: white; }}
                .total {{ font-size: 1.5em; font-weight: bold; color: #7C3AED; text-align: right; margin-top: 20px; }}
                .footer {{ background: #333; color: white; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>BIOMA UBERABA</h1>
                    <h2>Orçamento #{orcamento.get('numero')}</h2>
                </div>
                <div class="content">
                    <p><strong>Olá {cliente.get('nome', '')}!</strong></p>
                    <p>Segue o orçamento solicitado:</p>

                    <h3>Serviços</h3>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Serviço</th>
                                <th>Quantidade</th>
                                <th>Valor</th>
                            </tr>
                        </thead>
                        <tbody>
        """

        for servico in orcamento.get('servicos', []):
            corpo_html += f"""
                <tr>
                    <td>{servico.get('nome')}</td>
                    <td>{servico.get('quantidade')}</td>
                    <td>R$ {servico.get('preco_total', 0):.2f}</td>
                </tr>
            """

        corpo_html += """
                        </tbody>
                    </table>
        """

        if orcamento.get('produtos'):
            corpo_html += """
                <h3>Produtos</h3>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Produto</th>
                            <th>Quantidade</th>
                            <th>Valor</th>
                        </tr>
                    </thead>
                    <tbody>
            """

            for produto in orcamento.get('produtos', []):
                corpo_html += f"""
                    <tr>
                        <td>{produto.get('nome')}</td>
                        <td>{produto.get('quantidade')}</td>
                        <td>R$ {produto.get('preco_total', 0):.2f}</td>
                    </tr>
                """

            corpo_html += """
                    </tbody>
                </table>
            """

        corpo_html += f"""
                    <div class="total">
                        TOTAL: R$ {orcamento.get('total_final', 0):.2f}
                    </div>

                    <p style="margin-top: 30px;">Ficamos à disposição para qualquer dúvida!</p>
                </div>
                <div class="footer">
                    <p>BIOMA Uberaba - Sistema de Gestão</p>
                    <p>Este é um e-mail automático, por favor não responda.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Enviar e-mail
        sucesso = enviar_email(
            cliente.get('email'),
            f'Orçamento #{orcamento.get("numero")} - BIOMA Uberaba',
            corpo_html
        )

        if sucesso:
            # Registrar envio no banco
            db.emails_enviados.insert_one({
                'tipo': 'orcamento',
                'orcamento_id': ObjectId(id),
                'cliente_id': cliente['_id'],
                'email_destino': cliente.get('email'),
                'data_envio': datetime.utcnow(),
                'enviado_por': ObjectId(session.get('user_id'))
            })

            return jsonify({
                'success': True,
                'message': 'E-mail enviado com sucesso!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Erro ao enviar e-mail. Verifique as configurações.'
            }), 500

    except Exception as e:
        logger.error(f"Erro ao enviar e-mail do orçamento: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/email/teste', methods=['POST'])
def testar_email():
    """Testa configurações de e-mail"""
    try:
        data = request.json
        email_destino = data.get('email')

        if not email_destino:
            return jsonify({'success': False, 'message': 'E-mail não fornecido'}), 400

        corpo_html = """
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h2 style="color: #7C3AED;">Teste de Configuração de E-mail</h2>
            <p>Este é um e-mail de teste do sistema BIOMA Uberaba.</p>
            <p>Se você recebeu este e-mail, as configurações estão corretas! ✅</p>
        </body>
        </html>
        """

        sucesso = enviar_email(
            email_destino,
            'Teste de E-mail - BIOMA Uberaba',
            corpo_html
        )

        if sucesso:
            return jsonify({
                'success': True,
                'message': 'E-mail de teste enviado com sucesso!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Erro ao enviar e-mail de teste'
            }), 500

    except Exception as e:
        logger.error(f"Erro no teste de e-mail: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== UPLOAD DE FOTOS DE SERVIÇOS ====================

@api.route('/api/servicos/<id>/foto', methods=['POST'])
def upload_foto_servico(id):
    """Upload de foto do serviço"""
    try:
        if 'foto' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhuma foto enviada'}), 400

        file = request.files['foto']

        if file.filename == '':
            return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400

        if file and allowed_file(file.filename):
            # Redimensionar imagem
            img_redimensionada = redimensionar_imagem(file, max_width=800, max_height=600)

            filename = f"servico_{id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

            with open(filepath, 'wb') as f:
                f.write(img_redimensionada.read())

            # Atualizar no banco
            db = get_db()

            # Adicionar foto ao array de fotos
            db.servicos.update_one(
                {'_id': ObjectId(id)},
                {
                    '$push': {
                        'fotos': {
                            'url': f'/uploads/{filename}',
                            'data_upload': datetime.utcnow()
                        }
                    },
                    '$set': {
                        'foto_principal': f'/uploads/{filename}'  # Define como principal se for a primeira
                    }
                }
            )

            logger.info(f"Foto do serviço {id} salva: {filename}")

            return jsonify({
                'success': True,
                'foto_url': f'/uploads/{filename}',
                'message': 'Foto adicionada com sucesso'
            })

        return jsonify({'success': False, 'message': 'Tipo de arquivo não permitido'}), 400

    except Exception as e:
        logger.error(f"Erro ao fazer upload da foto do serviço: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/servicos/<id>/fotos', methods=['GET'])
def listar_fotos_servico(id):
    """Lista fotos do serviço"""
    try:
        db = get_db()
        servico = db.servicos.find_one({'_id': ObjectId(id)})

        if not servico:
            return jsonify({'success': False, 'message': 'Serviço não encontrado'}), 404

        fotos = servico.get('fotos', [])

        return jsonify({
            'success': True,
            'fotos': fotos,
            'foto_principal': servico.get('foto_principal')
        })

    except Exception as e:
        logger.error(f"Erro ao listar fotos do serviço: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/servicos/<id>/foto/<foto_index>', methods=['DELETE'])
def deletar_foto_servico(id, foto_index):
    """Deleta foto do serviço"""
    try:
        db = get_db()
        servico = db.servicos.find_one({'_id': ObjectId(id)})

        if not servico:
            return jsonify({'success': False, 'message': 'Serviço não encontrado'}), 404

        fotos = servico.get('fotos', [])
        index = int(foto_index)

        if index < 0 or index >= len(fotos):
            return jsonify({'success': False, 'message': 'Índice de foto inválido'}), 400

        # Remover arquivo físico
        foto_url = fotos[index].get('url', '')
        if foto_url:
            filename = foto_url.replace('/uploads/', '')
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(filepath):
                os.remove(filepath)

        # Remover do array
        fotos.pop(index)

        # Atualizar no banco
        update_data = {'fotos': fotos}

        # Se era a foto principal, definir nova
        if servico.get('foto_principal') == foto_url:
            update_data['foto_principal'] = fotos[0]['url'] if fotos else None

        db.servicos.update_one(
            {'_id': ObjectId(id)},
            {'$set': update_data}
        )

        logger.info(f"Foto {foto_index} do serviço {id} deletada")

        return jsonify({
            'success': True,
            'message': 'Foto deletada com sucesso'
        })

    except Exception as e:
        logger.error(f"Erro ao deletar foto do serviço: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== SISTEMA DE AVALIAÇÕES ====================

@api.route('/api/avaliacoes', methods=['POST'])
def criar_avaliacao():
    """Cria uma nova avaliação"""
    try:
        db = get_db()
        data = request.json

        avaliacao = {
            'cliente_id': ObjectId(data.get('cliente_id')),
            'profissional_id': ObjectId(data.get('profissional_id')),
            'servico_id': ObjectId(data.get('servico_id')) if data.get('servico_id') else None,
            'orcamento_id': ObjectId(data.get('orcamento_id')) if data.get('orcamento_id') else None,
            'nota': int(data.get('nota', 5)),  # 1 a 5
            'comentario': data.get('comentario', ''),
            'aspectos': {
                'atendimento': int(data.get('atendimento', 5)),
                'qualidade': int(data.get('qualidade', 5)),
                'pontualidade': int(data.get('pontualidade', 5)),
                'limpeza': int(data.get('limpeza', 5)),
                'preco': int(data.get('preco', 5))
            },
            'data_criacao': datetime.utcnow(),
            'aprovado': False,  # Requer aprovação do admin
            'respondido': False,
            'resposta': None
        }

        result = db.avaliacoes.insert_one(avaliacao)

        # Atualizar média do profissional
        atualizar_media_profissional(data.get('profissional_id'))

        logger.info(f"Avaliação criada - ID: {result.inserted_id}")

        return jsonify({
            'success': True,
            'message': 'Avaliação enviada! Será publicada após aprovação.',
            'id': str(result.inserted_id)
        })

    except Exception as e:
        logger.error(f"Erro ao criar avaliação: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/avaliacoes/profissional/<profissional_id>', methods=['GET'])
def listar_avaliacoes_profissional(profissional_id):
    """Lista avaliações de um profissional"""
    try:
        db = get_db()

        # Apenas avaliações aprovadas
        filtro = {
            'profissional_id': ObjectId(profissional_id),
            'aprovado': True
        }

        avaliacoes = list(db.avaliacoes.find(filtro).sort('data_criacao', DESCENDING))

        # Enriquecer com dados do cliente
        for av in avaliacoes:
            cliente = db.clientes.find_one({'_id': av.get('cliente_id')}, {'nome': 1})
            av['cliente_nome'] = cliente.get('nome') if cliente else 'Anônimo'

        # Calcular estatísticas
        if avaliacoes:
            total_avaliacoes = len(avaliacoes)
            media_geral = sum([av['nota'] for av in avaliacoes]) / total_avaliacoes

            # Médias por aspecto
            aspectos_media = {
                'atendimento': sum([av['aspectos']['atendimento'] for av in avaliacoes]) / total_avaliacoes,
                'qualidade': sum([av['aspectos']['qualidade'] for av in avaliacoes]) / total_avaliacoes,
                'pontualidade': sum([av['aspectos']['pontualidade'] for av in avaliacoes]) / total_avaliacoes,
                'limpeza': sum([av['aspectos']['limpeza'] for av in avaliacoes]) / total_avaliacoes,
                'preco': sum([av['aspectos']['preco'] for av in avaliacoes]) / total_avaliacoes
            }

            # Distribuição de notas
            distribuicao = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for av in avaliacoes:
                distribuicao[av['nota']] += 1

        else:
            media_geral = 0
            aspectos_media = {}
            distribuicao = {}

        return jsonify({
            'success': True,
            'avaliacoes': convert_objectid(avaliacoes),
            'estatisticas': {
                'total': total_avaliacoes if avaliacoes else 0,
                'media_geral': round(media_geral, 2) if avaliacoes else 0,
                'aspectos_media': aspectos_media,
                'distribuicao': distribuicao
            }
        })

    except Exception as e:
        logger.error(f"Erro ao listar avaliações: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/avaliacoes/<id>/aprovar', methods=['POST'])
def aprovar_avaliacao(id):
    """Aprova uma avaliação (apenas Admin)"""
    try:
        db = get_db()

        # Verificar permissão (simplificado - adicionar validação de perfil)
        result = db.avaliacoes.update_one(
            {'_id': ObjectId(id)},
            {
                '$set': {
                    'aprovado': True,
                    'aprovado_por': ObjectId(session.get('user_id')),
                    'data_aprovacao': datetime.utcnow()
                }
            }
        )

        if result.modified_count > 0:
            # Atualizar média do profissional
            avaliacao = db.avaliacoes.find_one({'_id': ObjectId(id)})
            atualizar_media_profissional(str(avaliacao.get('profissional_id')))

            return jsonify({
                'success': True,
                'message': 'Avaliação aprovada com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Avaliação não encontrada'
            }), 404

    except Exception as e:
        logger.error(f"Erro ao aprovar avaliação: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/avaliacoes/<id>/responder', methods=['POST'])
def responder_avaliacao(id):
    """Responde uma avaliação"""
    try:
        db = get_db()
        data = request.json

        result = db.avaliacoes.update_one(
            {'_id': ObjectId(id)},
            {
                '$set': {
                    'respondido': True,
                    'resposta': data.get('resposta'),
                    'respondido_por': ObjectId(session.get('user_id')),
                    'data_resposta': datetime.utcnow()
                }
            }
        )

        if result.modified_count > 0:
            return jsonify({
                'success': True,
                'message': 'Resposta enviada com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Avaliação não encontrada'
            }), 404

    except Exception as e:
        logger.error(f"Erro ao responder avaliação: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/avaliacoes/pendentes', methods=['GET'])
def listar_avaliacoes_pendentes():
    """Lista avaliações pendentes de aprovação"""
    try:
        db = get_db()

        avaliacoes = list(db.avaliacoes.find({'aprovado': False}).sort('data_criacao', DESCENDING))

        # Enriquecer com dados
        for av in avaliacoes:
            cliente = db.clientes.find_one({'_id': av.get('cliente_id')}, {'nome': 1})
            profissional = db.profissionais.find_one({'_id': av.get('profissional_id')}, {'nome': 1})

            av['cliente_nome'] = cliente.get('nome') if cliente else 'N/A'
            av['profissional_nome'] = profissional.get('nome') if profissional else 'N/A'

        return jsonify({
            'success': True,
            'avaliacoes': convert_objectid(avaliacoes)
        })

    except Exception as e:
        logger.error(f"Erro ao listar avaliações pendentes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

def atualizar_media_profissional(profissional_id):
    """Atualiza a média de avaliações do profissional"""
    try:
        db = get_db()

        # Calcular média das avaliações aprovadas
        pipeline = [
            {
                '$match': {
                    'profissional_id': ObjectId(profissional_id),
                    'aprovado': True
                }
            },
            {
                '$group': {
                    '_id': None,
                    'media_geral': {'$avg': '$nota'},
                    'total_avaliacoes': {'$sum': 1},
                    'media_atendimento': {'$avg': '$aspectos.atendimento'},
                    'media_qualidade': {'$avg': '$aspectos.qualidade'},
                    'media_pontualidade': {'$avg': '$aspectos.pontualidade'},
                    'media_limpeza': {'$avg': '$aspectos.limpeza'},
                    'media_preco': {'$avg': '$aspectos.preco'}
                }
            }
        ]

        resultado = list(db.avaliacoes.aggregate(pipeline))

        if resultado:
            stats = resultado[0]
            db.profissionais.update_one(
                {'_id': ObjectId(profissional_id)},
                {
                    '$set': {
                        'avaliacoes_stats': {
                            'media_geral': round(stats.get('media_geral', 0), 2),
                            'total': stats.get('total_avaliacoes', 0),
                            'aspectos': {
                                'atendimento': round(stats.get('media_atendimento', 0), 2),
                                'qualidade': round(stats.get('media_qualidade', 0), 2),
                                'pontualidade': round(stats.get('media_pontualidade', 0), 2),
                                'limpeza': round(stats.get('media_limpeza', 0), 2),
                                'preco': round(stats.get('media_preco', 0), 2)
                            }
                        }
                    }
                }
            )

            logger.info(f"Média do profissional {profissional_id} atualizada")

    except Exception as e:
        logger.error(f"Erro ao atualizar média do profissional: {e}")

# ==================== DADOS PARA GRÁFICOS ====================

@api.route('/api/graficos/faturamento-mensal', methods=['GET'])
def grafico_faturamento_mensal():
    """Retorna dados de faturamento dos últimos 12 meses para gráfico"""
    try:
        db = get_db()

        # Últimos 12 meses
        hoje = datetime.now()
        meses = []
        labels = []

        for i in range(11, -1, -1):
            mes_data = hoje - timedelta(days=30 * i)
            inicio_mes = mes_data.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            if mes_data.month == 12:
                fim_mes = mes_data.replace(year=mes_data.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                fim_mes = mes_data.replace(month=mes_data.month + 1, day=1) - timedelta(days=1)

            meses.append({'inicio': inicio_mes, 'fim': fim_mes})
            labels.append(inicio_mes.strftime('%b/%Y'))

        # Buscar faturamento por mês
        dados_faturamento = []
        dados_despesas = []
        dados_lucro = []

        for mes in meses:
            # Receitas
            pipeline_receitas = [
                {
                    '$match': {
                        'status': 'Aprovado',
                        'data_criacao': {'$gte': mes['inicio'], '$lte': mes['fim']}
                    }
                },
                {
                    '$group': {
                        '_id': None,
                        'total': {'$sum': '$total_final'}
                    }
                }
            ]

            resultado_receitas = list(db.orcamentos.aggregate(pipeline_receitas))
            receitas = resultado_receitas[0]['total'] if resultado_receitas else 0

            # Despesas
            pipeline_despesas = [
                {
                    '$match': {
                        'data': {'$gte': mes['inicio'], '$lte': mes['fim']}
                    }
                },
                {
                    '$group': {
                        '_id': None,
                        'total': {'$sum': '$valor'}
                    }
                }
            ]

            resultado_despesas = list(db.despesas.aggregate(pipeline_despesas))
            despesas = resultado_despesas[0]['total'] if resultado_despesas else 0

            dados_faturamento.append(round(receitas, 2))
            dados_despesas.append(round(despesas, 2))
            dados_lucro.append(round(receitas - despesas, 2))

        return jsonify({
            'success': True,
            'labels': labels,
            'datasets': [
                {
                    'label': 'Receitas',
                    'data': dados_faturamento,
                    'backgroundColor': 'rgba(16, 185, 129, 0.2)',
                    'borderColor': 'rgba(16, 185, 129, 1)',
                    'borderWidth': 2
                },
                {
                    'label': 'Despesas',
                    'data': dados_despesas,
                    'backgroundColor': 'rgba(239, 68, 68, 0.2)',
                    'borderColor': 'rgba(239, 68, 68, 1)',
                    'borderWidth': 2
                },
                {
                    'label': 'Lucro',
                    'data': dados_lucro,
                    'backgroundColor': 'rgba(59, 130, 246, 0.2)',
                    'borderColor': 'rgba(59, 130, 246, 1)',
                    'borderWidth': 2
                }
            ]
        })

    except Exception as e:
        logger.error(f"Erro ao gerar dados do gráfico de faturamento: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/graficos/servicos-mais-vendidos', methods=['GET'])
def grafico_servicos_mais_vendidos():
    """Retorna top 10 serviços mais vendidos para gráfico"""
    try:
        db = get_db()

        pipeline = [
            {'$match': {'status': 'Aprovado'}},
            {'$unwind': '$servicos'},
            {
                '$group': {
                    '_id': '$servicos.nome',
                    'quantidade': {'$sum': '$servicos.quantidade'},
                    'faturamento': {'$sum': '$servicos.preco_total'}
                }
            },
            {'$sort': {'quantidade': -1}},
            {'$limit': 10}
        ]

        resultados = list(db.orcamentos.aggregate(pipeline))

        labels = [r['_id'] for r in resultados]
        dados_quantidade = [r['quantidade'] for r in resultados]
        dados_faturamento = [round(r['faturamento'], 2) for r in resultados]

        return jsonify({
            'success': True,
            'labels': labels,
            'datasets': [
                {
                    'label': 'Quantidade Vendida',
                    'data': dados_quantidade,
                    'backgroundColor': 'rgba(124, 58, 237, 0.7)'
                },
                {
                    'label': 'Faturamento (R$)',
                    'data': dados_faturamento,
                    'backgroundColor': 'rgba(236, 72, 153, 0.7)'
                }
            ]
        })

    except Exception as e:
        logger.error(f"Erro ao gerar dados do gráfico de serviços: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/api/graficos/produtos-mais-vendidos', methods=['GET'])
def grafico_produtos_mais_vendidos():
    """Retorna top 10 produtos mais vendidos para gráfico"""
    try:
        db = get_db()

        pipeline = [
            {'$match': {'status': 'Aprovado'}},
            {'$unwind': '$produtos'},
            {
                '$group': {
                    '_id': '$produtos.nome',
                    'quantidade': {'$sum': '$produtos.quantidade'},
                    'faturamento': {'$sum': '$produtos.preco_total'}
                }
            },
            {'$sort': {'quantidade': -1}},
            {'$limit': 10}
        ]

        resultados = list(db.orcamentos.aggregate(pipeline))

        labels = [r['_id'] for r in resultados]
        dados_quantidade = [r['quantidade'] for r in resultados]
        dados_faturamento = [round(r['faturamento'], 2) for r in resultados]

        return jsonify({
            'success': True,
            'labels': labels,
            'datasets': [
                {
                    'label': 'Quantidade Vendida',
                    'data': dados_quantidade,
                    'backgroundColor': 'rgba(245, 158, 11, 0.7)'
                },
                {
                    'label': 'Faturamento (R$)',
                    'data': dados_faturamento,
                    'backgroundColor': 'rgba(16, 185, 129, 0.7)'
                }
            ]
        })

    except Exception as e:
        logger.error(f"Erro ao gerar dados do gráfico de produtos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500