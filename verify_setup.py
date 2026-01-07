#!/usr/bin/env python3
"""verify_setup.py - Verify multi-VM pipeline setup"""

import os
import sys
from pathlib import Path

def check_file(path, name):
    """Check if file exists and get size."""
    p = Path(path)
    if p.exists():
        size = p.stat().st_size
        return (True, f"OK: {name} ({size} bytes)")
    else:
        return (False, f"MISSING: {name}")

def check_content(path, pattern):
    """Check if file contains pattern."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            return pattern in content
    except:
        return False

def main():
    print("\n" + "="*70)
    print("  MULTI-VM HONEYPOT PIPELINE - VERIFICATION")
    print("="*70 + "\n")
    
    passed = []
    failed = []
    warnings = []
    
    os.chdir("C:\\project")
    
    # Core files
    print("Checking core files...")
    core_files = {
        "Vagrantfile": "C:\\project\\Vagrantfile",
        "docker-compose.yml": "C:\\project\\docker-compose.yml",
        "run_all.ps1": "C:\\project\\run_all.ps1",
        "run_docker.ps1": "C:\\project\\run_docker.ps1",
        "merge_sessions.py": "C:\\project\\merge_sessions.py",
        "append_session_csv.py": "C:\\project\\append_session_csv.py",
        "test_client_interactive.py": "C:\\project\\test_client_interactive.py",
    }
    
    for name, path in core_files.items():
        ok, msg = check_file(path, name)
        if ok:
            passed.append(msg)
            print(f"  [OK] {msg}")
        else:
            failed.append(msg)
            print(f"  [FAIL] {msg}")
    
    # Vagrant scripts
    print("\nChecking vagrant scripts...")
    vagrant_files = {
        "provision_honeypot.sh": "C:\\project\\vagrant\\provision_honeypot.sh",
        "run_merge_loop.sh": "C:\\project\\vagrant\\run_merge_loop.sh",
    }
    
    for name, path in vagrant_files.items():
        ok, msg = check_file(path, f"vagrant/{name}")
        if ok:
            passed.append(msg)
            print(f"  [OK] {msg}")
        else:
            failed.append(msg)
            print(f"  [FAIL] {msg}")
    
    # Check source file modifications
    print("\nChecking source file modifications...")
    if check_content("src/evidence_store.py", "append_session_csv"):
        passed.append("OK: src/evidence_store.py has CSV integration")
        print("  [OK] src/evidence_store.py - CSV integration found")
    else:
        warnings.append("WARN: src/evidence_store.py - CSV integration unclear")
        print("  [WARN] src/evidence_store.py - CSV integration not confirmed")
    
    if check_content("src/orchestrator.py", "save_session_data"):
        passed.append("OK: src/orchestrator.py has session tracking")
        print("  [OK] src/orchestrator.py - session tracking found")
    else:
        warnings.append("WARN: src/orchestrator.py - session tracking unclear")
        print("  [WARN] src/orchestrator.py - session tracking not confirmed")
    
    # Check app_auto.py exists
    print("\nChecking dashboard...")
    if Path("app_auto.py").exists():
        passed.append("OK: app_auto.py found")
        print("  [OK] app_auto.py - Streamlit dashboard found")
    else:
        failed.append("FAIL: app_auto.py missing")
        print("  [FAIL] app_auto.py - Streamlit dashboard missing")
    
    # Check documentation
    print("\nChecking documentation...")
    docs = {
        "MULTIVM_README.md": "C:\\project\\MULTIVM_README.md",
        "QUICK_START.md": "C:\\project\\QUICK_START.md",
        "IMPLEMENTATION_SUMMARY.md": "C:\\project\\IMPLEMENTATION_SUMMARY.md",
    }
    
    for name, path in docs.items():
        ok, msg = check_file(path, name)
        if ok:
            passed.append(msg)
            print(f"  [OK] {msg}")
        else:
            warnings.append(msg)
            print(f"  [WARN] {msg}")
    
    # Summary
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    print(f"\nPassed: {len(passed)}")
    print(f"Failed: {len(failed)}")
    print(f"Warnings: {len(warnings)}")
    
    if len(failed) == 0:
        print("\n[SUCCESS] All critical components present!")
        print("\nYou can now run:")
        print("  PowerShell> run_docker.ps1      (Recommended - Docker)")
        print("  PowerShell> run_all.ps1         (Alternative - Vagrant)")
        return 0
    else:
        print("\n[ERROR] Some critical components missing!")
        print("\nFailed checks:")
        for msg in failed:
            print(f"  - {msg}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
