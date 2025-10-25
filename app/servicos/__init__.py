#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Blueprint Servicos
"""

from flask import Blueprint

bp = Blueprint('servicos', __name__)

from app.servicos import routes
