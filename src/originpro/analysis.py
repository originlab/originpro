"""
originpro
A package for interacting with Origin software via Python.
Copyright (c) 2021 OriginLab Corporation
"""
# pylint: disable=C0103,W0622,W0621,C0301,R0913,R0201
import xml.etree.ElementTree as ET
from .config import po
from .utils import lt_tree_to_dict

class NLFit:
    '''
    class for performing Non-Linear Curve Fitting with Origin's internal fitting engine
    The name of the fitting function already defined inside Origin must be provided to use this class
    '''
    def __init__(self, func, method='auto'):
        self._tree_name = ''
        self._ended=False
        self.func=func
        try:
            self._trfdf = ET.fromstring(po.LT_get_str(f'GetFDFAsXML("{self.func}")$'))
        except Exception as e:
            raise ValueError(f'Invalid fitting function: {func}') from e
        function_model = self._general_info('FunctionModel')
        self._implicit = function_model is not None and function_model.text == 'Implicit'
        self._odr = False
        self._numDeps = int(self._general_info('NumberOfDependentVariables').text)
        self._numIndeps = int(self._general_info('NumberOfIndependentVariables').text)
        if method == 'auto':
            self._odr = self._implicit
        elif method == 'odr':
            self._odr = True
        elif method == 'lm':
            if self._implicit:
                raise ValueError(f'Implicit function({func}) supports odr fitting method only.')
        else:
            raise ValueError(f'Invalid fitting method: {method}')

    def __del__(self):
        tr = self._get_tree_name()
        if po:
            po.LT_execute(f'del -vt {tr}')

    def _get_tree_name(self):
        if not self._tree_name:
            self._tree_name = f'_PY_NLFIT_TREE_{id(self)}'
        return self._tree_name

    def _set(self, property, value):
        tr = self._get_tree_name()
        strLT = f'{tr}.{property}={value}'
        po.LT_execute(strLT)

    def _get(self, property):
        tr = self._get_tree_name()
        return po.LT_evaluate(f'{tr}.{property}')

    def _func_section(self, section):
        sec = self._trfdf.find(section)
        if sec:
            return sec
        return self._trfdf.find(section.upper())

    def _general_info(self, key):
        return self._func_section('GeneralInformation').find(key)

    def set_data(self, wks, x, y, yerr='', xerr='', z=''):
        """
        set the XY data with optional error bar column, or XYZ data
        Parameters:
            wks(worksheet):
            x,y(int or string):column index or name
            yerr,xerr,z(int or string):column index or name
        Returns:
            none
        Examples:
            model=op.NLFit('Gauss')
            wks=op.find_sheet()
            model.set_data(wks, 0, 1, xerr='D' )
        """
        rng = wks.to_xy_range(x, y, z if z else yerr, xerr)
        tr = self._get_tree_name()
        xf = 'nlbegin'
        if z:
            xf += 'z'
        elif self._odr:
            xf += 'o'
        po.LT_execute(f'{xf} {rng} {self.func} {tr}')
        self._ended=False

    def set_mdata(self, ms, z):
        """
        set the Matrix data
        Parameters:
            ms(matrix sheet):
            z(int or string):matrix object index or long name
        Returns:
            none
        Examples:
            aa = np.array([ [1, 2, 3.9], [4.1, 5, 6], [7, 8.5, 9] ])
            ma=op.new_sheet('m')
            ma.from_np(aa)
            model = op.NLFit('Plane')
            model.set_mdata(ma,1)
        """
        if isinstance(z, int):
            z =+ 1
        rng = f'{ms.lt_range(False)}!{z}'
        tr = self._get_tree_name()
        strLT=f'nlbeginm {rng} {self.func} {tr}'
        po.LT_execute(strLT)
        self._ended=False

    def set_range(self, rg):
        """
        set data as range string
        Parameters:
            rg(string): range string
        Returns:
            none
        Examples:
            gl=op.find_graph()[0]
            dp=gl.plot_list()[0]
            model=op.NLFit('Lorentz')
            model.set_range(dp.lt_range())
            model.fit()
        """
        tr = self._get_tree_name()
        xf = 'nlbegin'
        if self._odr:
            xf += 'o'
        if not ((self._implicit and self._numIndeps == 2) or
                (not self._implicit and self._numDeps == 1 and self._numIndeps == 1)):
            xf += 'r'
        strLT=f'{xf} {rg} {self.func} {tr}'
        po.LT_execute(strLT)
        self._ended=False

    def fix_param(self, p, val):
        """
        fix a parameter to a value or to turn off the fixing

        Parameters:
            p(str): name of a parameter
            val(bool or float): use False to turn off parameter fixing, or specify a value to fix it to
        Returns:
            none
        Examples:
            model.fix_param('y0', 0)
            model.fix_param('xc', False)
        """
        fix = 1
        if isinstance(val, bool):
            fix = 1 if val else 0
        else:
            self._set(p, val)
        self._set(f'f_{p}', fix)

    def set_param(self, p, val):
        """
        set a parameter value before fitting
        Parameters:
            p(str): name of a parameter
            val(float): value for the parameter
        Returns:
            none
        Examples:
            model.set_param('xc', 0.5)
        """
        self._set(p, val)

    def set_lbound(self, p, ctrl='>', val=None):
        r"""
        set parameter lower bounds in NLFit.
        Parameters:
            p(str): name of a parameter
            ctrl(str): '>' or '>='
            val(float): lower bound value
        Returns:
            none
        Examples:
            import originpro as op
            wks = op.new_sheet()
            fn=op.path('e') + r'Samples\Curve Fitting\Gaussian.dat'
            wks.from_file(fn, False)
            model2 = op.NLFit('Gauss')
            model2.set_data(wks, 0, 1)
            model2.set_lbound('y0','>','6')
            model2.set_ubound('A','<','800')
            model2.fit()
            r, c = model2.report()
        """
        return self._set_bound('l', p, ctrl, val, '>', '>=')

    def set_ubound(self, p, ctrl='<', val=None):
        r"""
        set parameter upper bounds in NLFit.
        Parameters:
            p(str): name of a parameter
            ctrl(str): '<' or '<='
            val(float): upper bound value
        Returns:
            none
        Examples:
            import originpro as op
            wks = op.new_sheet()
            fn=op.path('e') + r'Samples\Curve Fitting\Gaussian.dat'
            wks.from_file(fn, False)
            model2 = op.NLFit('Gauss')
            model2.set_data(wks, 0, 1)
            model2.set_lbound('y0','>','6')
            model2.set_ubound('A','<','800')
            model2.fit()
            r, c = model2.report()
        """
        return self._set_bound('u', p, ctrl, val, '<', '<=')

    def _set_bound(self, lu, p, ctrl, val, ctrlonx, ctrlon):
        on = 0
        if ctrl:
            if ctrl == ctrlonx:
                on = 1
            elif ctrl == ctrlon:
                on = 2
        self._set(f'{lu}bon_{p}', 1 if on else 0)
        if on:
            self._set(f'{lu}bx_{p}', 1 if on == 1 else 0)
        if val:
            self._set(f'{lu}b_{p}', val)

    def param_box(self):
        """
        open a modal dialog box to control fitting parameters and iterations.
        You can click the minimize button on the parameters dialog to manipulate the graph like zooming in, or use
        screen reader etc. Must still call fit() after.
        Parameters:
            none
        Returns:
            none
        Examples:
            model = op.NLFit('Gauss')
            wks=op.find_sheet()
            model.set_data(wks, 0, 1)
            model.param_box()
        """
        po.LT_execute('nlpara 1')

    def fit(self, iter=''):
        """
        iterate the fitting engine

        Parameters:
            iter (str or int): empty will iterate until converge, otherwise to specify the number of iterations
        Returns:
            none
        Examples:
            model = op.NLFit('Gauss')
            wks=op.find_sheet()
            model.set_data(wks, 0, 1)
            model.param_box()
            model.fit()
        """
        po.LT_execute(f'nlfit {iter}')

    def result(self):
        """
        you need to end the fitting by either calling result or report. If you need both, you need to call report first.
        Parameters:
            none
        Return:
            (dict) fitting parameters and statistics from the fit
        Examples:
            model = op.NLFit('Gauss')
            wks=op.find_sheet()
            model.set_data(wks, 0, 1)
            model.param_box()
            model.fit()
        """
        if not self._ended:
            po.LT_execute('nlend')
            self._ended = True
        tr = self._get_tree_name()
        d = lt_tree_to_dict(f'{tr}')
        return d

    def report(self, autoupdate=False):
        """
        you need to end the fitting by either calling result or report
        Parameters:
            autoupdate(bool): setup recalculation on the report or not

        Returns:
            (tuple): range strings of the report sheet and the fitted curves

        Example:
            model.fit()
            r, c = model.report()
            Report=op.find_sheet('w', r)
            Curves=op.find_sheet('w', c)
            print(Report)
            print(Curves.shape)
        """
        if self._ended:
            raise ValueError('You must call report() before calling result().')

        oldVal=po.LT_evaluate('@NLFS')
        po.LT_set_var('@NLFS',0)#do not show Reminder Messagebox about switching to reportsheet, and set to no-switch
        if autoupdate:
            po.LT_execute('nlend 1 1')
        else:
            po.LT_execute('nlend 1')
        self._ended = True
        po.LT_set_var('@NLFS',oldVal)
        return po.LT_get_str('__REPORT'), po.LT_get_str('__FITCURVE')

