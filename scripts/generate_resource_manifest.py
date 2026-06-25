"""Scan resource directories and generate a chapter-keyed JSON manifest."""

import os, re, json, shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIND_DIR = os.path.join(BASE, 'img&vidio', 'Mind Map')
RES_DIR = os.path.join(BASE, 'Chapter Resources')
OUT_DIR = os.path.join(BASE, 'frontend', 'public', 'resources')
OUT_JS = os.path.join(BASE, 'frontend', 'src', 'data', 'resourceData.js')

MIND_MAP = {
    '初级': 'Beginner',
    '中级': 'intermediate',
    '高级': 'advanced',
}

RES_MAP = {
    '初级': 'python_cer_base_resources',
    '中级': 'python_cer_midd_resource',
    '高级': 'python_cer_senior_resource',
}

CH_NUM_RE = re.compile(r'第\s*(\d+)\s*章')

def parse_chapter_num(name):
    m = CH_NUM_RE.search(name)
    if m:
        return int(m.group(1))
    # Try "12章" style
    m = re.match(r'(\d+)\s*章', name)
    if m:
        return int(m.group(1))
    # Try Chinese numerals
    cn = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,'十一':11,'十二':12}
    for k, v in cn.items():
        if name.startswith('第' + k + '章'):
            return v
    return None

def get_public_path(local_path):
    """Convert absolute filesystem path to public URL path. Served by backend static mount."""
    rel = os.path.relpath(local_path, BASE)
    return '/api/resources/static/' + rel.replace('\\', '/')

def scan_mind_maps():
    result = {}  # key: (level, ch_num) -> list of files
    for level, dirname in MIND_MAP.items():
        d = os.path.join(MIND_DIR, dirname)
        if not os.path.isdir(d):
            continue
        for fname in sorted(os.listdir(d)):
            if not fname.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.pdf')):
                continue
            ch = parse_chapter_num(fname)
            if ch is None:
                print(f'  WARN: Cannot parse chapter from mind map: {fname}')
                continue
            src = os.path.join(d, fname)
            key = (level, ch)
            if key not in result:
                result[key] = []
            result[key].append({'name': fname.rsplit('.', 1)[0], 'url': get_public_path(src)})
    return result

def scan_ppt_files():
    result = {}
    for level, dirname in RES_MAP.items():
        base_d = os.path.join(RES_DIR, dirname)
        if not os.path.isdir(base_d):
            continue
        # Find PPT directory
        ppt_dir = None
        for sub in os.listdir(base_d):
            sub_l = sub.lower()
            if 'ppt' in sub_l or '课件' in sub_l:
                ppt_dir = os.path.join(base_d, sub)
                break
        if not ppt_dir or not os.path.isdir(ppt_dir):
            continue

        # Check if PPTs are in chapter subdirs or flat files
        has_subdirs = any(os.path.isdir(os.path.join(ppt_dir, x)) for x in os.listdir(ppt_dir))

        if has_subdirs:
            for ch_dir in sorted(os.listdir(ppt_dir)):
                ch_path = os.path.join(ppt_dir, ch_dir)
                if not os.path.isdir(ch_path):
                    continue
                ch = parse_chapter_num(ch_dir)
                if ch is None:
                    print(f'  WARN: Cannot parse chapter from PPT dir: {ch_dir}')
                    continue
                for ppt_file in sorted(os.listdir(ch_path)):
                    if ppt_file.lower().endswith(('.pptx', '.ppt')):
                        key = (level, ch)
                        if key not in result:
                            result[key] = []
                        result[key].append({
                            'name': ppt_file.rsplit('.', 1)[0],
                            'url': get_public_path(os.path.join(ch_path, ppt_file)),
                        })
        else:
            # Flat: parse chapter from filename like "1.2-xxx.pptx"
            for ppt_file in sorted(os.listdir(ppt_dir)):
                if not ppt_file.lower().endswith(('.pptx', '.ppt')):
                    continue
                m = re.match(r'(\d+)\.', ppt_file)
                if not m:
                    continue
                ch = int(m.group(1))
                key = (level, ch)
                if key not in result:
                    result[key] = []
                result[key].append({
                    'name': ppt_file.rsplit('.', 1)[0],
                    'url': get_public_path(os.path.join(ppt_dir, ppt_file)),
                })
    return result

def scan_code_files():
    result = {}
    for level, dirname in RES_MAP.items():
        base_d = os.path.join(RES_DIR, dirname)
        if not os.path.isdir(base_d):
            continue
        # Find code directory
        code_dir = None
        for sub in os.listdir(base_d):
            sub_l = sub.lower()
            if '源码' in sub_l or '案例' in sub_l or 'code' in sub_l:
                code_dir = os.path.join(base_d, sub)
                break
        if not code_dir or not os.path.isdir(code_dir):
            continue

        for ch_dir in sorted(os.listdir(code_dir)):
            ch_path = os.path.join(code_dir, ch_dir)
            if not os.path.isdir(ch_path):
                continue
            ch = parse_chapter_num(ch_dir)
            if ch is None:
                print(f'  WARN: Cannot parse chapter from code dir: {ch_dir}')
                continue
            # Collect all .py and .zip files recursively
            py_files = []
            for root, dirs, files in os.walk(ch_path):
                for f in sorted(files):
                    if f.lower().endswith(('.py', '.zip', '.rar', '.7z', '.tar.gz', '.ipynb')):
                        py_files.append({
                            'name': f,
                            'url': get_public_path(os.path.join(root, f)),
                        })
            if py_files:
                key = (level, ch)
                if key not in result:
                    result[key] = []
                result[key].extend(py_files)
    return result

def build_manifest():
    mind = scan_mind_maps()
    ppt = scan_ppt_files()
    code = scan_code_files()

    # Merge all by (level, chapter)
    all_keys = set(list(mind.keys()) + list(ppt.keys()) + list(code.keys()))
    manifest = []

    for level in ['初级', '中级', '高级']:
        ch_keys = sorted([k for k in all_keys if k[0] == level], key=lambda x: x[1])
        for key in ch_keys:
            _, ch = key
            entry = {
                'level': level,
                'chapter': ch,
                'mindMaps': mind.get(key, []),
                'ppts': ppt.get(key, []),
                'codes': code.get(key, []),
            }
            manifest.append(entry)

    return manifest

def main():
    # Ensure public resources directory exists
    os.makedirs(OUT_DIR, exist_ok=True)

    manifest = build_manifest()

    # Write JS module
    os.makedirs(os.path.dirname(OUT_JS), exist_ok=True)
    with open(OUT_JS, 'w', encoding='utf-8') as f:
        f.write('// Auto-generated by scripts/generate_resource_manifest.py\n')
        f.write('export const resourceManifest = ')
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write(';\n')

    # Print summary
    for entry in manifest:
        mm = len(entry['mindMaps'])
        pp = len(entry['ppts'])
        cc = len(entry['codes'])
        if mm + pp + cc > 0:
            print(f"  {entry['level']} 第{entry['chapter']}章: {mm} mindmaps, {pp} PPTs, {cc} code files")

    print(f'\nTotal: {len(manifest)} chapter entries')
    print(f'Written: {OUT_JS}')

if __name__ == '__main__':
    main()
