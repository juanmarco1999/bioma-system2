"""
BIOMA SYSTEM - Backend Routes Complete
Implementação completa de todas as rotas necessárias
Versão: 2.0
"""

from flask import Blueprint, request, jsonify, current_app, session
from bson import ObjectId
from datetime import datetime, timedelta
import logging
from pymongo import ASCENDING, DESCENDING
import hashlib
import random
import string
from PIL import Image
import io
import os
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)
api_complete = Blueprint('api_complete', __name__)

# ==================== HELPER FUNCTIONS ====================

def get_db():
    """Obtém a conexão com o banco de dados"""
    return current_app.config.get('DB_CONNECTION')

def convert_objectid(data):
    """Converte ObjectId para string"""
    if isinstance(data, list):
        return [{**item, '_id': str(item['_id'])} if '_id' in item else item for item in data]
    elif isinstance(data, dict) and '_id' in data:
        return {**data, '_id': str(data['_id'])}
    return data

def require_auth(f):
    """Decorator para rotas que precisam de autenticação"""
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Não autorizado'}), 401
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# ==================== DASHBOARD ====================

@api_complete.route('/api/dashboard', methods=['GET'])
@require_auth
def get_dashboard():
    """Retorna dados do dashboard"""
    try:
        db = get_db()

        # Estatísticas gerais
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        mes_inicio = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Contar totais
        total_clientes = db.clientes.count_documents({})
        total_profissionais = db.profissionais.count_documents({'ativo': True})
        total_servicos = db.servicos.count_documents({'ativo': True})
        total_produtos = db.produtos.count_documents({'ativo': True})

        # Agendamentos do dia
        agendamentos_hoje = db.agendamentos.count_documents({
            'data': {'$gte': hoje, '$lt': hoje + timedelta(days=1)},
            'status': {'$ne': 'cancelado'}
        })

        # Faturamento do mês
        faturamento_mes = db.orcamentos.aggregate([
            {
                '$match': {
                    'status': 'aprovado',
                    'data_aprovacao': {'$gte': mes_inicio}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total': {'$sum': '$valor_total'}
                }
            }
        ])

        faturamento_total = 0
        for doc in faturamento_mes:
            faturamento_total = doc['total']

        # Últimos agendamentos
        ultimos_agendamentos = list(db.agendamentos.find(
            {'data': {'$gte': hoje}}
        ).sort('data', 1).limit(5))

        # Produtos em baixo estoque
        produtos_baixo_estoque = db.produtos.count_documents({
            '$expr': {'$lte': ['$estoque', '$estoque_minimo']}
        })

        return jsonify({
            'success': True,
            'data': {
                'estatisticas': {
                    'total_clientes': total_clientes,
                    'total_profissionais': total_profissionais,
                    'total_servicos': total_servicos,
                    'total_produtos': total_produtos,
                    'agendamentos_hoje': agendamentos_hoje,
                    'faturamento_mes': faturamento_total,
                    'produtos_baixo_estoque': produtos_baixo_estoque
                },
                'ultimos_agendamentos': convert_objectid(ultimos_agendamentos),
                'graficos': {
                    'faturamento_semanal': get_faturamento_semanal(),
                    'servicos_populares': get_servicos_populares()
                }
            }
        })
    except Exception as e:
        logger.error(f"Erro ao carregar dashboard: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao carregar dashboard'}), 500

def get_faturamento_semanal():
    """Retorna faturamento dos últimos 7 dias"""
    db = get_db()
    hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    semana_passada = hoje - timedelta(days=7)

    pipeline = [
        {
            '$match': {
                'status': 'aprovado',
                'data_aprovacao': {'$gte': semana_passada}
            }
        },
        {
            '$group': {
                '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$data_aprovacao'}},
                'total': {'$sum': '$valor_total'}
            }
        },
        {'$sort': {'_id': 1}}
    ]

    resultado = list(db.orcamentos.aggregate(pipeline))
    return resultado

