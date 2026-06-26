import glob
import re

for f in glob.glob('c:/Users/5600/Documents/G1/server-python/routers/*.py'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    content = re.sub(r'@router\.get\("/",', '@router.get("",', content)
    content = re.sub(r'@router\.get\("\/"\)', '@router.get("")', content)
    content = re.sub(r'@router\.post\("/",', '@router.post("",', content)
    content = re.sub(r'@router\.post\("\/"\)', '@router.post("")', content)
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
print("done")
