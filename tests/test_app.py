import app
from utils.data_loader import load_listings


def test_empty_query():
    listing, outfit, card = app.handle_query('   ', 'Example wardrobe')
    assert 'Enter an item' in listing and outfit == card == ''


def test_session_error_blanks_later_panels(monkeypatch):
    monkeypatch.setattr(app, 'run_agent', lambda *a: {'error': 'No matches. Increase the budget.'})
    assert app.handle_query('tee', 'Example wardrobe') == ('No matches. Increase the budget.', '', '')


def test_happy_panels_and_wardrobe_choice(monkeypatch):
    def fake(query, wardrobe):
        assert wardrobe['items'] == []
        return {'error': None, 'selected_item': load_listings()[1], 'outfit_suggestion': 'General advice.', 'fit_card': 'Caption.'}
    monkeypatch.setattr(app, 'run_agent', fake)
    result = app.handle_query('tee', 'Empty wardrobe (new user)')
    assert len(result) == 3 and 'Y2K Baby Tee' in result[0] and '$18.00' in result[0]
    assert result[1:] == ('General advice.', 'Caption.')
