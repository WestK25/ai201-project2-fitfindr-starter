import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import timedelta
from unittest.mock import MagicMock
from types import SimpleNamespace

import httpx
import pytest
import agent
import memory
import tools
import trends
from utils.data_loader import get_example_wardrobe, load_listings


@pytest.fixture
def item():
    return load_listings()[1]


def fake_generation(monkeypatch):
    monkeypatch.setattr(agent, 'suggest_outfit', lambda *a: 'Valid outfit.')
    monkeypatch.setattr(agent, 'create_fit_card', lambda *a: 'Valid caption.')


def test_actual_price_peers(item):
    result = tools.compare_price(item)
    assert result['assessment'] == 'good deal'
    assert set(result['comparable_ids']) == {'lst_006', 'lst_033'}
    assert result['median_price'] == 21.5 and result['comparable_count'] == 2
    assert 'mock listings' in result['reasoning']


@pytest.mark.parametrize('price,assessment', [(10, 'good deal'), (20, 'fair price'), (30, 'above comparable range')])
def test_price_thresholds(item, monkeypatch, price, assessment):
    selected = dict(item, price=price)
    peers = [dict(item, id=f'p{i}', price=20) for i in range(2)]
    monkeypatch.setattr(tools, 'load_listings', lambda: [selected, *peers])
    result = tools.compare_price(selected)
    assert result['assessment'] == assessment
    assert item['id'] not in result['comparable_ids']


def test_no_unrelated_comparables(item, monkeypatch):
    monkeypatch.setattr(tools, 'load_listings', lambda: [item, dict(item, id='wrong', title='A denim jacket')])
    result = tools.compare_price(item)
    assert result['assessment'] == 'insufficient data' and result['median_price'] is None


def test_optional_price_failure(item, monkeypatch):
    def broken():
        raise FileNotFoundError('private detail')
    monkeypatch.setattr(tools, 'load_listings', broken)
    assert tools.compare_price(item)['assessment'] == 'unavailable'


def test_memory_two_interactions(monkeypatch):
    fake_generation(monkeypatch)
    first = agent.run_agent('vintage graphic tee under $30, size M. I prefer baggy streetwear and chunky sneakers.', get_example_wardrobe())
    captured = []
    def suggest(item, wardrobe):
        captured.append(wardrobe['_style_profile'])
        return 'A second outfit.'
    monkeypatch.setattr(agent, 'suggest_outfit', suggest)
    second = agent.run_agent('90s track jacket size M under $50', get_example_wardrobe())
    assert first['style_profile_used']['likes'] == ['baggy', 'chunky sneakers', 'streetwear']
    assert captured[0]['likes'] == second['style_profile_used']['likes'] == first['style_profile_used']['likes']
    assert second['error'] is None


def test_memory_survives_new_process():
    memory.update_style_profile('I love grunge and black. I avoid pink.')
    output = subprocess.check_output([sys.executable, '-c', 'import json; from memory import load_style_profile; print(json.dumps(load_style_profile()))'], text=True, env=os.environ.copy())
    profile = json.loads(output)
    assert profile['likes'] == ['black', 'grunge'] and profile['dislikes'] == ['pink']


def test_memory_negation_and_reset():
    memory.update_style_profile('I prefer streetwear, not pink.')
    memory.update_style_profile("I don't like black. I love pink.")
    profile = memory.load_style_profile()
    assert 'pink' in profile['likes'] and 'pink' not in profile['dislikes'] and 'black' in profile['dislikes']
    assert 'reset' in memory.reset_style_profile()
    assert memory.load_style_profile()['likes'] == []


@pytest.mark.parametrize('content', ['not json', '[]', '{"likes": "baggy"}', '{"likes": [42], "dislikes": []}'])
def test_malformed_memory(content):
    directory = memory.state_directory()
    directory.mkdir()
    (directory / 'style_profile.json').write_text(content)
    assert memory.load_style_profile()['warning']


def test_search_is_not_a_preference():
    assert memory.update_style_profile('vintage graphic tee size M')['likes'] == []


def test_memory_write_failure(monkeypatch):
    def denied(*a):
        raise PermissionError()
    monkeypatch.setattr(memory, 'atomic_json', denied)
    result = memory.update_style_profile('I love grunge.')
    assert result['likes'] == ['grunge'] and 'this interaction only' in result['warning']


# Synthetic HTML fixture, never represented as a real fetched source.
HTML = '<html><p>Neo Nostalgia: A fixture heading</p><p>Vintage and 90s styling blends earlier eras through expressive layering and personal choices.</p><p>Modern Uniforms: A fixture heading</p><p>Neutral tailoring, button shirts and workwear jackets provide repeatable outfit combinations.</p></html>'


def mock_source(monkeypatch):
    response = httpx.Response(200, text=HTML, request=httpx.Request('GET', trends.SOURCE_URL))
    calls = []
    def get(*args, **kwargs):
        calls.append((args, kwargs))
        return response
    monkeypatch.setattr(trends.httpx, 'get', get)
    return calls


def test_trend_live_and_cache(item, monkeypatch):
    calls = mock_source(monkeypatch)
    result = trends.get_trends(item)
    assert result['status'] == 'live' and result['relevant_trend']['term'] == 'Neo Nostalgia'
    assert result['source_url'] == trends.SOURCE_URL and len(result['content_sha256']) == 64
    assert calls[0][1]['timeout'] == 6.0
    second = trends.get_trends(item)
    assert second['status'] == 'cached' and len(calls) == 1


