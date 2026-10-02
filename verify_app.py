"""Launch the actual app.py, check HTTP + a real UI event, then stop cleanly."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
from urllib.request import urlopen


def main():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
    url = f'http://127.0.0.1:{port}'
    with TemporaryDirectory(prefix='fitfindr-app-check-') as directory:
        env = dict(os.environ, GRADIO_SERVER_PORT=str(port), GRADIO_ANALYTICS_ENABLED='False', FITFINDR_STATE_DIR=directory, PYTHONUNBUFFERED='1')
        log = Path(directory) / 'server.log'
        with log.open('w') as output:
            process = subprocess.Popen([sys.executable, 'app.py'], stdout=output, stderr=subprocess.STDOUT, env=env)
            try:
                for _ in range(80):
                    if process.poll() is not None:
                        raise RuntimeError('App exited before startup; inspect local server log.')
                    try:
                        with urlopen(url + '/config', timeout=1) as response:
                            config = json.load(response)
                        break
                    except OSError:
                        time.sleep(.25)
                else:
                    raise RuntimeError('App did not start within 20 seconds.')
                from gradio_client import Client
                client = Client(url, verbose=False)
                names = [d.get('api_name') for d in config['dependencies']]
                name = next(n for n in names if n and n.startswith('handle_query_with_details'))
                result = client.predict('', 'Example wardrobe', api_name='/' + name)
                assert len(result) == 4 and 'Enter an item' in result[0] and result[1:3] == ('', '')
                print(json.dumps({'url': url, 'http_config': '200 OK', 'components': len(config['components']),
                                  'event_api': name, 'empty_query_result': result[:3], 'server_stopped': 'SIGINT in finally'}, indent=2))
            finally:
                process.send_signal(signal.SIGINT)
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    process.wait(timeout=5)
            print('Server exited:', process.returncode)


if __name__ == '__main__':
    main()
