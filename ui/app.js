const { createElement: h, useEffect, useState } = React;
const { createRoot } = ReactDOM;
const { BrowserRouter, Routes, Route, Link, useSearchParams } = ReactRouterDOM;

async function postJSON(path, body) {
  const res = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function Nav() {
  return h('nav', { className: 'bg-white shadow mb-6' },
    h('div', { className: 'max-w-5xl mx-auto px-4 py-3 flex gap-4' },
      h(Link, { to: '/admin', className: 'text-blue-600' }, 'Admin'),
      h(Link, { to: '/explore/graph', className: 'text-blue-600' }, 'Explore Graph'),
      h(Link, { to: '/learn/roadmap?domain=python', className: 'text-blue-600' }, 'Learn Roadmap')
    )
  );
}

function AdminPage() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await postJSON('/v1/search/graph', { cypher: 'MATCH (doc:Document) RETURN doc.id as id, doc.title as title ORDER BY doc.id LIMIT 100' });
        const rows = data.rows || [];
        const cols = data.columns || [];
        const idIdx = cols.indexOf('id');
        const titleIdx = cols.indexOf('title');
        const list = rows.map(r => ({ id: r[idIdx], title: r[titleIdx], status: 'unknown' }));
        setDocs(list);
      } catch (e) { setError(String(e)); }
      finally { setLoading(false); }
    })();
  }, []);

  async function rerun(id) {
    try {
      await fetch(`/admin/ingest/${id}/rerun`, { method: 'POST' });
      setDocs(docs => docs.map(d => d.id === id ? { ...d, status: 'queued' } : d));
    } catch (e) { console.error(e); }
  }

  if (loading) return h('div', { className: 'p-4' }, 'Loading...');
  if (error) return h('div', { className: 'p-4 text-red-600' }, error);
  return h('div', { className: 'max-w-5xl mx-auto px-4' },
    h('h1', { className: 'text-2xl font-semibold mb-4' }, 'Ingestion Jobs'),
    h('table', { className: 'w-full bg-white shadow rounded' },
      h('thead', { className: 'bg-gray-100' }, h('tr', null,
        h('th', { className: 'p-2 text-left' }, 'ID'),
        h('th', { className: 'p-2 text-left' }, 'Title'),
        h('th', { className: 'p-2 text-left' }, 'Status'),
        h('th', { className: 'p-2 text-left' }, 'Actions'),
      )),
      h('tbody', null,
        docs.map(d => h('tr', { key: d.id, className: 'border-b' },
          h('td', { className: 'p-2 text-xs' }, d.id),
          h('td', { className: 'p-2' }, d.title),
          h('td', { className: 'p-2' }, d.status),
          h('td', { className: 'p-2' }, h('button', { className: 'px-3 py-1 bg-blue-600 text-white rounded', onClick: () => rerun(d.id) }, 'Re-run'))
        ))
      )
    )
  );
}

function ExploreGraphPage() {
  const [cypher, setCypher] = useState('MATCH (t:Topic)-[:REFINES]->(d:Domain) RETURN t.name, d.name LIMIT 50');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  async function run() {
    setError(null);
    try { setResult(await postJSON('/v1/search/graph', { cypher })); }
    catch (e) { setError(String(e)); }
  }
  return h('div', { className: 'max-w-5xl mx-auto px-4' },
    h('h1', { className: 'text-2xl font-semibold mb-4' }, 'Explore Graph'),
    h('textarea', { className: 'border p-2 w-full h-32', value: cypher, onChange: e => setCypher(e.target.value) }),
    h('div', { className: 'mt-3' },
      h('button', { className: 'px-3 py-1 bg-blue-600 text-white rounded', onClick: run }, 'Run')
    ),
    error ? h('div', { className: 'text-red-600 mt-2' }, error) : null,
    h('pre', { className: 'mt-4 text-xs overflow-auto bg-white p-3 rounded shadow' }, result ? JSON.stringify(result, null, 2) : 'Run a query to see results')
  );
}

function LearnRoadmapPage() {
  const [params] = useSearchParams();
  const domain = params.get('domain') || 'python';
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`/v1/roadmaps/${encodeURIComponent(domain)}`);
        if (!res.ok) throw new Error(await res.text());
        setData(await res.json());
      } catch (e) { setError(String(e)); }
    })();
  }, [domain]);
  const weeks = {};
  (data?.nodes || []).forEach(n => { (weeks[n.week] ||= []).push(n); });
  return h('div', { className: 'max-w-5xl mx-auto px-4' },
    h('h1', { className: 'text-2xl font-semibold mb-4' }, `Roadmap: ${domain}`),
    error ? h('div', { className: 'text-red-600' }, error) : null,
    ...Object.keys(weeks).sort((a,b)=>a-b).map(w => h('div', { key: w, className: 'mb-4' },
      h('h2', { className: 'text-xl mb-2' }, `Week ${w}`),
      h('ul', { className: 'list-disc ml-6' }, weeks[w].map(n => h('li', { key: n.id }, `${n.label} `, h('span', { className: 'text-gray-500 text-sm' }, `(${n.hours}h)`))))
    ))
  );
}

function App() {
  return h(BrowserRouter, null,
    h(Nav, null),
    h('main', null,
      h(Routes, null,
        h(Route, { path: '/admin', element: h(AdminPage) }),
        h(Route, { path: '/explore/graph', element: h(ExploreGraphPage) }),
        h(Route, { path: '/learn/roadmap', element: h(LearnRoadmapPage) }),
        h(Route, { path: '*', element: h('div', { className: 'p-4' }, 'Welcome. Use the nav to explore.') })
      )
    )
  );
}

const root = createRoot(document.getElementById('root'));
root.render(h(App));

