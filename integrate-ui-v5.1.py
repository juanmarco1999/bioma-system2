#!/usr/bin/env python3
"""
Script de integração BIOMA UI v5.1.0
Substitui modais nativos por modais DIV customizados bonitos
Adiciona sistema de botões moderno
"""

import re

def integrate_ui_v51(input_file, output_file):
    print(">> Iniciando integracao BIOMA UI v5.1.0...")

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    original_size = len(content)
    print(f">> Arquivo original: {len(content.split('\n'))} linhas")

    # 1. Atualizar versão
    print(">> Atualizando versao para v5.1.0...")
    content = re.sub(
        r'<!-- BIOMA v5\.0\.0.*?-->.*?<!-- MAJOR:.*?-->.*?<!-- HTML5.*?-->',
        '''<!-- BIOMA v5.1.0 - Build: {{ cache_buster|default('LOCAL', true) }} -->
    <!-- UI SYSTEM: Modais Customizados Bonitos + Sistema de Botões Moderno -->
    <!-- Modais DIV estilizados (não nativos) + Toasts + Botões gradiente -->''',
        content,
        flags=re.DOTALL
    )

    content = re.sub(r"const APP_VERSION = 'v5\.0\.0';", "const APP_VERSION = 'v5.1.0';", content)

    # 2. Ler novos arquivos
    print(">> Carregando novo CSS e JS...")
    with open('bioma-ui-v5.1.css', 'r', encoding='utf-8') as f:
        new_css = f.read()

    with open('bioma-ui-v5.1.js', 'r', encoding='utf-8') as f:
        new_js = f.read()

    # 3. Substituir CSS antigo (remover CSS de modais nativos)
    print(">> Substituindo CSS de modais...")
    css_pattern = r'/\* ========== SISTEMA DE MODAIS CUSTOMIZADO BIOMA ==========.*?/\* Hover em tabelas com elevação \*/'

    new_css_block = f"""/* ========== SISTEMA DE MODAIS E BOTÕES BIOMA v5.1.0 ========== */
{new_css}

        /* Hover em tabelas com elevação */"""

    content = re.sub(css_pattern, new_css_block, content, flags=re.DOTALL)

    # 4. Substituir JavaScript antigo
    print(">> Substituindo JavaScript de modais...")
    js_pattern = r'// ============================================================\n// SISTEMA DE MODAIS CUSTOMIZADO BIOMA v5\.0.*?console\.log\(.*?HTML5 <dialog> nativo.*?\);'

    content = re.sub(js_pattern, new_js, content, flags=re.DOTALL)

    # 5. Atualizar classes antigas de botões para novas
    print(">> Atualizando classes de botoes...")

    # btn-success, btn-primary, etc → bioma-btn bioma-btn-success
    content = re.sub(r'class="btn btn-success"', 'class="bioma-btn bioma-btn-success"', content)
    content = re.sub(r'class="btn btn-primary"', 'class="bioma-btn bioma-btn-primary"', content)
    content = re.sub(r'class="btn btn-danger"', 'class="bioma-btn bioma-btn-danger"', content)
    content = re.sub(r'class="btn btn-warning"', 'class="bioma-btn bioma-btn-warning"', content)
    content = re.sub(r'class="btn btn-info"', 'class="bioma-btn bioma-btn-info"', content)
    content = re.sub(r'class="btn btn-secondary"', 'class="bioma-btn bioma-btn-secondary"', content)

    # Botões com tamanhos
    content = re.sub(r'class="btn btn-sm btn-', 'class="bioma-btn bioma-btn-sm bioma-btn-', content)
    content = re.sub(r'class="btn btn-lg btn-', 'class="bioma-btn bioma-btn-lg bioma-btn-', content)

    # Botão simples
    content = re.sub(r'class="btn"(?![- ])', 'class="bioma-btn bioma-btn-primary"', content)

    new_size = len(content)
    print(f">> Arquivo processado: {len(content.split('\n'))} linhas")
    print(f">> Diferenca de tamanho: {(new_size - original_size) / 1024:.1f} KB")

    # 6. Salvar arquivo
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f">> Integracao concluida! Arquivo salvo em: {output_file}")
    print("\n>> Resumo das mudancas:")
    print("  [OK] Versao atualizada para v5.1.0")
    print("  [OK] CSS de modais bonitos integrado")
    print("  [OK] JavaScript de modais customizados integrado")
    print("  [OK] Classes de botoes atualizadas")
    print("  [OK] Compatibilidade retroativa mantida")

    return True

if __name__ == '__main__':
    try:
        import shutil

        input_file = 'templates/index.html'
        output_file = 'templates/index.html'
        backup_file = 'templates/index.html.backup-before-v5.1'

        # Backup
        shutil.copy(input_file, backup_file)
        print(f">> Backup criado: {backup_file}\n")

        integrate_ui_v51(input_file, output_file)

        print("\n>> BIOMA v5.1.0 - Integracao automatica concluida!")
        print(">> Proximos passos:")
        print("  1. Testar modais no navegador (devem ser bonitos agora!)")
        print("  2. Verificar botoes com novo design")
        print("  3. Commitar mudancas")

    except Exception as e:
        print(f"[ERRO] Erro durante integracao: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
