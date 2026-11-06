"""Optional local UI fixtures: python tests/ui_fixture_server.py win|loss PORT."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from quantum2048 import Game
g=Game();g.board=[None]*16;g.groups={}
if sys.argv[1]=='win':
    g.add_classic(0,1024);g.add_classic(1,1024)
else:
    for i in range(16):g.add_classic(i,2 if (i//4+i%4)%2 else 4)
server.game=g
server.ThreadingHTTPServer(('127.0.0.1',int(sys.argv[2])),server.Handler).serve_forever()
