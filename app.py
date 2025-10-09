#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════
BIOMA UBERABA v3.9 ULTRA COMPLETO - BACKEND DEFINITIVO
═══════════════════════════════════════════════════════════════════════════
Desenvolvedor: Juan Marco Bernardos Souza e Silva (@juanmarco1999)
Email: 180147064@aluno.unb.br
Data: 2025-10-09 15:37:50 UTC
Versão: 3.9.0 (Build Final)
═══════════════════════════════════════════════════════════════════════════
"""

from flask import Flask, render_template, request, jsonify, session, send_file
from flask_cors import CORS
from pymongo import MongoClient, ASCENDING, DESCENDING
from bson import ObjectId
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps
from apscheduler.schedulers.background import BackgroundScheduler
import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import io
import csv
import json
import re
import secrets
import logging
import pytz

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DE LOGGING
# ═══════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('bioma_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# CARREGAR VARIÁVEIS DE AMBIENTE
# ═══════════════════════════════════════════════════════════════════════════

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════
# PYDANTIC SCHEMAS - VALIDAÇÃO DE DADOS
# ═══════════════════════════════════════════════════════════════════════════

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from PIL import Image

class ClientSchema(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    cpf: Optional[str] = None
    address: Optional[str] = None
    birth_date: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        # Remove caracteres não numéricos
        phone = ''.join(filter(str.isdigit, v))
        if len(phone) < 10:
            raise ValueError('Telefone inválido')
        return v

class ProfessionalSchema(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    specialty: str = Field(..., min_length=3, max_length=100)
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    commission: float = Field(default=0, ge=0, le=100)
    active: bool = True

class ServiceSchema(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    duration: int = Field(default=60, ge=5, le=480)
    category: Optional[str] = None
    active: bool = True

class ProductSchema(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    cost: float = Field(default=0, ge=0)
    stock: int = Field(default=0, ge=0)
    min_stock: int = Field(default=5, ge=0)
    category: Optional[str] = None
    barcode: Optional[str] = None
    active: bool = True

class BudgetItemSchema(BaseModel):
    id: str
    name: str
    price: float
    quantity: int = Field(default=1, ge=1)

class BudgetSchema(BaseModel):
    client_id: str
    client_name: str
    client_phone: Optional[str] = None
    client_email: Optional[EmailStr] = None
    services: List[BudgetItemSchema]
    products: Optional[List[BudgetItemSchema]] = []
    discount: float = Field(default=0, ge=0, le=100)
    notes: Optional[str] = None

class AppointmentSchema(BaseModel):
    client_id: str
    client_name: str
    professional_id: str
    professional_name: str
    service_id: str
    service_name: str
    date: str
    time: str
    duration: int = Field(default=60, ge=5, le=480)
    notes: Optional[str] = None

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DO FLASK
# ═══════════════════════════════════════════════════════════════════════════

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

CORS(app, supports_credentials=True)

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DO MONGODB
# ═══════════════════════════════════════════════════════════════════════════

try:
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client['bioma_system']
    logger.info('✅ MongoDB conectado com sucesso')
except Exception as e:
    logger.error(f'❌ Erro ao conectar MongoDB: {str(e)}')
    db = None

# Coleções do MongoDB
users_collection = db['users'] if db else None
clients_collection = db['clients'] if db else None
professionals_collection = db['professionals'] if db else None
services_collection = db['services'] if db else None
products_collection = db['products'] if db else None
budgets_collection = db['budgets'] if db else None
appointments_collection = db['appointments'] if db else None
stock_collection = db['stock_movements'] if db else None
sales_collection = db['sales'] if db else None
login_attempts_collection = db['login_attempts'] if db else None
sessions_collection = db['sessions'] if db else None
backups_collection = db['backups'] if db else None

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DE EMAIL
# ═══════════════════════════════════════════════════════════════════════════

EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# ═══════════════════════════════════════════════════════════════════════════
# TIMEZONE
# ═══════════════════════════════════════════════════════════════════════════

TIMEZONE = pytz.timezone('America/Sao_Paulo')

# ═══════════════════════════════════════════════════════════════════════════
# DECORADORES DE SEGURANÇA
# ═══════════════════════════════════════════════════════════════════════════

def login_required(f):
    """Decorator para verificar se o usuário está logado"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning(f'🔒 Tentativa de acesso não autorizado: {request.endpoint}')
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        # Verificar expiração da sessão
        if 'last_activity' in session:
            try:
                last_activity = datetime.fromisoformat(session['last_activity'])
                now = datetime.now()
                
                # Se não for "remember me", verificar timeout de 30 minutos
                if not session.get('remember_me', False):
                    if now - last_activity > timedelta(minutes=30):
                        logger.info(f'⏰ Sessão expirada para usuário: {session.get("user_email")}')
                        session.clear()
                        return jsonify({'success': False, 'message': 'Sessão expirada'}), 401
            except Exception as e:
                logger.error(f'❌ Erro ao verificar expiração de sessão: {str(e)}')
        
        # Atualizar última atividade
        session['last_activity'] = datetime.now().isoformat()
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator para verificar se o usuário é administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
        
        if not users_collection:
            return jsonify({'success': False, 'message': 'Banco de dados indisponível'}), 500
        
        user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
        if not user or user.get('role') != 'admin':
            logger.warning(f'🚫 Tentativa de acesso admin negada: {session.get("user_email")}')
            return jsonify({'success': False, 'message': 'Acesso negado - Apenas administradores'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════

def send_email(to_email, subject, body):
    """Envia email usando SMTP"""
    if not EMAIL_USER or not EMAIL_PASSWORD:
        logger.warning('⚠️ Email não configurado')
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, to_email, msg.as_string())
        server.quit()
        
        logger.info(f'📧 Email enviado para {to_email}')
        return True
    except Exception as e:
        logger.error(f'❌ Erro ao enviar email: {str(e)}')
        return False

def check_rate_limit(identifier, max_attempts=5, window_minutes=15):
    """Verifica limite de tentativas de login (Rate Limiting)"""
    if not login_attempts_collection:
        return True
    
    try:
        now = datetime.now()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Contar tentativas no período
        attempts = login_attempts_collection.count_documents({
            'identifier': identifier,
            'timestamp': {'$gte': window_start},
            'success': False
        })
        
        if attempts >= max_attempts:
            logger.warning(f'🚨 Rate limit excedido para {identifier} ({attempts} tentativas)')
            return False
        
        return True
    except Exception as e:
        logger.error(f'❌ Erro ao verificar rate limit: {str(e)}')
        return True  # Em caso de erro, permitir tentativa

def register_login_attempt(identifier, success, user_id=None):
    """Registra tentativa de login para auditoria"""
    if not login_attempts_collection:
        return
    
    try:
        login_attempts_collection.insert_one({
            'identifier': identifier,
            'success': success,
            'user_id': user_id,
            'timestamp': datetime.now(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        })
    except Exception as e:
        logger.error(f'❌ Erro ao registrar tentativa de login: {str(e)}')

def clear_old_login_attempts():
    """Remove tentativas de login antigas (>24h)"""
    if not login_attempts_collection:
        return
    
    try:
        cutoff = datetime.now() - timedelta(hours=24)
        result = login_attempts_collection.delete_many({'timestamp': {'$lt': cutoff}})
        logger.info(f'🧹 Removidas {result.deleted_count} tentativas de login antigas')
    except Exception as e:
        logger.error(f'❌ Erro ao limpar tentativas de login: {str(e)}')

def validate_password_strength(password):
    """Valida força da senha (mínimo 8 caracteres)"""
    if len(password) < 8:
        return False, 'Senha deve ter no mínimo 8 caracteres'
    
    # Verificações opcionais de complexidade
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, 'Senha deve conter letras maiúsculas, minúsculas e números'
    
    return True, 'Senha forte'

def backup_database():
    """Realiza backup completo do banco de dados"""
    if not backups_collection:
        logger.error('❌ Coleção de backups não disponível')
        return False
    
    try:
        logger.info('🔄 Iniciando backup do banco de dados...')
        
        backup_data = {
            'timestamp': datetime.now(),
            'collections': {}
        }
        
        # Backup de cada coleção
        collections_to_backup = [
            ('users', users_collection),
            ('clients', clients_collection),
            ('professionals', professionals_collection),
            ('services', services_collection),
            ('products', products_collection),
            ('budgets', budgets_collection),
            ('appointments', appointments_collection),
            ('stock', stock_collection),
            ('sales', sales_collection)
        ]
        
        for name, collection in collections_to_backup:
            if collection:
                backup_data['collections'][name] = list(collection.find())
        
        # Salvar backup
        backups_collection.insert_one(backup_data)
        
        # Manter apenas os últimos 30 backups
        backups = list(backups_collection.find().sort('timestamp', DESCENDING))
        if len(backups) > 30:
            for old_backup in backups[30:]:
                backups_collection.delete_one({'_id': old_backup['_id']})
            logger.info(f'🧹 Removidos {len(backups) - 30} backups antigos')
        
        logger.info('✅ Backup realizado com sucesso')
        return True
    except Exception as e:
        logger.error(f'❌ Erro ao realizar backup: {str(e)}')
        return False

def clear_all_data():
    """Limpa TODOS os dados do sistema (OPERAÇÃO CRÍTICA)"""
    try:
        logger.warning('⚠️ INICIANDO LIMPEZA TOTAL DE DADOS')
        
        collections_to_clear = [
            ('Clientes', clients_collection),
            ('Profissionais', professionals_collection),
            ('Serviços', services_collection),
            ('Produtos', products_collection),
            ('Orçamentos', budgets_collection),
            ('Agendamentos', appointments_collection),
            ('Vendas', sales_collection),
            ('Estoque', stock_collection)
        ]
        
        total_deleted = 0
        for name, collection in collections_to_clear:
            if collection:
                result = collection.delete_many({})
                total_deleted += result.deleted_count
                logger.info(f'🗑️ {name}: {result.deleted_count} registros removidos')
        
        logger.warning(f'⚠️ LIMPEZA CONCLUÍDA: {total_deleted} registros totais removidos')
        return True, total_deleted
    except Exception as e:
        logger.error(f'❌ Erro ao limpar dados: {str(e)}')
        return False, 0

def generate_modern_pdf(budget_data):
    """Gera PDF moderno e profissional do orçamento"""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=15*mm,
            bottomMargin=20*mm
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # ═══════════════════════════════════════════════════════════════
        # ESTILOS PERSONALIZADOS
        # ═══════════════════════════════════════════════════════════════
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#7C3AED'),
            spaceAfter=5*mm,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#4B5563'),
            spaceAfter=8*mm,
            spaceBefore=6*mm,
            fontName='Helvetica-Bold',
            borderPadding=5,
            backColor=colors.HexColor('#F3F4F6'),
            leftIndent=10,
            rightIndent=10
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#1F2937'),
            spaceAfter=4*mm,
            leading=14
        )
        
        # ═══════════════════════════════════════════════════════════════
        # CABEÇALHO
        # ═══════════════════════════════════════════════════════════════
        
        elements.append(Paragraph("🌳 BIOMA UBERABA", title_style))
        elements.append(Paragraph("Av. Santos Dumont 3110 - Santa Maria - Uberaba/MG", normal_style))
        elements.append(Paragraph("CNPJ: 49.470.937/0001-10 | Tel: (34) 99235-5890", normal_style))
        elements.append(Spacer(1, 8*mm))
        
        # Linha decorativa
        elements.append(Table([['', '']], colWidths=[85*mm, 85*mm], style=TableStyle([
            ('LINEABOVE', (0, 0), (-1, -1), 3, colors.HexColor('#7C3AED')),
        ])))
        elements.append(Spacer(1, 8*mm))
        
        elements.append(Paragraph("ORÇAMENTO DE SERVIÇOS", subtitle_style))
        
        # ═══════════════════════════════════════════════════════════════
        # DADOS DO CLIENTE
        # ═══════════════════════════════════════════════════════════════
        
        elements.append(Paragraph("Dados do Cliente", subtitle_style))
        
        client_data = [
            ['Cliente:', Paragraph(f"<b>{budget_data.get('client_name', 'N/A')}</b>", normal_style)],
            ['Telefone:', budget_data.get('client_phone', 'N/A')],
            ['E-mail:', budget_data.get('client_email', 'N/A')],
            ['Data:', budget_data.get('date', datetime.now().strftime('%d/%m/%Y'))]
        ]
        
        client_table = Table(client_data, colWidths=[35*mm, 135*mm])
        client_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F9FAFB')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1F2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#FAFAFA')])
        ]))
        
        elements.append(client_table)
        elements.append(Spacer(1, 10*mm))
        
        # ═══════════════════════════════════════════════════════════════
        # SERVIÇOS
        # ═══════════════════════════════════════════════════════════════
        
        elements.append(Paragraph("Serviços Contratados", subtitle_style))
        
        services_data = [[
            Paragraph('<b>Serviço</b>', normal_style),
            Paragraph('<b>Profissional</b>', normal_style),
            Paragraph('<b>Valor</b>', normal_style)
        ]]
        
        total = 0
        for service in budget_data.get('services', []):
            services_data.append([
                service.get('name', 'N/A'),
                service.get('professional', 'N/A'),
                f"R$ {service.get('price', 0):.2f}"
            ])
            total += service.get('price', 0)
        
        services_table = Table(services_data, colWidths=[70*mm, 60*mm, 40*mm])
        services_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7C3AED')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
        ]))
        
        elements.append(services_table)
        elements.append(Spacer(1, 8*mm))
        
        # ═══════════════════════════════════════════════════════════════
        # TOTAL
        # ═══════════════════════════════════════════════════════════════
        
        total_data = [['VALOR TOTAL:', f"R$ {total:.2f}"]]
        total_table = Table(total_data, colWidths=[130*mm, 40*mm])
        total_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#10B981')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        elements.append(total_table)
        elements.append(Spacer(1, 10*mm))
        
        # ═══════════════════════════════════════════════════════════════
        # OBSERVAÇÕES
        # ═══════════════════════════════════════════════════════════════
        
        if budget_data.get('notes'):
            elements.append(Paragraph("Observações", subtitle_style))
            elements.append(Paragraph(budget_data.get('notes', ''), normal_style))
            elements.append(Spacer(1, 8*mm))
        
        # ═══════════════════════════════════════════════════════════════
        # RODAPÉ
        # ═══════════════════════════════════════════════════════════════
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6B7280'),
            alignment=TA_CENTER,
            spaceAfter=2*mm
        )
        
        elements.append(Spacer(1, 12*mm))
        elements.append(Paragraph("━" * 80, footer_style))
        elements.append(Paragraph("Orçamento válido por 30 dias a partir da data de emissão", footer_style))
        elements.append(Paragraph("Bioma System v3.9 - Sistema Profissional de Gestão", footer_style))
        elements.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}", footer_style))
        
        # ═══════════════════════════════════════════════════════════════
        # CONSTRUIR PDF
        # ═══════════════════════════════════════════════════════════════
        
        doc.build(elements)
        buffer.seek(0)
        
        logger.info('📄 PDF moderno gerado com sucesso')
        return buffer
    except Exception as e:
        logger.error(f'❌ Erro ao gerar PDF: {str(e)}')
        return None

