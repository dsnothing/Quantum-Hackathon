# Bundled synthetic scenarios

All geography, names, populations and fixed road times are original fictional
demonstration data, released under CC0-1.0. Coordinates do not identify actual
roads or emergency resources. The local background is illustration, not a
survey or flood map. Travel times include illustrative access and turn delays.

`riverbend.json`: 40 road nodes, 8 candidate hubs, 15 communities (9,200 total
population), one bidirectional river crossing, one-way ridge roads, and a
disconnected island of 140 people. Default planning uses exactly 3 hubs and a
12-minute response threshold. Exact enumeration gives 9,060 people covered
with hubs 01, 07, 08. Closing `bridge-main` lowers the exact optimum to 8,140
and changes the selected deployment; some optimum sets tie. This is a
preparedness tradeoff, not an operational performance estimate.

`upland.json`: a second synthetic scenario using the same geography with slower
north/south travel, a slow northern detour bridge, and larger ridge demand.

`background.geojson`: offline water, park and district-block polygons. Feature
properties `kind` (`water`, `park`, `block`) and `name` support map styling.
Road geometries are in each scenario's `edges[].geometry`. Node and community
names are available to the UI. The `ridge-oneway` and `ridge-descent` roads are
directed; all other roads close both directions under their single ID.

`benchmark-variations.json`: frozen nominal, bridge, ridge, combined-closure
and slow-detour perturbations. They evaluate fixed closures; they do not
constitute robust optimization.

Regenerate JSON deterministically from the application directory with
`python scenarios/generate_fixtures.py`. Revisions are content hashes computed
by `backend.domain.scenario_revision`, so regenerated changes invalidate old
planning requests as intended.
