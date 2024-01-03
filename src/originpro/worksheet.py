"""
originpro
A package for interacting with Origin software via Python.
Copyright (c) 2020, 2021, 2022 OriginLab Corporation
"""
# pylint: disable=C0301,C0103,W0622,R0912,R0904,R0913,R0914,R0915,C0302
import os
from collections import abc
from datetime import datetime as dt, timedelta as tdlt, date, time
from .config import po, oext
from .base import DSheet, DBook
from .utils import org_ver

try:
    import pandas as pd
except ImportError:
    pass

def _origin_date_offset(to_df):
    # Harvey 03/04/2021 ORG-22488-P6 WORKSHEET_PY_DATA_OFFSET_SUPPORT_DSP_IS_2018
    #nJD = int(po.LT_get_var('@DSP'))
    #if nJD == 1:#True Julian Days
    #    return 0
    #if nJD == 0:#Origin's current default
    #    return 0.5 if to_df else -0.5
    #raise ValueError('@DSP with value not yet implemented')
    nD = 2415018.5 - po.LT_get_var('@DSO')
    return nD if to_df else -nD
    # END WORKSHEET_PY_DATA_OFFSET_SUPPORT_DSP_IS_2018

def _series_to_julian_date(s):
    offset = _origin_date_offset(False)
    # Must check that vv is not NaN or NaT (VC handles NaT correctly via _OPyIsNaT):
    return [vv if pd.isnull(vv) else vv.to_julian_date() + offset for vv in s]

def _series_to_time(s):
    # See https://pandas.pydata.org/pandas-docs/stable/user_guide/timedeltas.html
    # under "Frequency conversion"
    # Here need to convert it to number of days as float64:
    #listtoset = [vv/np.timedelta64(1, 'D') for vv in value]
    # See https://docs.python.org/2/library/datetime.html
    # under 8.1.2. timedelta Objects
    # In Origin Time column contains numeric floating values which represent fractions of one day.
    return [vv/tdlt(days=1) for vv in s]

def _check_convert_py_time_to_tdlt(s):
    if not s.empty:
        if isinstance(s.iloc[0], time):
            return [dt.combine(date.min, vv) - dt.min for vv in s]
    return s


