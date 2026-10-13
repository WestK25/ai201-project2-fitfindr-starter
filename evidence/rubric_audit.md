# Rubric evidence audit

This is an evidence assessment, not an awarded grade. Final unit result: **91 passed, 0 failed**. Real standalone Groq calls, the full agent, all stretch scenarios and the actual Gradio happy-path event succeeded. **25/25 required targets supported; 7/7 stretch targets supported.** Only recording/uploading the demo and adding its URL remain.

The original AI201 Project 2 specification required `meta-llama/llama-4-scout-17b-16e-instruct`. Groq shut that model down for free/developer-tier usage on **July 17, 2026**, and [officially recommends `openai/gpt-oss-120b` as a replacement](https://console.groq.com/docs/deprecations). After reviewing the actual Scout `model_not_found` failure and Groq’s recommended replacement, I explicitly approved the migration. Both generation tools therefore use **`openai/gpt-oss-120b` through Groq** so the required Groq-based workflow remains functional. The original Scout planning commits and historical failure evidence are preserved; GPT-OSS was not the original plan. All three required function signatures are unchanged.

Legend: **Supported** means concrete source, tests and/or genuine live evidence cited below. The point grouping follows the course rubric I supplied; planning-loop logic spans two of that group's four points. Mock fixtures and historical migration failures are explicitly separate from the successful live evidence.

## Required: three tools — 4/4 supported

| Target | Status | Repository evidence |
|---|---|---|
| README lists all three named required functions | Supported | README Tool Inventory; tools.py; test_tools.py::test_required_interfaces |
| Inputs include exact parameter names/types | Supported | README fenced signatures; planning.md Tool 1/2/3; verify_repository.py compares inspect.signature with both docs |
| Returns describe actual contents | Supported | README required-tool table lists all 11 listing fields and controlled strings; test_real_search_schema_and_rank, test_caption_request_and_facts |
| All three tools called in one working interaction | Supported | live_demo.json::scenarios.happy has real search → suggest_outfit → create_fit_card success and generation_records; app_live.json validates all three via the real Gradio event |

## Required: multi-step — 2/2 supported

| Target | Status | Repository evidence |
|---|---|---|
| Natural-language request through all three tools to fit card | Supported | live_demo.json::scenarios.happy and app_live.json::happy_outputs contain the actual selected item, named wardrobe outfit and 3-sentence fit card produced by GPT-OSS |
| Walkthrough explains each tool and reason | Supported | README Multi-Step Workflow; planning.md Complete interaction walkthrough uses actual lst_002; live_demo.json::scenarios.happy; test_identity_and_exact_state_flow |

## Required: state — 3/3 supported

| Target | Status | Repository evidence |
|---|---|---|
| Search item automatically passes to styling | Supported | agent.py::run_agent assigns results[0]; test_identity_and_exact_state_flow asserts identity; live_demo.json::scenarios.happy selected_item and suggest_outfit item_id agree |
| Outfit automatically passes to caption | Supported | run_agent card state passes exact outfit_suggestion; test_identity_and_exact_state_flow asserts exact string identity; test_caption_request_and_facts checks serialized payload; live_demo.json::scenarios.happy.live_validation confirms exact_outfit_passed and caption_item_identity during real calls |
| README explains state, timing and use | Supported | README State Management table; planning.md State management and diagrams |

## Required: planning loop — 4/4 supported

| Target | Status | Repository evidence |
|---|---|---|
| Explain actual conditional state logic (two-point logic requirement) | Supported | README Planning Loop; agent.py parse/search/context/outfit/card/done/error state machine; tests for outfit and caption failure |
| Specifically describe zero-result behavior | Supported | README fallback paragraphs; retry_history in live_demo.json::scenarios.deliberate_failures.agent; test_exhausted_retries_do_not_change_description |
| Different nonstandard path; no unconditional tools | Supported | test_no_result_does_not_style and test_outfit_failure_stops_caption; actual impossible query trace contains three searches and no generation |

## Required: error handling — 3/3 supported

| Target | Status | Repository evidence |
|---|---|---|
| Specific failure for each required tool | Supported | README Error Handling; planning.md error table; test_tools.py invalid constraints, empty wardrobe, empty caption and SDK errors |
| Deliberately triggered real failure | Supported | required_live_checks.txt; live_demo.json::scenarios.deliberate_failures; actual Scout model failure is separately documented |
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
| At least two specific Codex uses | Supported | README AI Usage Transparency lists my required implementation, agent/stretch, and model-migration directions alongside Codex’s outputs and the checks I required |
| Verification/revision truthful | Supported | README records my review of the incomplete 23/25 + 5/7 report, approval of the GPT-OSS migration, and required revalidation before acceptance; Codex’s test execution and output inspection remain explicitly attributed |

## Stretch: price comparison — 2/2 supported

| Target | Status | Repository evidence |
|---|---|---|
| Actual comparable assessment and reasoning | Supported | tools.py::compare_price; live_stretch_sources.json: $18 vs median $21.50 from lst_006/lst_033; tests for thresholds, insufficient/unrelated peers and dataset errors |
| Method documented | Supported | README Stretch Features / Price comparison; same-family/category, optional brand/style/condition narrowing, minimum two peers, 15% thresholds |

## Stretch: persistent memory — 2/2 supported

| Target | Status | Repository evidence |
|---|---|---|
| Second interaction reuses preferences without re-entry | Supported | live_demo.json::scenarios.memory.persisted_and_reused is true; new_process_profile proves separate-process persistence; test_memory_two_interactions captures metadata supplied to styling; both real interactions completed with error=null and live_validation.all_passed=true |
| Storage approach documented | Supported | README Style profile memory; memory.py atomic file/reset; gitignored .fitfindr; corrupted-state/negation/reset/write-failure tests |

## Stretch: trend awareness — 2/2 supported

| Target | Status | Repository evidence |
|---|---|---|
| Real trend source/data | Supported | live_stretch_sources.json includes real source, publication/retrieval dates, four parsed terms and HTML SHA-256; trends.py and mocked source/cache tests |
| Trend visibly influences actual outfit | Supported | live_demo.json::scenarios.happy.generation_records records the real Neo Nostalgia term sent to Groq and returned styling/application; live_validation proves it is visible in the outfit with attribution. app_live.json confirms the real UI displays it |
| README source documented | Supported | README Trend awareness links official annual source, discloses monthly HTTP 403, freshness windows and unavailable fallback |

## Stretch: retry — 1/1 supported

| Target | Status | Repository evidence |
|---|---|---|
| Zero-result search automatically retries | Supported | live_demo.json::scenarios.retry.retry_history has three real dataset attempts with counts 0/0/nonzero; live_demo.json::scenarios.retry completes real outfit/caption generation and passes all checks; unit tests also verify the branch |
| User sees changes | Supported | app.py::_format_session includes warning; actual session warning identifies size/max_price; test_fallback_warning_visible |

## Remaining submission work

No rubric target lacks repository evidence. The Scout retirement is resolved through the explicitly approved, documented GPT-OSS migration; original planning history is preserved. The evidence assessment does not claim a submitted video or an instructor-awarded score.

I still need to record/upload the 3–5 minute demo, add its actual URL to the README Demo section, and commit/push that README change.
