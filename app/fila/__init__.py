#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Blueprint Fila
"""

from flask import Blueprint

bp = Blueprint('fila', __name__)

from app.fila import routes
