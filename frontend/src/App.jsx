import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import ForceGraph2D from 'react-force-graph-2d';
import './App.css';

const API_BASE = 'http://127.0.0.1:8000';
const SIDEBAR_WIDTH = 420;

function App() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);
  const [isNebulaMode, setIsNebulaMode] = useState(false);
  
  // Explicit graph dimensions so ForceGraph2D doesn't swallow the sidebar
  const [graphDims, setGraphDims] = useState({ w: window.innerWidth - SIDEBAR_WIDTH, h: window.innerHeight });
  
  const graphRef = useRef();
  const chatEndRef = useRef();

  // Keep graph dimensions accurate on resize
  useEffect(() => {
    const onResize = () => {
      setGraphDims({ w: window.innerWidth - SIDEBAR_WIDTH, h: window.innerHeight });
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    fetchGraph(isNebulaMode);
  }, [isNebulaMode]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    if (graphRef.current) {
      graphRef.current.d3Force('charge')?.strength(isNebulaMode ? -60 : -280);
      graphRef.current.d3Force('link')?.distance(isNebulaMode ? 25 : 80);
      graphRef.current.d3ReheatSimulation();
    }
  }, [isNebulaMode, graphData]);

  const fetchGraph = async (dense) => {
    try {
      const res = await axios.get(`${API_BASE}/graph?limit=${dense ? 1000 : 150}`);
      setGraphData({
        nodes: res.data.nodes.map(n => ({ ...n, val: 2 })),
        links: res.data.edges.map(e => ({ source: e.source, target: e.target, name: e.relation }))
      });
    } catch (err) {
      console.error('Graph fetch failed:', err);
    }
  };

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    const userQuery = query;
    setQuery('');
    setMessages(prev => [...prev, { role: 'user', content: userQuery }]);
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/query`, { query: userQuery });
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.answer, data: res.data.data }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Backend connection error.' }]);
    } finally {
      setLoading(false);
    }
  };

  const NODE_COLORS = {
    partner:    '#38bdf8',
    order:      '#a78bfa',
    order_item: '#fb923c',
    product:    '#4ade80',
    delivery:   '#facc15',
    invoice:    '#f472b6',
    payment:    '#94a3b8',
  };
  const getNodeColor = (type) => NODE_COLORS[type] || '#64748b';

  const getNodeLabel = (node) => {
    const a = node.attributes || {};
    if (node.type === 'partner') return a.businessPartnerFullName || a.businessPartnerName || node.id;
    if (node.type === 'order') return `Order ${node.id.replace('order_', '')}`;
    if (node.type === 'order_item') return `Item #${a.salesOrderItem || node.id.split('_').pop()}`;
    if (node.type === 'product') return node.id.replace('product_', '').slice(0, 16);
    if (node.type === 'delivery') return `Delivery ${node.id.replace('delivery_', '')}`;
    if (node.type === 'invoice') return `Invoice ${node.id.replace('billing_', '')}`;
    return a.name || String(node.id);
  };

  const handleNodeClick = useCallback((node) => {
    setSelectedNode(node);
    graphRef.current?.centerAt(node.x, node.y, 800);
    graphRef.current?.zoom(4, 800);
  }, []);

  return (
    <div className="nexus-app">

      {/* ── LEFT: GRAPH ── */}
      <div className="graph-panel" style={{ width: graphDims.w }}>

        <div className="viewport-hud">
          <button className={`mode-pill ${isNebulaMode ? 'nebula' : ''}`} onClick={() => setIsNebulaMode(v => !v)}>
            <span className="pip" />
            {isNebulaMode ? 'Nebula Mode' : 'Constellation Mode'}
          </button>
        </div>

        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          width={graphDims.w}
          height={graphDims.h}
          backgroundColor="#030712"
          nodeLabel={() => ''}
          linkColor={() => 'rgba(100,116,139,0.22)'}
          linkWidth={isNebulaMode ? 0.5 : 1.2}
          linkDirectionalParticles={isNebulaMode ? 0 : 3}
          linkDirectionalParticleSpeed={0.006}
          linkDirectionalParticleWidth={1.5}
          linkDirectionalParticleColor={() => '#38bdf8'}
          onNodeClick={handleNodeClick}
          onBackgroundClick={() => setSelectedNode(null)}
          nodeCanvasObjectMode={() => 'after'}
          nodeCanvasObject={(node, ctx, scale) => {
            const color = getNodeColor(node.type);
            const sel = selectedNode?.id === node.id;
            const r = isNebulaMode ? 2 : (sel ? 6 : 4);

            // Glow halo
            ctx.beginPath();
            ctx.arc(node.x, node.y, r * 1.7, 0, 2 * Math.PI);
            ctx.fillStyle = color + '33';
            ctx.shadowColor = color;
            ctx.shadowBlur = sel ? 20 : 8;
            ctx.fill();
            ctx.shadowBlur = 0;

            // Solid core
            ctx.beginPath();
            ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();

            // White center
            ctx.beginPath();
            ctx.arc(node.x, node.y, r * 0.35, 0, 2 * Math.PI);
            ctx.fillStyle = '#ffffff';
            ctx.fill();

            // Label
            if (!isNebulaMode || scale > 3) {
              const raw = getNodeLabel(node);
              const label = raw.length > 24 ? raw.slice(0, 22) + '…' : raw;
              const fs = Math.max(9, 11 / scale);
              ctx.font = `${fs}px "Space Grotesk", sans-serif`;
              ctx.textAlign = 'center';
              ctx.textBaseline = 'top';
              ctx.fillStyle = sel ? '#fff' : 'rgba(226,232,240,0.75)';
              ctx.fillText(label, node.x, node.y + r + 3);
            }
          }}
        />

        {selectedNode && (
          <div className="node-hud">
            <div className="hud-header">
              <span className="hud-dot" style={{ background: getNodeColor(selectedNode.type) }} />
              <h3>{selectedNode.type.replace('_', ' ').toUpperCase()}</h3>
              <button className="hud-close" onClick={() => setSelectedNode(null)}>✕</button>
            </div>
            <div className="hud-rows">
              <div className="hud-row"><span className="hud-key">ID</span><span className="hud-val">{selectedNode.id}</span></div>
              {Object.entries(selectedNode.attributes || {}).slice(0, 12).map(([k, v]) => (
                <div className="hud-row" key={k}>
                  <span className="hud-key">{k}</span>
                  <span className="hud-val">{String(v ?? '')}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── RIGHT: SIDEBAR ── */}
      <div className="command-sidebar">
        <div className="sidebar-header">
          <div className="logo-orb" />
          <div>
            <h1>Nexus Engine</h1>
            <p>Order-to-Cash Intelligence</p>
          </div>
        </div>

        <div className="chat-stream">
          {messages.length === 0 && (
            <div className="empty-state">
              <div className="empty-icon">✦</div>
              <p>System online.<br />Awaiting query.</p>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div key={idx} className={`bubble-wrap ${msg.role}`}>
              <div className="bubble">
                <p>{msg.content}</p>
                 {msg.data?.length > 0 && (
                  <div className="data-table-container">
                    <div className="table-meta">
                      {msg.data.length > 100 
                        ? `Showing first 100 of ${msg.data.length} results` 
                        : `Showing ${msg.data.length} results`}
                    </div>
                    <div className="data-table">
                      <table>
                        <thead>
                          <tr>{Object.keys(msg.data[0]).map(k => <th key={k}>{k}</th>)}</tr>
                        </thead>
                        <tbody>
                          {msg.data.slice(0, 100).map((row, i) => (
                            <tr key={i}>
                              {Object.values(row).map((v, j) => (
                                <td key={j}>{String(v ?? '')}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="bubble-wrap assistant loading">
              <div className="bubble"><p>Processing query…</p></div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <form className="input-bar" onSubmit={handleQuery}>
          <input
            type="text"
            placeholder="Initialize query…"
            value={query}
            onChange={e => setQuery(e.target.value)}
            disabled={loading}
          />
          <button type="submit" disabled={loading || !query.trim()}>Run</button>
        </form>
      </div>

    </div>
  );
}

export default App;