class LinearFit:
    '''
    class for performing Linear Fitting with Origin's internal fitting engine
    '''
    def __init__(self):
        self._tree_name = ''
        self._output_tree_name = ''
        strGUITreeName = self._get_tree_name()
        po.LT_execute(f'Tree {strGUITreeName}')
        strLT = f'xop execute:=init classname:=FitLinear iotrgui:={strGUITreeName}'
        po.LT_execute(strLT)

    def __del__(self):
        tr = self._get_tree_name()
        if po:
            po.LT_execute(f'del -vt {tr}')

    def _get_tree_name(self):
        if not self._tree_name:
            self._tree_name = f'_PY_LR_TREE_{id(self)}'
        return self._tree_name
    def _get_output_tree_name(self):
        if not self._output_tree_name:
            self._output_tree_name = f'_PY_LR_OUTPUT_{id(self)}'
        return self._output_tree_name

    def _set(self, property, value):
        tr = self._get_tree_name()
        strLT = f'{tr}.GUI.{property}={value}'
        po.LT_execute(strLT)

    def set_data(self, wks, x, y, err = ''):
        """
        set the XY data with optional error bar column
        Parameters:
            wks(worksheet):
            x,y(int or string):column index or name
            err(int or string):column index or name
        Returns:
            none
        Examples:
            lr = op.LinearFit()
            wks=op.find_sheet()
            lr.set_data(wks, 1, 2)
        """
        self._set('InputData.Range1.X$', wks.to_col_range(x))
        self._set('InputData.Range1.Y$', wks.to_col_range(y))
        if err:
            self._set('InputData.Range1.ED$', wks.to_col_range(err))

    def fix_slope(self, val):
        """
        fix slope to a value
        Parameters:
            val(float): slope value
        Returns:
            none
        Examples:
            lr=op.LinearFit()
            lr.fix_slope=0.6
        """
        self._set('Fit.FixSlope', 1)
        self._set('Fit.FixSlopeAt', val)
    def fix_intercept(self, val):
        """
        fix intercept to a value
        Parameters:
            val(float): intercept value
        Returns:
            none
        Examples:
            lr=op.LinearFit()
            lr.fix_intercept=0.6
        """
        self._set('Fit.FixIntercept', 1)
        self._set('Fit.FixInterceptAt', val)

    def result(self):
        """
        perform the fitting and return the parameters. You need to end the fitting by either calling result or report

        Return:
            (dict) fitting parameters and statistics from the fit

        Examples:
            lr = op.LinearFit()
            lr.set_data(wks, 1, 2)
            rr = lr.result()
            b       =rr['Parameters']['Slope']['Value']
            b_err   =rr['Parameters']['Slope']['Error']

        """
        trOut = self._get_output_tree_name()
        strGUITreeName = self._get_tree_name()
        strLT = f'xop execute:=run iotrgui:={strGUITreeName} otrresult:={trOut}'
        po.LT_execute(strLT)
        dd = lt_tree_to_dict(trOut)
        po.LT_execute(f'del -vt {trOut}')
        return dd

    def report(self, band=0):
        """
        perform the fitting and generate the report. You need to end the fitting by either calling result or report

        Parameters:
            band (int): confidence and prediction bands. 0=none,1=confidence,2=prediction,3=both

        Returns:
            (tuple): range strings of the report sheet and the fitted curves

        Examples:
            lr = op.LinearFit()
            lr.set_data(wks, 1, 2)
            r, c = lr.report(1)
            wReport=op.find_sheet('w', r)
            wCurves=op.find_sheet('w', c)
        """
        if band & 1:
            self._set('Graph1.ConfBands',1)
        if band & 2:
            self._set('Graph1.PredBands',1)
        strGUITreeName = self._get_tree_name()
        strLT = f'xop execute:=report iotrgui:={strGUITreeName}'

        oldVal=po.LT_evaluate('@NLFS')
        po.LT_set_var('@NLFS',0)#do not show Reminder Messagebox about switching to reportsheet, and set to no switch
        po.LT_execute(strLT)
        po.LT_set_var('@NLFS',oldVal)

        return po.LT_get_str('__REPORT'), po.LT_get_str('__FITCURVE')
