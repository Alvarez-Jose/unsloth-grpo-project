# create check_main.py in your project root
import sys
from pathlib import Path

# Add src to path
PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

print("🔍 Checking src/main.py...")
print(f"Project root: {PROJECT_ROOT}")
print(f"Main.py path: {SRC_DIR / 'main.py'}")

# Check if file exists
if (SRC_DIR / 'main.py').exists():
    # Read and analyze the file
    with open(SRC_DIR / 'main.py', 'r') as f:
        content = f.read()
    
    print(f"\n📄 File size: {len(content)} characters")
    
    # Check for AgentOS class
    if 'class AgentOS' in content:
        print("✅ Found 'class AgentOS' in main.py")
        
        # Find the line number
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'class AgentOS' in line:
                print(f"\n📝 AgentOS class definition (line {i+1}):")
                # Show context
                for j in range(max(0, i-2), min(len(lines), i+5)):
                    prefix = ">>> " if j == i else "    "
                    print(f"{prefix}{lines[j]}")
                break
    else:
        print("❌ 'class AgentOS' NOT FOUND in main.py")
        print("\n📄 First 20 lines of main.py:")
        for i, line in enumerate(content.split('\n')[:20]):
            print(f"   {i+1:3d}: {line}")
        
        print("\n📄 Last 20 lines of main.py:")
        for i, line in enumerate(content.split('\n')[-20:]):
            print(f"   {len(content.split('\n'))-20+i+1:3d}: {line}")
else:
    print("❌ main.py does not exist in src/ directory!")
    
    print("\n📁 Contents of src/ directory:")
    for item in SRC_DIR.iterdir():
        print(f"   - {item.name}")