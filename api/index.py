#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA UBERABA - Vercel Serverless Entry Point
Ponto de entrada para deploy no Vercel (serverless)
"""

import sys
import os

# Adicionar o diretório raiz ao Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar a aplicação Flask
from application import create_app

# Criar aplicação
app = create_app()

# Vercel usa esta variável para servir a aplicação
# Não precisa de app.run() - o Vercel gerencia isso
