#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de Normalização de Colunas para Importação de Serviços
Testa se as colunas da planilha estão sendo detectadas corretamente
"""

import unicodedata
import re

def normalizar_coluna(texto):
    """Normalização extrema de nomes de colunas para máxima compatibilidade"""
    if not texto:
        return ''

    # Converter para string
    texto = str(texto)

    # Remover acentos (NFD = Canonical Decomposition)
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(char for char in texto if unicodedata.category(char) != 'Mn')

    # Converter para lowercase
    texto = texto.lower()

    # Remover caracteres especiais, manter apenas alfanuméricos e underscores
    texto = re.sub(r'[^a-z0-9_]', '', texto)

    # Remover espaços/underscores duplicados
    texto = re.sub(r'_+', '_', texto)

    # Remover underscores no início/fim
    texto = texto.strip('_')

    return texto


# Testar com colunas que o usuário pode ter
colunas_teste = [
    # Tamanhos do usuário
    'Kids',
    'Masculino',
    'Curto',
    'Médio',
    'Longo',
    'Extra Longo',

    # Variações possíveis
    'P',
    'M',
    'G',
    'GG',
    'Preço Kids',
    'Preço Masculino',
    'Preço Curto',
    'Preço Médio',
    'Preço Longo',
    'Preço Extra Longo',

    # Com acentos
    'Preço',
    'Preço P',
    'Preço M',
    'Preço G',
    'Preço GG',
]

print("=" * 80)
print("TESTE DE NORMALIZAÇÃO DE COLUNAS")
print("=" * 80)

for coluna in colunas_teste:
    normalizado = normalizar_coluna(coluna)
    print(f"{coluna:25} -> {normalizado}")

print("\n" + "=" * 80)
print("TESTE DE DETECÇÃO DE TAMANHOS")
print("=" * 80)

# Simular a detecção v7.2 - Ordem importa! (extra_longo ANTES de longo)
from collections import OrderedDict
tamanhos_patterns = OrderedDict([
    ('extra_longo', ['extralongo', 'extra_longo', 'extralong', 'extra_long', 'extralarge', 'extra_large', 'muitolongo']),
    ('kids', ['kids', 'crianca', 'infantil', 'child', 'kid', 'bebe']),
    ('masculino', ['masculino', 'male', 'homem', 'masc', 'barba', 'beard']),
    ('curto', ['curto', 'short', 'pequeno', 'mini', 'small']),
    ('medio', ['medio', 'medium', 'media', 'normal']),
    ('longo', ['longo', 'long', 'grande', 'large', 'big']),
])

tamanhos_letras = {
    'curto': ['p', 's'],
    'medio': ['m'],
    'longo': ['g', 'l'],
    'extra_longo': ['gg', 'xl', 'xxl']
}

def detectar_tamanho(coluna_original):
    """Detecta o tamanho baseado na coluna v7.2 - ORDEM CORRIGIDA"""
    coluna_normalizada = normalizar_coluna(coluna_original)

    tamanho_detectado = None
    metodo = None

    # 1. Letra exata (P, M, G, GG, etc)
    if len(coluna_normalizada) <= 3:
        for tam, letras in tamanhos_letras.items():
            if coluna_normalizada in letras:
                tamanho_detectado = tam
                metodo = "letra exata"
                break

    # 2. PADRÃO TEXTUAL (ANTES de "termina com" para evitar "kids" -> "curto")
    if not tamanho_detectado:
        for tam, patterns in tamanhos_patterns.items():
            for pattern in patterns:
                pattern_norm = normalizar_coluna(pattern)
                # v7.2: Match unidirecional para evitar "longo" in "extralongo"
                if pattern_norm in coluna_normalizada:
                    tamanho_detectado = tam
                    metodo = "padrao textual"
                    break
            if tamanho_detectado:
                break

    # 3. TERMINA COM (ÚLTIMA PRIORIDADE)
    if not tamanho_detectado and len(coluna_normalizada) > 1:
        ultima_letra = coluna_normalizada[-1]
        if ultima_letra in ['p', 's']:
            tamanho_detectado = 'curto'
            metodo = "termina com"
        elif ultima_letra == 'm':
            tamanho_detectado = 'medio'
            metodo = "termina com"
        elif ultima_letra in ['g', 'l']:
            tamanho_detectado = 'longo'
            metodo = "termina com"

        if not tamanho_detectado and len(coluna_normalizada) >= 2:
            ultimas_duas = coluna_normalizada[-2:]
            if ultimas_duas in ['gg', 'xl']:
                tamanho_detectado = 'extra_longo'
                metodo = "termina com"

    return tamanho_detectado, metodo

# Testar detecção
for coluna in colunas_teste:
    tamanho, metodo = detectar_tamanho(coluna)
    if tamanho:
        print(f"{coluna:25} -> {tamanho:15} (metodo: {metodo})")
    else:
        print(f"{coluna:25} -> NAO DETECTADO")

print("\n" + "=" * 80)
print("RESULTADO DO TESTE")
print("=" * 80)

# Verificar se todos os tamanhos do usuário foram detectados
tamanhos_usuario = ['Kids', 'Masculino', 'Curto', 'Médio', 'Longo', 'Extra Longo']
print("\nTamanhos do usuário:")
for tam in tamanhos_usuario:
    detectado, metodo = detectar_tamanho(tam)
    if detectado:
        print(f"  OK {tam:15} -> {detectado:15}")
    else:
        print(f"  ERRO {tam:15} -> NAO DETECTADO")

print("\n" + "=" * 80)
