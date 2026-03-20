#!/usr/bin/env python3
"""
Quick status checker for batch job logs.
Usage: python3 check_status.py logs/260311
"""

import sys
import os
from pathlib import Path
import re

def check_log_status(log_file):
    """
    Check a log file and return status.
    Returns: (status, key_info)
        status: 'SUCCESS', 'FAILED', 'RUNNING', 'UNKNOWN'
        key_info: relevant message
    """
    if not log_file.exists():
        return 'MISSING', 'File does not exist'
    
    try:
        with open(log_file, 'r') as f:
            content = f.read()
    except Exception as e:
        return 'ERROR', f'Cannot read file: {e}'
    
    if not content.strip():
        return 'EMPTY', 'Log file is empty (still running?)'
    
    lines = content.split('\n')
    last_100_lines = '\n'.join(lines[-100:])
    
    # Check for explicit failures
    error_patterns = [
        r'ERROR:',
        r'EXCEPTION:',
        r'Traceback \(most recent call last\)',
        r'FAILED',
        r'No such file or directory',
        r'command not found',
        r'Segmentation fault',
        r'core dumped'
    ]
    
    for pattern in error_patterns:
        if re.search(pattern, last_100_lines, re.IGNORECASE):
            # Find the actual error line
            for line in reversed(lines[-50:]):
                if re.search(pattern, line, re.IGNORECASE):
                    return 'FAILED', line.strip()[:100]
    
    # Check for success indicators
    success_patterns = [
        r'ALL PHASES COMPLETE',
        r'Harvesting complete:.*successful',
        r'Phase.*complete',
        r'Done'
    ]
    
    for pattern in success_patterns:
        if re.search(pattern, last_100_lines, re.IGNORECASE):
            return 'SUCCESS', 'Completed successfully'
    
    # Check if still running (file updated recently)
    mtime = log_file.stat().st_mtime
    import time
    age_seconds = time.time() - mtime
    
    if age_seconds < 60:  # Modified in last minute
        return 'RUNNING', f'Active (updated {int(age_seconds)}s ago)'
    elif age_seconds < 300:  # Modified in last 5 minutes
        return 'RUNNING?', f'Possibly running (updated {int(age_seconds/60)}m ago)'
    
    # If we get here, unclear status
    last_line = [l for l in lines if l.strip()][-1] if any(l.strip() for l in lines) else ''
    return 'UNKNOWN', last_line[:100] if last_line else 'No clear status'

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check_status.py <log_directory>")
        print("Example: python3 check_status.py logs/260311")
        sys.exit(1)
    
    log_dir = Path(sys.argv[1])
    
    if not log_dir.exists():
        print(f"ERROR: Directory {log_dir} does not exist")
        sys.exit(1)
    
    # Find all log files
    log_files = sorted(log_dir.glob('*_log'))
    
    if not log_files:
        print(f"No log files found in {log_dir}")
        sys.exit(0)
    
    print(f"\n{'='*120}")
    print(f"STATUS REPORT: {log_dir}")
    print(f"{'='*120}\n")
    
    results = {
        'SUCCESS': [],
        'FAILED': [],
        'RUNNING': [],
        'RUNNING?': [],
        'EMPTY': [],
        'UNKNOWN': [],
        'MISSING': [],
        'ERROR': []
    }
    
    for log_file in log_files:
        status, info = check_log_status(log_file)
        results[status].append((log_file.name, info))
    
    # Print summary
    total = len(log_files)
    print(f"Total logs: {total}")
    print(f"  ✓ SUCCESS: {len(results['SUCCESS'])}")
    print(f"  ✗ FAILED:  {len(results['FAILED'])}")
    print(f"  ⟳ RUNNING: {len(results['RUNNING']) + len(results['RUNNING?'])}")
    print(f"  ? UNKNOWN: {len(results['UNKNOWN']) + len(results['EMPTY'])}")
    
    # Print details for each category
    for status in ['FAILED', 'RUNNING', 'RUNNING?', 'UNKNOWN', 'EMPTY', 'SUCCESS']:
        if results[status]:
            print(f"\n{'-'*120}")
            print(f"{status}:")
            print(f"{'-'*120}")
            for name, info in results[status]:
                # Color coding
                if status == 'SUCCESS':
                    color = '\033[92m'  # Green
                elif status == 'FAILED':
                    color = '\033[91m'  # Red
                elif status in ['RUNNING', 'RUNNING?']:
                    color = '\033[93m'  # Yellow
                else:
                    color = '\033[94m'  # Blue
                reset = '\033[0m'
                
                print(f"{color}[{status}]{reset} {name}")
                if info and status in ['FAILED', 'UNKNOWN']:
                    print(f"         → {info}")
    
    print(f"\n{'='*120}\n")
    
    # Exit code
    if results['FAILED']:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
