import copy
import hashlib
import json
import unittest
import sys
import types
import re
from unittest.mock import patch
from pathlib import Path
from moss_image_character_sheet.catalog import DEFAULT, CONTRACT, ROOT, VIEWS
from moss_image_character_sheet.state import parse_state, compact, StateError
from moss_image_character_sheet.compiler import preview
from moss_image_character_sheet.layout import compute_layout
from moss_image_character_sheet.features import needs_analysis, parse_features, apply_features

class CompilerTests(unittest.TestCase):
    def test_empty_outfit_preserves_explicit_garment_details_and_shape(self):
        features=dict(subject='robot',head='metal head',outfit='',hands='',feet='',shared='')
        for views in (['body_front','clothing_front','clothing_back'],['clothing_front','clothing_back']):
            for shape in ('auto','pants','skirt_robe'):
                with self.subTest(views=views,shape=shape):
                    s=copy.deepcopy(DEFAULT);s['views']=views;s['character']['identity']='A robot.'
                    s['part_prompts']={'upper_clothing':'PURPLE_COAT','back_clothing':'GOLD_BACK','lower_body':'GREEN_PANTS'}
                    s['appearance']['clothing_type']=shape
                    before=preview(compact(s));after=apply_features(before,s,features)
                    by_id=dict(zip(views,after['layout_draft']['items']))
                    for view in ('clothing_front','clothing_back'):
                        self.assertEqual(by_id[view]['caption'],dict(zip(views,before['layout_draft']['items']))[view]['caption'])
                        self.assertIn('PURPLE_COAT',by_id[view]['caption'])
                        self.assertIn('GREEN_PANTS',by_id[view]['caption'])
                    self.assertNotIn('GOLD_BACK',by_id['clothing_front']['caption'])
                    self.assertIn('GOLD_BACK',by_id['clothing_back']['caption'])
                    self.assertNotIn('blank',after['layout_draft']['summary']['caption'].lower())

    def test_empty_outfit_blanks_only_unspecified_garment_views(self):
        features=dict(subject='robot',head='',outfit='',hands='',feet='',shared='')
        for views in (['body_front','clothing_front','clothing_back'],['clothing_front','clothing_back']):
            for parts,shape in (({},'auto'),({'back_clothing':'GOLD_BACK'},'auto'),({},'pants'),({},'skirt_robe')):
                with self.subTest(views=views,parts=parts,shape=shape):
                    s=copy.deepcopy(DEFAULT);s['views']=views;s['character']['identity']='A robot.'
                    s['part_prompts']=parts;s['appearance']['clothing_type']=shape
                    after=apply_features(preview(compact(s)),s,features)
                    by_id=dict(zip(views,after['layout_draft']['items']))
                    for view in ('clothing_front','clothing_back'):
                        specified=shape!='auto' or view=='clothing_back' and bool(parts)
                        self.assertEqual(by_id[view]['caption']=='Blank white space.',not specified)
                    if len(views)==2:
                        self.assertEqual('blank' in after['layout_draft']['summary']['caption'].lower(),not parts and shape=='auto')

    def test_scoped_all13_summary_follows_actual_rows(self):
        features=dict(subject='robot',head='metal head',outfit='purple coat',hands='',feet='',shared='')
        for size in (dict(mode='auto'),dict(mode='manual',manual_width=512,manual_height=2048),dict(mode='manual',manual_width=4096,manual_height=512),dict(mode='manual',manual_width=1024,manual_height=1024)):
            with self.subTest(size=size):
                s=copy.deepcopy(DEFAULT);s['views']=VIEWS[:];s['character']['identity']='A robot.';s['size'].update(size)
                before=preview(compact(s));after=apply_features(before,s,features)
                summary=after['layout_draft']['summary']['caption']
                self.assertNotIn('at left',summary);self.assertNotIn('at right',summary)
                self.assertIn('6 close-up headshots',summary)
                rows=before['layout_plan']['rows']
                if len(rows)>1:
                    for i in range(len(rows)):self.assertIn(f'Sheet row {i+1}, from left to right:',summary)
                else:self.assertIn('From left to right:',summary)
                if size.get('manual_width')==512:
                    self.assertEqual(rows,[['portrait'],['body'],['clothing'],['detail']])
                self.assertEqual([i['bbox'] for i in before['layout_draft']['items']],[i['bbox'] for i in after['layout_draft']['items']])

    def test_caption_keeps_each_panel_position_after_feature_analysis(self):
        features=dict(subject='robot',head='silver head',outfit='purple coat',hands='',feet='red boots',shared='')
        for views in (['face_front','face_left','face_right'],['face_front','face_left','face_right','feet'],VIEWS[:]):
            s=copy.deepcopy(DEFAULT);s['views']=views;s['character']['identity']='A robot.';s['prompt_format']='caption'
            s['size'].update(mode='manual',manual_width=512,manual_height=2048)
            before=preview(compact(s));after=apply_features(before,s,features)
            locations=lambda prompt:re.findall(r'The [^.]+ is in the [^.]+ region\.',prompt)
            self.assertEqual(len(locations(after['prompt'])),len(views))
            self.assertEqual(locations(after['prompt']),locations(before['prompt']))
            self.assertNotIn(' is in the ',after['layout_draft']['items'][0]['caption'])

    def test_external_prompt_limit_is_checked_before_analysis(self):
        with patch.dict(sys.modules,{'nodes':types.SimpleNamespace(MAX_RESOLUTION=16384)}):
            from moss_image_character_sheet.node import MOSSImageCharacterSheetDesigner as Node
        raw=compact(DEFAULT)
        for value in ('A'*2000,'😀'*1000):
            self.assertIs(Node.VALIDATE_INPUTS(raw,value),True)
            self.assertIn(value,Node().compile(raw,value)['result'][0])
        for value,code in (('A'*2001,'E_TEXT_LIMIT'),('😀'*1001,'E_TEXT_LIMIT'),('\ud800','E_UNICODE')):
            for views in (DEFAULT['views'],CONTRACT['presets']['clothing']):
                s=copy.deepcopy(DEFAULT);s['views']=views;raw=compact(s)
                self.assertTrue(Node.VALIDATE_INPUTS(raw,value).startswith(code+': prompt'))
                with patch('moss_image_character_sheet.node.encoder_link') as encoder:
                    with self.assertRaises(StateError) as raised:Node().compile(raw,value)
                    self.assertEqual((raised.exception.code,raised.exception.path),(code,'prompt'))
                    encoder.assert_not_called()

    def test_footwear_off_retains_described_socks_without_requesting_bare_feet(self):
        s=copy.deepcopy(DEFAULT);s['views']=['body_front','feet'];s['character']['identity']='A robot.'
        s['part_prompts']={'footwear':'RED_SOCKS'};s['appearance']['footwear_state']='unshod'
        for item in preview(compact(s))['layout_draft']['items']:
            self.assertIn('RED_SOCKS',item['caption'])
            self.assertIn('no shoes or boots',item['caption'])
            self.assertIn('retain described socks or tights',item['caption'])
            self.assertNotIn('feet are bare',item['caption'])

    def test_analysis_only_targets_troublesome_views(self):
        for preset in ('single','turnaround','five','basic','seven','head','clothing','detail'):
            s=copy.deepcopy(DEFAULT);s['views']=CONTRACT['presets'][preset]
            self.assertEqual(needs_analysis(s),preset in ('head','clothing','detail'))

    def test_scoped_features_keep_garments_free_of_identity_and_preserve_boxes(self):
        s=copy.deepcopy(DEFAULT);s['views']=VIEWS[:]
        s['character']['identity']='A brass robot with a red head and a purple coat.'
        features=parse_features(compact(dict(subject='ROBOT',head='RED_HEAD',outfit='PURPLE_COAT',hands='METAL_HANDS',feet='YELLOW_BOOTS',shared='')))
        original=preview(compact(s));result=apply_features(original,s,features)
        items=result['layout_draft']['items']
        self.assertEqual([i['bbox'] for i in items],[i['bbox'] for i in original['layout_draft']['items']])
        for i in (9,10):
            self.assertIn('PURPLE_COAT',items[i]['caption'])
            self.assertNotIn('RED_HEAD',items[i]['caption'])
            self.assertNotIn(s['character']['identity'],items[i]['caption'])
        self.assertIn('METAL_HANDS',items[11]['caption'])
        self.assertEqual((result['width'],result['height']),(original['width'],original['height']))
        self.assertNotEqual(result['prompt'],original['prompt'])
        self.assertNotIn('RED_HEAD',original['prompt'])

    def test_invalid_model_json_is_rejected_without_silent_fallback(self):
        valid=dict(subject='',head='',outfit='',hands='',feet='',shared='')
        for raw in ('not JSON',compact(dict(valid,unknown='')),compact(dict(valid,head=None)),compact(dict(valid,head='x'*1501))):
            with self.assertRaises(StateError):parse_features(raw)

    def test_node_reports_missing_prompt_and_accepts_entered_prompt(self):
        with patch.dict(sys.modules, {'nodes':types.SimpleNamespace(MAX_RESOLUTION=16384)}):
            from moss_image_character_sheet.node import MOSSImageCharacterSheetDesigner as Node
        raw=compact(DEFAULT)
        self.assertIs(Node.VALIDATE_INPUTS(raw),True)
        self.assertIn('E_PROMPT_EMPTY',Node.VALIDATE_INPUTS(raw,''))
        self.assertTrue(Node.INPUT_TYPES()['required']['prompt'][1]['forceInput'])
        with self.assertRaises(StateError):Node().compile(raw,'')
        state=copy.deepcopy(DEFAULT)
        state['character']['identity']='An adult woman wearing a navy jacket.'
        raw=compact(state)
        self.assertIs(Node.VALIDATE_INPUTS(raw),True)
        prompt,width,height=Node().compile(compact(DEFAULT),state['character']['identity'])['result']
        self.assertIn(state['character']['identity'],prompt)
        self.assertGreater(width,0)
        self.assertGreater(height,0)
    def test_auto_h3_horizontal_structure(self):
        s=copy.deepcopy(DEFAULT);s['views']=VIEWS[:]
        for budget in (1000000,1500000,2000000,4000000):
            s['size']['pixel_budget']=budget
            r=compute_layout(s);b={p['id']:p['bbox_px'] for p in r['panels']}
            self.assertEqual(len(r['rows']),1)
            self.assertGreater(r['canvas'][0]/r['canvas'][1],3)
            self.assertLessEqual(r['canvas'][0]*r['canvas'][1],budget)
            for v in ('body_left','body_back','clothing_front','clothing_back'):
                self.assertEqual(b[v][1],b['body_front'][1])
                self.assertEqual(b[v][3],b['body_front'][3])
            self.assertLess(b['face_back'][2],b['body_front'][0])
            self.assertGreater(b['hands'][0],b['clothing_back'][2])

    def test_single_portrait_uses_h3_auxiliary_width(self):
        s=copy.deepcopy(DEFAULT);s['views']=CONTRACT['presets']['basic']
        for budget in (1000000,1500000,2000000,4000000):
            s['size']['pixel_budget']=budget
            layout=compute_layout(s);b={p['id']:p['bbox_px'] for p in layout['panels']}
            self.assertAlmostEqual((b['face_front'][2]-b['face_front'][0])/(b['body_front'][2]-b['body_front'][0]),1.25,delta=.01)
            self.assertEqual(b['face_front'][1],b['body_front'][1])
            self.assertEqual(b['face_front'][3],b['body_front'][3])

    def test_composition_describes_groups_and_selected_order(self):
        s=copy.deepcopy(DEFAULT);s['views']=VIEWS[:];s['character']['identity']='A brass robot wearing a purple raincoat.'
        result=preview(compact(s));summary=result['layout_draft']['summary']['caption']
        self.assertIn('6 close-up headshots in 2 columns and 3 rows',summary)
        self.assertIn('paired hand detail, paired foot or footwear detail from top to bottom',summary)
        self.assertLess(summary.index('6 close-up headshots'),summary.index('3 full-length figures'))
        self.assertLess(summary.index('3 full-length figures'),summary.index('2 flat-laid outfits'))
        self.assertEqual(summary.count(s['character']['identity']),1)
        items=result['layout_draft']['items']
        self.assertEqual(len(items),13)
        self.assertEqual([item['bbox'] for item in items],[p['bbox_px'] for p in result['layout_plan']['panels']])
        self.assertTrue(all(item['label']=='character' for item in items[:6]))
        self.assertEqual(sum('back of the head' in item['caption'] for item in items[:6]),1)
        self.assertEqual(len(result['layout_plan']['panels']),13)
        s['views']=['face_front','face_right','face_back','feet']
        s['size'].update(mode='manual',manual_width=512,manual_height=2048)
        result=preview(compact(s));summary=result['layout_draft']['summary']['caption']
        self.assertIn('3 close-up headshots in 2 columns and 2 rows',summary)
        self.assertNotIn('right-facing profile portrait',summary)
        self.assertNotIn('paired hand detail',summary)
        self.assertIn('Sheet row 2',summary)
        self.assertEqual(len(result['layout_draft']['items']),4)

    def test_user_descriptions_are_not_character_specific(self):
        for identity in ('An elderly man in a red robe.', 'A woman wearing a blue work suit.', 'A humanoid robot with a smooth visor and ceramic armor.'):
            s=copy.deepcopy(DEFAULT);s['views']=VIEWS[:];s['character']['identity']=identity
            s['part_prompts']={'face':'FACIAL_MARKER','upper_clothing':'OUTFIT_MARKER','other':'COMMON_MARKER'}
            for mode in ('worn','garment'):
                s['appearance']['clothing_mode']=mode
                r=preview(compact(s));items=r['layout_draft']['items'];summary=r['layout_draft']['summary']['caption']
                self.assertEqual(summary.count(identity),1)
                self.assertEqual(summary.count('COMMON_MARKER'),1)
                self.assertEqual(len(r['layout_plan']['panels']),13)
                self.assertEqual(len(items),13)
                self.assertNotIn('FACIAL_MARKER',items[5]['caption'])
                self.assertIn('OUTFIT_MARKER',items[9]['caption'])
                self.assertEqual(items[9]['label'],'object')
                self.assertNotIn('clothing_mode',r['canonical_state']['appearance'])
                self.assertNotIn('outfit worn by',r['prompt'])
                self.assertNotIn('son goku',r['prompt'].lower())
    def test_prompt_fixtures(self):
        for name in ('five_view','single_view'):
            with self.subTest(name=name):
                result=preview((ROOT/f'examples/{name}_state.json').read_text(encoding='utf-8'))
                expected=json.loads((ROOT/f'examples/{name}_expected_result.json').read_text(encoding='utf-8'))
                self.assertEqual((result['width'],result['height']),(expected['width'],expected['height']))
                self.assertEqual(hashlib.sha256(result['prompt'].encode()).hexdigest(),expected['prompt_sha256'])

    def test_geometry_golden(self):
        golden=json.loads((ROOT/'verification/layout_golden_cases.json').read_text())
        for name,expected in golden.items():
            with self.subTest(name=name):
                state=copy.deepcopy(DEFAULT)
                state['views']=[v for v in VIEWS if v in expected['boxes']]
                state['size']['mode']=expected['mode']
                state['size']['pixel_budget']=expected['budget']
                if expected['mode']=='manual':
                    state['size'].update(manual_width=expected['width'],manual_height=expected['height'])
                result=compute_layout(state)
                self.assertEqual(result['canvas'],[expected['width'],expected['height']])
                self.assertEqual({p['id']:p['bbox_px'] for p in result['panels']},expected['boxes'])
                self.assertEqual(result['rows'],expected['rows'])
                self.assertAlmostEqual(result['actual_body_height'],expected['actual_body_height'])

    def test_strict_state(self):
        raw=compact(DEFAULT)
        for bad in (raw.replace('1120','1120.0'),raw.replace('1120','1.12e3'),raw.replace('1120','true'),raw.replace('1120','NaN'),raw.replace('"schema_version":1','"schema_version":1,"schema_version":1'),raw.replace('"identity":""','"identity":"\\ud800"')):
            with self.assertRaises(StateError): parse_state(bad)
        for mutation in (lambda s:s.update(unknown=1),lambda s:s.update(views=[]),lambda s:s.update(views=['hands','hands'])):
            s=copy.deepcopy(DEFAULT); mutation(s)
            with self.assertRaises(StateError):parse_state(compact(s))

    def test_unicode_and_blank(self):
        s=copy.deepcopy(DEFAULT)
        s['character']['identity']='日本語\n"😀"'
        self.assertEqual(parse_state(compact(s)),s)
        self.assertFalse(preview(compact(DEFAULT))['ready'])
        s['character']['identity']='😀'*1001
        with self.assertRaises(StateError):parse_state(compact(s))

    def test_manual_and_part_visibility(self):
        s=copy.deepcopy(DEFAULT);s['views']=VIEWS[:];s['character']['identity']='Example adult'
        s['part_prompts']={'face':'FACE_MARKER','hands':'HAND_MARKER','other':'OTHER_MARKER'}
        s['appearance']['clothing_mode']='garment'
        s['size'].update(mode='manual',manual_width=256,manual_height=16384)
        result=preview(compact(s));self.assertEqual([result['width'],result['height']],[256,16384])
        items=json.loads(result['prompt'])['items']
        by_id=dict(zip(VIEWS,items))
        self.assertNotIn('FACE_MARKER',by_id['face_back']['caption'])
        for v in ('body_back','clothing_front','clothing_back','hands','feet'):
            self.assertNotIn('FACE_MARKER',by_id[v]['caption'])
        self.assertNotIn('HAND_MARKER',by_id['clothing_front']['caption'])
        self.assertEqual(result['prompt'].count('OTHER_MARKER'),1)

    def test_garment_sheet_uses_product_description_and_keeps_source_text(self):
        s=copy.deepcopy(DEFAULT);s['views']=CONTRACT['presets']['clothing']
        s['character']['identity']='A humanoid robot in a purple coat.'
        s['part_prompts']={'head_hair':'HEAD_MARKER','face':'FACE_MARKER','hands':'HAND_MARKER','upper_clothing':'COAT_MARKER'}
        r=preview(compact(s));draft=r['layout_draft']
        self.assertIn('clothing-only reference sheet',draft['summary']['caption'])
        self.assertEqual(draft['summary']['caption'].count(s['character']['identity']),1)
        self.assertNotIn('The depicted character:',draft['summary']['caption'])
        for item in draft['items']:
            self.assertEqual(item['label'],'object')
            self.assertIn('flat-lay of the empty outfit',item['caption'])
            self.assertIn('Clothing only.',item['caption'])
            self.assertIn('COAT_MARKER',item['caption'])
            for text in ('HEAD_MARKER','FACE_MARKER','HAND_MARKER'):
                self.assertNotIn(text,item['caption'])

    def test_clothing_never_inherits_hand_or_body_setting(self):
        for hand_state in ('bare','gloved'):
            s=copy.deepcopy(DEFAULT);s['views']=VIEWS[:]
            s['character']['identity']='A character in a green coat.'
            s['appearance']['hand_state']=hand_state
            s['part_prompts']['lower_body']='Blue trousers.'
            items=preview(compact(s))['layout_draft']['items']
            by_id=dict(zip(VIEWS,items))
            for view in ('clothing_front','clothing_back'):
                caption=by_id[view]['caption']
                self.assertNotIn('Visible hands',caption)
                self.assertNotIn('lower-body',caption)
                self.assertIn('Lower-garment details: Blue trousers.',caption)
            self.assertIn('Visible hands',by_id['hands']['caption'])

if __name__=='__main__':unittest.main()
