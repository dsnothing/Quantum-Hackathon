export type Node = {id:string;lon:number;lat:number};
export type Road = {id:string;fromNodeId:string;toNodeId:string;travelMinutes:number;bidirectional:boolean;name?:string;geometry?:{type:'LineString';coordinates:number[][]}};
export type Community = {id:string;nodeId:string;name?:string;population:number;priorityMultiplier:number};
export type Hub = {id:string;nodeId:string;name?:string};
export type Scenario = {id:string;title:string;revision?:string;schemaVersion:string;nodes:Node[];edges:Road[];communities:Community[];candidateHubs:Hub[];provenance:{kind:string;license:string;transformationNotes:string;sources:string[]}};
export type Assignment = {communityId:string;hubId:string|null;travelMinutes:number|null;covered:boolean;pathEdgeIds?:string[];pathNodeIds?:string[]};
export type Plan = {solver:string;problemHash:string;runHash:string;selectedHubIds:string[];feasible:boolean;deployedHubCount:number;coveredPopulation:number;totalPopulation:number;weightedCoverage:number;uncoveredCommunityIds:string[];assignments:Assignment[];timing:Record<string,number>;provenance:Record<string,unknown>;diagnostics:Record<string,unknown>};
export type Run = {runId:string;status:string;problemHash?:string;result?:Plan;error?:{code:string;message:string};[key:string]:unknown};
export type Inputs = {scenarioId:string;scenarioRevision:string;closedEdgeIds:string[];hubCount:number;responseTimeMinutes:number;solver:string;seed:number;qaoa?:{layers:number;shots:number;maxEvaluations:number;starts:number}};
export async function api<T>(path:string, options?:RequestInit):Promise<T>{
 const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),15000);
 try{const response=await fetch('/api/v1'+path,{...options,signal:controller.signal,headers:{'Content-Type':'application/json',...options?.headers}});const data=await response.json();if(!response.ok)throw new Error(data.error?.message||`The service returned ${response.status}.`);return data as T;}catch(e){if(e instanceof TypeError||e instanceof DOMException)throw new Error('The local planning service is unavailable. Start ReliefGrid, then reconnect.');throw e;}finally{clearTimeout(timer);}
}
export const post=(body:unknown):RequestInit=>({method:'POST',body:JSON.stringify(body)});
export function download(value:unknown,name:string,type='application/json'){const url=URL.createObjectURL(new Blob([typeof value==='string'?value:JSON.stringify(value,null,2)],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
