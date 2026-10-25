#!/usr/bin/env bash
# Baixa o ramo `dados` para a pasta ./dados (ou cria o ramo se ainda não existir).
set -euo pipefail
URL="https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"

if git ls-remote --exit-code --heads "$URL" dados >/dev/null 2>&1; then
  git clone --quiet --depth 1 --branch dados "$URL" dados
else
  mkdir -p dados
  git -C dados init --quiet -b dados
  git -C dados remote add origin "$URL"
  printf '# Dados do Sinal do Satoshi\n\nRamo gravado automaticamente a cada 15 minutos. Não editar à mão.\n' > dados/README.md
fi
git -C dados config user.name "sinal-do-satoshi[bot]"
git -C dados config user.email "41898282+github-actions[bot]@users.noreply.github.com"
