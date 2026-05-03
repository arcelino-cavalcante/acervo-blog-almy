#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Uso: $0 <repo-url-git> [branch]"
  echo "Exemplo: $0 https://github.com/SEU_USUARIO/SEU_REPO.git main"
  exit 1
fi

REPO_URL="$1"
BRANCH="${2:-main}"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  git init
fi

git checkout -B "$BRANCH"
git add .

if git diff --cached --quiet; then
  echo "Nada novo para commit."
else
  git commit -m "Acervo completo: PDFs, buscador offline e deploy GitHub Pages"
fi

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REPO_URL"
else
  git remote add origin "$REPO_URL"
fi

git push -u origin "$BRANCH"

echo
echo "Publicacao enviada com sucesso."
echo "Ative o Pages em: Settings > Pages > Source: GitHub Actions"
