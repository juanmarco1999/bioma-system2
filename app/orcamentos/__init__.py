#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Blueprint Orcamentos
"""

from flask import Blueprint

bp = Blueprint('orcamentos', __name__)

from app.orcamentos import routes
