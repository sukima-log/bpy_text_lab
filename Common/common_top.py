#------------------------------------------------------------------
# = Define (環境毎に変更)
#------------------------------------------------------------------
# Extensions Download Dir
__addon_directory = "C:/Users/..."
#------------------------------------------------------------------
# = Import
#------------------------------------------------------------------
import bpy
import math
import random
import numpy as np
from mathutils import Matrix, Vector
import mathutils
import os
import sys
import bmesh
import requests
import urllib.request
import zipfile
import importlib
import time
import json
import pkgutil
import subprocess
from itertools import combinations
from collections import Counter
from collections import deque, defaultdict

#------------------------------------------------------------------
# = Set Path
#------------------------------------------------------------------
# Get File Path
script_path = bpy.path.abspath(bpy.context.space_data.text.filepath)
script_dir = os.path.dirname(script_path)
# Get Git Root
git_root = subprocess.run(
    ["git", "-C", script_dir, "rev-parse", "--show-toplevel"],
    stdout=subprocess.PIPE, text=True
).stdout.strip()
# Add the parent directory of the root to sys.path
if git_root and git_root not in sys.path:
    sys.path.append(git_root)

import Mylib
# Common Lib
from Mylib import *
from Assets.parts import *
from Assets.parts import model
from Assets.parts import material

