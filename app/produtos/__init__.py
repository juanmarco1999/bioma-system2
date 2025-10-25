#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Blueprint Produtos
"""

from flask import Blueprint

bp = Blueprint('produtos', __name__)

from app.produtos import routes
