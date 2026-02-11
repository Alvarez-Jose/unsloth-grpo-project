Write-Host "=== Project Cortex Installation Verification ===" -ForegroundColor Cyan

# Check Python environment
Write-Host "`n1. Python Environment:" -ForegroundColor Yellow
python -c "
import sys
import os
print('  Executable:', sys.executable)
print('  Prefix:', sys.prefix)
print('  Base prefix:', sys.base_prefix)
print('  Venv active:', sys.prefix != sys.base_prefix)
print('  VIRTUAL_ENV:', os.environ.get('VIRTUAL_ENV', 'Not set'))
"

# Check pip
Write-Host "`n2. Pip Location:" -ForegroundColor Yellow
pip --version

# Check installed packages
Write-Host "`n3. Installed Packages:" -ForegroundColor Yellow
python -c "
import pkg_resources
packages = ['loguru', 'psutil', 'watchdog', 'your_project']
for pkg in packages:
    try:
        dist = pkg_resources.get_distribution(pkg)
        location = dist.location
        status = '✓' if 'venv' in location else '⚠'
        print(f'  {status} {pkg}: {dist.version} ({location})')
    except:
        print(f'  ✗ {pkg}: Not installed')
"

# Test imports
Write-Host "`n4. Testing Imports:" -ForegroundColor Yellow
$testScript = @'
import sys
from pathlib import Path

# Add project to path
project_root = Path('.').resolve()
sys.path.insert(0, str(project_root))

imports_to_test = [
    ('loguru', 'logger'),
    ('psutil', 'Process'),
    ('watchdog.observers', 'Observer'),
]

all_ok = True
for module, item in imports_to_test:
    try:
        __import__(module)
        print(f'  ✓ {module}')
    except ImportError as e:
        print(f'  ✗ {module}: {e}')
        all_ok = False

# Try project imports
try:
    from c_core.etw_monitor import SystemEvent
    print('  ✓ c_core.etw_monitor')
except ImportError as e:
    print(f'  ✗ c_core.etw_monitor: {e}')
    all_ok = False

print(f'\n  Overall: {"SUCCESS" if all_ok else "FAILED"}')
'@

python -c $testScript

Write-Host "`n=== Verification Complete ===" -ForegroundColor Green