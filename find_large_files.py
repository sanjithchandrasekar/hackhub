import os
base = r"e:\Projects\hackhub\geo-engine"
results = []
for root, dirs, files in os.walk(base):
    if "node_modules" in root or "venv" in root:
        continue
    for f in files:
        fp = os.path.join(root, f)
        try:
            results.append((fp, os.path.getsize(fp)))
        except:
            pass
results.sort(key=lambda x: x[1], reverse=True)
for fp, s in results[:30]:
    print(f"{s/1024/1024:.2f} MB - {fp}")
