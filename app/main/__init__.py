#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Blueprint Main
Rotas principais: index, health
"""

from flask import Blueprint

bp = Blueprint('main', __name__)

from app.main import routes