def criar_usuario_admin():
    """Cria usuário administrador padrão se não existir"""
    if not users_collection:
        logger.error('❌ Coleção de usuários não disponível')
        return False
    
    try:
        # Verificar se já existe admin
        admin_exists = users_collection.find_one({'email': 'admin@bioma.com'})
        
        if not admin_exists:
            hashed_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
            
            admin_user = {
                'name': 'Administrador',
                'email': 'admin@bioma.com',
                'password': hashed_password,
                'role': 'admin',
                'active': True,
                'created_at': datetime.now(),
                'last_login': None
            }
            
            users_collection.insert_one(admin_user)
            logger.info('✅ Usuário administrador criado: admin@bioma.com / admin123')
            return True
        else:
            logger.info('ℹ️ Usuário administrador já existe')
            return True
    except Exception as e:
        logger.error(f'❌ Erro ao criar usuário admin: {str(e)}')
        return False

# ═══════════════════════════════════════════════════════════════════════════
# ROTAS - PÁGINA INICIAL
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    """Página inicial"""
    logger.info(f'📄 Acesso à página inicial - IP: {request.remote_addr}')
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check para monitoramento"""
    status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '3.9.0',
        'database': 'connected' if db else 'disconnected'
    }
    return jsonify(status), 200

# ═══════════════════════════════════════════════════════════════════════════
# ROTAS - AUTENTICAÇÃO
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/register', methods=['POST'])
def register():
    """Registra novo usuário com validação de senha forte"""
    try:
        data = request.json
        
        # Validação de campos obrigatórios
        if not data.get('name') or not data.get('email') or not data.get('password'):
            return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
        
        # Validar força da senha
        is_strong, msg = validate_password_strength(data['password'])
        if not is_strong:
            return jsonify({'success': False, 'message': msg}), 400
        
        # Verificar se email já existe
        if users_collection.find_one({'email': data['email']}):
            return jsonify({'success': False, 'message': 'Email já cadastrado'}), 400
        
        # Hash da senha
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        
        # Criar usuário
        user = {
            'name': data['name'],
            'email': data['email'],
            'password': hashed_password,
            'role': data.get('role', 'user'),
            'active': True,
            'created_at': datetime.now(),
            'last_login': None
        }
        
        result = users_collection.insert_one(user)
        
        # Enviar email de boas-vindas
        if EMAIL_USER:
            send_email(
                data['email'],
                'Bem-vindo ao Bioma System',
                f'''
                <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#f9fafb;border-radius:10px">
                    <h2 style="color:#7C3AED;text-align:center">🌳 Bem-vindo ao BIOMA!</h2>
                    <p>Olá <strong>{data["name"]}</strong>,</p>
                    <p>Sua conta foi criada com sucesso no Bioma System.</p>
                    <p>Email: <strong>{data["email"]}</strong></p>
                    <p style="margin-top:30px;color:#6B7280;font-size:12px;text-align:center">
                        BIOMA Uberaba - Sistema Profissional v3.9
                    </p>
                </div>
                '''
            )
        
        logger.info(f'✅ Novo usuário registrado: {data["email"]}')
        return jsonify({'success': True, 'message': 'Usuário registrado com sucesso'}), 201
        
    except Exception as e:
        logger.error(f'❌ Erro ao registrar usuário: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro ao registrar usuário'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Realiza login com rate limiting e auditoria"""
    try:
        data = request.json
        
        # Validação
        if not data.get('email') or not data.get('password'):
            return jsonify({'success': False, 'message': 'Email e senha são obrigatórios'}), 400
        
        # Verificar rate limit
        if not check_rate_limit(data['email']):
            return jsonify({'success': False, 'message': 'Muitas tentativas. Tente novamente em 15 minutos'}), 429
        
        # Buscar usuário
        user = users_collection.find_one({'email': data['email']})
        
        if not user:
            register_login_attempt(data['email'], False)
            return jsonify({'success': False, 'message': 'Email ou senha incorretos'}), 401
        
        # Verificar se usuário está ativo
        if not user.get('active', True):
            register_login_attempt(data['email'], False, str(user['_id']))
            return jsonify({'success': False, 'message': 'Usuário inativo'}), 401
        
        # Verificar senha
        if not bcrypt.checkpw(data['password'].encode('utf-8'), user['password']):
            register_login_attempt(data['email'], False, str(user['_id']))
            return jsonify({'success': False, 'message': 'Email ou senha incorretos'}), 401
        
        # Login bem-sucedido - Criar sessão
        session.clear()
        session['user_id'] = str(user['_id'])
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        session['user_role'] = user.get('role', 'user')
        session['last_activity'] = datetime.now().isoformat()
        
        # Configurar "Remember me"
        remember_me = data.get('remember_me', False)
        if remember_me:
            session.permanent = True
            app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
            session['remember_me'] = True
        else:
            session.permanent = False
            app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
            session['remember_me'] = False
        
        # Registrar tentativa bem-sucedida e atualizar último login
        register_login_attempt(data['email'], True, str(user['_id']))
        users_collection.update_one(
            {'_id': user['_id']},
            {'$set': {'last_login': datetime.now()}}
        )
        
        logger.info(f'✅ Login bem-sucedido: {data["email"]} (Remember: {remember_me})')
        
        return jsonify({
            'success': True,
            'message': 'Login realizado com sucesso',
            'user': {
                'id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'role': user.get('role', 'user')
            }
        }), 200
        
    except Exception as e:
        logger.error(f'❌ Erro ao realizar login: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro ao realizar login'}), 500

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    """Realiza logout do usuário"""
    try:
        email = session.get('user_email', 'Unknown')
        session.clear()
        logger.info(f'🚪 Logout: {email}')
        return jsonify({'success': True, 'message': 'Logout realizado com sucesso'}), 200
    except Exception as e:
        logger.error(f'❌ Erro ao realizar logout: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro ao realizar logout'}), 500

