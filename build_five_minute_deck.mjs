import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const runtime=process.env.QUANTUM_DECK_RUNTIME||'C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1105-1297-0_26.1105.1297.0_x64__3k8sg7r9htsxt/dependencies';
process.env.RUNTIME_NODE_MODULES=runtime+'/node/node_modules';
const {Presentation,PresentationFile}=await import(pathToFileURL(runtime+'/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs'));
const root=process.cwd(), skill='C:/Users/ds980_ugnlatu/.codex/plugins/cache/openai-primary-runtime/presentations/26.1105.12137/skills/presentations';
const {applyPresentationChartFont,finalizePresentation}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs'));
const D=JSON.parse(await fs.readFile('build/five-minute/results.json','utf8'));
await fs.mkdir('build/five-minute/slides',{recursive:true});await fs.mkdir('output',{recursive:true});
const deck=Presentation.create({slideSize:{width:1280,height:720}});
const C={bg:'#101A1B',white:'#EDF3F1',mint:'#B4EDC7',dim:'#B6CAC1',gold:'#F0CF82',line:'#4A635A'};
const talk=[];
function txt(s,text,x,y,w,h,size=28,color=C.white,bold=false){const p=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});p.text=text;p.text.style={fontFamily:'Arial',fontSize:size,color,bold};return p}
function page(title,timing,script,detail,sources=''){const s=deck.slides.add();s.background.fill=C.bg;txt(s,title,64,48,1150,100,46,C.white,true);const n=deck.slides.items.length;txt(s,timing,64,658,1020,28,17,C.dim);txt(s,String(n).padStart(2,'0'),1170,658,50,28,17,C.dim);s.speakerNotes.text=`${timing}\n\nSPOKEN SCRIPT\n${script}\n\nPRESENTER CUES AND OPTIONAL DETAIL\n${detail}\n\nSOURCES\n${sources}`;talk.push({n,title,timing,script,detail,sources});return s}
async function img(s,name,x,y,w,h,alt){const b=await fs.readFile('build/five-minute/'+name);s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:'image/png',alt,fit:'contain',position:{left:x,top:y,width:w,height:h}})}
function table(s,values,x,y,w,h,widths){const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,columnWidths:widths,values});t.borders.assign({fill:C.line,width:1,style:'solid'});for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){const cell=t.getCell(r,c);cell.fill=r===0?'#25463B':C.bg;cell.text.style={fontFamily:'Arial',fontSize:25,color:r===0?C.mint:C.white,bold:r===0};}return t}
const official='https://uwquantum.com/qiskit-fall-fest\nhttps://uwquantum.com/fall-fest-signup';
const ibm='https://quantum.cloud.ibm.com/docs/en/api/qiskit/quantum_info';
let s=page('Quantum 2048','0:00–0:25  ·  The idea',
`Quantum 2048 keeps the familiar sliding-number puzzle: combine equal numbers and work toward 2048. Some tiles can become either 2 or 4, and some share a joint state. Before you commit a move, our forecast shows what can merge and with what probability. That makes the relationship between tiles something you can plan around.`,
`Keep this introduction to 25 seconds. Point to the diamond and link ID, not every control. Explain the normal puzzle objective once. The right-hand image is an actual game screenshot crop. Five minutes is the user's presentation target, not a confirmed organizer limit. The team identity has not been supplied, so no names are invented.`,official+'\nProject: Quantum_2048.ipynb, section 1; evidence/mobile-board.png');
txt(s,'Planning with\nshared fate',64,196,570,174,62,C.mint,true);
txt(s,'See the chance of a merge\nbefore committing a move.',64,430,580,100,31);
txt(s,'Waterloo Qiskit Fall Fest 2026\nQuantum simulation meets game development',64,579,610,65,21,C.dim);
await img(s,'hero-board.png',710,173,430,430,'Real game board with two linked uncertain tiles and two fixed tiles');

