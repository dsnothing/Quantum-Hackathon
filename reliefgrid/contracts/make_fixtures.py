"""Regenerate tiny golden contracts independently of graph/solver modules."""
from pathlib import Path
import json
from reliefgrid.backend.domain import *

ROOT = Path(__file__).resolve().parent / "fixtures"


def write(name, model):
    data = model.model_dump(mode="json") if isinstance(model, Contract) else model
    (ROOT / f"{name}.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def generate():
    scenario = Scenario(id="golden-tiny", title="Synthetic three-community contract fixture",
        provenance=ScenarioProvenance(kind="synthetic", license="CC0-1.0", transformationNotes="Invented coordinates and populations; no operational use."),
        nodes=[Node(id=f"n{i}",lon=-80+i*.01,lat=43) for i in range(3)],
        edges=[Edge(id="bridge",fromNodeId="n0",toNodeId="n1",travelMinutes=5,bidirectional=True)],
        communities=[Community(id=f"c{i}",nodeId=f"n{i}",population=(100,60,40)[i]) for i in range(3)],
        candidateHubs=[Hub(id="a",nodeId="n0"),Hub(id="b",nodeId="n1")])
    revision = scenario_revision(scenario)
    request = PlanningRequest(scenarioId=scenario.id,scenarioRevision=revision,hubCount=1,responseTimeMinutes=4,solver="greedy",seed=42)
    payload = dict(modelVersion=MODEL_VERSION,scenarioRevision=revision,hubIds=("a","b"),communityIds=("c0","c1","c2"),hubCount=1,demandWeights=(100.,60.,40.),populations=(100.,60.,40.),coverageMatrix=((True,False),(False,True),(False,False)),travelMinutes=((0.,5.),(5.,0.),(None,None)),responseTimeMinutes=4.,closedEdgeIds=())
    prepared = PreparedProblem(problemHash=problem_hash(**payload),**payload)
    result = PlanResult(solver="greedy",problemHash=prepared.problemHash,runHash=run_hash(prepared,request),selectedHubIds=("a",),feasible=True,deployedHubCount=1,coveredPopulation=100,totalPopulation=200,weightedCoverage=100,uncoveredCommunityIds=("c1","c2"),assignments=(Assignment(communityId="c0",hubId="a",travelMinutes=0,covered=True),Assignment(communityId="c1",hubId=None,travelMinutes=None,covered=False),Assignment(communityId="c2",hubId=None,travelMinutes=None,covered=False)),provenance=Provenance(scenarioRevision=revision,seed=42,executionMode="contract-fixture",parameters={"label":"Fixed golden example, not a live computation"}))
    for name, model in (("scenario.valid",scenario),("request.valid",request),("prepared.valid",prepared),("result.valid",result)):
        write(name,model)
    invalid = scenario.model_dump(mode="json")
    invalid["edges"][0]["travelMinutes"] = 0
    write("scenario.invalid-zero-time", invalid)
    invalid_request = request.model_dump(mode="json")
    invalid_request["hubCount"] = -1
    write("request.invalid-negative-k", invalid_request)
    write("job.succeeded",dict(runId="golden-success",status="succeeded",problemHash=prepared.problemHash,runHash=result.runHash,result=result.model_dump(mode="json"),error=None))
    write("job.failed",dict(runId="golden-failure",status="failed",problemHash=prepared.problemHash,runHash=result.runHash,result=None,error={"code":"SOLVER_FAILED","message":"Golden mock failure. Retry with greedy.","retryable":True}))


if __name__ == "__main__":
    generate()
