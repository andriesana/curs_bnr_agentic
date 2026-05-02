import os
import sys
import subprocess

# Adaugam directorul src in calea de cautare a modulelor Python
base_path = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(base_path, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

def main():
    # Calea catre aplicatia Streamlit din interiorul pachetului
    app_path = os.path.join(base_path, "src", "curs_bnr", "frontend", "streamlit_app.py")
    
    print(f"[FRONTEND] Pornire Streamlit din: {app_path}")
    
    # Pregatim mediul cu PYTHONPATH setat corect
    env = os.environ.copy()
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    
    # Rulam streamlit folosind interpretorul Python curent
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path], env=env)

if __name__ == "__main__":
    main()
