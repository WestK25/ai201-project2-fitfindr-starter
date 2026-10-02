"""Run genuine demo scenarios with isolated preferences; save only actual results."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from agent import run_agent
from memory import reset_style_profile
from tools import search_listings, suggest_outfit, create_fit_card, compare_price, MODEL
from trends import get_trends
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

HAPPY_QUERY = 'vintage graphic tee under $30, size M'
FAILURE_QUERY = 'designer ballgown size XXS under $5'
RETRY_QUERY = 'vintage graphic tee size XXS under $1'
MEMORY_FIRST = 'vintage graphic tee under $30, size M. I prefer baggy streetwear and chunky sneakers.'
MEMORY_SECOND = '90s track jacket size M under $50'


def run_scenarios(scenario):
    report = {'ran_at': datetime.now(timezone.utc).isoformat(), 'model': MODEL, 'scenarios': {}}
    results = report['scenarios']
    if scenario in ('all', 'happy'):
        result = run_agent(HAPPY_QUERY, get_example_wardrobe())
        results['happy'] = result
        result['identity_verified'] = result['selected_item'] is result['search_results'][0] if result['search_results'] else False
    if scenario in ('all', 'failure'):
        item = search_listings('vintage graphic tee', max_price=50)[0]
        results['deliberate_failures'] = {
            'search_tool': search_listings('designer ballgown', size='XXS', max_price=5),
            'agent': run_agent(FAILURE_QUERY, get_example_wardrobe()),
            'empty_caption': create_fit_card('', item),
        }
    if scenario in ('all', 'empty'):
        results['empty_wardrobe'] = run_agent(HAPPY_QUERY, get_empty_wardrobe())
    if scenario in ('all', 'retry'):
        results['retry'] = run_agent(RETRY_QUERY, get_example_wardrobe())
    if scenario in ('all', 'price', 'trend'):
        item = search_listings('vintage graphic tee', 'M', 30)[0]
        results['price'] = compare_price(item)
        results['trend'] = get_trends(item)
    if scenario in ('all', 'memory'):
        reset_style_profile()
        first = run_agent(MEMORY_FIRST, get_example_wardrobe())
        child = subprocess.check_output([sys.executable, '-c',
            'import json; from memory import load_style_profile; print(json.dumps(load_style_profile()))'], text=True)
        second = run_agent(MEMORY_SECOND, get_example_wardrobe())
        results['memory'] = {'first': first, 'new_process_profile': json.loads(child), 'second': second,
            'persisted_and_reused': first['style_profile_used']['likes'] == json.loads(child)['likes'] == second['style_profile_used']['likes'] and bool(second['style_profile_used']['likes'])}
    failures = []
    for name in ('happy', 'empty_wardrobe', 'retry'):
        if name in results and results[name]['error']:
            failures.append(name)
    if 'memory' in results:
        m = results['memory']
        if not m['persisted_and_reused'] or m['first']['error'] or m['second']['error']:
            failures.append('memory generation')
    if 'deliberate_failures' in results:
        f = results['deliberate_failures']
        if f['search_tool'] != [] or not f['agent']['error'] or any(t['tool'] == 'suggest_outfit' for t in f['agent']['tool_trace']) or not f['empty_caption'].startswith('Error:'):
            failures.append('failure guards')
    report['failed_scenarios'] = failures
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', choices=['all', 'happy', 'failure', 'empty', 'retry', 'price', 'trend', 'memory'], default='all')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    # Demo inputs are synthetic; never overwrite the actual local user's profile.
    with TemporaryDirectory(prefix='fitfindr-demo-') as directory:
        os.environ['FITFINDR_STATE_DIR'] = directory
        report = run_scenarios(args.scenario)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(exist_ok=True, parents=True)
        args.output.write_text(text + '\n')
    print(text)
    raise SystemExit(bool(report['failed_scenarios']))
