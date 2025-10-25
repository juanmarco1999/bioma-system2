#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Orcamentos Routes
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

from app.orcamentos import bp
from app.decorators import login_required, permission_required, get_user_permissions
from app.utils import convert_objectid, allowed_file, registrar_auditoria
from app.extensions import db as get_db, get_from_cache, set_in_cache

logger = logging.getLogger(__name__)

@bp.route('/api/orcamento/<id>/pdf')
@login_required
def gerar_pdf_orcamento_singular(id):
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    try:
        orcamento = db.orcamentos.find_one({'_id': ObjectId(id)})
        if not orcamento:
            return jsonify({'success': False, 'message': 'Orçamento não encontrado'}), 404

        buffer = io.BytesIO()
        doc_width, doc_height = A4
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=1.5*cm, bottomMargin=2.5*cm)

        COLOR_PRIMARY = HexColor('#7C3AED')
        COLOR_SECONDARY = HexColor('#6B7280')
        COLOR_LIGHT_BG = HexColor('#F9FAFB')
        COLOR_WHITE = HexColor('#FFFFFF')
        
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='MainTitle', fontName='Helvetica-Bold', fontSize=20, textColor=COLOR_PRIMARY, spaceAfter=18))
        styles.add(ParagraphStyle(name='SubTitle', fontName='Helvetica', fontSize=10, textColor=COLOR_SECONDARY, spaceAfter=24))
        styles.add(ParagraphStyle(name='SectionTitle', fontName='Helvetica-Bold', fontSize=10, textColor=white))
        styles.add(ParagraphStyle(name='Body', fontName='Helvetica', fontSize=9, leading=14))
        styles.add(ParagraphStyle(name='BodyRight', fontName='Helvetica', fontSize=9, leading=14, alignment=TA_RIGHT))
        styles.add(ParagraphStyle(name='Clause', fontName='Helvetica', fontSize=8, leading=14, alignment=TA_JUSTIFY, leftIndent=12))
        styles.add(ParagraphStyle(name='Signature', fontName='Helvetica', fontSize=9, alignment=TA_CENTER))

        story = []
        
        story.append(GradientHeader(doc_width - 4*cm, "BIOMA"))
        story.append(Spacer(1, 1.5*cm))
        story.append(Paragraph("Contrato de Prestação de Serviços", styles['MainTitle']))
        story.append(Paragraph(
            "Pelo presente instrumento particular, as 'Partes' resolvem celebrar o presente 'Contrato', de acordo com as cláusulas e condições a seguir.", 
            styles['SubTitle']
        ))

        data_contrato = orcamento.get('created_at', datetime.now())
        info_data = [
            [Paragraph('<b>NÚMERO DO CONTRATO</b>', styles['Body']), Paragraph(f"#{orcamento.get('numero', 'N/A')}", styles['Body'])],
            [Paragraph('<b>DATA DE EMISSÃO</b>', styles['Body']), Paragraph(format_date_pt_br(data_contrato), styles['Body'])]
        ]
        story.append(Table(info_data, colWidths=[5*cm, '*'], style=[('VALIGN', (0,0), (-1,-1), 'TOP')]))
        story.append(Spacer(1, 1*cm))

        story.append(HRFlowable(doc_width - 4*cm, color=HexColor('#E5E7EB'), thickness=1))
        story.append(Spacer(1, 1*cm))

        contratante_details = f"""
            <b>Nome:</b> {orcamento.get('cliente_nome', 'N/A')}<br/>
            <b>CPF:</b> {orcamento.get('cliente_cpf', 'N/A')}<br/>
            <b>Telefone:</b> {orcamento.get('cliente_telefone', 'N/A')}<br/>
            <b>E-mail:</b> {orcamento.get('cliente_email', 'N/A')}
        """
        contratada_details = f"""
            <b>Razão Social:</b> BIOMA UBERABA<br/>
            <b>CNPJ:</b> 49.470.937/0001-10<br/>
            <b>Endereço:</b> Av. Santos Dumont 3110, Santa Maria, Uberaba/MG<br/>
            <b>Contato:</b> (34) 99235-5890
        """
        partes_data = [
            [Paragraph('<b>CONTRATANTE</b>', styles['Body']), Paragraph('<b>CONTRATADA</b>', styles['Body'])],
            [Paragraph(contratante_details, styles['Body']), Paragraph(contratada_details, styles['Body'])]
        ]
        partes_table = Table(partes_data, colWidths=['*', '*'], hAlign='LEFT')
        partes_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'), ('LINEBELOW', (0,0), (-1,0), 1, COLOR_PRIMARY),
            ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ]))
        story.append(partes_table)
        story.append(Spacer(1, 1.5*cm))

        story.append(Paragraph("SERVIÇOS E PRODUTOS CONTRATADOS", styles['MainTitle']))
        table_header = [Paragraph(c, styles['SectionTitle']) for c in ['Item', 'Descrição', 'Qtd', 'Vl. Unit.', 'Total']]
        items_data = [table_header]
        all_items = orcamento.get('servicos', []) + orcamento.get('produtos', [])
        
        table_style_commands = [
            ('BACKGROUND', (0,0), (-1,0), COLOR_PRIMARY), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 10), ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('GRID', (0,0), (-1,-1), 1, COLOR_PRIMARY),
            ('ALIGN', (2,1), (-1,-1), 'RIGHT'), # Alinha colunas numéricas à direita
            ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]

        for i, item in enumerate(all_items):
            desc = f"{item.get('nome', '')} {item.get('tamanho', '')}".strip() if 'servico' in item.get('id', '') else f"{item.get('nome', '')} {item.get('marca', '')}".strip()
            items_data.append([
                Paragraph(str(i+1), styles['Body']), Paragraph(desc, styles['Body']),
                Paragraph(str(item.get('qtd', 1)), styles['BodyRight']), 
                Paragraph(f"R$ {item.get('preco_unit', 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), styles['BodyRight']),
                Paragraph(f"R$ {item.get('total', 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), styles['BodyRight']),
            ])
            # Adiciona estilo de zebra (cores alternadas)
            if i % 2 == 0:
                table_style_commands.append(('BACKGROUND', (0, i + 1), (-1, i + 1), COLOR_LIGHT_BG))
            else:
                table_style_commands.append(('BACKGROUND', (0, i + 1), (-1, i + 1), COLOR_WHITE))

        items_table = Table(items_data, colWidths=[1.5*cm, '*', 1.5*cm, 3*cm, 3*cm], repeatRows=1)
        items_table.setStyle(TableStyle(table_style_commands))
        story.append(items_table)
        story.append(Spacer(1, 1*cm))

        subtotal = orcamento.get('subtotal', 0)
        desconto = orcamento.get('desconto_valor', 0)
        total = orcamento.get('total_final', 0)
        pag_tipo = orcamento.get('pagamento', {}).get('tipo', 'Não especificado')
        
        valores_data = [
            [Paragraph('Subtotal:', styles['Body']), Paragraph(f'R$ {subtotal:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."), styles['BodyRight'])],
            [Paragraph('Desconto Global:', styles['Body']), Paragraph(f'R$ {desconto:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."), styles['BodyRight'])],
            ['', HRFlowable(8*cm, color=COLOR_PRIMARY, thickness=1.5)],
            [Paragraph('<b>Valor Total a Pagar:</b>', styles['Body']), Paragraph(f'<b>R$ {total:,.2f}</b>'.replace(",", "X").replace(".", ",").replace("X", "."), styles['BodyRight'])],
            [Paragraph('Forma de Pagamento:', styles['Body']), Paragraph(pag_tipo, styles['BodyRight'])],
        ]
        
        # Tabela para alinhar o bloco de valores à direita
        container_valores = Table([[Table(valores_data, colWidths=[4*cm, 4*cm])]], colWidths=[doc_width-4*cm])
        container_valores.setStyle(TableStyle([('ALIGN', (0,0), (0,0), 'RIGHT')]))
        story.append(container_valores)
        story.append(Spacer(1, 1.5*cm))

        story.append(Paragraph("DISPOSIÇÕES GERAIS E CLÁUSULAS", styles['MainTitle']))
        clausulas = [
            "O Contrato tem por objeto a prestação de serviços acima descritos, pela Contratada à Contratante, mediante agendamento prévio. A Contratada utilizará produtos com ingredientes naturais para a saúde dos cabelos, de alta qualidade, que serão manipulados dentro das normas de higiene e limpeza exigidas pela Vigilância Sanitária.",
            "A Contratante declara e está ciente que (i) os serviços têm caráter pessoal e são intransferíveis; (ii) só poderá alterar os Serviços contratados com a anuência da Contratada e desde que a utilização seja no prazo originalmente contratado; (iii) não tem nenhum impedimento médico e/ou alergias que impeçam de realizar os serviços contratados; (iv) escolheu os tratamentos de acordo com o seu tipo de cabelo; (v) concorda em realizar os tratamentos com a frequência indicada pela Contratada; e (vi) o resultado pretendido depende do respeito à frequência indicada pela Contratada.",
            "Os serviços deverão ser utilizados em conformidade com o prazo de 18 (dezoito) meses e a Contratante está ciente de que não haverá prorrogação do prazo previsto para a utilização dos serviços, ou seja, ao final de 18 (dezoito) meses, o Contrato será extinto e a Contratante não terá direito ao reembolso de tratamentos não realizados no prazo contratual.",
            "A Contratante poderá desistir dos serviços no prazo de até 90 (noventa) dias a contar da assinatura deste Contrato e, neste caso, está de acordo com a restituição do valor equivalente a 80% (oitenta por cento) dos tratamentos não realizados, no prazo de até 5 (cinco) dias úteis da desistência. Eventuais descontos ou promoções nos valores dos serviços e/ou tratamentos não serão reembolsáveis.",
            "No caso de devolução de valor pago por cartão de crédito, o cancelamento será efetuado junto à administradora do seu cartão e o estorno poderá ocorrer em até 2 (duas) faturas posteriores de acordo com procedimentos internos da operadora do cartão de crédito, ou outro prazo definido pela administradora do cartão de crédito, ou, a exclusivo arbítrio da Contratada, mediante transferência direta do valor equivalente ao reembolso.",
            "Na hipótese de responsabilidade civil da Contratada, independentemente da natureza do dano, fica desde já limitada a responsabilidade da Contratada ao valor máximo equivalente a 2 (duas) sessões de tratamento dos serviços.",
            "No caso de alergias decorrentes dos produtos utilizados pela Contratada, a Contratante poderá optar pela suspensão dos serviços com a retomada após o reestabelecimento de sua saúde, ou pela concessão de crédito do valor remanescente em outros serviços junto à Contratada. A Contratada não é responsável por qualquer perda, independentemente do valor, incluindo danos diretos, indiretos, à imagem, lucros cessantes e/ou morais que se tornem exigíveis em decorrência de eventual alergia.",
            "As Partes se comprometem a tratar apenas os dados pessoais estritamente necessários para atingir as finalidades específicas do objeto do Contrato, em cumprimento ao disposto na Lei nº 13.709/2018 (\"LGPD\") e na regulamentação aplicável.",
            "Fica eleito o Foro da Comarca de UBERABA, Estado de MINAS GERAIS, como o competente para dirimir as dúvidas e controvérsias decorrentes do presente Contrato, com renúncia a qualquer outro, por mais privilegiado que seja.",
            "Este Contrato poderá ser assinado e entregue eletronicamente e terá a mesma validade e efeitos de um documento original com assinaturas físicas."
        ]
        for i, clausula in enumerate(clausulas):
            story.append(Paragraph(f"<b>{i+1}.</b> {clausula}", styles['Clause']))
            story.append(Spacer(1, 0.4*cm))
        
        story.append(PageBreak())
        story.append(Paragraph("ASSINATURAS", styles['MainTitle']))
        story.append(Spacer(1, 4*cm))

        assinatura_contratante = Paragraph("________________________________________<br/><b>CONTRATANTE</b><br/>" + orcamento.get('cliente_nome', 'N/A'), styles['Signature'])
        assinatura_contratada = Paragraph("________________________________________<br/><b>CONTRATADA</b><br/>BIOMA UBERABA", styles['Signature'])
        
        assinaturas_table = Table([[assinatura_contratante, assinatura_contratada]], colWidths=['*', '*'])
        story.append(assinaturas_table)
        
        def on_each_page(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(COLOR_SECONDARY)
            page_num = canvas.getPageNumber()
            canvas.drawCentredString(doc_width/2, 1.5*cm, f"Página {page_num} | Contrato BIOMA Uberaba")
            canvas.restoreState()

        doc.build(story, onFirstPage=on_each_page, onLaterPages=on_each_page)
        
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'contrato_bioma_{orcamento.get("numero")}.pdf')
        
    except Exception as e:
        logger.error(f"❌ PDF error: {e}")
        return jsonify({'success': False, 'message': f'Erro interno ao gerar PDF: {e}'}), 500

# --- FIM DA SEÇÃO MODIFICADA ---


@bp.route('/api/contratos')


@bp.route('/api/orcamentos', methods=['GET', 'POST'])
@login_required
def handle_orcamentos():
    """Gerenciar orçamentos com suporte a múltiplos profissionais"""
    if db is None:
        return jsonify({'success': False, 'message': 'Database offline'}), 500
    
    try:
        if request.method == 'GET':
            # Listar orçamentos
            orcamentos = list(db.orcamentos.find().sort('created_at', DESCENDING).limit(100))
            for orc in orcamentos:
                orc['_id'] = str(orc['_id'])
                if 'created_at' in orc and isinstance(orc['created_at'], datetime):
                    orc['created_at'] = orc['created_at'].isoformat()
                # Converter ObjectIds dos profissionais vinculados
                if 'profissionais_vinculados' in orc:
                    for prof in orc['profissionais_vinculados']:
                        if 'profissional_id' in prof and isinstance(prof['profissional_id'], ObjectId):
                            prof['profissional_id'] = str(prof['profissional_id'])
            
            logger.info(f"📊 Listando {len(orcamentos)} orçamentos")
            return jsonify({'success': True, 'orcamentos': orcamentos})
        
        elif request.method == 'POST':
            # Criar novo orçamento
            data = request.json
            logger.info(f"💼 Criando orçamento para cliente: {data.get('cliente_nome')}")
            
            # Processar profissionais vinculados
            profissionais_vinculados = data.get('profissionais_vinculados', [])
            for prof in profissionais_vinculados:
                if 'profissional_id' in prof and isinstance(prof['profissional_id'], str):
                    try:
                        prof['profissional_id'] = ObjectId(prof['profissional_id'])
                    except:
                        pass
            
            # Gerar número do orçamento
            ultimo_orc = db.orcamentos.find_one(sort=[('numero', DESCENDING)])
            proximo_numero = (ultimo_orc.get('numero', 0) + 1) if ultimo_orc else 1
            
            orcamento = {
                'numero': proximo_numero,
                'cliente_cpf': data.get('cliente_cpf'),
                'cliente_nome': data.get('cliente_nome'),
                'cliente_telefone': data.get('cliente_telefone'),
                'cliente_email': data.get('cliente_email'),
                'servicos': data.get('servicos', []),
                'produtos': data.get('produtos', []),
                'profissionais_vinculados': profissionais_vinculados,
                'total_servicos': data.get('total_servicos', 0),
                'total_produtos': data.get('total_produtos', 0),
                'desconto_perc': data.get('desconto_perc', 0),
                'desconto_valor': data.get('desconto_valor', 0),
                'total_final': data.get('total_final', 0),
                'total_comissoes': sum(p.get('comissao_valor', 0) for p in profissionais_vinculados),
                'forma_pagamento': data.get('forma_pagamento'),
                'observacoes': data.get('observacoes', ''),
                'status': data.get('status', 'Pendente'),
                'created_at': datetime.now(),
                'created_by': session.get('username')
            }
            
            result = db.orcamentos.insert_one(orcamento)
            orcamento['_id'] = str(result.inserted_id)

            # Update cliente denormalized fields for performance
            if orcamento.get('cliente_cpf'):
                update_cliente_denormalized_fields(orcamento['cliente_cpf'])

            # Registrar comissões no histórico
            if profissionais_vinculados:
                for prof in profissionais_vinculados:
                    db.comissoes_historico.insert_one({
                        'orcamento_id': result.inserted_id,
                        'profissional_id': prof.get('profissional_id'),
                        'nome': prof.get('nome'),
                        'tipo': prof.get('tipo'),
                        'comissao_perc': prof.get('comissao_perc'),
                        'comissao_valor': prof.get('comissao_valor'),
                        'valor_base': data.get('total_servicos', 0),
                        'status_orcamento': orcamento['status'],
                        'data_registro': datetime.now()
                    })
            
            logger.info(f"✅ Orçamento #{proximo_numero} criado com {len(profissionais_vinculados)} profissionais")
            return jsonify({'success': True, 'orcamento': orcamento, 'numero': proximo_numero})
            
    except Exception as e:
        logger.error(f"❌ Erro em handle_orcamentos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/api/orcamentos/<id>', methods=['GET', 'PUT', 'DELETE'])


@bp.route('/api/orcamentos/<id>/pdf', methods=['GET'])
@login_required
def gerar_pdf_orcamento(id):
    """Gerar PDF de orçamento para impressão (Diretriz #3)"""
    if db is None:
        return jsonify({'success': False}), 500

    try:
        orcamento = db.orcamentos.find_one({'_id': ObjectId(id)})
        if not orcamento:
            return jsonify({'success': False, 'message': 'Orçamento não encontrado'}), 404

        # Criar buffer para o PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        # Título
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=TA_CENTER)
        elements.append(Paragraph(f"ORÇAMENTO #{orcamento.get('numero', str(orcamento['_id'])[-6:])}", title_style))
        elements.append(Spacer(1, 0.3*cm))

        # Informações do cliente
        elements.append(Paragraph('<b>DADOS DO CLIENTE</b>', styles['Heading2']))
        cliente_data = [
            ['Nome:', orcamento.get('cliente_nome', 'N/A')],
            ['CPF:', orcamento.get('cliente_cpf', 'N/A')],
            ['Telefone:', orcamento.get('cliente_telefone', 'N/A')],
            ['Email:', orcamento.get('cliente_email', 'N/A')],
            ['Data:', orcamento.get('created_at', datetime.now()).strftime('%d/%m/%Y') if isinstance(orcamento.get('created_at'), datetime) else 'N/A']
        ]
        cliente_table = Table(cliente_data, colWidths=[4*cm, 12*cm])
        cliente_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f0f0f0')),
            ('GRID', (0, 0), (-1, -1), 0.5, black),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        elements.append(cliente_table)
        elements.append(Spacer(1, 0.5*cm))

        # Serviços
        if orcamento.get('servicos'):
            elements.append(Paragraph('<b>SERVIÇOS</b>', styles['Heading2']))
            servicos_data = [['Descrição', 'Quantidade', 'Valor Unit.', 'Total']]
            for srv in orcamento['servicos']:
                servicos_data.append([
                    srv.get('nome', 'N/A'),
                    str(srv.get('quantidade', 1)),
                    f"R$ {srv.get('preco', 0):.2f}",
                    f"R$ {srv.get('total', 0):.2f}"
                ])
            servicos_table = Table(servicos_data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
            servicos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#4CAF50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]))
            elements.append(servicos_table)
            elements.append(Spacer(1, 0.3*cm))

        # Produtos
        if orcamento.get('produtos'):
            elements.append(Paragraph('<b>PRODUTOS</b>', styles['Heading2']))
            produtos_data = [['Descrição', 'Quantidade', 'Valor Unit.', 'Total']]
            for prd in orcamento['produtos']:
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
            ['Subtotal Serviços:', f"R$ {orcamento.get('total_servicos', 0):.2f}"],
            ['Subtotal Produtos:', f"R$ {orcamento.get('total_produtos', 0):.2f}"],
            ['Desconto:', f"R$ {orcamento.get('desconto_valor', 0):.2f}"],
            ['<b>TOTAL FINAL:</b>', f"<b>R$ {orcamento.get('total_final', 0):.2f}</b>"]
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
        if orcamento.get('observacoes'):
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph('<b>OBSERVAÇÕES:</b>', styles['Heading3']))
            elements.append(Paragraph(orcamento['observacoes'], styles['Normal']))

        # Gerar PDF
        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"orcamento_{orcamento.get('numero', id)}.pdf"
        )

    except Exception as e:
        logger.error(f"Erro ao gerar PDF de orçamento: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/orcamentos/<id>/whatsapp', methods=['GET'])
