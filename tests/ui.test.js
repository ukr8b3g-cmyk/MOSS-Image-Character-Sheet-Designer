import test from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFileSync} from 'node:fs';
import {CONTRACT,DEFAULT_STATE} from '../web/catalog.js';
import {parseState,DesignerController,validatePreview} from '../web/controller.js';
import {createDesignerUI} from '../web/ui.js';
import {installDesigner} from '../web/integration.js';
const require=createRequire(import.meta.url);
const {JSDOM}=require(process.env.MOSS_TEST_JSDOM);
const raw=()=>JSON.stringify(DEFAULT_STATE);
const pause=ms=>new Promise(r=>setTimeout(r,ms));
function setup(){const dom=new JSDOM('<body></body>',{url:'http://localhost/'});for(const key of ['window','document','AbortController','Event','CompositionEvent'])globalThis[key]=dom.window[key];return dom;}
test('browser contract and compiler preview agree',()=>{
  const contract=JSON.parse(readFileSync(new URL('../contracts/prompt_contract.v1.json',import.meta.url),'utf8'));
  const preview=JSON.parse(readFileSync(new URL('./fixtures/sample_preview.json',import.meta.url),'utf8'));
  assert.deepEqual(CONTRACT,contract);
  assert.equal(validatePreview(preview,preview.canonical_state),preview);
});
test('strict parser and retained manual dimensions',async()=>{
  assert.throws(()=>parseState(raw().replace('1120','1120.0')));
  assert.throws(()=>parseState(raw().replace('1120','true')));
  assert.throws(()=>parseState(raw().replace('"identity":""','"identity":"\\ud800"')));
  const c=new DesignerController({raw:raw(),requestPreview:()=>new Promise(()=>{})});
  c.setMode('manual');assert.equal(c.state.size.manual_width,1536);assert.equal(c.state.size.manual_height,1024);c.dispose();
});
test('real UI drafts, same-JSON Apply, IME, independent instances, external input',()=>{
  const dom=setup();let ui;
  const c=new DesignerController({raw:raw(),requestPreview:()=>new Promise(()=>{}),onChange:(_,reason)=>ui?.render(reason)});
  ui=createDesignerUI({controller:c});document.body.append(ui.root);ui.render();
  assert.equal(ui.root.querySelector('[data-character-field]'),null);
  const numeric=ui.root.querySelector('input');numeric.value='-';numeric.dispatchEvent(new Event('input'));assert.throws(()=>ui.flushDrafts());
  const json=ui.root.querySelector('.moss-json-editor textarea');json.value=c.raw;ui.root.querySelector('.moss-apply').click();ui.flushDrafts();assert.equal(numeric.value,'1120');
  ui.setExternal(true);assert.equal(numeric.disabled,true);
  ui.setExternal(false);assert.equal(ui.root.querySelector('[data-view]').disabled,false);
  assert.equal(ui.root.querySelectorAll('.moss-card').length,13);
  assert.equal(ui.root.querySelectorAll('.moss-head-row .moss-card').length,6);
  assert.equal(ui.root.querySelectorAll('.moss-body-row .moss-card').length,7);
  assert.equal(ui.root.querySelector('.moss-generated-prompt'),null);
  assert.equal(ui.root.querySelector('.moss-settings-panel').hidden,true);
  ui.root.querySelector('[data-tab="settings"]').click();
  assert.equal(ui.root.querySelector('.moss-stage').hidden,true);
  assert.equal(ui.root.querySelector('.moss-settings-panel').hidden,false);
  assert.equal(ui.root.querySelector('.moss-json-editor').closest('.moss-settings-panel'),ui.root.querySelector('.moss-settings-panel'));
  ui.root.querySelector('[data-tab="parts"]').click();assert.equal(ui.root.querySelector('.moss-stage').hidden,true);assert.equal(ui.root.querySelector('.moss-part-panel').hidden,false);
  const part=ui.root.querySelector('[data-part-prompt]');part.value='silver hairpin';part.dispatchEvent(new Event('input'));assert.equal(c.state.part_prompts.head_hair,'silver hairpin');
  ui.root.querySelector('[data-tab="style"]').click();assert.equal(ui.root.querySelector('.moss-part-panel').hidden,true);assert.equal(ui.root.querySelector('.moss-style-panel').hidden,false);
  const anime=ui.root.querySelector('[data-style="anime"]');anime.checked=true;anime.dispatchEvent(new Event('change'));assert.equal(c.state.style,'anime');
  ui.root.querySelector('[data-view="hands"]').click();assert.ok(c.state.views.includes('hands'));
  assert.equal(ui.root.querySelector('[data-clothing-mode]'),null);
  const c2=new DesignerController({raw:raw(),requestPreview:()=>new Promise(()=>{})});assert.equal(c2.state.character.identity,'');
  ui.dispose();c.dispose();c2.dispose();dom.window.close();
});

