#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA UBERABA v3.7 - Funções Utilitárias Compartilhadas
Desenvolvedor: Juan Marco (@juanmarco1999)
"""

from bson import ObjectId
from datetime import datetime
from flask import current_app
import logging

logger = logging.getLogger(__name__)


def convert_objectid(obj):
    """Converter ObjectId para string recursivamente"""
    if isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    elif isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            if isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, (dict, list)):
                result[key] = convert_objectid(value)
            else:
                result[key] = value
        return result
    elif isinstance(obj, ObjectId):
        return str(obj)
    return obj


def allowed_file(filename):
    """Verificar se extensão do arquivo é permitida"""
    allowed = current_app.config['ALLOWED_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def registrar_auditoria(acao, detalhes, usuario_id=None, colecao=None):
    """Registrar ação de auditoria no banco de dados"""
    from application.extensions import db
    from flask import session

    if db is None:
        return

    try:
        if usuario_id is None:
            usuario_id = session.get('user_id', 'Sistema')

        auditoria_data = {
            'timestamp': datetime.utcnow(),
            'usuario_id': usuario_id,
            'acao': acao,
            'detalhes': detalhes,
            'colecao': colecao,
            'ip': session.get('_ip', 'Unknown')
        }

        db.auditoria.insert_one(auditoria_data)
        logger.info(f"📋 Auditoria: {acao} por {usuario_id}")

    except Exception as e:
        logger.error(f"❌ Erro ao registrar auditoria: {e}")


def validar_cpf(cpf):
    """Validar CPF brasileiro"""
    # Remove caracteres não numéricos
    cpf = ''.join(filter(str.isdigit, cpf))

    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False

    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False

    # Validação dos dígitos verificadores
    for i in range(9, 11):
        value = sum((int(cpf[num]) * ((i + 1) - num) for num in range(0, i)))
        digit = ((value * 10) % 11) % 10
        if digit != int(cpf[i]):
            return False

    return True


def formatar_moeda(valor):
    """Formatar valor para moeda brasileira (R$)"""
    if valor is None:
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def calcular_comissao(valor_total, percentual):
    """Calcular comissão baseada em percentual"""
    if not valor_total or not percentual:
        return 0.0
    return round(float(valor_total) * (float(percentual) / 100), 2)


def safe_int(value, default=0):
    """Conversão segura para inteiro"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """Conversão segura para float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def parse_date(date_string):
    """Parse de string de data para datetime"""
    if not date_string:
        return None

    formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f'
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue

    return None


def update_cliente_denormalized_fields(cliente_cpf):
    """
    Update denormalized fields on cliente document for performance.

    This function calculates and stores:
    - total_faturado: Sum of all approved orcamentos
    - ultima_visita: Date of last orcamento
    - total_visitas: Count of all orcamentos

    This prevents N+1 query problem when loading cliente lists.
    """
    from application.extensions import db
    from pymongo import DESCENDING

    if db is None or not cliente_cpf:
        return

    try:
        # Calculate aggregated values
        total_faturado = sum(
            o.get('total_final', 0)
            for o in db.orcamentos.find(
                {'cliente_cpf': cliente_cpf, 'status': 'Aprovado'},
                {'total_final': 1}
            )
        )

        ultimo_orc = db.orcamentos.find_one(
            {'cliente_cpf': cliente_cpf},
            sort=[('created_at', DESCENDING)],
            projection={'created_at': 1}
        )

        ultima_visita = ultimo_orc['created_at'] if ultimo_orc else None
        total_visitas = db.orcamentos.count_documents({'cliente_cpf': cliente_cpf})

        # Update cliente document with denormalized values
        db.clientes.update_one(
            {'cpf': cliente_cpf},
            {'$set': {
                'total_faturado': total_faturado,
                'ultima_visita': ultima_visita,
                'total_visitas': total_visitas,
                'updated_at': datetime.now()
            }}
        )

        logger.debug(f"Updated denormalized fields for cliente CPF: {cliente_cpf}")

    except Exception as e:
        logger.error(f"Error updating denormalized fields for cliente {cliente_cpf}: {e}")


def get_assistente_details(assistente_id, assistente_tipo=None):
    """Recupera os dados do assistente a partir do ID informado.

    O assistente pode estar na coleção de profissionais ou na coleção dedicada
    de assistentes. O campo assistente_tipo permite definir explicitamente a
    prioridade de busca e garante compatibilidade com registros antigos que
    armazenavam apenas o ID do profissional.
    """
    from application.extensions import db

    if db is None or not assistente_id:
        return None

    try:
        # Se tipo definido, buscar diretamente
        if assistente_tipo == 'profissional':
            return db.profissionais.find_one({'_id': ObjectId(assistente_id)})
        elif assistente_tipo == 'assistente':
            return db.assistentes.find_one({'_id': ObjectId(assistente_id)})

        # Busca dupla para compatibilidade
        assistente = db.assistentes.find_one({'_id': ObjectId(assistente_id)})
        if assistente:
            return assistente

        return db.profissionais.find_one({'_id': ObjectId(assistente_id)})

    except Exception as e:
        logger.error(f"Error fetching assistente {assistente_id}: {e}")
        return None
