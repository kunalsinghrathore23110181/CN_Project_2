#!/usr/bin/env python3
"""Compatibility entry point: runs non-overwriting VM single-flow sessions.

The previous 50-run script is preserved as single_flow_legacy.py for reference.
Use --runs 50 to repeat 50 measurements; default is five runs.
"""
from run_vm import main

if __name__ == '__main__':
    main()
