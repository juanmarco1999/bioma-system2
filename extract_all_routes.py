#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para extrair TODAS as rotas do app.py e criar um blueprint consolidado
"""

import re
from pathlib import Path


def extract_all_routes_content(app_py_path):
    """Extrai TODO o conteúdo de rotas do app.py"""
    with open(app_py_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Encontrar a primeira rota
    first_route = re.search(r'@app\.route\(', content)
    if not first_route:
        print("[ERROR] Nenhuma rota encontrada")
        return ""

    # Extrair desde a primeira rota até o final do arquivo (ou até if __name__)
    start_idx = first_route.start()

    # Procurar por if __name__ == '__main__'
    main_check = re.search(r'if __name__ == [\'"]__main__[\'"]:', content[start_idx:])
    if main_check:
        end_idx = start_idx + main_check.start()
    else:
        end_idx = len(content)

    routes_content = content[start_idx:end_idx]

    # Substituir @app.route por @bp.route
    routes_content = routes_content.replace('@app.route', '@bp.route')

    # Substituir referências diretas a 'db' por 'get_db_connection()'
    # mas manter como está por enquanto para compatibilidade

    return routes_content


def create_consolidated_blueprint():
    """Criar um blueprint consolidado com TODAS as rotas"""
    app_py = Path('app.py')

    if not app_py.exists():
        print("[ERROR] app.py nao encontrado")
        return False

    print("[INFO] Extraindo rotas do app.py...")
    routes_content = extract_all_routes_content(app_py)

    if not routes_content:
        return False

    # Criar blueprint api com todas as rotas
    api_dir = Path('app/api')
    api_dir.mkdir(parents=True, exist_ok=True)

    # Criar __init__.py
    init_content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
BIOMA v3.7 - API Blueprint (Consolidado)
Todas as rotas do sistema
\"\"\"

from flask import Blueprint

bp = Blueprint('api', __name__)

from app.api import routes
"""

    with open(api_dir / '__init__.py', 'w', encoding='utf-8') as f:
        f.write(init_content)

    # Criar routes.py com TODAS as rotas
    routes_header = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
BIOMA v3.7 - Todas as Rotas (Consolidado)
Migrado automaticamente do app.py monolítico
\"\"\"

from flask import request, jsonify, session, current_app, send_file, render_template
from flask_cors import CORS
from pymongo import MongoClient, ASCENDING, DESCENDING
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson import ObjectId
from functools import wraps, lru_cache
from datetime import datetime, timedelta
from dotenv import load_dotenv
import urllib.parse
import os
import io
from io import BytesIO
import csv
import json
import re
import requests
import logging
import random
from time import time

# ReportLab para PDFs
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import cm

# OpenPyXL para Excel
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

from app.api import bp
from app.decorators import login_required, permission_required, get_user_permissions
from app.utils import convert_objectid, allowed_file, registrar_auditoria, update_cliente_denormalized_fields, get_assistente_details
from app.constants import ANAMNESE_FORM, PRONTUARIO_FORM, default_form_state
from app.extensions import get_from_cache, set_in_cache

logger = logging.getLogger(__name__)

# Helper para obter DB do current_app
def get_db():
    return current_app.config.get('DB_CONNECTION')

# Alias para compatibilidade com código existente
db = None  # Será definido em cada função usando get_db()


"""

    with open(api_dir / 'routes.py', 'w', encoding='utf-8') as f:
        f.write(routes_header)
        f.write('\n\n')
        f.write(routes_content)

    print(f"[OK] Blueprint consolidado criado em app/api/")
    print(f"[INFO] Total de linhas de rotas: {len(routes_content.splitlines())}")
    return True


if __name__ == '__main__':
    if create_consolidated_blueprint():
        print("\n[OK] Migracao concluida!")
        print("[INFO] Atualize app/__init__.py para registrar o blueprint 'api'")
    else:
        print("\n[ERROR] Migracao falhou!")
