"""Local, single-player stdlib server. No accounts, telemetry, or remote services."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Lock
import json
from quantum2048 import Game

ROOT = Path(__file__).parent
game = Game()
lock = Lock()

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'web'), **kwargs)

    def do_GET(self):
        if self.path == '/api/state':
            with lock: self.send_json(game.view(True))
        else: super().do_GET()

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers(); self.wfile.write(body)

    def do_POST(self):
        global game
        try:
            data = json.loads(self.rfile.read(min(int(self.headers.get('Content-Length', 0)), 4096)))
            with lock:
                if self.path == '/api/restart':
                    scenario = data.get('scenario')
                    if scenario not in (None, 'linked', 'independent', 'tradeoff'): raise ValueError('Unknown scenario')
                    game = Game(seed=data.get('seed', 1), scenario=scenario)
                    result = game.view(True)
                elif self.path == '/api/preview': result = game.preview(data['direction'])
                elif self.path == '/api/move':
                    game.move(data['direction']); result = game.view(True)
                else: raise ValueError('Unknown endpoint')
            self.send_json(result)
        except (ValueError, KeyError, TypeError) as exc: self.send_json({'error': str(exc)}, 400)

if __name__ == '__main__':
    print('Quantum 2048: http://127.0.0.1:8000 (Ctrl+C to stop)', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8000), Handler).serve_forever()
