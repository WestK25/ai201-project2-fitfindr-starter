# Actual validation record

Validated October 2, 2026 (America/New_York). Python 3.12.1, Groq SDK 0.15.0, Gradio 6.29.0, pytest 9.1.1. Exact installed packages are in requirements-lock.txt.

## Passing objective checks

- **87 passed, 0 failed** in the final pytest run; unedited stdout: [test_results.txt](test_results.txt). Earlier staged results: 34 isolated required-tool tests before agent wiring, then [57 required tests](required_test_results.txt).
- Exact required tool signatures match both planning.md and README.md. [security_audit.json](security_audit.json) records the programmatic check.
- Happy-path argument identity and conditional control flow pass mocked unit tests. Mocked generations are not represented as actual Groq outputs.
- Real starter search selected lst_002 for the size-M, $30 tee query. Its actual comparable prices are $24/$19, median $21.50. [Live source/comparison output](live_stretch_sources.json).
- A real official Depop report fetch succeeded; source URL, publication date, retrieval timestamp and content digest were recorded. Monthly blog requests returned 403, so the official annual report is used with explicit scope.
- Persistent preference storage and reuse succeeded across two actual agent interactions and a new Python process, even though subsequent generation is blocked. See live_demo.json::memory.persisted_and_reused and memory.new_process_profile.
- Real deliberate failures: impossible tool search returned []; full impossible query performed three searches and stopped before generation; blank caption input returned a specific Error string. See live_demo.json::deliberate_failures.
- Real fallback search removed size then budget and found an item; final generation for that candidate remains blocked. Original description was unchanged and adjustments were recorded.
- **Actual app.py startup passed**: Gradio HTTP config returned 200, gradio_client invoked the UI's empty-query event and received four correctly mapped outputs (three primary + details). Server exited cleanly with code 0. [app_smoke.txt](app_smoke.txt) records the temporary local URL; that server is now stopped.
- Starter data and loader are unchanged. No implementation stubs remain. .env, .venv, profile and trend cache are ignored. Tracked/untracked deliverable files and Git history were scanned without printing matches; no secret matches were found.
- Project 1 has no added/missing/size-or-modification-time-changed files relative to the pre-setup baseline. [Preservation check](project1_preservation.json). Project 2 was created as a sibling.

## Real external blocker — no success fabricated

The required `meta-llama/llama-4-scout-17b-16e-instruct` request returned HTTP 404 with service code `model_not_found`; the authenticated model listing also omitted it. [Groq's official notice](https://console.groq.com/docs/deprecations) says the model was shut down July 17, 2026. The account lists `openai/gpt-oss-120b`, Groq's recommended replacement. Because the user explicitly required Scout, changing to that model was asked as an unavoidable external-blocker decision and remains pending.

Consequently **no genuine Groq end-to-end request succeeded**. The real scenario harness truthfully exited 1 and saved [live_demo.json](live_demo.json), with failed scenarios happy, empty_wardrobe, retry generation and memory generation. [agent_cli.txt](agent_cli.txt) is actual CLI output; the app shows controlled model-unavailable errors rather than a traceback. Trend prompt/application behavior is unit-tested with mocks; real trend-influenced styling is not claimed.

The audit conservatively supports **23/25 required and 5/7 stretch targets**, not an awarded grade. See [every target and its evidence](rubric_audit.md). Completing the model decision and subsequent real validation is required before claiming the only remaining task is recording/uploading the demo and adding its URL.

## Reproduction

```bash
source .venv/bin/activate
python -m pytest tests/ -q
python agent.py
python demo_scenarios.py --scenario all --output evidence/live_demo.json
python verify_app.py
python verify_repository.py
```

The scenario runner uses temporary synthetic preference data. It returns nonzero if a required live scenario fails. Tests isolate all persistence and mock services, so they do not consume Groq quota or overwrite user state.

## Commit chronology

1. e806702 — Complete FitFindr required-feature plan (planning.md only; tools/agent/app still starter stubs).
2. 8d0fa1a — Implement and test FitFindr required tools and workflow.
3. 4e69b58 — Plan FitFindr stretch features (planning.md only, before stretch code).
4. 359bbe4 — Add and verify FitFindr stretch features and demo harness.
5. Final documentation/audit commit follows; Git history is authoritative for its hash.

No demo URL has been fabricated. The only allowed submission placeholder is `Demo video: TODO — add after recording`; no AI-transparency statement claims student review that has not occurred.
