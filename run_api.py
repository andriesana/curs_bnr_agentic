import uvicorn
import os
import sys

# Adaugam directorul src in calea de cautare a modulelor Python
base_path = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(base_path, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

if __name__ == "__main__":
    # Pornim serverul FastAPI folosind Uvicorn
    print("[API] Pornire server la http://127.0.0.1:8000")
    uvicorn.run("curs_bnr.api.app:app", host="127.0.0.1", port=8000, reload=True)