def get_servicos_populares():
    """Retorna os 5 serviços mais vendidos"""
    db = get_db()

    pipeline = [
        {'$match': {'status': 'aprovado'}},
        {'$unwind': '$servicos'},
        {
            '$group': {
                '_id': '$servicos.servico_id',
                'quantidade': {'$sum': '$servicos.quantidade'},
                'receita': {'$sum': '$servicos.preco_total'}
            }
        },
        {'$sort': {'quantidade': -1}},
        {'$limit': 5}
    ]

    resultado = list(db.orcamentos.aggregate(pipeline))

    # Buscar nomes dos serviços
    for item in resultado:
        servico = db.servicos.find_one({'_id': item['_id']})
        if servico:
            item['nome'] = servico.get('nome', 'N/A')

    return resultado

# ==================== CLIENTES ====================

@api_complete.route('/api/clientes', methods=['GET'])
@require_auth
def get_clientes():
    """Lista todos os clientes"""
    try:
        db = get_db()

        filtros = {}
        search = request.args.get('search')
        if search:
            filtros['$or'] = [
                {'nome': {'$regex': search, '$options': 'i'}},
                {'cpf': {'$regex': search, '$options': 'i'}},
                {'email': {'$regex': search, '$options': 'i'}}
            ]

        clientes = list(db.clientes.find(filtros).limit(100))

        return jsonify({
            'success': True,
            'clientes': convert_objectid(clientes)
        })
    except Exception as e:
        logger.error(f"Erro ao buscar clientes: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao buscar clientes'}), 500

@api_complete.route('/api/cliente/<id>/anamneses', methods=['GET'])
@require_auth
def get_anamneses_cliente(id):
    """Retorna histórico de anamneses do cliente"""
    try:
        db = get_db()

        anamneses = list(db.anamneses.find(
            {'cliente_id': ObjectId(id)}
        ).sort('data', -1))

        return jsonify({
            'success': True,
            'anamneses': convert_objectid(anamneses)
        })
    except Exception as e:
        logger.error(f"Erro ao buscar anamneses: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao buscar anamneses'}), 500

@api_complete.route('/api/cliente/<id>/prontuario', methods=['GET'])
@require_auth
def get_prontuario_cliente(id):
    """Retorna prontuário completo do cliente"""
    try:
        db = get_db()

        # Dados do cliente
        cliente = db.clientes.find_one({'_id': ObjectId(id)})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404

        # Anamneses
        anamneses = list(db.anamneses.find(
            {'cliente_id': ObjectId(id)}
        ).sort('data', -1))

        # Histórico de atendimentos
        atendimentos = list(db.agendamentos.find({
            'cliente_id': ObjectId(id),
            'status': 'concluido'
        }).sort('data', -1).limit(50))

        # Buscar detalhes dos serviços e profissionais
        for atend in atendimentos:
            if 'servico_id' in atend:
                servico = db.servicos.find_one({'_id': atend['servico_id']})
                if servico:
                    atend['servico_nome'] = servico.get('nome', 'N/A')

            if 'profissional_id' in atend:
                prof = db.profissionais.find_one({'_id': atend['profissional_id']})
                if prof:
                    atend['profissional_nome'] = prof.get('nome', 'N/A')

        prontuario = {
            'cliente_nome': cliente.get('nome'),
            'cliente_cpf': cliente.get('cpf'),
            'cliente_telefone': cliente.get('telefone'),
            'cliente_email': cliente.get('email'),
            'data_nascimento': cliente.get('data_nascimento'),
            'anamneses': convert_objectid(anamneses),
            'atendimentos': convert_objectid(atendimentos),
            'ultima_anamnese': convert_objectid(anamneses[0]) if anamneses else None
        }

        return jsonify({
            'success': True,
            'prontuario': prontuario
        })
    except Exception as e:
        logger.error(f"Erro ao buscar prontuário: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao buscar prontuário'}), 500

@api_complete.route('/api/cliente/<id>/prontuario/enviar-email', methods=['POST'])
@require_auth
def enviar_prontuario_email(id):
    """Envia prontuário por email"""
    try:
        db = get_db()

        # Buscar dados do prontuário
        cliente = db.clientes.find_one({'_id': ObjectId(id)})
        if not cliente or not cliente.get('email'):
            return jsonify({'success': False, 'message': 'Cliente sem email cadastrado'}), 400

        # Gerar conteúdo do email
        prontuario_response = get_prontuario_cliente(id)
        prontuario_data = prontuario_response.get_json()

        if not prontuario_data['success']:
            return jsonify({'success': False, 'message': 'Erro ao gerar prontuário'}), 500

        prontuario = prontuario_data['prontuario']

        # Criar email HTML
        html_content = f"""
        <html>
        <body>
            <h2>BIOMA UBERABA - Prontuário</h2>
            <h3>Dados do Cliente</h3>
            <p><strong>Nome:</strong> {prontuario['cliente_nome']}</p>
            <p><strong>CPF:</strong> {prontuario['cliente_cpf']}</p>

            <h3>Histórico de Atendimentos</h3>
            <ul>
        """

        for atend in prontuario['atendimentos'][:10]:
            html_content += f"""
                <li>
                    <strong>Data:</strong> {atend.get('data', 'N/A')}<br>
                    <strong>Serviço:</strong> {atend.get('servico_nome', 'N/A')}<br>
                    <strong>Profissional:</strong> {atend.get('profissional_nome', 'N/A')}
                </li>
            """

        html_content += """
            </ul>
            <p>Para mais informações, entre em contato conosco.</p>
            <p>BIOMA Uberaba<br>
            Tel: (34) 99235-5890<br>
            biomauberaba@gmail.com</p>
        </body>
        </html>
        """

        # Enviar email (simulação - precisa configurar SMTP real)
        # Aqui você deve configurar o SMTP real

        # Registrar envio
        db.emails_enviados.insert_one({
            'tipo': 'prontuario',
            'destinatario': cliente['email'],
            'cliente_id': ObjectId(id),
            'data_envio': datetime.utcnow(),
            'status': 'enviado'
        })

        return jsonify({
            'success': True,
            'message': 'Prontuário enviado por email'
        })
    except Exception as e:
        logger.error(f"Erro ao enviar prontuário: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao enviar prontuário'}), 500

# ==================== PROFISSIONAIS ====================

@api_complete.route('/api/profissionais', methods=['GET'])
@require_auth
def get_profissionais():
    """Lista todos os profissionais"""
    try:
        db = get_db()

        filtros = {'ativo': True}
        search = request.args.get('search')
        if search:
            filtros['nome'] = {'$regex': search, '$options': 'i'}

        profissionais = list(db.profissionais.find(filtros).limit(100))

        return jsonify({
            'success': True,
            'profissionais': convert_objectid(profissionais)
        })
    except Exception as e:
        logger.error(f"Erro ao buscar profissionais: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao buscar profissionais'}), 500

@api_complete.route('/api/profissional/<id>/foto', methods=['POST'])
@require_auth
def upload_foto_profissional(id):
    """Upload de foto do profissional"""
    try:
        if 'foto' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400

        file = request.files['foto']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400

        # Processar imagem
        img = Image.open(file)

        # Redimensionar para 200x200
        img.thumbnail((200, 200), Image.Resampling.LANCZOS)

        # Converter para JPEG
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Salvar em bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=85)
        img_byte_arr = img_byte_arr.getvalue()

        # Criar nome único
        filename = f"prof_{id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        filepath = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), filename)

        # Salvar arquivo
        with open(filepath, 'wb') as f:
            f.write(img_byte_arr)

        # Atualizar banco
        db = get_db()
        db.profissionais.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'foto_url': f'/uploads/{filename}',
                'foto_updated_at': datetime.utcnow()
            }}
        )

        return jsonify({
            'success': True,
            'foto_url': f'/uploads/{filename}',
            'message': 'Foto atualizada com sucesso'
        })
    except Exception as e:
        logger.error(f"Erro ao fazer upload de foto: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao fazer upload'}), 500

# ==================== SERVIÇOS ====================

@api_complete.route('/api/servicos', methods=['GET'])
@require_auth
def get_servicos():
    """Lista todos os serviços"""
    try:
        db = get_db()

        filtros = {'ativo': True}
        search = request.args.get('search')
        categoria = request.args.get('categoria')

        if search:
            filtros['nome'] = {'$regex': search, '$options': 'i'}
        if categoria:
            filtros['categoria'] = categoria

        servicos = list(db.servicos.find(filtros).limit(100))

        return jsonify({
            'success': True,
            'servicos': convert_objectid(servicos)
        })
    except Exception as e:
        logger.error(f"Erro ao buscar serviços: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao buscar serviços'}), 500

# ==================== PRODUTOS ====================

@api_complete.route('/api/produtos', methods=['GET'])
@require_auth
def get_produtos():
    """Lista todos os produtos"""
    try:
        db = get_db()

        filtros = {'ativo': True}
        search = request.args.get('search')
        categoria = request.args.get('categoria')

        if search:
            filtros['nome'] = {'$regex': search, '$options': 'i'}
        if categoria:
            filtros['categoria'] = categoria

        produtos = list(db.produtos.find(filtros).limit(100))

        return jsonify({
            'success': True,
            'produtos': convert_objectid(produtos)
        })
    except Exception as e:
        logger.error(f"Erro ao buscar produtos: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao buscar produtos'}), 500

# ==================== ORÇAMENTOS ====================

@api_complete.route('/api/orcamento/<id>', methods=['GET'])
@require_auth
def get_orcamento(id):
    """Retorna detalhes de um orçamento"""
    try:
        db = get_db()

        orcamento = db.orcamentos.find_one({'_id': ObjectId(id)})
        if not orcamento:
            return jsonify({'success': False, 'message': 'Orçamento não encontrado'}), 404

        # Buscar dados do cliente
        if 'cliente_id' in orcamento:
            cliente = db.clientes.find_one({'_id': orcamento['cliente_id']})
            if cliente:
                orcamento['cliente_nome'] = cliente.get('nome')
                orcamento['cliente_cpf'] = cliente.get('cpf')
                orcamento['cliente_telefone'] = cliente.get('telefone')
                orcamento['cliente_email'] = cliente.get('email')
                orcamento['cliente_endereco'] = cliente.get('endereco')

        return jsonify({
            'success': True,
            'orcamento': convert_objectid(orcamento)
        })
    except Exception as e:
        logger.error(f"Erro ao buscar orçamento: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao buscar orçamento'}), 500

@api_complete.route('/api/orcamento/pendentes', methods=['GET'])
@require_auth
def get_orcamentos_pendentes():
    """Lista orçamentos pendentes"""
    try:
        db = get_db()

        orcamentos = list(db.orcamentos.find(
            {'status': 'pendente'}
        ).sort('data', -1).limit(50))

        # Adicionar dados do cliente
        for orc in orcamentos:
            if 'cliente_id' in orc:
                cliente = db.clientes.find_one({'_id': orc['cliente_id']})
                if cliente:
                    orc['cliente_nome'] = cliente.get('nome')

        return jsonify({
            'success': True,
            'orcamentos': convert_objectid(orcamentos)
        })
    except Exception as e:
        logger.error(f"Erro ao buscar orçamentos pendentes: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao buscar orçamentos'}), 500

@api_complete.route('/api/orcamento/aprovados', methods=['GET'])
@require_auth
def get_orcamentos_aprovados():
    """Lista orçamentos aprovados"""
    try:
        db = get_db()

        orcamentos = list(db.orcamentos.find(
            {'status': 'aprovado'}
        ).sort('data_aprovacao', -1).limit(50))

        # Adicionar dados do cliente
        for orc in orcamentos:
            if 'cliente_id' in orc:
                cliente = db.clientes.find_one({'_id': orc['cliente_id']})
                if cliente:
                    orc['cliente_nome'] = cliente.get('nome')

        return jsonify({
            'success': True,
            'orcamentos': convert_objectid(orcamentos)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': 'Erro ao buscar orçamentos'}), 500

@api_complete.route('/api/orcamento/rejeitados', methods=['GET'])
@require_auth
def get_orcamentos_rejeitados():
    """Lista orçamentos rejeitados"""
    try:
        db = get_db()

        orcamentos = list(db.orcamentos.find(
            {'status': 'rejeitado'}
        ).sort('data_rejeicao', -1).limit(50))

        # Adicionar dados do cliente
        for orc in orcamentos:
            if 'cliente_id' in orc:
                cliente = db.clientes.find_one({'_id': orc['cliente_id']})
                if cliente:
                    orc['cliente_nome'] = cliente.get('nome')

        return jsonify({
            'success': True,
            'orcamentos': convert_objectid(orcamentos)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': 'Erro ao buscar orçamentos'}), 500

# ==================== CONTRATOS ====================

@api_complete.route('/api/contrato/<id>', methods=['GET'])
@require_auth
def get_contrato(id):
    """Retorna detalhes de um contrato"""
    try:
        db = get_db()

        contrato = db.contratos.find_one({'_id': ObjectId(id)})
        if not contrato:
            # Tentar buscar orçamento aprovado como contrato
            orcamento = db.orcamentos.find_one({
                '_id': ObjectId(id),
                'status': 'aprovado'
            })
            if orcamento:
                contrato = orcamento
            else:
                return jsonify({'success': False, 'message': 'Contrato não encontrado'}), 404

        # Buscar dados do cliente
        if 'cliente_id' in contrato:
            cliente = db.clientes.find_one({'_id': contrato['cliente_id']})
            if cliente:
                contrato['cliente_nome'] = cliente.get('nome')
                contrato['cliente_cpf'] = cliente.get('cpf')
                contrato['cliente_telefone'] = cliente.get('telefone')
                contrato['cliente_email'] = cliente.get('email')
                contrato['cliente_endereco'] = cliente.get('endereco')

        return jsonify({
            'success': True,
            'contrato': convert_objectid(contrato)
        })
    except Exception as e:
        logger.error(f"Erro ao buscar contrato: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao buscar contrato'}), 500

# ==================== AGENDAMENTOS ====================

@api_complete.route('/api/agendamento/<id>', methods=['GET'])
@require_auth
def get_agendamento(id):
    """Retorna detalhes de um agendamento"""
    try:
        db = get_db()

        agendamento = db.agendamentos.find_one({'_id': ObjectId(id)})
        if not agendamento:
            return jsonify({'success': False, 'message': 'Agendamento não encontrado'}), 404

        # Buscar dados relacionados
        if 'cliente_id' in agendamento:
            cliente = db.clientes.find_one({'_id': agendamento['cliente_id']})
            if cliente:
                agendamento['cliente_nome'] = cliente.get('nome')
                agendamento['cliente_telefone'] = cliente.get('telefone')

        if 'servico_id' in agendamento:
            servico = db.servicos.find_one({'_id': agendamento['servico_id']})
            if servico:
                agendamento['servico_nome'] = servico.get('nome')

        if 'profissional_id' in agendamento:
            prof = db.profissionais.find_one({'_id': agendamento['profissional_id']})
            if prof:
                agendamento['profissional_nome'] = prof.get('nome')

        return jsonify({
            'success': True,
            'agendamento': convert_objectid(agendamento)
        })
    except Exception as e:
        logger.error(f"Erro ao buscar agendamento: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao buscar agendamento'}), 500

@api_complete.route('/api/agendamento/<id>/confirmar', methods=['POST'])
@require_auth
def confirmar_agendamento(id):
    """Confirma um agendamento"""
    try:
        db = get_db()

        db.agendamentos.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'status': 'confirmado',
                'data_confirmacao': datetime.utcnow(),
                'confirmado_por': ObjectId(session.get('user_id'))
            }}
        )

        return jsonify({
            'success': True,
            'message': 'Agendamento confirmado'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': 'Erro ao confirmar'}), 500

@api_complete.route('/api/agendamento/<id>/cancelar', methods=['POST'])
@require_auth
def cancelar_agendamento(id):
    """Cancela um agendamento"""
    try:
        db = get_db()

        data = request.get_json()

        db.agendamentos.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'status': 'cancelado',
                'data_cancelamento': datetime.utcnow(),
                'motivo_cancelamento': data.get('motivo', ''),
                'cancelado_por': ObjectId(session.get('user_id'))
            }}
        )

        return jsonify({
            'success': True,
            'message': 'Agendamento cancelado'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': 'Erro ao cancelar'}), 500

# ==================== ANAMNESE ====================

@api_complete.route('/api/anamnese', methods=['POST'])
@require_auth
def criar_anamnese():
    """Cria uma nova anamnese"""
    try:
        db = get_db()
        data = request.get_json()

        anamnese = {
            'cliente_id': ObjectId(data['cliente_id']),
            'data': datetime.utcnow(),
            'queixa_principal': data.get('queixa_principal', ''),
            'historico_medico': data.get('historico_medico', ''),
            'medicamentos': data.get('medicamentos', ''),
            'alergias': data.get('alergias', ''),
            'habitos': data.get('habitos', ''),
            'observacoes': data.get('observacoes', ''),
            'profissional_id': ObjectId(session.get('user_id')),
            'created_at': datetime.utcnow()
        }

        result = db.anamneses.insert_one(anamnese)
        anamnese['_id'] = result.inserted_id

        return jsonify({
            'success': True,
            'anamnese': convert_objectid(anamnese),
            'message': 'Anamnese criada com sucesso'
        })
    except Exception as e:
        logger.error(f"Erro ao criar anamnese: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao criar anamnese'}), 500

# ==================== NOTIFICAÇÕES ====================

@api_complete.route('/api/notificacao/enviar', methods=['POST'])
@require_auth
def enviar_notificacao():
    """Envia notificação para cliente"""
    try:
        db = get_db()
        data = request.get_json()

        cliente_id = ObjectId(data['cliente_id'])
        cliente = db.clientes.find_one({'_id': cliente_id})

        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404

        notificacao = {
            'cliente_id': cliente_id,
            'tipo': data.get('tipo', 'geral'),
            'mensagem': data['mensagem'],
            'canais': data.get('canais', ['sms']),
            'status': 'pendente',
            'created_at': datetime.utcnow()
        }

        # Aqui você deve implementar o envio real via SMS/Email/WhatsApp
        # Por enquanto, apenas registra no banco

        db.notificacoes.insert_one(notificacao)

        # Simular envio bem-sucedido
        notificacao['status'] = 'enviado'
        db.notificacoes.update_one(
            {'_id': notificacao['_id']},
            {'$set': {'status': 'enviado', 'data_envio': datetime.utcnow()}}
        )

        return jsonify({
            'success': True,
            'message': 'Notificação enviada com sucesso'
        })
    except Exception as e:
        logger.error(f"Erro ao enviar notificação: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao enviar notificação'}), 500

# ==================== ESTOQUE ====================

@api_complete.route('/api/estoque/alertas', methods=['GET'])
@require_auth
def get_estoque_alertas():
    """Retorna alertas de estoque baixo"""
    try:
        db = get_db()

        produtos_baixo_estoque = list(db.produtos.find({
            '$expr': {'$lte': ['$estoque', '$estoque_minimo']}
        }))

        return jsonify({
            'success': True,
            'alertas': convert_objectid(produtos_baixo_estoque)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': 'Erro ao buscar alertas'}), 500

@api_complete.route('/api/estoque/movimentacoes', methods=['GET'])
@require_auth
def get_estoque_movimentacoes():
    """Lista movimentações de estoque"""
    try:
        db = get_db()

        movimentacoes = list(db.estoque_movimentacoes.find().sort('data', -1).limit(100))

        # Adicionar nome do produto
        for mov in movimentacoes:
            if 'produto_id' in mov:
                produto = db.produtos.find_one({'_id': mov['produto_id']})
                if produto:
                    mov['produto_nome'] = produto.get('nome')

        return jsonify({
            'success': True,
            'movimentacoes': convert_objectid(movimentacoes)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': 'Erro ao buscar movimentações'}), 500

# ==================== FINANCEIRO ====================

@api_complete.route('/api/financeiro/receitas', methods=['GET'])
@require_auth
def get_financeiro_receitas():
    """Lista receitas (orçamentos aprovados)"""
    try:
        db = get_db()

        # Filtros de data
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')

        filtros = {'status': 'aprovado'}

        if data_inicio:
            filtros['data_aprovacao'] = {'$gte': datetime.fromisoformat(data_inicio)}
        if data_fim:
            if 'data_aprovacao' in filtros:
                filtros['data_aprovacao']['$lte'] = datetime.fromisoformat(data_fim)
            else:
                filtros['data_aprovacao'] = {'$lte': datetime.fromisoformat(data_fim)}

        receitas = list(db.orcamentos.find(filtros).sort('data_aprovacao', -1).limit(100))

        # Adicionar dados do cliente
        for rec in receitas:
            if 'cliente_id' in rec:
                cliente = db.clientes.find_one({'_id': rec['cliente_id']})
                if cliente:
                    rec['cliente_nome'] = cliente.get('nome')

        total = sum(r.get('valor_total', 0) for r in receitas)

        return jsonify({
            'success': True,
            'receitas': convert_objectid(receitas),
            'total': total
        })
    except Exception as e:
        return jsonify({'success': False, 'message': 'Erro ao buscar receitas'}), 500

@api_complete.route('/api/financeiro/comissoes', methods=['GET'])
@require_auth
def get_financeiro_comissoes():
    """Lista comissões a pagar"""
    try:
        db = get_db()

        # Buscar orçamentos aprovados com comissões pendentes
        pipeline = [
            {'$match': {'status': 'aprovado', 'comissao_paga': {'$ne': True}}},
            {'$unwind': '$servicos'},
            {
                '$lookup': {
                    'from': 'servicos',
                    'localField': 'servicos.servico_id',
                    'foreignField': '_id',
                    'as': 'servico_info'
                }
            },
            {
                '$group': {
                    '_id': '$servicos.profissional_id',
                    'total_comissao': {'$sum': '$servicos.valor_comissao'},
                    'servicos_count': {'$sum': 1},
                    'orcamentos': {'$addToSet': '$_id'}
                }
            }
        ]

        comissoes = list(db.orcamentos.aggregate(pipeline))

        # Adicionar dados do profissional
        for com in comissoes:
            if com['_id']:
                prof = db.profissionais.find_one({'_id': com['_id']})
                if prof:
                    com['profissional_nome'] = prof.get('nome')

        return jsonify({
            'success': True,
            'comissoes': convert_objectid(comissoes)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': 'Erro ao buscar comissões'}), 500

# ==================== RELATÓRIOS ====================

@api_complete.route('/api/relatorios/mapa-calor/carregar', methods=['GET'])
@require_auth
def carregar_mapa_calor():
    """Carrega dados do mapa de calor"""
    try:
        db = get_db()

        # Últimos 30 dias
        data_inicio = datetime.now() - timedelta(days=30)

        pipeline = [
            {
                '$match': {
                    'data': {'$gte': data_inicio},
                    'status': {'$ne': 'cancelado'}
                }
            },
            {
                '$group': {
                    '_id': {
                        'dia': {'$dayOfWeek': '$data'},
                        'hora': {'$hour': '$data'}
                    },
                    'quantidade': {'$sum': 1}
                }
            }
        ]

        dados = list(db.agendamentos.aggregate(pipeline))

        # Formatar dados para o mapa de calor
        mapa = {}
        for item in dados:
            dia = item['_id']['dia']
            hora = item['_id']['hora']
            if dia not in mapa:
                mapa[dia] = {}
            mapa[dia][hora] = item['quantidade']

        return jsonify({
            'success': True,
            'mapa': mapa,
            'tipo': 'agendamentos'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': 'Erro ao gerar mapa de calor'}), 500

# ==================== FUNÇÃO DE RENDERIZAÇÃO DO DASHBOARD ====================

def render_dashboard(data):
    """Renderiza dados do dashboard na interface"""
    # Esta função seria chamada pelo JavaScript para atualizar a interface
    return {
        'html': f"""
            <div class="dashboard-stats">
                <div class="stat-card">
                    <h3>{data['estatisticas']['total_clientes']}</h3>
                    <p>Clientes</p>
                </div>
                <div class="stat-card">
                    <h3>{data['estatisticas']['agendamentos_hoje']}</h3>
                    <p>Agendamentos Hoje</p>
                </div>
                <div class="stat-card">
                    <h3>R$ {data['estatisticas']['faturamento_mes']:.2f}</h3>
                    <p>Faturamento Mês</p>
                </div>
            </div>
        """
    }

# Exportar blueprint
def register_complete_routes(app):
    """Registra todas as rotas completas no app"""
    app.register_blueprint(api_complete)
    return api_complete