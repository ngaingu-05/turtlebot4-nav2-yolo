#!/usr/bin/env python3
"""Compatibility executable: use goals_file (yaw radians), not goals_json."""
import sys
from navigation_node import main

if __name__ == '__main__':
    sys.exit(main())
