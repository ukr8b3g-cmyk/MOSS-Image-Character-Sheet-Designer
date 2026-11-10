import copy,json,unittest
from moss_image_character_sheet.catalog import DEFAULT,VIEWS
from moss_image_character_sheet.compiler import preview
from moss_image_character_sheet.features import apply_features
from moss_image_character_sheet.state import compact,parse_state,StateError
class ViewPromptTests(unittest.TestCase):
 def test_formats_and_analysis_keep_every_edited_view(self):
  features=dict(subject='robot',head='metal head',outfit='',hands='metal hands',feet='metal feet',shared='')
  for views in (list(VIEWS),['clothing_front','clothing_back'],list(VIEWS)[:6]):
   for form in ('layout_json','caption'):
    s=copy.deepcopy(DEFAULT);s['character']['identity']='robot';s['views']=views;s['prompt_format']=form
    base=preview(compact(s));s['view_prompts']={v:'CUSTOM '+v+'\nSecond sentence.' for v in views}
    s['part_prompts']={'upper_clothing':'PURPLE_COAT'}
    result=preview(compact(s));after=apply_features(result,parse_state(compact(s)),features)
    self.assertEqual(base['layout_plan'],result['layout_plan'])
    self.assertEqual(parse_state(compact(result['canonical_state'])),s)
    for v,item in zip(views,after['layout_draft']['items']):
     self.assertIn('CUSTOM '+v+'\nSecond sentence.',item['caption'])
     if form=='layout_json':self.assertIn('CUSTOM '+v,json.loads(after['prompt'])['items'][views.index(v)]['caption'])
     else:self.assertIn('CUSTOM '+v,after['prompt'])
 def test_blank_reset_and_legacy(self):
  s=copy.deepcopy(DEFAULT);s['character']['identity']='robot';s['views']=['clothing_front','clothing_back']
  before=preview(compact(s));s['view_prompts']={'clothing_front':''}
  parsed=parse_state(compact(s));self.assertEqual(parsed['view_prompts']['clothing_front'],'')
  result=apply_features(preview(compact(s)),parsed,dict(subject='robot',head='',outfit='',hands='',feet='',shared=''))
  self.assertEqual(result['layout_draft']['items'][0]['caption'],'')
  del s['view_prompts'];self.assertEqual(before['prompt'],preview(compact(s))['prompt'])
 def test_reject_invalid_overrides(self):
  for raw in ('[]','null','3'):
   with self.assertRaises(StateError):parse_state(raw)
  for value in ({'bad':'x'},{'feet':200},{'feet':'x'*2001},{'feet':'\ud800'},[]):
   s=copy.deepcopy(DEFAULT);s['view_prompts']=value
   with self.assertRaises(StateError):parse_state(json.dumps(s))
