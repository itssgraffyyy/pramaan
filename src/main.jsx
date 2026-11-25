import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

function App() {
  const [data, setData] = useState(null), [record, setRecord] = useState(null);
  const [error, setError] = useState(''), [loading, setLoading] = useState(false);
  async function loadDemo() {
    setLoading(true); setError(''); setRecord(null);
    try { const r = await fetch('/api/v1/demo'); if (!r.ok) throw Error(`Backend returned ${r.status}`); setData(await r.json()); }
    catch (e) { setError(`Unable to load demo. Check the backend is running. ${e.message}`); }
    finally { setLoading(false); }
  }
  async function openRecord(ref) {
    setError(''); const [digest, row] = ref.split(':');
    try { const r = await fetch(`/api/v1/demo/records/${encodeURIComponent(digest)}/${encodeURIComponent(row)}`); if (!r.ok) throw Error(`Backend returned ${r.status}`); setRecord(await r.json()); }
    catch (e) { setError(`Unable to open source record. ${e.message}`); }
  }
  const refButton = ref => <button className="ref" key={ref} title={ref} onClick={() => openRecord(ref)}>Row {ref.split(':')[1]} ↗</button>;
  return <div className="shell"><aside className="sidebar"><div className="brand"><span className="mark">P</span><div><strong>PRAMAAN</strong><small>Evidence intelligence</small></div></div><div className="side-label">WORKSPACE</div><div className="active">▦ &nbsp; Overview</div><div className="side-note">● &nbsp; SYNTHETIC DEMO<p>Local fixture data only. Real evidence uploads are disabled.</p></div><div className="side-footer">TEAM ARC · PS03</div></aside>
    <div className="content"><header className="topbar"><div>Investigation workspace <span> / </span> <strong>Overview</strong></div><div className="pill">● &nbsp; Synthetic environment</div></header><main>
      <div className="heading"><div><div className="eyebrow">CASE WORKSPACE &nbsp; / &nbsp; SYNTHETIC DEMO</div><h1>Investigation overview</h1><p>Explore computed communication data and trace findings back to source records.</p></div><button className="primary" onClick={loadDemo} disabled={loading}>{loading ? 'Loading…' : data ? '↻ Reload synthetic demo' : '↓ Load synthetic demo'}</button></div>
      <div className="notice"><strong>Synthetic data only</strong><span>This early prototype is not a secure evidence system. Results require human review.</span></div>
      {error && <div className="error" role="alert">{error}</div>}
      {!data ? <section className="empty"><div className="empty-icon">▤</div><h2>Start with a synthetic case</h2><p>Load the bundled sample records to see computed statistics, validation issues, and source references.</p><button className="primary" onClick={loadDemo} disabled={loading}>{loading ? 'Loading…' : 'Load synthetic demo'}</button></section> : <>
        <div className="section-title"><div><h2>Evidence at a glance</h2><p>Computed from bundled sample files</p></div><span className="tag">3 SAMPLE FILES</span></div>
        <div className="stats">{[['Source files',data.totals.files,'CDR and IPDR'],['Original records',data.totals.rows,'Across all files'],['Accepted records',data.totals.accepted,'Available for analysis'],['Quarantined',data.totals.quarantined,'Excluded from analysis']].map(([label,value,note]) => <div className="stat" key={label}><div>{label}</div><strong>{value}</strong><small>{note}</small></div>)}</div>
        <div className="grid"><section className="card"><div className="card-head"><div><h2>Communication activity</h2><p>Accepted CDR rows grouped by direction</p></div><span className="tag">{data.totals.calls} CALL RECORDS</span></div><div className="table-wrap"><table><thead><tr><th>FROM</th><th>TO</th><th>CALLS</th><th>SOURCE RECORDS</th></tr></thead><tbody>{data.contacts.map(c => <tr key={`${c.caller}-${c.callee}`}><td><strong>{c.caller}</strong></td><td>{c.callee}</td><td>{c.calls}</td><td><div className="refs">{c.references.map(refButton)}</div></td></tr>)}</tbody></table></div><div className="card-foot">Repeated records are retained; counts do not establish identity or intent.</div></section>
        <section className="card"><div className="card-head"><div><h2>Validation issues</h2><p>Records that need closer review</p></div><span className="issue-count">{data.issues.length}</span></div><div className="issue-list">{data.issues.length ? data.issues.map((issue,i) => <div className="issue" key={i}><span className="issue-icon">!</span><div><strong>{issue.message.split(':')[0]}</strong><p>{issue.message.split(':').slice(1).join(':').trim()}</p><small>{issue.file} {issue.reference && <>· {refButton(issue.reference)}</>}</small></div></div>) : <p>No issues found.</p>}</div></section></div>
        <section className="card inventory"><div className="card-head"><div><h2>Evidence inventory</h2><p>Integrity checks and row accounting for each sample file</p></div><span className="tag">MAPPING V1</span></div><div className="table-wrap"><table><thead><tr><th>FILE</th><th>FORMAT</th><th>ROWS</th><th>ACCEPTED</th><th>QUARANTINED</th><th>CHECK</th></tr></thead><tbody>{data.inventory.map(f => <tr key={f.name}><td><strong>{f.name}</strong><small className="hash" title={f.sha256}>SHA-256 {f.sha256}</small></td><td>{f.kind.toUpperCase()}</td><td>{f.original}</td><td>{f.accepted}</td><td>{f.quarantined}</td><td><span className="check">{f.verification_issues.length ? 'Issues found' : 'Reconciled'}</span></td></tr>)}</tbody></table></div><div className="card-foot">Reconciliation checks row accounting and mapped fields; it does not prove authenticity.</div></section>
      </>}
      <footer>PRAMAAN · Team ARC · Rajasthan Police Hackathon 2026</footer></main></div>
      {record && <div className="overlay" onClick={() => setRecord(null)}><section className="drawer" role="dialog" aria-modal="true" aria-labelledby="record-title" onClick={e => e.stopPropagation()}><div className="drawer-head"><div><div className="eyebrow">SOURCE EVIDENCE</div><h2 id="record-title">Original record</h2></div><button className="close" aria-label="Close source record" onClick={() => setRecord(null)}>×</button></div><p>Original values from <strong>{record.file}</strong></p><div className="reference-full">{record.reference}</div><dl>{Object.entries(record.fields).map(([key,value]) => <div key={key}><dt>{key}</dt><dd>{String(value ?? '—')}</dd></div>)}</dl><p>Synthetic fixture · Logical CSV row {record.reference.split(':')[1]}</p></section></div>}
    </div>;
}

createRoot(document.getElementById('root')).render(<App />);
