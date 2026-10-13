# FitFindr

A stateful secondhand-fashion agent for CodePath AI201 Project 2. Describe a piece, get a ranked mock listing, style it with your wardrobe, and generate a shareable fit card. It also compares asking prices, remembers explicit style preferences, retrieves verified Depop trend context, and retries empty searches with visible filter changes.

Based on the [official CodePath starter](https://github.com/codepath/ai201-project2-fitfindr-starter). The 40 starter listings are mock inventory; the trend source is real. The original data files and utils/data_loader.py are preserved.

## Setup

Tested on macOS with Python 3.12.1. From a terminal:

```bash
git clone https://github.com/WestK25/ai201-project2-fitfindr-starter.git
cd ai201-project2-fitfindr-starter
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Python 3.12 is recommended. For an existing checkout, activate the existing environment; it does not need to be recreated for every launch. `requirements-lock.txt` records exact installed versions for reproducibility (`python -m pip install -r requirements-lock.txt`).

Create `.env` locally if it does not already exist, containing this placeholder replaced by your own key:

```dotenv
GROQ_API_KEY=your_key_here
```

The project reads its local `.env`, and Git ignores that file. I keep the key out of source code, documentation, test output, and Git history.

```bash
python app.py
```

Open the localhost URL printed by Gradio. Ctrl-C stops the app. It binds to 127.0.0.1, with no public share link. This is a single-user local app: saved preferences belong to the person using this computer.

### Model and approved migration

The original AI201 Project 2 specification required `meta-llama/llama-4-scout-17b-16e-instruct`. Groq shut that model down for free/developer-tier usage on **July 17, 2026**, and [officially recommends `openai/gpt-oss-120b` as a replacement](https://console.groq.com/docs/deprecations). After reviewing the actual Scout `model_not_found` failure and Groq’s recommended replacement, I explicitly approved the migration. Both generation tools therefore use **`openai/gpt-oss-120b` through Groq** so the required Groq-based workflow remains functional. The original Scout planning commits and historical failure evidence are preserved; GPT-OSS was not the original plan. All three required function signatures are unchanged.

No extra model setting is needed: tools.py defines the shared model constant used by both generation requests. Live standalone tools, the complete agent, all stretch scenarios and a real Gradio interaction have passed with the replacement; see [validation](evidence/validation.md). The app uses a 2,500-token cap, low reasoning effort, no returned reasoning, and strict JSON schemas. Wardrobe IDs are restricted to actual provided pieces; trend data is placed at the JSON root. Local content validation and controlled API errors remain in place.

## Tool Inventory

### Required tools — tools.py

```python
search_listings(description: str, size: str | None = None, max_price: float | None = None) -> list[dict]
suggest_outfit(new_item: dict, wardrobe: dict) -> str
create_fit_card(outfit: str, new_item: dict) -> str
```

| Tool | Named inputs and purpose | Exact return contents | Failure behavior |
|---|---|---|---|
| `search_listings` | `description: str`: shopping keywords; `size: str \| None = None`: optional complete label; `max_price: float \| None = None`: optional inclusive USD cap. Calls load_listings(). | `list[dict]`, sorted by relevance, then price/id. Each unchanged dict contains `id: str`, `title: str`, `description: str`, `category: str`, `style_tags: list[str]`, `size: str`, `condition: str`, `price: float`, `colors: list[str]`, `brand: str \| None`, `platform: str`. | Ordinary zero matches/blank description: `[]`. Invalid size/budget: `ValueError`. File/JSON problems propagate to a controlled agent error. |
| `suggest_outfit` | `new_item: dict`: selected search listing; `wardrobe: dict`: starter items list and optional controlled `_style_profile` / `_trend_info` metadata. Suggest 1–2 realistic combinations. | Non-empty `str` naming actual wardrobe pieces and styling advice. Empty wardrobe returns labeled general suggestions; available relevant trend adds an attributed application note. | Invalid listing/wardrobe, missing credentials, Groq failure, malformed response or invented wardrobe IDs: actionable `Error:` string. |
| `create_fit_card` | `outfit: str`: exact successful suggestion; `new_item: dict`: same selected listing. Make a casual OOTD caption. | `str` with 2–4 sentences: deterministic opening includes exact title, price and platform once, followed by 1–3 generated vibe sentences. | None/blank/whitespace/Error outfit returns a descriptive `Error:` string without a network call. Invalid item, unavailable Groq or invalid generated sentences also return `Error:`. |

Search case-folds and normalizes whitespace, weights title/tag overlaps, and anchors recognized garment types to titles so a vintage tee search does not return a vintage jacket. S/M supports S or M; numeric 8 matches US 8, never 8.5. Parenthetical fit notes are not sizes; One Size is never assumed to fit an arbitrary letter size. Sizes do not imply fit guarantees or cross-country conversion. Groq calls have a 25-second timeout and one SDK retry. Styling temperature is 0.5; captions use 0.85.

### Stretch tools and persistence helpers

```python
# tools.py
compare_price(item: dict) -> dict
# trends.py
get_trends(item: dict) -> dict
# memory.py
load_style_profile() -> dict
update_style_profile(query: str) -> dict
reset_style_profile() -> str
```

| Interface | Purpose and exact return |
|---|---|
| `compare_price(item: dict) -> dict` | Selected listing in; `assessment: str`, `item_price: float \| None`, `comparable_count: int`, `comparable_ids: list[str]`, `comparable_prices: list[float]`, `median_price: float \| None`, `strategy: str`, `reasoning: str` out. Invalid item/data gives unavailable; fewer than two peers gives insufficient data. |
| `get_trends(item: dict) -> dict` | Selected listing in; `status: str` (live/cached/unavailable), `source: str`, `source_url: str`, `published_at: str`, `retrieved_at: str \| None`, `terms: list[dict]` (each `term: str`, `keywords: list[str]`), `relevant_trend: dict \| None`, `warning: str \| None`, `content_sha256: str \| None` out. Network/cache/parse failure degrades gracefully. |
| `load_style_profile() -> dict` | No parameters; returns `likes: list[str]`, `dislikes: list[str]`, `updated_at: str \| None`, `warning: str \| None`. Missing file is empty; corrupt file returns empty plus reset advice. |
| `update_style_profile(query: str) -> dict` | Original natural-language query in; merges explicit recognized preferences, saves atomically, returns the same profile structure. Write failure keeps preferences in the current session and reports that persistence failed. |
| `reset_style_profile() -> str` | No parameters; removes only the profile file and returns an actionable success/failure string. |

No extra required arguments were added to the starter tools. `run_agent(query: str, wardrobe: dict) -> dict`, `_new_session(query: str, wardrobe: dict) -> dict`, and `handle_query(user_query: str, wardrobe_choice: str) -> tuple[str, str, str]` retain their interfaces. A separate four-output UI wrapper adds the details accordion without changing the compatibility handler.

## Multi-Step Workflow

For `vintage graphic tee under $30, size M`:

1. Deterministically parse description `vintage graphic tee`, size `M`, budget `30.0`. No LLM call is needed to parse these constraints.
2. Call `search_listings('vintage graphic tee', size='M', max_price=30.0)` to locate a relevant candidate. The actual starter top match is `lst_002`, **Y2K Baby Tee — Butterfly Print**, $18, S/M, excellent condition, depop. Its description warns that the tagged medium fits like a small.
3. Store `search_results`, then `selected_item = search_results[0]`. Compare prices and retrieve optional trend context; load saved preferences into a copied wardrobe.
4. Call `suggest_outfit(session['selected_item'], session['wardrobe'])` to style that precise item with available named pieces, such as the actual example wardrobe's baggy straight-leg jeans and chunky white sneakers. Store the returned string in `outfit_suggestion` only on success.
5. Call `create_fit_card(session['outfit_suggestion'], session['selected_item'])` to create the caption. Store its successful string in `fit_card`.
6. Display the listing, outfit and fit card in the three primary panels. Expand the details accordion to inspect constraints, retry history, memory, source dates, comparable IDs and the tool trace.

The examples above describe the specified flow, not an invented live caption. [demo_scenarios.py](demo_scenarios.py) records actual results; [unit state-flow tests](tests/test_agent.py) verify the exact object/string arguments.

## Planning Loop

The `stage` field drives a bounded state machine: **parse → search → context → outfit → card → done**. Each result decides whether the next tool is allowed to run.

- **Search success:** select index zero and enrich context before styling.
- **Zero results:** retry the same description without the requested size. If still empty, remove the budget too. Skip identical attempts when a filter was already absent. Maximum three searches.
- **Fallback success:** continue and visibly warn which original filters were removed; the displayed candidate may exceed the original budget or size.
- **Fallback failure:** set an actionable error and stop. Neither generation tool receives empty input.
- **Invalid query/data:** correct the query or restore data/listings.json; do not mistake a data failure for an empty result.
- **Outfit failure:** stop before caption generation; an `Error:` string is never treated as an outfit.
- **Caption failure:** retain successful earlier state for diagnosis, set a caption-specific error, and leave later UI panels blank.
- **Optional tool failure:** retain an unavailable status/warning and continue the required workflow without fabricated prices, preferences, or trends.

## State Management

| Field | Written when / consumed by |
|---|---|
| `query` | Original input at session creation; parser and preference extraction read it. |
| `parsed` | Successful parse; original description, size and budget. Retries copy these constraints rather than overwriting them. |
| `search_results` | After each search attempt; selection reads the successful list. |
| `selected_item` | Direct reference to `search_results[0]`; both outfit and caption tools receive this same object. |
| `wardrobe` | Deep copy on session creation, enriched with `_style_profile` and `_trend_info`; consumed by styling. |
| `outfit_suggestion` | Exact successful styling return; passed directly into the caption tool. |
| `fit_card` | Successful caption return; consumed by UI/CLI. |
| `error`, `stage` | Each decision; stop required processing on terminal error. |
| `tool_trace` | Each call/result/transition; contains public IDs, counts and input-source references, never credentials. |
| `retry_history` | Each search records original/current constraints, changed fields, reason and count. |
| `price_assessment` | After selection; read by the listing panel/details. |
| `trend_info` | After selection; read by wardrobe context and the details panel. |
| `style_profile_used` | After parse; read by wardrobe context and the details panel. |
| `warnings` | Nonterminal fallback/storage/source issues; shown in listing/details. |

**Automatic data flow:** `search_results[0] → selected_item → suggest_outfit`, then `returned string → outfit_suggestion → create_fit_card`. The user never re-enters intermediate data. See `test_identity_and_exact_state_flow`, which asserts item identity and exact string passing. The [text architecture diagrams](planning.md#architecture) show these relationships.

## Error Handling

| Tool | Specific failure | Behavior / useful next step |
|---|---|---|
| `search_listings` | Zero matches | Returns []; agent relaxes size then budget and, if still empty, recommends broadening description, removing size or increasing budget. No styling call follows terminal failure. |
| `search_listings` | Malformed constraints / missing or invalid dataset | Correct the size/budget or restore data/listings.json; no downstream generation. |
| `suggest_outfit` | Empty or minimal wardrobe | General advice is labeled as unowned suggestions; populated wardrobes use validated IDs and actual names. Missing categories are not asserted as owned. |
| `suggest_outfit` | Missing key / real API failure / invalid generated content | Controlled actionable `Error:`; caption is skipped. No raw API error body or secret is displayed. |
| `create_fit_card` | Missing/blank/Error outfit | `Error: A valid outfit suggestion is required before creating a fit card.` No Groq call. |
| `create_fit_card` | Invalid listing / API failure / malformed caption | Specific controlled error; retry after fixing credentials, connectivity, quota or input. |

**Actually triggered:** `search_listings('designer ballgown', size='XXS', max_price=5)` returned `[]`; the full agent ultimately stops with broadening advice, and its trace contains only searches. `create_fit_card('', item)` returned the exact descriptive error above. The historical Scout request produced a controlled API failure before the approved migration; current GPT-OSS generation succeeds. Rate-limit errors now specifically advise waiting one minute and checking quota. [Recorded required checks](evidence/required_live_checks.txt) were refreshed after migration and show actual zero-result, empty-wardrobe and empty-caption behavior; the full harness records staged retries and successful generation. SDK connection exceptions are also deliberately tested with mocks; those mocked cases are not labeled as live network failures.

## Stretch Features

### Price comparison

Exclude the selected listing. Match category **and garment family**, then prefer at least two same-brand peers, otherwise shared style tags, otherwise broaden only within the same garment family/category. Use same-condition peers if at least two remain; otherwise disclose varying condition. Fewer than two peers means insufficient data, never an invented deal judgment. Prices below 85% of the peer median are a good deal; above 115% are above comparable range; the inclusive middle band is fair.

Real dataset example: lst_002 costs $18; same-family peers lst_006 and lst_033 cost $24 and $19, median $21.50. It is a good deal by that rule. These are **mock asking prices**, not sale transactions or a live market valuation. The UI shows the assessment and reasoning.

### Style profile memory

Recognize explicit clauses such as “I prefer baggy streetwear and chunky sneakers” or “I avoid pink”; do not persist every search as a preference. Store only a bounded vocabulary in `.fitfindr/style_profile.json`, never full queries or API keys. The next interaction loads it automatically, including after a new Python process starts. New opposing preferences replace old ones. Writes use atomic replacement and an in-process lock. Multi-process simultaneous updates are not transactional; this app is intended for one local user.

The reset button calls `reset_style_profile()`. Missing/corrupt files do not crash. Tests use temporary directories via `FITFINDR_STATE_DIR` and cannot modify real preferences. [Memory tests](tests/test_stretch.py) verify interaction reuse, new-process persistence, negations, corrupt files and reset.

### Trend awareness

Source: [Depop's official 2026 annual trends report](https://news.depop.com/company-news/depop-unveils-2026-fashion-trends-report-the-edited-self/), published **December 20, 2025**, describing **2026**. Direct retrieval was verified with HTTP 200. The more recent August blog returned HTTP 403 to the app, so the implementation uses the accessible official annual source. It does not mislabel this as today's social activity or manufacture popularity counts.

The parser accepts verified report headings and keywords actually present in their following paragraphs. Item overlap determines whether any trend applies. Source URL, publication date, UTC retrieval timestamp and HTML SHA-256 accompany the result. The cache is written only after successful retrieval, reused for 24 hours, then refreshed with a 6-second timeout. Failed refresh can use a verified snapshot up to 30 days old, visibly labeled cached. Otherwise trends become unavailable. After the report's coverage year, the source is disabled pending a verified update.

`wardrobe['_trend_info']` passes relevant context into the unchanged two-argument outfit tool. Generated output must identify the exact trend and explain how the actual pieces express it; the suggestion displays that application with attribution. A disconnected badge alone is insufficient. Live source evidence is [saved here](evidence/live_stretch_sources.json); mocked tests separately prove prompt inclusion and visible styling influence. Real GPT-OSS generations now demonstrate this influence: [live_demo.json](evidence/live_demo.json) contains the actual trend sent to Groq, its returned `trend_used`/`trend_application`, the visibly attributed outfit, and passing checks. [app_live.json](evidence/app_live.json) proves the same behavior through the real Gradio event.

### Retry with fallback

For `vintage graphic tee size XXS under $1`, the first search is empty, the second removes size but keeps $1, and the third removes the budget too. Every attempt keeps `vintage graphic tee`. The final candidate is shown with a warning to check its size/price. For `designer ballgown size XXS under $5`, all attempts remain empty and the agent stops. Tests prove recovery, no unnecessary retries, unchanged description, visible adjustments and no downstream calls after terminal failure.

## Spec Reflection

**How planning helped:** Planning the state table and error branches helped me make the data-flow requirements directly testable. I required isolated tool tests before agent integration; Codex ran 34 passing tool tests at that checkpoint. The later identity test checked that both tools received the actual search object and that the caption received the exact outfit string. I also required a separate stretch plan, which allowed profile/trend enrichment without changing the required tool signatures.

**Real implementation divergence:** The original course specification required Scout. During validation, the real request failed because Groq had retired that model for developer-tier use. After reviewing the failure and [Groq’s recommended replacement](https://console.groq.com/docs/deprecations), I approved migrating both generation tools to GPT-OSS while preserving their required interfaces. I required a complete end-to-end revalidation before accepting the implementation. The original Scout plan and its actual failure evidence remain preserved.

Live migration testing exposed two response-format differences: one response exhausted the former 1,000-token cap, and another put the new listing ID among owned wardrobe IDs. Codex increased the cap to 2,500 with low reasoning effort, required strict schemas with an enum of real wardrobe IDs, specified root-level trend fields, and rejected truncated output. [Actual diagnostic responses](evidence/migration_diagnostic.json) and [wardrobe-ID diagnostic](evidence/migration_wardrobe_diagnostic.json) preserve what failed before the fix. The final real responses pass the content and state checks. The caption's factual opening remains deterministic, followed by 1–3 generated vibe sentences, keeping the required total at 2–4 sentences.

## AI Usage Transparency

I supplied the official Project 2 assignment and grading rubric and directed the project toward every required target and all feasible stretch targets. I required the exact interfaces, planning before implementation, secrets kept out of Git, Project 1 preserved, and evidence for each rubric claim. Codex wrote substantial application and test code and ran the automated and live checks. My role was to set those requirements, review the completion reports, decide how to resolve the model blocker, and accept the implementation after revalidation.

1. **Required implementation:** I supplied the course tool specifications and required Codex to preserve the signatures, conditional workflow, and automatic state passing. Codex produced `tools.py`, `agent.py`, `app.py`, and tests for signatures, failure branches, and exact object/string flow. I required isolated tool tests before agent integration and a complete rubric check before acceptance. The recorded checkpoints were 34 tool tests and then 57 required-feature tests; Codex ran these checks.
2. **Agent and stretch implementation:** I directed Codex to implement the separately planned stretch features and required evidence for persistent memory across interactions/processes, real sourced trend information, price reasoning, and bounded retry behavior. Codex produced the comparison, memory, trend, and retry code, along with automated tests and the technical validation harness. I required real Groq workflows and a Gradio interaction in addition to mocked tests, so generated code alone was not enough for acceptance.
3. **Model migration and revision:** I reviewed the first completion report, which supported only 23/25 required and 5/7 stretch targets because the course-required Scout model had been retired. I did not accept that as the finished project. After reviewing the retirement issue and Groq’s recommended GPT-OSS replacement, I explicitly approved the migration. I then required Codex to rerun the full test suite, real Groq workflows, Gradio interaction, stretch validations, security audit, and rubric audit. Live testing exposed truncation and invalid wardrobe-ID responses; Codex adjusted the token budget and structured-output constraints, added regression coverage, and reran the checks. I accepted the implementation for final demo preparation only after the reported validation showed 91 passing tests and evidence supporting 25/25 required and 7/7 stretch targets.

My review and acceptance covered the completion reports and their evidence summaries against the rubric. Codex performed the implementation work, test execution, and individual-output inspection described here. The commit history preserves both planning gates, and mocked fixtures are clearly separate from actual live results.

## Testing

```bash
python -m pytest tests/
python agent.py
python demo_scenarios.py --scenario all --output evidence/live_demo.json
python verify_app.py --output evidence/app_live.json
```

Unit tests mock external services and isolate persistent state. Final result: **91 passed, 0 failed**. The scenario runner makes real Groq/source calls, checks deliberate failures and two-interaction/new-process memory, and exits nonzero if generation or output checks fail. It spaces requests by 15 seconds by default to respect the verified 8,000-token/minute account limit, so the full batch takes a few minutes. The application itself has no artificial delay; an API rate-limit response tells you when to retry.

The app verifier starts app.py, requests the real HTTP config, and invokes empty, happy and impossible queries through Gradio's actual event API. The happy query completed all three required tools with real Groq generation, and the server stopped cleanly. Live checks verify real wardrobe names, 2–4 caption sentences, title/price/platform, identical item references, exact outfit-string passing and visible sourced trend application. Codex also inspected the recorded outputs for outfit coherence and vibe. I reviewed the completion reports and required successful revalidation before accepting the implementation.

See [validation](evidence/validation.md), [test output](evidence/test_results.txt), [real agent outputs](evidence/live_demo.json), [real app outputs](evidence/app_live.json), and [every rubric target](evidence/rubric_audit.md): **25/25 required and 7/7 stretch evidence supported**. These are supported targets, not an awarded grade. No implementation blocker remains.

## Demo

Demo video: [Watch the Project 2 demo](https://drive.google.com/file/d/1cwBPY42pi_oHp3Z9VzE9VN5SOEnPCBUv/view?usp=drivesdk)

The 3–5 minute demo will show a complete three-tool workflow, state passing, adaptive/error behavior, and the implemented stretch features.
