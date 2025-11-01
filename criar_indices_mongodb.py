#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v7.2 - Script de Criacao de Indices MongoDB
Otimiza performance do banco de dados adicionando indices estrategicos
"""

import os
import sys
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from dotenv import load_dotenv

# Configurar encoding para UTF-8 no Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

# Carregar variaveis de ambiente
load_dotenv()

def criar_indices():
    """Cria todos os indices necessarios para otimizacao de performance"""

    # Conectar ao MongoDB
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        print("[ERRO] MONGO_URI nao encontrada no .env")
        return False

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client.get_database()
        print(f"[OK] Conectado ao MongoDB: {db.name}")
        print()

    except Exception as e:
        print(f"[ERRO] Erro ao conectar ao MongoDB: {e}")
        return False

    indices_criados = 0
    indices_existentes = 0

    print("=" * 80)
    print("CRIANDO INDICES DE PERFORMANCE v7.2")
    print("=" * 80)
    print()

    # ========== ORCAMENTOS (MAIS CRITICO) ==========
    print("[*] Collection: orcamentos")
    print("-" * 40)

    try:
        # Status (usado em quase todas as queries)
        result = db.orcamentos.create_index([('status', ASCENDING)], name='idx_status')
        if result == 'idx_status':
            indices_criados += 1
            print("  [OK] Criado: status (ASCENDING)")
        else:
            indices_existentes += 1
            print(f"  [!] Ja existe: {result}")
    except Exception as e:
        print(f"  [ERRO] {e}")

    try:
        # CPF do cliente (usado para buscar orçamentos por cliente)
        result = db.orcamentos.create_index([('cliente_cpf', ASCENDING)], name='idx_cliente_cpf')
        if result == 'idx_cliente_cpf':
            indices_criados += 1
            print("  [OK] Criado: cliente_cpf (ASCENDING)")
        else:
            indices_existentes += 1
            print(f"  [!] Ja existe: {result}")
    except Exception as e:
        print(f"  [ERRO] {e}")

    try:
        # Data de criação (usado para ordenação e filtros temporais)
        result = db.orcamentos.create_index([('created_at', DESCENDING)], name='idx_created_at_desc')
        if result == 'idx_created_at_desc':
            indices_criados += 1
            print("  [OK] Criado: created_at (DESCENDING)")
        else:
            indices_existentes += 1
            print(f"  [!] Ja existe: {result}")
    except Exception as e:
        print(f"  [ERRO] {e}")

    try:
        # Compound index: status + created_at (queries comuns)
        result = db.orcamentos.create_index(
            [('status', ASCENDING), ('created_at', DESCENDING)],
            name='idx_status_created_at'
        )
        if result == 'idx_status_created_at':
            indices_criados += 1
            print("  [OK] Criado: status + created_at (COMPOUND)")
        else:
            indices_existentes += 1
            print(f"  [!] Ja existe: {result}")
    except Exception as e:
        print(f"  [ERRO] {e}")

    print()

    # ========== PRODUTOS ==========
    print("[*] Collection: produtos")
    print("-" * 40)

    try:
        result = db.produtos.create_index([('status', ASCENDING)], name='idx_status')
        if result == 'idx_status':
            indices_criados += 1
            print("  [OK] Criado: status (ASCENDING)")
        else:
            indices_existentes += 1
            print(f"  [!] Ja existe: {result}")
    except Exception as e:
        print(f"  [ERRO] {e}")

    try:
        result = db.produtos.create_index([('estoque', ASCENDING)], name='idx_estoque')
        if result == 'idx_estoque':
            indices_criados += 1
            print("  [OK] Criado: estoque (ASCENDING)")
        else:
            indices_existentes += 1
            print(f"  [!] Ja existe: {result}")
    except Exception as e:
        print(f"  [ERRO] {e}")

    try:
        result = db.produtos.create_index([('nome', TEXT)], name='idx_nome_text')
        if result == 'idx_nome_text':
            indices_criados += 1
            print("  [OK] Criado: nome (TEXT SEARCH)")
        else:
            indices_existentes += 1
            print(f"  [!] Ja existe: {result}")
    except Exception as e:
        print(f"  [ERRO] {e}")

    print()

    # ========== CLIENTES ==========
    print("[*] Collection: clientes")
    print("-" * 40)

    try:
        # CPF único (já deve existir, mas garantir)
        result = db.clientes.create_index([('cpf', ASCENDING)], unique=True, name='idx_cpf_unique')
        if result == 'idx_cpf_unique':
            indices_criados += 1
            print("  [OK] Criado: cpf (UNIQUE)")
        else:
            indices_existentes += 1
            print(f"  [!] Ja existe: {result}")
    except Exception as e:
        print(f"  [ERRO] {e}")

    try:
        result = db.clientes.create_index([('nome', TEXT)], name='idx_nome_text')
        if result == 'idx_nome_text':
            indices_criados += 1
            print("  [OK] Criado: nome (TEXT SEARCH)")
        else:
            indices_existentes += 1
            print(f"  [!] Ja existe: {result}")
    except Exception as e:
        print(f"  [ERRO] {e}")

    print()

    # ========== PROFISSIONAIS ==========
    print("[*] Collection: profissionais")
    print("-" * 40)

    try:
        result = db.profissionais.create_index([('ativo', ASCENDING)], name='idx_ativo')
        if result == 'idx_ativo':
            indices_criados += 1
            print("  [OK] Criado: ativo (ASCENDING)")
        else:
            indices_existentes += 1
            print(f"  [!] Ja existe: {result}")
    except Exception as e:
        print(f"  [ERRO] {e}")

    try:
        # REMOVER índice antigo de CPF se existir (pode não ser único)
        try:
            db.profissionais.drop_index('cpf_1')
            print("  [DEL] Removido: cpf_1 (índice antigo)")
        except:
            pass

        # Criar novo índice de CPF com sparse=True
        result = db.profissionais.create_index(
            [('cpf', ASCENDING)],
            sparse=True,
            name='idx_cpf_sparse'
        )
        if result == 'idx_cpf_sparse':
            indices_criados += 1
            print("  [OK] Criado: cpf (SPARSE - permite nulls)")
        else:
            indices_existentes += 1
            print(f"  [!] Ja existe: {result}")
    except Exception as e:
        print(f"  [ERRO] {e}")

    print()

    # ========== SERVIÇOS ==========
    print("[*] Collection: servicos")
    print("-" * 40)

    try:
        result = db.servicos.create_index([('categoria', ASCENDING)], name='idx_categoria')
        if result == 'idx_categoria':
            indices_criados += 1
            print("  [OK] Criado: categoria (ASCENDING)")
        else:
            indices_existentes += 1
            print(f"  [!] Ja existe: {result}")
    except Exception as e:
        print(f"  [ERRO] {e}")

    try:
        result = db.servicos.create_index([('nome', TEXT)], name='idx_nome_text')
        if result == 'idx_nome_text':
            indices_criados += 1
            print("  [OK] Criado: nome (TEXT SEARCH)")
        else:
            indices_existentes += 1
            print(f"  [!] Ja existe: {result}")
    except Exception as e:
        print(f"  [ERRO] {e}")

    print()
    print("=" * 80)
    print("RESUMO DA OTIMIZACAO")
    print("=" * 80)
    print(f"[OK] Indices criados: {indices_criados}")
    print(f"[!] Indices ja existentes: {indices_existentes}")
    print(f"[*] Total processado: {indices_criados + indices_existentes}")
    print()

    if indices_criados > 0:
        print("[PERFORMANCE] MELHORADA!")
        print("   Queries agora devem ser 10x-100x mais rapidas")
        print()

    # Listar todos os indices criados
    print("[LISTA] INDICES ATIVOS POR COLLECTION:")
    print("-" * 80)
    for collection_name in ['orcamentos', 'produtos', 'clientes', 'profissionais', 'servicos']:
        collection = db[collection_name]
        indices = collection.list_indexes()
        print(f"\n{collection_name}:")
        for idx in indices:
            nome = idx.get('name', 'unknown')
            keys = idx.get('key', {})
            unique = ' (UNIQUE)' if idx.get('unique', False) else ''
            sparse = ' (SPARSE)' if idx.get('sparse', False) else ''
            print(f"  - {nome}: {dict(keys)}{unique}{sparse}")

    print()
    print("=" * 80)
    print("[OK] OTIMIZACAO CONCLUIDA!")
    print("=" * 80)

    return True

if __name__ == '__main__':
    criar_indices()
