#!/bin/bash
# Script para deletar TODOS os serviços via API
# ATENÇÃO: Esta ação NÃO pode ser desfeita!

echo "=========================================="
echo "DELETAR TODOS OS SERVIÇOS - BIOMA"
echo "=========================================="
echo ""
echo "Esta ação vai DELETAR TODOS os serviços cadastrados!"
echo "Você terá que fazer login e confirmar."
echo ""
read -p "Tem certeza? Digite 'SIM' para confirmar: " confirmacao

if [ "$confirmacao" != "SIM" ]; then
    echo "Operação cancelada."
    exit 0
fi

# URL do sistema (ajuste conforme necessário)
URL="https://bioma-system2.vercel.app/api/servicos/deletar-todos"

echo ""
echo "Fazendo requisição DELETE para: $URL"
echo ""

# Fazer requisição (vai exigir autenticação)
curl -X DELETE "$URL" \
  -H "Content-Type: application/json" \
  --cookie-jar cookies.txt \
  --cookie cookies.txt

echo ""
echo "=========================================="
echo "Operação concluída!"
echo "=========================================="
