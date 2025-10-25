#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Blueprint Relatorios
"""

from flask import Blueprint

bp = Blueprint('relatorios', __name__)

from app.relatorios import routes
