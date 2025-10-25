#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Blueprint Estoque
"""

from flask import Blueprint

bp = Blueprint('estoque', __name__)

from app.estoque import routes
