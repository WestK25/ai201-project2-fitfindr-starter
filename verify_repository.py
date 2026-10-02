"""Read-only repository hygiene audit; outputs counts/status, never secret matches."""
import inspect
import json
import re
import subprocess
from pathlib import Path
from dotenv import dotenv_values
import tools

ROOT = Path(__file__).parent


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    files = sorted(set(git('ls-files', '-c', '--others', '--exclude-standard', '-z').decode().split('\0')) - {''})
    tracked = set(git('ls-files', '-z').decode().split('\0'))
    patterns = re.compile(rb'(?:gsk_[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})')
    key = dotenv_values(ROOT / '.env').get('GROQ_API_KEY', '')
    key_bytes = key.encode() if key and key != 'your_key_here' else None
    def contains_secret(data):
        return bool(patterns.search(data) or (key_bytes and key_bytes in data))
    worktree_matches = sum(contains_secret((ROOT / f).read_bytes()) for f in files if (ROOT / f).is_file())
    objects = set(line.split()[0] for line in git('rev-list', '--objects', '--all').decode().splitlines())
    blobs = [o for o in objects if git('cat-file', '-t', o).strip() == b'blob']
    history_matches = sum(contains_secret(git('cat-file', 'blob', o)) for o in blobs)
    forbidden = [f for f in tracked if f == '.env' or any(part in f.split('/') for part in ('.venv', '.fitfindr', '__pycache__', '.pytest_cache'))]
    ignored = {}
    for path in ('.env', '.venv', '.fitfindr/style_profile.json', '.fitfindr/trends.json'):
        ignored[path] = subprocess.run(['git', 'check-ignore', '-q', path], cwd=ROOT).returncode == 0
    signatures = {}
    for function in (tools.search_listings, tools.suggest_outfit, tools.create_fit_card):
        signature = function.__name__ + str(inspect.signature(function))
        signatures[signature] = all(signature in (ROOT / document).read_text() for document in ('README.md', 'planning.md'))
    plan_gates = {}
    for subject in ('Complete FitFindr required-feature plan', 'Plan FitFindr stretch features'):
        commit = git('log', '--format=%H', '--fixed-strings', '--grep=' + subject).decode().splitlines()[0]
        changed = git('diff-tree', '--no-commit-id', '--name-only', '-r', commit).decode().splitlines()
        plan_gates[subject] = changed == ['planning.md']
    starter_data_unchanged = not bool(git('diff', 'upstream/main', '--', 'data', 'utils/data_loader.py'))
    implementation_placeholders = sum(bool(re.search(r'TODO|NotImplementedError|not yet implemented', (ROOT / f).read_text())) for f in files if f.endswith('.py'))
    # Ignore this auditor's own literal detector expression, which is not a stub.
    implementation_placeholders -= 1
    result = {'worktree_files_scanned': len(files), 'history_blobs_scanned': len(blobs),
              'secret_matches_worktree': worktree_matches, 'secret_matches_history': history_matches,
              'forbidden_tracked_files': forbidden, 'ignored_runtime_paths': ignored,
              'documented_required_signatures_match': signatures, 'planning_commits_only_change_plan': plan_gates,
              'starter_data_and_loader_unchanged': starter_data_unchanged,
              'implementation_placeholder_count': implementation_placeholders}
    print(json.dumps(result, indent=2))
    assert worktree_matches == history_matches == 0 and not forbidden
    assert all(ignored.values()) and all(signatures.values()) and all(plan_gates.values())
    assert starter_data_unchanged and implementation_placeholders == 0


if __name__ == '__main__':
    main()
