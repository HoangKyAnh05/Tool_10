// Regression: approving an already approved, paused schedule must not toggle it off again.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const dummy = {addEventListener(){}};
const calls = [], remote = {active:false};
const context = vm.createContext({
  document:{addEventListener(){},querySelector(){return dummy;}},
  setInterval(){},setTimeout(){},clearTimeout(){},calls,remote,
});
const source = fs.readFileSync(path.join(__dirname,'../web/app.js'),'utf8').replace(/\binit\(\);\s*$/, '');
vm.runInContext(source,context);
vm.runInContext(`
  state={settings:{approved:true,telegram_chat_id:'123',active:false}};
  page='overview'; toast=()=>{}; refresh=async()=>{};
  api=async(path)=>{
    calls.push(path);
    if(path==='/api/approve')remote.active=true;
    if(path==='/api/toggle')remote.active=!remote.active;
    return {ok:true};
  };
`,context);
(async()=>{
  await vm.runInContext("perform('approve')",context);
  assert.equal(remote.active,true);
  assert.deepEqual(calls,['/api/approve']);
  console.log('PASS: approval leaves the schedule active.');
})().catch(error=>{console.error(error);process.exitCode=1;});