def test_timeout_uses_only_verified_cache(item, monkeypatch):
    mock_source(monkeypatch)
    trends.get_trends(item)
    path = memory.state_directory() / 'trends.json'
    cache = json.loads(path.read_text())
    cache['retrieved_at'] = (trends._now() - timedelta(days=2)).isoformat()
    path.write_text(json.dumps(cache))
    def timeout(*args, **kwargs):
        raise httpx.ReadTimeout('private data')
    monkeypatch.setattr(trends.httpx, 'get', timeout)
    result = trends.get_trends(item)
    assert result['status'] == 'cached' and 'refresh failed' in result['warning']
    cache['retrieved_at'] = (trends._now() - timedelta(days=31)).isoformat()
    path.write_text(json.dumps(cache))
    result = trends.get_trends(item)
    assert result['status'] == 'unavailable' and not result['terms']


def test_trend_timeout_no_cache(item, monkeypatch):
    def timeout(*args, **kwargs):
        raise httpx.ReadTimeout('private data')
    monkeypatch.setattr(trends.httpx, 'get', timeout)
    result = trends.get_trends(item)
    assert result['status'] == 'unavailable' and 'private' not in result['warning']
    assert not (memory.state_directory() / 'trends.json').exists()


def test_parser_drift_is_unavailable(item, monkeypatch):
    monkeypatch.setattr(trends.httpx, 'get', lambda *a, **k: httpx.Response(200, text='<p>No actual trend headings</p>', request=httpx.Request('GET', trends.SOURCE_URL)))
    assert trends.get_trends(item)['status'] == 'unavailable'


def test_no_forced_irrelevant_trend(monkeypatch):
    mock_source(monkeypatch)
    result = trends.get_trends({'title': 'Quartz pendant', 'style_tags': [], 'description': 'Mineral jewelry'})
    assert result['status'] == 'live' and result['relevant_trend'] is None


def test_expired_report_is_not_current(item, monkeypatch):
    monkeypatch.setattr(trends, '_now', lambda: __import__('datetime').datetime(2027, 1, 1, tzinfo=__import__('datetime').timezone.utc))
    assert trends.get_trends(item)['status'] == 'unavailable'


def test_trends_and_profile_change_outfit_request(item, monkeypatch):
    mock_source(monkeypatch)
    context = trends.get_trends(item)
    received = []
    def generate(system, payload, temperature):
        received.append(payload)
        return {'looks': [{'wardrobe_ids': ['w_001', 'w_007'], 'advice': 'A relaxed tuck and chunky silhouette lean into vintage layering.'}],
                'trend_used': 'Neo Nostalgia', 'trend_application': 'The vintage tee and baggy denim mix eras with an easy streetwear silhouette.'}
    monkeypatch.setattr(tools, '_generate_json', generate)
    wardrobe = get_example_wardrobe() | {'_trend_info': context, '_style_profile': {'likes': ['baggy'], 'dislikes': []}}
    result = tools.suggest_outfit(item, wardrobe)
    assert received[0]['style_profile']['likes'] == ['baggy']
    assert received[0]['relevant_trend']['term'] == 'Neo Nostalgia'
    assert 'Trend note — Neo Nostalgia' in result and 'mix eras' in result and trends.SOURCE_URL in result


def test_retry_recovers_and_changes_visible(monkeypatch):
    fake_generation(monkeypatch)
    result = agent.run_agent('vintage graphic tee size XXS under $30', get_example_wardrobe())
    assert result['error'] is None and len(result['retry_history']) == 2
    assert result['retry_history'][1]['changed'] == ['size']
    assert result['parsed']['size'] == 'XXS'
    assert 'removed size' in result['warnings'][0]


def test_budget_retry_recovers(monkeypatch):
    fake_generation(monkeypatch)
    result = agent.run_agent('vintage graphic tee size XXS under $1', get_example_wardrobe())
    assert result['error'] is None and len(result['retry_history']) == 3
    assert result['retry_history'][-1]['changed'] == ['size', 'max_price']
    assert result['selected_item']['price'] > 1


def test_no_unnecessary_retry(monkeypatch):
    fake_generation(monkeypatch)
    assert len(agent.run_agent('tee size M under $30', get_example_wardrobe())['retry_history']) == 1


def test_exhausted_retries_do_not_change_description(monkeypatch):
    monkeypatch.setattr(agent, 'suggest_outfit', lambda *a: pytest.fail('no result'))
    result = agent.run_agent('designer ballgown size XXS under $5', get_example_wardrobe())
    assert len(result['retry_history']) == 3
    assert {x['constraints']['description'] for x in result['retry_history']} == {'designer ballgown'}
    assert result['selected_item'] is None and 'Broaden' in result['error']


def test_optional_failure_does_not_block(monkeypatch):
    fake_generation(monkeypatch)
    def broken(item):
        raise OSError('sensitive text')
    monkeypatch.setattr(agent, 'get_trends', broken)
    result = agent.run_agent('tee', get_example_wardrobe())
    assert result['error'] is None and any('unavailable' in s for s in result['warnings'])
    assert 'sensitive text' not in str(result)