s=page('Same tiles. Different merge chances.','0:25–1:35  ·  Live demo or screenshot fallback',
`These two situations look similar. Each tile has an equal chance of becoming 2 or 4. First, the independent tiles: a left move has a 50 percent chance of merging. Now the linked pair: the same individual probabilities produce a guaranteed match. We still do not know whether the merge will make 4 or 8. The forecast shows both possibilities before the next spawn. I will commit once. Qiskit calculates the probabilities and measurement outcomes behind this interaction. The player sees ordinary language instead of needing to interpret a circuit.`,
`Demo order: Independent button, preview left, point to 50%; Linked button, preview left, point to Guaranteed merge and the 4/8 outcomes; Commit left once. Allow about 25–30 seconds for clicks and audience attention. Do not play a full game. The two images are real forecast crops and serve as the fallback if the live demo fails. Resume on slide 3 by 1:35. Exact probabilities are simulator results, not sampled estimates. Independent expected gain is +3; linked is +6, but those extra statistics are optional Q&A material.`, 'Quantum_2048.ipynb, section 2\nquantum2048.py: Game.preview, QuantumGroup\nevidence/desktop-independent.jpg\nevidence/desktop-linked.jpg');
txt(s,'50%',64,162,430,90,80,C.gold,true);txt(s,'Independent tiles',64,260,510,48,29,C.white,true);
txt(s,'100%',690,162,480,90,80,C.mint,true);txt(s,'Linked pair',690,260,510,48,29,C.white,true);
await img(s,'independent-forecast.png',65,322,510,274,'Actual independent forecast showing a 50% chance to merge');
await img(s,'linked-forecast.png',690,322,510,274,'Actual linked forecast showing a guaranteed merge');
txt(s,'Each tile is 50/50 for 2 or 4. A successful merge makes 4 or 8.',64,611,1140,38,24,C.dim);

s=page('A choice between points and preserving the pair','1:35–2:20  ·  The player’s decision',
`A guaranteed pair is useful, but you still have to position it. In our harder-choice fixture, a left move contacts an outside 2. That gives an expected gain of two points, and the contact reveals the distant linked partner as well. An up move earns no immediate points and preserves both uncertain tiles while repositioning them. The screenshot shows the pair still uncertain after that up move. Preserving the connection costs space and extra turns. This creates a decision to evaluate, although we have not yet tested whether players find it well balanced.`,
`The expected +2 and +0 refer to the starting A harder choice fixture, before spawning. The screenshot shows the state AFTER committing up, including the new ordinary tile; do not present it as the starting board. If demonstrating live, load A harder choice and compare left/up forecasts before committing. Avoid the phrase 'guaranteed strategic depth': there is no player-study evidence. A pair spawn takes two cells and no special score bonus is awarded. In outside contacts that fail to merge, measurement can still reveal both tiles.`, 'Quantum_2048.ipynb, section 5\ntests/test_core.py: partner collapse and preservation assertion\nevidence/tradeoff-preserved.jpg');
txt(s,'LEFT: expected +2',64,179,560,56,35,C.gold,true);
txt(s,'Outside contact reveals\nthe distant partner.',64,247,560,90,29);
txt(s,'UP: immediate +0',64,382,560,56,35,C.mint,true);
txt(s,'Reposition while keeping\nboth tiles uncertain.',64,451,560,90,29);
await img(s,'preserved-board.png',730,175,420,420,'Actual board after an up move preserves the two uncertain linked tiles');
txt(s,'Actual board after preserving the pair',706,604,500,35,20,C.dim);

s=page('What Qiskit does','2:20–3:15  ·  One shared Python core',
`A single uncertain tile starts with a Hadamard preparation. A linked pair uses a Hadamard followed by CNOT, producing a Bell state. When a possible matching contact occurs, Qiskit performs a computational-basis measurement and returns the updated joint state. A distant partner can therefore become certain, and a revealed value does not reroll. For a preview, we read exact probabilities and evaluate copies of the game through the same merge rules. We never measure the live state during a preview. The browser calls this Python engine, while the notebook imports it directly. Four unresolved qubits keep exact forecasting small enough to run locally.`,
`Point to preparation, measurement, then forecasting. No code walkthrough is needed. Group states have at most two qubits and groups are independent of each other. With at most four unresolved qubits there are at most 16 basis branches. Preview equivalence relies on computational-basis measurements and no intervening gameplay gates. Persistent measurement uses the returned Qiskit Statevector. Controls and ordinary tile spawning use classical code; quantum tile probabilities/outcomes come from Qiskit. Simulator only; no IBM credentials or Aer required.`, ibm+'\nquantum2048.py: QuantumGroup, Game._reduce, Game.preview, Game.resolve\nQuantum_2048.ipynb, sections 3–4');
txt(s,'Preparation',64,184,540,55,36,C.mint,true);
txt(s,'Single tile: H\nLinked pair: H followed by CNOT',64,257,550,100,29);
txt(s,'Measurement',690,184,520,55,36,C.mint,true);
txt(s,'Possible contact resolves a tile.\nThe remaining joint state updates.',690,257,520,100,29);
txt(s,'Forecasting',64,422,540,55,36,C.mint,true);
txt(s,'Exact probabilities on copies\nSame movement and merge rules',64,495,550,100,29);
txt(s,'Shared implementation',690,422,520,55,36,C.mint,true);
txt(s,'Browser calls the Python core.\nNotebook imports that same core.',690,495,520,100,29);

