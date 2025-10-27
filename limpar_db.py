#!/usr/bin/env python3
"""
Script de Limpeza do Banco de Dados BIOMA v4.0
Remove dados de teste e prepara para produção
"""

from pymongo import MongoClient
from datetime import datetime
import os

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')

def limpar_banco():
    print("🧹 Iniciando limpeza do banco de dados BIOMA v4.0...")

    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client.bioma

        # Testar conexão
        client.admin.command('ping')
        print("✅ Conectado ao MongoDB")

        # Coleções para limpar (mantém estrutura, remove dados)
        colecoes_limpar = [
            'orcamentos',
            'clientes',
            'profissionais',
            'servicos',
            'produtos',
            'agendamentos',
            'fila',
            'comissoes',
            'estoque_movimentos',
            'despesas',
            'auditoria'
        ]

        # Coleções para manter (configurações)
        colecoes_manter = [
            'users',  # Usuários (admin)
            'configuracoes'  # Configurações do sistema
        ]

        stats = {}

        for colecao in colecoes_limpar:
            if colecao in db.list_collection_names():
                count_antes = db[colecao].count_documents({})
                resultado = db[colecao].delete_many({})
                stats[colecao] = {
                    'antes': count_antes,
                    'removidos': resultado.deleted_count
                }
                print(f"   📦 {colecao}: {resultado.deleted_count} documentos removidos")
            else:
                print(f"   ⏭️ {colecao}: coleção não existe")

        # Criar índices para performance
        print("\n⚡ Criando índices para performance...")

        db.clientes.create_index([("nome", 1)])
        db.clientes.create_index([("cpf", 1)], unique=True, sparse=True)
        db.orcamentos.create_index([("numero", 1)])
        db.orcamentos.create_index([("created_at", -1)])
        db.agendamentos.create_index([("data_hora", 1)])
        db.profissionais.create_index([("nome", 1)])

        print("✅ Índices criados")

        # Estatísticas finais
        print("\n📊 RESUMO DA LIMPEZA:")
        print(f"{'Coleção':<25} {'Docs Removidos':>15}")
        print("-" * 42)
        total_removidos = 0
        for col, stat in stats.items():
            print(f"{col:<25} {stat['removidos']:>15,}")
            total_removidos += stat['removidos']
        print("-" * 42)
        print(f"{'TOTAL':<25} {total_removidos:>15,}")

        # Verificar integridade
        print("\n🔍 Verificando integridade...")
        for col in colecoes_manter:
            if col in db.list_collection_names():
                count = db[col].count_documents({})
                print(f"   ✅ {col}: {count} documentos mantidos")

        # Criar usuário admin padrão se não existir
        if 'users' in db.list_collection_names():
            admin_exists = db.users.find_one({"username": "admin"})
            if not admin_exists:
                from werkzeug.security import generate_password_hash
                db.users.insert_one({
                    "username": "admin",
                    "password": generate_password_hash("admin123"),
                    "name": "Administrador",
                    "role": "admin",
                    "created_at": datetime.now()
                })
                print("   ➕ Usuário admin criado")

        print("\n✅ Limpeza concluída com sucesso!")
        print("💡 Banco de dados pronto para produção")

        client.close()
        return True

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return False

if __name__ == "__main__":
    limpar_banco()
