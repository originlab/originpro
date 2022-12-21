"""
originpro
A package for interacting with Origin software via Python.
Copyright (c) 2020 OriginLab Corporation
"""
# pylint: disable=C0103,W0611
oext = False
_EXIT = [False]
_OBJS_COUNT = [0]
try:
    import PyOrigin as po
except ImportError:
    import OriginExt
    import atexit
    class APP:
        'OriginExt.Application() wrapper'
        def __init__(self):
            self._app = None
            self._first = True
        def __getattr__(self, name):
            try:
                return getattr(OriginExt, name)
            except AttributeError:
                pass
            if self._app is None:
                self._app = OriginExt.Application()
            return getattr(self._app, name)
        def Exit(self, releaseonly=False):
            'Exit if Application exists'
            if self._app is not None:
                self._app.Exit(releaseonly)
                self._app = None
        def Attach(self):
            'Attach to exising Origin instance'
            releaseonly = True
            if self._first:
                releaseonly = False
                self._first = False
            self.Exit(releaseonly)
            self._app = OriginExt.ApplicationSI()
        def Detach(self):
            'Detach from Origin instance'
            self.Exit(True)
    po = APP()
    oext = True
    def _exit_handler():
        global _EXIT, _OBJS_COUNT
        _EXIT[0] = True
        if not _OBJS_COUNT[0]:
            po.Detach()
    atexit.register(_exit_handler)

import warnings
if po.LT_get_var('@V') < 10.05:
    warnings.simplefilter(action='ignore', category=FutureWarning)

try:
    import numpy as np
    npdtype_to_orgdtype = {
        np.float64: po.DF_DOUBLE,
        np.float32: po.DF_FLOAT,
        np.int16: po.DF_SHORT,
        np.int32: po.DF_LONG,
        np.int8: po.DF_CHAR,
        np.uint8: po.DF_BYTE,
        np.uint16: po.DF_USHORT,
        np.uint32: po.DF_ULONG,
        np.complex128: po.DF_COMPLEX,
    }
    orgdtype_to_npdtype = {v: k for k, v in npdtype_to_orgdtype.items()}
except ImportError:
    pass
