import copy
from moss_image_character_sheet.catalog import DEFAULT,VIEWS
from moss_image_character_sheet.layout import compute_layout

count=0
for budget in (1000000,1500000,2000000,4000000):
    for mask in range(1,8192):
        state=copy.deepcopy(DEFAULT)
        state['views']=[v for i,v in enumerate(VIEWS) if mask&(1<<i)]
        state['size']['pixel_budget']=budget
        plan=compute_layout(state)
        w,h=plan['canvas']
        assert w%16==h%16==0 and w*h<=budget
        assert [p['id'] for p in plan['panels']]==state['views']
        count+=1
    print(f'{budget}: 8191 combinations passed',flush=True)
print(f'C03: {count} passed')
