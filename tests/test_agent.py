import pytest
import agent
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe, load_listings


@pytest.mark.parametrize('query,expected', [
    ("I'm looking for a vintage graphic tee under $30, size M. I mostly wear baggy jeans and chunky sneakers.", {'description': 'vintage graphic tee', 'size': 'M', 'max_price': 30.0}),
    ('tee $30 max', {'description': 'tee', 'size': None, 'max_price': 30.0}),
    ('tee in medium', {'description': 'tee', 'size': 'M', 'max_price': None}),
    ('boots size US 8', {'description': 'boots', 'size': 'US 8', 'max_price': None}),
    ('jeans size W30 L30 up to $40', {'description': 'jeans', 'size': 'W30 L30', 'max_price': 40.0}),
    ('tee', {'description': 'tee', 'size': None, 'max_price': None}),
    ('tee under 30 dollars', {'description': 'tee', 'size': None, 'max_price': 30.0}),
])
def test_parser(query, expected):
    assert agent.parse_query(query) == expected


@pytest.mark.parametrize('query', ['', ' ', 'tee size banana', 'tee under $-5', 'tee size', 'under $30', 'tee under infinity'])
def test_invalid_query_stops(query, monkeypatch):
    monkeypatch.setattr(agent, 'search_listings', lambda **k: pytest.fail('must stop'))
    assert agent.run_agent(query, get_example_wardrobe())['error']


def test_identity_and_exact_state_flow(monkeypatch):
    item = load_listings()[1]
    results = [item]
    outfit = 'A specific, exact outfit suggestion.'
    calls = []
    monkeypatch.setattr(agent, 'search_listings', lambda **kwargs: results)
    def suggest(new_item, wardrobe):
        assert new_item is item
        calls.append('outfit')
        return outfit
    def card(received, new_item):
        assert received is outfit and new_item is item
        calls.append('card')
        return 'Actual mocked caption.'
    monkeypatch.setattr(agent, 'suggest_outfit', suggest)
    monkeypatch.setattr(agent, 'create_fit_card', card)
    session = agent.run_agent('tee size M under $30', get_example_wardrobe())
    assert session['selected_item'] is session['search_results'][0] is item
    assert session['outfit_suggestion'] is outfit
    assert session['error'] is None and session['stage'] == 'done'
    assert calls == ['outfit', 'card']


def test_no_result_does_not_style(monkeypatch):
    monkeypatch.setattr(agent, 'suggest_outfit', lambda *a: pytest.fail('no item'))
    monkeypatch.setattr(agent, 'create_fit_card', lambda *a: pytest.fail('no outfit'))
    session = agent.run_agent('designer ballgown size XXS under $5', get_example_wardrobe())
    assert session['error'] and 'Broaden' in session['error']
    assert session['selected_item'] is None and session['fit_card'] is None


def test_outfit_failure_stops_caption(monkeypatch):
    monkeypatch.setattr(agent, 'suggest_outfit', lambda *a: 'Error: Outfit styling unavailable. Retry.')
    monkeypatch.setattr(agent, 'create_fit_card', lambda *a: pytest.fail('error is not outfit'))
    result = agent.run_agent('tee', get_example_wardrobe())
    assert result['error'].startswith('Error: Outfit') and result['fit_card'] is None


def test_card_failure_preserves_earlier_state(monkeypatch):
    monkeypatch.setattr(agent, 'suggest_outfit', lambda *a: 'Valid outfit.')
    monkeypatch.setattr(agent, 'create_fit_card', lambda *a: 'Error: Fit card failed. Retry.')
    result = agent.run_agent('tee', get_example_wardrobe())
    assert result['outfit_suggestion'] == 'Valid outfit.' and 'Fit card failed' in result['error']


def test_empty_wardrobe_passes_through(monkeypatch):
    def suggest(item, wardrobe):
        assert wardrobe['items'] == []
        return 'General advice, no owned pieces claimed.'
    monkeypatch.setattr(agent, 'suggest_outfit', suggest)
    monkeypatch.setattr(agent, 'create_fit_card', lambda *a: 'A caption.')
    assert agent.run_agent('tee', get_empty_wardrobe())['error'] is None


def test_missing_data_controlled(monkeypatch):
    def missing(**kwargs):
        raise FileNotFoundError('private path')
    monkeypatch.setattr(agent, 'search_listings', missing)
    result = agent.run_agent('tee', get_empty_wardrobe())
    assert 'Restore data/listings.json' in result['error'] and 'private path' not in result['error']


def test_decimal_shoe_size():
    assert agent.parse_query('boots size 8.5')['size'] == '8.5'
