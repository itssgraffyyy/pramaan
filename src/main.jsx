import React from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

function App() {
  return (
    <main>
      <span className="eyebrow">TEAM ARC · PS03</span>
      <h1>PRAMAAN</h1>
      <h2>Telecom Forensic Investigation Platform</h2>
      <p>CDR/IPDR analysis with evidence-linked AI assistance.</p>
      <span className="status">Frontend initialised · Prototype under development</span>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
