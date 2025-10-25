#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIOMA v3.7 - Constantes do Sistema
Formulários de Anamnese e Prontuário
"""

ANAMNESE_FORM = [
    {
        'ordem': 1,
        'campo': 'QUAIS SÃO AS COISAS QUE INCOMODAM NO SEU COURO CABELUDO?',
        'tipo': 'select',
        'opcoes': ['Coceira', 'Descamação', 'Oleosidade', 'Sensibilidade', 'Feridas', 'Ardor', 'Outro']
    },
    {
        'ordem': 2,
        'campo': 'QUAIS SÃO AS COISAS QUE INCOMODAM NO COURO CABELUDO?',
        'tipo': 'select',
        'opcoes': ['Ressecamento', 'Queda', 'Quebra', 'Frizz', 'Pontas Duplas', 'Outro']
    },
    {
        'ordem': 3,
        'campo': 'QUAIS PROCESSOS QUÍMICOS VOCÊ JÁ FEZ NO CABELO?',
        'tipo': 'select',
        'opcoes': ['Coloração', 'Descoloração', 'Alisamento', 'Relaxamento', 'Progressiva', 'Botox', 'Nenhum']
    },
    {
        'ordem': 4,
        'campo': 'COM QUE FREQUÊNCIA VOCÊ LAVA O CABELO?',
        'tipo': 'select',
        'opcoes': ['Todos os dias', '3x por semana', '2x por semana', '1x por semana', 'Menos de 1x por semana']
    },
    {
        'ordem': 5,
        'campo': 'JÁ TEVE ANEMIA?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 6,
        'campo': 'ESTÁ COM QUEDA DE CABELO?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 7,
        'campo': 'SE SIM HÁ QUANTO TEMPO?',
        'tipo': 'textarea'
    },
    {
        'ordem': 8,
        'campo': 'TEM ALERGIA A ALGUMA SUBSTÂNCIA?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 9,
        'campo': 'SE SIM, QUAL (SUBSTÂNCIA)?',
        'tipo': 'text'
    },
    {
        'ordem': 10,
        'campo': 'JÁ FOI DIAGNOSTICADO ALGUM TIPO DE ALOPECIA OU CALVÍCIE?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 11,
        'campo': 'TEVE ALGUMA ALTERAÇÃO HORMONAL A MENOS DE UM ANO?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 12,
        'campo': 'JÁ FEZ TRATAMENTO PARA QUEDA?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 14,
        'campo': 'QUAL MARCA DE SHAMPOO E CONDICIONADOR VOCÊ COSTUMA USAR?',
        'tipo': 'text'
    },
    {
        'ordem': 15,
        'campo': 'FAZ USO DE PRODUTOS SEM ENXÁGUE?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 16,
        'campo': 'SE SIM QUAL SEM ENXÁGUE?',
        'tipo': 'text'
    },
    {
        'ordem': 17,
        'campo': 'QUANDO LAVA TEM COSTUME DE SECAR O CABELO?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 18,
        'campo': 'VOCÊ É VEGANO?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 19,
        'campo': 'VOCÊ É CELÍACO?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 20,
        'campo': 'VOCÊ É VEGETARIANO?',
        'tipo': 'radio',
        'opcoes': ['Sim', 'Não']
    },
    {
        'ordem': 21,
        'campo': 'COMO VOCÊ CONHECEU O BIOMA UBERABA?',
        'tipo': 'checkbox',
        'opcoes': ['Redes sociais', 'Indicação', 'Busca no Google', 'Eventos', 'Passagem em frente', 'Outro']
    }
]

PRONTUARIO_FORM = [
    {'ordem': 1, 'campo': 'Alquimia', 'tipo': 'text'},
    {'ordem': 2, 'campo': 'Protocolo Adotado', 'tipo': 'textarea'},
    {'ordem': 3, 'campo': 'Técnicas Complementares', 'tipo': 'textarea'},
    {'ordem': 4, 'campo': 'Produtos Utilizados', 'tipo': 'textarea'},
    {'ordem': 5, 'campo': 'Valor Cobrado', 'tipo': 'text'},
    {'ordem': 6, 'campo': 'Observações Durante o Atendimento', 'tipo': 'textarea'},
    {'ordem': 7, 'campo': 'Vendas', 'tipo': 'text'}
]


def default_form_state(definition):
    """Criar estado padrão do formulário"""
    return {item['campo']: '' for item in definition}
