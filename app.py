#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA UBERABA v2.5 - CORRIGIDO FINAL
Data: 2025-10-05 03:29:09 UTC
"""

from flask import Flask, render_template, request, jsonify, session, send_file
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import urllib.parse, os, io, csv, json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests, pandas as pd
from bson import ObjectId
from functools import wraps
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'bioma-2025')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

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
        print("✅ MongoDB OK")
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
            return jsonify({'success': False}), 401
        return f(*args, **kwargs)
    return decorated

def send_email(to, name, subj, html, pdf=None):
    key = os.getenv('MAILERSEND_API_KEY')
    if not key: return {'success': False}
    data = {
        "from": {"email": os.getenv('MAILERSEND_FROM_EMAIL', 'noreply@bioma.com'), "name": "BIOMA"},
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

@app.route('/api/system/status')
def status():
    return jsonify({
        'success': True,
        'status': {
            'mongodb': {'operational': db is not None, 'message': 'OK' if db is not None else 'OFF'},
            'mailersend': {'operational': bool(os.getenv('MAILERSEND_API_KEY'))},
            'server': {'operational': True, 'time': datetime.now().isoformat()}
        }
    })

@app.route('/api/register', methods=['POST'])
def register():
    if db is None: return jsonify({'success': False, 'message': 'BD OFF'})
    d = request.json
    if db.users.find_one({'$or': [{'username': d.get('username')}, {'email': d.get('email')}]}):
        return jsonify({'success': False, 'message': 'Usuário existe'})
    db.users.insert_one({
        'username': d.get('username'), 'email': d.get('email'), 'name': d.get('name'),
        'password': generate_password_hash(d.get('password')),
        'role': 'user', 'theme': 'light', 'created_at': datetime.now()
    })
    send_email(d.get('email'), d.get('name'), 'Bem-vindo!', f'<h2>Olá {d.get("name")}!</h2>')
    return jsonify({'success': True})

@app.route('/api/login', methods=['POST'])
def login():
    if db is None: return jsonify({'success': False})
    d = request.json
    u = db.users.find_one({'$or': [{'username': d.get('username')}, {'email': d.get('username')}]})
    if u and check_password_hash(u['password'], d.get('password')):
        session.clear()
        session['user_id'] = str(u['_id'])
        session['username'] = u['username']
        session['role'] = u.get('role', 'user')
        session['theme'] = u.get('theme', 'light')
        session.permanent = True
        return jsonify({
            'success': True,
            'user': {'id': str(u['_id']), 'username': u['username'], 'email': u['email'], 
                    'name': u.get('name', ''), 'role': u.get('role', 'user'), 'theme': u.get('theme', 'light')}
        })
    return jsonify({'success': False})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/current-user')
def current_user():
    if 'user_id' not in session or db is None: return jsonify({'success': False})
    u = db.users.find_one({'_id': ObjectId(session['user_id'])})
    if u:
        return jsonify({'success': True, 'user': {
            'id': str(u['_id']), 'username': u['username'], 'email': u['email'],
            'name': u.get('name', ''), 'role': u.get('role', 'user'), 'theme': u.get('theme', 'light')
        }})
    return jsonify({'success': False})

@app.route('/api/update-theme', methods=['POST'])
@login_required
def update_theme():
    t = request.json.get('theme', 'light')
    db.users.update_one({'_id': ObjectId(session['user_id'])}, {'$set': {'theme': t}})
    session['theme'] = t
    return jsonify({'success': True})

@app.route('/api/clientes/buscar')
@login_required
def buscar_clientes():
    t = request.args.get('termo', '').strip()
    if len(t) < 3: return jsonify({'success': True, 'clientes': []})
    c = list(db.clientes.find({'$or': [{'nome': {'$regex': t, '$options': 'i'}}, {'cpf': {'$regex': t, '$options': 'i'}}]}).limit(10))
    return jsonify({'success': True, 'clientes': c})

@app.route('/api/clientes', methods=['GET', 'POST'])
@login_required
def clientes():
    if request.method == 'GET':
        return jsonify({'success': True, 'clientes': list(db.clientes.find({}).sort('nome', 1))})
    d = request.json
    c = {'cpf': d.get('cpf'), 'nome': d.get('nome'), 'rg': d.get('rg', ''), 'email': d.get('email', ''),
         'telefone': d.get('telefone', ''), 'cep': d.get('cep', ''), 'endereco': d.get('endereco', ''),
         'bairro': d.get('bairro', ''), 'cidade': d.get('cidade', ''), 'estado': d.get('estado', ''),
         'created_at': datetime.now(), 'updated_at': datetime.now()}
    e = db.clientes.find_one({'cpf': d.get('cpf')})
    if e: db.clientes.update_one({'cpf': d.get('cpf')}, {'$set': c})
    else: db.clientes.insert_one(c)
    return jsonify({'success': True})

@app.route('/api/clientes/<cpf>')
@login_required
def cliente(cpf):
    c = db.clientes.find_one({'cpf': cpf})
    return jsonify({'success': bool(c), 'cliente': c}) if c else jsonify({'success': False})

@app.route('/api/profissionais', methods=['GET', 'POST'])
@login_required
def profissionais():
    if request.method == 'GET':
        return jsonify({'success': True, 'profissionais': list(db.profissionais.find({}).sort('nome', 1))})
    d = request.json
    p = {'nome': d.get('nome'), 'cpf': d.get('cpf'), 'email': d.get('email', ''), 'telefone': d.get('telefone', ''),
         'especialidade': d.get('especialidade', ''), 'comissao_perc': float(d.get('comissao_perc', 0)),
         'ativo': True, 'created_at': datetime.now()}
    e = db.profissionais.find_one({'cpf': d.get('cpf')})
    if e: db.profissionais.update_one({'_id': e['_id']}, {'$set': p})
    else: db.profissionais.insert_one(p)
    return jsonify({'success': True})

@app.route('/api/profissionais/buscar')
@login_required
def buscar_profissionais():
    t = request.args.get('termo', '').strip()
    if len(t) < 2: return jsonify({'success': True, 'profissionais': []})
    p = list(db.profissionais.find({'$or': [{'nome': {'$regex': t, '$options': 'i'}}, {'especialidade': {'$regex': t, '$options': 'i'}}], 'ativo': True}).limit(10))
    return jsonify({'success': True, 'profissionais': p})

@app.route('/api/servicos/buscar')
@login_required
def buscar_servicos():
    t = request.args.get('termo', '').strip()
    if len(t) < 2: return jsonify({'success': True, 'servicos': []})
    s = list(db.servicos.find({'nome': {'$regex': t, '$options': 'i'}, 'ativo': True}).limit(20))
    return jsonify({'success': True, 'servicos': s})

@app.route('/api/servicos', methods=['GET', 'POST'])
@login_required
def servicos():
    if request.method == 'GET':
        return jsonify({'success': True, 'servicos': list(db.servicos.find({}).sort('nome', 1))})
    d = request.json
    tam = ['Kids', 'Masculino', 'Curto', 'Médio', 'Longo', 'Extra Longo']
    for t in tam:
        db.servicos.insert_one({
            'nome': d.get('nome'), 'sku': f"{d.get('nome')}-{t}".upper().replace(' ', '-'),
            'tamanho': t, 'preco': float(d.get(f'preco_{t.lower().replace(" ", "_")}', 0)),
            'categoria': d.get('categoria', 'Serviço'), 'ativo': True, 'created_at': datetime.now()
        })
    return jsonify({'success': True})

@app.route('/api/produtos/buscar')
@login_required
def buscar_produtos():
    t = request.args.get('termo', '').strip()
    if len(t) < 2: return jsonify({'success': True, 'produtos': []})
    p = list(db.produtos.find({'nome': {'$regex': t, '$options': 'i'}, 'ativo': True}).limit(20))
    return jsonify({'success': True, 'produtos': p})

@app.route('/api/produtos', methods=['GET', 'POST'])
@login_required
def produtos():
    if request.method == 'GET':
        return jsonify({'success': True, 'produtos': list(db.produtos.find({}).sort('nome', 1))})
    d = request.json
    db.produtos.insert_one({
        'nome': d.get('nome'), 'sku': d.get('sku', ''), 'preco': float(d.get('preco', 0)),
        'custo': float(d.get('custo', 0)), 'estoque': int(d.get('estoque', 0)),
        'categoria': d.get('categoria', 'Produto'), 'ativo': True, 'created_at': datetime.now()
    })
    return jsonify({'success': True})

@app.route('/api/fila', methods=['GET', 'POST'])
@login_required
def fila():
    if request.method == 'GET':
        return jsonify({'success': True, 'fila': list(db.fila_atendimento.find({'status': 'aguardando'}).sort('created_at', 1))})
    d = request.json
    p = db.fila_atendimento.count_documents({'status': 'aguardando'}) + 1
    i = db.fila_atendimento.insert_one({
        'cliente_nome': d.get('cliente_nome'), 'cliente_telefone': d.get('cliente_telefone'),
        'servico': d.get('servico'), 'profissional': d.get('profissional', ''),
        'posicao': p, 'status': 'aguardando', 'created_at': datetime.now()
    })
    if d.get('cliente_telefone'):
        send_sms(d.get('cliente_telefone'), f"BIOMA: Posicao {p} na fila")
    return jsonify({'success': True, 'posicao': p, 'id': str(i.inserted_id)})

@app.route('/api/fila/chamar/<id>', methods=['POST'])
@login_required
def chamar_fila(id):
    i = db.fila_atendimento.find_one({'_id': ObjectId(id)})
    if not i: return jsonify({'success': False})
    db.fila_atendimento.update_one({'_id': ObjectId(id)}, {'$set': {'status': 'atendendo', 'chamado_at': datetime.now()}})
    if i.get('cliente_telefone'):
        send_sms(i.get('cliente_telefone'), f"BIOMA: Sua vez!")
    return jsonify({'success': True})

@app.route('/api/fila/finalizar/<id>', methods=['POST'])
@login_required
def finalizar_fila(id):
    db.fila_atendimento.update_one({'_id': ObjectId(id)}, {'$set': {'status': 'finalizado', 'finalizado_at': datetime.now()}})
    return jsonify({'success': True})

def gerar_pdf(orc):
    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    p.setFillColor(HexColor('#7C3AED'))
    p.rect(0, h-120, w, 120, fill=1)
    p.setFillColor(HexColor('#FFFFFF'))
    p.setFont("Helvetica-Bold", 32)
    p.drawCentredString(w/2, h-60, "BIOMA")
    p.setFont("Helvetica", 14)
    p.drawCentredString(w/2, h-85, "UBERABA")
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(w/2, h-110, f"ORÇAMENTO #{orc.get('numero', '')}")
    y = h-160
    p.setFillColor(HexColor('#000000'))
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "CLIENTE")
    y -= 25
    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Nome: {orc.get('cliente_nome', '')}")
    y -= 18
    p.drawString(50, y, f"CPF: {orc.get('cliente_cpf', '')}")
    y -= 50
    p.setFont("Helvetica-Bold", 16)
    p.setFillColor(HexColor('#7C3AED'))
    p.drawString(50, y, f"TOTAL: R$ {orc.get('total_final', 0):.2f}")
    p.setFont("Helvetica", 8)
    p.drawCentredString(w/2, 50, "BIOMA Uberaba - (34) 99235-5890")
    p.showPage()
    p.save()
    buf.seek(0)
    return buf

@app.route('/api/orcamentos', methods=['GET', 'POST'])
@login_required
def orcamentos():
    if request.method == 'GET':
        return jsonify({'success': True, 'orcamentos': list(db.orcamentos.find({}).sort('created_at', -1))})
    d = request.json
    ts = sum(i['total'] for i in d.get('servicos', []))
    tp = sum(i['total'] for i in d.get('produtos', []))
    st = ts + tp
    dg = float(d.get('desconto_global', 0))
    tc = st * (1 - dg/100)
    cp = float(d.get('cashback_perc', 0))
    cv = tc * (cp/100)
    o = {
        'numero': db.orcamentos.count_documents({}) + 1,
        'cliente_cpf': d.get('cliente_cpf'), 'cliente_nome': d.get('cliente_nome'),
        'cliente_email': d.get('cliente_email', ''), 'cliente_telefone': d.get('cliente_telefone', ''),
        'profissional': d.get('profissional', ''), 'servicos': d.get('servicos', []), 'produtos': d.get('produtos', []),
        'subtotal': st, 'desconto_global': dg, 'total_com_desconto': tc,
        'cashback_perc': cp, 'cashback_valor': cv, 'total_final': tc,
        'pagamento': d.get('pagamento', {}), 'observacoes': d.get('observacoes', ''),
        'status': d.get('status', 'Pendente'), 'created_at': datetime.now(), 'user_id': session['user_id']
    }
    r = db.orcamentos.insert_one(o)
    if d.get('cliente_email') and d.get('status') == 'Aprovado':
        pdf = gerar_pdf(o)
        send_email(d.get('cliente_email'), d.get('cliente_nome'), f'Orçamento #{o["numero"]}',
                  f'<h2>Orçamento BIOMA</h2><p>Total: R$ {tc:.2f}</p>',
                  {'filename': f'orcamento_{o["numero"]}.pdf', 'content': pdf.getvalue()})
    if d.get('cliente_telefone'):
        send_sms(d.get('cliente_telefone'), f"BIOMA: Orcamento #{o['numero']} - R$ {tc:.2f}")
    return jsonify({'success': True, 'id': str(r.inserted_id), 'numero': o['numero']})

@app.route('/api/contratos')
@login_required
def contratos():
    return jsonify({'success': True, 'contratos': list(db.orcamentos.find({'status': 'Aprovado'}).sort('created_at', -1))})

@app.route('/api/gerar-contrato-pdf/<id>')
@login_required
def gerar_contrato(id):
    o = db.orcamentos.find_one({'_id': ObjectId(id)})
    if not o: return jsonify({'success': False})
    return send_file(gerar_pdf(o), as_attachment=True, download_name=f'contrato_{o.get("numero", "")}.pdf', mimetype='application/pdf')

@app.route('/api/pacotes', methods=['GET', 'POST'])
@login_required
def pacotes():
    if request.method == 'GET':
        return jsonify({'success': True, 'pacotes': list(db.pacotes.find({}))})
    d = request.json
    db.pacotes.insert_one({
        'nome': d.get('nome'), 'tipo': d.get('tipo'), 'valor': float(d.get('valor', 0)),
        'conteudo': d.get('conteudo'), 'beneficios': d.get('beneficios'),
        'desconto_perc': float(d.get('desconto_perc', 0)), 'cashback_perc': float(d.get('cashback_perc', 0)),
        'ativo': True, 'created_at': datetime.now()
    })
    return jsonify({'success': True})

@app.route('/api/config', methods=['GET', 'POST'])
@login_required
def config():
    if request.method == 'GET':
        c = db.config.find_one({'key': 'unidade'})
        return jsonify({'success': True, 'config': c}) if c else jsonify({'success': True, 'config': {}})
    d = request.json
    db.config.update_one({'key': 'unidade'}, {'$set': {
        'key': 'unidade', 'nome': d.get('nome'), 'cnpj': d.get('cnpj'),
        'endereco': d.get('endereco'), 'telefone': d.get('telefone'), 'email': d.get('email')
    }}, upsert=True)
    return jsonify({'success': True})

@app.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    return jsonify({
        'success': True,
        'stats': {
            'total_orcamentos': db.orcamentos.count_documents({}),
            'total_clientes': db.clientes.count_documents({}),
            'total_servicos': db.servicos.count_documents({}),
            'total_produtos': db.produtos.count_documents({}),
            'total_profissionais': db.profissionais.count_documents({'ativo': True}),
            'faturamento': sum([o.get('total_final', 0) for o in db.orcamentos.find({'status': 'Aprovado'})])
        }
    })

@app.route('/api/importar', methods=['POST'])
@login_required
def importar():
    if 'file' not in request.files: return jsonify({'success': False, 'message': 'Sem arquivo'})
    f = request.files['file']
    t = request.form.get('tipo', 'produtos')
    if not f.filename or not f.filename.endswith(('.csv', '.xlsx', '.xls')):
        return jsonify({'success': False, 'message': 'Formato inválido'})
    try:
        fn = secure_filename(f.filename)
        fp = os.path.join(app.config['UPLOAD_FOLDER'], fn)
        f.save(fp)
        df = pd.read_csv(fp) if fn.endswith('.csv') else pd.read_excel(fp)
        df = df.fillna('')
        cs = 0
        if t == 'produtos':
            for _, r in df.iterrows():
                db.produtos.insert_one({
                    'nome': str(r.get('nome', '')).strip(), 'sku': str(r.get('sku', '')).strip(),
                    'preco': float(r.get('preco', 0)), 'custo': float(r.get('custo', 0)),
                    'estoque': int(r.get('estoque', 0)), 'categoria': str(r.get('categoria', 'Produto')).strip(),
                    'ativo': True, 'created_at': datetime.now()
                })
                cs += 1
        else:
            tam = ['Kids', 'Masculino', 'Curto', 'Médio', 'Longo', 'Extra Longo']
            for _, r in df.iterrows():
                n = str(r.get('nome', '')).strip()
                for t in tam:
                    db.servicos.insert_one({
                        'nome': n, 'sku': f"{n}-{t}".upper().replace(' ', '-'),
                        'tamanho': t, 'preco': float(r.get(t.lower().replace(' ', '_'), 0)),
                        'categoria': str(r.get('categoria', 'Serviço')).strip(),
                        'ativo': True, 'created_at': datetime.now()
                    })
                cs += 1
        os.remove(fp)
        return jsonify({'success': True, 'message': f'{cs} importados', 'count_success': cs, 'count_error': 0})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/template/download/<tipo>')
@login_required
def download_template(tipo):
    buf = io.StringIO()
    w = csv.writer(buf)
    if tipo == 'produtos':
        w.writerow(['nome', 'sku', 'preco', 'custo', 'estoque', 'categoria'])
        w.writerow(['Shampoo 500ml', 'SHAMP-500', '45.00', '20.00', '50', 'Produto'])
    else:
        w.writerow(['nome', 'categoria', 'kids', 'masculino', 'curto', 'médio', 'longo', 'extra_longo'])
        w.writerow(['Hidratação', 'Tratamento', '60', '50', '60', '75', '90', '110'])
    buf.seek(0)
    return send_file(io.BytesIO(buf.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name=f'template_{tipo}.csv')

@app.route('/api/cep/<cep>')
def buscar_cep(cep):
    try:
        c = cep.replace('-', '').replace('.', '')
        r = requests.get(f'https://viacep.com.br/ws/{c}/json/', timeout=5)
        if r.status_code == 200:
            d = r.json()
            if not d.get('erro'):
                return jsonify({'success': True, 'endereco': {
                    'logradouro': d.get('logradouro', ''), 'bairro': d.get('bairro', ''),
                    'cidade': d.get('localidade', ''), 'estado': d.get('uf', ''), 'cep': d.get('cep', '')
                }})
        return jsonify({'success': False})
    except: return jsonify({'success': False})

def init_db():
    if db is None: return  # ✅ CORRIGIDO AQUI
    print("\n🔧 Inicializando...")
    if not db.users.find_one({'username': 'admin'}):
        db.users.insert_one({
            'username': 'admin', 'email': 'admin@bioma.com', 'name': 'Admin BIOMA',
            'password': generate_password_hash('admin123'), 'role': 'admin', 'theme': 'light', 'created_at': datetime.now()
        })
        print("✅ Admin: admin/admin123")
    if db.servicos.count_documents({}) == 0:
        tam = ['Kids', 'Masculino', 'Curto', 'Médio', 'Longo', 'Extra Longo']
        for n in ['Hidratação', 'Corte Feminino', 'Corte Masculino']:
            for t in tam:
                db.servicos.insert_one({
                    'nome': n, 'sku': f"{n}-{t}".upper().replace(' ', '-'),
                    'tamanho': t, 'preco': 50.0, 'categoria': 'Corte' if 'Corte' in n else 'Tratamento',
                    'ativo': True, 'created_at': datetime.now()
                })
        print("✅ Serviços OK")
    if db.produtos.count_documents({}) == 0:
        db.produtos.insert_one({'nome': 'Shampoo 500ml', 'sku': 'SHAMP-500', 'preco': 45.0, 'custo': 20.0, 'estoque': 50, 'categoria': 'Produto', 'ativo': True, 'created_at': datetime.now()})
        print("✅ Produtos OK")
    if db.profissionais.count_documents({}) == 0:
        db.profissionais.insert_one({'nome': 'Ana Silva', 'cpf': '000.000.000-00', 'especialidade': 'Coloração', 'comissao_perc': 30.0, 'ativo': True, 'email': '', 'telefone': '', 'created_at': datetime.now()})
        print("✅ Profissionais OK")
    if not db.config.find_one({'key': 'unidade'}):
        db.config.insert_one({'key': 'unidade', 'nome': 'BIOMA UBERABA', 'cnpj': '49.470.937/0001-10', 'endereco': 'Av. Santos Dumont 3110', 'telefone': '(34) 99235-5890', 'email': 'biomauberaba@gmail.com'})
        print("✅ Config OK")
    if db.pacotes.count_documents({}) == 0:
        db.pacotes.insert_one({'nome': 'BIOMA Bronze', 'tipo': 'Mensal', 'valor': 100.0, 'conteudo': '1 corte + 1 hidratação', 'beneficios': '5% desc + 5% cash', 'desconto_perc': 5, 'cashback_perc': 5, 'ativo': True, 'created_at': datetime.now()})
        print("✅ Pacotes OK")

if __name__ == '__main__':
    init_db()
    print("\n" + "="*80)
    print("🌳 BIOMA UBERABA v2.5 - COMPLETO")
    print("="*80)
    ip = os.getenv('PORT')
    url = 'https://bioma-system.onrender.com' if ip else 'http://localhost:5000'
    print(f"🚀 URL: {url}")
    print("👤 Login: admin / admin123")
    print(f"📧 Email: {'✅ OK' if os.getenv('MAILERSEND_API_KEY') else '⚠️  OFF'}")
    print(f"💾 MongoDB: {'✅ OK' if db is not None else '❌ OFF'}")  # ✅ CORRIGIDO AQUI
    print("="*80 + "\n")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)