// Run with node tests/test_web_startup.mjs. No browser or packages required.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source=fs.readFileSync(new URL('../web/app.js',import.meta.url),'utf8');
function fixture(protocol){
  const elements=new Map(),events={};
  const element=id=>{if(!elements.has(id))elements.set(id,{hidden:id==='#connection',innerHTML:'',textContent:'',disabled:false,open:false,classList:{remove(){},toggle(){}},setAttribute(){},addEventListener(){},focus(){},showModal(){this.open=true},close(){this.open=false}});return elements.get(id)};
  const controls=Array.from({length:8},()=>element('button'+elements.size));
  let fetchCount=0;
  const context=vm.createContext({console,AbortSignal,location:{protocol,assign(){}},localStorage:{getItem(){return '1'},setItem(){}},document:{querySelector:element,querySelectorAll(){return controls},addEventListener(name,fn){events[name]=fn}},fetch:async()=>{fetchCount++;throw new TypeError('Failed to fetch')}});
  vm.runInContext(source,context);
  return {context,element,controls,events,get fetchCount(){return fetchCount}};
}
const file=fixture('file:');
assert.equal(file.fetchCount,0,'Direct file opening must never make a broken API request');
assert.match(file.element('#connection-message').textContent,/opened directly/);
assert.equal(file.element('#connection').hidden,false);
assert.equal((file.element('#board').innerHTML.match(/class="cell"/g)||[]).length,16);
assert.ok(file.controls.every(c=>c.disabled));
file.events.keydown({key:'ArrowLeft',preventDefault(){}});
const http=fixture('http:');
await new Promise(setImmediate);
assert.equal(http.element('#connection').hidden,false);
assert.match(http.element('#connection-message').textContent,/not responding/);
assert.doesNotMatch(http.element('#forecast').textContent,/Failed to fetch/);
assert.ok(http.controls.every(c=>c.disabled));
http.context.fetch=async()=>({ok:true,json:async()=>({score:0,turn:0,status:'playing',board:[{id:1,value:2,group:null,linked:false},...Array(15).fill(null)]})});
await vm.runInContext('loadGame()',http.context);
assert.equal(http.element('#connection').hidden,true);
assert.ok(http.controls.every(c=>!c.disabled));
assert.match(http.element('#board').innerHTML,/#1/);
assert.equal(http.element('#commit').disabled,true,'Reconnect resyncs without replaying a move');
console.log('PASS: direct-file guidance, offline engine, guarded input, reconnect and real tile rendering');
