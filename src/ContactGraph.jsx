import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';

export default function ContactGraph({ nodes, edges, onSource }) {
  const container = useRef(null), [selection, setSelection] = useState(null);
  useEffect(() => {
    setSelection(null);
    const cy = cytoscape({ container: container.current,
      elements: [...nodes.map(n => ({ data: { id:n.identifier, label:n.identifier, sources:n.sources } })),
        ...edges.map((e,i) => ({ data: { id:`edge-${i}`, source:e.caller, target:e.callee, label:String(e.calls), sources:e.sources } }))],
      style: [{ selector:'node', style:{ 'background-color':'#326cb1', label:'data(label)', color:'#253d58', 'font-size':11, 'text-valign':'bottom', 'text-margin-y':7, width:26, height:26 } },
        { selector:'edge', style:{ width:2, 'line-color':'#9aaec5', 'target-arrow-color':'#9aaec5', 'target-arrow-shape':'triangle', 'curve-style':'bezier', label:'data(label)', 'font-size':10, color:'#53677e' } }],
      layout:{ name:'circle', padding:45 }, minZoom:0.3, maxZoom:3,
    });
    cy.on('tap','node, edge', e => setSelection({ label:e.target.isNode() ? e.target.id() : `${e.target.source().id()} → ${e.target.target().id()}`, sources:e.target.data('sources') }));
    return () => cy.destroy();
  }, [nodes,edges]);
  return <section className="card panel spaced"><h2>Contact network</h2><p className="hint">Select a node or directed link for supporting rows. Use the relationship table below for keyboard access.</p><div ref={container} className="network" aria-label="Interactive contact network" />{selection && <div><strong>{selection.label}</strong><div className="refs">{selection.sources.map((r,i) => <button key={`${r.file_id}-${r.row}-${i}`} className="ref" onClick={() => onSource(r)}>{r.filename} · row {r.row}{r.disputed ? ' ⚑' : ''}</button>)}</div></div>}</section>;
}
