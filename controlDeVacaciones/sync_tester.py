import os
import subprocess
from datetime import datetime
from pathlib import Path

# Mock settings
BASE_DIR = r"c:\Sistemas ABBAMAT\ControlDeVacaciones\controlDeVacaciones"

def test_github_sync():
    project_dir = str(BASE_DIR)
    # Buscar raíz real
    current = os.path.abspath(project_dir)
    found_root = current
    for _ in range(5):
        if os.path.exists(os.path.join(current, '.git')):
            found_root = current
            break
        parent = os.path.dirname(current)
        if parent == current: break
        current = parent
    
    project_dir = found_root
    print(f"Project dir: {project_dir}")
    
    # 1. Verificar cambios
    print("Checking status...")
    status_res = subprocess.run(['git', 'status', '--porcelain'], cwd=project_dir, capture_output=True, text=True)
    if status_res.stdout.strip():
        print("Changes detected. Adding and committing...")
        subprocess.run(['git', 'add', '-A'], cwd=project_dir, check=True, capture_output=True)
        commit_msg = f'Sincronización test - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        subprocess.run(['git', 'commit', '-m', commit_msg], cwd=project_dir, capture_output=True)
        
        print("Pushing...")
        push_res = subprocess.run(['git', 'push', 'origin', 'main'], cwd=project_dir, capture_output=True, text=True)
        print(f"Return code: {push_res.returncode}")
        print(f"Stdout: {push_res.stdout}")
        print(f"Stderr: {push_res.stderr}")
    else:
        print("No changes. Pushing anyway...")
        push_res = subprocess.run(['git', 'push', 'origin', 'main'], cwd=project_dir, capture_output=True, text=True)
        print(f"Return code: {push_res.returncode}")
        print(f"Stdout: {push_res.stdout}")
        print(f"Stderr: {push_res.stderr}")

if __name__ == "__main__":
    test_github_sync()
