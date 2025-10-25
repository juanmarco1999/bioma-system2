#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Blueprint Profissionais
"""

from flask import Blueprint

bp = Blueprint('profissionais', __name__)

from app.profissionais import routes
