#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA UBERABA v2.5 - SISTEMA ULTRA PROFISSIONAL
Desenvolvido por: @juanmarco1999
Data: 2025-10-05 05:01:32 UTC
"""

from flask import Flask, render_template, request, jsonify, session, send_file
from flask_cors import CORS
from flask_talisman import Talisman
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import urllib.parse, os, io, csv, json, re
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
from bson import ObjectId
from functools import wraps
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'bioma-2025')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

if os.getenv('FLASK_ENV') == 'production':
    csp = {
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'", 'cdn.jsdelivr.net', 'cdnjs.cloudflare.com'],
        'style-src': ["'self'", "'unsafe-inline'", 'cdn.jsdelivr.net', 'fonts.googleapis.com'],
        'font-src': ["'self'", 'fonts.gstatic.com', 'cdn.jsdelivr.net'],
        'img-src': ["'self'", 'data:', 'https:'],
    }
    Talisman(app, force_https=True, strict_transport_security=True, content_security_policy=csp)

CORS(app, supports_credentials=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# MongoDB
def get_db():
    try:
        u = urllib.parse.quote_plus(os.getenv('MONGO_USERNAME', ''))
        p = urllib.parse.quote_plus(os.getenv('MONGO_PASSWORD', ''))
        c = os.getenv('MONGO_CLUSTER', '')
        if not all([u, p, c]): return None
        uri = f"mongodb+srv://{u}:{p}@{c}/bioma_db?retryWrites=true&w=majority"
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.server_info()
        return client.bioma_db
    except Exception as e:
        print(f"❌ MongoDB: {e}")
        return None

db = get_db()

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId): return str(o)
        if isinstance(o, datetime): return o.isoformat()
        return super().default(o)

app.json_encoder = JSONEncoder

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def send_email(to, name, subj, html, pdf=None):
    key = os.getenv('MAILERSEND_API_KEY')
    if not key: return {'success': False}
    data = {
        "from": {"email": os.getenv('MAILERSEND_FROM_EMAIL', 'noreply@bioma.com'), "name": "BIOMA Uberaba"},
        "to": [{"email": to, "name": name}],
        "subject": subj,
        "html": html
    }
    if pdf:
        import base64
        data['attachments'] = [{"filename": pdf['filename'], "content": base64.b64encode(pdf['content']).decode()}]
    try:
        r = requests.post("https://api.mailersend.com/v1/email", 
                         headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}, 
                         json=data, timeout=10)
        return {'success': r.status_code == 202}
    except: return {'success': False}

def send_sms(num, msg):
    key = os.getenv('MAILERSEND_API_KEY')
    if not key: return {'success': False}
    n = '+55' + ''.join(filter(str.isdigit, num)) if not num.startswith('+') else num
    try:
        r = requests.post("https://api.mailersend.com/v1/sms",
                         headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
                         json={"from": "BIOMA", "to": [n], "text": msg}, timeout=10)
        return {'success': r.status_code == 202}
    except: return {'success': False}

# ROTAS
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'time': datetime.now().isoformat()}), 200

@app.route('/api/system/status')
@login_required
def system_status():
    status = {
        'mongodb': {'operational': db is not None, 'message': 'Conectado' if db else 'Desconectado', 'last_check': datetime.now()},
        'mailersend': {'operational': bool(os.getenv('MAILERSEND_API_KEY'))},
        'server': {'time': datetime.now()}
    }
    return jsonify({'success': True, 'status': status})

@app.route('/api/register', methods=['POST'])
def register():
    d = request.json
    if db.users.find_one({'$or': [{'username': d['username']}, {'email': d['email']}]}):
        return jsonify({'success': False, 'message': 'Usuário ou email já existe'})
    db.users.insert_one({
        'name': d['name'],
        'username': d['username'],
        'email': d['email'],
        'password': generate_password_hash(d['password']),
        'role': 'user',
        'theme': 'light',
        'created_at': datetime.now()
    })
    return jsonify({'success': True})

@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    u = db.users.find_one({'$or': [{'username': d['username']}, {'email': d['username']}]})
    if u and check_password_hash(u['password'], d['password']):
        session.permanent = True
        session['user_id'] = str(u['_id'])
        session['username'] = u['username']
        return jsonify({'success': True, 'user': {'id': str(u['_id']), 'name': u['name'], 'username': u['username'], 'theme': u.get('theme', 'light')}})
    return jsonify({'success': False, 'message': 'Credenciais inválidas'})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/current-user')
def current_user():
    if 'user_id' in session:
        u = db.users.find_one({'_id': ObjectId(session['user_id'])})
        if u:
            return jsonify({'success': True, 'user': {'id': str(u['_id']), 'name': u['name'], 'username': u['username'], 'theme': u.get('theme', 'light')}})
    return jsonify({'success': False})

@app.route('/api/update-theme', methods=['POST'])
@login_required
def update_theme():
    db.users.update_one({'_id': ObjectId(session['user_id'])}, {'$set': {'theme': request.json['theme']}})
    return jsonify({'success': True})

@app.route('/api/clientes', methods=['GET', 'POST'])
@login_required
def clientes():
    if request.method == 'GET':
        return jsonify({'success': True, 'clientes': list(db.clientes.find({}).sort('nome', 1))})
    d = request.json
    existing = db.clientes.find_one({'cpf': d['cpf']})
    if existing:
        db.clientes.update_one({'cpf': d['cpf']}, {'$set': {**d, 'updated_at': datetime.now()}})
    else:
        db.clientes.insert_one({**d, 'created_at': datetime.now()})
    return jsonify({'success': True})

@app.route('/api/clientes/buscar')
@login_required
def buscar_clientes():
    termo = request.args.get('termo', '')
    regex = {'$regex': termo, '$options': 'i'}
    clientes = list(db.clientes.find({'$or': [{'nome': regex}, {'cpf': regex}]}).limit(10))
    return jsonify({'success': True, 'clientes': clientes})

@app.route('/api/profissionais', methods=['GET', 'POST'])
@login_required
def profissionais():
    if request.method == 'GET':
        return jsonify({'success': True, 'profissionais': list(db.profissionais.find({}).sort('nome', 1))})
    d = request.json
    db.profissionais.insert_one({
        'nome': d['nome'],
        'cpf': d['cpf'],
        'email': d.get('email', ''),
        'telefone': d.get('telefone', ''),
        'especialidade': d.get('especialidade', ''),
        'comissao_perc': float(d.get('comissao_perc', 0)),
        'ativo': True,
        'created_at': datetime.now()
    })
    return jsonify({'success': True})

@app.route('/api/servicos', methods=['GET', 'POST'])
@login_required
def servicos():
    if request.method == 'GET':
        return jsonify({'success': True, 'servicos': list(db.servicos.find({}).sort('nome', 1))})
    d = request.json
    tamanhos = {
        'Kids': d.get('preco_kids', 0),
        'Masculino': d.get('preco_masculino', 0),
        'Curto': d.get('preco_curto', 0),
        'Médio': d.get('preco_medio', 0),
        'Longo': d.get('preco_longo', 0),
        'Extra Longo': d.get('preco_extra_longo', 0)
    }
    for tam, preco in tamanhos.items():
        db.servicos.insert_one({
            'nome': d['nome'],
            'sku': f"{d['nome'].upper().replace(' ', '-')}-{tam.upper().replace(' ', '-')}",
            'tamanho': tam,
            'preco': float(preco),
            'categoria': d.get('categoria', 'Serviço'),
            'ativo': True,
            'created_at': datetime.now()
        })
    return jsonify({'success': True})

@app.route('/api/servicos/buscar')
@login_required
def buscar_servicos():
    termo = request.args.get('termo', '')
    regex = {'$regex': termo, '$options': 'i'}
    servicos = list(db.servicos.find({'nome': regex}).limit(20))
    return jsonify({'success': True, 'servicos': servicos})

@app.route('/api/produtos', methods=['GET', 'POST'])
@login_required
def produtos():
    if request.method == 'GET':
        return jsonify({'success': True, 'produtos': list(db.produtos.find({}).sort('nome', 1))})
    d = request.json
    db.produtos.insert_one({
        'nome': d['nome'],
        'marca': d.get('marca', ''),
        'sku': d.get('sku', ''),
        'preco': float(d.get('preco', 0)),
        'custo': float(d.get('custo', 0)),
        'estoque': int(d.get('estoque', 0)),
        'categoria': d.get('categoria', 'Produto'),
        'ativo': True,
        'created_at': datetime.now()
    })
    return jsonify({'success': True})

@app.route('/api/produtos/buscar')
@login_required
def buscar_produtos():
    termo = request.args.get('termo', '')
    regex = {'$regex': termo, '$options': 'i'}
    produtos = list(db.produtos.find({'nome': regex}).limit(20))
    return jsonify({'success': True, 'produtos': produtos})

@app.route('/api/orcamentos', methods=['GET', 'POST'])
@login_required
def orcamentos():
    if request.method == 'GET':
        status = request.args.get('status')
        query = {'status': status} if status else {}
        return jsonify({'success': True, 'orcamentos': list(db.orcamentos.find(query).sort('created_at', -1))})
    
    d = request.json
    
    # Salvar/atualizar cliente
    db.clientes.update_one(
        {'cpf': d['cliente_cpf']},
        {'$set': {
            'cpf': d['cliente_cpf'],
            'nome': d['cliente_nome'],
            'email': d.get('cliente_email', ''),
            'telefone': d.get('cliente_telefone', ''),
            'updated_at': datetime.now()
        }},
        upsert=True
    )
    
    # Calcular totais
    subtotal = sum(s['total'] for s in d['servicos']) + sum(p['total'] for p in d['produtos'])
    desconto_valor = subtotal * (d.get('desconto_global', 0) / 100)
    total_com_desconto = subtotal - desconto_valor
    cashback_valor = total_com_desconto * (d.get('cashback_perc', 0) / 100)
    
    # Gerar número sequencial
    ultimo = db.orcamentos.find_one(sort=[('numero', -1)])
    numero = (ultimo['numero'] + 1) if ultimo and 'numero' in ultimo else 1
    
    # Salvar orçamento
    orc_id = db.orcamentos.insert_one({
        'numero': numero,
        'cliente_cpf': d['cliente_cpf'],
        'cliente_nome': d['cliente_nome'],
        'cliente_email': d.get('cliente_email', ''),
        'cliente_telefone': d.get('cliente_telefone', ''),
        'servicos': d['servicos'],
        'produtos': d['produtos'],
        'subtotal': subtotal,
        'desconto_global': d.get('desconto_global', 0),
        'desconto_valor': desconto_valor,
        'total_com_desconto': total_com_desconto,
        'cashback_perc': d.get('cashback_perc', 0),
        'cashback_valor': cashback_valor,
        'total_final': total_com_desconto,
        'pagamento': d.get('pagamento', {}),
        'status': d.get('status', 'Pendente'),
        'created_at': datetime.now(),
        'user_id': session['user_id']
    }).inserted_id
    
    # Se aprovado, gerar PDF e enviar email
    if d.get('status') == 'Aprovado':
        orc = db.orcamentos.find_one({'_id': orc_id})
        pdf_bytes = gerar_contrato_pdf(orc)
        
        if d.get('cliente_email'):
            send_email(
                d['cliente_email'],
                d['cliente_nome'],
                f"Contrato BIOMA #{numero}",
                f"<h2>Olá {d['cliente_nome']},</h2><p>Segue em anexo seu contrato de prestação de serviços.</p><p><strong>Total: R$ {total_com_desconto:.2f}</strong></p>",
                {'filename': f'contrato_bioma_{numero}.pdf', 'content': pdf_bytes}
            )
        
        if d.get('cliente_telefone'):
            send_sms(d['cliente_telefone'], f"BIOMA: Contrato #{numero} aprovado! Total: R$ {total_com_desconto:.2f}. Acesse seu email para detalhes.")
    
    return jsonify({'success': True, 'numero': numero, 'id': str(orc_id)})

@app.route('/api/contratos')
@login_required
def contratos():
    return jsonify({'success': True, 'contratos': list(db.orcamentos.find({'status': 'Aprovado'}).sort('created_at', -1))})

@app.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    return jsonify({'success': True, 'stats': {
        'total_orcamentos': db.orcamentos.count_documents({}),
        'total_clientes': db.clientes.count_documents({}),
        'total_servicos': db.servicos.count_documents({'ativo': True}),
        'faturamento': sum(o.get('total_final', 0) for o in db.orcamentos.find({'status': 'Aprovado'}))
    }})

@app.route('/api/fila', methods=['GET', 'POST'])
@login_required
def fila():
    if request.method == 'GET':
        return jsonify({'success': True, 'fila': list(db.fila_atendimento.find({'status': {'$in': ['aguardando', 'atendendo']}}).sort('created_at', 1))})
    
    d = request.json
    total = db.fila_atendimento.count_documents({'status': {'$in': ['aguardando', 'atendendo']}})
    
    db.fila_atendimento.insert_one({
        'cliente_nome': d['cliente_nome'],
        'cliente_telefone': d['cliente_telefone'],
        'servico': d.get('servico', ''),
        'profissional': d.get('profissional', ''),
        'posicao': total + 1,
        'status': 'aguardando',
        'created_at': datetime.now()
    })
    
    if d.get('cliente_telefone'):
        send_sms(d['cliente_telefone'], f"BIOMA: Você está na posição {total + 1} da fila. Aguarde ser chamado!")
    
    return jsonify({'success': True, 'posicao': total + 1})

@app.route('/api/fila/chamar/<id>', methods=['POST'])
@login_required
def chamar_fila(id):
    item = db.fila_atendimento.find_one({'_id': ObjectId(id)})
    if item:
        db.fila_atendimento.update_one({'_id': ObjectId(id)}, {'$set': {'status': 'atendendo', 'chamado_at': datetime.now()}})
        if item.get('cliente_telefone'):
            send_sms(item['cliente_telefone'], f"BIOMA: {item['cliente_nome']}, é sua vez! Dirija-se ao atendimento.")
    return jsonify({'success': True})

@app.route('/api/fila/finalizar/<id>', methods=['POST'])
@login_required
def finalizar_fila(id):
    db.fila_atendimento.update_one({'_id': ObjectId(id)}, {'$set': {'status': 'finalizado', 'finalizado_at': datetime.now()}})
    return jsonify({'success': True})

@app.route('/api/config', methods=['GET', 'POST'])
@login_required
def config():
    if request.method == 'GET':
        cfg = db.config.find_one({'key': 'unidade'}) or {}
        return jsonify({'success': True, 'config': cfg})
    d = request.json
    db.config.update_one({'key': 'unidade'}, {'$set': d}, upsert=True)
    return jsonify({'success': True})

@app.route('/api/cep/<cep>')
@login_required
def buscar_cep(cep):
    try:
        r = requests.get(f'https://viacep.com.br/ws/{cep}/json/', timeout=5)
        data = r.json()
        if 'erro' not in data:
            return jsonify({'success': True, 'endereco': {'logradouro': data.get('logradouro', ''), 'bairro': data.get('bairro', ''), 'cidade': data.get('localidade', ''), 'estado': data.get('uf', '')}})
    except: pass
    return jsonify({'success': False})

@app.route('/api/importar', methods=['POST'])
@login_required
def importar():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'})
    
    f = request.files['file']
    t = request.form.get('tipo', 'produtos')
    
    if not f.filename:
        return jsonify({'success': False, 'message': 'Arquivo inválido'})
    
    ext = f.filename.rsplit('.', 1)[1].lower() if '.' in f.filename else ''
    
    if ext not in ['csv', 'xlsx', 'xls']:
        return jsonify({'success': False, 'message': 'Apenas CSV ou XLSX'})
    
    try:
        fn = secure_filename(f.filename)
        fp = os.path.join(app.config['UPLOAD_FOLDER'], fn)
        f.save(fp)
        
        cs = 0
        ce = 0
        rows = []
        
        if ext == 'csv':
            encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(fp, 'r', encoding=encoding) as csvfile:
                        reader = csv.DictReader(csvfile)
                        rows = list(reader)
                        break
                except UnicodeDecodeError:
                    continue
            if not rows:
                return jsonify({'success': False, 'message': 'Erro ao ler CSV'})
        else:
            from openpyxl import load_workbook
            wb = load_workbook(fp, read_only=True, data_only=True)
            ws = wb.active
            headers = [str(cell.value).strip().lower() if cell.value else '' for cell in next(ws.iter_rows(min_row=1, max_row=1))]
            for row in ws.iter_rows(min_row=2, values_only=True):
                row_dict = {}
                for i in range(len(headers)):
                    if i < len(row):
                        val = row[i]
                        if isinstance(val, str):
                            val = val.strip()
                            if 'r$' in val.lower():
                                val = val.replace('R$', '').replace('r$', '').strip().replace('.', '').replace(',', '.')
                        row_dict[headers[i]] = val
                rows.append(row_dict)
            wb.close()
        
        if t == 'produtos':
            nome_cols = ['nome', 'produto', 'name', 'descricao', 'descrição']
            marca_cols = ['marca', 'brand', 'fabricante']
            preco_cols = ['preco', 'preço', 'price', 'valor']
            custo_cols = ['custo', 'cost']
            estoque_cols = ['estoque', 'quantidade', 'qtd', 'stock']
            categoria_cols = ['categoria', 'category', 'tipo']
            sku_cols = ['sku', 'codigo', 'código', 'code']
            
            for row in rows:
                try:
                    row_lower = {k.lower().strip(): v for k, v in row.items()}
                    
                    nome = None
                    for col in nome_cols:
                        if col in row_lower and row_lower[col]:
                            nome = str(row_lower[col]).strip()
                            break
                    
                    if not nome or len(nome) < 2:
                        ce += 1
                        continue
                    
                    marca = ''
                    for col in marca_cols:
                        if col in row_lower and row_lower[col]:
                            marca = str(row_lower[col]).strip()
                            break
                    
                    sku = ''
                    for col in sku_cols:
                        if col in row_lower and row_lower[col]:
                            sku = str(row_lower[col]).strip()
                            break
                    if not sku:
                        sku_base = re.sub(r'[^A-Z0-9]', '', nome.upper())[:10]
                        sku = f"{sku_base}-{cs+1}"
                    
                    preco = 0.0
                    for col in preco_cols:
                        if col in row_lower and row_lower[col]:
                            try:
                                val = str(row_lower[col]).replace('R$', '').replace('r$', '').strip().replace('.', '').replace(',', '.')
                                preco = float(val)
                                break
                            except: continue
                    
                    custo = 0.0
                    for col in custo_cols:
                        if col in row_lower and row_lower[col]:
                            try:
                                val = str(row_lower[col]).replace('R$', '').replace('r$', '').strip().replace('.', '').replace(',', '.')
                                custo = float(val)
                                break
                            except: continue
                    
                    estoque = 0
                    for col in estoque_cols:
                        if col in row_lower and row_lower[col]:
                            try:
                                estoque = int(float(row_lower[col]))
                                break
                            except: continue
                    
                    categoria = 'Produto'
                    for col in categoria_cols:
                        if col in row_lower and row_lower[col]:
                            categoria = str(row_lower[col]).strip().title()
                            break
                    
                    db.produtos.insert_one({
                        'nome': nome,
                        'marca': marca,
                        'sku': sku,
                        'preco': preco,
                        'custo': custo,
                        'estoque': estoque,
                        'categoria': categoria,
                        'ativo': True,
                        'created_at': datetime.now()
                    })
                    cs += 1
                except Exception as e:
                    ce += 1
                    continue
        else:
            nome_cols = ['nome', 'servico', 'serviço', 'service', 'concat']
            categoria_cols = ['categoria', 'category', 'tipo']
            tamanho_map = {
                'kids': ['kids', 'kid', 'infantil', 'crianca', 'criança'],
                'masculino': ['masculino', 'male', 'homem', 'masc'],
                'curto': ['curto', 'short', 'pequeno'],
                'medio': ['medio', 'médio', 'medium', 'm'],
                'longo': ['longo', 'long', 'grande', 'l'],
                'extra_longo': ['extra_longo', 'extra longo', 'xl', 'extra']
            }
            
            for row in rows:
                try:
                    row_lower = {k.lower().strip(): v for k, v in row.items()}
                    
                    nome = None
                    for col in nome_cols:
                        if col in row_lower and row_lower[col]:
                            val = str(row_lower[col]).strip()
                            match = re.search(r'\d*([A-Za-zÀ-ú\s]+)', val)
                            nome = match.group(1).strip() if match else val
                            break
                    
                    if not nome or len(nome) < 2:
                        ce += 1
                        continue
                    
                    categoria = 'Serviço'
                    for col in categoria_cols:
                        if col in row_lower and row_lower[col]:
                            categoria = str(row_lower[col]).strip().title()
                            break
                    
                    precos = {}
                    for tam_key, tam_aliases in tamanho_map.items():
                        for alias in tam_aliases:
                            if alias in row_lower and row_lower[alias]:
                                try:
                                    val = str(row_lower[alias]).replace('R$', '').replace('r$', '').strip().replace('.', '').replace(',', '.')
                                    preco = float(val)
                                    if preco > 0:
                                        precos[tam_key] = preco
                                        break
                                except: continue
                    
                    if not precos:
                        precos = {'curto': 0.0}
                    
                    for tam_key, preco in precos.items():
                        tam_nome = tam_key.replace('_', ' ').title()
                        db.servicos.insert_one({
                            'nome': nome,
                            'sku': f"{nome.upper().replace(' ', '-')}-{tam_nome.upper().replace(' ', '-')}",
                            'tamanho': tam_nome,
                            'preco': preco,
                            'categoria': categoria,
                            'ativo': True,
                            'created_at': datetime.now()
                        })
                    cs += 1
                except Exception as e:
                    ce += 1
                    continue
        
        os.remove(fp)
        msg = f'{cs} registros importados!'
        if ce > 0:
            msg += f' ({ce} erros)'
        return jsonify({'success': True, 'message': msg, 'count_success': cs, 'count_error': ce})
    except Exception as e:
        if os.path.exists(fp):
            os.remove(fp)
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@app.route('/api/template/download/<tipo>')
@login_required
def download_template(tipo):
    output = io.StringIO()
    writer = csv.writer(output)
    
    if tipo == 'produtos':
        writer.writerow(['nome', 'marca', 'sku', 'preco', 'custo', 'estoque', 'categoria'])
        writer.writerow(['Shampoo 500ml', 'Loreal', 'SHAMP-500', '49.90', '20.00', '50', 'SHAMPOO'])
    else:
        writer.writerow(['nome', 'categoria', 'kids', 'masculino', 'curto', 'medio', 'longo', 'extra_longo'])
        writer.writerow(['Hidratação', 'Tratamento', '50', '60', '80', '100', '120', '150'])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'template_{tipo}.csv'
    )

# GERAÇÃO DE PDF PROFISSIONAL
def gerar_contrato_pdf(orc):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    
    # Cabeçalho com logo BIOMA
    c.setFillColor(HexColor('#7C3AED'))
    c.setFont('Helvetica-Bold', 24)
    c.drawRightString(w - 2*cm, h - 2*cm, 'BIOMA')
    
    c.setFillColor(black)
    c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(w/2, h - 3*cm, 'CONTRATO DE PRESTAÇÃO DE SERVIÇOS')
    
    c.setFont('Helvetica', 10)
    c.drawCentredString(w/2, h - 3.7*cm, 'Pelo presente Instrumento Particular e na melhor forma de direito, as partes abaixo qualificadas:')
    
    # Linha
    c.setStrokeColor(HexColor('#7C3AED'))
    c.setLineWidth(2)
    c.line(2*cm, h - 4.2*cm, w - 2*cm, h - 4.2*cm)
    
    y = h - 5*cm
    
    # PARTES
    c.setFillColor(black)
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(w/2, y, 'PARTES')
    y -= 0.8*cm
    
    # CONTRATANTE
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(w/2, y, 'CONTRATANTE')
    y -= 0.6*cm
    
    c.setFont('Helvetica', 9)
    c.drawString(2*cm, y, f"Nome: {orc['cliente_nome']}")
    y -= 0.5*cm
    c.drawString(2*cm, y, f"CPF: {orc['cliente_cpf']}")
    if orc.get('cliente_telefone'):
        c.drawString(10*cm, y, f"Tel: {orc['cliente_telefone']}")
    y -= 0.5*cm
    if orc.get('cliente_email'):
        c.drawString(2*cm, y, f"E-mail: {orc['cliente_email']}")
    y -= 0.8*cm
    
    # CONTRATADA
    cfg = db.config.find_one({'key': 'unidade'}) or {}
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(w/2, y, 'CONTRATADA')
    y -= 0.6*cm
    
    c.setFont('Helvetica', 9)
    c.drawString(2*cm, y, f"Raz. Soc: {cfg.get('nome', 'BIOMA UBERABA')}")
    y -= 0.5*cm
    c.drawString(2*cm, y, f"CNPJ: {cfg.get('cnpj', '49.470.937/0001-10')}")
    y -= 0.5*cm
    c.drawString(2*cm, y, f"Cidade: UBERABA")
    c.drawString(10*cm, y, "Estado: MINAS GERAIS")
    y -= 0.5*cm
    c.drawString(2*cm, y, f"END.: {cfg.get('endereco', 'Av. Santos Dumont 3110 - Santa Maria - CEP 38050-400')}")
    y -= 0.5*cm
    c.drawString(2*cm, y, f"Tel: {cfg.get('telefone', '34 99235-5890')}")
    c.drawString(10*cm, y, f"E-mail: {cfg.get('email', 'biomauberaba@gmail.com')}")
    y -= 1*cm
    
    # ALERGIAS
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(w/2, y, 'ALERGIAS E CONDIÇÕES ESPECIAIS DE SAÚDE')
    y -= 0.6*cm
    c.setFont('Helvetica', 9)
    c.drawString(2*cm, y, "SUBSTÂNCIAS ALÉRGENAS:")
    y -= 0.5*cm
    c.setFillColor(HexColor('#DC2626'))
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(w/2, y, 'NÃO')
    c.setFillColor(black)
    y -= 0.7*cm
    c.setFont('Helvetica', 9)
    c.drawString(2*cm, y, "CONDIÇÕES ESPECIAIS DE SAÚDE:")
    y -= 0.5*cm
    c.setFillColor(HexColor('#DC2626'))
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(w/2, y, 'NÃO')
    c.setFillColor(black)
    y -= 1*cm
    
    # SERVIÇOS
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(w/2, y, 'SERVIÇOS')
    y -= 0.6*cm
    
    # Tabela de serviços
    data = [['Qtde.', 'SERVIÇOS', 'Desc.', 'Total s/ Desc.', 'Total c/ Desc.']]
    
    for srv in orc['servicos']:
        data.append([
            str(srv['qtd']),
            f"{srv['nome']} - {srv['tamanho']}",
            f"{srv.get('desconto', 0)}%",
            f"R$ {srv['preco_unit'] * srv['qtd']:.2f}",
            f"R$ {srv['total']:.2f}"
        ])
    
    if data:
        table = Table(data, colWidths=[2*cm, 8*cm, 2*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#7C3AED')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        table.wrapOn(c, w, h)
        table.drawOn(c, 2*cm, y - len(data) * 0.7*cm)
        y -= (len(data) + 1) * 0.7*cm
    
    y -= 1*cm
    
    # TOTAIS
    c.setFont('Helvetica-Bold', 10)
    c.drawRightString(14*cm, y, 'TOTAL BRUTO')
    c.drawRightString(w - 2*cm, y, f"R$ {orc['subtotal']:.2f}")
    y -= 0.5*cm
    
    if orc.get('desconto_valor', 0) > 0:
        c.drawRightString(14*cm, y, f"Desconto Total ({orc.get('desconto_global', 0)}%)")
        c.drawRightString(w - 2*cm, y, f"R$ {orc['desconto_valor']:.2f}")
        y -= 0.5*cm
    
    c.setFont('Helvetica-Bold', 12)
    c.drawRightString(14*cm, y, 'TOTAL')
    c.drawRightString(w - 2*cm, y, f"R$ {orc['total_final']:.2f}")
    y -= 1*cm
    
    # PAGAMENTO
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(w/2, y, 'VALOR E FORMA DE PAGAMENTO')
    y -= 0.6*cm
    
    c.setFont('Helvetica', 9)
    c.drawString(2*cm, y, f"VALOR TOTAL: R$ {orc['total_final']:.2f}")
    y -= 0.5*cm
    c.drawString(2*cm, y, f"FORMA DE PAGAMENTO: {orc.get('pagamento', {}).get('tipo', 'Pix')}")
    y -= 1*cm
    
    # DISPOSIÇÕES GERAIS
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(w/2, y, 'DISPOSIÇÕES GERAIS')
    y -= 0.6*cm
    
    c.setFont('Helvetica', 8)
    texto = 'Pelo presente instrumento particular, as "Partes" resolvem celebrar o presente "Contrato", de acordo com as cláusulas e condições a seguir.'
    c.drawString(2*cm, y, texto[:100])
    y -= 0.4*cm
    if len(texto) > 100:
        c.drawString(2*cm, y, texto[100:])
        y -= 0.4*cm
    
    y -= 0.5*cm
    
    clausulas = [
        "1. O Contrato tem por objeto a prestação de serviços acima descritos, pela Contratada à Contratante, mediante agendamento prévio.",
        "2. A Contratante declara estar ciente que (i) os serviços têm caráter pessoal e são transferíveis.",
        "3. Os serviços deverão ser utilizados em conformidade com o prazo acima indicado à Contratante."
    ]
    
    for clausula in clausulas:
        linhas = [clausula[i:i+110] for i in range(0, len(clausula), 110)]
        for linha in linhas:
            c.drawString(2*cm, y, linha)
            y -= 0.4*cm
        y -= 0.2*cm
    
    y -= 1*cm
    
    # ASSINATURAS
    c.setFont('Helvetica', 9)
    c.drawCentredString(w/2, y, f"UBERABA, {datetime.now().strftime('%d de %B de %Y')}")
    y -= 1.5*cm
    
    c.line(3*cm, y, 8*cm, y)
    c.line(11*cm, y, 16*cm, y)
    y -= 0.4*cm
    
    c.setFont('Helvetica-Bold', 8)
    c.drawCentredString(5.5*cm, y, f"CONTRATANTE: {orc['cliente_nome']}")
    c.drawCentredString(13.5*cm, y, f"CONTRATADA: BIOMA UBERABA - {cfg.get('cnpj', '49.470.937/0001-10')}")
    
    # Rodapé
    c.setFont('Helvetica', 7)
    c.setFillColor(HexColor('#6B7280'))
    c.drawCentredString(w/2, 1.5*cm, f"Contrato #{orc['numero']} | BIOMA UBERABA | {cfg.get('telefone', '34 99235-5890')} | {cfg.get('email', 'biomauberaba@gmail.com')}")
    
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

@app.route('/api/gerar-contrato-pdf/<id>')
@login_required
def gerar_contrato_pdf_route(id):
    orc = db.orcamentos.find_one({'_id': ObjectId(id)})
    if not orc:
        return "Orçamento não encontrado", 404
    
    pdf_bytes = gerar_contrato_pdf(orc)
    
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'contrato_bioma_{orc["numero"]}.pdf'
    )

def init_db():
    if db is None: return
    
    if db.users.count_documents({}) == 0:
        db.users.insert_one({
            'name': 'Administrador',
            'username': 'admin',
            'email': 'admin@bioma.com',
            'password': generate_password_hash('admin123'),
            'role': 'admin',
            'theme': 'light',
            'created_at': datetime.now()
        })
        print("✅ Admin: admin/admin123")
    
    if db.servicos.count_documents({}) == 0:
        for nome in ['Hidratação', 'Corte Feminino', 'Corte Masculino']:
            for tam, preco in [('Kids', 50), ('Masculino', 60), ('Curto', 80), ('Médio', 100), ('Longo', 120), ('Extra Longo', 150)]:
                db.servicos.insert_one({
                    'nome': nome,
                    'sku': f"{nome.upper().replace(' ', '-')}-{tam.upper().replace(' ', '-')}",
                    'tamanho': tam,
                    'preco': preco,
                    'categoria': 'Cabelo',
                    'ativo': True,
                    'created_at': datetime.now()
                })
        print("✅ Serviços OK")
    
    if db.produtos.count_documents({}) == 0:
        db.produtos.insert_one({
            'nome': 'Shampoo 500ml',
            'marca': 'BIOMA',
            'sku': 'SHAMP-500',
            'preco': 49.90,
            'custo': 20.00,
            'estoque': 50,
            'categoria': 'SHAMPOO',
            'ativo': True,
            'created_at': datetime.now()
        })
        print("✅ Produtos OK")
    
    if db.profissionais.count_documents({}) == 0:
        db.profissionais.insert_one({
            'nome': 'Maria Silva',
            'cpf': '000.000.000-00',
            'email': 'maria@bioma.com',
            'telefone': '(34) 99999-9999',
            'especialidade': 'Coloração',
            'comissao_perc': 10.0,
            'ativo': True,
            'created_at': datetime.now()
        })
        print("✅ Profissionais OK")
    
    if db.config.count_documents({}) == 0:
        db.config.insert_one({
            'key': 'unidade',
            'nome': 'BIOMA UBERABA',
            'cnpj': '49.470.937/0001-10',
            'endereco': 'Av. Santos Dumont 3110 - Santa Maria - Uberaba/MG - CEP 38050-400',
            'telefone': '34 99235-5890',
            'email': 'biomauberaba@gmail.com'
        })
        print("✅ Config OK")
    
    print("✅ Banco inicializado")

if __name__ == '__main__':
    init_db()
    print("\n" + "="*80)
    print("🌳 BIOMA UBERABA v2.5 - PRODUÇÃO")
    print("="*80)
    is_prod = os.getenv('FLASK_ENV') == 'production'
    url = 'https://bioma-system2.onrender.com' if is_prod else 'http://localhost:5000'
    print(f"🚀 URL: {url}")
    print(f"🔒 HTTPS: {'✅ ATIVO' if is_prod else '⚠️  Local'}")
    print(f"👤 Login: admin / admin123")
    print(f"📧 Email: {'✅ OK' if os.getenv('MAILERSEND_API_KEY') else '⚠️  OFF'}")
    print(f"💾 MongoDB: {'✅ OK' if db is not None else '❌ OFF'}")
    print("="*80 + "\n")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)