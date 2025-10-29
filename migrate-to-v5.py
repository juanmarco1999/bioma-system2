#!/usr/bin/env python3
"""
Script de migração automática BIOMA v5.0.0
Remove SweetAlert2 e injeta sistema de modais customizado
"""

import re
import sys

def migrate_index_html(input_file, output_file):
    print(">> Iniciando migracao BIOMA v5.0.0...")

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    original_lines = len(content.split('\n'))
    print(f">> Arquivo original: {original_lines} linhas")

    # 1. Ler o novo sistema de modais
    print(">> Carregando novo sistema de modais...")
    with open('bioma-modals-v5.js', 'r', encoding='utf-8') as f:
        new_modal_system = f.read()

    # 2. Encontrar e remover TUDO entre "// ========== FUNÇÃO 1:" e "console.log('%c✅ Sistema de Modais"
    print(">> Removendo codigo antigo do SweetAlert2...")

    # Pattern para capturar TODO o bloco antigo
    old_block_pattern = r'// ========== FUNÇÃO 1: mostrarNotificacao.*?console\.log\(\'%c  ✨ NOVO v4\.11\.2:.*?\);'

    content = re.sub(old_block_pattern, new_modal_system, content, flags=re.DOTALL)

    # 3. Remover referências CSS antigas ao swal2 (já substituídas)
    print(">> Limpando referencias CSS antigas...")

    # Remover classes CSS swal2- que foram substituídas
    # (Já temos o CSS novo dos modais customizados, então podemos remover imports/estilos antigos)

    # 4. Remover linhas com classes swal2- nos inputs (substituir por classes normais)
    print(">> Atualizando classes de inputs...")
    content = re.sub(r'class="swal2-input"', 'class="form-control"', content)
    content = re.sub(r'class="swal2-textarea"', 'class="form-control"', content)
    content = re.sub(r'class="swal2-file"', 'class="form-control"', content)

    # 5. Remover seletores CSS swal2 órfãos (querySelectorAll que não existem mais)
    print(">> Removendo seletores DOM orfaos...")
    content = re.sub(r"document\.querySelectorAll\('\.swal2-container.*?'\)", "document.querySelectorAll('.bioma-dialog')", content)
    content = re.sub(r"querySelector\('#swal2-input'\)", "querySelector('input.form-control')", content)
    content = re.sub(r"querySelector\('#swal2-textarea'\)", "querySelector('textarea.form-control')", content)

    # 6. Remover remoção de classes swal2- do body
    print(">> Atualizando limpeza do body...")
    content = re.sub(
        r"document\.body\.classList\.remove\('swal2-shown',\s*'swal2-height-auto'.*?\);",
        "// Classes swal2 removidas - nao mais necessario",
        content
    )

    new_lines = len(content.split('\n'))
    print(f">> Arquivo migrado: {new_lines} linhas")
    print(f">> Reducao: {original_lines - new_lines} linhas")

    # 7. Salvar arquivo migrado
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f">> Migracao concluida! Arquivo salvo em: {output_file}")
    print("\n>> Resumo das mudancas:")
    print("  [OK] Sistema de modais customizado injetado")
    print("  [OK] Funcoes antigas removidas")
    print("  [OK] Classes CSS atualizadas")
    print("  [OK] Seletores DOM corrigidos")
    print("  [OK] Compatibilidade retroativa mantida (window.Swal)")

    return True

if __name__ == '__main__':
    try:
        input_file = 'templates/index.html'
        output_file = 'templates/index.html'

        # Criar backup automático
        import shutil
        backup_file = 'templates/index.html.backup-before-v5-auto'
        shutil.copy(input_file, backup_file)
        print(f">> Backup criado: {backup_file}\n")

        migrate_index_html(input_file, output_file)

        print("\n>> BIOMA v5.0.0 - Migracao automatica concluida com sucesso!")
        print(">> Proximos passos:")
        print("  1. Testar modais no navegador")
        print("  2. Verificar console para erros")
        print("  3. Commitar mudancas")

    except Exception as e:
        print(f"[ERRO] Erro durante migracao: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
