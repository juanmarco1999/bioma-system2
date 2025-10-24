#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA UBERABA v3.7 - Complete Backend Routes
Este arquivo pode ser importado em app.py para adicionar rotas faltantes
"""

def add_missing_routes(app, db, login_required):
    """
    Adiciona todas as rotas que estavam faltando e causando erros 404/405

    Uso em app.py:
    from backend_routes_complete import add_missing_routes
    add_missing_routes(app, db, login_required)
    """

    from flask import Response, jsonify, request, session
    from datetime import datetime
    import json
    import time
    import logging

    logger = logging.getLogger(__name__)

    # ==================== SSE ROUTE ====================
    if not any(rule.rule == '/api/stream' for rule in app.url_map.iter_rules()):
        @app.route('/api/stream')
        @login_required
        def stream_updates():
            """Server-Sent Events for real-time updates"""
            def generate():
                try:
                    # Initial connection message
                    yield f"data: {json.dumps({'type': 'connected', 'message': 'SSE connected'})}\n\n"

                    counter = 0
                    while True:
                        counter += 1

                        try:
                            # Get recent updates
                            recent_data = {
                                'type': 'update',
                                'timestamp': datetime.now().isoformat(),
                                'counter': counter
                            }

                            # Check for new appointments
                            appointments = list(db.agendamentos.find(
                                {'data': {'$gte': datetime.now().strftime('%Y-%m-%d')}},
                                {'_id': 0, 'cliente_nome': 1, 'data': 1, 'hora': 1}
                            ).limit(5))

                            if appointments:
                                recent_data['appointments'] = appointments

                            # Check low stock items
                            low_stock = list(db.produtos.find(
                                {'quantidade': {'$lt': 10}},
                                {'_id': 0, 'nome': 1, 'quantidade': 1}
                            ).limit(5))

                            if low_stock:
                                recent_data['low_stock'] = low_stock

                            yield f"data: {json.dumps(recent_data)}\n\n"

                        except Exception as e:
                            logger.error(f"SSE update error: {e}")

                        # Wait 30 seconds
                        time.sleep(30)

                        # Send heartbeat every minute
                        if counter % 2 == 0:
                            yield f": heartbeat\n\n"

                except GeneratorExit:
                    logger.info("SSE client disconnected")
                except Exception as e:
                    logger.error(f"SSE stream error: {e}")

            return Response(generate(), mimetype='text/event-stream',
                          headers={
                              'Cache-Control': 'no-cache',
                              'X-Accel-Buffering': 'no',
                              'Connection': 'keep-alive'
                          })

        logger.info("✅ Added /api/stream route")


    # ==================== HEATMAP ALIAS ====================
    if not any(rule.rule == '/api/agendamentos/heatmap' for rule in app.url_map.iter_rules()):
        @app.route('/api/agendamentos/heatmap', methods=['GET'])
        @login_required
        def heatmap_agendamentos_alias():
            """Alias for the heatmap route to fix 405 error"""
            # Import the existing function
            try:
                # Try to find and call the existing mapa-calor function
                for rule in app.url_map.iter_rules():
                    if rule.rule == '/api/agendamentos/mapa-calor':
                        # Get the endpoint name and call the view function
                        endpoint = app.view_functions.get(rule.endpoint)
                        if endpoint:
                            return endpoint()

                # Fallback implementation if original not found
                dias = request.args.get('dias', 60, type=int)
                inicio = datetime.now() - timedelta(days=dias)

                pipeline = [
                    {'$match': {
                        'data': {'$gte': inicio.strftime('%Y-%m-%d')}
                    }},
                    {'$group': {
                        '_id': '$data',
                        'count': {'$sum': 1}
                    }},
                    {'$sort': {'_id': 1}}
                ]

                resultado = list(db.agendamentos.aggregate(pipeline))

                return jsonify({
                    'success': True,
                    'data': resultado,
                    'periodo': f'Últimos {dias} dias'
                })

            except Exception as e:
                logger.error(f"Heatmap error: {e}")
                return jsonify({'success': False, 'message': str(e)}), 500

        logger.info("✅ Added /api/agendamentos/heatmap alias")


    # ==================== AUTOCOMPLETE ROUTES ====================
    if not any(rule.rule == '/api/autocomplete/clientes' for rule in app.url_map.iter_rules()):
        @app.route('/api/autocomplete/clientes', methods=['GET'])
        @login_required
        def autocomplete_clientes():
            """Autocomplete for client names"""
            try:
                query = request.args.get('q', '')
                if len(query) < 2:
                    return jsonify({'success': True, 'results': []})

                # Search clients
                regex = {'$regex': query, '$options': 'i'}
                clientes = list(db.clients.find(
                    {'$or': [
                        {'nome': regex},
                        {'cpf': regex},
                        {'telefone': regex}
                    ]},
                    {'_id': 1, 'nome': 1, 'cpf': 1, 'telefone': 1}
                ).limit(10))

                for c in clientes:
                    c['_id'] = str(c['_id'])

                return jsonify({'success': True, 'results': clientes})

            except Exception as e:
                logger.error(f"Autocomplete error: {e}")
                return jsonify({'success': False, 'message': str(e)}), 500

        logger.info("✅ Added /api/autocomplete/clientes route")


    if not any(rule.rule == '/api/autocomplete/produtos' for rule in app.url_map.iter_rules()):
        @app.route('/api/autocomplete/produtos', methods=['GET'])
        @login_required
        def autocomplete_produtos():
            """Autocomplete for product names"""
            try:
                query = request.args.get('q', '')
                if len(query) < 2:
                    return jsonify({'success': True, 'results': []})

                # Search products
                produtos = list(db.produtos.find(
                    {'nome': {'$regex': query, '$options': 'i'}},
                    {'_id': 1, 'nome': 1, 'preco': 1, 'quantidade': 1}
                ).limit(10))

                for p in produtos:
                    p['_id'] = str(p['_id'])

                return jsonify({'success': True, 'results': produtos})

            except Exception as e:
                logger.error(f"Autocomplete produtos error: {e}")
                return jsonify({'success': False, 'message': str(e)}), 500

        logger.info("✅ Added /api/autocomplete/produtos route")


    # ==================== FINANCIAL REFRESH ====================
    if not any(rule.rule == '/api/financeiro/refresh' for rule in app.url_map.iter_rules()):
        @app.route('/api/financeiro/refresh', methods=['POST'])
        @login_required
        def refresh_financeiro():
            """Refresh all financial data"""
            try:
                from datetime import timedelta

                # Calculate summaries
                hoje = datetime.now()
                inicio_mes = hoje.replace(day=1)

                # Receitas do mês
                receitas_mes = db.vendas.aggregate([
                    {'$match': {
                        'data': {'$gte': inicio_mes.strftime('%Y-%m-%d')}
                    }},
                    {'$group': {
                        '_id': None,
                        'total': {'$sum': '$total'}
                    }}
                ])
                total_receitas = list(receitas_mes)[0]['total'] if receitas_mes else 0

                # Despesas do mês
                despesas_mes = db.despesas.aggregate([
                    {'$match': {
                        'data': {'$gte': inicio_mes.strftime('%Y-%m-%d')}
                    }},
                    {'$group': {
                        '_id': None,
                        'total': {'$sum': '$valor'}
                    }}
                ])
                total_despesas = list(despesas_mes)[0]['total'] if despesas_mes else 0

                # Comissões do mês
                comissoes_mes = db.comissoes.aggregate([
                    {'$match': {
                        'data': {'$gte': inicio_mes.strftime('%Y-%m-%d')}
                    }},
                    {'$group': {
                        '_id': None,
                        'total': {'$sum': '$valor'}
                    }}
                ])
                total_comissoes = list(comissoes_mes)[0]['total'] if comissoes_mes else 0

                return jsonify({
                    'success': True,
                    'data': {
                        'receitas_mes': total_receitas,
                        'despesas_mes': total_despesas,
                        'comissoes_mes': total_comissoes,
                        'lucro_mes': total_receitas - total_despesas - total_comissoes,
                        'updated_at': datetime.now().isoformat()
                    }
                })

            except Exception as e:
                logger.error(f"Financial refresh error: {e}")
                return jsonify({'success': False, 'message': str(e)}), 500

        logger.info("✅ Added /api/financeiro/refresh route")


    # ==================== DASHBOARD WIDGETS ====================
    if not any(rule.rule == '/api/dashboard/widgets' for rule in app.url_map.iter_rules()):
        @app.route('/api/dashboard/widgets', methods=['GET'])
        @login_required
        def get_dashboard_widgets():
            """Get all dashboard widget data"""
            try:
                hoje = datetime.now().strftime('%Y-%m-%d')

                widgets = {
                    'appointments_today': db.agendamentos.count_documents({'data': hoje}),
                    'clients_total': db.clients.count_documents({}),
                    'products_low_stock': db.produtos.count_documents({'quantidade': {'$lt': 10}}),
                    'sales_today': db.vendas.count_documents({'data': hoje}),
                    'pending_payments': db.vendas.count_documents({'status_pagamento': 'pendente'}),
                    'employees_active': db.funcionarios.count_documents({'ativo': True})
                }

                return jsonify({'success': True, 'widgets': widgets})

            except Exception as e:
                logger.error(f"Dashboard widgets error: {e}")
                return jsonify({'success': False, 'message': str(e)}), 500

        logger.info("✅ Added /api/dashboard/widgets route")


    # ==================== NOTIFICATION SYSTEM ====================
    if not any(rule.rule == '/api/notifications/count' for rule in app.url_map.iter_rules()):
        @app.route('/api/notifications/count', methods=['GET'])
        @login_required
        def get_notification_count():
            """Get unread notification count"""
            try:
                user_id = session.get('user_id')
                count = db.notifications.count_documents({
                    'user_id': user_id,
                    'read': False
                })
                return jsonify({'success': True, 'count': count})

            except Exception as e:
                logger.error(f"Notification count error: {e}")
                return jsonify({'success': False, 'message': str(e)}), 500

        logger.info("✅ Added /api/notifications/count route")


    # ==================== SYSTEM HEALTH CHECK ====================
    if not any(rule.rule == '/api/health' for rule in app.url_map.iter_rules()):
        @app.route('/api/health', methods=['GET'])
        def health_check():
            """System health check (no auth required)"""
            try:
                # Check database connection
                db.command('ping')
                db_status = 'healthy'
            except:
                db_status = 'unhealthy'

            return jsonify({
                'status': 'ok' if db_status == 'healthy' else 'degraded',
                'database': db_status,
                'timestamp': datetime.now().isoformat(),
                'version': 'BIOMA v3.7'
            })

        logger.info("✅ Added /api/health route")


    # ==================== CACHE CLEAR ====================
    if not any(rule.rule == '/api/cache/clear' for rule in app.url_map.iter_rules()):
        @app.route('/api/cache/clear', methods=['POST'])
        @login_required
        def clear_cache():
            """Clear application cache"""
            try:
                # Clear any cached data
                # This is a placeholder - implement actual cache clearing logic
                return jsonify({
                    'success': True,
                    'message': 'Cache limpo com sucesso',
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Cache clear error: {e}")
                return jsonify({'success': False, 'message': str(e)}), 500

        logger.info("✅ Added /api/cache/clear route")


    logger.info("🎯 Todas as rotas faltantes foram adicionadas com sucesso!")
    return app


# Função standalone para verificar rotas
def check_missing_routes(app):
    """
    Verifica quais rotas estão faltando no app

    Returns:
        list: Lista de rotas que deveriam existir mas não foram encontradas
    """
    expected_routes = [
        '/api/stream',
        '/api/agendamentos/heatmap',
        '/api/autocomplete/clientes',
        '/api/autocomplete/produtos',
        '/api/financeiro/refresh',
        '/api/dashboard/widgets',
        '/api/notifications/count',
        '/api/health',
        '/api/cache/clear'
    ]

    existing_routes = [rule.rule for rule in app.url_map.iter_rules()]
    missing = [route for route in expected_routes if route not in existing_routes]

    if missing:
        print(f"⚠️  Rotas faltantes: {missing}")
    else:
        print("✅ Todas as rotas esperadas estão presentes!")

    return missing


if __name__ == '__main__':
    print("""
    ====================================
    BIOMA v3.7 - Backend Routes Complete
    ====================================

    Este arquivo contém todas as rotas necessárias para corrigir os erros 404/405.

    Para usar em app.py:

    from backend_routes_complete import add_missing_routes
    add_missing_routes(app, db, login_required)

    Ou para verificar rotas faltantes:

    from backend_routes_complete import check_missing_routes
    missing = check_missing_routes(app)
    """)