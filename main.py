#!/usr/bin/env python3
"""
Main entry point for NASA Mission Control integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import sys
from pathlib import Path

# Add the package to the Python path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    from uc_intg_nasa.driver import main
    import asyncio
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Integration stopped by user")
    except Exception as e:
        print(f"Integration failed: {e}")
        sys.exit(1)