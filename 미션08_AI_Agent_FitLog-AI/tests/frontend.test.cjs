const { test } = require('node:test');
const assert = require('node:assert/strict');
const { harness } = require('./frontend-harness.cjs');
const conversationId = '3380d3d0fb2f4ba0b6f15e84b4f40db5';

test('startup uses data summary/chart and never starts GPT/Ollama', async () => {
  const h = harness(); await h.ready;
  assert.equal(h.el('data-count').textContent, '40개'); assert.equal(h.el('data-rows').children.length, 10);
  assert.equal(h.el('recent').children.length, 7); assert.equal(h.el('chart-content').hidden, false);
  assert(h.el('data-trend').textContent.includes('+20%'));
  assert(!h.state.calls.some(r => r.path === '/api/chat' || r.path === '/workouts/ai-analysis'));
  assert.equal(h.el('data-rows').children[0].children[2].textContent, '<img src=x onerror=alert(1)>');
});

test('chat loading, duplicate prevention, success, ID and history refresh', async () => {
  const h = harness(); await h.ready; let release;
  h.state.override = r => r.path === '/api/chat' ? new Promise(resolve => { release = () => resolve(undefined); }) : undefined;
  h.el('chat-input').value = '질문'; const sending = h.el('chat-form').fire('submit');
  assert(h.el('chat-send').disabled); assert(h.el('chat-status').textContent.includes('분석하고'));
  assert.equal(h.el('chat-messages').children.length, 1);
  await h.el('chat-form').fire('submit'); assert.equal(h.state.calls.filter(r => r.path === '/api/chat').length, 1);
  release(); await sending; h.state.override = null;
  assert.equal(h.run('currentConversationId'), 'b'.repeat(32)); assert.equal(h.el('chat-messages').children.length, 2);
  assert(h.el('chat-messages').children[1].children[1].textContent.includes('<script>'));
  assert(!h.el('chat-send').disabled); assert.equal(h.el('history-list').children.length, 2);
  h.el('chat-input').value = '이어 질문'; await h.el('chat-form').fire('submit');
  assert.equal(h.state.calls.filter(r => r.path === '/api/chat').at(-1).body.conversation_id, 'b'.repeat(32));
});

test('existing conversation loads roles and new chat resets without deletion', async () => {
  const h = harness(); await h.ready;
  await h.el('history-list').children[0].children[0].fire('click');
  assert.equal(h.run('currentConversationId'), conversationId); assert.equal(h.el('chat-messages').children.length, 2);
  assert.equal(h.el('chat-messages').children[0].children[1].textContent, '최근 운동 추세를 간단히 알려줘.');
  h.el('chat-new').fire('click'); assert.equal(h.run('currentConversationId'), null); assert.equal(h.el('chat-messages').children.length, 0);
  assert(!h.state.calls.some(r => r.method === 'DELETE'));
});

test('chat errors restore input and permit manual recovery; no raw detail displayed', async () => {
  const h = harness(); await h.ready;
  for (const code of [404, 409, 422, 429, 502, 503, 504]) {
    h.state.override = r => r.path === '/api/chat' ? h.response({ detail: 'INTERNAL_SENTINEL' }, code) : undefined;
    h.el('chat-input').value = '질문'; await h.el('chat-form').fire('submit');
    assert(!h.el('chat-send').disabled); assert.equal(h.el('chat-input').value, '질문');
    assert(!h.el('chat-status').textContent.includes('INTERNAL_SENTINEL'));
  }
  h.state.override = r => { if (r.path === '/api/chat') throw Error('network'); };
  await h.el('chat-form').fire('submit'); assert(h.el('chat-status').textContent.includes('연결'));
  h.state.override = null; await h.el('chat-form').fire('submit'); assert.equal(h.el('chat-input').value, '');
});

test('blank and oversized questions do not send', async () => {
  const h = harness(); await h.ready;
  for (const value of ['  ', 'x'.repeat(4001)]) { h.el('chat-input').value = value; await h.el('chat-form').fire('submit'); }
  assert(!h.state.calls.some(r => r.path === '/api/chat'));
});

