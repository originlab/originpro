"""
originpro
A package for interacting with Origin software via Python.
Copyright (c) 2020 OriginLab Corporation
"""
# pylint: disable=C0103
from .config import po
from .utils import lt_tree_to_dict, lt_dict_to_tree, lt_delete_tree

class Connector:
    r'''
    Data Connector
        Parameters:
            wks (DSheet): the worksheet or martix sheet to use the connector
            dctype(str):  Name of the connector, CSV, Excel etc
            keep_DC(bool): Keep the connector after import
        Example:
            import originpro as op
            f = op.path('e')+r'Samples\Import and Export\S15-125-03.dat'
            wks = op.find_sheet()
            dc = op.Connector(wks)
            ss = dc.settings()
            partial = ss['partial']
            partial[op.attrib_key('Use')]='1'
            partial['row']='10:20'
            dc.imp(f)
    '''
    def __init__(self, wks, dctype = '', keep_DC=True):
        self.keep = keep_DC
        self.wks=wks
        currentDC = self.wks.has_DC()
        if not dctype:
            dctype = currentDC if currentDC else 'csv'
        self.dc = dctype.lower()
        if currentDC and currentDC != self.dc:
            self.wks.remove_DC()
            currentDC = ''
        if not currentDC:
            self.wks.obj.DoMethod('DC.Allow', '2') #this will reset old import info in the book
            self.wks.lt_exec(f'wbook.dc.add({self.dc})')
        self._trLTname = '_trTmpDCSettings'
        self._trOptn = None

    def __del__(self):
        if not self.keep:
            self.wks.remove_DC()

    def settings(self):
        '''
        Parameters:
            none
        Returns:
            Import settings
        Examples:
            wks=op.find_sheet()
            dc=op.Connector(wks)
            ss=dc.settings()
        '''
        return self._optn()['Settings']

    @property
    def source(self):
        """
        Property getter returns the source of Data Connector
        Parameters:
            none
        Returns:
            (str) Data Source
        Examples:
            wks=op.find_sheet()
            dc=op.Connector(wks)
            print(dc.source)
        """
        return self.wks.get_str('DC.Source')
    @source.setter
    def source(self, s):
        r"""
        Property setter set the source of Data Connector
        Parameters:
            s(str): Data Source
        Returns:
            None
        Examples:
            wks=op.find_sheet()
            dc=op.Connector(wks)
            dc.source=op.path('e')+r'Samples\Import and Export\S15-125-03.dat'
            dc.imp()
        """
        self.wks.set_str('DC.Source', s)

    def new_sheet(self, name):
        """
            Import a new selection into a new sheet

        Parameters:
            name(str): selection, for example an Excel sheet name

        Returns:
            None
        Examples:
            dc.imp(f, sel='Oil')
            dc.new_sheet('Natural Gas')
        """
        self.wks.lt_exec(f'wbook.dc.newsheet({name})')

    def _optn(self):
        if not self._trOptn:
            self.wks.lt_exec(f'tree {self._trLTname} = wks.dc.optn$')
            self._trOptn = lt_tree_to_dict(self._trLTname)
            lt_delete_tree(self._trLTname)
        return self._trOptn

    def imp(self, fname='', sel='', sparks=False):
        r'''
        Import file
        Parameters:
            fname(string): source file name
            sel(string):selection
        Returns:
            none
        Examples:
            wks=op.find_sheet()
            dc=op.Connector(wks)
            f=op.path('e')+r'Samples\Import and Export\ASCII Simple.dat'
            dc.imp(f)

        '''
        optn = self._trOptn
        if optn:
            lt_dict_to_tree(optn, self._trLTname, True, True)
            self.wks.lt_exec(f'{self._trLTname}.tostring(wks.dc.optn$)')
            lt_delete_tree(self._trLTname)
        if fname:
            self.source = fname
        #Import Filter Connector need to do wks.dc.Import(1) in order to find the OIF filter
        imp_arg = '1' if self.dc=='Import Filter' else ''
        if sel:
            self.wks.set_str('DC.Sel', sel)
            imp_arg = ''
        oldspark=int(po.LT_get_var('@IMPS'))
        newspark = 1 if sparks else 0
        po.LT_set_var("@IMPS", newspark)
        self.wks.method_int('dc.import', imp_arg)
        po.LT_set_var("@IMPS", oldspark)
