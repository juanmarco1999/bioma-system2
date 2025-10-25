#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA UBERABA v3.7 - Entry Point
Desenvolvedor: Juan Marco (@juanmarco1999)
Email: 180147064@aluno.unb.br
Data: 2025-10-25

Entry point para a aplicação Flask com Application Factory pattern
"""

import os
from application import create_app

# Criar aplicação usando Application Factory
app = create_app()

if __name__ == '__main__':
    # Configurações para desenvolvimento
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'

    print(f"\n[BIOMA UBERABA v3.7] Sistema de Gestao Ultra Profissional")
    print(f"Servidor: http://localhost:{port}")
    print(f"Modo: {'DESENVOLVIMENTO' if debug else 'PRODUCAO'}\n")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
