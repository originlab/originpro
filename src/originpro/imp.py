"""
originpro
A package for interacting with Origin software via Python.
Copyright (c) 2020 OriginLab Corporation
"""
# pylint: disable=C0103
from typing import Union
from .config import po
from .project import find_sheet, _WBOOK_TYPE
from .worksheet import WSheet
from .matrix import MSheet

def get_sheet(index=0, _type=_WBOOK_TYPE) -> Union[WSheet, MSheet]:
    """
    This is for importing into multiple sheets, to get the needed sheet by index.
    For exmaple a file with multiple blocks.

    Parameters:
        index(int): sheet index in a multisheet group, 0,1,2
        type (str): Specify 'w' for WBook object or 'm' for MBook object
    Returns:
        (WSheet or MSheet or None)

    Examples:
        wks1 = op.imp.get_sheet()   #when active book that is a workbook
        wks2 = op.imp.get_sheet(1)
    """
    po.LT_execute(f'doc.ImpSheet({index})')
    ref = po.LT_get_str('__ImpSheet')
    if not ref:
        return None
    return find_sheet(_type, ref)

def prepare_range(objs_count, sheet_index=0):
    '''
    Prepare column ranges for Connector import
    Parameters:
        objs_count(int):
        sheet_index(int):
    Returns:
        the first column index in column range
    Examples:
        op.imp.prepare_range(3,0) #This function must be used with the
                                  #COConnMultipleSheetsMonitorBase class
    '''
    return int(po.LT_evaluate(f'doc.ImpPrepareRange({objs_count}, {sheet_index})'))
