#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Blueprint Assistentes
"""

from flask import Blueprint

bp = Blueprint('assistentes', __name__)

from app.assistentes import routes
