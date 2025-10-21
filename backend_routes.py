from flask import Blueprint, request, jsonify, current_app
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import base64

api = Blueprint('api', __name__)

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