class WSheet(DSheet):
    """
    This class represents an Origin Worksheet, it holds an instance of a PyOrigin Worksheet.
    """
    # Adds a maximum of needecols columns beginning with c1 to
    # Origin worksheet wks:
    def _check_add_cols(self, needecols, c1 = 0):
        if self.obj.Cols < needecols + c1:
            self.obj.Cols = c1 + needecols
    @staticmethod
    def _set_col_LN(colobj, key, col):
        if isinstance(key, int) and key == col:
            return
        colobj.LongName = str(key)
    @staticmethod
    def _isParam(name, prefix):
        if name[0] == prefix:
            try:
                return int(name[1:]) - 1
            except ValueError:
                pass
        return -1
    @staticmethod
    def _getlabel(colobj, type):
        if isinstance(type, int):
            if type < 0 or type > 15:
                raise ValueError('Invalid index to user parameter')
            return colobj.GetUserDefLabel(type)
        index = WSheet._isParam(type, 'P')
        if index >= 0:
            return colobj.GetParameter(index)
        try:
            dd = {
                'L': colobj.GetLongName,
                'C': colobj.GetComments,
                'U': colobj.GetUnits,
                'G': colobj.GetName,
                }
            func = dd[type]
            return func()
        except KeyError as e:
            raise ValueError('Invalid label row character') from e
    @staticmethod
    def _setlabel(colobj, type, val):
        """type is int if user parameter row, or 'L', 'C', 'U' etc, see _col_label_row()"""
        if isinstance(type, int):
            if type < 0 or type > 15:
                raise ValueError('Invalid index to user parameter')
            return colobj.SetUserDefLabel(type, str(val))
        index = WSheet._isParam(type, 'P')
        if index >= 0:
            return colobj.SetParameter(index, str(val))
        if len(type) > 1:
            raise ValueError('Invalid label row character')
        try:
            dd = {
                'L': colobj.SetLongName,
                'C': colobj.SetComments,
                'U': colobj.SetUnits,
                'G': colobj.SetName,
                }
            func = dd[type]
            return func(str(val))
        except KeyError as e:
            raise ValueError('Invalid label row character') from e

    @staticmethod
    def _cname(colobj, type):
        try:
            return WSheet._getlabel(colobj, type)
        except ValueError:
            pass
        lname = colobj.LongName
        if lname:
            return lname
        return colobj.GetName()

    @staticmethod
    def _cgetdata(colobj, nStart=0, nEnd=-1):
        if oext:
            return colobj.GetData(9999, nStart, nEnd)
        return colobj.GetData(nStart, nEnd)

    def _col_label_row(self, head=''):
        """return int if user parameter row, or 'L', 'C', 'U' etc """
        if len(head) == 0:
            return 'L'
        if not isinstance(head, str):
            raise ValueError('must specify a str')
        if len(head) == 1:
            return head
        return self._user_param_row(head, True)

    def _user_param_row(self, name, add=False):
        """find user defined parameter row index from name, if add, then add it if not existed"""
        ltarg= '++' if add else ''
        ltarg += name
        return self.method_int('UserParam', ltarg)-1

    def _col_index(self, col, convert_negative=False):
        if isinstance(col,int):
            if convert_negative and col < 0:
                return col + self.cols
            return col
        cobj = self.obj.FindCol(col)
        if cobj is None:
            return -1
        return cobj.GetIndex()

    def _find_col(self, col):
        if not isinstance(col, int):
            obj = self.obj.FindCol(col)
            if obj is None:
                return None
            col = obj.GetIndex()
        return self.obj[col]

    @property
    def rows(self):
        """
        Get the last row index in worksheet with data, hidden rows has no effect on this
        This is different from shape[0] which does not care of having data or not
        Parameters:

        Returns:
            the last row index in worksheet with data
        Examples:
            wks=op.find_sheet()
            nrows = wks.rows
        """
        return self.get_int('maxrows')

    @property
    def cols(self):
        """
        get the last column index in worksheet, this is the same as shape[1]
        Parameters:

        Returns:
            get the last column index in worksheet
        Examples:
            wks=op.find_sheet()
            ncols = wks.cols
        """
        return self.obj.Cols

    @cols.setter
    def cols(self, val):
        """
        set the number of columns in worksheet
        Parameters:
            val(int):number of columns
        Returns:
            the last column index in worksheet
        Examples:
            wks=op.find_sheet()
            wks.cols=5
        """
        self.obj.Cols = val
        return self.cols

    def get_book(self):
        """
        Returns parent book of sheet.

        Parameters:

        Returns:
            (WBook)

        Examples:
            wks2 = wks.get_book().add_sheet('Result')
        """
        return WBook(self._get_book())

    def lt_col_index(self, col, convert_negative=False):
        """
        convert a 0-offset index to LabTalk index which is 1-offset

        Parameters:
            col (int or str): If int, column index. If str, tries short name and if not exists, tries column long name, <0 supported as from the end

        Return:
            (int) 1-offset column index

        Examples:
            ii = wks.lt_col_index('Intensity')
            if ii < 1:
                print('no such column')
        """
        return self._col_index(col, convert_negative) + 1

    def from_df(self, df, c1=0, addindex=False, head=''):
        r"""
        Sets a pandas DataFrame to an Origin worksheet.

        Parameters:
            df (DataFrame): Input DataFrame object
            c1 (int or str): Starting column index
            addindex (bool): add an index column at c1 if df has text indices
            head(str): if not specified, column longname is used if df has column names,
                head can be one of the Column Label Row character like 'L', 'C', or a user parameter by its name

        Returns:
            None

        Examples:
            wks=op.find_sheet()
            my_df = pd.DataFrame({'aa':[1,2,3], 'bb':[4,5,6]})
            wks.from_df(my_df)

            import pandas as pd
            fname = op.path('e') + "Samples\\Import and Export\donations.csv"
            df = pd.read_csv(fname)
            wks.from_df(df,'B')
        """
        c1 = self._col_index(c1)
        if c1 < 0:    # caller's mistake
            raise ValueError('c1 must not be <0')

        if df.empty:
            return
        head_row = self._col_label_row(head)
        ndfcols = len(df.columns)
        #print(str(type(df.index)))
        if addindex:
            # Find out if index is not default (0, 1, 2,...)
            addindex = list(range(len(df.index))) != list(df.index)

        colstohave = ndfcols
        colBeginData = c1
        if addindex:
            colstohave += 1
            colBeginData += 1

        self._check_add_cols(colstohave, c1)
        if addindex:
            # c1 should receive the index
            self.obj[c1].SetData(df.index)

        bSetColumnAsMixedInGeneralCase = int(po.LT_get_var('@DFSM')) > 0    # ML 06/26/2020 ORG-21995-P2 FROM_DF_DONT_SET_TEXT_AND_NUMERIC_FOR_GENERAL_CASE_BY_DEFAULT

        col = colBeginData
        for key, value in df.items():
            colobj = self.obj[col]
            if str(value.dtype) == 'category':
                dfseriestypechar = 'cat'        # our own "name" for convenience
            else:
                #dfseriestypechar = df.dtypes[col - colBeginData].char
                dfseriestypechar = value.dtype.char
            #print(dfseriestypechar)
            #print(value)
            displayFmt = -1
            if dfseriestypechar == 'O':
                v1 = _check_convert_py_time_to_tdlt(value)
                if v1 is not value:
                    value = v1
                    dfseriestypechar = 'm'
                    displayFmt = 2
            if dfseriestypechar == 'd':    # if floating:
                colobj.SetDataFormat(po.DF_DOUBLE)
                listtoset = list(value)
            elif dfseriestypechar == 'q':    # if integer
                colobj.SetDataFormat(po.DF_LONG)
                listtoset = list(value)
            elif dfseriestypechar == 'D':    # if complex:
                colobj.SetDataFormat(po.DF_COMPLEX)
                listtoset = list(value)
            elif dfseriestypechar == 'M':    # if datetime64[ns]:
                colobj.SetDataFormat(po.DF_DATE)
                listtoset = _series_to_julian_date(value)
            elif dfseriestypechar == 'm':    # if 'timedelta':
                colobj.SetDataFormat(po.DF_TIME)
                listtoset = _series_to_time(value)
            elif dfseriestypechar == 'cat':    # if categorical
                colobj.SetDataFormat(po.DF_TEXT)
                listtoset = list(value)
            else:
                # ML 06/26/2020 ORG-21995-P2 FROM_DF_DONT_SET_TEXT_AND_NUMERIC_FOR_GENERAL_CASE_BY_DEFAULT
                # colobj.SetDataFormat(po.DF_TEXT_NUMERIC)
                if bSetColumnAsMixedInGeneralCase:
                    colobj.SetDataFormat(po.DF_TEXT_NUMERIC)
                # end FROM_DF_DONT_SET_TEXT_AND_NUMERIC_FOR_GENERAL_CASE_BY_DEFAULT
                listtoset = list(value)

            colobj.SetData(listtoset)
            if dfseriestypechar == 'cat':    # if categorical
                #if value.cat.ordered:
                #    colobj.SetCategMapSortCategories(po.CM_SORTING_ASCENDING, [])
                #else:
                # Per sam's request we always do custom:
                colobj.SetCategMapSortCategories(po.CM_SORTING_CUSTOM, [str(v) for v in value.cat.categories])
            elif displayFmt >= 0:
                colobj.SetDisplayFormat(displayFmt)
            if isinstance(key, str) and key.startswith('Unnamed:'):
                key = ''
            if len(head) == 0:
                self._set_col_LN(colobj, key, col)
            else:
                self._setlabel(colobj, head_row, key)
            col += 1

    def to_df(self, c1=0, numcols = -1, cindex = -1, head=''):
        """
        Creates a pandas DataFrame from an Origin worksheet.

        Parameters:
            c1 (int or str): column to start the export
            numcols (int): Total number of columns, -1 to the end
            cindex (int or str): Column to use for DataFrame index if specified
            head (str): user parameter or built-in label row name, if not specified, lname(column long name), or short name if lname empty or duplicated
        Returns:
            (DataFrame)

        Examples:
            df = wks.to_df(2)#from 3rd column

            #use col(A) as index, and B and C as data
            df1 = wks.to_df('B', 2, 'A')

            #to use a user defined label row as column heading
            df2 = wks.to_df(head='Tag')
        """
        c1 = self._col_index(c1)
        if c1 < 0:    # caller's mistake
            raise ValueError('c1 must not be <0')
        cindex = self._col_index(cindex)
        if self.obj.Cols <= cindex:    # invalid index column
            raise ValueError('cindex outside of number of columns')
        lns = set()
        cname=-1
        if head:
            row = self._col_label_row(head)
            if isinstance(row, int) and row < 0:
                raise ValueError(f'user parameter row {head} not found')
            cname = row

        df = pd.DataFrame()
        if numcols < 0:
            totalcols = self.obj.Cols - c1
        else:
            totalcols = min(self.obj.Cols - c1, numcols)

        _, r2 = self.obj.GetBounds(c1, c1 + totalcols - 1)

        dd = {}
        for col in range(c1, c1 + totalcols):
            colobj = self.obj[col]
            coldata = self._cgetdata(colobj)
            coldatatype = colobj.GetDataFormat()
            if coldatatype == po.DF_DATE:
                offset = _origin_date_offset(True)
                coldata = [xx + offset for xx in coldata]
                # See https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Timestamp.html
                listtimestamps = pd.to_datetime(coldata, unit='D', origin='julian')
                dfseries = pd.Series(listtimestamps, list(range(len(listtimestamps))))
            elif coldatatype == po.DF_TIME:
                # See https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.to_timedelta.html
                listtimedeltas = pd.to_timedelta(coldata, unit='d')
                dfseries = pd.Series(listtimedeltas, list(range(len(listtimedeltas))))
            elif colobj.CategMapType != po.CMTYPE_NONE:
                sort = colobj.CategMapSort
                if sort == po.CM_SORTING_ASCENDING:
                    # if ascending, just set the Categorical property "ordered" to True:
                    dfseries = pd.Categorical(coldata, ordered=True)
                #elif sort == po.CM_SORTING_UNSORTED:
                #    dfseries = pd.Series(coldata, list(range(len(coldata))), dtype="category")
                else:
                    # For all the other cases get the categories array from the columns and set it into df:
                    categories = colobj.CategMapCategories
                    dfseries = pd.Categorical(coldata, categories)
                dfseries = pd.Series(dfseries)

            else:
                cnt = r2 + 1 - len(coldata)
                if cnt > 0:
                    coldata += [float('nan')] * cnt
                dfseries = pd.Series(coldata, list(range(len(coldata))), dtype=None if coldata else 'object')
            #loc = col - c1
            ## ML 06/25/2020 ORG-21995-P1 APPEND_EMPTY_ROWS_BEFORE_LONGER_SERIES_TO_ADD
            ## https://stackoverflow.com/questions/39998262/append-an-empty-row-in-dataframe-using-pandas
            ## If the series being added is longer than the current size, must append with empty rows first
            #lengthseries = len(dfseries)
            #if len(df.index) > 0 and len(df.index) < lengthseries:
                #for _ in range(len(df.index), lengthseries):
                    #df = df.append(pd.Series(), ignore_index = True)
            ## end APPEND_EMPTY_ROWS_BEFORE_LONGER_SERIES_TO_ADD
            #df.insert(loc, self._cname(colobj, cname), dfseries)
            cname2 = cname
            if not head:
                ln = colobj.LongName
                if ln:
                    if ln in lns:
                        cname2 = 'G'
                    else:
                        lns.add(ln)
            dd[self._cname(colobj, cname2)] = dfseries
        df = pd.concat(dd, axis=1)

        if cindex >= 0:
            colobj = self.obj[cindex]
            df.index = self._cgetdata(colobj)


        return df

    def to_list(self, col):
        """
        Creates a list object from the data in an Origin column.

        Parameters:
            col (int or str): If int, column index. If str, tries short name and if not exists, tries column long name

        Returns:
            (list)

        Examples:
            data1 = wks.to_list(1)
            data2 = wks.to_list('Intensity')
        """
        ncol = self._col_index(col)
        if ncol < 0 or ncol >= self.obj.Cols:
            return []
        return self._cgetdata(self.obj[ncol])

    def from_list(self, col, data, lname='', units='', comments='', axis='', start=0):
        """
        Sets a list object into an Origin column, optionally specifying long name, units ,comments label row values.

        Parameters:
            col (int or str): If int, column index. If str, tries short name and if not exists, tries column long name
            data (list): data to put into column
            lname (str): Optional column long name
            units (str): Optional column units
            comments (str): Optional column comments
            axis (str): empty will not set, otherwise set column designation for plotting,
                        can be X,Y,Z, or N(None), E(Yerr), M(Xerr), L(label)
                        see https://www.originlab.com/doc/Origin-Help/WksCol-SetDesignation
            start(int): row offset
        Returns:
            None

        Examples:
            data = [1,2,3,4,5]
            wks.from_list(1, data)
            wks.from_list('Intensity', data, units='a. u.', axis='Y')
            wks.from_list(0, data, start=2)
        """
        ncol = self._col_index(col)
        if ncol < 0:
            raise ValueError('Column does not exist')
        if ncol >= self.obj.Cols:
            self.obj.Cols = ncol + 1
        self.obj[ncol].SetData(data, start)
        if lname:
            self.obj[ncol].SetLongName(lname)
        if units:
            self.obj[ncol].SetUnits(units)
        if comments:
            self.obj[ncol].SetComments(comments)
        if axis:
            if len(axis) > 1:
                raise ValueError('axis type must be a single letter')
            if axis not in list('XYZNEML'):
                raise ValueError('Invalid axis type letter')
            self.obj.SetColDesignations(axis, 0, ncol, ncol)

    def get_label(self, col, type = 'L'):
        """
        Return a column label row text.

        Parameters:
            col (int or str): If int, column index. If str, tries short name and if not exists, tries column long name
            type (str): A column label row character (see https://www.originlab.com/doc/LabTalk/ref/Column-Label-Row-Characters) or a user defined parameter name

        Returns:
            (str)

        Examples:
            wks=op.find_sheet()
            comments = wks.get_label(1,'C')
        """
        ncol = self._col_index(col)
        if ncol < 0:
            raise ValueError('Column does not exist')
        colobj = self.obj[ncol]
        if not isinstance(type, int):
            try:
                return self._getlabel(colobj, type)
            except ValueError:
                pass
            type = self._user_param_row(type)
            if type < 0:
                return '' # not found
        return self._getlabel(colobj, type)

    def set_label(self, col, val, type = 'L'):
        """
        Set a column label row text.

        Parameters:
            col (int or str): If int, column index. If str, tries short name and if not exists, tries column long name
            val (str): the text to set
            type (str): A column label row character (see https://www.originlab.com/doc/LabTalk/ref/Column-Label-Row-Characters) or a user defined parameter name

        Examples:
            wks=op.find_sheet()
            wks.set_label('A','long name for col A')
            wks.set_label(1, 'for col B, add user parameter if not there', 'Channel')
        """

        if isinstance(type,int) or len(type)==0:
            raise ValueError('type cannot be integers or empty')

        ncol = self._col_index(col)
        if ncol < 0:
            raise ValueError('Column does not exist')
        colobj = self.obj[ncol]
        if not isinstance(type, int):
            try:
                return self._setlabel(colobj, type, val)
            except ValueError:
                pass
            type = self._user_param_row(type, True)
        return self._setlabel(colobj, type, val)

    def get_labels(self, type_ = 'L'):
        '''
        Return columns label row text.

        Parameters:
            type_ (str): A column label row character (see https://www.originlab.com/doc/LabTalk/ref/Column-Label-Row-Characters) or a user defined parameter name

        Returns:
            (list)

        Examples:
            wks=op.find_sheet()
            comments = wks.get_labels('C')
        '''
        return [self.get_label(col, type_) for col in range(self.cols)]

    def set_labels(self, labels, type_ = 'L', offset=0):
        """
        Set columns label row text.

        Parameters:
            labels (list): the text to set
            type_ (str): A column label row character (see https://www.originlab.com/doc/LabTalk/ref/Column-Label-Row-Characters) or a user defined parameter name

        Examples:
            wks=op.find_sheet()
            wks.set_labels(['long name for col A', 'long name for col B'], 'L')
        """
        for ii, val in enumerate(labels[:self.cols]):
            self.set_label(ii + offset, val, type_)

    def from_dict(self, data, col=0, row=0):
        """
        Set a dictionary into a Worksheet. Keys are not used for any purpose.

        Parameters:
            data (dict): The data to set
            col (int or str): If int, column index. If str, tries short name and if not exists, tries column long name
            row (int): Row index to start setting the data

        Returns:
            None

        Examples:
            data ={'aa': [1,2,3], 'bb':[4,5,6]}
            wks.from_dict(data)
            wks.from_dict(data,'C')
        """
        col = self._col_index(col)
        self.obj.SetData(data, row, col)

    def header_rows(self, spec=''):
        """
        Controls which worksheet label rows to show, same as LabTalk wks.labels string.

        Parameters:
            spec (str): A combination of letters. See https://www.originlab.com/doc/LabTalk/ref/Column-Label-Row-Characters

        Returns:
            None

        Examples:
            wks.header_rows('lu')# Show only long-name and unit.
            wks.header_rows()# Remove all label rows, keep only heading.
        """
        if len(spec)==0:
            Specs = '0'
        else:
            Specs = spec.upper()
        getattr(self.obj, 'Labels' if oext else 'ShowLabels')(Specs)

    def cols_axis(self, spec='', c1 = 0, c2 = -1, repeat=True):
        """
        Set column plotting designations with a string pattern.

        Parameters:
            spec (str): A combination of 'x', 'y', 'z', etc letters
            c1 (int or str): Starting column to set
            c2 (int or str): Last column to set. c2 < 0 sets to last column
            repeat (bool): Repeat the last designation letter or not

        Returns:
            None

        Examples:
            wks.cols_axis('nxy') # 1st col none, 2nd=x, others=y.
            wks.cols_axis() # Clear designations from all columns.
        """
        c1 = self._col_index(c1)
        c2 = self._col_index(c2)
        if len(spec)==0:
            Specs = 'N'
        else:
            Specs = spec.upper()
        self.obj.SetColDesignations(Specs, repeat, c1, c2)

    def del_col(self, c1, nc=1):
        """
        Delete worksheet columns

        Parameters:
            c1 (int or str): Starting column to delete, <0 supported as from the end
            nc (int):      Number of columns to delete starting from c1
        Examples:
            wks.del_col(0)# del col A
            wks.del_col('C', 2)#del col C and D
        """
        c1 = self.lt_col_index(c1, True)
        c2 = c1 + nc - 1
        if c2 > self.cols:
            c2 = self.cols
        rr1 = f'({c1})' if nc==1 else f'({c1}:{c2})'
        vname = 'TMP_COL_RANGE_FOR_DEL'
        self.lt_exec(f'range {vname}={rr1};del {vname};del -al {vname}')

    def clear(self, c1 = 0, ncols = 0, c2 = -1):
        """
        Clear data in worksheet

        Parameters:
            c1 (int or str): starting col, if int, column index. If str, column name, short name first, then long name.
            ncols(int): number of columns to clear if > 0, cannot specify togeher with c2
            c2 (int or str): ending col, if int, column index. If str, column name, short name first, then long name.

        Returns:
            (int): 0 for success, otherwise an internal error code

        Examples:
            wks.clear()#clear all
            wks.clear(1)#clear from 2nd column to the end
            wks.clear(1,2)#clear from 2nd and 3rd
        """
        n1 = self.lt_col_index(c1)
        n2 = self.lt_col_index(c2)
        if ncols > 0:
            if n2 > 0:
                raise ValueError('should not specify both ncols and c2')
            n2 = n1 + ncols-1

        return self.method_int('clear', f'{n1},{n2}')

    def sort(self, col, dec = False):
        """
        Sort worksheet data by a specified column

        Parameters:
            col (int or str): If int, column index (1-offset). If str, column name, short name first, then long name.
            dec (bool): Ascending(False) or Descending(True)

        Returns:
            (int): 0 for success, otherwise an internal error code

        Examples:
            wks.sort('A')#sort using 1st col, ascending
            wks.sort(0, True)#sort using 1st col, descending
        """
        #we need LT col index for this
        ncol = self.lt_col_index(col)
        ndec = 1 if dec else 0
        return self.method_int('sort', f'{ncol},{ndec}')

    def to_list2(self, r1=0, r2=-1, c1=0, c2=-1):
        """
        get a block of cells as a list of lists

        Parameters:
            r1 (int): beginning row index
            r2 (int): ending row index (inclusive), -1 to the end
            c1 (int): beginning column index
            c2 (int): ending column index (inclusive), -1 to the end

        Returns:
            (list) list of lists of results

        Examples:
            #copy 1st row and append to last row
            ll = wks.to_list2(0,0)
            wks.from_list2(ll,wks.rows)
        """
        nrow, ncol = self.shape

        if c2 < 0:
            c2 = ncol - 1
        if r2 < 0:
            r2 = nrow - 1

        if c1 > c2:
            raise ValueError('c1 should be less than c2')

        if r1 > r2:
            raise ValueError('r1 should be less than r2')

        if c1 < 0 or c2 >= ncol or r1 < 0 or r2 >= nrow:
            raise ValueError('coloumn and row index must be within worksheet')

        return self.obj.GetData(r1, c1, r2, c2)

    def from_list2(self, data, row=0, col=0):
        """
        set a block of cells

        Parameters:
            data (list): a list of lists of values
            row (int): starting row index
            col (int or str): starting col, by index of by name

        Returns:
            (None)

        Examples:
            wks=op.find_sheet()
            #append a row to worksheet
            data = [ [10], [40] ]
            wks.from_list2(data, wks.rows)
        See Also:
            to_list2
        """
        def is_seq(d):
            return isinstance(d, abc.Sequence)
        if oext and is_seq(data):
            if not is_seq(data[0]):
                data = [[d] for d in data]
        ncol = self._col_index(col)
        self.obj.SetData(data, row, ncol)

    def _as_datetime(self, dt_, customfmt, col, fmt):
        colobj = self._find_col(col)
        colobj.SetDataFormat(dt_)
        if isinstance(fmt, int):
            colobj.SetDisplayFormat(fmt)
        else:
            colobj.SetDisplayFormat(customfmt)
            colobj.SetCustomDisplay(fmt)

    def as_date(self, col, fmt):
        """
        set col as date format

        Parameters:
            col (int or str): If int, column index. If str, column name, short name first, then long name.
            fmt (int or str): can be custom format string, or date display option as int

        Returns:
            (None)

        Examples:
            wks=op.find_sheet()
            data = [1,2,3,4,5,6]
            wks.from_list(0, data)
            wks.as_date(0, "yyyy'Q'q")
        See Also:
        """
        self._as_datetime(po.DF_DATE, 21, col, fmt)

    def as_time(self, col, fmt):
        """
        set col as time format

        Parameters:
            col (int or str): If int, column index. If str, column name, short name first, then long name.
            fmt (int or str): can be custom format string, or time display option as int

        Returns:
            (None)

        Examples:
            wks=op.find_sheet()
            data = [1.1,2.2,3.3,4.4,5.5,6.6]
            wks.from_list(0, data)
            wks.as_time(0, "D:hh':'mm':'ss TT")
        See Also:
        """
        self._as_datetime(po.DF_TIME, 17, col, fmt)

    def move_cols(self, n, c1, ncols=1):
        """
        moves a contiguous set of columns

        Parameters:
            n (int): by how many positions to move; if negative, columns are moved left,
                     otherwise right.
            c1 (int): the index of the first columns in the contiguous set.
            ncols (int): the total number of columns in the contiguous set.

        Returns:
            (bool)    returns True for success.

        Examples:
            wks=op.find_sheet()
            wks.move_cols(2, 1, 3)    # it moves three columns, beginning with the second column,
                                    # by two positions right.
        See Also:
        """
        return self.obj.MoveColumns(c1, ncols, n)

    def plot_cloneable(self, template):
        r'''
        Plots workbook data into a cloneable graph template

        Parameters:
            template (str): Cloneable graph template name.
        Returns:
            (None)
        Example:
            ws = op.new_book('w', hidden = False)[0]
            ws.from_file(op.path('e') + r'Samples\Statistics\Automobile.dat', True)
            ws.plot_cloneable('mytemplate')
        '''
        self.obj.LT_execute(f'worksheet -pa ? "{template}";win -rp %H;')

    def set_formula(self, col, formula):
        """
        set column formula
        Parameters:
            col (int or str): If int, column index. If str, column name, short name first, then long name.
            formula(str): column formula (Fx) to set.
        Example:
            wks = op.find_sheet()
            wks.set_formula('B', 'A+1')

        """
        if org_ver() < 9.85:
            if isinstance(col, int):
                col += 1
            self.obj.LT_execute(f'col({col})[O]$={formula}')
        else:
            colobj = self._find_col(col)
            colobj.SetStrProp('formula', formula)

    def report_table(self, *args):
        """
        Get Report table as DataFrame
        Parameters:
            args: Table names as string
        Example:
            wks = op.find_sheet()
            df1 = wks.report_table("Parameters")
        """
        ff = po.LT_get_str(f'GetReportTable({self.lt_range()}, {"|".join(args)}, 1, 1, 1)$')
        if not ff:
            return None
        df = pd.read_table(ff)
        os.remove(ff)
        return df

    def _to_lt_str(self, col):
        """
        return empty str if not valid, otherwise return LabTalk column index as str
        """
        if isinstance(col,str):
            if len(col) == 0 or col == '#':
                return col
            temp = self.lt_col_index(col)
            if temp < 1:
                return ''
            return str(temp)
        if not isinstance(col,int):
            raise ValueError('invalid column specification')
        if col < 0:
            return ''
        return str(col + 1)

    def to_xy_range(self, colx, coly, colyerr, colxerr=''):
        """
        Make XY range string from columns
        Parameters:
            colx, coly, colyerr, colxerr:type can be int or str, If int, column index. If str, tries short name and if not exists, tries column long name

        Returns:
            XY range string
        Examples:
            wks=op.find_sheet()
            wks.cols=3
            strRange = wks.to_xy_range(0,1,2)

        """
        colx = self._to_lt_str(colx)
        coly = self._to_lt_str(coly)
        colyerr = self._to_lt_str(colyerr)
        colxerr = self._to_lt_str(colxerr)
        if colxerr:
            colspec = f'({colx}, {coly}, {colyerr}, {colxerr})'
        elif colyerr:
            colspec = f'({colx}, {coly}, {colyerr})'
        else:
            colspec = f'({colx}, {coly})'
        srange = self.lt_range(False)
        return f'{srange}!{colspec}'

    def to_col_range(self, col):
        """
        Make Column range string
        Parameters:
            col(int or str): If int, column index. If str, tries short name and if not exists, tries column long name
        Returns:
            XY range string
        Examples:
            wks=op.find_sheet()
            wks.cols=3
            strRange = wks.to_col_range(1)
        """
        col = self._to_lt_str(col)
        srange = self.lt_range(False)
        return f'{srange}!{col}'

    def merge_label(self, type_ = 'L', unmerge=False):
        """
        merge or unmerge specified label row
        Parameters:
            type_(string):can be 'L' for longname, 'U' for Units, 'C' for comments
            unmerge(bool):false for merge, true for unmerge
        Returns:
            (None)
        Examples:
            wks=op.find_sheet()
            arrLName = ['longname','longname']
            wks.set_labels(arrLName)
            wks.merge_label()
        """
        if org_ver() < 9.9:
            raise ValueError('merge_label requires Origin 2022 or later')
        nn = 0 if unmerge else 1
        self.method_int('merge', f'{type_},{nn}')

    def cell(self, row, col):
        """
        It returns the contents of a worksheet cell as a string.

        Parameters:
            row (int): the row index.
            col (int, str): if int, it is the column index, otherwise the column name

        Returns:
            (str) the contents of a worksheet cell as a string.
        Examples:
            wks=op.find_sheet()
            ls = [1,2,3]
            wks.from_list(0,ls)
            nVal = wks.cell(0,0)
            print(nVal)
        """
        if isinstance(col, int):
            colarg = col + 1
        else:
            colarg = col        # column name
        return self.method_str('cell', f'{row + 1},{colarg}')

    def set_cell_note(self, row, col, text):
        """
        create or update a cell's Note

        Parameters:
            row (int):          the row index.
            col (int, str):     if int, it is the column index, otherwise the column name
            text (str):         The cell note content
        Returns:
            (None)
        Examples:
            wks=op.find_sheet()
            wks.set_cell_note(0,0,'test cell note')
        """
        if org_ver() < 9.95:
            raise Exception("Needs Origin 2022b or later")

        ncol = self._col_index(col)
        self.method_int('SetNote', f'{row + 1},{ncol+1},"{text}"')

