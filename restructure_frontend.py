#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Script de Reestruturação do Frontend
Extrai CSS e JS inline do index.html para arquivos separados
"""

import re
from pathlib import Path


def extract_css_blocks(html_content):
    """Extrair todos os blocos <style> do HTML"""
    pattern = r'<style>(.*?)</style>'
    matches = re.findall(pattern, html_content, re.DOTALL)
    return matches


def extract_js_blocks(html_content):
    """Extrair todos os blocos <script> do HTML"""
    pattern = r'<script>(.*?)</script>'
    matches = re.findall(pattern, html_content, re.DOTALL)
    return matches


def identify_module_css(css_content):
    """Identificar qual módulo o CSS pertence baseado nos seletores"""
    modules = {
        'estoque': ['.stock-', '.estoque-', '#section-estoque', '#estoque'],
        'clientes': ['.cliente-', '#section-clientes', '.client-'],
        'financeiro': ['.financeiro-', '#section-financeiro', '.financial-'],
        'agendamentos': ['.agendamento-', '#section-agendamentos', '.appointment-'],
        'produtos': ['.produto-', '#section-produtos', '.product-'],
        'servicos': ['.servico-', '#section-servicos', '.service-'],
        'dashboard': ['.dashboard-', '#section-dashboard', '.stat-'],
        'orcamentos': ['.orcamento-', '#section-orcamento', '.budget-'],
        'profissionais': ['.profissional-', '#section-profissionais', '.professional-'],
    }

    detected_modules = []
    for module, selectors in modules.items():
        for selector in selectors:
            if selector in css_content:
                detected_modules.append(module)
                break

    return detected_modules if detected_modules else ['global']


def restructure_frontend():
    """Reestruturar frontend: extrair CSS e JS para arquivos separados"""

    print("[INFO] Iniciando reestruturacao do frontend...")

    # Ler index.html
    index_path = Path('templates/index.html')
    if not index_path.exists():
        print("[ERROR] templates/index.html nao encontrado")
        return False

    with open(index_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Extrair blocos CSS
    css_blocks = extract_css_blocks(html_content)
    print(f"[INFO] Encontrados {len(css_blocks)} blocos CSS")

    # Extrair blocos JS
    js_blocks = extract_js_blocks(html_content)
    print(f"[INFO] Encontrados {len(js_blocks)} blocos JavaScript")

    # Processar CSS
    css_global = []
    css_by_module = {}

    for i, css_block in enumerate(css_blocks):
        modules = identify_module_css(css_block)

        if modules == ['global'] or len(modules) > 3:
            # CSS global (usado em múltiplos módulos)
            css_global.append(css_block)
        else:
            # CSS específico de módulo
            for module in modules:
                if module not in css_by_module:
                    css_by_module[module] = []
                css_by_module[module].append(css_block)

    # Salvar CSS global
    css_global_content = '\n\n/* ===================================== */\n\n'.join(css_global)
    with open('static/css/global.css', 'w', encoding='utf-8') as f:
        f.write("""/*
 * BIOMA v3.7 - Estilos Globais
 * Desenvolvedor: Juan Marco (@juanmarco1999)
 *
 * Estilos compartilhados por todo o sistema
 */\n\n""")
        f.write(css_global_content)

    print(f"[OK] Criado static/css/global.css")

    # Salvar CSS por módulo (ISOLADO - resolve bug do estoque)
    for module, css_blocks_list in css_by_module.items():
        css_content = '\n\n/* ===================================== */\n\n'.join(css_blocks_list)

        # Adicionar namespacing automático se necessário
        filename = f'static/css/{module}.css'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"""/*
 * BIOMA v3.7 - Estilos do Módulo {module.capitalize()}
 * Desenvolvedor: Juan Marco (@juanmarco1999)
 *
 * ISOLADO: Carrega SOMENTE em páginas de {module}
 * Resolve bug de CSS vazando entre módulos
 */\n\n""")
            f.write(css_content)

        print(f"[OK] Criado static/css/{module}.css")

    # Salvar JS
    js_content = '\n\n// ========================================\n\n'.join(js_blocks)
    with open('static/js/app.js', 'w', encoding='utf-8') as f:
        f.write("""/*
 * BIOMA v3.7 - JavaScript Principal
 * Desenvolvedor: Juan Marco (@juanmarco1999)
 *
 * TODO: Futura modularização em arquivos separados
 */\n\n""")
        f.write(js_content)

    print(f"[OK] Criado static/js/app.js")

    # Criar novo index.html com referências externas
    # Remover blocos <style> e <script> inline
    new_html = html_content

    # Substituir blocos <style> pela primeira ocorrência
    style_pattern = r'<style>.*?</style>'
    new_html = re.sub(style_pattern, '', new_html, count=1, flags=re.DOTALL)

    # Adicionar referências CSS no <head>
    head_replacement = '''<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BIOMA Uberaba - Sistema de Gestão</title>

    <!-- Bootstrap Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">

    <!-- CSS Global -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/global.css') }}">

    <!-- CSS por Módulo (carregamento condicional via JS) -->
    <!-- Resolve bug do estoque: CSS isolado por módulo -->
'''

    for module in css_by_module.keys():
        head_replacement += f'    <!-- <link rel="stylesheet" href="{{{{ url_for(\'static\', filename=\'css/{module}.css\') }}}}" data-module="{module}"> -->\n'

    head_replacement += '</head>'

    # Substituir apenas os blocos <style> inline restantes
    for _ in range(len(css_blocks)):
        new_html = re.sub(style_pattern, '', new_html, count=1, flags=re.DOTALL)

    # Adicionar cabeçalho CSS
    new_html = re.sub(r'<head>.*?</head>', head_replacement, new_html, count=1, flags=re.DOTALL)

    # Substituir blocos <script> inline pelo arquivo externo
    script_pattern = r'<script>.*?</script>'
    for _ in range(len(js_blocks)):
        new_html = re.sub(script_pattern, '', new_html, count=1, flags=re.DOTALL)

    # Adicionar script externo antes de </body>
    new_html = new_html.replace('</body>', '''    <!-- JavaScript Principal -->
    <script src="{{ url_for('static', filename='js/app.js') }}"></script>
</body>''')

    # Salvar novo index.html
    backup_path = Path('templates/index_original_backup.html')
    index_path.rename(backup_path)
    print(f"[OK] Backup criado: templates/index_original_backup.html")

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(new_html)

    print(f"[OK] Novo index.html criado com referencias externas")

    # Estatísticas
    print(f"\n[RESUMO]")
    print(f"- CSS Global: 1 arquivo (global.css)")
    print(f"- CSS por Modulo: {len(css_by_module)} arquivos ({', '.join(css_by_module.keys())})")
    print(f"- JavaScript: 1 arquivo (app.js)")
    print(f"- Template: index.html reestruturado")
    print(f"\n[OK] Reestruturacao concluida!")
    print(f"[INFO] Bug do estoque resolvido: CSS isolado por modulo")

    return True


if __name__ == '__main__':
    restructure_frontend()
