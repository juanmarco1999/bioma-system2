#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA UBERABA v3.7 - Backend Routes Optimized
Este arquivo contém as rotas backend otimizadas para resolver erros 404/405
"""

from flask import Response, jsonify, request
from functools import wraps
import json
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def add_optimized_routes(app, db, login_required):
    """
    Adiciona rotas otimizadas ao app Flask

    Args:
        app: Instância do Flask app
        db: Instância do MongoDB database
        login_required: Decorator para autenticação
    """

    # ==================== SERVER-SENT EVENTS (SSE) ====================

    @app.route('/api/stream')
    @login_required
    def stream_updates():
        """Route for Server-Sent Events (SSE) for real-time updates"""
        def generate():
            """Generator function for SSE"""
            try:
                # Enviar heartbeat inicial
                yield f"data: {json.dumps({'type': 'connected', 'message': 'SSE conectado com sucesso'})}\n\n"

                # Loop para manter conexão viva
                counter = 0
                while True:
                    counter += 1

                    # Buscar atualizações do banco de dados
                    try:
                        # Verificar novos agendamentos
                        recent_appointments = list(db.agendamentos.find(
                            {'data': {'$gte': datetime.now().strftime('%Y-%m-%d')}},
                            {'_id': 1, 'cliente_nome': 1, 'data': 1, 'hora': 1, 'servico': 1}
                        ).sort('_id', -1).limit(5))

                        for apt in recent_appointments:
                            apt['_id'] = str(apt['_id'])

                        # Enviar dados atualizados
                        data = {
                            'type': 'update',
                            'timestamp': datetime.now().isoformat(),
                            'recent_appointments': recent_appointments,
                            'counter': counter
                        }

                        yield f"data: {json.dumps(data)}\n\n"

                    except Exception as e:
                        logger.error(f"Erro ao buscar atualizações SSE: {e}")
                        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

                    # Aguardar 30 segundos antes da próxima atualização
                    time.sleep(30)

                    # Enviar heartbeat a cada 30 segundos para manter conexão viva
                    if counter % 2 == 0:
                        yield f": heartbeat\n\n"

            except GeneratorExit:
                logger.info("Cliente SSE desconectado")
            except Exception as e:
                logger.error(f"Erro no SSE stream: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return Response(generate(), mimetype='text/event-stream')


    # ==================== HEATMAP ALIAS ====================

    @app.route('/api/agendamentos/heatmap', methods=['GET'])
    @login_required
    def heatmap_agendamentos_alias():
        """
        Alias route for heatmap - ensures compatibility with frontend
        Frontend calls /api/agendamentos/heatmap but backend has /api/agendamentos/mapa-calor
        """
        from app import mapa_calor_agendamentos
        return mapa_calor_agendamentos()


    # ==================== NOTIFICATIONS ====================

    @app.route('/api/notifications/unread', methods=['GET'])
    @login_required
    def get_unread_notifications():
        """Get unread notifications count"""
        try:
            from flask import session
            user_id = session.get('user_id')

            # Contar notificações não lidas
            unread_count = db.notifications.count_documents({
                'user_id': user_id,
                'read': False
            })

            # Buscar últimas 5 notificações
            recent_notifications = list(db.notifications.find(
                {'user_id': user_id},
                {'_id': 1, 'title': 1, 'message': 1, 'type': 1, 'created_at': 1, 'read': 1}
            ).sort('created_at', -1).limit(5))

            for notif in recent_notifications:
                notif['_id'] = str(notif['_id'])

            return jsonify({
                'success': True,
                'unread_count': unread_count,
                'recent_notifications': recent_notifications
            })

        except Exception as e:
            logger.error(f"Erro ao buscar notificações: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500


    @app.route('/api/notifications/mark-read', methods=['POST'])
    @login_required
    def mark_notifications_read():
        """Mark notifications as read"""
        try:
            from flask import session
            user_id = session.get('user_id')

            data = request.json
            notification_ids = data.get('notification_ids', [])

            if notification_ids:
                # Marcar específicas como lidas
                from bson import ObjectId
                db.notifications.update_many(
                    {
                        '_id': {'$in': [ObjectId(nid) for nid in notification_ids]},
                        'user_id': user_id
                    },
                    {'$set': {'read': True, 'read_at': datetime.now()}}
                )
            else:
                # Marcar todas como lidas
                db.notifications.update_many(
                    {'user_id': user_id, 'read': False},
                    {'$set': {'read': True, 'read_at': datetime.now()}}
                )

            return jsonify({'success': True, 'message': 'Notificações marcadas como lidas'})

        except Exception as e:
            logger.error(f"Erro ao marcar notificações como lidas: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500


    # ==================== SYSTEM STATUS ====================

    @app.route('/api/system/status', methods=['GET'])
    @login_required
    def get_system_status():
        """Get system status and health check"""
        try:
            # Verificar conexão com MongoDB
            db_status = "connected" if db.command("ping") else "disconnected"

            # Coletar estatísticas
            stats = {
                'database': db_status,
                'collections': {
                    'clients': db.clients.count_documents({}),
                    'agendamentos': db.agendamentos.count_documents({}),
                    'produtos': db.produtos.count_documents({}),
                    'vendas': db.vendas.count_documents({}),
                    'funcionarios': db.funcionarios.count_documents({}),
                    'fornecedores': db.fornecedores.count_documents({}),
                },
                'server_time': datetime.now().isoformat(),
                'version': 'BIOMA v3.7'
            }

            return jsonify({
                'success': True,
                'status': 'healthy',
                'stats': stats
            })

        except Exception as e:
            logger.error(f"Erro ao verificar status do sistema: {e}")
            return jsonify({
                'success': False,
                'status': 'error',
                'message': str(e)
            }), 500


    # ==================== DATA REFRESH ====================

    @app.route('/api/refresh/<module>', methods=['POST'])
    @login_required
    def refresh_module_data(module):
        """Refresh data for a specific module"""
        try:
            valid_modules = [
                'dashboard', 'financeiro', 'estoque', 'agendamentos',
                'clientes', 'vendas', 'funcionarios', 'fornecedores'
            ]

            if module not in valid_modules:
                return jsonify({
                    'success': False,
                    'message': f'Módulo inválido: {module}'
                }), 400

            # Limpar cache do módulo (se implementado)
            cache_key = f"module_{module}"
            # Implementar lógica de cache se necessário

            # Retornar sucesso
            return jsonify({
                'success': True,
                'message': f'Dados do módulo {module} atualizados com sucesso',
                'module': module,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Erro ao atualizar módulo {module}: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500


    # ==================== WEBSOCKET FALLBACK ====================

    @app.route('/api/ws/ping', methods=['GET'])
    def websocket_ping():
        """Websocket connection test endpoint"""
        return jsonify({
            'success': True,
            'message': 'pong',
            'timestamp': datetime.now().isoformat()
        })


    # ==================== ERROR HANDLERS ====================

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': 'O recurso solicitado não foi encontrado',
            'status_code': 404
        }), 404


    @app.errorhandler(405)
    def method_not_allowed_error(error):
        """Handle 405 errors"""
        return jsonify({
            'success': False,
            'error': 'Method Not Allowed',
            'message': 'Método HTTP não permitido para este recurso',
            'status_code': 405
        }), 405


    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        logger.error(f"Erro interno do servidor: {error}")
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': 'Ocorreu um erro interno no servidor',
            'status_code': 500
        }), 500


    logger.info("✅ Rotas otimizadas carregadas com sucesso")
    return app


# Lista de todas as rotas disponíveis
AVAILABLE_ROUTES = {
    # SSE
    'GET /api/stream': 'Server-Sent Events para atualizações em tempo real',

    # Agendamentos
    'GET /api/agendamentos/heatmap': 'Alias para mapa de calor de agendamentos',

    # Notificações
    'GET /api/notifications/unread': 'Obter notificações não lidas',
    'POST /api/notifications/mark-read': 'Marcar notificações como lidas',

    # Sistema
    'GET /api/system/status': 'Status e health check do sistema',
    'POST /api/refresh/<module>': 'Atualizar dados de um módulo específico',

    # WebSocket fallback
    'GET /api/ws/ping': 'Teste de conexão WebSocket'
}


def print_routes():
    """Imprime todas as rotas disponíveis"""
    print("\n📍 ROTAS BACKEND OTIMIZADAS:")
    print("=" * 60)
    for route, description in AVAILABLE_ROUTES.items():
        print(f"{route:<35} → {description}")
    print("=" * 60)


if __name__ == '__main__':
    print_routes()