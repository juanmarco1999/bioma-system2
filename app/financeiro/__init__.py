#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Blueprint Financeiro
"""

from flask import Blueprint

bp = Blueprint('financeiro', __name__)

from app.financeiro import routes
