"""
Read frontend/src/data/courseData.js and regenerate the COURSES_DATA block in seed.py.
Run from the backend directory: python scripts/sync_course_data.py
"""
import json
import re
from pathlib import Path

FRONTEND_DATA = Path(__file__).resolve().parent.parent.parent / "frontend" / "src" / "data" / "courseData.js"
SEED_PY = Path(__file__).resolve().parent.parent / "app" / "seed.py"

CATEGORY_MAP = {'初级': 'Basic', '中级': 'Medium', '高级': 'Advanced'}
COLOR_MAP = {
    '初级': 'bg-blue-100 text-blue-500',
    '中级': 'bg-purple-100 text-purple-500',
    '高级': 'bg-orange-100 text-orange-500',
}
ICON_MAP = {'初级': 'fab fa-python', '中级': 'fas fa-code', '高级': 'fas fa-crown'}
COVER_MAP = {
    '初级': 'bg-gradient-to-r from-blue-500 to-cyan-400',
    '中级': 'bg-gradient-to-r from-purple-500 to-pink-500',
    '高级': 'bg-gradient-to-r from-orange-500 to-red-600',
}

def main():
    # Read frontend data
    with open(FRONTEND_DATA, 'r', encoding='utf-8') as f:
        content = f.read()

    start = content.index('[')
    depth = 0
    for i, c in enumerate(content[start:], start):
        if c == '[':
            depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    levels = json.loads(content[start:end])

    # Build COURSES_DATA lines
    lines = ['COURSES_DATA = [']

    for idx, level in enumerate(levels):
        bvid = level['chapters'][0].get('bvid', '')
        level_id = level['id']

        # Collect all lessons
        lesson_tuples = []
        for ch in level['chapters']:
            chapter_title = ch['title']
            for sec in ch['sections']:
                for l in sec['lessons']:
                    lesson_tuples.append((chapter_title, l['title'], l['duration'], l['page']))

        lines.append('    {')
        lines.append(f'        "id": {idx + 1},')
        lines.append(f'        "title": "{level["name"]}",')
        lines.append(f'        "description": "{level.get("description", level["name"])}",')
        lines.append(f'        "category": "{CATEGORY_MAP.get(level_id, "Basic")}",')
        lines.append(f'        "category_color": "{COLOR_MAP.get(level_id, "bg-blue-100 text-blue-500")}",')
        lines.append(f'        "icon": "{ICON_MAP.get(level_id, "fab fa-python")}",')
        lines.append(f'        "cover_color": "{COVER_MAP.get(level_id, "bg-gradient-to-r from-blue-500 to-cyan-400")}",')
        lines.append(f'        "bvid": "{bvid}",')
        lines.append(f'        "sort_order": {idx + 1},')
        lines.append(f'        "lessons": [')

        for i, (ch_title, l_title, dur, page) in enumerate(lesson_tuples):
            comma = ',' if i < len(lesson_tuples) - 1 else ''
            # Escape any double quotes in titles
            ch_esc = ch_title.replace('"', '\\"')
            l_esc = l_title.replace('"', '\\"')
            lines.append(f'            ("{ch_esc}", "{l_esc}", "{dur}", {page}){comma}')

        lines.append('        ]')
        lines.append('    },')

    lines.append(']')
    new_courses_block = '\n'.join(lines)

    # Read current seed.py
    with open(SEED_PY, 'r', encoding='utf-8') as f:
        seed_content = f.read()

    # Find and replace the COURSES_DATA block
    # Pattern: from "COURSES_DATA = [" to the matching "]" followed by newline
    start_marker = 'COURSES_DATA = ['
    start_pos = seed_content.index(start_marker)

    # Find matching closing bracket
    depth = 0
    for i, c in enumerate(seed_content[start_pos:], start_pos):
        if c == '[':
            depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0:
                end_pos = i + 1
                break

    new_seed = seed_content[:start_pos] + new_courses_block + seed_content[end_pos:]

    with open(SEED_PY, 'w', encoding='utf-8') as f:
        f.write(new_seed)

    print(f"Updated seed.py: {len(levels)} courses, {sum(len(lt) for lt in [ls for ls in [[l for ch in lvl['chapters'] for sec in ch['sections'] for l in sec['lessons']] for lvl in levels]])} total lessons")

if __name__ == '__main__':
    main()
