# Rubric evidence audit

This is an evidence assessment, not a grade. Final unit result: **87 passed, 0 failed**. Full real Groq generation is blocked because the explicitly required Scout model is retired. No replacement has been authorized at this checkpoint. Counts are conservative: **23/25 required targets supported**, **5/7 stretch targets supported**. The code/tests support additional mocked flow, but those are not substituted for a successful live end-to-end demo or live trend-influenced outfit. The demo video is also pending.

Legend: **Supported** means concrete repository/test evidence; **Blocked** means a needed live result does not exist. The point grouping follows the user-supplied rubric. Planning-loop logic spans two of its four points; other rows in that group cover the remaining two. Trend's two points are held pending the complete feature's live generation proof.

## Required: three tools — 3/4 supported

| Target | Status | Repository evidence |
|---|---|---|
| README lists all three named required functions | Supported | README Tool Inventory; tools.py; test_tools.py::test_required_interfaces |
| Inputs include exact parameter names/types | Supported | README fenced signatures; planning.md Tool 1/2/3; verify_repository.py compares inspect.signature with both docs |
| Returns describe actual contents | Supported | README required-tool table lists all 11 listing fields and controlled strings; test_real_search_schema_and_rank, test_caption_request_and_facts |
| All three tools called in one working interaction | **Blocked for live proof** | run_agent wires all three; test_identity_and_exact_state_flow proves calls with mocks, but live_demo.json::happy stops at Scout failure and cannot call create_fit_card with a real outfit |

## Required: multi-step — 1/2 supported

| Target | Status | Repository evidence |
|---|---|---|
| Natural-language request through all three tools to fit card | **Blocked for live proof** | parse_query and state-flow tests pass; live_demo.json::happy has no successful live outfit/fit_card because model_not_found |
| Walkthrough explains each tool and reason | Supported | README Multi-Step Workflow; planning.md Complete interaction walkthrough uses actual lst_002; demo_queries.md |

## Required: state — 3/3 supported

| Target | Status | Repository evidence |
|---|---|---|
| Search item automatically passes to styling | Supported | agent.py::run_agent assigns results[0]; test_identity_and_exact_state_flow asserts identity; live_demo.json::happy selected_item and suggest_outfit item_id agree |
| Outfit automatically passes to caption | Supported | run_agent card state passes exact outfit_suggestion; test_identity_and_exact_state_flow asserts exact string identity; test_caption_request_and_facts checks serialized payload |
| README explains state, timing and use | Supported | README State Management table; planning.md State management and diagrams |

## Required: planning loop — 4/4 supported

| Target | Status | Repository evidence |
|---|---|---|
| Explain actual conditional state logic (two-point logic requirement) | Supported | README Planning Loop; agent.py parse/search/context/outfit/card/done/error state machine; tests for outfit and caption failure |
| Specifically describe zero-result behavior | Supported | README fallback paragraphs; retry_history in live_demo.json::deliberate_failures.agent; test_exhausted_retries_do_not_change_description |
| Different nonstandard path; no unconditional tools | Supported | test_no_result_does_not_style and test_outfit_failure_stops_caption; actual impossible query trace contains three searches and no generation |

## Required: error handling — 3/3 supported

| Target | Status | Repository evidence |
|---|---|---|
| Specific failure for each required tool | Supported | README Error Handling; planning.md error table; test_tools.py invalid constraints, empty wardrobe, empty caption and SDK errors |
| Deliberately triggered real failure | Supported | required_live_checks.txt; live_demo.json::deliberate_failures; actual Scout model failure is separately documented |
| Specific/actionable response | Supported | Empty caption requires valid outfit; impossible query advises broadening/removing filters; test_unavailable_model_error_is_actionable handles actual observed HTTP 404 class without leaking details |

## Required: planning.md — 4/4 supported

