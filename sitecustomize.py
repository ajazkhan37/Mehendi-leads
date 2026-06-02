"""Compatibility shim for Python 3.14.

Some dependencies (or their internal dependencies) still reference `ast.Str`,
which was removed in Python 3.14.

Python automatically imports `sitecustomize` (if importable) on startup,
so placing this file at the project root ensures it runs for gunicorn.
"""

import ast

# Python 3.14 removes ast.Str; map it to ast.Constant for compatibility.
if not hasattr(ast, "Str") and hasattr(ast, "Constant"):
    ast.Str = ast.Constant

