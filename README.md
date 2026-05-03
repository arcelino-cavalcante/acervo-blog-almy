# Acervo Blog Almy Alves (Pronto para GitHub Pages)

Este projeto ja esta pronto para publicar no GitHub Pages com deploy automatico.

## O que ja esta pronto
- `data/extracted_blog/pdfs/`: 2.387 PDFs (1 por post)
- `data/extracted_blog/search-index.json`: indice de busca offline
- `data/extracted_blog/posts.json`: base completa dos posts
- `data/extracted_blog/posts.csv`: base tabular
- `data/extracted_blog/viewer/`: sistema local com busca + filtros + paginacao
- `.github/workflows/deploy-pages.yml`: deploy automatico no Pages
- `.nojekyll`: evita problemas de build Jekyll

## Como publicar (2 minutos)
1. Crie um repositorio no GitHub.
2. Envie estes arquivos para a branch `main`.
3. No GitHub: `Settings > Pages`.
4. Em `Source`, escolha `GitHub Actions`.
5. Pronto: a cada push na `main`, publica automaticamente.

Ou use o script pronto:
- `./scripts/publish_to_github.sh https://github.com/SEU_USUARIO/SEU_REPO.git main`

## URL do site
- Home: `https://SEU_USUARIO.github.io/SEU_REPO/`
- Buscador: `https://SEU_USUARIO.github.io/SEU_REPO/data/extracted_blog/viewer/`

## "Banco de dados" no GitHub
Voce pode tratar estes arquivos como banco de dados estatico:
- JSON principal: `data/extracted_blog/posts.json`
- JSON para busca: `data/extracted_blog/search-index.json`
- CSV para analise: `data/extracted_blog/posts.csv`

Esses arquivos podem ser lidos diretamente por qualquer app/web via URL crua do GitHub (raw) ou pelo proprio Pages.
