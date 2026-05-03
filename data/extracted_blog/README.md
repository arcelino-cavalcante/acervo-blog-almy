# Extracao do blog almyalves.blogspot.com

Total de posts extraidos: **2387**
Periodo encontrado: **2013-01-31T11:42:00.002-03:00** ate **2026-05-03T07:34:00.001-03:00**

## Arquivos gerados

- `posts.json`: dataset completo com conteudo HTML e texto limpo.
- `posts.csv`: inventario tabular dos artigos.
- `posts/<ano>/<mes>/*.md`: um markdown por artigo.
- `pdfs/<ano>/<mes>/*.pdf`: um PDF por artigo.
- `search-index.json`: indice usado pela busca offline.
- `viewer/`: app local offline para pesquisar e abrir os arquivos.

## Anos encontrados

2013, 2014, 2015, 2020, 2021, 2022, 2023, 2024, 2025, 2026

## Como abrir o sistema local offline

1. No terminal, entre na pasta do projeto:
   `cd /Users/arc/Documents/New project 2`
2. Inicie um servidor local simples:
   `python3 -m http.server 8000`
3. Abra no navegador:
   `http://localhost:8000/data/extracted_blog/viewer/`
