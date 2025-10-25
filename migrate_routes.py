#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Script de Migração Automática de Rotas
Extrai rotas do app.py monolítico e distribui nos Blueprints
"""

import re
import os
from pathlib import Path

# Mapeamento de rotas para blueprints
ROUTE_MAPPING = {
    # Auth (já criado)
    r'/api/login': 'auth',
    r'/api/logout': 'auth',
    r'/api/register': 'auth',
    r'/api/current-user': 'auth',
    r'/api/permissions': 'auth',
    r'/api/update-theme': 'auth',

    # Dashboard (criar)
    r'/api/dashboard/': 'dashboard',

    # Clientes
    r'/api/clientes/': 'clientes',
    r'/api/clientes$': 'clientes',

    # Profissionais
    r'/api/profissionais/': 'profissionais',
    r'/api/profissionais$': 'profissionais',
    r'/api/comissao/': 'profissionais',
    r'/api/comissoes/': 'profissionais',

    # Assistentes
    r'/api/assistentes': 'assistentes',

    # Agendamentos
    r'/api/agendamentos': 'agendamentos',

    # Fila
    r'/api/fila': 'fila',

    # Produtos
    r'/api/produtos': 'produtos',

    # Serviços
    r'/api/servicos': 'servicos',

    # Estoque
    r'/api/estoque': 'estoque',

    # Orçamentos
    r'/api/orcamentos': 'orcamentos',
    r'/api/orcamento/': 'orcamentos',

    # Contratos
    r'/api/contratos': 'contratos',

    # Financeiro
    r'/api/financeiro': 'financeiro',

    # Relatórios
    r'/api/relatorios': 'relatorios',

    # Sistema (catch-all para rotas administrativas)
    r'/api/users': 'sistema',
    r'/api/config': 'sistema',
    r'/api/upload': 'sistema',
    r'/api/system': 'sistema',
    r'/api/auditoria': 'sistema',
    r'/api/importar': 'sistema',
    r'/api/template': 'sistema',
    r'/api/busca': 'sistema',
    r'/api/notificacoes': 'sistema',
    r'/api/admin': 'sistema',
    r'/api/stream': 'sistema',
    r'/uploads/': 'sistema',
}


def detect_blueprint(route_path):
    """Detecta qual blueprint deve receber a rota"""
    for pattern, blueprint in ROUTE_MAPPING.items():
        if re.search(pattern, route_path):
            return blueprint
    return 'sistema'  # Default


def extract_route_function(lines, start_idx):
    """Extrai função completa de uma rota"""
    function_lines = []
    indent_level = None
    in_function = False

    for i in range(start_idx, len(lines)):
        line = lines[i]

        # Capturar @app.route
        if line.strip().startswith('@app.route'):
            function_lines.append(line)
            continue

        # Capturar outros decorators (@login_required, @permission_required)
        if line.strip().startswith('@') and not in_function:
            function_lines.append(line)
            continue

        # Início da função
        if line.strip().startswith('def ') and not in_function:
            in_function = True
            indent_level = len(line) - len(line.lstrip())
            function_lines.append(line)
            continue

        # Dentro da função
        if in_function:
            current_indent = len(line) - len(line.lstrip())

            # Fim da função (nova função ou decorator)
            if line.strip() and current_indent <= indent_level:
                if line.strip().startswith(('def ', '@', 'class ')):
                    break

            function_lines.append(line)

    return function_lines


def main():
    """Migrar rotas do app.py para blueprints"""
    print("[INFO] Iniciando migracao de rotas...")

    app_path = Path('app.py')
    if not app_path.exists():
        print("[ERROR] app.py nao encontrado")
        return

    # Ler app.py
    with open(app_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Detectar rotas
    routes_by_blueprint = {}
    i = 0

    while i < len(lines):
        line = lines[i]

        # Encontrar @app.route
        if '@app.route' in line:
            # Extrair path da rota
            match = re.search(r"@app\.route\(['\"](.+?)['\"]", line)
            if match:
                route_path = match.group(1)
                blueprint = detect_blueprint(route_path)

                # Extrair função completa
                function_lines = extract_route_function(lines, i)

                if blueprint not in routes_by_blueprint:
                    routes_by_blueprint[blueprint] = []

                routes_by_blueprint[blueprint].append({
                    'route': route_path,
                    'lines': function_lines
                })

                print(f"   {route_path} -> {blueprint}")

                # Pular para próxima rota
                i += len(function_lines)
                continue

        i += 1

    # Escrever arquivos de rotas
    print(f"\n[INFO] Criando arquivos de rotas...")

    for blueprint, routes in routes_by_blueprint.items():
        # Pular blueprints já criados manualmente
        if blueprint in ['main', 'auth']:
            print(f"   [SKIP] {blueprint} (ja criado manualmente)")
            continue

        blueprint_dir = Path(f'app/{blueprint}')
        blueprint_dir.mkdir(parents=True, exist_ok=True)

        routes_file = blueprint_dir / 'routes.py'

        # Cabeçalho
        header = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
BIOMA v3.7 - {blueprint.capitalize()} Routes
Auto-gerado pelo script de migração
\"\"\"

from flask import request, jsonify, session, current_app, send_file, render_template
from bson import ObjectId
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import logging
import io
import csv
import json

from app.{blueprint} import bp
from app.decorators import login_required, permission_required, get_user_permissions
from app.utils import convert_objectid, allowed_file, registrar_auditoria
from app.extensions import db as get_db, get_from_cache, set_in_cache

logger = logging.getLogger(__name__)

"""

        # Converter rotas
        route_functions = []
        for route_info in routes:
            # Converter @app.route para @bp.route
            converted_lines = []
            for line in route_info['lines']:
                # Substituir @app.route por @bp.route
                if '@app.route' in line:
                    line = line.replace('@app.route', '@bp.route')

                converted_lines.append(line)

            route_functions.append(''.join(converted_lines))

        # Escrever arquivo
        with open(routes_file, 'w', encoding='utf-8') as f:
            f.write(header)
            f.write('\n\n'.join(route_functions))

        print(f"   [OK] {blueprint}/routes.py ({len(routes)} rotas)")

    print(f"\n[OK] Migracao concluida!")
    print(f"[INFO] Total: {len(routes_by_blueprint)} blueprints")


if __name__ == '__main__':
    main()