@app.route('/api/extend-session', methods=['POST'])
@login_required
def extend_session():
    """Estende a sessão do usuário (auto-renovação)"""
    try:
        session['last_activity'] = datetime.now().isoformat()
        return jsonify({'success': True, 'message': 'Sessão estendida'}), 200
    except Exception as e:
        logger.error(f'❌ Erro ao estender sessão: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro ao estender sessão'}), 500

@app.route('/api/check-session', methods=['GET'])
def check_session():
    """Verifica se a sessão está ativa"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'authenticated': False}), 200
        
        # Verificar expiração
        if 'last_activity' in session:
            try:
                last_activity = datetime.fromisoformat(session['last_activity'])
                now = datetime.now()
                
                if not session.get('remember_me', False):
                    if now - last_activity > timedelta(minutes=30):
                        session.clear()
                        return jsonify({'success': False, 'authenticated': False, 'message': 'Sessão expirada'}), 200
            except:
                pass
        
        return jsonify({
            'success': True,
            'authenticated': True,
            'user': {
                'id': session['user_id'],
                'name': session['user_name'],
                'email': session['user_email'],
                'role': session['user_role']
            }
        }), 200
    except Exception as e:
        logger.error(f'❌ Erro ao verificar sessão: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro ao verificar sessão'}), 500

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    """Envia email para recuperação de senha"""
    try:
        data = request.json
        
        if not data.get('email'):
            return jsonify({'success': False, 'message': 'Email é obrigatório'}), 400
        
        user = users_collection.find_one({'email': data['email']})
        
        if not user:
            # Por segurança, não revelar se o email existe
            return jsonify({'success': True, 'message': 'Se o email existir, você receberá instruções'}), 200
        
        # Gerar token de recuperação
        token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(hours=1)
        
        users_collection.update_one(
            {'_id': user['_id']},
            {'$set': {'reset_token': token, 'reset_token_expiry': expiry}}
        )
        
        # Enviar email
        reset_link = f"https://bioma-system2.onrender.com/reset-password?token={token}"
        
        if EMAIL_USER:
            send_email(
                data['email'],
                'Recuperação de Senha - Bioma System',
                f'''
                <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#f9fafb;border-radius:10px">
                    <h2 style="color:#7C3AED">🔐 Recuperação de Senha</h2>
                    <p>Você solicitou a recuperação de senha.</p>
                    <p>Clique no botão abaixo para redefinir:</p>
                    <div style="text-align:center;margin:30px 0">
                        <a href="{reset_link}" style="background:#7C3AED;color:#fff;padding:15px 30px;text-decoration:none;border-radius:8px;display:inline-block">Redefinir Senha</a>
                    </div>
                    <p style="color:#6B7280;font-size:12px">Este link expira em 1 hora.</p>
                    <p style="color:#6B7280;font-size:12px">Se você não solicitou, ignore este email.</p>
                </div>
                '''
            )
        
        logger.info(f'📧 Email de recuperação enviado para: {data["email"]}')
        return jsonify({'success': True, 'message': 'Se o email existir, você receberá instruções'}), 200
        
    except Exception as e:
        logger.error(f'❌ Erro ao processar recuperação de senha: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro ao processar solicitação'}), 500

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    """Redefine a senha do usuário"""
    try:
        data = request.json
        
        if not data.get('token') or not data.get('password'):
            return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
        
        # Validar força da nova senha
        is_strong, msg = validate_password_strength(data['password'])
        if not is_strong:
            return jsonify({'success': False, 'message': msg}), 400
        
        # Buscar usuário pelo token
        user = users_collection.find_one({
            'reset_token': data['token'],
            'reset_token_expiry': {'$gt': datetime.now()}
        })
        
        if not user:
            return jsonify({'success': False, 'message': 'Token inválido ou expirado'}), 400
        
        # Atualizar senha
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        
        users_collection.update_one(
            {'_id': user['_id']},
            {
                '$set': {'password': hashed_password},
                '$unset': {'reset_token': '', 'reset_token_expiry': ''}
            }
        )
        
        logger.info(f'🔑 Senha redefinida para: {user["email"]}')
        return jsonify({'success': True, 'message': 'Senha redefinida com sucesso'}), 200
        
    except Exception as e:
        logger.error(f'❌ Erro ao redefinir senha: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro ao redefinir senha'}), 500

# ═══════════════════════════════════════════════════════════════════════════
# CONTINUA NA PRÓXIMA MENSAGEM...
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# ROTAS - CLIENTES (CRUD COMPLETO)
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# ROTAS - CLIENTES v4.0 COM PAGINAÇÃO E VALIDAÇÃO
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/clients', methods=['GET'])
@login_required
def get_clients():
    """Retorna clientes com paginação e busca"""
    try:
        # Parâmetros de paginação
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        search = request.args.get('search', '')
        
        # Filtro de busca
        query = {}
        if search:
            query = {
                '$or': [
                    {'name': {'$regex': search, '$options': 'i'}},
                    {'phone': {'$regex': search, '$options': 'i'}},
                    {'email': {'$regex': search, '$options': 'i'}},
                    {'cpf': {'$regex': search, '$options': 'i'}}
                ]
            }
        
        # Total de registros
        total = clients_collection.count_documents(query)
        
        # Paginação
        skip = (page - 1) * limit
        clients = list(clients_collection.find(query).skip(skip).limit(limit).sort('name', ASCENDING))
        
        for client in clients:
            client['_id'] = str(client['_id'])
        
        logger.info(f'📋 {len(clients)} clientes recuperados (página {page}/{(total + limit - 1) // limit})')
        
        return jsonify({
            'success': True,
            'clients': clients,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }), 200
    except Exception as e:
        logger.error(f'❌ Erro ao buscar clientes: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro ao buscar clientes'}), 500

@app.route('/api/clients', methods=['POST'])
@login_required
def add_client():
    """Adiciona cliente com validação Pydantic"""
    try:
        # Validar dados com Pydantic
        client_data = ClientSchema(**request.json)
        
        # Verificar duplicidade
        if clients_collection.find_one({'phone': client_data.phone}):
            return jsonify({'success': False, 'message': 'Telefone já cadastrado'}), 400
        
        client = {
            'name': client_data.name,
            'phone': client_data.phone,
            'email': client_data.email,
            'cpf': client_data.cpf,
            'address': client_data.address,
            'birth_date': client_data.birth_date,
            'notes': client_data.notes,
            'created_at': datetime.now(),
            'created_by': session['user_id'],
            'updated_at': datetime.now()
        }
        
        result = clients_collection.insert_one(client)
        client['_id'] = str(result.inserted_id)
        
        logger.info(f'✅ Cliente adicionado: {client_data.name} por {session["user_email"]}')
        return jsonify({'success': True, 'message': 'Cliente adicionado com sucesso', 'client': client}), 201
        
    except Exception as e:
        logger.error(f'❌ Erro ao adicionar cliente: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/clients/<client_id>', methods=['GET'])
@login_required
def get_client(client_id):
    """Retorna dados de um cliente específico"""
    try:
        client = clients_collection.find_one({'_id': ObjectId(client_id)})
        if not client:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
        
        client['_id'] = str(client['_id'])
        return jsonify({'success': True, 'client': client}), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro ao buscar cliente'}), 500

@app.route('/api/clients/<client_id>', methods=['PUT'])
@login_required
def update_client(client_id):
    """Atualiza cliente com validação Pydantic"""
    try:
        # Validar dados
        client_data = ClientSchema(**request.json)
        
        client = clients_collection.find_one({'_id': ObjectId(client_id)})
        if not client:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
        
        # Verificar se telefone já está em uso
        existing = clients_collection.find_one({
            'phone': client_data.phone,
            '_id': {'$ne': ObjectId(client_id)}
        })
        if existing:
            return jsonify({'success': False, 'message': 'Telefone já cadastrado para outro cliente'}), 400
        
        update_data = {
            'name': client_data.name,
            'phone': client_data.phone,
            'email': client_data.email,
            'cpf': client_data.cpf,
            'address': client_data.address,
            'birth_date': client_data.birth_date,
            'notes': client_data.notes,
            'updated_at': datetime.now(),
            'updated_by': session['user_id']
        }
        
        clients_collection.update_one({'_id': ObjectId(client_id)}, {'$set': update_data})
        
        logger.info(f'✏️ Cliente atualizado: {client_id} por {session["user_email"]}')
        return jsonify({'success': True, 'message': 'Cliente atualizado com sucesso'}), 200
        
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 400

# ═══════════════════════════════════════════════════════════════════════════
# ROTAS - PROFISSIONAIS (CRUD COMPLETO)
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/professionals', methods=['GET'])
@login_required
def get_professionals():
    """Retorna todos os profissionais"""
    try:
        professionals = list(professionals_collection.find())
        for prof in professionals:
            prof['_id'] = str(prof['_id'])
        
        return jsonify({'success': True, 'professionals': professionals}), 200
    except Exception as e:
        logger.error(f'❌ Erro ao buscar profissionais: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro ao buscar profissionais'}), 500

@app.route('/api/professionals', methods=['POST'])
@login_required
def add_professional():
    """Adiciona novo profissional"""
    try:
        data = request.json
        
        if not data.get('name') or not data.get('specialty'):
            return jsonify({'success': False, 'message': 'Nome e especialidade são obrigatórios'}), 400
        
        professional = {
            'name': data['name'],
            'specialty': data['specialty'],
            'phone': data.get('phone', ''),
            'email': data.get('email', ''),
            'commission': float(data.get('commission', 0)),
            'active': True,
            'created_at': datetime.now(),
            'created_by': session['user_id']
        }
        
        result = professionals_collection.insert_one(professional)
        professional['_id'] = str(result.inserted_id)
        
        logger.info(f'✅ Profissional adicionado: {data["name"]}')
        return jsonify({'success': True, 'message': 'Profissional adicionado', 'professional': professional}), 201
        
    except Exception as e:
        logger.error(f'❌ Erro ao adicionar profissional: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro ao adicionar profissional'}), 500

@app.route('/api/professionals/<professional_id>', methods=['PUT'])
@login_required
def update_professional(professional_id):
    """Atualiza profissional"""
    try:
        data = request.json
        
        if not data.get('name') or not data.get('specialty'):
            return jsonify({'success': False, 'message': 'Nome e especialidade obrigatórios'}), 400
        
        prof = professionals_collection.find_one({'_id': ObjectId(professional_id)})
        if not prof:
            return jsonify({'success': False, 'message': 'Profissional não encontrado'}), 404
        
        update_data = {
            'name': data['name'],
            'specialty': data['specialty'],
            'phone': data.get('phone', ''),
            'email': data.get('email', ''),
            'commission': float(data.get('commission', 0)),
            'active': data.get('active', True),
            'updated_at': datetime.now(),
            'updated_by': session['user_id']
        }
        
        professionals_collection.update_one({'_id': ObjectId(professional_id)}, {'$set': update_data})
        
        logger.info(f'✏️ Profissional atualizado: {professional_id}')
        return jsonify({'success': True, 'message': 'Profissional atualizado'}), 200
        
    except Exception as e:
        logger.error(f'❌ Erro ao atualizar profissional: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro'}), 500

@app.route('/api/professionals/<professional_id>', methods=['DELETE'])
@login_required
def delete_professional(professional_id):
    """Remove profissional"""
    try:
        result = professionals_collection.delete_one({'_id': ObjectId(professional_id)})
        if result.deleted_count == 0:
            return jsonify({'success': False, 'message': 'Não encontrado'}), 404
        
        logger.info(f'🗑️ Profissional removido: {professional_id}')
        return jsonify({'success': True, 'message': 'Removido'}), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro'}), 500

# ═══════════════════════════════════════════════════════════════════════════
# ROTAS - SERVIÇOS (CRUD COMPLETO)
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/services', methods=['GET'])
@login_required
def get_services():
    """Retorna todos os serviços"""
    try:
        services = list(services_collection.find())
        for service in services:
            service['_id'] = str(service['_id'])
        return jsonify({'success': True, 'services': services}), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro'}), 500

@app.route('/api/services', methods=['POST'])
@login_required
def add_service():
    """Adiciona serviço"""
    try:
        data = request.json
        if not data.get('name') or not data.get('price'):
            return jsonify({'success': False, 'message': 'Nome e preço obrigatórios'}), 400
        
        service = {
            'name': data['name'],
            'description': data.get('description', ''),
            'price': float(data['price']),
            'duration': int(data.get('duration', 60)),
            'category': data.get('category', ''),
            'active': True,
            'created_at': datetime.now(),
            'created_by': session['user_id']
        }
        
        result = services_collection.insert_one(service)
        service['_id'] = str(result.inserted_id)
        
        logger.info(f'✅ Serviço adicionado: {data["name"]}')
        return jsonify({'success': True, 'service': service}), 201
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/services/<service_id>', methods=['PUT'])
@login_required
def update_service(service_id):
    """Atualiza serviço"""
    try:
        data = request.json
        if not data.get('name') or not data.get('price'):
            return jsonify({'success': False, 'message': 'Campos obrigatórios'}), 400
        
        service = services_collection.find_one({'_id': ObjectId(service_id)})
        if not service:
            return jsonify({'success': False, 'message': 'Não encontrado'}), 404
        
        update_data = {
            'name': data['name'],
            'description': data.get('description', ''),
            'price': float(data['price']),
            'duration': int(data.get('duration', 60)),
            'category': data.get('category', ''),
            'active': data.get('active', True),
            'updated_at': datetime.now(),
            'updated_by': session['user_id']
        }
        
        services_collection.update_one({'_id': ObjectId(service_id)}, {'$set': update_data})
        logger.info(f'✏️ Serviço atualizado: {service_id}')
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/services/<service_id>', methods=['DELETE'])
@login_required
def delete_service(service_id):
    """Remove serviço"""
    try:
        result = services_collection.delete_one({'_id': ObjectId(service_id)})
        if result.deleted_count == 0:
            return jsonify({'success': False}), 404
        logger.info(f'🗑️ Serviço removido: {service_id}')
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

# ═══════════════════════════════════════════════════════════════════════════
# ROTAS - PRODUTOS (CRUD COMPLETO)
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/products', methods=['GET'])
@login_required
def get_products():
    """Retorna produtos"""
    try:
        products = list(products_collection.find())
        for product in products:
            product['_id'] = str(product['_id'])
        return jsonify({'success': True, 'products': products}), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/products', methods=['POST'])
@login_required
def add_product():
    """Adiciona produto"""
    try:
        data = request.json
        if not data.get('name') or not data.get('price'):
            return jsonify({'success': False, 'message': 'Nome e preço obrigatórios'}), 400
        
        product = {
            'name': data['name'],
            'description': data.get('description', ''),
            'price': float(data['price']),
            'cost': float(data.get('cost', 0)),
            'stock': int(data.get('stock', 0)),
            'min_stock': int(data.get('min_stock', 5)),
            'category': data.get('category', ''),
            'barcode': data.get('barcode', ''),
            'active': True,
            'created_at': datetime.now(),
            'created_by': session['user_id']
        }
        
        result = products_collection.insert_one(product)
        product['_id'] = str(result.inserted_id)
        
        logger.info(f'✅ Produto adicionado: {data["name"]}')
        return jsonify({'success': True, 'product': product}), 201
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/products/<product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    """Atualiza produto"""
    try:
        data = request.json
        if not data.get('name') or not data.get('price'):
            return jsonify({'success': False}), 400
        
        product = products_collection.find_one({'_id': ObjectId(product_id)})
        if not product:
            return jsonify({'success': False}), 404
        
        update_data = {
            'name': data['name'],
            'description': data.get('description', ''),
            'price': float(data['price']),
            'cost': float(data.get('cost', 0)),
            'stock': int(data.get('stock', 0)),
            'min_stock': int(data.get('min_stock', 5)),
            'category': data.get('category', ''),
            'barcode': data.get('barcode', ''),
            'active': data.get('active', True),
            'updated_at': datetime.now(),
            'updated_by': session['user_id']
        }
        
        products_collection.update_one({'_id': ObjectId(product_id)}, {'$set': update_data})
        logger.info(f'✏️ Produto atualizado: {product_id}')
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/products/<product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    """Remove produto"""
    try:
        result = products_collection.delete_one({'_id': ObjectId(product_id)})
        if result.deleted_count == 0:
            return jsonify({'success': False}), 404
        logger.info(f'🗑️ Produto removido: {product_id}')
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

# ═══════════════════════════════════════════════════════════════════════════
# ROTAS - ORÇAMENTOS (CRUD + PDF)
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/budgets', methods=['GET'])
@login_required
def get_budgets():
    """Retorna orçamentos"""
    try:
        budgets = list(budgets_collection.find().sort('date', DESCENDING))
        for budget in budgets:
            budget['_id'] = str(budget['_id'])
        return jsonify({'success': True, 'budgets': budgets}), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/budgets', methods=['POST'])
@login_required
def add_budget():
    """Adiciona orçamento"""
    try:
        data = request.json
        if not data.get('client_id') or not data.get('services'):
            return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
        
        total = sum(float(s.get('price', 0)) for s in data['services'])
        discount = float(data.get('discount', 0))
        final_total = total - discount
        
        budget = {
            'client_id': data['client_id'],
            'client_name': data.get('client_name', ''),
            'client_phone': data.get('client_phone', ''),
            'client_email': data.get('client_email', ''),
            'services': data['services'],
            'products': data.get('products', []),
            'total': total,
            'discount': discount,
            'final_total': final_total,
            'notes': data.get('notes', ''),
            'status': 'pending',
            'date': datetime.now(),
            'created_by': session['user_id']
        }
        
        result = budgets_collection.insert_one(budget)
        budget['_id'] = str(result.inserted_id)
        
        logger.info(f'✅ Orçamento criado: {budget["_id"]}')
        return jsonify({'success': True, 'budget': budget}), 201
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/budgets/<budget_id>', methods=['PUT'])
@login_required
def update_budget(budget_id):
    """Atualiza orçamento com recálculo automático"""
    try:
        data = request.json
        if not data.get('client_id') or not data.get('services'):
            return jsonify({'success': False}), 400
        
        budget = budgets_collection.find_one({'_id': ObjectId(budget_id)})
        if not budget:
            return jsonify({'success': False}), 404
        
        # Recalcular total
        total = sum(float(s.get('price', 0)) for s in data['services'])
        discount = float(data.get('discount', 0))
        final_total = total - discount
        
        update_data = {
            'client_id': data['client_id'],
            'client_name': data.get('client_name', ''),
            'client_phone': data.get('client_phone', ''),
            'client_email': data.get('client_email', ''),
            'services': data['services'],
            'products': data.get('products', []),
            'total': total,
            'discount': discount,
            'final_total': final_total,
            'notes': data.get('notes', ''),
            'status': data.get('status', 'pending'),
            'updated_at': datetime.now(),
            'updated_by': session['user_id']
        }
        
        budgets_collection.update_one({'_id': ObjectId(budget_id)}, {'$set': update_data})
        logger.info(f'✏️ Orçamento atualizado: {budget_id}')
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/budgets/<budget_id>', methods=['DELETE'])
@login_required
def delete_budget(budget_id):
    """Remove orçamento"""
    try:
        result = budgets_collection.delete_one({'_id': ObjectId(budget_id)})
        if result.deleted_count == 0:
            return jsonify({'success': False}), 404
        logger.info(f'🗑️ Orçamento removido: {budget_id}')
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/budgets/<budget_id>/pdf', methods=['GET'])
@login_required
def generate_budget_pdf(budget_id):
    """Gera PDF moderno do orçamento"""
    try:
        budget = budgets_collection.find_one({'_id': ObjectId(budget_id)})
        if not budget:
            return jsonify({'success': False, 'message': 'Orçamento não encontrado'}), 404
        
        pdf_data = {
            'client_name': budget.get('client_name', 'N/A'),
            'client_phone': budget.get('client_phone', 'N/A'),
            'client_email': budget.get('client_email', 'N/A'),
            'date': budget.get('date', datetime.now()).strftime('%d/%m/%Y'),
            'services': budget.get('services', []),
            'notes': budget.get('notes', '')
        }
        
        pdf_buffer = generate_modern_pdf(pdf_data)
        if not pdf_buffer:
            return jsonify({'success': False, 'message': 'Erro ao gerar PDF'}), 500
        
        logger.info(f'📄 PDF gerado: {budget_id}')
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'orcamento_bioma_{budget_id}.pdf'
        )
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

# ═══════════════════════════════════════════════════════════════════════════
# ROTAS - AGENDAMENTOS
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/appointments', methods=['GET'])
@login_required
def get_appointments():
    """Retorna agendamentos"""
    try:
        appointments = list(appointments_collection.find().sort('date', ASCENDING))
        for appt in appointments:
            appt['_id'] = str(appt['_id'])
        return jsonify({'success': True, 'appointments': appointments}), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/appointments', methods=['POST'])
@login_required
def add_appointment():
    """Adiciona agendamento"""
    try:
        data = request.json
        if not all([data.get('client_id'), data.get('professional_id'), data.get('service_id'), data.get('date'), data.get('time')]):
            return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
        
        appointment = {
            'client_id': data['client_id'],
            'client_name': data.get('client_name', ''),
            'professional_id': data['professional_id'],
            'professional_name': data.get('professional_name', ''),
            'service_id': data['service_id'],
            'service_name': data.get('service_name', ''),
            'date': data['date'],
            'time': data['time'],
            'duration': int(data.get('duration', 60)),
            'status': 'scheduled',
            'notes': data.get('notes', ''),
            'created_at': datetime.now(),
            'created_by': session['user_id']
        }
        
        result = appointments_collection.insert_one(appointment)
        appointment['_id'] = str(result.inserted_id)
        
        logger.info(f'✅ Agendamento criado: {appointment["_id"]}')
        return jsonify({'success': True, 'appointment': appointment}), 201
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/appointments/<appointment_id>', methods=['PUT'])
@login_required
def update_appointment(appointment_id):
    """Atualiza agendamento"""
    try:
        data = request.json
        appointment = appointments_collection.find_one({'_id': ObjectId(appointment_id)})
        if not appointment:
            return jsonify({'success': False}), 404
        
        update_data = {
            'client_id': data.get('client_id', appointment['client_id']),
            'client_name': data.get('client_name', appointment.get('client_name', '')),
            'professional_id': data.get('professional_id', appointment['professional_id']),
            'professional_name': data.get('professional_name', appointment.get('professional_name', '')),
            'service_id': data.get('service_id', appointment['service_id']),
            'service_name': data.get('service_name', appointment.get('service_name', '')),
            'date': data.get('date', appointment['date']),
            'time': data.get('time', appointment['time']),
            'duration': int(data.get('duration', appointment.get('duration', 60))),
            'status': data.get('status', appointment.get('status', 'scheduled')),
            'notes': data.get('notes', appointment.get('notes', '')),
            'updated_at': datetime.now(),
            'updated_by': session['user_id']
        }
        
        appointments_collection.update_one({'_id': ObjectId(appointment_id)}, {'$set': update_data})
        logger.info(f'✏️ Agendamento atualizado: {appointment_id}')
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/appointments/<appointment_id>', methods=['DELETE'])
@login_required
def delete_appointment(appointment_id):
    """Remove agendamento"""
    try:
        result = appointments_collection.delete_one({'_id': ObjectId(appointment_id)})
        if result.deleted_count == 0:
            return jsonify({'success': False}), 404
        logger.info(f'🗑️ Agendamento removido: {appointment_id}')
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

# ═══════════════════════════════════════════════════════════════════════════
# ROTAS - VENDAS
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/sales', methods=['GET'])
@login_required
def get_sales():
    """Retorna vendas"""
    try:
        sales = list(sales_collection.find().sort('date', DESCENDING))
        for sale in sales:
            sale['_id'] = str(sale['_id'])
        return jsonify({'success': True, 'sales': sales}), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/sales', methods=['POST'])
@login_required
def add_sale():
    """Adiciona venda e atualiza estoque automaticamente"""
    try:
        data = request.json
        if not data.get('items'):
            return jsonify({'success': False, 'message': 'Itens obrigatórios'}), 400
        
        total = sum(float(item.get('price', 0)) * int(item.get('quantity', 1)) for item in data['items'])
        discount = float(data.get('discount', 0))
        final_total = total - discount
        
        sale = {
            'client_id': data.get('client_id', ''),
            'client_name': data.get('client_name', ''),
            'items': data['items'],
            'total': total,
            'discount': discount,
            'final_total': final_total,
            'payment_method': data.get('payment_method', 'cash'),
            'status': 'completed',
            'date': datetime.now(),
            'created_by': session['user_id']
        }
        
        result = sales_collection.insert_one(sale)
        sale['_id'] = str(result.inserted_id)
        
        # Atualizar estoque automaticamente
        for item in data['items']:
            if item.get('type') == 'product' and item.get('id'):
                products_collection.update_one(
                    {'_id': ObjectId(item['id'])},
                    {'$inc': {'stock': -int(item.get('quantity', 1))}}
                )
                
                # Registrar movimentação
                stock_collection.insert_one({
                    'product_id': item['id'],
                    'type': 'out',
                    'quantity': int(item.get('quantity', 1)),
                    'reason': f'Venda #{sale["_id"]}',
                    'date': datetime.now(),
                    'created_by': session['user_id']
                })
        
        logger.info(f'✅ Venda criada: {sale["_id"]}')
        return jsonify({'success': True, 'sale': sale}), 201
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

# ═══════════════════════════════════════════════════════════════════════════
# ROTAS - DASHBOARD E RELATÓRIOS
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/dashboard/stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    """Retorna estatísticas do dashboard em tempo real"""
    try:
        total_clients = clients_collection.count_documents({})
        total_professionals = professionals_collection.count_documents({})
        total_services = services_collection.count_documents({})
        total_products = products_collection.count_documents({})
        total_budgets = budgets_collection.count_documents({})
        
        # Vendas do mês
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_sales = list(sales_collection.find({'date': {'$gte': start_of_month}}))
        monthly_revenue = sum(sale.get('final_total', 0) for sale in monthly_sales)
        
        # Agendamentos de hoje
        today = datetime.now().strftime('%Y-%m-%d')
        today_appointments = appointments_collection.count_documents({'date': today})
        
        # Produtos com estoque baixo
        low_stock_products = list(products_collection.find({'$expr': {'$lte': ['$stock', '$min_stock']}}))
        
        stats = {
            'total_clients': total_clients,
            'total_professionals': total_professionals,
            'total_services': total_services,
            'total_products': total_products,
            'total_budgets': total_budgets,
            'monthly_revenue': monthly_revenue,
            'monthly_sales_count': len(monthly_sales),
            'today_appointments': today_appointments,
            'low_stock_count': len(low_stock_products),
            'low_stock_products': [{'_id': str(p['_id']), 'name': p['name'], 'stock': p.get('stock', 0), 'min_stock': p.get('min_stock', 0)} for p in low_stock_products[:5]]
        }
        
        return jsonify({'success': True, 'stats': stats}), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500
    
# ═══════════════════════════════════════════════════════════════════════════
# ROTAS - RELATÓRIOS AVANÇADOS v4.0
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/reports/monthly-revenue', methods=['GET'])
@login_required
def get_monthly_revenue():
    """Retorna faturamento mensal com pipeline de agregação"""
    try:
        year = int(request.args.get('year', datetime.now().year))
        
        pipeline = [
            {
                '$match': {
                    'date': {
                        '$gte': datetime(year, 1, 1),
                        '$lt': datetime(year + 1, 1, 1)
                    },
                    'status': 'completed'
                }
            },
            {
                '$group': {
                    '_id': {'$month': '$date'},
                    'total': {'$sum': '$final_total'},
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {'_id': 1}
            }
        ]
        
        result = list(sales_collection.aggregate(pipeline))
        
        # Formatar dados para o gráfico
        months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        data = [0] * 12
        
        for item in result:
            month_index = item['_id'] - 1
            data[month_index] = item['total']
        
        logger.info(f'📊 Relatório de faturamento mensal gerado para {year}')
        
        return jsonify({
            'success': True,
            'year': year,
            'labels': months,
            'data': data
        }), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro ao gerar relatório'}), 500

@app.route('/api/reports/top-services', methods=['GET'])
@login_required
def get_top_services():
    """Retorna top serviços mais realizados"""
    try:
        limit = int(request.args.get('limit', 5))
        
        pipeline = [
            {'$unwind': '$services'},
            {
                '$group': {
                    '_id': '$services.name',
                    'total': {'$sum': '$services.price'},
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'total': -1}},
            {'$limit': limit}
        ]
        
        result = list(budgets_collection.aggregate(pipeline))
        
        return jsonify({
            'success': True,
            'services': result
        }), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/reports/top-products', methods=['GET'])
@login_required
def get_top_products():
    """Retorna produtos mais vendidos"""
    try:
        limit = int(request.args.get('limit', 10))
        
        pipeline = [
            {'$unwind': '$items'},
            {'$match': {'items.type': 'product'}},
            {
                '$group': {
                    '_id': '$items.name',
                    'quantity': {'$sum': '$items.quantity'},
                    'revenue': {'$sum': {'$multiply': ['$items.price', '$items.quantity']}}
                }
            },
            {'$sort': {'quantity': -1}},
            {'$limit': limit}
        ]
        
        result = list(sales_collection.aggregate(pipeline))
        
        return jsonify({
            'success': True,
            'products': result
        }), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/reports/professional-performance', methods=['GET'])
@login_required
def get_professional_performance():
    """Retorna desempenho por profissional"""
    try:
        pipeline = [
            {
                '$group': {
                    '_id': '$professional_id',
                    'professional_name': {'$first': '$professional_name'},
                    'total_appointments': {'$sum': 1},
                    'completed': {
                        '$sum': {'$cond': [{'$eq': ['$status', 'completed']}, 1, 0]}
                    }
                }
            },
            {'$sort': {'total_appointments': -1}}
        ]
        
        result = list(appointments_collection.aggregate(pipeline))
        
        return jsonify({
            'success': True,
            'professionals': result
        }), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

# ═══════════════════════════════════════════════════════════════════════════
# ROTAS - ESTOQUE
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/stock/alerts', methods=['GET'])
@login_required
def get_stock_alerts():
    """Retorna alertas de estoque baixo"""
    try:
        low_stock = list(products_collection.find({'$expr': {'$lte': ['$stock', '$min_stock']}, 'active': True}))
        for product in low_stock:
            product['_id'] = str(product['_id'])
        return jsonify({'success': True, 'alerts': low_stock}), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/stock/movement', methods=['POST'])
@login_required
def add_stock_movement():
    """Adiciona movimentação de estoque"""
    try:
        data = request.json
        if not all([data.get('product_id'), data.get('quantity'), data.get('type')]):
            return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
        
        product = products_collection.find_one({'_id': ObjectId(data['product_id'])})
        if not product:
            return jsonify({'success': False, 'message': 'Produto não encontrado'}), 404
        
        quantity = int(data['quantity'])
        movement_type = data['type']  # 'in' ou 'out'
        
        if movement_type == 'in':
            new_stock = product['stock'] + quantity
        else:
            new_stock = product['stock'] - quantity
            if new_stock < 0:
                return jsonify({'success': False, 'message': 'Estoque insuficiente'}), 400
        
        products_collection.update_one({'_id': ObjectId(data['product_id'])}, {'$set': {'stock': new_stock}})
        
        movement = {
            'product_id': data['product_id'],
            'product_name': product['name'],
            'type': movement_type,
            'quantity': quantity,
            'previous_stock': product['stock'],
            'new_stock': new_stock,
            'reason': data.get('reason', ''),
            'date': datetime.now(),
            'created_by': session['user_id']
        }
        
        stock_collection.insert_one(movement)
        logger.info(f'📦 Movimentação de estoque: {data["product_id"]}')
        return jsonify({'success': True}), 201
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500


# ═══════════════════════════════════════════════════════════════════════════
# ROTAS - EXPORTAÇÃO EXCEL v4.0
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/export/clients', methods=['GET'])
@login_required
def export_clients():
    """Exporta clientes para Excel"""
    try:
        clients = list(clients_collection.find())
        
        # Criar workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Clientes"
        
        # Estilo do cabeçalho
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="7C3AED", end_color="7C3AED", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Cabeçalhos
        headers = ['Nome', 'Telefone', 'E-mail', 'CPF', 'Endereço', 'Data Cadastro']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        # Dados
        for row, client in enumerate(clients, start=2):
            ws.cell(row=row, column=1, value=client.get('name', ''))
            ws.cell(row=row, column=2, value=client.get('phone', ''))
            ws.cell(row=row, column=3, value=client.get('email', ''))
            ws.cell(row=row, column=4, value=client.get('cpf', ''))
            ws.cell(row=row, column=5, value=client.get('address', ''))
            ws.cell(row=row, column=6, value=client.get('created_at', datetime.now()).strftime('%d/%m/%Y'))
        
        # Ajustar largura das colunas
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column].width = adjusted_width
        
        # Salvar em buffer
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        logger.info(f'📊 Exportação de clientes realizada por {session["user_email"]}')
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'clientes_bioma_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/export/sales', methods=['GET'])
@login_required
def export_sales():
    """Exporta vendas para Excel"""
    try:
        sales = list(sales_collection.find().sort('date', DESCENDING))
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Vendas"
        
        # Cabeçalho
        headers = ['Data', 'Cliente', 'Total', 'Desconto', 'Total Final', 'Pagamento', 'Status']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="7C3AED", end_color="7C3AED", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
        
        # Dados
        for row, sale in enumerate(sales, start=2):
            ws.cell(row=row, column=1, value=sale.get('date', datetime.now()).strftime('%d/%m/%Y %H:%M'))
            ws.cell(row=row, column=2, value=sale.get('client_name', ''))
            ws.cell(row=row, column=3, value=sale.get('total', 0))
            ws.cell(row=row, column=4, value=sale.get('discount', 0))
            ws.cell(row=row, column=5, value=sale.get('final_total', 0))
            ws.cell(row=row, column=6, value=sale.get('payment_method', ''))
            ws.cell(row=row, column=7, value=sale.get('status', ''))
        
        # Ajustar colunas
        for col in ws.columns:
            max_length = max(len(str(cell.value)) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = max_length + 2
        
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        logger.info(f'📊 Exportação de vendas realizada')
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'vendas_bioma_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500
    
# ═══════════════════════════════════════════════════════════════════════════
# ROTAS - ADMINISTRATIVAS
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/admin/backup', methods=['POST'])
@admin_required
def manual_backup():
    """Realiza backup manual do banco de dados"""
    try:
        success = backup_database()
        if success:
            logger.info(f'💾 Backup manual realizado por {session["user_email"]}')
            return jsonify({'success': True, 'message': 'Backup realizado com sucesso'}), 200
        else:
            return jsonify({'success': False, 'message': 'Erro ao realizar backup'}), 500
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro ao realizar backup'}), 500

@app.route('/api/admin/clear-data', methods=['POST'])
@admin_required
def clear_data():
    """LIMPA TODOS OS DADOS DO SISTEMA (OPERAÇÃO CRÍTICA)"""
    try:
        logger.warning(f'⚠️ LIMPEZA TOTAL solicitada por {session["user_email"]}')
        success, total_deleted = clear_all_data()
        
        if success:
            logger.warning(f'🗑️ LIMPEZA CONCLUÍDA: {total_deleted} registros removidos por {session["user_email"]}')
            return jsonify({
                'success': True,
                'message': f'Limpeza concluída. {total_deleted} registros removidos.',
                'total_deleted': total_deleted
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Erro ao limpar dados'}), 500
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False, 'message': 'Erro ao limpar dados'}), 500

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def get_users():
    """Retorna todos os usuários (sem senha)"""
    try:
        users = list(users_collection.find({}, {'password': 0}))
        for user in users:
            user['_id'] = str(user['_id'])
        return jsonify({'success': True, 'users': users}), 200
    except Exception as e:
        logger.error(f'❌ Erro: {str(e)}')
        return jsonify({'success': False}), 500

# ═══════════════════════════════════════════════════════════════════════════
# SCHEDULER - TAREFAS AUTOMÁTICAS
# ═══════════════════════════════════════════════════════════════════════════

def init_scheduler():
    """Inicializa scheduler para tarefas automáticas"""
    scheduler = BackgroundScheduler(timezone=TIMEZONE)
    
    # Backup diário às 3h
    scheduler.add_job(func=backup_database, trigger='cron', hour=3, minute=0, id='daily_backup')
    
    # Limpar tentativas de login antigas a cada 6h
    scheduler.add_job(func=clear_old_login_attempts, trigger='interval', hours=6, id='clear_login_attempts')
    
    scheduler.start()
    logger.info('⏰ Scheduler iniciado com sucesso')

# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZAÇÃO
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    logger.info('═══════════════════════════════════════════════════════════════')
    logger.info('🌳 BIOMA UBERABA v3.9 - INICIANDO SISTEMA')
    logger.info('═══════════════════════════════════════════════════════════════')
    
    # Inicializar scheduler
    init_scheduler()
    
    # Criar usuário admin padrão
    criar_usuario_admin()
    
    # Criar índices no MongoDB
    if db:
        try:
            users_collection.create_index('email', unique=True)
            clients_collection.create_index('phone')
            appointments_collection.create_index([('date', ASCENDING), ('time', ASCENDING)])
            sales_collection.create_index('date')
            logger.info('📑 Índices do MongoDB criados com sucesso')
        except Exception as e:
            logger.warning(f'⚠️ Erro ao criar índices: {str(e)}')
    
    # Informações de inicialização
    logger.info(f'📧 Email configurado: {"✅ SIM" if EMAIL_USER else "❌ NÃO"}')
    logger.info(f'💾 MongoDB: {"✅ CONECTADO" if db else "❌ DESCONECTADO"}')
    logger.info('═══════════════════════════════════════════════════════════════')
    logger.info('✅ Sistema pronto para receber requisições')
    logger.info('═══════════════════════════════════════════════════════════════')
    
    # Iniciar aplicação
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)