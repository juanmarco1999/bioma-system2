#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Compatibility Shim for Render
Este arquivo permite que o Render use 'gunicorn app:app' mesmo com a nova estrutura

IMPORTANTE: Este é apenas um wrapper. O código real está em:
- run.py (entry point principal)
- app/ (Application Factory com Blueprints)
"""

# Importar a aplicação da nova estrutura
from run import app

# Agora 'gunicorn app:app' funcionará!
# O Render pode usar app:app (antigo) ou run:app (novo)

if __name__ == "__main__":
    # Se executado diretamente, rodar o servidor
    import os
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
