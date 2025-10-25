#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - API Blueprint (Consolidado)
Todas as rotas do sistema
"""

from flask import Blueprint

bp = Blueprint('api', __name__)

from app.api import routes
