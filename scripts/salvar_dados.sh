#!/usr/bin/env bash
# Faz um commit no ramo `dados` e envia. Tenta de novo se o ramo andou no meio do caminho.
set -euo pipefail
cd dados
git add -A
if git diff --cached --quiet; then
  echo "Nada novo para salvar."
  exit 0
fi
git commit --quiet -m "${1:-coleta} $(date -u +%Y-%m-%dT%H:%MZ)"
for i in 1 2 3; do
  if git push --quiet origin HEAD:dados; then exit 0; fi
  echo "Push recusado, sincronizando (tentativa $i)..."
  git fetch --quiet --depth 1 origin dados && git rebase --quiet origin/dados || true
  sleep 5
done
echo "Não consegui salvar os dados." >&2
exit 1
