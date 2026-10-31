from nodes import MAX_RESOLUTION
from .catalog import DEFAULT, REVISION
from .compiler import preview
from .state import compact, StateError, fail, parse_state, nonblank
from .features import INSTRUCTION, needs_analysis, parse_features, apply_features

def encoder_link(execution_graph, node_id):
    links = set()
    if execution_graph is not None:
        for key in execution_graph.all_node_ids():
            node = execution_graph.get_node(key)
            inputs = node.get('inputs', {})
            if node['class_type']=='CLIPTextEncode' and inputs.get('text')==[node_id,0]:
                clip = inputs.get('clip')
                if isinstance(clip,list) and len(clip)==2:
                    links.add(tuple(clip))
    if len(links)!=1:
        fail('E_ANALYSIS_ENCODER', 'prompt', 'Connect this prompt output directly to one MOSS CLIPTextEncode encoder. / prompt出力をMOSSのCLIPTextEncodeへ直接接続してください。')
    return list(links.pop())

def output(result):
    status={k:result[k] for k in ('compiler_revision','input_hash','width','height','resolved_format')}
    status['warning_codes'] = [warning['code'] for warning in result['warnings']]
    return {'ui':{'moss_sheet_status':[status]},'result':(result['prompt'],result['width'],result['height'])}

class MOSSImageCharacterSheetDesigner:
    CATEGORY='MOSS-Image/Character Sheet'
    FUNCTION='compile'
    RETURN_TYPES=('STRING','INT','INT')
    RETURN_NAMES=('prompt','width','height')
    DESCRIPTION='Choose illustrated views and describe the character. Connect prompt to positive CLIPTextEncode and width/height to EmptyFlux2LatentImage. Edit the negative prompt in a separate CLIPTextEncode.'

    @classmethod
    def INPUT_TYPES(cls):
        return {'required':{'prompt':('STRING',{'forceInput':True}),'state_json':('STRING',{'default':compact(DEFAULT),'multiline':True,'dynamicPrompts':False})},'hidden':{'execution_graph':'DYNPROMPT','node_id':'UNIQUE_ID'}}

    @classmethod
    def IS_CHANGED(cls, state_json, **kwargs):
        # The encoder is a downstream connection, so rebuild the tiny expansion
        # when targeting it. ComfyUI still caches the internal TextGenerate node.
        return float('nan') if needs_analysis(parse_state(state_json,MAX_RESOLUTION)) else False

    @classmethod
    def VALIDATE_INPUTS(cls,state_json,prompt=None):
        try:
            parse_state(state_json,MAX_RESOLUTION)
            if prompt is not None and (not isinstance(prompt,str) or not nonblank(prompt)):
                return 'E_PROMPT_EMPTY: prompt入力に人物・衣装の説明を接続してください。 / Connect a nonempty prompt.'
            return True
        except StateError as error:
            return str(error)

    def compile(self,state_json,prompt,execution_graph=None,node_id=None):
        if not isinstance(prompt,str) or not nonblank(prompt):
            fail('E_PROMPT_EMPTY','prompt','prompt入力に人物・衣装の説明を接続してください。 / Connect a nonempty prompt.')
        state=parse_state(state_json,MAX_RESOLUTION)
        state['character']={'identity':prompt,'outfit':''}
        if needs_analysis(state):
            from comfy_execution.graph_utils import GraphBuilder
            clip = encoder_link(execution_graph, node_id)
            graph = GraphBuilder()
            analysis = graph.node('TextGenerate',clip=clip,prompt=INSTRUCTION+prompt,max_length=512,sampling_mode='off',thinking=False,mtp='off',use_default_template=True)
            composed = graph.node('_MOSSComposeScopedSheet',state_json=compact(state),features_json=analysis.out(0))
            composed.set_override_display_id(node_id)
            return {'result':tuple(composed.out(i) for i in range(3)),'expand':graph.finalize()}
        result=preview(compact(state),MAX_RESOLUTION)
        return output(result)

class MOSSComposeScopedSheet:
    CATEGORY='_internal/MOSS-Image'
    DEPRECATED=True
    FUNCTION='compile'
    RETURN_TYPES=('STRING','INT','INT')

    @classmethod
    def INPUT_TYPES(cls):
        return {'required':{'state_json':('STRING',),'features_json':('STRING',)}}

    def compile(self,state_json,features_json):
        state=parse_state(state_json,MAX_RESOLUTION)
        result=preview(compact(state),MAX_RESOLUTION)
        return output(apply_features(result,state,parse_features(features_json)))
