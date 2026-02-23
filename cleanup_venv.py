import os
import shutil

backend_dir = r'c:\Users\hisham\Desktop\compute_test\parametric-platform\Growvity\backend'
redundant_items = ['Include', 'Lib', 'Scripts', 'pyvenv.cfg']

for item in redundant_items:
    path = os.path.join(backend_dir, item)
    try:
        if os.path.isfile(path):
            os.remove(path)
            print(f"Deleted file: {path}")
        elif os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
            print(f"Deleted dir: {path}")
        else:
            print(f"Path not found: {path}")
    except Exception as e:
        print(f"Error deleting {path}: {e}")
