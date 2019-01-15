import sys
from cx_Freeze import setup, Executable

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(name="BatchTINTV3",
      version="3.0",
      description="This program uses Axona's command line interface to Batch spike sort .set files within a "
      "user defined directory!",
      executables=[Executable("BatchSort.py", base=base)])
