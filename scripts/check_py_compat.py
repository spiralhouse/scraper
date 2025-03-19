#!/usr/bin/env python3
"""
Script to verify Python version compatibility with project requirements.
This helps identify packages that might not be compatible with specific Python versions.
"""

import sys
import subprocess
import tempfile
import os
import platform
from pathlib import Path

def check_requirements(requirements_file):
    """Test if all packages in the requirements file can be installed"""
    print(f"Checking compatibility of {requirements_file} with Python {platform.python_version()}")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a virtual environment in the temp directory
        venv_dir = os.path.join(tmpdir, "venv")
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        
        # Determine pip path
        if sys.platform.startswith('win'):
            pip_path = os.path.join(venv_dir, "Scripts", "pip")
        else:
            pip_path = os.path.join(venv_dir, "bin", "pip")
        
        # Upgrade pip
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
        
        # Test installing the requirements
        try:
            subprocess.run(
                [pip_path, "install", "-r", requirements_file], 
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✅ All packages in {requirements_file} are compatible with Python {platform.python_version()}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Some packages in {requirements_file} are NOT compatible with Python {platform.python_version()}")
            print("Error details:")
            print(e.stdout)
            print(e.stderr)
            return False

def main():
    """Main function"""
    proj_root = Path(__file__).parent.parent
    
    # Check both requirements files
    req_files = [
        proj_root / "requirements.txt",
        proj_root / "requirements-dev.txt"
    ]
    
    success = True
    for req_file in req_files:
        if req_file.exists():
            if not check_requirements(req_file):
                success = False
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 