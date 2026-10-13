# Actual validation record

Completed October 11, 2026 (America/New_York). The full paced scenario capture ran at `2026-10-02T17:37:11.387010+00:00`; the final real Gradio capture ran at `2026-10-11T15:11:06.058554+00:00`. Evidence files retain actual timestamps. Python 3.12.1, Groq SDK 0.15.0, Gradio 6.29.0 and pytest 9.1.1; exact installed versions are in requirements-lock.txt.

## Verified results

- **91 passed, 0 failed** in the full pytest suite. [Unedited stdout](test_results.txt). Earlier development milestones were 34 isolated tool tests before agent wiring and 57 required tests; those historical results are retained.
- **Real standalone tools passed:** live_demo.json::scenarios.standalone_tools contains a real example-wardrobe outfit and caption, with selected-item, actual-wardrobe-name, 2–4 sentence and item/price/platform checks.
- **Real Groq end-to-end passed:** [live_demo.json](live_demo.json) records happy, empty-wardrobe, retry, first-memory and second-memory runs, each with error=null and live_validation.all_passed=true. Its failed_scenarios is empty.
- **Actual state identity passed:** observing wrappers delegated to the real production tools and SDK; no model responses were mocked. They confirmed that the actual search result object reached both generation tools and the exact outfit string reached the caption tool. The original functions were restored after each observation.
- **Content inspected:** populated-wardrobe outputs named real provided pieces, and captions used 2–4 sentences with the correct item, price, platform and outfit vibe. Structured ID enums and local checks reject invalid pieces; Codex also inspected the observed narrative. My review covered the completion reports and reported validation results against the rubric.
- **All stretch features passed:** real same-family comparison, staged retry recovery, memory reuse across two interactions and a new Python process, and real sourced trend application. The second memory query omitted preferences but reused baggy/streetwear/chunky-sneakers preferences and produced a successful outfit.
- **Trend retrieval and influence passed:** [latest source metadata](live_stretch_sources.json) comes from the real app's source fetch. The full agent evidence stores the actual trend sent to Groq, its returned trend_used/trend_application, and the final attributed outfit. The source remains the official annual 2026 Depop report, published December 20, 2025; retrieval time is not presented as publication time. No trend terms or popularity counts were fabricated.
- **Full deliberate-failure checks passed:** impossible search returned []; the full agent exhausted applicable retries and called no downstream generation; blank caption input returned the expected descriptive Error string. See live_demo.json::scenarios.deliberate_failures and refreshed required_live_checks.txt. Rate-limit, absent-key, malformed-content and real SDK exception classes also have deterministic unit coverage.
- **Real Gradio end-to-end passed:** [app_live.json](app_live.json) records actual app.py launch, HTTP 200 config, empty/happy/impossible calls through Gradio's event API, genuine Groq generation, all output checks, visible trend application and clean server exit code 0. This was an actual server/event interaction, not a direct handler mock. The recorded temporary server has been stopped.
- **Signatures/security:** verify_repository.py compares required signatures with planning.md and README.md; checks planning-only commits; scans deliverable files and Git history without printing secrets; verifies .env/.venv/profile/cache exclusions and unchanged starter data/loader. See security_audit.json. No generated personal profile is tracked; example preference data in evidence is synthetic demo input. Project 1 was not edited during migration.

On October 11, cloud-offloaded environment files stalled imports. Restoring the local environment and dependency packages from the exact lockfile resolved the issue; the final test and real app checks above passed afterward.

## Submission cleanup verification — October 13, 2026

The documentation cleanup preserved the application, tests, datasets, and saved live responses. The local test suite passed again with **91 passed, 0 failed**; `test_results.txt` records this run. The refreshed `security_audit.json` records the pre-commit repository and Git-history scan with zero secret matches, matching required signatures, preserved planning gates, and ignored runtime files. The live evidence above remains from the October 11 validation; no external model calls were needed for this cleanup.

## Approved model divergence and resolved migration issues

The original AI201 Project 2 specification required `meta-llama/llama-4-scout-17b-16e-instruct`. Groq shut that model down for free/developer-tier usage on **July 17, 2026**, and [officially recommends `openai/gpt-oss-120b` as a replacement](https://console.groq.com/docs/deprecations). After reviewing the actual Scout `model_not_found` failure and Groq’s recommended replacement, I explicitly approved the migration. Both generation tools therefore use **`openai/gpt-oss-120b` through Groq** so the required Groq-based workflow remains functional. The original Scout planning commits and historical failure evidence are preserved; GPT-OSS was not the original plan. All three required function signatures are unchanged.

The migration required more than replacing the ID. [The real initial diagnostic](migration_diagnostic.json) showed finish_reason=length at 1,000 tokens and incorrect trend nesting. [The next diagnostic](migration_wardrobe_diagnostic.json) showed the model putting a listing ID in the owned-wardrobe list; the existing guard rejected it. The final request uses a 2,500-token budget, low reasoning effort, no returned reasoning, and strict JSON Schema with valid-ID enums, root trend fields and bounded arrays. Truncated output is rejected even if its JSON parses. Both production tools still retain their original signatures and temperatures.

Groq rate-limit headers verified an 8,000-token/minute account allowance during migration. The validation runner spaces calls by 15 seconds by default; the app returns actionable wait-and-retry guidance for HTTP 429. The final paced run succeeded. Historical Scout/pre-fix failure outputs are retained as historical evidence or Git history and do not describe the final application's status.

**25/25 required targets supported; 7/7 stretch targets supported.** This is an evidence assessment, not an awarded grade. The [line-by-line rubric audit](rubric_audit.md) cites source, tests and real results for every target. No implementation blocker remains. My remaining submission work is recording/uploading the 3–5 minute demo, adding its actual URL to README, and committing/pushing that link.

## Reproduce

```bash
source .venv/bin/activate
python -m pytest tests/ -q
python agent.py
python demo_scenarios.py --scenario all --output evidence/live_demo.json
python verify_app.py --output evidence/app_live.json
python verify_repository.py
```

Run live commands sequentially with normal pauses to respect Groq quota. The full scenario runner takes a few minutes and isolates synthetic preferences in a temporary directory. It returns nonzero on a generation or quality-check failure. Tests isolate storage and mock network services; live evidence does not.

## Commit chronology

1. e806702 — Complete FitFindr required-feature plan (planning.md only; starter code still untouched).
2. 8d0fa1a — Implement and test FitFindr required tools and workflow.
3. 4e69b58 — Plan FitFindr stretch features (planning.md only, before stretch code).
4. 359bbe4 — Add and verify FitFindr stretch features and demo harness.
5. 6ce520e — Document FitFindr validation, rubric evidence, and model blocker (historical pre-approval state).
6. Model migration/live-validation commit follows these existing commits; Git history supplies its exact hash. No planning history was rewritten.

I have left the demo-video URL pending in README until I record and upload the video. The saved test and live results document actual runs.
