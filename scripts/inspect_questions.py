"""Inspect all question bank Excel files to understand their structures."""
import os
import struct

base_dir = r"D:\My_Program\codex\PyGrow\Chapter Resources"

# Collect all question bank files
dirs = [
    os.path.join(base_dir, "python_cer_base_resources", "题库"),
    os.path.join(base_dir, "python_cer_midd_resource", "03-题库"),
    os.path.join(base_dir, "python_cer_senior_resource", "03-题库"),
]

for d in dirs:
    if not os.path.exists(d):
        print(f"MISSING: {d}")
        continue
    for f in sorted(os.listdir(d)):
        if f.startswith("~$"):
            continue
        path = os.path.join(d, f)
        with open(path, "rb") as fh:
            magic = fh.read(4)
        is_zip = magic[:2] == b"PK"
        print(f"  {f} | magic={magic.hex()} | {'ZIP/xlsx' if is_zip else 'OLE/xls'}")

print("\n--- Done ---")
