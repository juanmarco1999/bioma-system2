#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Contratos Routes
Auto-gerado pelo script de migração
"""

from flask import request, jsonify, session, current_app, send_file, render_template
from bson import ObjectId
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import logging
import io
import csv
import json

from app.contratos import bp
from app.decorators import login_required, permission_required, get_user_permissions
from app.utils import convert_objectid, allowed_file, registrar_auditoria
from app.extensions import db as get_db, get_from_cache, set_in_cache

logger = logging.getLogger(__name__)

@bp.route('/api/contratos/<id>/pdf', methods=['GET'])
@login_required
def gerar_pdf_contrato(id):
    """Gerar PDF de contrato para impressão (Diretriz #4)"""
    if db is None:
        return jsonify({'success': False}), 500

    try:
        contrato = db.orcamentos.find_one({'_id': ObjectId(id)})
        if not contrato:
            return jsonify({'success': False, 'message': 'Contrato não encontrado'}), 404

        # Criar buffer para o PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        # Título
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=TA_CENTER)
        elements.append(Paragraph(f"CONTRATO #{contrato.get('numero', str(contrato['_id'])[-6:])}", title_style))
        elements.append(Spacer(1, 0.3*cm))

        # Status
        status_style = ParagraphStyle('Status', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10)
        status_color = HexColor('#4CAF50') if contrato.get('status') == 'Aprovado' else HexColor('#FF9800')
        elements.append(Paragraph(f'<font color="{status_color}"><b>STATUS: {contrato.get("status", "N/A")}</b></font>', status_style))
        elements.append(Spacer(1, 0.3*cm))

        # Informações do cliente
        elements.append(Paragraph('<b>DADOS DO CLIENTE</b>', styles['Heading2']))
        cliente_data = [
            ['Nome:', contrato.get('cliente_nome', 'N/A')],
            ['CPF:', contrato.get('cliente_cpf', 'N/A')],
            ['Telefone:', contrato.get('cliente_telefone', 'N/A')],
            ['Email:', contrato.get('cliente_email', 'N/A')],
            ['Data Contrato:', contrato.get('created_at', datetime.now()).strftime('%d/%m/%Y') if isinstance(contrato.get('created_at'), datetime) else 'N/A'],
            ['Forma Pagamento:', contrato.get('forma_pagamento', 'N/A')]
        ]
        cliente_table = Table(cliente_data, colWidths=[4*cm, 12*cm])
        cliente_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f0f0f0')),
            ('GRID', (0, 0), (-1, -1), 0.5, black),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        elements.append(cliente_table)
        elements.append(Spacer(1, 0.5*cm))

        # Serviços contratados
        if contrato.get('servicos'):
            elements.append(Paragraph('<b>SERVIÇOS CONTRATADOS</b>', styles['Heading2']))
            servicos_data = [['Descrição', 'Profissional', 'Qtd', 'Valor Unit.', 'Total']]
            for srv in contrato['servicos']:
                servicos_data.append([
                    srv.get('nome', 'N/A'),
                    srv.get('profissional_nome', '-'),
                    str(srv.get('quantidade', 1)),
                    f"R$ {srv.get('preco', 0):.2f}",
                    f"R$ {srv.get('total', 0):.2f}"
                ])
            servicos_table = Table(servicos_data, colWidths=[6*cm, 4*cm, 1.5*cm, 2.5*cm, 2*cm])
            servicos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#4CAF50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]))
            elements.append(servicos_table)
            elements.append(Spacer(1, 0.3*cm))

        # Produtos
        if contrato.get('produtos'):
            elements.append(Paragraph('<b>PRODUTOS</b>', styles['Heading2']))
            produtos_data = [['Descrição', 'Quantidade', 'Valor Unit.', 'Total']]
            for prd in contrato['produtos']:
                produtos_data.append([
                    prd.get('nome', 'N/A'),
                    str(prd.get('quantidade', 1)),
                    f"R$ {prd.get('preco', 0):.2f}",
                    f"R$ {prd.get('total', 0):.2f}"
                ])
            produtos_table = Table(produtos_data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
            produtos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2196F3')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]))
            elements.append(produtos_table)
            elements.append(Spacer(1, 0.3*cm))

        # Totais
        totais_data = [
            ['Subtotal Serviços:', f"R$ {contrato.get('total_servicos', 0):.2f}"],
            ['Subtotal Produtos:', f"R$ {contrato.get('total_produtos', 0):.2f}"],
            ['Desconto:', f"R$ {contrato.get('desconto_valor', 0):.2f}"],
            ['<b>TOTAL DO CONTRATO:</b>', f"<b>R$ {contrato.get('total_final', 0):.2f}</b>"]
        ]
        totais_table = Table(totais_data, colWidths=[12*cm, 4*cm])
        totais_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('BACKGROUND', (0, -1), (-1, -1), HexColor('#FFD700')),
        ]))
        elements.append(totais_table)

        # Observações
        if contrato.get('observacoes'):
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph('<b>OBSERVAÇÕES:</b>', styles['Heading3']))
            elements.append(Paragraph(contrato['observacoes'], styles['Normal']))

        # Termos e condições
        elements.append(Spacer(1, 1*cm))
        elements.append(Paragraph('<b>TERMOS E CONDIÇÕES</b>', styles['Heading3']))
        termos = """Este contrato estabelece os serviços e produtos acordados entre as partes.
        O cliente declara estar ciente dos valores e condições apresentados.
        A BIOMA se compromete a prestar os serviços com excelência e profissionalismo."""
        elements.append(Paragraph(termos, styles['Normal']))

        # Gerar PDF
        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"contrato_{contrato.get('numero', id)}.pdf"
        )

    except Exception as e:
        logger.error(f"Erro ao gerar PDF de contrato: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/contratos/<id>/whatsapp', methods=['GET'])
