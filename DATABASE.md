# Banco de dados no GitHub (estrutura)

## Arquivos-base
- `data/extracted_blog/posts.json`
  - Dataset completo: titulo, data, labels, URL original, HTML e texto limpo.
- `data/extracted_blog/search-index.json`
  - Dataset otimizado para busca no frontend.
- `data/extracted_blog/posts.csv`
  - Versao tabular para planilhas/BI.

## Como consultar como "DB"
1. Frontend statico: consumir `search-index.json`.
2. Integracoes: consumir `posts.json`.
3. Analise externa: usar `posts.csv`.

## Vantagem
Sem servidor backend: o proprio repositorio funciona como armazenamento versionado.
