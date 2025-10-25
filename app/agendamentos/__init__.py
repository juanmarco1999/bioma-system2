#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Blueprint Agendamentos
"""

from flask import Blueprint

bp = Blueprint('agendamentos', __name__)

from app.agendamentos import routes