class WBook(DBook):
    """
    This class represents an Origin Workbook, it holds an instance of a PyOrigin WorksheetPage.
    """
    def _sheet(self, obj):
        return WSheet(obj)

    def add_sheet(self, name='', active=True):
        """
        add a new worksheet to the workbook

        Parameters:
            name (str): the name of the new sheet. If not specified, default names will be used
            active (bool): Activate the newly added sheet or not
        """
        return WSheet(self._add_sheet(name, active))

    def unembed_sheet(self, sheet):
        '''
        unembeds and activates embedded graph sheet
        if graph was embedded in worksheet by Add Graph as Sheet, this
        unembeds the page and deletes the worksheet.

        Parameters:
            sheet (int or str): sheet index, or sheet name
        Returns:
            (None)

        Example:
            book = op.find_book('w','Book1')
            book.unembed_sheet(1)
            #book.unembed_sheet('Graph1') #can also use using sheet name
        '''
        wks = self[sheet]
        wks.obj.LT_execute('%A=%@G')
        name = po.LT_get_str('%A')
        if name:
            page = po.Pages(name)
            opt = '' if page else 'n'
            po.LT_execute(f'win -a{opt} {name};layer -d {wks.lt_range()}')
        else:
            print(f'{wks.lt_range()} has no embedded')

def from_series(*args):
    'Construct python list from pd series'
    data = []
    for s in args:
        if isinstance(s, pd.Series):
            dtype = str(s.dtype)
            if dtype == 'object':
                s1 = _check_convert_py_time_to_tdlt(s)
                if s1 is not s:
                    s = s1
                    dtype = 'timedelta'
            if dtype == 'datetime64[ns]':
                d = _series_to_julian_date(s)
            elif dtype == 'timedelta':
                d = _series_to_time(s)
            else:
                d = s
        else:
            d = s
        data.append(d)
    return data
