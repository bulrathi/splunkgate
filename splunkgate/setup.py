#!/usr/bin/python

__author__  = "bw"
__version__ = "0.1.0"

import sys
sys.path.append("sglib") 

from cx_Freeze import setup, Executable

base = None

options = {
    'build_exe': {
        'includes': ['sg_config', 'sg_db', 'sg_esb', 'sg_alerts'],
    }
}

executables = [
    Executable('splunkgate.py', base=base)
]

setup(
  name = "SplunkGate",
  version = "0.1.0",
  description = "SplunkGate",
  options=options,
  executables=executables
)