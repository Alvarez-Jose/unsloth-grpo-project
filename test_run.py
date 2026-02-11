# test_run.py
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    print("Testing project imports...")
    
    # Test basic imports
    from loguru import logger
    logger.success("loguru imported successfully")
    
    # Test your modules
    try:
        from c_core.etw_monitor import SystemEvent
        logger.success("SystemEvent imported")
    except ImportError as e:
        logger.error(f"Could not import SystemEvent: {e}")
        
    try:
        from c_core.master_router import MasterRouter
        logger.success("MasterRouter imported")
    except ImportError as e:
        logger.error(f"Could not import MasterRouter: {e}")
    
    print("\n Project is ready!")
    
except Exception as e:
    print(f"\n Error: {e}")
    import traceback
    traceback.print_exc()
