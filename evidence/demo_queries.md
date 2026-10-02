# Recording guide (3–5 minutes)

First resolve any model limitation reported in validation.md; a failed generation is not a successful happy-path demo. Open Project 2, activate `.venv`, run `python app.py`, and open the printed localhost URL. Choose Example wardrobe. Use Reset style memory for a known starting point.

## 0:00–1:00 — Three-tool happy path

Paste:

```text
vintage graphic tee under $30, size M
```

Show the three panels. Point to the actual title/size/price, named closet pieces, and 2–4 sentence shareable caption. Explain that listings are mock starter inventory and the trend report is a real official source.

## 1:00–1:40 — State passing, comparison and trend

Expand the details accordion. Say: “The search result at index zero is stored as selected_item. That same dictionary is passed directly into suggest_outfit. Its returned string is stored as outfit_suggestion and passed directly into create_fit_card. I never retype intermediate values.” Show the repeated item ID and `outfit_source: session.outfit_suggestion`. The unit identity test proves object/string passing, which cannot be established by a screenshot alone.

Point to comparable IDs lst_006/lst_033, their $24/$19 prices and $21.50 median, and the $18 selected item. Show the published/retrieved dates and live/cached status of Depop's **annual** 2026 report. Read the trend application in the outfit itself.

## 1:40–2:10 — Deliberate failure

```text
designer ballgown size XXS under $5
```

Show actionable broadening advice, blank later panels, and only search calls in the trace. The agent tries applicable relaxations and stops because no matching garment exists.

## 2:10–2:40 — Retry recovery

```text
vintage graphic tee size XXS under $1
```

Show three attempts: original, size removed, then budget removed. Read the warning that the found candidate may not meet original size/budget. Description remains unchanged.

## 2:40–3:50 — Persistent style memory

Reset memory, then submit exactly these two interactions:

```text
vintage graphic tee under $30, size M. I prefer baggy streetwear and chunky sneakers.
```

```text
90s track jacket size M under $50
```

Show that the second query contains no preferences but `style_profile_used.likes` still contains baggy, streetwear and chunky sneakers. Point out how the outfit applies those preferences. The harness's `memory.new_process_profile` also verifies persistence across a new Python process. Use `python demo_scenarios.py --scenario memory` to reproduce that proof without modifying your actual saved profile.

## 3:50–4:30 — Plan, tests and transparency

Show the two planning commits before their respective implementations, the test output, and README AI Usage Transparency. Explain Codex's actual role and objective tests; do not claim personal edits/review you did not do. An optional Empty wardrobe query demonstrates general advice.

## Commands for focused terminal demonstrations

```bash
python demo_scenarios.py --scenario happy
python demo_scenarios.py --scenario failure
python demo_scenarios.py --scenario retry
python demo_scenarios.py --scenario price
python demo_scenarios.py --scenario trend
python demo_scenarios.py --scenario memory
python -m pytest tests/ -q
```

The harness runs real services and reports failures truthfully. It uses isolated temporary preferences, avoiding your personal state. After uploading the video, replace `Demo video: TODO — add after recording` in README.md with the actual link, then:

```bash
git add README.md
git commit -m "Add FitFindr demo video"
git push origin main
```