test('data POST refreshes summary/list/chart and preserves range', async () => {
  const h = harness(); await h.ready; h.el('chart-range').value = '7';
  h.el('data-date').value = '2026-10-11'; h.el('data-value').value = '60'; h.el('data-memo').value = '  운동  ';
  await h.el('data-form').fire('submit');
  const req = h.state.calls.find(r => r.path === '/api/data' && r.method === 'POST');
  assert.equal(req.body.memo, '운동'); assert.equal(h.el('data-count').textContent, '41개');
  assert(h.el('chart-period').textContent.includes('2026-10-11')); assert.equal(h.el('chart-range').value, '7');
});

test('data PUT locks date and sends original ID/date', async () => {
  const h = harness(); await h.ready; h.el('data-rows').querySelectorAll('button')[0].fire('click');
  const id = h.run('editingDataId'); assert(h.el('data-date').readOnly);
  h.el('data-date').value = '2000-01-01'; h.el('data-value').value = '55'; h.el('data-memo').value = '수정';
  await h.el('data-form').fire('submit');
  const req = h.state.calls.find(r => r.method === 'PUT'); assert.equal(req.path, '/api/data/' + id); assert.equal(req.body.date, id);
  assert.equal(h.run('editingDataId'), null); assert(!h.el('data-date').readOnly);
});

test('DELETE cancellation and 204 success refresh', async () => {
  const h = harness(); await h.ready; h.state.confirm = false;
  await h.el('data-rows').querySelectorAll('button')[1].fire('click'); assert(!h.state.calls.some(r => r.method === 'DELETE'));
  h.state.confirm = true; await h.el('data-rows').querySelectorAll('button')[1].fire('click');
  assert.equal(h.el('data-count').textContent, '39개'); assert(h.el('data-save-status').textContent.includes('삭제되었습니다'));
  assert(!h.el('data-fields').disabled);
});

test('CRUD validation and server error restore controls', async () => {
  const h = harness(); await h.ready;
  h.el('data-date').value = '2026-10-11'; h.el('data-value').value = '-1';
  await h.el('data-form').fire('submit'); assert(!h.state.calls.some(r => r.method === 'POST'));
  h.el('data-value').value = '60'; h.state.override = r => r.method === 'POST' ? h.response({}, 409) : undefined;
  await h.el('data-form').fire('submit'); assert(h.el('data-save-status').textContent.includes('이미'));
  assert(!h.el('data-fields').disabled);
});

test('empty and failed data reads remove stale chart and show messages', async () => {
  const h = harness(); await h.ready; h.state.rows = []; await h.run('refreshData()');
  assert(h.el('chart-content').hidden); assert(h.el('data-summary-status').textContent.includes('없습니다'));
  h.state.override = r => { if (r.path.startsWith('/api/data')) throw Error('offline'); };
  await h.run('refreshData()'); assert(h.el('data-list-status').textContent.includes('연결')); assert(!h.el('data-refresh').disabled);
});

test('graph 7/30/all, rest days and keyboard details', async () => {
  const h = harness(); await h.ready;
  for (const [range, count] of [['7', 7], ['30', 30], ['all', 40]]) {
    h.el('chart-range').value = range; h.el('chart-range').fire('change'); assert(h.el('chart-period').textContent.includes(`${count}개`));
  }
  h.el('workout-chart').fire('keydown'); assert(h.el('chart-detail').textContent.includes('0분'));
});

test('conversation load error preserves current conversation and releases lock', async () => {
  const h = harness(); await h.ready; await h.run(`openConversation('${conversationId}')`);
  h.state.override = r => r.path.startsWith('/api/conversations/') ? h.response({}, 404) : undefined;
  await h.run("openConversation('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')");
  assert.equal(h.run('currentConversationId'), conversationId); assert(!h.el('chat-send').disabled);
});

test('legacy workouts create/date lookup still work without replacing data graph', async () => {
  const h = harness(); await h.ready; const graph = h.el('chart-period').textContent;
  h.el('entry-date').value = '2026-10-11'; h.el('entry-value').value = '60'; h.el('entry-memo').value = '기존';
  await h.el('create-form').fire('submit'); assert(h.state.calls.some(r => r.path === '/workouts' && r.method === 'POST'));
  assert.equal(h.el('chart-period').textContent, graph);
  h.el('date').value = '1900-01-01'; await h.el('date-form').fire('submit'); assert(h.el('date-status').textContent.includes('없습니다'));
});