| Target | Status | Repository evidence |
|---|---|---|
| Three completely specified tools | Supported | planning.md Required tool inventory; commit e806702 before tools implementation |
| Specific loop and state | Supported | planning.md Planning loop and State management, plus stretch updates in 4e69b58 |
| Error table and full walkthrough | Supported | planning.md Error handling and Complete interaction walkthrough; listing JSON is from unchanged starter |
| Text architecture and specific AI Tool Plan | Supported | Two Mermaid diagrams and AI Tool Plan input/output/verification table |

## Required: README — 3/3 supported

| Target | Status | Repository evidence |
|---|---|---|
| Tool inventory, planning and state | Supported | README corresponding sections; signatures programmatically verified |
| Per-tool errors and tested concrete example | Supported | README Error Handling links actual required_live_checks.txt and final live_demo.json |
| Spec reflection | Supported | README Spec Reflection explains plan-driven identity checks and factual caption-opening refinement; verified model availability divergence is disclosed |

## Required: AI usage — 2/2 supported

| Target | Status | Repository evidence |
|---|---|---|
| At least two specific Codex uses | Supported | README AI Usage Transparency lists tool implementation, architecture/UI, and stretch/error verification inputs and outputs |
| Verification/revision truthful | Supported | 34 required-tool tests ran before agent wiring, then 57 required tests; final 87 tests; decimal size regression and actual retired-model diagnosis described; no fabricated student review |

## Stretch: price comparison — 2/2 supported

| Target | Status | Repository evidence |
|---|---|---|
| Actual comparable assessment and reasoning | Supported | tools.py::compare_price; live_stretch_sources.json: $18 vs median $21.50 from lst_006/lst_033; tests for thresholds, insufficient/unrelated peers and dataset errors |
| Method documented | Supported | README Stretch Features / Price comparison; same-family/category, optional brand/style/condition narrowing, minimum two peers, 15% thresholds |

## Stretch: persistent memory — 2/2 supported

| Target | Status | Repository evidence |
|---|---|---|
| Second interaction reuses preferences without re-entry | Supported | live_demo.json::memory.persisted_and_reused is true; new_process_profile proves separate-process persistence; test_memory_two_interactions captures metadata supplied to styling; actual generation remains blocked separately |
| Storage approach documented | Supported | README Style profile memory; memory.py atomic file/reset; gitignored .fitfindr; corrupted-state/negation/reset/write-failure tests |

## Stretch: trend awareness — 0/2 supported for complete feature

| Target | Status | Repository evidence |
|---|---|---|
| Real trend source/data | Supported component | live_stretch_sources.json includes real source, publication/retrieval dates, four parsed terms and HTML SHA-256; trends.py and mocked source/cache tests |
| Trend visibly influences actual outfit | **Blocked for live proof** | test_trends_and_profile_change_outfit_request proves prompt and displayed application with a mocked model, but no live outfit can be generated on the required retired Scout model |
| README source documented | Supported component | README Trend awareness links official annual source, discloses monthly HTTP 403, freshness windows and unavailable fallback |

## Stretch: retry — 1/1 supported

| Target | Status | Repository evidence |
|---|---|---|
| Zero-result search automatically retries | Supported | live_demo.json::retry.retry_history has three real dataset attempts with counts 0/0/nonzero; tests verify successful downstream continuation with mocked generation |
| User sees changes | Supported | app.py::_format_session includes warning; actual session warning identifies size/max_price; test_fallback_warning_visible |

## Remaining blockers and student task

1. Resolve the explicit Scout requirement: Groq retired it July 17, 2026. The user was asked whether to permit the available recommended replacement openai/gpt-oss-120b. No silent model substitution was made.
2. After approval, change and document the model, run real happy/empty/retry/memory/trend-generation scenarios, and update this evidence assessment. Until then the remaining two required and two stretch points are not claimed.
3. Record/upload the 3–5 minute demo and replace the README demo placeholder with its actual URL. There are no fake video links or unconfirmed student-review statements.
