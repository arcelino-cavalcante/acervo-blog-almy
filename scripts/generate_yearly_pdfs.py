import os
import json
from PyPDF2 import PdfMerger

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    index_path = os.path.join(base_dir, 'data', 'extracted_blog', 'search-index.json')
    
    with open(index_path, 'r', encoding='utf-8') as f:
        posts = json.load(f)

    # Sort posts by year and then by published date
    posts.sort(key=lambda x: x.get('published', ''))

    by_year = {}
    for p in posts:
        year = p.get('year')
        if not year:
            continue
        if year not in by_year:
            by_year[year] = []
        
        pdf_path = os.path.join(base_dir, 'data', 'extracted_blog', p['pdf'])
        if os.path.exists(pdf_path):
            by_year[year].append(pdf_path)

    out_dir = os.path.join(base_dir, 'data', 'extracted_blog', 'viewer', 'yearly_pdfs')
    os.makedirs(out_dir, exist_ok=True)

    for year, pdf_list in by_year.items():
        out_path = os.path.join(out_dir, f"{year}.pdf")
        
        # Skip if already exists and up to date? Let's just overwrite for now.
        print(f"Gerando PDF compilado para {year} ({len(pdf_list)} posts)...")
        merger = PdfMerger()
        
        for pdf in pdf_list:
            try:
                merger.append(pdf)
            except Exception as e:
                print(f"  Erro ao adicionar {pdf}: {e}")
                
        try:
            merger.write(out_path)
            merger.close()
            print(f"  -> Salvo: {out_path}")
        except Exception as e:
            print(f"  Erro ao salvar o compilado de {year}: {e}")

if __name__ == '__main__':
    main()
