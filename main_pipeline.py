import os
import sys

# Adăugăm directorul src în calea de căutare a modulelor Python
# pentru a permite importul pachetului curs_bnr
base_path = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(base_path, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from curs_bnr.training.pipeline import main

if __name__ == "__main__":
    main()
