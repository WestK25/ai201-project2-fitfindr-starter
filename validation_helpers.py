"""Evidence checks shared by CLI and real Gradio verification; no mock responses."""
import re


def check_outputs(item, wardrobe, outfit, caption):
    names = {piece['name'] for piece in wardrobe.get('items', [])}
    used = []
    for paragraph in (outfit or '').split('\n\n'):
        if paragraph.startswith('Outfit ') and ' + ' in paragraph:
            header = paragraph.split('. ', 1)[0]
            used.extend(header.split(' + ', 1)[1].split('; '))
    count = len(re.findall(r'[.!?](?=\s|$)', caption or ''))
    checks = {
        'outfit_nonempty': bool(outfit and not outfit.startswith('Error:')),
        'selected_item_named': item['title'] in (outfit or ''),
        'owned_pieces_are_real': bool(used) and all(n in names for n in used) if names else 'not owned' in (outfit or ''),
        'caption_sentence_count_valid': 2 <= count <= 4,
        'caption_item_once': (caption or '').count(item['title']) == 1,
        'caption_price_once': (caption or '').count(f"${item['price']:g}") == 1,
        'caption_platform_once': (caption or '').casefold().count(item['platform'].casefold()) == 1,
    }
    return {'checks': checks, 'all_passed': all(checks.values()), 'caption_sentence_count': count,
            'wardrobe_names_used': list(dict.fromkeys(used))}


def run_observed_agent(query, wardrobe):
    """Observe real tool calls, preserving object identity and original SDK execution."""
    import agent
    import tools
    from copy import deepcopy
    originals = agent.suggest_outfit, agent.create_fit_card, tools._generate_json
    references, records = {}, []

    def observed_outfit(item, context):
        references['outfit_item'] = item
        return originals[0](item, context)

    def observed_card(outfit, item):
        references['card_outfit'], references['card_item'] = outfit, item
        return originals[1](outfit, item)

    def observed_generation(system, payload, temperature):
        # This delegates to the actual production Groq request, never a fixture.
        try:
            response = originals[2](system, payload, temperature)
        except Exception as exc:
            records.append({'kind': 'caption' if 'outfit' in payload else 'outfit',
                            'model': tools.MODEL, 'exception_class': type(exc).__name__,
                            'http_status': getattr(exc, 'status_code', None)})
            raise
        records.append({'kind': 'caption' if 'outfit' in payload else 'outfit',
                        'model': tools.MODEL, 'temperature': temperature,
                        'input': deepcopy(payload), 'response': deepcopy(response)})
        return response

    try:
        agent.suggest_outfit, agent.create_fit_card, tools._generate_json = observed_outfit, observed_card, observed_generation
        session = agent.run_agent(query, wardrobe)
    finally:
        agent.suggest_outfit, agent.create_fit_card, tools._generate_json = originals
    session['generation_records'] = records
    if not session['error']:
        item = session['selected_item']
        validation = check_outputs(item, wardrobe, session['outfit_suggestion'], session['fit_card'])
        validation['checks'].update({
            'search_item_identity': item is session['search_results'][0],
            'outfit_item_identity': references.get('outfit_item') is item,
            'caption_item_identity': references.get('card_item') is item,
            'exact_outfit_passed': references.get('card_outfit') is session['outfit_suggestion'],
        })
        trend = (session.get('trend_info') or {}).get('relevant_trend')
        if trend:
            outfit_record = next(r for r in records if r['kind'] == 'outfit')
            generated = outfit_record['response']
            validation['checks']['trend_in_real_request'] = outfit_record['input']['relevant_trend'] == trend
            validation['checks']['generated_trend_application_visible'] = (
                generated.get('trend_used') == trend['term']
                and bool(generated.get('trend_application'))
                and generated['trend_application'] in session['outfit_suggestion']
                and session['trend_info']['source_url'] in session['outfit_suggestion'])
        validation['all_passed'] = all(validation['checks'].values())
        session['live_validation'] = validation
    return session
