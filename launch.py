"""Start the local engine and open its HTTP page; reuse an existing game server."""
import json
import sys
import urllib.request
import urllib.error
import webbrowser

URL='http://127.0.0.1:8000'

def existing_game():
    # A local connection should not be routed through a configured HTTP proxy.
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(URL+'/api/health',timeout=2) as response:
            return json.load(response).get('app')=='quantum-2048'
    except (urllib.error.URLError,TimeoutError,ValueError,OSError):
        return False

def main():
    if existing_game():
        print('Opening the running game at '+URL)
        webbrowser.open(URL+'/')
        return 0
    try:
        from server import run
    except ImportError:
        print('Install the project dependencies first:')
        print(f'"{sys.executable}" -m pip install -r requirements.txt')
        return 1
    try:
        run(open_browser=True)
    except OSError as exc:
        print('Could not start the game on '+URL+'. Close the previous server or other app using port 8000, then retry.')
        print(str(exc))
        return 1
    return 0

if __name__=='__main__':
    raise SystemExit(main())
