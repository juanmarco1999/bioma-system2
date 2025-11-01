#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para deletar todos os serviços e produtos do banco BIOMA
"""

import os
import sys
from pymongo import MongoClient
import urllib.parse
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def conectar_mongodb():
    """Conectar ao MongoDB"""
    try:
        username = urllib.parse.quote_plus(os.getenv('MONGO_USERNAME'))
        password = urllib.parse.quote_plus(os.getenv('MONGO_PASSWORD'))
        cluster = os.getenv('MONGO_CLUSTER')

        if not all([username, password, cluster]):
            print("[ERRO] Credenciais do MongoDB nao encontradas no .env")
            return None

        uri = f"mongodb+srv://{username}:{password}@{cluster}/bioma_db?retryWrites=true&w=majority&appName=Juan-Analytics-DBServer"

        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client.bioma_db

        print("[OK] Conectado ao MongoDB")
        return db

    except Exception as e:
        print(f"[ERRO] Erro ao conectar: {e}")
        return None

def deletar_servicos(db):
    """Deletar todos os serviços"""
    try:
        count_antes = db.servicos.count_documents({})
        print(f"\n[INFO] Servicos encontrados: {count_antes}")

        if count_antes == 0:
            print("[OK] Nenhum servico para deletar")
            return

        confirmacao = input(f"[ATENCAO] Deseja DELETAR {count_antes} servicos? (digite 'SIM' para confirmar): ")

        if confirmacao.upper() != 'SIM':
            print("[CANCELADO] Operacao cancelada")
            return

        resultado = db.servicos.delete_many({})
        print(f"[OK] {resultado.deleted_count} servicos deletados")

    except Exception as e:
        print(f"[ERRO] Erro ao deletar servicos: {e}")

def deletar_produtos(db):
    """Deletar todos os produtos"""
    try:
        count_antes = db.produtos.count_documents({})
        print(f"\n[INFO] Produtos encontrados: {count_antes}")

        if count_antes == 0:
            print("[OK] Nenhum produto para deletar")
            return

        confirmacao = input(f"[ATENCAO] Deseja DELETAR {count_antes} produtos? (digite 'SIM' para confirmar): ")

        if confirmacao.upper() != 'SIM':
            print("[CANCELADO] Operacao cancelada")
            return

        resultado = db.produtos.delete_many({})
        print(f"[OK] {resultado.deleted_count} produtos deletados")

    except Exception as e:
        print(f"[ERRO] Erro ao deletar produtos: {e}")

def main():
    print("=" * 60)
    print("BIOMA - Limpeza de Servicos e Produtos")
    print("=" * 60)

    db = conectar_mongodb()
    if db is None:
        sys.exit(1)

    print("\nOpcoes:")
    print("1 - Deletar todos os SERVICOS")
    print("2 - Deletar todos os PRODUTOS")
    print("3 - Deletar AMBOS (Servicos + Produtos)")
    print("0 - Sair")

    opcao = input("\nEscolha uma opcao: ")

    if opcao == '1':
        deletar_servicos(db)
    elif opcao == '2':
        deletar_produtos(db)
    elif opcao == '3':
        deletar_servicos(db)
        deletar_produtos(db)
    elif opcao == '0':
        print("[SAIR] Saindo...")
    else:
        print("[ERRO] Opcao invalida")

    print("\n[OK] Script finalizado")

if __name__ == "__main__":
    main()
