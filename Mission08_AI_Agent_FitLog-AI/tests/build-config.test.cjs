const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const vm = require("node:vm");
const { spawnSync } = require("node:child_process");
const script = fs.readFileSync(path.join(__dirname, "../frontend/build-config.js"));
function run(value, verify) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "fitlog-build-"));
  try {
    fs.writeFileSync(path.join(dir, "build-config.js"), script);
    fs.writeFileSync(path.join(dir, "config.js"), "original");
    const env = { PATH: process.env.PATH, SystemRoot: process.env.SystemRoot };
    if (value !== undefined) env.API_BASE_URL = value;
    const result = spawnSync(process.execPath, [path.join(dir, "build-config.js")], {env, encoding:"utf8"});
    verify(result, fs.readFileSync(path.join(dir, "config.js"), "utf8"));
  } finally { fs.rmSync(dir, {recursive:true, force:true}); }
}
test("missing and blank env fail without overwriting config", () => {
  for (const value of [undefined, "", "  "]) run(value, (r, text) => { assert.equal(r.status,1); assert.equal(text,"original"); });
});
test("public Render origin generated, trailing slashes removed", () => {
  run(" https://fitlog-ai-tfe9.onrender.com/// ", (r, text) => {
    assert.equal(r.status,0);
    assert.equal(vm.runInNewContext(text + "\nAPI_BASE_URL"), "https://fitlog-ai-tfe9.onrender.com");
  });
});
test("invalid URLs fail safely without echoing input", () => {
  for (const value of ["invalid", "javascript:alert(1)", "https://fitlog-ai-tfe9.onrender.com/path", "https://fitlog-ai-tfe9.onrender.com/?token=sentinel", "https://user:sentinel@fitlog-ai-tfe9.onrender.com"]) {
    run(value, (r,text) => { assert.equal(r.status,1); assert.equal(text,"original"); assert.ok(!r.stderr.includes(value)); assert.ok(!r.stderr.includes("sentinel")); });
  }
});