test('legacy clothing mode loads without retaining the removed setting',()=>{
  const saved=structuredClone(DEFAULT_STATE);saved.appearance.clothing_mode='worn';
  const c=new DesignerController({raw:JSON.stringify(saved),requestPreview:()=>new Promise(()=>{})});
  assert.equal(c.state.appearance.clothing_mode,undefined);
  assert.equal(JSON.parse(c.raw).appearance.clothing_mode,'worn');
  c.preset('clothing');assert.equal(JSON.parse(c.raw).appearance.clothing_mode,undefined);
  assert.deepEqual(c.state.views,CONTRACT.presets.clothing);
  c.dispose();
});

test('invalid saved JSON opens settings for recovery without losing the original',()=>{
  const dom=setup();let ui;
  const broken='{"broken":';
  const c=new DesignerController({raw:broken,requestPreview:()=>new Promise(()=>{}),onChange:(_,reason)=>ui?.render(reason)});
  ui=createDesignerUI({controller:c});
  assert.equal(ui.root.querySelector('.moss-settings-panel').hidden,false);
  assert.equal(ui.root.querySelector('.moss-json-editor').open,true);
  assert.equal(ui.root.querySelector('.moss-json-editor textarea').value,broken);
  ui.root.querySelector('.moss-json-editor textarea').value=raw();ui.root.querySelector('.moss-apply').click();
  assert.equal(c.error,null);assert.deepEqual(c.state.views,DEFAULT_STATE.views);
  assert.equal(ui.root.querySelector('.moss-metrics .moss-status').textContent,'更新中…');
  ui.setExternal(true);assert.equal(ui.root.querySelector('[data-tab="layout"]').disabled,false);
  ui.dispose();c.dispose();dom.window.close();
});
test('integration retains widget, flushes serialize, restores hooks and readds',()=>{
  const dom=setup();let callbacks=0;
  const original={name:'state_json',value:raw(),options:{setValue(){callbacks++;return 7;}},callback(){return 3;}};
  const node={type:'MOSSImageCharacterSheetDesigner',widgets:[original],inputs:[],size:[870,1180],graph:{beforeChange(){},afterChange(){}},
    serialize(){return {widgets_values:[original.value]};},setSize(s){this.size=s;},setDirtyCanvas(){},
    addDOMWidget(name,type,element,options){const w={name,type,element,options};this.widgets.push(w);document.body.append(element);return w;},removeWidget(w){this.widgets.splice(this.widgets.indexOf(w),1);w.element.remove();}};
  const app={canvas:{emitBeforeChange(){},emitAfterChange(){}}};const api={fetchApi:()=>new Promise(()=>{})};
  const record=installDesigner(node,app,api);assert.ok(record);assert.equal(original.options.setValue(),7);assert.equal(callbacks,1);assert.equal(node.widgets[0],original);
  record.controller.setPartPrompt('head_hair','silver hairpin');assert.equal(JSON.parse(node.serialize().widgets_values[0]).part_prompts.head_hair,'silver hairpin');
  for(let i=0;i<10;i++){node.onRemoved();assert.equal(node.widgets.length,1);node.onAdded();assert.equal(node.widgets.length,2);}
  node.onRemoved();assert.equal(document.querySelectorAll('.moss-sheet-designer').length,0);dom.window.close();
});

test('late preview responses never replace the current saved input',async()=>{
  const fixture=JSON.parse(readFileSync(new URL('./fixtures/sample_preview.json',import.meta.url),'utf8'));
  const requests=[];
  const c=new DesignerController({raw:JSON.stringify(fixture.canonical_state),requestPreview:raw=>new Promise(resolve=>requests.push({raw,resolve}))});
  await pause(290);
  c.change(s=>{s.character.identity='Current adult character';});
  await pause(290);
  assert.equal(requests.length,2);
  const answer=req=>({...structuredClone(fixture),canonical_state:JSON.parse(req.raw),prompt:JSON.parse(req.raw).character.identity});
  requests[1].resolve(answer(requests[1]));await pause(0);
  assert.equal(c.preview.prompt,'Current adult character');
  requests[0].resolve(answer(requests[0]));await pause(0);
  assert.equal(c.preview.prompt,'Current adult character');assert.equal(c.isCurrentPreview,true);
  c.dispose();
});

test('clothing cards and layout use garment symbols without a wearer',()=>{
  const dom=setup();let ui;
  const fixture=JSON.parse(readFileSync(new URL('./fixtures/sample_preview.json',import.meta.url),'utf8'));
  const c=new DesignerController({raw:JSON.stringify(fixture.canonical_state),requestPreview:()=>new Promise(()=>{}),onChange:()=>ui?.render()});
  ui=createDesignerUI({controller:c});
  c.preset('clothing');
  c.pending=false;c.previewRaw=c.raw;c.preview={...fixture,layout_plan:{...fixture.layout_plan,panels:[{id:'clothing_front',bbox_px:[0,0,500,1000]},{id:'clothing_back',bbox_px:[500,0,1000,1000]}]}};
  ui.render();assert.equal(ui.root.querySelectorAll('.moss-panel [data-artwork-source="garment-symbol"]').length,2);
  assert.equal(ui.root.querySelectorAll('.moss-card [data-artwork-source="garment-symbol"]').length,2);
  ui.dispose();c.dispose();dom.window.close();
});
