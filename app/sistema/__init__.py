#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Blueprint Sistema
"""

from flask import Blueprint

bp = Blueprint('sistema', __name__)

from app.sistema import routes
