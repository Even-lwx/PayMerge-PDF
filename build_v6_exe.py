#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import os
from pathlib import Path

def build_v6_exe():
    print("=" * 60)
    print("Start packaging Invoice Merge Tool v6.0")
    print("=" * 60)
    
    # Check PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not installed")
        print("Please run: pip install pyinstaller")
        return False
    
    # Check required libs
    required_libs = ['pypdfium2', 'Pillow']
    missing_libs = []
    
    for lib in required_libs:
        try:
            __import__(lib.lower() if lib != 'Pillow' else 'PIL')
            print(f"OK {lib} installed")
        except ImportError:
            missing_libs.append(lib)
            print(f"ERROR {lib} not installed")
    
    if missing_libs:
        print(f"\nPlease install missing libs: pip install {' '.join(missing_libs)}")
        return False
    
    # PyInstaller command
    icon_path = Path('source/icon.ico')
    if not icon_path.exists():
        print("WARNING: icon.ico not found, building without icon")
        icon_arg = '--icon=NONE'
    else:
        icon_arg = f'--icon={icon_path}'
    
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=ASC_InvoiceMergeTool_v6.1',
        icon_arg,
        '--add-data=merge_invoices_v6.py;.',
        '--add-data=source/icon.ico;source',
        '--add-data=source/1.png;source',
        '--clean',
        'invoice_merger_v6.py'
    ]
    
    print("\nPackaging...")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True)
        
        print("\n" + "=" * 60)
        print("SUCCESS! Package complete!")
        print("=" * 60)
        print("\nExecutable location:")
        print(f"  dist/InvoiceMergeTool_v6.exe")
        print("\nInstructions:")
        print("1. First run will ask for name and group")
        print("2. Supports multi-page PDF invoices (2-3 pages)")
        print("3. Output files auto-saved to app root directory")
        print("4. File naming: Name_Group_Amount_InvoiceLastFour.pdf")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Packaging failed: {e}")
        return False
    except Exception as e:
        print(f"\nERROR: {e}")
        return False


def main():
    os.chdir(Path(__file__).parent)
    
    if not os.path.exists('invoice_merger_v6.py'):
        print("ERROR: invoice_merger_v6.py not found")
        return 1
    
    if not os.path.exists('merge_invoices_v6.py'):
        print("ERROR: merge_invoices_v6.py not found")
        return 1
    
    success = build_v6_exe()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
