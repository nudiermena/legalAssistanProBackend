#!/usr/bin/env python3
"""
Build script for Vercel deployment optimization.
This script helps prepare the project for deployment by:
1. Cleaning up unnecessary files
2. Optimizing dependencies
3. Creating deployment-ready structure
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def clean_large_files():
    """Remove large files that shouldn't be deployed."""
    large_dirs = [
        'data',
        'data_integration', 
        'data_pipeline_output',
        'tmp',
        'tmp_html',
        'venv',
        '__pycache__',
        '.git'
    ]
    
    large_files = [
        '*.json',
        '*.csv', 
        '*.log',
        '*.png',
        '*.jpg',
        '*.jpeg',
        '*.gif',
        '*.pdf'
    ]
    
    print("Cleaning large files and directories...")
    
    for dir_name in large_dirs:
        if os.path.exists(dir_name):
            print(f"Removing directory: {dir_name}")
            shutil.rmtree(dir_name, ignore_errors=True)
    
    # Remove large files
    for pattern in large_files:
        for file_path in Path('.').glob(f'**/{pattern}'):
            if file_path.is_file() and file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                print(f"Removing large file: {file_path}")
                file_path.unlink()

def optimize_requirements():
    """Create optimized requirements file for Vercel."""
    print("Creating optimized requirements file...")
    
    # Read the original requirements
    with open('requirements.txt', 'r') as f:
        original_reqs = f.read()
    
    # Create optimized version
    optimized_reqs = []
    skip_packages = ['PyMuPDF', 'agno']  # Skip large/problematic packages
    
    for line in original_reqs.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            package_name = line.split('==')[0].split('>=')[0].split('<=')[0]
            if package_name not in skip_packages:
                optimized_reqs.append(line)
    
    with open('requirements-vercel.txt', 'w') as f:
        f.write('\n'.join(optimized_reqs))
    
    print("Optimized requirements created: requirements-vercel.txt")

def create_vercel_ignore():
    """Ensure .vercelignore is properly configured."""
    print("Updating .vercelignore...")
    
    ignore_content = """# Large binary files and dependencies
**/*.dll
**/*.pyd
**/*.so
**/*.dylib

# Virtual environment
venv/
env/
.venv/
.env/

# Data directories
data/
data_integration/
data_pipeline_output/
tmp/
tmp_html/

# Large data files
*.json
*.csv
*.log
*.png
*.jpg
*.jpeg
*.gif
*.pdf

# Development files
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db

# Documentation
*.md
docs/

# Test files
tests/
test_*
*_test.py

# Scraped data
scraped_legal_documents_*.json
processed_legal_documents_*.json
legal_database_pipeline_*.log
scraping_errors.log
failed_urls.log

# Screenshots and debug files
*_debug.html
*_screenshot.png
page_screenshot_*.png
page_content_*.html
page_text_*.txt

# Pipeline outputs
pipeline_report_*.json
knowledge_base_population_report_*.json
network_analysis_*.json
api_response_*.txt
constitutional_court_*.json
constitutional_court_*.html
search_results_*.png
"""
    
    with open('.vercelignore', 'w') as f:
        f.write(ignore_content)
    
    print(".vercelignore updated")

def main():
    """Main build process."""
    print("Starting Vercel build optimization...")
    
    try:
        clean_large_files()
        optimize_requirements()
        create_vercel_ignore()
        
        print("\n✅ Build optimization complete!")
        print("\nNext steps:")
        print("1. Commit your changes")
        print("2. Push to your repository")
        print("3. Redeploy on Vercel")
        print("\nThe deployment should now be under 250MB limit.")
        
    except Exception as e:
        print(f"❌ Error during build optimization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
