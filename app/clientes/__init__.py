#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Blueprint Clientes
"""

from flask import Blueprint

bp = Blueprint('clientes', __name__)

from app.clientes import routes
