#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Agendamentos Routes
Auto-gerado pelo script de migração
"""

from flask import request, jsonify, session, current_app, send_file, render_template
from bson import ObjectId
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import logging
import io
import csv
import json

from app.agendamentos import bp
from app.decorators import login_required, permission_required, get_user_permissions
from app.utils import convert_objectid, allowed_file, registrar_auditoria
from app.extensions import db as get_db, get_from_cache, set_in_cache

logger = logging.getLogger(__name__)

@bp.route('/api/agendamentos', methods=['GET', 'POST'])
@login_required
def agendamentos():
    if db is None:
        return jsonify({'success': False}), 500
    if request.method == 'GET':
        try:
            agora = datetime.now()
            agends = list(db.agendamentos.find({'data': {'$gte': agora}}).sort('data', ASCENDING).limit(10))
            return jsonify({'success': True, 'agendamentos': convert_objectid(agends)})
        except:
            return jsonify({'success': False}), 500
    # POST - Criar novo agendamento com VALIDAÇÃO ROBUSTA (Roadmap - Input Validation)
    data = request.json

    # Validação de campos obrigatórios
    required_fields = ['data', 'horario', 'cliente_id', 'profissional_id', 'servico_id']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({
            'success': False,
            'message': f'Campos obrigatórios ausentes: {", ".join(missing_fields)}'
        }), 400

    try:
        # Validar e converter data
        data_agendamento = datetime.fromisoformat(data['data'].replace('Z', '+00:00'))

        # Validar que a data não está no passado
        if data_agendamento < datetime.now():
            return jsonify({
                'success': False,
                'message': 'Não é possível agendar para data/hora no passado'
            }), 400

        # Validar formato do horário (HH:MM)
        horario = data['horario']
        if not isinstance(horario, str) or not len(horario.split(':')) == 2:
            return jsonify({
                'success': False,
                'message': 'Formato de horário inválido. Use HH:MM'
            }), 400

        # Verificar se já existe agendamento conflitante
        conflito = db.agendamentos.find_one({
            'profissional_id': data['profissional_id'],
            'data': data_agendamento,
            'horario': horario,
            'status': {'$ne': 'cancelado'}
        })

        if conflito:
            return jsonify({
                'success': False,
                'message': 'Já existe um agendamento para este profissional neste horário'
            }), 409  # HTTP 409 Conflict

        # Inserir agendamento
        agend_id = db.agendamentos.insert_one({
            'cliente_id': data['cliente_id'],
            'cliente_nome': data.get('cliente_nome', 'N/A'),
            'cliente_telefone': data.get('cliente_telefone'),
            'profissional_id': data['profissional_id'],
            'profissional_nome': data.get('profissional_nome', 'N/A'),
            'servico_id': data['servico_id'],
            'servico_nome': data.get('servico_nome', 'N/A'),
            'data': data_agendamento,
            'horario': horario,
            'status': 'confirmado',
            'created_at': datetime.now(),
            'created_by': session.get('user_email', 'sistema')
        }).inserted_id

        logger.info(f"✅ Agendamento criado: {agend_id} para {data.get('cliente_nome')} em {data_agendamento}")
        return jsonify({'success': True, 'id': str(agend_id)})

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': f'Erro de validação: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Erro ao criar agendamento: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno ao criar agendamento'
        }), 500

@bp.route('/api/agendamentos/horarios-disponiveis', methods=['GET'])


@bp.route('/api/agendamentos/mapa-calor', methods=['GET'])
@login_required
def mapa_calor_agendamentos():
    """Gerar mapa de calor de agendamentos e orçamentos"""
    if db is None:
        return jsonify({'success': False}), 500
    
    try:
        # Últimos 30 dias
        data_inicio = datetime.now() - timedelta(days=30)
        data_fim = datetime.now()
        
        # Buscar agendamentos
        agendamentos = list(db.agendamentos.find({
            'created_at': {'$gte': data_inicio, '$lte': data_fim}
        }))
        
        # Buscar orçamentos
        orcamentos = list(db.orcamentos.find({
            'created_at': {'$gte': data_inicio, '$lte': data_fim}
        }))
        
        # Agrupar por dia
        mapa_calor = {}
        
        for agend in agendamentos:
            data_agend = agend.get('created_at', datetime.now())
            dia = data_agend.strftime('%Y-%m-%d')
            if dia not in mapa_calor:
                mapa_calor[dia] = {'agendamentos': 0, 'orcamentos': 0, 'total': 0}
            mapa_calor[dia]['agendamentos'] += 1
            mapa_calor[dia]['total'] += 1
        
        for orc in orcamentos:
            data_orc = orc.get('created_at', datetime.now())
            dia = data_orc.strftime('%Y-%m-%d')
            if dia not in mapa_calor:
                mapa_calor[dia] = {'agendamentos': 0, 'orcamentos': 0, 'total': 0}
            mapa_calor[dia]['orcamentos'] += 1
            mapa_calor[dia]['total'] += 1
        
        # Converter para lista ordenada
        mapa_lista = [
            {
                'data': dia,
                'agendamentos': dados['agendamentos'],
                'orcamentos': dados['orcamentos'],
                'total': dados['total']
            }
            for dia, dados in sorted(mapa_calor.items())
        ]
        
        return jsonify({'success': True, 'mapa_calor': mapa_lista})
    except Exception as e:
        logger.error(f"Erro ao gerar mapa de calor: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/api/agendamentos/<id>', methods=['DELETE'])


@bp.route('/api/agendamentos/hoje', methods=['GET'])
@login_required
def agendamentos_hoje():
    """Buscar agendamentos de hoje com estatísticas"""
    if db is None:
        return jsonify({'success': False, 'message': 'Banco de dados indisponível'}), 500
    
    try:
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        amanha = hoje + timedelta(days=1)
        
        # Buscar agendamentos de hoje
        agendamentos = list(db.agendamentos.find({
            'data': {'$gte': hoje, '$lt': amanha}
        }).sort('horario', ASCENDING))
        
        resultado = []
        confirmados = 0
        pendentes = 0
        concluidos = 0
        cancelados = 0
        
        for a in agendamentos:
            # Buscar dados relacionados
            cliente = db.clientes.find_one({'_id': ObjectId(a['cliente_id'])}) if a.get('cliente_id') else None
            servico = db.servicos.find_one({'_id': ObjectId(a['servico_id'])}) if a.get('servico_id') else None
            prof = db.profissionais.find_one({'_id': ObjectId(a['profissional_id'])}) if a.get('profissional_id') else None
            
            status = a.get('status', 'Pendente')
            
            # Contar por status
            if status == 'Confirmado':
                confirmados += 1
            elif status == 'Pendente':
                pendentes += 1
            elif status == 'Concluído':
                concluidos += 1
            elif status == 'Cancelado':
                cancelados += 1
            
            resultado.append({
                '_id': str(a['_id']),
                'horario': a.get('horario', ''),
                'cliente_nome': cliente.get('nome') if cliente else 'Desconhecido',
                'servico': servico.get('nome') if servico else 'Desconhecido',
                'profissional': prof.get('nome') if prof else 'Desconhecido',
                'status': status,
                'observacoes': a.get('observacoes', '')
            })
        
        logger.info(f"Agendamentos hoje: {len(resultado)} encontrados")
        
        return jsonify({
            'success': True,
            'agendamentos': resultado,
            'total': len(resultado),
            'confirmados': confirmados,
            'pendentes': pendentes,
            'concluidos': concluidos,
            'cancelados': cancelados
        })
        
    except Exception as e:
        logger.error(f"Erro em agendamentos_hoje: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/api/agendamentos/semana', methods=['GET'])


@bp.route('/api/agendamentos/mes', methods=['GET'])
@login_required
def agendamentos_mes():
    """Buscar agendamentos do mês atual"""
    if db is None:
        return jsonify({'success': False, 'message': 'Banco de dados indisponível'}), 500
    
    try:
        hoje = datetime.now()
        inicio_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calcular último dia do mês
        if hoje.month == 12:
            fim_mes = hoje.replace(year=hoje.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            fim_mes = hoje.replace(month=hoje.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        agendamentos = list(db.agendamentos.find({
            'data': {'$gte': inicio_mes, '$lt': fim_mes}
        }).sort('data', ASCENDING))
        
        resultado = []
        for a in agendamentos:
            cliente = db.clientes.find_one({'_id': ObjectId(a['cliente_id'])}) if a.get('cliente_id') else None
            servico = db.servicos.find_one({'_id': ObjectId(a['servico_id'])}) if a.get('servico_id') else None
            prof = db.profissionais.find_one({'_id': ObjectId(a['profissional_id'])}) if a.get('profissional_id') else None
            
            resultado.append({
                '_id': str(a['_id']),
                'data': a.get('data').isoformat() if a.get('data') else '',
                'horario': a.get('horario', ''),
                'cliente_nome': cliente.get('nome') if cliente else 'Desconhecido',
                'servico': servico.get('nome') if servico else 'Desconhecido',
                'profissional': prof.get('nome') if prof else 'Desconhecido',
                'status': a.get('status', 'Pendente')
            })
        
        logger.info(f"Agendamentos mês: {len(resultado)} encontrados")
        
        return jsonify({
            'success': True,
            'agendamentos': resultado,
            'periodo': 'mes',
            'mes': hoje.strftime('%B %Y'),
            'inicio': inicio_mes.isoformat(),
            'fim': fim_mes.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro em agendamentos_mes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/api/fila', methods=['GET', 'POST'])


@bp.route('/api/agendamentos/heatmap', methods=['GET'])
@login_required
def heatmap_agendamentos_alias():
    """Alias route for heatmap - redirects to the actual route"""
    # Redirecionar para a rota existente
    dias = request.args.get('dias', 60, type=int)
    return mapa_calor_agendamentos()


# ==================== FIM ROTAS ADICIONAIS ====================

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🌳 BIOMA UBERABA v3.7 COMPLETO E DEFINITIVO")
    print("=" * 80)
    init_db()
    is_production = os.getenv('FLASK_ENV') == 'production'
    base_url = 'https://bioma-system2.onrender.com' if is_production else 'http://localhost:5000'
    print(f"\n🚀 Servidor: {base_url}")
    print(f"👤 Login Padrão: admin / admin123")
    print(f"🔑 TODOS os novos usuários têm privilégios de ADMIN automaticamente")
    if db is not None:
        try:
            db.command('ping')
            print(f"💾 MongoDB: ✅ CONECTADO")
        except:
            print(f"💾 MongoDB: ❌ ERRO DE CONEXÃO")
    else:
        print(f"💾 MongoDB: ❌ NÃO CONECTADO")
    if os.getenv('MAILERSEND_API_KEY'):
        print(f"📧 MailerSend: ✅ CONFIGURADO")
    else:
        print(f"📧 MailerSend: ⚠️  NÃO CONFIGURADO")
    print("\n" + "=" * 80)
    print(f"🕐 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"👨‍💻 Desenvolvedor: @juanmarco1999")
    print(f"📧 Contato: 180147064@aluno.unb.br")
    print("=" * 80 + "\n")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)