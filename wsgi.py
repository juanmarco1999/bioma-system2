#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - WSGI Entry Point
Compatível com gunicorn app:app E gunicorn run:app

Este arquivo serve como bridge/shim para o Render
"""

from run import app

# Expor 'app' para gunicorn
# Agora funciona com: gunicorn app:app OU gunicorn run:app OU gunicorn wsgi:app
if __name__ == "__main__":
    app.run()