s=page('Evidence from the executed notebook','3:15–4:20  ·  Correctness and coherence',
`The notebook executes from a fresh kernel without the browser or IBM credentials. Ten core tests check ordinary merge behavior, normalized states, partial measurement, repeated outcomes, and forecasts that leave the live state and RNG unchanged. The exact match probabilities are one half and one. Actual committed-game samples gave 198 merges out of 400 independent trials and 400 out of 400 linked trials. Matching correlations can also arise from classical shared randomness, so they alone do not demonstrate a quantum advantage or certify entanglement. Separately, our coherence comparison applies a second Hadamard to the prepared plus state. It gives zero with probability one. If we dephase first, that probability becomes one half. Both results come from Qiskit simulation.`,
`Spend roughly 25 seconds on execution/tests, then 35 seconds on the scientific distinction and chart. The chart shows exact P(0), not the sampled matching results. 'Coherent' means H|0> followed by H. 'Dephased' means remove off-diagonal entries of that prepared density matrix before the final H. This one-qubit test isolates coherence; it is not an entanglement test. The ten-test claim is from the executed notebook and documented core checks. Do not imply these are hardware data or a new run during the talk. Notebook has seven successfully executed code cells.`, 'Quantum_2048.ipynb, sections 2, 6–7\nquantum2048.py: interference\n'+ibm);
txt(s,String(D.core_tests)+' core tests passed',64,175,530,65,39,C.mint,true);
txt(s,'Fresh-kernel notebook execution\nPartial collapse and repeat outcomes\nNon-mutating forecasts',64,271,530,150,27);
txt(s,'Committed-game samples',64,466,530,45,27,C.white,true);
txt(s,`${D.independent.merges}/${D.independent.trials} independent\n${D.linked.merges}/${D.linked.trials} linked`,64,530,530,90,29,C.dim);
const chart=s.charts.add('bar',{
 position:{left:650,top:170,width:560,height:415},title:'P(0) after the final H',titleTextStyle:{fontSize:26,fill:C.white,bold:true},
 categories:['Coherent','Dephased'],series:[{name:'Probability of 0',values:[D.coherence.coherent,D.coherence.dephased],valuesFormatCode:'0%',fill:C.mint,points:[{idx:0,fill:C.mint},{idx:1,fill:C.gold}]}],
 hasLegend:false,barOptions:{direction:'column',grouping:'clustered',gapWidth:125},chartFill:C.bg,plotAreaFill:C.bg,chartLine:{fill:'none',width:0},plotAreaLine:{fill:'none',width:0},
 xAxis:{textStyle:{fontSize:23,fill:C.white},line:{fill:C.line,width:1},majorGridlines:null},
 yAxis:{min:0,max:1.2,majorUnit:.5,numberFormatCode:'0%',textStyle:{fontSize:19,fill:C.dim},line:{fill:'none',width:0},majorGridlines:{fill:C.line,width:.5}},
 dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0%',textStyle:{fontSize:25,fill:C.white,bold:true}}
});applyPresentationChartFont(chart,{fontFamily:'Arial'});
txt(s,'Local simulator. Matching correlations alone have a classical explanation.',64,616,1140,35,22,C.gold);

