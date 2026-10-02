const {test} = require('node:test');
const assert = require('node:assert/strict');
const {harness} = require('./frontend-harness.cjs');

test('insights render from summary and update after CRUD', async()=>{
 const h=harness();await h.ready;
 assert.equal(h.el('insight-workout').textContent,'26일');
 assert.equal(h.el('insight-rest').textContent,'14일');
 assert.equal(h.el('insight-average').textContent,'40분');
 h.el('data-date').value='2026-10-11';h.el('data-value').value='60';h.el('data-memo').value='운동';
 await h.el('data-form').fire('submit');assert.equal(h.el('insight-workout').textContent,'27일');
 h.el('data-rows').querySelectorAll('button')[0].fire('click');h.el('data-value').value='0';
 await h.el('data-form').fire('submit');assert.equal(h.el('insight-workout').textContent,'26일');
 await h.el('data-rows').querySelectorAll('button')[1].fire('click');assert.equal(h.el('insight-rest').textContent,'14일');
});

test('CSV BOM, header, ordering, Korean, quotes and multiline escaping',async()=>{
 const h=harness();await h.ready;
 const csv=h.run(`workoutCSV([{date:'2026-02-02',value:0,memo:'휴식'},{date:'2026-02-01',value:60,memo:'웨이트, "가슴"\\n걷기',id:'NOT_EXPORTED'}])`);
 assert.equal(csv,'\uFEFFdate,value,memo\r\n"2026-02-01","60","웨이트, ""가슴""\n걷기"\r\n"2026-02-02","0","휴식"\r\n');
 assert(!csv.includes('NOT_EXPORTED'));
 assert.deepEqual([...Buffer.from(csv).subarray(0,3)],[239,187,191]);
});

test('CSV formula neutralization and empty export',async()=>{
 const h=harness();await h.ready;
 assert(h.run(`workoutCSV([{date:'2026-01-01',value:0,memo:'=1+1'}])`).includes('"\'=1+1"'));
 assert.equal(h.run('workoutCSV([])'),'\uFEFFdate,value,memo\r\n');
 h.state.rows=[];await h.run('refreshData()');assert(h.el('csv-download').disabled);
});

test('theme toggle stores choice, restores it and redraws chart',async()=>{
 const storage=new Map();const h=harness({storage});await h.ready;
 h.el('theme-toggle').fire('click');assert.equal(storage.get('fitlog-theme'),'dark');
 assert.equal(h.docRoot.getAttribute('data-theme'),'dark');assert.equal(h.el('theme-toggle').attributes['aria-pressed'],'true');
 assert(h.el('workout-chart').colors.includes('#83dbad'));assert(h.el('workout-chart').colors.includes('#bdcec5'));
 const restored=harness({storage});await restored.ready;assert.equal(restored.docRoot.getAttribute('data-theme'),'dark');
 for(const range of ['7','30','all']){restored.el('chart-range').value=range;restored.el('chart-range').fire('change');assert(!restored.el('chart-content').hidden);}
 restored.el('theme-toggle').fire('click');assert.equal(storage.get('fitlog-theme'),'light');
});

test('system theme and blocked storage do not break controls',async()=>{
 const h=harness({systemDark:true,storageError:true});await h.ready;
 assert.equal(h.docRoot.getAttribute('data-theme'),'dark');h.el('theme-toggle').fire('click');assert.equal(h.docRoot.getAttribute('data-theme'),'light');
 const stored=harness({systemDark:true,storage:new Map([['fitlog-theme','light']])});await stored.ready;assert.equal(stored.docRoot.getAttribute('data-theme'),'light');
});


test('CSV button downloads whole dataset without requests',async()=>{
 const h=harness();await h.ready;const before=h.state.calls.length;
 h.el('csv-download').fire('click');
 assert.equal(h.state.calls.length,before);
 assert(h.el('export-status').textContent.includes('40개'));
 assert(h.run('document.body.children.at(-1).clicked'));
 assert.match(h.run('document.body.children.at(-1).download'),/^fitlog-data-\d{4}-\d{2}-\d{2}\.csv$/);
 assert.equal(h.run('workoutCSV(dataRecords).split("\\r\\n").length'),42);
});
