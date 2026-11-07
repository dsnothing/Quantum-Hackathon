import type {Plan} from './api';

const num=(value:unknown)=>typeof value==='number'?new Intl.NumberFormat('en-CA',{maximumFractionDigits:2}).format(value):'—';
const percent=(value:unknown)=>typeof value==='number'?`${num(value*100)}%`:'—';

export function EvidencePanel({plan}:{plan:Plan}){
 const d=plan.diagnostics;
 const resources=(d.resources||{}) as Record<string,unknown>;
 const history=(Array.isArray(d.convergence)?d.convergence:[]) as {evaluation:number;expectedWeightedCoverage:number;bestExpectedWeightedCoverage:number}[];
 const values=history.map(x=>x.bestExpectedWeightedCoverage);
 const maximum=Math.max(1,...values,Number(d.optimalWeightedCoverage)||0);
 const points=history.map((x,i)=>`${42+i*350/Math.max(1,history.length-1)},${122-x.bestExpectedWeightedCoverage/maximum*100}`).join(' ');
 const counts=Object.entries((d.counts||{}) as Record<string,number>).sort((a,b)=>b[1]-a[1]).slice(0,6);
 return <section className="solver-evidence" aria-label="Measured solver evidence">
 <h4>{plan.solver==='qaoa'?'Circuit and measurement':'Computation record'}</h4>
 <div className="evidence-metrics">
 {(plan.solver==='qaoa'?[['Qubits',num(resources.qubits)],['Circuit depth',num(resources.depth)],['Two-qubit gates',num(resources.twoQubitGates)],['Shots',num(d.shots)],['Feasible samples',percent(d.feasibleFraction)],['Ideal optimum probability',percent(d.optimumProbability)]]:[['Objective evaluations',num(d.evaluations)],['Proven optimal',d.provenOptimal?'Yes':'No'],['Selected coverage',num(plan.weightedCoverage)]]).map(([label,value])=><div key={label}><small>{label}</small><strong>{value}</strong></div>)}
 </div>
 {plan.solver==='qaoa'&&<p className="evidence-caption">Expected weighted coverage {num(d.expectedWeightedCoverage)}. Best sampled plan {num(plan.weightedCoverage)}. These are different measures; the recommended plan is the best feasible measured sample.</p>}
 {history.length>0&&<figure className="convergence"><figcaption>Best expected coverage during optimization</figcaption><svg viewBox="0 0 440 155" role="img" aria-label={`Convergence over ${history.length} circuit evaluations; best expected coverage ${num(values[values.length-1])}`}><path d="M42 22V122H392" fill="none" stroke="#b4c0bc"/><path d="M42 72H392" stroke="#e6ece8" strokeDasharray="3 4"/><polyline points={points} fill="none" stroke="#087f78" strokeWidth="2.5"/><text x="37" y="26" textAnchor="end">{num(maximum)}</text><text x="37" y="125" textAnchor="end">0</text><text x="42" y="142">1</text><text x="392" y="142" textAnchor="end">{history.length} evaluations</text></svg></figure>}
 {counts.length>0&&<div><h4>Most frequent measured configurations</h4><table className="sample-table"><thead><tr><th>Bitstring</th><th>Count</th><th>Share</th></tr></thead><tbody>{counts.map(([bits,count])=><tr key={bits}><td><code>{bits}</code></td><td>{count}</td><td>{percent(count/Number(d.shots))}</td></tr>)}</tbody></table><p className="evidence-caption">Rightmost bit represents the first hub in the ordered model. Frequency does not by itself establish solution quality.</p></div>}
 <details><summary>Full reproducibility record</summary><pre>{JSON.stringify(d,null,2)}</pre></details>
 </section>
}

export function StressResults({data}:{data:Record<string,unknown>}){
 const variants=(Array.isArray(data.variants)?data.variants:[]) as {title:string;closedEdgeIds:string[];coveredPopulation:number;weightedCoverage:number}[];
 const maximum=Math.max(1,...variants.map(v=>v.coveredPopulation));
 return <div className="stress-results"><div className="stress-summary"><span>Nominal coverage <strong>{num(data.nominalCoveredPopulation)}</strong></span><span>Worst observed coverage <strong>{num(data.worstCoveredPopulation)}</strong></span></div><table><thead><tr><th>Scenario</th><th>Population served</th><th>Access retained</th></tr></thead><tbody>{variants.map((v,i)=><tr key={i}><td>{v.title}<small>{v.closedEdgeIds.length} closed roads</small></td><td>{num(v.coveredPopulation)}</td><td><span className="stress-bar"><i style={{width:`${v.coveredPopulation/maximum*100}%`}}/></span></td></tr>)}</tbody></table><p className="evidence-caption">The hub sites stay fixed in every row. This measures these specific disruptions, not every possible emergency.</p></div>
}
