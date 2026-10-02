// Node built-ins only. No real provider requests or Firestore writes.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..', 'frontend');
const conversationId = '3380d3d0fb2f4ba0b6f15e84b4f40db5';

class Element {
  constructor(tag = 'div') {
    this.tag = tag; this.children = []; this.listeners = {}; this.attributes = {};
    this.value = ''; this.textContent = ''; this.hidden = false; this.disabled = false;
    this.classList = { toggle() {} }; this.parentElement = {}; this.scrollHeight = 100;
  }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = nodes; }
  setAttribute(key, value) { this.attributes[key] = value; }
  getAttribute(key) { return this.attributes[key]; }
  click() { this.clicked = true; }
  remove() {}
  addEventListener(type, listener) { this.listeners[type] = listener; }
  fire(type) { return this.listeners[type]?.({ preventDefault() {}, key: 'ArrowRight' }); }
  querySelectorAll(tag) { return this.children.flatMap(c => [...(c.tag === tag ? [c] : []), ...c.querySelectorAll(tag)]); }
  focus() { this.focused = true; }
  reportValidity() { return true; }
  reset() {}
  getBoundingClientRect() { return { width: 320, height: 260, left: 0 }; }
  getContext() { this.colors = []; return new Proxy({}, { get: () => () => {}, set: (obj, key, value) => { if (key === "fillStyle" || key === "strokeStyle") this.colors.push(value); obj[key] = value; return true; } }); }
}

function harness(options = {}) {
  const elements = {};
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  for (const match of html.matchAll(/id="([^"]+)"/g)) {
    assert(!elements[match[1]], 'duplicate HTML id'); elements[match[1]] = new Element();
  }
  const el = id => { assert(elements[id], `missing DOM id ${id}`); return elements[id]; };
  el('chart-range').value = '30';
  const state = {
    calls: [], confirm: true,
    rows: Array.from({ length: 40 }, (_, i) => { const day = new Date(Date.UTC(2026, 8, i + 1)).toISOString().slice(0, 10); return { id: day, date: day, value: i % 3 ? 40 : 0, memo: '<img src=x onerror=alert(1)>' }; }),
    conversations: [{ id: conversationId, title: '기존 대화', updated_at: '2026-10-01T00:00:00Z', messages: [{ role: 'user', content: '최근 운동 추세를 간단히 알려줘.' }, { role: 'assistant', content: '최근 285분입니다.' }] }],
    override: null,
  };
  const summary = () => ({ insights: { workout_days: state.rows.filter(r => r.value > 0).length, rest_days: state.rows.filter(r => r.value === 0).length, workout_day_average: 40, longest_workout_streak: 2 }, period: { start: state.rows[0]?.date ?? null, end: state.rows.at(-1)?.date ?? null }, count: state.rows.length, metrics: { total: 1000, average: 25, max: 40, min: 0 }, trend: { recent_total: 120, previous_total: 100, absolute_change: 20, percent_change: 20, direction: 'increase' } });
  const response = (body, status = 200) => ({ ok: status >= 200 && status < 300, status, json: async () => { if (status === 204) throw Error('204 must not be parsed'); return structuredClone(body); } });
  async function fetchFake(url, opts = {}) {
    const request = { path: new URL(url).pathname, method: opts.method || 'GET', body: opts.body ? JSON.parse(opts.body) : null };
    state.calls.push(request);
    if (state.override) { const value = await state.override(request); if (value !== undefined) return value; }
    const p = request.path;
    if (p === '/api/chat') {
      let row = state.conversations.find(c => c.id === request.body.conversation_id);
      if (!row) { row = { id: 'b'.repeat(32), title: request.body.message, updated_at: '2026-10-02T00:00:00Z', messages: [] }; state.conversations.unshift(row); }
      row.messages.push({ role: 'user', content: request.body.message }, { role: 'assistant', content: '<script>unsafe()</script>답변' });
      return response({ conversation_id: row.id, answer: row.messages.at(-1).content, provider: 'codyssey-openai-compatible', model: 'gpt-5-mini', summary: summary() });
    }
    if (p === '/api/conversations') return response(state.conversations);
    if (p.startsWith('/api/conversations/')) return response(state.conversations.find(c => c.id === p.split('/').at(-1)));
    if (p === '/api/data/summary') return response(summary());
    if (p === '/api/data' && request.method === 'GET') return response(state.rows);
    if (p === '/api/data' && request.method === 'POST') { state.rows.push({ id: request.body.date, ...request.body }); return response(state.rows.at(-1), 201); }
    if (p.startsWith('/api/data/')) {
      const id = p.split('/').at(-1), i = state.rows.findIndex(r => r.id === id);
      if (request.method === 'PUT') { state.rows[i] = { id, ...request.body }; return response(state.rows[i]); }
      if (request.method === 'DELETE') { state.rows.splice(i, 1); return response(null, 204); }
    }
    if (p === '/workouts/summary') return response({ total_records: 40, start_date: '2026-09-01', end_date: '2026-10-10', average_value: 25, min_value: 0, max_value: 40 });
    if (p === '/workouts') return response(request.method === 'POST' ? request.body : state.rows);
    if (p === '/workouts/1900-01-01') return response({ detail: 'not found' }, 404);
    if (p.startsWith('/workouts/')) return response(state.rows[0]);
    throw Error('Unexpected request ' + p);
  }
  const storage = options.storage || new Map();
  const docRoot = new Element('html'), events = {};
  const themeWindow = { addEventListener: (type, fn) => { events[type] = fn; }, dispatchEvent: event => events[event.type]?.(), matchMedia: () => ({ matches: !!options.systemDark }) };
  const context = vm.createContext({ document: { documentElement: docRoot, body: new Element("body"), getElementById: el, createElement: tag => new Element(tag) }, window: { ...themeWindow, devicePixelRatio: 1, confirm: () => state.confirm }, ResizeObserver: class { observe() {} }, fetch: options.fetch || fetchFake, AbortController, setTimeout, clearTimeout, Intl, Date, Event, Blob, URL, localStorage: {getItem: key => { if(options.storageError) throw Error("blocked"); return storage.get(key); }, setItem: (key,value) => { if(options.storageError) throw Error("blocked"); storage.set(key,value); }} });
  for (const file of ['config.js', 'theme.js', 'chart.js', 'app.js', 'ai.js', 'data.js', 'chat.js', 'export.js']) vm.runInContext(fs.readFileSync(path.join(root, file), 'utf8'), context, { filename: file });
  const run = code => vm.runInContext(code, context);
  const ready = Promise.all([run('refresh()'), run('refreshData()'), run('loadConversations()')]);
  return { el, state, run, ready, response, storage, docRoot };
}


module.exports = { harness };
