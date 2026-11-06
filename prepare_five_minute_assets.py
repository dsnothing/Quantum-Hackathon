"""Crop real interface evidence and read the executed notebook's results."""
from pathlib import Path
from PIL import Image
import json, re

root=Path(__file__).resolve().parent
dest=root/'build/five-minute';dest.mkdir(parents=True,exist_ok=True)
# These are crops of real screenshots, not reconstructed or generated gameplay.
Image.open(root/'evidence/mobile-board.png').save(dest/'hero-board.png')
for name in ['linked','independent']:
    Image.open(root/f'evidence/desktop-{name}.jpg').crop((690,332,1178,565)).save(dest/f'{name}-forecast.png')
Image.open(root/'evidence/tradeoff-preserved.jpg').crop((18,477,372,831)).save(dest/'preserved-board.png')
nb=json.loads((root/'Quantum_2048.ipynb').read_text(encoding='utf-8'))
code=[c for c in nb['cells'] if c['cell_type']=='code']
assert all(c['execution_count'] is not None for c in code)
assert not any(o['output_type']=='error' for c in code for o in c['outputs'])
output='\n'.join(''.join(o.get('text',[])) for c in code for o in c['outputs'] if o['output_type']=='stream')
assert 'Ran 10 tests' in output and 'OK' in output
assert 'coherent P(0), P(1): [1. 0.]' in output
assert 'dephased P(0), P(1): [0.5 0.5]' in output
assert 'independent match probability: 0.5' in output
assert 'linked match probability: 1.0' in output
ind=re.search(r'independent (\d+)/(\d+) swipes merged',output)
linked=re.search(r'linked (\d+)/(\d+) swipes merged',output)
assert ind and linked
results={'independent':{'exact':.5,'merges':int(ind[1]),'trials':int(ind[2])},
         'linked':{'exact':1.,'merges':int(linked[1]),'trials':int(linked[2])},
         'coherence':{'coherent':1.,'dephased':.5},'core_tests':10,'executed_cells':len(code)}
(dest/'results.json').write_text(json.dumps(results,indent=2),encoding='utf8')
print('Prepared screenshot crops and verified notebook results.')
