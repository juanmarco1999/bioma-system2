#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OTIMIZAÇÃO DO BANCO DE DADOS - BIOMA v5.1.0
Cria índices e otimiza consultas
"""

import os
import sys
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv
import logging
import urllib.parse

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

def conectar_banco():
    """Conecta ao MongoDB"""
    try:
        username = urllib.parse.quote_plus(os.getenv('MONGO_USERNAME', ''))
        password = urllib.parse.quote_plus(os.getenv('MONGO_PASSWORD', ''))
        cluster = os.getenv('MONGO_CLUSTER')

        if not all([username, password, cluster]):
            logger.error("❌ Variáveis de ambiente não configuradas!")
            return None

        mongo_uri = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority"
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)

        # Testar conexão
        client.admin.command('ping')
        logger.info("✅ Conectado ao MongoDB com sucesso!")

        return client['bioma_db']

    except Exception as e:
        logger.error(f"❌ Erro ao conectar ao MongoDB: {e}")
        return None

def criar_indice_safe(collection, index_spec, **kwargs):
    """Cria índice ignorando erros de duplicação"""
    try:
        collection.create_index(index_spec, **kwargs)
        return True
    except Exception as e:
        if 'IndexKeySpecsConflict' in str(e) or 'already exists' in str(e):
            return False  # Índice já existe, ignorar
        raise  # Outro erro, propagar

def criar_indices(db):
    """Cria índices para otimizar consultas"""

    logger.info("\n📊 CRIANDO ÍNDICES PARA OTIMIZAÇÃO...\n")

    indices_criados = 0

    try:
        # 1. ÍNDICES NA COLEÇÃO USERS
        logger.info("1️⃣ Criando índices em 'users'...")
        if criar_indice_safe(db.users, [('username', ASCENDING)], unique=True): indices_criados += 1
        if criar_indice_safe(db.users, [('email', ASCENDING)], unique=True): indices_criados += 1
        if criar_indice_safe(db.users, [('role', ASCENDING)]): indices_criados += 1
        logger.info(f"   ✅ Índices processados em 'users'")

        # 2. ÍNDICES NA COLEÇÃO CLIENTES
        logger.info("\n2️⃣ Criando índices em 'clientes'...")
        if criar_indice_safe(db.clientes, [('cpf', ASCENDING)], unique=True, background=True): indices_criados += 1
        if criar_indice_safe(db.clientes, [('nome', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.clientes, [('telefone', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.clientes, [('email', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.clientes, [('created_at', DESCENDING)]): indices_criados += 1
        logger.info(f"   ✅ Índices processados em 'clientes'")

        # 3. ÍNDICES NA COLEÇÃO ORCAMENTOS
        logger.info("\n3️⃣ Criando índices em 'orcamentos'...")
        if criar_indice_safe(db.orcamentos, [('status', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.orcamentos, [('cliente_cpf', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.orcamentos, [('profissional_id', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.orcamentos, [('created_at', DESCENDING)]): indices_criados += 1
        if criar_indice_safe(db.orcamentos, [('data', DESCENDING)]): indices_criados += 1
        logger.info(f"   ✅ Índices processados em 'orcamentos'")

        # 4. ÍNDICES NA COLEÇÃO AGENDAMENTOS
        logger.info("\n4️⃣ Criando índices em 'agendamentos'...")
        if criar_indice_safe(db.agendamentos, [('data', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.agendamentos, [('status', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.agendamentos, [('cliente_cpf', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.agendamentos, [('profissional_id', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.agendamentos, [('created_at', DESCENDING)]): indices_criados += 1
        logger.info(f"   ✅ Índices processados em 'agendamentos'")

        # 5. ÍNDICES NA COLEÇÃO PRODUTOS
        logger.info("\n5️⃣ Criando índices em 'produtos'...")
        if criar_indice_safe(db.produtos, [('nome', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.produtos, [('categoria', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.produtos, [('estoque_atual', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.produtos, [('ativo', ASCENDING)]): indices_criados += 1
        logger.info(f"   ✅ Índices processados em 'produtos'")

        # 6. ÍNDICES NA COLEÇÃO PROFISSIONAIS
        logger.info("\n6️⃣ Criando índices em 'profissionais'...")
        if criar_indice_safe(db.profissionais, [('nome', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.profissionais, [('especialidade', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.profissionais, [('cpf', ASCENDING)], unique=True, background=True): indices_criados += 1
        if criar_indice_safe(db.profissionais, [('ativo', ASCENDING)]): indices_criados += 1
        logger.info(f"   ✅ Índices processados em 'profissionais'")

        # 7. ÍNDICES NA COLEÇÃO SERVICOS
        logger.info("\n7️⃣ Criando índices em 'servicos'...")
        if criar_indice_safe(db.servicos, [('nome', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.servicos, [('categoria', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.servicos, [('ativo', ASCENDING)]): indices_criados += 1
        logger.info(f"   ✅ Índices processados em 'servicos'")

        # 8. ÍNDICES NA COLEÇÃO FILA_ATENDIMENTO
        logger.info("\n8️⃣ Criando índices em 'fila_atendimento'...")
        if criar_indice_safe(db.fila_atendimento, [('status', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.fila_atendimento, [('posicao', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.fila_atendimento, [('created_at', ASCENDING)]): indices_criados += 1
        logger.info(f"   ✅ Índices processados em 'fila_atendimento'")

        # 9. ÍNDICES NA COLEÇÃO COMISSOES_HISTORICO
        logger.info("\n9️⃣ Criando índices em 'comissoes_historico'...")
        if criar_indice_safe(db.comissoes_historico, [('profissional_id', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.comissoes_historico, [('periodo_mes', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.comissoes_historico, [('created_at', DESCENDING)]): indices_criados += 1
        logger.info(f"   ✅ Índices processados em 'comissoes_historico'")

        # 10. ÍNDICES NA COLEÇÃO NOTIFICACOES
        logger.info("\n🔟 Criando índices em 'notificacoes'...")
        if criar_indice_safe(db.notificacoes, [('user_id', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.notificacoes, [('lida', ASCENDING)]): indices_criados += 1
        if criar_indice_safe(db.notificacoes, [('created_at', DESCENDING)]): indices_criados += 1
        logger.info(f"   ✅ Índices processados em 'notificacoes'")

        # 11. ÍNDICE COMPOSTO PARA BUSCA GLOBAL
        logger.info("\n🔍 Criando índices compostos para busca global...")
        if criar_indice_safe(db.clientes, [
            ('nome', 'text'),
            ('email', 'text'),
            ('telefone', 'text')
        ], name='busca_global_clientes'): indices_criados += 1
        if criar_indice_safe(db.produtos, [
            ('nome', 'text'),
            ('descricao', 'text'),
            ('categoria', 'text')
        ], name='busca_global_produtos'): indices_criados += 1
        if criar_indice_safe(db.profissionais, [
            ('nome', 'text'),
            ('especialidade', 'text')
        ], name='busca_global_profissionais'): indices_criados += 1
        logger.info(f"   ✅ Índices de busca global processados")

        logger.info(f"\n✅ OTIMIZAÇÃO CONCLUÍDA!")
        logger.info(f"📊 Total de índices criados: {indices_criados}")

        return True

    except Exception as e:
        logger.error(f"\n❌ Erro ao criar índices: {e}")
        return False

def analisar_performance(db):
    """Analisa a performance das coleções"""

    logger.info("\n\n📈 ANÁLISE DE PERFORMANCE...\n")

    colecoes = [
        'users', 'clientes', 'orcamentos', 'agendamentos',
        'produtos', 'profissionais', 'servicos', 'fila_atendimento',
        'comissoes_historico', 'notificacoes'
    ]

    for colecao in colecoes:
        try:
            count = db[colecao].count_documents({})
            indices = db[colecao].list_indexes()
            num_indices = len(list(indices))

            logger.info(f"📊 {colecao.upper()}")
            logger.info(f"   Documentos: {count}")
            logger.info(f"   Índices: {num_indices}")
            logger.info("")

        except Exception as e:
            logger.warning(f"⚠️ Erro ao analisar '{colecao}': {e}\n")

def main():
    """Função principal"""

    logger.info("=" * 60)
    logger.info("  OTIMIZAÇÃO DE BANCO DE DADOS - BIOMA v5.1.0")
    logger.info("=" * 60)

    # Conectar ao banco
    db = conectar_banco()
    if db is None:
        logger.error("\n❌ Falha ao conectar ao banco de dados!")
        sys.exit(1)

    # Criar índices
    sucesso = criar_indices(db)
    if not sucesso:
        logger.error("\n❌ Falha ao criar índices!")
        sys.exit(1)

    # Analisar performance
    analisar_performance(db)

    logger.info("\n" + "=" * 60)
    logger.info("  ✅ OTIMIZAÇÃO CONCLUÍDA COM SUCESSO!")
    logger.info("=" * 60)
    logger.info("\nAgora o banco de dados está otimizado e as consultas")
    logger.info("serão muito mais rápidas!")
    logger.info("\n")

if __name__ == '__main__':
    main()