s=page('Joint probabilities become game decisions','4:20–5:00  ·  Contribution and close',
`Quantum 2048 has prior implementations, which we acknowledge. Our contribution is accurate visual merge forecasting tied to linked-tile decisions, with one reproducible core behind the game and notebook. We make the effect of a joint distribution visible before the player acts. Everything shown uses a local simulator, with no demonstrated speedup. Usability, balance, and learning benefits still need real player testing. The result is a concrete bridge from quantum state simulation to game development: players can see how relationships change the consequences of their next move.`,
`Finish the spoken talk here at five minutes. Slides 7–10 are optional Q&A material only. Suggested final sentence: 'Our contribution is turning joint quantum probabilities into understandable game decisions.' If judges ask what is new, discuss this implementation's forecasting/measurement contract and interaction design, not a global first. AI assisted implementation, writing and validation; disclose that accurately if asked. No source or visual assets were copied from the credited earlier games.`, 'https://github.com/nirbhaykwatra/Quantum2048\nhttps://github.com/gabrielecirulli/2048\nQuantum_2048.ipynb, sections 8 and sources');
txt(s,'The contribution',64,191,540,55,36,C.mint,true);
txt(s,'Understandable merge forecasts\nLinked-tile positioning decisions\nA reproducible game / notebook core',64,281,550,160,29);
txt(s,'What remains unproven',690,191,530,55,36,C.gold,true);
txt(s,'Player appeal and strategic balance\nLearning gains\nQuantum computational advantage',690,281,540,160,29);
txt(s,'A working bridge from quantum simulation to game development.',64,547,1120,84,35,C.white,true);

s=page('Appendix: exact outcomes and measured trials','Optional Q&A  ·  Outside the five-minute talk',
`Independent tiles have four equally likely basis outcomes. Two of them match, so the match chance is one half. The Bell pair supports only the two matching outcomes, so its chance is one.`,
`Bit labels are printed with qubit 0 on the right. Map 0 to tile 2 and 1 to tile 4. Pairs 22 and 44 merge into 4 and 8. Independent expected score is 0.25*4 + 0.25*8 = 3. Linked expected score is 0.5*4 + 0.5*8 = 6. The 198/400 sample is 49.5%, not exactly 50%, while 400/400 linked is 100%. Finite samples illustrate committed execution; the exact probabilities come directly from the statevector.`, 'Quantum_2048.ipynb, sections 2 and 7');
table(s,[['Quantity','Independent','Linked'],['Individual tile values','2 or 4, equally likely','2 or 4, equally likely'],['Possible joint outcomes','22, 24, 42, 44','22, 44'],['Exact match chance','50%','100%'],['Expected score gain','+3','+6'],['Observed merges','198 / 400 (49.5%)','400 / 400 (100%)']],64,176,1150,390,[370,390,390]);
txt(s,'Exact probabilities and finite samples answer different questions.',64,603,1140,45,25,C.dim);

s=page('Appendix: the measurement and forecast contract','Optional Q&A  ·  Implementation detail',
`The measurement rule is fixed before the forecast runs, so the preview and the committed move describe the same game.`,
`Process rows top-to-bottom for horizontal moves, columns left-to-right for vertical moves, and each line from the destination edge. Compress and compare candidates. Measure only when candidate supports overlap, destination tile then incoming tile. Failed uncertain contacts still resolve tiles and consume a turn. Returned post-measurement states condition remaining partners. Identities survive movement. A merge consumes both identities and creates a fixed tile that cannot merge again that swipe. A true no-op neither scores nor spawns. Win at 2048. A full board loses when all directions have zero probability of an active move. Reconnect reads state and does not replay a failed request. The model is an ideal statevector simulator, with at most two qubits per group and four unresolved tile qubits total.`, 'Quantum_2048.ipynb, section 1\nquantum2048.py: Game.lines, Game._reduce, Game.resolve, Game.preview, Game.status');
txt(s,'At contact',64,181,540,55,35,C.mint,true);
txt(s,'Resolve a possible match, even if it fails.\nUpdate any now-certain partner.\nKeep revealed values fixed.',64,267,550,170,28);
txt(s,'Before contact',690,181,530,55,35,C.mint,true);
txt(s,'Read exact Qiskit probabilities.\nEnumerate clones through one reducer.\nLeave the live state and RNG untouched.',690,267,540,170,28);
txt(s,'A tile merges once per swipe. A true no-op never spawns.\nForecast outcome boards exclude the next spawn.',64,529,1130,100,28,C.dim);

