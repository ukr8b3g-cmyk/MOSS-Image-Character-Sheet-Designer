__version__ = '1.0'
from .moss_image_character_sheet.node import MOSSImageCharacterSheetDesigner, MOSSComposeScopedSheet
from .moss_image_character_sheet.preview import register_preview

NODE_CLASS_MAPPINGS={'MOSSImageCharacterSheetDesigner':MOSSImageCharacterSheetDesigner,'_MOSSComposeScopedSheet':MOSSComposeScopedSheet}
NODE_DISPLAY_NAME_MAPPINGS={'MOSSImageCharacterSheetDesigner':'MOSS-Image Character Sheet Designer v1.0'}
WEB_DIRECTORY='./web'
register_preview()
