"""Separate visible appearance facts using the connected MOSS encoder."""
from copy import deepcopy
from .catalog import CONTRACT as C, VIEWS
from .compiler import composition_caption
from .state import compact, strict_load, keys, text

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
    if head_only:
        numbers = ('zero','one','two','three','four','five','six')
        panels = result['layout_plan']['panels']
        columns, rows = len({p['bbox_px'][0] for p in panels}), len({p['bbox_px'][1] for p in panels})
        summary = f'{numbers[len(views)].capitalize()} close-up head portraits in {numbers[columns]} columns and {numbers[rows]} rows on {background}. '+features['head']
    elif clothing_only:
        sides = 'front and back' if len(views)==2 else 'front' if views[0]=='clothing_front' else 'back'
        summary = f'Clothing only, laid flat on {background}, {sides}. '+features['outfit'] if features['outfit'] else f'A blank {background} sheet.'
    elif views == VIEWS:
        summary = f'A reference sheet on {background}: six head portraits at left, three full-length views, two flat-laid outfits, hands above feet at right.'
    else:
        summary = f'A reference sheet on {background}. '+composition_caption(result['layout_plan'], concise=True)
    style = C['styles'][state['style']] or features['shared']
    draft['summary']['caption'] = ' '.join(s for s in (summary, style, state['part_prompts'].get('other','')) if s)
    for v, item in zip(views, draft['items']):
        if head_only or clothing_only:
            continue
        if v.startswith('face_'):
            detail = features['head']
        elif v.startswith('body_'):
            detail = state['character']['identity']
        elif v.startswith('clothing_'):
            if not features['outfit']:
                item['caption'] = f'Blank {background} space.'
                continue
            detail = features['outfit']
        elif v=='hands':
            detail = features['hands'] or 'Hands of '+features['subject']
        else:
            detail = features['feet'] or 'Feet of '+features['subject']
        item['caption'] = ' '.join(s for s in (detail, item['caption']) if s)
    w,h = draft['width'],draft['height']
    model = dict(summary=draft['summary'],items=[dict(label=i['label'],caption=i['caption'],bbox=[i['bbox'][1]-h//2,i['bbox'][0]-w//2,i['bbox'][3]-h//2,i['bbox'][2]-w//2]) for i in draft['items']],bbox_coord_space='abs_centralized',bbox_format='yxyx')
    prompt = compact(model) if result['resolved_format']=='layout_json' else '\n\n'.join([draft['summary']['caption']]+[i['caption'] for i in draft['items']])
    return dict(result,prompt=prompt,layout_draft=draft)
