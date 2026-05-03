const state = {
  posts: [],
  filtered: [],
  currentPage: 1,
  pageSize: 24,
};

const q = (sel) => document.querySelector(sel);
const resultsEl = q('#results');
const tpl = q('#cardTpl');
const searchInput = q('#searchInput');
const yearFilter = q('#yearFilter');
const monthFilter = q('#monthFilter');
const labelFilter = q('#labelFilter');
const clearBtn = q('#clearBtn');
const countLabel = q('#countLabel');
const pageInfo = q('#pageInfo');
const pageSizeEl = q('#pageSize');
const prevPageBtn = q('#prevPage');
const nextPageBtn = q('#nextPage');
const yearDownloadSection = q('#yearDownloadSection');
const downloadYearBtn = q('#downloadYearBtn');

function normalize(str) {
  return (str || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '');
}

function buildYearOptions(posts) {
  const years = [...new Set(posts.map((p) => p.year))].sort((a, b) => b.localeCompare(a));
  for (const y of years) {
    const opt = document.createElement('option');
    opt.value = y;
    opt.textContent = y;
    yearFilter.appendChild(opt);
  }
}

function buildMonthOptions(posts) {
  const months = [...new Set(posts.map((p) => p.month))]
    .sort((a, b) => a.localeCompare(b));

  for (const m of months) {
    const opt = document.createElement('option');
    opt.value = m;
    opt.textContent = m;
    monthFilter.appendChild(opt);
  }
}

function buildLabelOptions(posts) {
  const labels = new Set();
  for (const post of posts) {
    for (const label of (post.labels || [])) {
      if (label) labels.add(label);
    }
  }

  for (const label of [...labels].sort((a, b) => a.localeCompare(b))) {
    const opt = document.createElement('option');
    opt.value = label;
    opt.textContent = label;
    labelFilter.appendChild(opt);
  }
}

function render(posts) {
  resultsEl.innerHTML = '';
  const frag = document.createDocumentFragment();

  for (const post of posts) {
    const node = tpl.content.cloneNode(true);
    node.querySelector('.title').textContent = post.title;
    node.querySelector('.meta').textContent = `Publicado: ${post.published} | ${post.year}/${post.month}`;
    node.querySelector('.labels').textContent = post.labels?.length
      ? `Labels: ${post.labels.join(', ')}`
      : 'Labels: (nenhuma)';
    node.querySelector('.excerpt').textContent = post.excerpt || '(Sem trecho)';

    node.querySelector('.btn.pdf').href = `../${post.pdf}`;
    node.querySelector('.btn.md').href = `../${post.markdown}`;
    node.querySelector('.btn.original').href = post.url;

    frag.appendChild(node);
  }

  resultsEl.appendChild(frag);
}

function renderPage() {
  const total = state.filtered.length;
  const pages = Math.max(1, Math.ceil(total / state.pageSize));

  if (state.currentPage > pages) state.currentPage = pages;
  if (state.currentPage < 1) state.currentPage = 1;

  const start = (state.currentPage - 1) * state.pageSize;
  const end = start + state.pageSize;
  const pagePosts = state.filtered.slice(start, end);

  render(pagePosts);

  countLabel.textContent = `${total} resultado(s) de ${state.posts.length} posts.`;
  pageInfo.textContent = `Pagina ${state.currentPage} de ${pages}`;
  prevPageBtn.disabled = state.currentPage <= 1;
  nextPageBtn.disabled = state.currentPage >= pages;
}

function applyFilters() {
  const term = normalize(searchInput.value.trim());
  const year = yearFilter.value;
  const month = monthFilter.value;
  const label = labelFilter.value;
  const normalizedLabel = normalize(label);

  state.filtered = state.posts.filter((post) => {
    if (year && post.year !== year) return false;
    if (month && post.month !== month) return false;
    if (label) {
      const hasLabel = (post.labels || []).some((item) => normalize(item) === normalizedLabel);
      if (!hasLabel) return false;
    }
    if (!term) return true;
    return normalize(post.search_text).includes(term);
  });

  if (year) {
    yearDownloadSection.style.display = 'block';
    downloadYearBtn.href = `./yearly_pdfs/${year}.pdf`;
    downloadYearBtn.textContent = `Baixar Compilado de ${year} (Todos os PDFs)`;
  } else {
    yearDownloadSection.style.display = 'none';
  }

  state.currentPage = 1;
  renderPage();
}

async function load() {
  const res = await fetch('../search-index.json');
  const posts = await res.json();
  state.posts = posts;
  state.filtered = posts;

  buildYearOptions(posts);
  buildMonthOptions(posts);
  buildLabelOptions(posts);
  renderPage();
}

searchInput.addEventListener('input', applyFilters);
yearFilter.addEventListener('change', applyFilters);
monthFilter.addEventListener('change', applyFilters);
labelFilter.addEventListener('change', applyFilters);

pageSizeEl.addEventListener('change', () => {
  state.pageSize = Number(pageSizeEl.value) || 24;
  state.currentPage = 1;
  renderPage();
});

prevPageBtn.addEventListener('click', () => {
  state.currentPage -= 1;
  renderPage();
});

nextPageBtn.addEventListener('click', () => {
  state.currentPage += 1;
  renderPage();
});

clearBtn.addEventListener('click', () => {
  searchInput.value = '';
  yearFilter.value = '';
  monthFilter.value = '';
  labelFilter.value = '';
  pageSizeEl.value = String(state.pageSize);
  applyFilters();
});

load().catch((err) => {
  countLabel.textContent = 'Erro ao carregar o indice offline.';
  console.error(err);
});
