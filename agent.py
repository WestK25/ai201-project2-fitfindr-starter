"""Adaptive FitFindr state machine; tools consume previous results automatically."""
from copy import deepcopy
import json
import re

from tools import search_listings, suggest_outfit, create_fit_card, normalize_size, compare_price

from memory import update_style_profile
from trends import get_trends


def _new_session(query: str, wardrobe: dict) -> dict:
    return {
        "query": query, "parsed": {}, "search_results": [], "selected_item": None,
        "wardrobe": deepcopy(wardrobe), "outfit_suggestion": None, "fit_card": None,
        "error": None, "stage": "parse", "tool_trace": [],
        "retry_history": [], "price_assessment": None, "trend_info": None,
        "style_profile_used": {}, "warnings": [],
    }


def parse_query(query: str) -> dict:
    """Parse common explicit size and inclusive budget constraints without an LLM."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Enter an item, for example: vintage graphic tee under $30, size M.")
    text = " ".join(query.split())
    size = None
    size_pattern = r"\bsize\s+((?:US|UK|EU)\s+\d+(?:\.\d+)?|one\s+size|extra\s+(?:small|large)|W\d+(?:\s+L\d+)?|\d+(?:\.\d+)?|[^\s,;.!?]+)"
    natural_pattern = r"\b(?:in|wear|wearing|am|I'm)\s+(?:a\s+)?(extra small|extra large|small|medium|large|XXS|XS|XXL|XL|S|M|L)\b"
    match = re.search(size_pattern, text, flags=re.I) or re.search(natural_pattern, text, flags=re.I)
    if match:
        size = normalize_size(match.group(1))
        text = text[:match.start()] + " " + text[match.end():]
    elif re.search(r"\bsize\b", text, flags=re.I):
        raise ValueError("Supply a size after 'size', such as M, US 8 or W30.")
    price = None
    patterns = [
        r"\b(?:under|below|up to|at most|less than|budget(?: of)?|max(?:imum)?(?: of)?)\s*\$?\s*(-?\d+(?:\.\d+)?)\s*(?:dollars|usd)?",
        r"\$\s*(-?\d+(?:\.\d+)?)\s*(?:max(?:imum)?|or less|budget)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            price = float(match.group(1))
            if price < 0:
                raise ValueError("Use a nonnegative budget, such as under $30.")
            text = text[:match.start()] + " " + text[match.end():]
            break
    if re.search(r"\b(?:under|below|budget|maximum)\b|\$", text, flags=re.I):
        raise ValueError("Use a price such as under $30 or $30 max.")
    text = re.split(r"\bI\s+(?:(?:mostly|usually)\s+wear|prefer|like|love|wear|avoid|dislike)\b|\bwhat(?:'s| is) out there\b|\bhow (?:would|should|can)\b", text, maxsplit=1, flags=re.I)[0]
    text = re.sub(r"^(?:I'm |I am |I |)(?:looking for|searching for|want|need|find me|show me)\s+(?:a |an |some |)", "", text, flags=re.I)
    text = " ".join(re.sub(r"[,;.!?]", " ", text).split()).strip()
    if not text:
        raise ValueError("Include an item description, such as vintage graphic tee.")
    return {"description": text, "size": size, "max_price": price}


def _trace(session, tool, inputs, output, next_stage):
    session["tool_trace"].append({"tool": tool, "inputs": inputs, "output": output,
                                  "transition": f"{session['stage']} -> {next_stage}"})


def _fail(session, message):
    session["error"] = message
    session["stage"] = "error"
    return session


def run_agent(query: str, wardrobe: dict) -> dict:
    """Return complete session state, stopping immediately on a required-tool failure."""
    session = _new_session(query, wardrobe)
    while session["stage"] not in {"done", "error"}:
        if session["stage"] == "parse":
            try:
                session["parsed"] = parse_query(query)
            except ValueError as exc:
                return _fail(session, str(exc))
            profile = update_style_profile(query)
            session["style_profile_used"] = profile
            session["wardrobe"]["_style_profile"] = profile
            if profile.get("warning"):
                session["warnings"].append(profile["warning"])
            session["stage"] = "search"
        elif session["stage"] == "search":
            original = session["parsed"]
            attempts = [dict(original)]
            if original["size"] is not None:
                attempts.append({**original, "size": None})
            if original["max_price"] is not None:
                attempts.append({**original, "size": None, "max_price": None})
            results = []
            for number, constraints in enumerate(attempts, 1):
                try:
                    results = search_listings(**constraints)
                except ValueError:
                    return _fail(session, "Search constraints or listing data are invalid. Use size M/US 8 and a nonnegative budget; check data/listings.json.")
                except (OSError, TypeError, KeyError):
                    return _fail(session, "Search could not load the listings. Restore data/listings.json and retry.")
                changed = [k for k in ("size", "max_price") if constraints[k] != original[k]]
                session["retry_history"].append({"attempt": number, "original_constraints": dict(original),
                    "constraints": dict(constraints), "changed": changed,
                    "reason": "initial search" if number == 1 else "Previous search returned no results; loosen filters without changing the item description.",
                    "result_count": len(results)})
                session["search_results"] = results
                next_stage = "context" if results else "search" if number < len(attempts) else "error"
                _trace(session, "search_listings", dict(constraints), {"result_count": len(results)}, next_stage)
                if results:
                    if changed:
                        session["warnings"].append("Search fallback removed " + ", ".join(changed) + ". Check the listed size and price against your original request.")
                    break
            if not results:
                return _fail(session, "No matching listings after all applicable retries. Broaden the description, remove the size filter, or increase the budget and retry.")
            session["selected_item"] = results[0]
            session["stage"] = "context"
        elif session["stage"] == "context":
            for field, function in (("price_assessment", compare_price), ("trend_info", get_trends)):
                try:
                    value = function(session["selected_item"])
                except (OSError, ValueError, TypeError, KeyError):
                    value = {"status": "unavailable", "warning": f"{field} is unavailable; styling will continue."}
                session[field] = value
                if value.get("warning"):
                    session["warnings"].append(value["warning"])
                _trace(session, function.__name__, {"item_id": session["selected_item"]["id"]},
                       {"status": value.get("status", value.get("assessment"))}, "context")
            session["wardrobe"]["_trend_info"] = session["trend_info"]
            session["stage"] = "outfit"
        elif session["stage"] == "outfit":
            result = suggest_outfit(session["selected_item"], session["wardrobe"])
            failed = not isinstance(result, str) or not result.strip() or result.startswith("Error:")
            _trace(session, "suggest_outfit", {"item_id": session["selected_item"]["id"], "wardrobe_count": len(session["wardrobe"].get("items", []))}, {"success": not failed}, "error" if failed else "card")
            if failed:
                return _fail(session, result if isinstance(result, str) and result.strip() else "Error: Outfit styling returned no suggestion. Retry generation.")
            session["outfit_suggestion"] = result
            session["stage"] = "card"
        elif session["stage"] == "card":
            result = create_fit_card(session["outfit_suggestion"], session["selected_item"])
            failed = not isinstance(result, str) or not result.strip() or result.startswith("Error:")
            _trace(session, "create_fit_card", {"item_id": session["selected_item"]["id"], "outfit_source": "session.outfit_suggestion", "outfit_characters": len(session["outfit_suggestion"])}, {"success": not failed}, "error" if failed else "done")
            if failed:
                return _fail(session, result if isinstance(result, str) and result.strip() else "Error: Fit card generation returned no caption. Retry generation.")
            session["fit_card"] = result
            session["stage"] = "done"
    return session


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe
    for label, query in [("Happy path", "vintage graphic tee under $30, size M"),
                         ("Deliberate no-results", "designer ballgown size XXS under $5")]:
        session = run_agent(query, get_example_wardrobe())
        print(f"\n=== {label} ===")
        print(json.dumps(session, indent=2, ensure_ascii=False))
