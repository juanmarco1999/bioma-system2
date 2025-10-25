#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Blueprint Dashboard
"""

from flask import Blueprint

bp = Blueprint('dashboard', __name__)

from app.dashboard import routes
