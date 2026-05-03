# Publicar no GitHub Pages

Este projeto ja esta pronto para hospedagem estatica.

## Conteudo pronto
- `data/extracted_blog/pdfs/` (2.387 PDFs)
- `data/extracted_blog/search-index.json`
- `data/extracted_blog/viewer/` (busca offline)
- `index.html` na raiz (atalho para o viewer)
- `.nojekyll` (evita processamento Jekyll)

## Como publicar
1. Crie um repositorio no GitHub e envie os arquivos.
2. No GitHub: `Settings` > `Pages`.
3. Em `Build and deployment`, escolha:
   - `Source`: `Deploy from a branch`
   - `Branch`: `main` (ou `master`) / `/ (root)`
4. Salve e aguarde o link do site.

## URL esperada
- Pagina inicial: `https://SEU_USUARIO.github.io/SEU_REPO/`
- Buscador: `https://SEU_USUARIO.github.io/SEU_REPO/data/extracted_blog/viewer/`

## Observacao
Se alterar posts/PDFs no futuro, so fazer novo commit e push que o Pages atualiza.
