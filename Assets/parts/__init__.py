# Assets/parts/__init__.py
import importlib, pkgutil, sys

package = sys.modules[__name__]

for loader, name, ispkg in pkgutil.walk_packages(__path__, __name__ + "."):
    importlib.import_module(name)