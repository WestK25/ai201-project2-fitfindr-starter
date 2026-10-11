"""Launch the actual app.py, check HTTP + a real UI event, then stop cleanly."""
import argparse
from datetime import datetime, timezone
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


def main(output_path=None):
    report = {"ran_at": datetime.now(timezone.utc).isoformat()}
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
                from demo_scenarios import HAPPY_QUERY, FAILURE_QUERY
                from validation_helpers import check_outputs
                from utils.data_loader import load_listings, get_example_wardrobe
                from tools import MODEL
                happy = client.predict(HAPPY_QUERY, 'Example wardrobe', api_name='/' + name)
                details = json.loads(happy[3])
                trace = details['tool_trace']
                item_id = next(t['inputs']['item_id'] for t in trace if t['tool'] == 'suggest_outfit')
                item = next(i for i in load_listings() if i['id'] == item_id)
                validation = check_outputs(item, get_example_wardrobe(), happy[1], happy[2])
                validation['checks']['all_three_required_tools'] = all(any(t['tool'] == tool and t['output'].get('success', True) for t in trace) for tool in ('search_listings', 'suggest_outfit', 'create_fit_card'))
                validation['checks']['real_trend_application_visible'] = details['trend_info']['relevant_trend']['term'] in happy[1] and 'Trend note' in happy[1]
                validation['all_passed'] = all(validation['checks'].values())
                failure = client.predict(FAILURE_QUERY, 'Example wardrobe', api_name='/' + name)
                failure_details = json.loads(failure[3])
                failure_ok = 'No matching listings' in failure[0] and failure[1:3] == ('', '') and all(t['tool'] == 'search_listings' for t in failure_details['tool_trace'])
                report.update({'model': MODEL, 'url': url, 'http_config': '200 OK', 'components': len(config['components']),
                               'event_api': name, 'empty_query_result': result[:3],
                               'happy_query': HAPPY_QUERY, 'happy_outputs': happy[:3], 'happy_details': details,
                               'validation': validation, 'failure_query': FAILURE_QUERY,
                               'failure_outputs': failure[:3], 'failure_details': failure_details,
                               'deliberate_failure_passed': failure_ok})
            finally:
                process.send_signal(signal.SIGINT)
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    process.wait(timeout=5)
            report['server_exit_code'] = process.returncode
            report['all_passed'] = report['validation']['all_passed'] and report['deliberate_failure_passed'] and process.returncode == 0
            text = json.dumps(report, indent=2, ensure_ascii=False)
            if output_path:
                output_path.write_text(text + '\n')
            print(text)
            assert report['all_passed'], 'Real Gradio interaction checks failed; inspect recorded outputs.'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    main(parser.parse_args().output)
