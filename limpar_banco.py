#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para limpar o banco de dados BIOMA mantendo índices e estrutura.

Este script:
- Remove todos os documentos das coleções (exceto users e auditoria)
- Mantém os índices e estrutura das coleções
- Registra auditoria da operação
- Requer confirmação com código LIMPAR2025

Uso:
    python limpar_banco.py

ATENÇÃO: Esta operação é IRREVERSÍVEL! Use com extrema cautela.
"""

import os
import sys
from datetime import datetime
from pymongo import MongoClient
from getpass import getpass

# Configurações do MongoDB
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
DB_NAME = os.environ.get('DB_NAME', 'bioma')

# Código de segurança
CODIGO_SEGURANCA = 'LIMPAR2025'

# Coleções que serão limpas (mantém users e auditoria)
COLECOES_LIMPAR = [
    'clientes',
    'profissionais',
    'servicos',
    'produtos',
    'orcamentos',
    'contratos',
    'agendamentos',
    'estoque_movimentacoes',
    'comissoes',
    'despesas',
    'assistentes',
    'fila',
    'prontuarios'
]


def conectar_banco():
    """Conecta ao banco de dados MongoDB."""
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Testa a conexão
        client.admin.command('ping')
        db = client[DB_NAME]
        print(f"✅ Conectado ao MongoDB: {DB_NAME}")
        return db, client
    except Exception as e:
        print(f"❌ Erro ao conectar ao MongoDB: {e}")
        sys.exit(1)


def verificar_indices(db):
    """Lista os índices de todas as coleções antes da limpeza."""
    print("\n📋 Índices atuais nas coleções:")
    print("=" * 60)
    indices_salvos = {}

    for colecao_nome in COLECOES_LIMPAR:
        try:
            colecao = db[colecao_nome]
            indices = list(colecao.list_indexes())
            indices_salvos[colecao_nome] = indices
            print(f"\n📂 {colecao_nome}:")
            for idx in indices:
                print(f"   - {idx['name']}: {idx.get('key', {})}")
        except Exception as e:
            print(f"   ⚠️ Erro ao listar índices: {e}")

    return indices_salvos


def limpar_banco(db):
    """Limpa os dados do banco mantendo índices e estrutura."""
    print("\n🗑️  Iniciando limpeza do banco de dados...")
    print("=" * 60)

    estatisticas = {}
    total_deletados = 0

    for colecao_nome in COLECOES_LIMPAR:
        try:
            colecao = db[colecao_nome]

            # Contar documentos antes
            count_antes = colecao.count_documents({})

            if count_antes == 0:
                print(f"⚪ {colecao_nome}: já está vazia")
                estatisticas[colecao_nome] = {'antes': 0, 'deletados': 0}
                continue

            # Deletar todos os documentos (mantém coleção e índices)
            resultado = colecao.delete_many({})
            deletados = resultado.deleted_count
            total_deletados += deletados

            # Contar documentos depois (deve ser 0)
            count_depois = colecao.count_documents({})

            print(f"✅ {colecao_nome}: {deletados} documentos deletados ({count_antes} → {count_depois})")

            estatisticas[colecao_nome] = {
                'antes': count_antes,
                'deletados': deletados,
                'depois': count_depois
            }

        except Exception as e:
            print(f"❌ Erro ao limpar {colecao_nome}: {e}")
            estatisticas[colecao_nome] = {'erro': str(e)}

    return estatisticas, total_deletados


def registrar_auditoria(db, usuario='Script'):
    """Registra a operação de limpeza na auditoria."""
    try:
        db.auditoria.insert_one({
            'username': usuario,
            'acao': 'LIMPAR_BANCO_DADOS',
            'entidade': 'SISTEMA',
            'timestamp': datetime.now(),
            'detalhes': 'Limpeza completa via script Python (mantendo índices)',
            'codigo_usado': CODIGO_SEGURANCA
        })
        print("✅ Auditoria registrada")
    except Exception as e:
        print(f"⚠️ Erro ao registrar auditoria: {e}")


def main():
    """Função principal do script."""
    print("=" * 60)
    print("🧹 SCRIPT DE LIMPEZA DO BANCO DE DADOS BIOMA v6.0")
    print("=" * 60)
    print("\n⚠️  ATENÇÃO: Esta operação irá DELETAR TODOS OS DADOS!")
    print("⚠️  Os índices e estrutura das coleções serão MANTIDOS")
    print("⚠️  As coleções 'users' e 'auditoria' NÃO serão afetadas\n")

    # Solicitar confirmação 1
    resposta = input("Você tem certeza que deseja continuar? (sim/não): ").strip().lower()
    if resposta not in ['sim', 's', 'yes', 'y']:
        print("❌ Operação cancelada pelo usuário")
        sys.exit(0)

    # Solicitar código de segurança
    print(f"\n🔐 Para confirmar, digite o código de segurança: {CODIGO_SEGURANCA}")
    codigo = input("Código: ").strip()

    if codigo != CODIGO_SEGURANCA:
        print("❌ Código inválido! Operação cancelada.")
        sys.exit(1)

    # Conectar ao banco
    db, client = conectar_banco()

    # Verificar índices antes da limpeza
    print("\n🔍 Verificando índices atuais...")
    indices_antes = verificar_indices(db)

    # Solicitar confirmação final
    print("\n⚠️  ÚLTIMA CONFIRMAÇÃO")
    resposta_final = input("Digite 'CONFIRMO' para prosseguir com a limpeza: ").strip()
    if resposta_final != 'CONFIRMO':
        print("❌ Operação cancelada")
        client.close()
        sys.exit(0)

    # Registrar auditoria ANTES da limpeza
    registrar_auditoria(db)

    # Executar limpeza
    estatisticas, total = limpar_banco(db)

    # Verificar índices após limpeza
    print("\n🔍 Verificando índices após limpeza...")
    indices_depois = verificar_indices(db)

    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DA OPERAÇÃO")
    print("=" * 60)
    print(f"✅ Total de documentos deletados: {total}")
    print(f"✅ Coleções processadas: {len(estatisticas)}")
    print(f"✅ Índices mantidos: {'SIM' if indices_antes == indices_depois else 'VERIFICAR'}")
    print("\n💾 Detalhes:")
    for colecao, stats in estatisticas.items():
        if 'erro' in stats:
            print(f"   ❌ {colecao}: {stats['erro']}")
        else:
            print(f"   ✅ {colecao}: {stats['deletados']} docs deletados")

    print("\n✅ Limpeza concluída com sucesso!")
    print("=" * 60)

    # Fechar conexão
    client.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)
