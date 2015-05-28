#!/usr/bin/python

import sys
sys.path.append("sglib") 

from cx_Freeze import setup, Executable

print sys.platform

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

options = {
    'build_exe': {
        'includes': ['sgconfig', 'sglogger', 'sgdb', 'sgesb'],
    }
}

executables = [
    Executable('splunkgate.py', base=base)
]
#includes = ['ConfigParser']
#build_exe_options = {'include_files': ["sglib/sgconfig.py", "sglib/sglogger.py", "sglib/sgdb.py", "sglib/sgesb.py"]}

setup(
  name = "SplunkGate",
  version = "0.1.0",
  description = "SplunkGate",
  options=options,
  executables=executables
)