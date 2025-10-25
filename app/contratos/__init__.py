#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Blueprint Contratos
"""

from flask import Blueprint

bp = Blueprint('contratos', __name__)

from app.contratos import routes
