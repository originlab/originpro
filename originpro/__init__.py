"""
originpro
A package for interacting with Origin software via Python.
Copyright (c) 2020 OriginLab Corporation
"""
# pylint: disable=W0622
from os.path import dirname, basename, isfile, join
import glob
from .config import *
from .project import *
from .worksheet import *
from .matrix import *
from .graph import *
from .utils import *
from .analysis import *
from . import imp
from . import pe
from .pe import Folder, active_folder, root_folder
from .dc import Connector

modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
