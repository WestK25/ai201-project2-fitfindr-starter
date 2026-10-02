"""Single-user local preference storage. No queries or credentials are persisted."""
import json
import os
from pathlib import Path
import re
from threading import RLock
from datetime import datetime, timezone
from tempfile import NamedTemporaryFile

_LOCK = RLock()
VOCABULARY = {'vintage', 'y2k', 'grunge', 'cottagecore', 'streetwear', 'minimal', 'classic',
              'athletic', 'baggy', 'oversized', 'fitted', 'wide-leg', 'earth tones',
              'chunky sneakers', 'denim', 'black', 'white', 'pink', 'blue', 'green', 'neutral'}


def state_directory():
    return Path(os.environ.get('FITFINDR_STATE_DIR', str(Path(__file__).parent / '.fitfindr')))


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as f:
            temporary = Path(f.name)
            json.dump(value, f, indent=2)
        temporary.replace(path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def _empty(warning=None):
    return {'likes': [], 'dislikes': [], 'updated_at': None, 'warning': warning}


def load_style_profile() -> dict:
    try:
        data = json.loads((state_directory() / 'style_profile.json').read_text())
        if not isinstance(data, dict):
            raise ValueError('profile object')
        for k in ('likes', 'dislikes'):
            if not isinstance(data.get(k), list) or any(not isinstance(x, str) or x not in VOCABULARY for x in data[k]):
                raise ValueError('invalid preferences')
        if data.get('updated_at') is not None and not isinstance(data['updated_at'], str):
            raise ValueError('invalid timestamp')
        return {k: data.get(k) for k in ('likes', 'dislikes', 'updated_at')} | {'warning': None}
    except FileNotFoundError:
        return _empty()
    except (OSError, ValueError, TypeError):
        return _empty('Saved preferences could not be read. Use Reset style memory, then state your preferences again.')


def update_style_profile(query: str) -> dict:
    with _LOCK:
        profile = load_style_profile()
        likes, dislikes = set(profile['likes']), set(profile['dislikes'])
        clauses = re.finditer(r"\bI\s+(?:(?P<negative>avoid|dislike|hate|do not like|don't like)|(?P<positive>prefer|like|love|mostly wear|usually wear))\s+(?P<text>.*?)(?=[.!?;]|\bI\s+(?:prefer|like|love|avoid|dislike|hate|don't|do not)|$)", query, flags=re.I)
        changed = False
        for match in clauses:
            clause = match['text'].casefold()
            positive = not match['negative']
            # 'I prefer X, not Y' and 'but avoid Y' preserve the stated negation.
            chunks = re.split(r"\b(?:not|avoid|without)\b", clause, maxsplit=1)
            for index, chunk in enumerate(chunks):
                found = {v for v in VOCABULARY if re.search(r'(?<!\w)' + re.escape(v) + r'(?!\w)', chunk)}
                target, opposite = (likes, dislikes) if positive and index == 0 else (dislikes, likes)
                target.update(found)
                opposite.difference_update(found)
                changed = changed or bool(found)
        if not changed:
            return profile
        profile = {'likes': sorted(likes), 'dislikes': sorted(dislikes), 'updated_at': datetime.now(timezone.utc).isoformat(), 'warning': None}
        try:
            atomic_json(state_directory() / 'style_profile.json', {k: v for k, v in profile.items() if k != 'warning'})
        except OSError:
            profile['warning'] = 'Preferences apply to this interaction only; local storage could not be written.'
        return profile


def reset_style_profile() -> str:
    with _LOCK:
        try:
            (state_directory() / 'style_profile.json').unlink(missing_ok=True)
            return 'Style memory reset. Your next search starts without saved preferences.'
        except OSError:
            return 'Style memory could not be reset. Check write access to the local state directory.'
