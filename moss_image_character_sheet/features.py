"""Separate visible appearance facts using the connected MOSS encoder."""
from copy import deepcopy
from .catalog import CONTRACT as C
from .compiler import composition_caption, render_prompt
from .state import strict_load, keys, text

FIELDS = ('subject', 'head', 'outfit', 'hands', 'feet', 'shared')
INSTRUCTION = '''Describe a design as compact English appearance facts for separate character-sheet views. Return exactly one JSON object with six string fields:
subject: core identity/name, species, overall material; no hair, clothes or pose.
head: identity/name plus face, hair, headwear and visible head material; no torso clothing or legs.
outfit: the unworn garments and wearable accessories, including specified footwear; no wearer, character name, anatomy, hair, skin or robot components.
hands: hand or paw material and any gloves or wrist accessories; no head or torso.
feet: feet or footwear appearance; no whole figure.
shared: supplied art style or rendering medium, otherwise empty.
Preserve explicit facts and colors. For an unmistakably named fictional character, established appearance may supply missing visual details; explicit input always takes precedence. Otherwise do not invent missing facts. Use empty strings for unspecified features. Write descriptions, not commands or view directions. Keep the headwear both in head and outfit when applicable. Keep footwear both in outfit and feet.
Input: '''

def needs_analysis(state):
    return any(v.startswith('clothing_') for v in state['views']) or sum(v.startswith('face_') for v in state['views']) >= 3

def parse_features(raw):
    text(raw, 12000, 'appearance_analysis')
    data = strict_load(raw)
    keys(data, FIELDS, 'appearance_analysis')
    return {k: text(data[k], 1500, 'appearance_analysis.'+k).strip() for k in FIELDS}

def apply_features(result, state, features):
    draft = deepcopy(result['layout_draft'])
    views = state['views']
    background = state['background'].replace('_', ' ')
    head_only = all(v.startswith('face_') for v in views)
    clothing_only = all(v.startswith('clothing_') for v in views)
    explicit_garments = {
        v for v in views if v.startswith('clothing_') and (
            any(state['part_prompts'].get(part) and v in C['part_visibility'][part] for part in C['part_order'])
            or state['appearance']['clothing_type'] != 'auto')
    }
    if head_only:
        numbers = ('zero','one','two','three','four','five','six')
        panels = result['layout_plan']['panels']
        columns, rows = len({p['bbox_px'][0] for p in panels}), len({p['bbox_px'][1] for p in panels})
        summary = f'{numbers[len(views)].capitalize()} close-up head portraits in {numbers[columns]} columns and {numbers[rows]} rows on {background}. '+features['head']
    elif clothing_only:
        sides = 'front and back' if len(views)==2 else 'front' if views[0]=='clothing_front' else 'back'
        summary = f'Clothing only, laid flat on {background}, {sides}. '+features['outfit'] if features['outfit'] or explicit_garments else f'A blank {background} sheet.'
    else:
        summary = f'A reference sheet on {background}. '+composition_caption(result['layout_plan'], concise=True)
    style = C['styles'][state['style']] or features['shared']
    draft['summary']['caption'] = ' '.join(s for s in (summary, style, state['part_prompts'].get('other','')) if s)
    for v, item in zip(views, draft['items']):
        if head_only:
            continue
        if v.startswith('face_'):
            detail = features['head']
        elif v.startswith('body_'):
            detail = state['character']['identity']
        elif v.startswith('clothing_'):
            if not features['outfit'] and v not in explicit_garments:
                item['caption'] = f'Blank {background} space.'
                continue
            detail = '' if clothing_only else features['outfit']
        elif v=='hands':
            detail = features['hands'] or 'Hands of '+features['subject']
        else:
            detail = features['feet'] or 'Feet of '+features['subject']
        item['caption'] = ' '.join(s for s in (detail, item['caption']) if s)
    prompt = render_prompt(draft,result['layout_plan'],result['resolved_format'])
    return dict(result,prompt=prompt,layout_draft=draft)
