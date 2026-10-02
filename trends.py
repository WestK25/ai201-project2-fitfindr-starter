"""Verified Depop annual report retrieval, bounded cache, and item relevance."""
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from html.parser import HTMLParser
import json
import re

import httpx
from memory import state_directory, atomic_json

SOURCE_URL = 'https://news.depop.com/company-news/depop-unveils-2026-fashion-trends-report-the-edited-self/'
SOURCE = 'Depop newsroom · 2026 annual trends report'
PUBLISHED_AT = '2025-12-20'
REPORT_YEAR = 2026
TERMS = ('Modern Uniforms', 'Neo Nostalgia', 'Everyday Ceremony', 'Romanticized Sports')
KEYWORDS = {'neutral', 'tailoring', 'knits', 'button', 'workwear', 'jackets', 'peacoats', 'shirts',
            'nostalgia', 'nostalgic', '70s', '90s', '2000s', 'y2k', 'vintage', 'layering', 'bandage',
            'dresses', 'jorts', 'medieval', 'coats', 'skirts', 'metallic', 'accessories', 'blazers',
            'heels', 'jewelry', 'sportswear', 'tennis', 'jerseys', 'shorts', 'ski', 'silk', 'ballet', 'athletic'}


def _now():
    return datetime.now(timezone.utc)


class _Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.parts = []
        self.paragraphs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.active, self.parts = True, []

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'p' and self.active:
            self.paragraphs.append(' '.join(''.join(self.parts).split()))
            self.active = False


def _parse(html):
    parser = _Paragraphs()
    parser.feed(html)
    found = []
    for i, paragraph in enumerate(parser.paragraphs[:-1]):
        name = paragraph.split(':')[0].strip()
        if name in TERMS and len(parser.paragraphs[i + 1]) > 60:
            words = set(re.findall(r'[a-z0-9]+', parser.paragraphs[i + 1].casefold()))
            found.append({'term': name, 'keywords': sorted(words & KEYWORDS)})
    if len(found) < 2:
        raise ValueError('Source structure changed')
    return found


def _valid_cache(data):
    if not isinstance(data, dict) or data.get('source_url') != SOURCE_URL or data.get('published_at') != PUBLISHED_AT:
        return False
    if not re.fullmatch(r'[0-9a-f]{64}', str(data.get('content_sha256', ''))):
        return False
    terms = data.get('terms')
    return (isinstance(terms, list) and 2 <= len(terms) <= 4 and all(
        isinstance(t, dict) and t.get('term') in TERMS and isinstance(t.get('keywords'), list)
        and all(isinstance(k, str) and k in KEYWORDS for k in t['keywords']) for t in terms))


def _read_cache():
    try:
        data = json.loads((state_directory() / 'trends.json').read_text())
        age = _now() - datetime.fromisoformat(data['retrieved_at'])
        if _valid_cache(data) and timedelta(0) <= age <= timedelta(days=30):
            return data, age
    except (OSError, ValueError, TypeError, KeyError):
        pass
    return None, None


def _with_relevance(data, item, status, warning=None):
    text = ' '.join([str(item.get('title', '')), str(item.get('description', '')), ' '.join(item.get('style_tags', []))])
    words = set(re.findall(r'[a-z0-9]+', text.casefold()))
    ranked = sorted(data['terms'], key=lambda t: len(words & set(t['keywords'])), reverse=True)
    relevant = ranked[0] if ranked and words & set(ranked[0]['keywords']) else None
    return {**data, 'status': status, 'warning': warning, 'relevant_trend': relevant}


def get_trends(item: dict) -> dict:
    """Return sourced live/cached annual trends, or an informative unavailable state."""
    unavailable = {'status': 'unavailable', 'source': SOURCE, 'source_url': SOURCE_URL,
                   'published_at': PUBLISHED_AT, 'retrieved_at': None, 'terms': [],
                   'relevant_trend': None, 'warning': 'Trend source unavailable. Styling will continue without trend context.', 'content_sha256': None}
    if _now().year != REPORT_YEAR:
        return {**unavailable, 'warning': 'The configured annual trend report is outside its coverage year. Update the verified source.'}
    cache, age = _read_cache()
    if cache and age < timedelta(hours=24):
        return _with_relevance(cache, item, 'cached', 'Verified snapshot retrieved within 24 hours; annual report, not daily trends.')
    try:
        response = httpx.get(SOURCE_URL, timeout=6.0, follow_redirects=True,
                             headers={'User-Agent': 'FitFindr/1.0 (educational fashion trends reader)'})
        response.raise_for_status()
        data = {'source': SOURCE, 'source_url': SOURCE_URL, 'published_at': PUBLISHED_AT,
                'retrieved_at': _now().isoformat(), 'terms': _parse(response.text),
                'content_sha256': sha256(response.content).hexdigest()}
        warning = None
        try:
            atomic_json(state_directory() / 'trends.json', data)
        except OSError:
            warning = 'Live report verified, but the local trend cache could not be saved.'
        return _with_relevance(data, item, 'live', warning)
    except (httpx.HTTPError, ValueError, TypeError, KeyError):
        if cache:
            return _with_relevance(cache, item, 'cached', 'Live refresh failed; using a previously verified snapshot no more than 30 days old.')
        return unavailable