s=page('Appendix: demo sequence and judge questions','Optional Q&A  ·  Practical fallback',
`Use the notebook or supplied screenshots if the live application is unavailable.`,
`Before the talk: double-click Launch Quantum 2048.cmd, or run .venv\\Scripts\\python.exe launch.py, and keep the server running. Use the HTTP URL, not file://. Sequence: Independent > preview left > Linked > preview left > commit once > A harder choice > compare left/up. Fallback: screenshots on slide 2 and notebook sections 2–6. Q: Is this entanglement certification? A: The preparation is a Bell state, but its computational-basis correlations also occur in a classical mixture. Q: Is there an advantage? A: No advantage demonstrated. Q: Why Qiskit? A: It computes the actual state preparation, probabilities, evolution and collapse used by the game and notebook. Q: Are usability gains measured? A: No. A test protocol is provided. Q: What about hardware? A: No hardware runs are claimed. Q: Why no gate button in the game? A: Interference remains a notebook demonstration so the puzzle stays understandable.`, 'README.md\nQuantum_2048.ipynb, sections 2–8\nVERIFICATION.md');
txt(s,'Reliable demo',64,181,540,55,35,C.mint,true);
txt(s,'Independent: preview left\nLinked: preview left, commit once\nHarder choice: compare left and up\nFallback: notebook sections 2–6',64,267,550,210,28);
txt(s,'Short, accurate answers',690,181,530,55,35,C.gold,true);
txt(s,'Advantage: none demonstrated\nEntanglement proof: Z odds insufficient\nLearning gains: not measured\nHardware execution: not performed',690,267,540,210,28);
txt(s,'Launch with Launch Quantum 2048.cmd and keep the engine running.',64,573,1140,65,26,C.dim);

s=page('Appendix: sources and event alignment','Optional reference  ·  Not part of the timed close',
`The official project goal is a Python notebook that bridges quantum computing and a non-quantum field. Our field is game development.`,
`The official site requires a notebook and explanatory slides, and says judges use a simulator. No public scoring weights or rubric were found on the accessible event/registration pages when the outline was reviewed November 6, 2026. The five-minute length is the user's target, not a verified organizer limit. The event page and registration form disagree on presentation session times. Cutoff, upload destination, exact slide formats, AI/reuse eligibility and team identity still require human confirmation. Individual registration and live presentation for certificate eligibility remain human actions. AI assisted code, slides, notebook writing and verification. Credit the original 2048 concept and prior Quantum2048 implementation without claiming first-ever novelty.`,official+'\n'+ibm+'\nhttps://github.com/nirbhaykwatra/Quantum2048\nhttps://github.com/gabrielecirulli/2048');
txt(s,'Official goal: a notebook bridging quantum and another field.\nThis project connects Qiskit simulation with game development.',64,174,1150,98,29,C.mint,true);
txt(s,'Waterloo requirements and registration\nuwquantum.com/qiskit-fall-fest\nuwquantum.com/fall-fest-signup',64,329,570,140,23);
txt(s,'Qiskit API reference\nquantum.cloud.ibm.com/docs/en/api/\nqiskit/quantum_info',690,329,520,140,23);
txt(s,'Prior art and puzzle concept\ngithub.com/nirbhaykwatra/Quantum2048\ngithub.com/gabrielecirulli/2048',64,505,570,132,23,C.dim);
txt(s,'AI assistance disclosed\nNo copied prior-game code or assets\nNo public scoring weights found',690,505,530,132,23,C.dim);

for(let i=0;i<deck.slides.items.length;i++){
 const slide=deck.slides.items[i];
 const b=await deck.export({slide,format:'png',scale:1});await fs.writeFile(`build/five-minute/slides/${String(i+1).padStart(2,'0')}.png`,new Uint8Array(await b.arrayBuffer()));
 const layout=await slide.export({format:'layout'});await fs.writeFile(`build/five-minute/slides/${String(i+1).padStart(2,'0')}.json`,await layout.text());
}
await fs.writeFile('output/Quantum_2048_Five_Minute_Speaker_Notes.md','# Quantum 2048: speaker notes\n\nSix main slides target five minutes. Slides 7–10 are optional appendix material.\n\n'+talk.map(t=>`## ${t.n}. ${t.title}\n\n**${t.timing}**\n\n### Spoken script\n\n${t.script}\n\n### Presenter cues and optional detail\n\n${t.detail}\n\n### Sources\n\n${t.sources}`).join('\n\n'));
await (await PresentationFile.exportPptx(deck)).save('build/five-minute/draft.pptx');
const result=await finalizePresentation({workspaceDir:root,candidatePath:path.join(root,'build/five-minute/draft.pptx'),finalPath:path.join(root,'output/Quantum_2048_Five_Minute.pptx'),pythonExecutable:runtime+'/python/python.exe',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit','--require-native-table-slide','7'],requiredNativeChartOwnerSlides:[5],requiredNativeTableOwnerSlides:[7],materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:path.join(root,'build/five-minute/validation.json')});
console.log(JSON.stringify({finalPath:result.finalPath,slideCount:10,mainSlides:6,validation:result.presentationLayout}));
