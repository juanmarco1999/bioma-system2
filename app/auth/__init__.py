#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Blueprint Auth
"""

from flask import Blueprint

bp = Blueprint('auth', __name__)

from app.auth import routes
