import inspect
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from groq import APIConnectionError
import tools
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe, load_listings


@pytest.fixture
def item():
    return next(x for x in load_listings() if x["id"] == "lst_002")


@pytest.fixture
def groq_mock(monkeypatch):
    client = MagicMock()
    client.__enter__.return_value = client
    monkeypatch.setattr(tools, "_get_groq_client", lambda: client)
    def respond(value):
        client.chat.completions.create.return_value = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(value)))])
        return client
    return respond


def test_required_interfaces():
    assert str(inspect.signature(tools.search_listings)) == '(description: str, size: str | None = None, max_price: float | None = None) -> list[dict]'
    assert str(inspect.signature(tools.suggest_outfit)) == '(new_item: dict, wardrobe: dict) -> str'
    assert str(inspect.signature(tools.create_fit_card)) == '(outfit: str, new_item: dict) -> str'


def test_real_search_schema_and_rank():
    results = tools.search_listings("vintage graphic tee", "M", 30)
    assert isinstance(results, list) and results[0]["id"] == "lst_002"
    assert set(results[0]) == set(load_listings()[0])
    assert all(x["price"] <= 30 for x in results)


@pytest.mark.parametrize('query,size,price', [('designer ballgown', 'XXS', 5), ('quasar ceremonial spacesuit', None, None), ('', None, None)])
def test_no_results(query, size, price):
    assert tools.search_listings(query, size, price) == []


def test_case_and_whitespace():
    assert tools.search_listings('  VINTAGE   GRAPHIC\nTEE ', 'medium', 30) == tools.search_listings('vintage graphic tee', 'M', 30)


@pytest.mark.parametrize('requested,actual,expected', [('M', 'S/M', True), ('S', 'XS', False), ('L', 'XL (oversized)', False), ('8', 'US 8.5', False), ('8', 'US 8', True), ('M', 'One Size / Oversized', False), ('W30', 'W30 L30', True), ('US 8', 'UK 8', False)])
def test_exact_size_tokens(requested, actual, expected):
    assert tools._size_matches(requested, actual) == expected


def test_size_and_budget():
    results = tools.search_listings('vintage', 'M', 20)
    assert results and all(tools._size_matches('M', i['size']) and i['price'] <= 20 for i in results)


@pytest.mark.parametrize('price', [-1, float('nan'), float('inf'), '30', True])
def test_invalid_price(price):
    with pytest.raises(ValueError):
        tools.search_listings('tee', max_price=price)


def test_invalid_size():
    with pytest.raises(ValueError):
        tools.search_listings('tee', size='banana')


def test_relevance_and_garment_anchor(monkeypatch, item):
    low = dict(item, id='low', title='Plain Tee', description='A vintage tee', style_tags=['vintage'])
    wrong = dict(item, id='wrong', title='Vintage Graphic Hoodie')
    monkeypatch.setattr(tools, 'load_listings', lambda: [wrong, low, item])
    assert [x['id'] for x in tools.search_listings('vintage graphic tee')] == [item['id'], 'low']


def test_empty_wardrobe_general_advice(item, groq_mock):
    groq_mock({'looks': [{'wardrobe_ids': [], 'advice': 'Try relaxed jeans and simple sneakers for a casual silhouette.'}]})
    result = tools.suggest_outfit(item, get_empty_wardrobe())
    assert 'General styling' in result and 'not owned' in result and 'jeans' in result


def test_example_wardrobe_and_request(item, groq_mock):
    client = groq_mock({'looks': [{'wardrobe_ids': ['w_001', 'w_007'], 'advice': 'Half-tuck the tee for a relaxed silhouette.'}]})
    result = tools.suggest_outfit(item, get_example_wardrobe())
    assert 'Baggy straight-leg jeans, dark wash' in result and 'Chunky white sneakers' in result
    call = client.chat.completions.create.call_args.kwargs
    assert call['model'] == tools.MODEL and call['temperature'] == 0.5
    payload = json.loads(call['messages'][1]['content'])
    assert payload['new_item'] == item and len(payload['wardrobe']['items']) == 10


def test_invented_piece_rejected(item, groq_mock):
    groq_mock({'looks': [{'wardrobe_ids': ['imaginary'], 'advice': 'Wear this with a new designer bag.'}]})
    assert tools.suggest_outfit(item, get_example_wardrobe()).startswith('Error:')


@pytest.mark.parametrize('tool', ['outfit', 'card'])
def test_real_sdk_exception_sanitized(tool, item, groq_mock, monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY', 'unit-test-placeholder')
    client = groq_mock({})
    client.chat.completions.create.side_effect = APIConnectionError(message='sensitive detail must never appear', request=httpx.Request('POST', 'https://api.groq.com'))
    result = tools.suggest_outfit(item, get_example_wardrobe()) if tool == 'outfit' else tools.create_fit_card('Valid outfit.', item)
    assert result.startswith('Error:') and 'retry' in result and 'sensitive' not in result


@pytest.mark.parametrize('outfit', [None, '', ' \n ', 'Error: failed'])
def test_empty_caption_guard(item, outfit, monkeypatch):
    monkeypatch.setattr(tools, '_get_groq_client', lambda: pytest.fail('must not call Groq'))
    assert 'valid outfit suggestion is required' in tools.create_fit_card(outfit, item)


def test_caption_request_and_facts(item, groq_mock):
    client = groq_mock({'sentences': ['Baggy denim and chunky kicks keep the whole look easy.', 'A little throwback energy for today.']})
    result = tools.create_fit_card('Exact outfit input.', item)
    assert item['title'] in result and '$18' in result and result.count('depop') == 1
    assert len(result.split('. ')) == 3
    call = client.chat.completions.create.call_args.kwargs
    assert call['model'] == tools.MODEL and call['temperature'] == 0.85
    assert json.loads(call['messages'][1]['content']) == {'outfit': 'Exact outfit input.', 'new_item': item}


def test_malformed_generation(item, groq_mock):
    groq_mock({'sentences': []})
    assert tools.create_fit_card('Valid outfit.', item).startswith('Error:')


def test_missing_key(item, monkeypatch):
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    assert 'GROQ_API_KEY in the local .env' in tools.suggest_outfit(item, get_empty_wardrobe())
