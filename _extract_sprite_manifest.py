import json
from pathlib import Path

src = Path('design_handoff_dnd_vtt/data/assets.js').read_text(encoding='utf-8')
obj = src[src.index('{'): src.rindex('}') + 1]
data = json.loads(obj)
out = Path('dd3esheet/sprites/fixtures/sprite_manifest.json')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
print('assets:', data['total'], 'sections:', len(data['sections']))
