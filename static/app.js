const $ = id => document.getElementById(id);
const pct = x => `${(x * 100).toFixed(2)}%`;

async function get(url, options={}) { const r = await fetch(url, options); if (!r.ok) throw new Error(await r.text()); return r.json(); }

async function loadMarket() {
  const data = await get('/api/market');
  $('market').innerHTML = data.items.map(x => `<div class="card"><b>${x.ticker}</b><strong>$${x.price.toFixed(2)}</strong><span class="${x.change >= 0 ? 'up':'down'}">${pct(x.change)}</span></div>`).join('');
}

async function analyze() {
  const holdings = [
    ['aapl','AAPL'],['msft','MSFT'],['nvda','NVDA'],['spy','SPY']
  ].map(([id,ticker]) => ({ticker, shares:Number($(id).value)})).filter(x => x.shares > 0);
  const data = await get('/api/portfolio', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({holdings})});
  const m = data.metrics;
  $('metrics').innerHTML = [
    ['Annualized Return', pct(m.annual_return)], ['Volatility', pct(m.volatility)], ['Sharpe Ratio', m.sharpe.toFixed(2)], ['Max Drawdown', pct(m.max_drawdown)], ['Daily VaR (95%)', pct(m.var_95_daily)], ['Monte Carlo VaR', pct(m.monte_carlo_var_95)]
  ].map(([k,v]) => `<div class="metric"><span>${k}</span><strong>${v}</strong></div>`).join('');
}

async function findAnomalies() {
  const t = $('ticker').value; const data = await get(`/api/anomalies/${t}`);
  $('anomalies').innerHTML = data.anomalies.length ? data.anomalies.map(a => `<div class="row"><b>${a.date}</b><span>Return ${pct(a.return)}</span><span>Score ${a.score.toFixed(3)}</span></div>`).join('') : '<p>No anomalies detected.</p>';
}

async function backtest() {
  const t = $('backticker').value; const d = await get(`/api/backtest/${t}`);
  $('backtest').innerHTML = `<div class="result"><p>Strategy return: <b>${pct(d.strategy_return)}</b></p><p>Buy & hold: <b>${pct(d.benchmark_return)}</b></p><p>Max drawdown: <b>${pct(d.max_drawdown)}</b></p><p>Position changes: <b>${d.trades}</b></p></div>`;
}

async function loadAll() { try { await loadMarket(); await analyze(); await findAnomalies(); await backtest(); } catch(e) { alert(e.message); } }
loadAll();
