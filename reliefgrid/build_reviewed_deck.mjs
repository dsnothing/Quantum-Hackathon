import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const runtime='C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1105-1297-0_26.1105.1297.0_x64__3k8sg7r9htsxt/dependencies';
process.env.RUNTIME_NODE_MODULES=runtime+'/node/node_modules';
const {PresentationFile,FileBlob}=await import(pathToFileURL(runtime+'/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs'));
const skill='C:/Users/ds980_ugnlatu/.codex/plugins/cache/openai-primary-runtime/presentations/26.1105.12137/skills/presentations';
const root=process.cwd(), dir=path.join(root,'build/relief-review');
const deck=await PresentationFile.importPptx(await FileBlob.load('output/ReliefGrid_Presentation.pptx'));
for(const owner of [...deck.layouts.items,...deck.masters.items])for(const shape of owner.shapes.items)shape.text='';
const warm=JSON.parse(await fs.readFile('reliefgrid/benchmarks/optimization-warm-matched.json','utf8'));
const cold=JSON.parse(await fs.readFile('reliefgrid/benchmarks/optimization-cached.json','utf8'));
const tuned=JSON.parse(await fs.readFile('reliefgrid/benchmarks/optimization-tuned.json','utf8'));
const bg=await fs.readFile(path.join(dir,'template-background.jpeg'));
const C={bg:'#F3FAF7',ink:'#07343D',teal:'#0B6470'};
function text(s,value,x,y,w,h,size=32,bold=false,color=C.ink){
 const box=s.shapes.add({geometry:'textbox',name:value.slice(0,45),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 box.text=value;box.text.style={typeface:'Calibri',fontSize:size,color,bold};box.text.insets=0;return box;
}
function page(i,title,notes){
 const s=deck.slides.items[i];
 // Preserve the imported masters and canvas. Reflow only the slide-level content.
 for(const shape of s.shapes.items){shape.text='';shape.fill='none';shape.line={fill:'none',width:0};}
 const art=s.images.add({blob:bg.buffer.slice(bg.byteOffset,bg.byteOffset+bg.byteLength),contentType:'image/jpeg',alt:'Natural Intelligence template artwork, PresentationGO',fit:'cover',position:{left:850,top:0,width:430,height:720}});art.sendToBack();
 const area=s.shapes.add({geometry:'rect',name:'Plain reading area',position:{left:0,top:0,width:850,height:720},fill:C.bg,line:{fill:'none',width:0}});area.sendToBack();
 text(s,title,64,54,730,120,48,true);
 text(s,'Template artwork: Natural Intelligence, PresentationGO.com',64,674,730,25,16,false,C.teal);
 if(i===0||i===5)text(s,String(i+1),1170,674,32,25,16,false,'#EBFFFA');
 s.speakerNotes.text=notes+'\nAll populations and roads are synthetic. Original artwork/template: https://www.presentationgo.com/presentation/natural-intelligence-powerpoint-template/ .';
 return s;
}
function table(s,values,y,widths){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:64,top:y,width:730,height:values.length*62,columnWidths:widths,values});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=t.getCell(r,c);cell.fill=r===0?'#D8EBE5':C.bg;cell.text.style={typeface:'Calibri',fontSize:27,color:C.ink,bold:r===0};
 }
 return t;
}
let s=page(0,'ReliefGrid','0:00–0:30. ReliefGrid chooses a fixed number of emergency supply hubs using a directed road model. The notebook is the reproducible artifact. The model does not include capacities, inventories, live traffic, or dispatch.');
text(s,'Emergency hub planning\nwith QAOA',64,220,730,135,44,false,C.teal);
text(s,'Road closures change which\ncommunities a hub can serve',64,410,730,110,32);
text(s,'Synthetic scenarios. Local ideal simulator.',64,570,730,45,25,false,C.teal);
s=page(1,'The planning model','0:30–1:15. Travel runs from each hub to each community, not in the reverse direction. Choose exactly k=3 hubs. Coverage counts each community once when at least one selected hub can reach it within T=12 minutes. In Riverbend, the nominal optimum is 9060 and bridge-closed optimum is 8140, a reduction of 920 synthetic residents. Source: reliefgrid/benchmarks/optimization-warm-matched.json.');
text(s,'Three supply hubs\nTwelve-minute travel threshold',64,208,730,105,34,true);
text(s,'Directed travel from hub to community\nEach covered community counts once',64,350,730,100,30);
text(s,'Riverbend optimum\n9,060 open roads     8,140 bridge closed',64,510,730,100,30,false,C.teal);
s=page(2,'The quantum implementation','1:15–2:10. One qubit represents each of eight candidate hubs. Start from the greedy deployment, then two coherent fixed-k XY sweeps. Direct all-zero-neighborhood phases encode H=-coverage/sum(weights), up to a global phase. Ordered XXPlusYY gates preserve the count of selected hubs. This discrete feasible warm start is not IBM’s continuous relaxation warm-start mixer. Bounded Powell training uses exact statevector expectations, followed by a separately seeded 256-shot evaluation. Build the parameterized circuit once, then bind angles. Tests verify phase sign, bit order, feasibility, binding equivalence, sampling and coherence controls. Sources: reliefgrid/backend/solvers/qaoa.py; https://quantum.cloud.ibm.com/docs/en/tutorials/warm-start-qaoa .');
text(s,'1   Coherent feasible preparation',64,202,730,45,32,true);
text(s,'A greedy plan seeds the fixed-hub-count state',96,252,690,60,28);
text(s,'2   Coverage cost phases',64,339,730,45,32,true);
text(s,'Road reachability sets each community’s phase',96,389,690,60,28);
text(s,'3   XY mixing',64,476,730,45,32,true);
text(s,'Exchanges preserve exactly three selected hubs',96,526,690,60,28);
const a=cold.rows[0].results.qaoa,b=warm.rows[0].results.qaoa;
s=page(3,'The warm start closes the gap',`2:10–3:05. Riverbend nominal, p=1, seed42. Both QAOA versions use 24 exact-expectation evaluations, 256 final samples and phaseScale=1. Only initialization differs. First-k sampled coverage=${a.weightedCoverage}, expected=${a.diagnostics.expectedWeightedCoverage}; greedy-start sampled coverage=${b.weightedCoverage}, expected=${b.diagnostics.expectedWeightedCoverage}. The selected score differs from the expectation. Exact and seeded uniform random each find9060. Source: optimization-cached.json and optimization-warm-matched.json; samplingSeed=${b.diagnostics.samplingSeed}.`);
text(s,'Riverbend nominal, seed 42',64,182,730,45,29,false,C.teal);
table(s,[['Method','Best plan','Expected'],['Exact optimum','9,060','—'],['QAOA, first k','8,680',Math.round(a.diagnostics.expectedWeightedCoverage).toLocaleString('en-US')],['QAOA, greedy start','9,060',Math.round(b.diagnostics.expectedWeightedCoverage).toLocaleString('en-US')]],250,[350,180,200]);
text(s,'Same 24 evaluations and 256 samples\nSynthetic population covered',64,553,730,80,27,false,C.teal);
function hits(data,method){return data.rows.filter(r=>r.results[method].weightedCoverage===r.results.exact.weightedCoverage).length;}
function range(data,method){const v=data.rows.map(r=>r.results[method].timing.totalMs);return `${Math.min(...v).toFixed(1)}–${Math.max(...v).toFixed(1)}`;}
s=page(4,'Quality parity across eight runs',`3:05–4:05. Two synthetic scenarios, nominal/bridge-closed, seeds42 and7, p1,24 evaluations,256 samples. All cases and seeds included. Exact search needs only C(8,3)=56 deployments. QAOA costs include construction, optimization, final sampling, compilation and post-training audit; classical times use their full solver times. Single-machine ranges are not a rigorous speedup benchmark. A rejected setting with phaseScale6,120 evaluations,3 starts found ${hits(tuned,'qaoa')}/8 optima; more effort did not improve these best-sample results. Sources: reliefgrid/benchmarks/optimization-{cached,warm-matched,tuned}.json.`);
table(s,[['Method','Optima','Time, ms'],['Exact search',`${hits(cold,'exact')}/8`,range(cold,'exact')],['Uniform random',`${hits(cold,'random')}/8`,range(cold,'random')],['QAOA, first k',`${hits(cold,'qaoa')}/8`,range(cold,'qaoa')],['QAOA, greedy start',`${hits(warm,'qaoa')}/8`,range(warm,'qaoa')]],208,[350,140,240]);
text(s,'Eight hubs, two scenarios, two closure states\nSeeds 42 and 7. Ideal simulator.',64,552,730,90,27,false,C.teal);
s=page(5,'What these results establish','4:05–5:00. Warm-started QAOA reaches exact best-sample quality in all eight tested runs, but finite shots do not guarantee the optimum on arbitrary instances. A portfolio can retain the better of greedy and QAOA, guaranteeing at least greedy coverage. Its optional bounded exact guard guarantees optimum coverage for supported small instances. The actual winning solver and separate raw QAOA output remain in evidence. These guarantees arise from classical selection. Exact enumeration remains much faster here. No hardware, noise robustness, asymptotic speedup, or general quantum advantage is demonstrated. Extending to a genuine advantage on larger realistic inputs would require substantial research and is not established by this project. Sources: reliefgrid/backend/solvers/portfolio.py; reliefgrid/docs/Optimization_Review.md.');
text(s,'Optimal sampled plans in 8 of 8 tests',64,204,730,65,34,true);
text(s,'Classical exact search remains much faster\nFinite samples give no general guarantee',64,314,730,100,30);
text(s,'A classical safeguard retains the better plan\nIts guarantee comes from that comparison',64,468,730,100,30,false,C.teal);
await fs.writeFile(path.join(dir,'reviewed-inspect.json'),JSON.stringify(await deck.inspect({kind:'slide,textbox,table,layout',maxChars:60000}),null,2));
await (await PresentationFile.exportPptx(deck)).save(path.join(dir,'reviewed-candidate.pptx'));
for(const [i,slide] of deck.slides.items.entries())await fs.writeFile(path.join(dir,`after-${i+1}.png`),new Uint8Array(await(await slide.export({format:'png',scale:1})).arrayBuffer()));
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')));
const result=await finalizePresentation({workspaceDir:root,candidatePath:path.join(dir,'reviewed-candidate.pptx'),finalPath:path.join(root,'output/ReliefGrid_Improved.pptx'),
 pythonExecutable:runtime+'/python/python.exe',integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit','--require-native-table-slide','4','--require-native-table-slide','5'],explicitTotalSlideCount:6,requiredNativeTableOwnerSlides:[4,5],fontPolicy:{basis:'reference',families:['Calibri'],referencePath:path.join(root,'output/ReliefGrid_Presentation.pptx'),referenceSha256:createHash('sha256').update(await fs.readFile('output/ReliefGrid_Presentation.pptx')).digest('hex')},verifyArtifactToolImport:true,receiptPath:path.join(dir,'validation-improved.json')});
console.log(JSON.stringify(result));
