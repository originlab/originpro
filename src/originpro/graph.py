"""
originpro
A package for interacting with Origin software via Python.
Copyright (c) 2020 OriginLab Corporation
"""
# pylint: disable=C0301,C0103,C0302,W0622,R0913,W0212
from contextlib import contextmanager
from .config import po
from .base import BaseObject, BaseLayer, BasePage, _layer_range
from .utils import to_rgb, ocolor, get_file_parts, last_backslash, origin_class, org_ver

@contextmanager
def CopyPageRatio(ratio):
    """
        temporarily change System.copyPage.ratio
        Parameters:
            ratio(float):ratio when copy page
        Returns:
            (none)
        Examples:
            import originpro as op
            with op.CopyPageRatio(50) as cpr:
                print('set System.copyPage.ratio to',op.lt_int('System.copyPage.ratio'))
            print('set System.copyPage.ratio back to',op.lt_int('System.copyPage.ratio'))
    """

    COPY_PAGE_RATIO = 'System.CopyPage.Ratio'
    oldRatio = po.LT_evaluate(COPY_PAGE_RATIO)
    po.LT_set_var(COPY_PAGE_RATIO, ratio)
    yield
    po.LT_set_var(COPY_PAGE_RATIO, oldRatio)

class Axis:
    """
    This class represents an instance of Axis on a GLayer.
    """

    def __init__(self, obj, ax):
        self.layer = obj
        types = {
            'x':2,'y':4,'z':1
            }
        self.type = types[ax]
        self.ax = ax

    @property
    def sfrom(self):
        """
        get scale limit from value
        Parameters:
            none
        Returns:
            scale.from val
        Examples:
            gl=op.find_graph()[0]
            ax=gl.axis('x')
            print(ax.sfrom)
        """
        return self.layer.GetNumProp(f'{self.ax}.from')
    @sfrom.setter
    def sfrom(self, value):
        """
        set scale limit from value
        Parameters:
            value(float):
        Returns:
            scale.from val
        Examples:
            gl=op.find_graph()[0]
            ax=gl.axis('x')
            ax.sfrom=0.7
        """
        self.layer.SetNumProp(f'{self.ax}.from', value)

    @property
    def sto(self):
        """
        get scale limit to value
        Parameters:
            none
        Returns:
            scale.to val
        Examples:
            gl=op.find_graph()[0]
            ax=gl.axis('x')
            print(ax.sto)
        """
        return self.layer.GetNumProp(f'{self.ax}.to')
    @sto.setter
    def sto(self, value):
        """
        set scale limit to value
        Parameters:
            value(float):
        Returns:
            none
        Examples:
            gl=op.find_graph()[0]
            ax=gl.axis('x')
            ax.sto=7
        """
        self.layer.SetNumProp(f'{self.ax}.to', value)

    @property
    def sstep(self):
        """
        get scale limit increment
        Parameters:
            none
        Returns:
            scale limit increment val
        Examples:
            gl=op.find_graph()[0]
            ax=gl.axis('x')
            print(ax.sstep)
        """
        return self.layer.GetNumProp(f'{self.ax}.inc')
    @sstep.setter
    def sstep(self, value):
        """
        set scale limit increment
        Parameters:
            value(float):
        Returns:
            none
        Examples:
            gl=op.find_graph()[0]
            ax=gl.axis('x')
            ax.sstep=0.7
        """
        self.layer.SetNumProp(f'{self.ax}.inc', value)

    @property
    def scale(self) -> int:
        """
        get axis scale type
        Parameters:
            none
        Returns:
            scale type:int value for a type
            1:'linear', 2: 'log10', 3: 'probability', 4: 'probit', 5: 'reciprocal',
            6:'offset_reciprocal', 7: 'logit', 8: 'ln', 9: 'log2'.
        Examples,
            gl=op.find_graph()[0]
            ax=gl.axis('x')
            print(ax.scale)
        """
        return int(self.layer.GetNumProp(f'{self.ax}.type'))

    @scale.setter
    def scale(self, value):
        """
        set axis scale type
        Parameters:
            value(int or str): if int, it is a value between 1 to 9, if string, it can be one of belew:
            'linear', 'log10', 'probability', 'probit', 'reciprocal', 'offset_reciprocal', 'logit', 'ln', 'log2'
        Returns:
            return scale type as int val
        Examples:
            gl=op.find_graph()[0]
            ax=gl.axis('x')
            ax.scale="log10"
            ax.scale=3
        """
        if isinstance(value, int):
            self.layer.SetNumProp(f'{self.ax}.type', value)
        elif isinstance(value, str):
            scales = {'linear': 1, 'log10': 2, 'probability': 3, 'probit': 4, 'reciprocal': 5,
                      'offset_reciprocal': 6, 'logit': 7, 'ln': 8, 'log2': 9}
            self.scale = scales.get(value)
        else:
            raise TypeError('unknown scale type')
        return self.scale

    @property
    def limits(self):
        """
        axis scale limits

        Parameters:

        Returns:
            (tuple) from, to, increment

        Examples:
            from, to, inc = ax.limits
        """
        return self.sfrom, self.sto, self.sstep

    @limits.setter
    def limits(self, limits):
        """
        Property setter returns the scale limits (from` and `to) for the axis.

        Parameters:
            limits (tuple): (from, to)

        Returns:
            None

        Examples:
            ax.limits = (1, 10, 1)
        """
        self.set_limits(limits)

    def set_limits(self, begin=None, end=None, step=None):
        """

        Sets scale from and to values for the axis

        Parameters:
            begin (float, tuple, list): The From value of limits, or specify [begin,end], or [begin,end,step]
            end (float): The To value of limits. None leaves the value unchanged.
            step (float): The Increment of the limits. None leaves the value unchanged.

        Returns:
            (tuple) from, to, increment

        Examples:
            ax.set_limits(step=0.3)
            ax.set_limits(5, 15)
        """
        #if auto:
            #cmd = {'x': 'yzm', 'y': 'xzm', 'z': 'xym'}[self.ax]
            #self.layer.LT_execute(f'layer -ar{cmd}e')
            #return self.limits
        #elif sto is None and isinstance(sfrom, (tuple, list)):
        #    sfrom, sto = sfrom
        if end is None and step is None and isinstance(begin, (tuple, list)):
            if len(begin) == 3:
                begin, end, step = begin
            elif len(begin) == 2:
                begin, end = begin
            else:
                raise ValueError('must specify 2 or 3 values')

        if begin is not None:
            self.sfrom = begin
        if end is not None:
            self.sto = end
        if step is not None:
            self.sstep = step
        return self.limits

    @property
    def title(self):
        """
        Property getter for axis title.

        Parameters:

        Returns:
            (str) Title

        Examples:
            txt = ax.title
        """
        label_name = {'x': 'xb', 'x2': 'xt', 'y': 'yl', 'y2': 'yr', 'z': 'zb', 'z2': 'zf'}[self.ax]
        label = GLayer(self.layer).label(label_name)
        if label is None:
            return ''
        return label.text

    @title.setter
    def title(self, value):
        """
        Property setter for axis title.

        Parameters:
            value (str): Title text

        Returns:
            (str) Title

        Examples:
            ax.title = 'X Axis'
        """
        label_name = {'x': 'xb', 'x2': 'xt', 'y': 'yl', 'y2': 'yr', 'z': 'zb', 'z2': 'zf'}[self.ax]
        cmd = f'label -{label_name} {value}'
        self.layer.LT_execute(cmd)
        return self.title


class Label(BaseObject):
    """
    This class represents an instance of a text object on a GLayer.
    """
    def __init__(self, obj, layer):
        self.layer=layer
        super().__init__(obj)

    def remove(self):
        """
        Deletes label.
        Parameters:
            none
        Returns:
            None
        Examples:
            gl=op.find_graph()[0]
            label = gl.label('xb')
            label.remove()
        """
        self.obj.Destroy()

    # def __repr__(self) -> str:
        # if self.obj.IsValid():
            # return f'Label named {self.name} in [{self.layer.GetParent().Name}]{self.layer.Name}'
        # else:
            # raise RuntimeError('label no longer exists')

    @property
    def color(self):
        """
        Property getter returns the RGB color of the text object as a tuple (Red, Green, Blue)

        Parameters:

        Returns:
            (tuple) r,g,b

        Examples:
            label = g[0].label('text')
            red, green, blue = label.color
        """
        orgb = self.get_int('color')
        return to_rgb(orgb)

    @color.setter
    def color(self, rgb):
        """
        Property setter for the RGB color of the text object

        Parameters:
            rgb(int, str, tuple): various way to specify color, see function ocolor(rgb) in op.utils

        Returns:
            None

        Examples:
            label = g[0].label('text')
            label.color = 'Red'
            label.color = 3            # 'Green'
            label.color = '#00f'       # 'blue'
            label.color = '#0000ff'    # 'blue'
            label.color = [0, 255, 0]  # 'green'
        """
        self.set_int('color', ocolor(rgb))
    @property
    def text(self) -> str:
        """
        Property getter for object text.

        Parameters:

        Returns:
            (str) Object text
        Examples:
            gl=op.find_graph()[0]
            label = gl.label('xb')
            print(label.text)
        """
        return self.obj.Text

    @text.setter
    def text(self, text: str) -> str:
        """
        Property setter for object text.

        Parameters:
            value (str): Text

        Returns:
            (str) Object text
        Examples:
            gl=op.find_graph()[0]
            label = gl.label('yl')
            label.text='123'
        """
        self.obj.Text = text
        return self.text

class Plot(BaseObject):
    """
    This class represents an instance of a data plot in a GLayer.
    """
    def __init__(self, obj, layer):
        self.layer=layer
        super().__init__(obj)

    def _format_property(self, prop):
        nplot = self.index() + 1
        return f'plot{nplot}.{prop}'

    def lt_range(self):
        """
        Return the Origin Range String that identify Data Plot object
        Parameters:
            none
        Returns:
            Origin Range String
        Examples:
            gl=op.find_graph()[0]
            p=gl.plot_list()[0]
            print(p.lt_range())

        """
        return f'{_layer_range(self.layer, False)}!{self.index() + 1}'

    @property
    def color(self):
        """
        returns the RGB color of the plot object as a tuple (Red, Green, Blue)

        Parameters:

        Returns:
            (tuple) r,g,b

        Examples:
            p = g[0].plot_list()[0]
            red, green, blue = p.color
        """
        orgb = int(self.layer.GetNumProp(self._format_property('color')))
        return to_rgb(orgb)

    @color.setter
    def color(self, rgb):
        """
        set for the RGB color of the plot object

        Parameters:
            rgb(int, str, tuple): various way to specify color, see function ocolor(rgb) in op.utils

        Returns:
            None

        Examples:
            p = g[0].add_plot(wks,'(0,1)')
            p.color = '#0f0'
        See Also:
            ocolor(rgb)
        """
        self.layer.SetNumProp(self._format_property('color'), ocolor(rgb))

    @property
    def colorinc(self):
        """
        returns the color increment of the grouped plot object

        Parameters:

        Returns:
            (int) color increment

        Examples:
            p = g[0].plot_list()[0]
            inc = p.colorinc
        """
        return int(self.layer.GetNumProp(self._format_property('colorinc')))

    @colorinc.setter
    def colorinc(self, inc):
        """
        set the color increment of the plot object

        Parameters:
            inc(int): color increment

        Returns:
            None

        Examples:
            p = g[0].add_plot(wks,'(0,1)')
            p.colorinc = 1
        """
        self.layer.SetNumProp(self._format_property('colorinc'), inc)

    @property
    def colormap(self):
        """
        Returns the colormap name a string

        Parameters:

        Returns:
            (str) colormap name

        Examples:
            pl = g[0].plot_list()[0]
            cm = pl.colormap
        """
        name = self.layer.GetStrProp(self._format_property('colorlist'))
        return name if name else self.layer.GetStrProp(self._format_property('cmap.palette'))

    @colormap.setter
    def colormap(self, name):
        """
        Set the colormap of the plot object

        Parameters:
            Colormap name, can be colorlist, palette.

        Returns:
            None

        Examples:
            p = g[0].add_plot(wks,'(0,1)')
            p.colormap = 'Fire' # colorlist
            p.colormap = 'Maple.pal' # palette
        """
        namelow = name.lower()
        if namelow.endswith('.pal') or namelow.endswith('.xml'):
            if org_ver() < 10.0:
                self.layer.SetStrProp(self._format_property('cmap.palette'), name)
            else:
                self.layer.SetStrProp(self._format_property('colorlist'), name)
            self.layer.SetNumProp(self._format_property('cmap.stretchpal'), 1)
        else:
            self.layer.SetStrProp(self._format_property('colorlist'), name)
            self.layer.SetNumProp(self._format_property('cmap.stretchpal'), 0)
        self.layer.SetNumProp(self._format_property('cmap.linkpal'), 1)

    def set_shapelist(self, name):
        """
        Set the shape list of the plot object

        Parameters:
            Shape list, can be theme file name, or integer list

        Returns:
            None

        Examples:
            p = g[0].add_plot(wks,'(0,1)')
            p.shapelist = 'Symbol Type Square and Circle' # theme file
            p.shapelist = [3, 2, 1]
        """
        if isinstance(name, list):
            name = '{' + ','.join(str(n) for n in name) + '}'
        self.layer.SetStrProp(self._format_property('shapelist'), name)
    shapelist = property(None, set_shapelist)

    @property
    def zlevels(self):
        """
        Returns the information about z-levels as a dictionary
        Parameters:
            none
        Returns:
            dictionary of z-levels
        Examples:
            gl=op.find_graph()[0]
            p = gl.plot_list()[0]
            print(p.zlevels)

        """
        numlevels = int(self.layer.GetNumProp(self._format_property('cmap.numcolors')))
        listzlevels = []
        for ilevel in range(numlevels):
            propname = f'cmap.z{ilevel + 1}'
            zval = self.layer.GetNumProp(self._format_property(propname))
            listzlevels.append(zval)

        zabove = self.layer.GetNumProp(self._format_property('cmap.zabove'))
        listzlevels.append(zabove)
        minors = int(self.layer.GetNumProp(self._format_property('cmap.NumMinorLevels')))
        if minors > 0:
            listzlevels = listzlevels[::minors+1]
        dictret = {
            'minors': minors,
            'levels': listzlevels,
            #'levelabove': zabove,
        }

        return dictret


    @zlevels.setter
    def zlevels(self, dict):
        """
        set the z-levels from the modified dictionary returned from the getter

        Examples:
            msheet = op.find_sheet('m', '[MBook1]')
            graph = op.new_graph(template='contour')
            gl = graph[0];
            plot = gl.add_mplot(msheet, z=0, type='contour')
            gl.rescale()
            z = plot.zlevels
            z['minors'] = 4
            z['levels'] = [0, 5, 10, 15,20]
            plot.zlevels = z
            plot.colormap = 'Beach.pal'
        """
        minor_levels = dict['minors']
        listlevels = dict['levels']
        strTempLTvarName = '__opZLevelsVar$' #must start with "__" so that it matches LT_SYS_STR_PREFIX
        strVarValue = '|'.join(str(level) for level in listlevels)

        self.layer.DoMethod(self._format_property('cmap.setLevels'), '1') # set Levels by Major
        po.LT_set_str(strTempLTvarName, strVarValue)
        strLT = self._format_property('cmap.setZLevels')
        self.layer.DoMethod(strLT, f'{strTempLTvarName}, {minor_levels}')
        strLT = f'del -v {strTempLTvarName}'
        po.LT_execute(strLT)
        #self.layer.SetNumProp(self._format_property('cmap.zabove'), dict['levelabove'])



    @property
    def symbol_size(self):
        """
        returns the symbol size, see the Labtalk get %C -z command

        Parameters:

        Returns:
            (float) symbol size

        Examples:
            p = g[0].plot_list()[0]
            size = p.symbol_size
        """
        return self.layer.GetNumProp(self._format_property('symbol.size'))

    @symbol_size.setter
    def symbol_size(self, size):
        """
        set symbol size of the plot object, see the LabTalk set %C -z command

        Parameters:
            size(float): symbol size

        Returns:
            None

        Examples:
            p = g[0].add_plot(wks,'(0,1)')
            p.symbol_size = 20.5
        """
        self.layer.SetNumProp(self._format_property('symbol.size'), size)

    @property
    def symbol_kind(self):
        """
        returns the symbol shape, see the LabTalk get %C -k command

        Parameters:

        Returns:
            (int) symbol shape

        Examples:
            p = g[0].plot_list()[0]
            shape = p.symbol_kind
        """
        return int(self.layer.GetNumProp(self._format_property('symbol.kind')))

    @symbol_kind.setter
    def symbol_kind(self, shape):
        """
        set symbol shape of the plot object, see the LabTalk set %C -k command

        Parameters:
            shape(int): symbol shape

        Returns:
            None

        Examples:
            p = g[0].add_plot(wks,'(0,1)')
            p.symbol_kind = 2
        """
        self.layer.SetNumProp(self._format_property('symbol.kind'), shape)

    @property
    def symbol_kindinc(self):
        """
        returns the symbol shape increment of the grouped plot object

        Parameters:

        Returns:
            (int) symbol shape increment

        Examples:
            p = g[0].plot_list()[0]
            shape = p.symbol_kindinc
        """
        return int(self.layer.GetNumProp(self._format_property('symbol.kindinc')))

    @symbol_kindinc.setter
    def symbol_kindinc(self, inc):
        """
        set symbol shape increment of the grouped plot object

        Parameters:
            inc(int): symbol shape increment

        Returns:
            None

        Examples:
            p = g[0].add_plot(wks,'(0,1)')
            p.symbol_kindinc = 1
        """
        self.layer.SetNumProp(self._format_property('symbol.kindinc'), inc)

    @property
    def symbol_interior(self):
        """
        returns the symbol interior type. 0 = no symbol, 1=solid, 2=open, 3=dot center

        Parameters:

        Returns:
            (int) symbol interior

        Examples:
            p = g[0].plot_list()[0]
            kind = p.symbol_interior
        """
        return int(self.layer.GetNumProp(self._format_property('symbol.interior')))

    @symbol_interior.setter
    def symbol_interior(self, fill):
        """
        set symbol interior of the plot object. 0 = no symbol, 1=solid, 2=open, 3=dot center

        Parameters:
            fill(int): symbol interior

        Returns:
            None

        Examples:
            p = g[0].add_plot(wks,'(0,1)')
            p.symbol_interior = 2
        """
        self.layer.SetNumProp(self._format_property('symbol.interior'), fill)

    @property
    def symbol_sizefactor(self):
        """
        returns the symbol size factor, 1 if not changing. This is useful when size is controlled by a worksheet column

        Parameters:

        Returns:
            (float) symbol size factor

        Examples:
            p = g[0].plot_list()[0]
            size = p.symbol_size * p.symbol_sizefactor
        """
        return self.layer.GetNumProp(self._format_property('symbol.sizefactor'))

    @symbol_sizefactor.setter
    def symbol_sizefactor(self, fac):
        """
        set symbol size factor of the plot object. This is useful when size if controlled by a worksheet column

        Parameters:
            fac(float): symbol size factor

        Returns:
            None

        Examples:
            p = g[0].add_plot(wks,'(0,1)')
            p.symbol_size=modi_col(1)
            p.symbol_sizefactor = 10
        """
        self.layer.SetNumProp(self._format_property('symbol.sizefactor'), fac)

    @property
    def transparency(self):
        """
        returns the plot's line or symbol transparency in percent
        Parameters:
            none
        Returns:
            transparency in percent
        Examples:
            gl=op.find_graph()[0]
            p = gl.plot_list()[0]
            print(p.transparency)
        """
        return self.layer.GetNumProp(self._format_property('transparency'))

    @transparency.setter
    def transparency(self, t):
        """
        set the plot's line or symbol transparency in percent
        Parameters:
            t(int):0-100
        Returns:
            transparency in percent
        Examples:
            gl=op.find_graph()[0]
            p = gl.plot_list()[0]
            p.transparency=60

        """
        self.layer.SetNumProp(self._format_property('transparency'), t)

    def remove(self):
        """
        Deletes plot.
        Parameters:
            none
        Returns:
            None
        Examples:
            gl=op.find_graph()[0]
            p = gl.plot_list()[0]
            p.remove()
        """
        self.obj.Destroy()

    def change_data(self, wks, **kwargs):
        '''
        change the data source for an existing data plot

        Parameters:
            wks (WSheet): the worksheet to use
            kwargs : columns and the corresponding axis
        Returns:
            None
        Examples:
            wks = op.find_sheet('w', 'Book1')
            gl = op.find_graph('Graph1')[0]
            dp = gl.plot_list()[0]
            dp.change_data(wks, x='C', y='D')
        '''
        data = []
        if wks:
            data = {desig: wks._find_col(obj) for desig, obj in kwargs.items()}
        else:
            data = kwargs
        for desig, obj in data.items():
            self.obj.ChangeData(obj, desig.upper())

    def set_fill_area(self, above=-1, type=9, below=-1):
        """
        For line plots only, to set Fill Area Under curve option

        Parameters:
            above (int): fill color of "Pattern Above" (or "Pattern")
            type (int): fill area option, 9=Fill to next data plot – above below colors,  see https://www.originlab.com/doc/LabTalk/ref/Set-cmd#Specifying_Pattern
            below (int): fill color of "Pattern Below"


        Returns:
            none
        Examples:
            gl=op.find_graph()[0]
            p=gl.plot_list()[0]
            p.set_fill_area(2, 9, 3)
        """
        sname = self.layer.GetStrProp(self._format_property('name'))
        po.LT_execute(f'set {sname} -pf 1')
        po.LT_execute(f'set {sname} -pfv {type}')
        if above != -1:
            po.LT_execute(f'set {sname} -pfb {above}')
        if below != -1:
            po.LT_execute(f'set {sname} -p2fb {below}')

    def set_cmd(self, *args):
        '''
        Execute labtalk set command for this data plot

        Parameters:
            args: set command options
        Returns:
            none
        Examples:
            wks = op.find_sheet('w', 'Book1')
            gl = op.find_graph('Graph1')[0]
            dp = gl.add_plot(wks, 1, 0)
            dp.set_cmd('-c 2', '-d 2') # line color as red, style as dot
        '''
        cmds = [f'range rr={self.lt_range()}']
        for arg in args:
            cmds.append(f'set rr {arg}')
        if cmds:
            self.layer.LT_execute('{' + ';'.join(cmds) + '}')

    @property
    def group(self):
        """
        Check if data plot in group or not.

        Parameters:

        Returns:
            (int) 0: Not in group, 1: Group Head, 2: Group Member

        Examples:
            pl = g[0].plot_list()[0]
            group = pl.group
        """
        return int(self.layer.GetNumProp(self._format_property('group')))


class GLayer(BaseLayer):
    """
    This class represents an Origin Graph Layer, it holds an instance of a PyOrigin GraphLAyer
    """
    def __repr__(self):
        return 'GLayer: ' + self.lt_range()

    def lt_range(self):
        """
        Return the Origin Range String that identify Graph Layer object
        Parameters:
            none
        Returns:
            Origin Range String
        Examples:
            gl=op.find_graph()[0]
            print(gl.lt_range())

        """
        return _layer_range(self.obj, False)

    def rescale(self, skip = ''):
        """
        update limits to show all the data, including color scale range is colormap is used

        Parameters:
            skip(str): axis to skip(keep limits). Can be a combination of x,y,z,m where m is for colormap

        Returns:
            None

        Examples:
            gl=op.find_graph()[0]
            gl.rescale('x')#rescale Y only
            gl.rescale('m')#do not change colormap scale range
        """
        if len(skip) == 0:
            self.obj.LT_execute('layer -a')
        else:
            self.obj.LT_execute(f'layer -ar{skip}')

    def group(self, group=True, begin=-1, end=-1):
        """
        Group/Ungroup data plots

        Parameters:
            begin(int): plot index, -1 is the same as 0
            end(int): -1 to the last, otherwise ending plot index (0-offset)
        Returns:
            None
        Examples:
            graph = op.new_graph(template='scatter')
            gl=graph[0]
            plot = gl.add_plot('[Book1]1!(A,B:C)', type='s')
            gl.group(True,0,1)
            plot = gl.add_plot('[Book1]1!(A,D:0)', type='l')
            gl.group(True,2,3)
        """
        script = (f'layer -g{"" if group else "u"} '
                f'{"" if begin < 0 else begin+1} '
                f'{"" if not group or end < 0 else end+1}')
        self.obj.LT_execute(script.rstrip())

    def axis(self, ax):
        """
        Creates a new Axis object

        Parameters:
            ax (str): One of 'x', 'y', or 'z'

        Returns:
            (Axis)

        Examples:
            ax = lay.axis('x')
        """
        return Axis(self.obj, ax)

    @property
    def xlim(self):
        """
        Property getter for X axis limits.
        Parameters:
            none
        Returns:
            New X axis limits
        Examples:
            gl=op.find_graph()[0]
            print(gl.xlim)
        """
        return self.axis('x').limits
    @xlim.setter
    def xlim(self, limits):
        """
        Sets X axis scale begin(From), end(To) and step(Increment)
        Parameters:
            limit(axis scale):(begin,end, step)
        Returns:
            New axis limits
        Examples:
            gl=op.find_graph()[0]
            gl.xlim=(2,9,3)
        """
        return self.set_xlim(limits)

    @property
    def ylim(self):
        """
        Property getter for Y axis limits.
        Parameters:
            none
        Returns:
            Y axis limits
        Examples:
            gl=op.find_graph()[0]
            print(gl.ylim)
        """
        return self.axis('y').limits
    @ylim.setter
    def ylim(self, limits):
        """
        Sets Y axis scale begin(From), end(To) and step(Increment)
        Parameters:
            limit(axis scale):(begin,end, step)
        Returns:
            New axis limits
        Examples:
            gl=op.find_graph()[0]
            gl.ylim=(2,9,3)
        """
        return self.set_ylim(limits)

    @property
    def zlim(self):
        """
        Property getter for Y axis limits.
        Parameters:
            none
        Returns:
            Z axis limits
        Examples:
            gl=op.find_graph()[0]
            print(gl.zlim)
        """
        return self.axis('z').limits
    @zlim.setter
    def zlim(self, limits):
        """
        Sets Z axis scale begin(From), end(To) and step(Increment)
        Parameters:
            limit(axis scale):(begin,end, step)
        Returns:
            New axis limits
        Examples:
            gl=op.find_graph()[0]
            gl.zlim=(2,9,3)
        """
        return self.set_zlim(limits)


    def set_xlim(self, begin=None, end=None, step=None):
        """
        Sets X axis scale begin(From), end(To) and step(Increment)

        Parameters:
            begin (float or None): axis new From or Begin value.
            end (float or None): axis new To or End value.
            step (float or None): axis new Step or Increment value.

        Returns:
            New axis limits

        Examples:
            g = op.new_graph()
            g[0].set_xlim(0, 1)
            g[0].set_xlim(step=0.2)
        """
        return self.axis('x').set_limits(begin, end, step)

    def set_ylim(self, begin=None, end=None, step=None):
        """
        Sets Y axis scale begin(From), end(To) and step(Increment)

        Parameters:
            begin (float or None): axis new From or Begin value.
            end (float or None): axis new To or End value.
            step (float or None): axis new Step or Increment value.

        Returns:
            New axis limits

        Examples:
            g = op.new_graph()
            g[0].set_ylim(1, 100, 20)
            g[0].set_ylim(begin=0)
        """
        return self.axis('y').set_limits(begin, end, step)

    def set_zlim(self, begin=None, end=None, step=None):
        """
        Sets Z axis scale begin(From), end(To) and step(Increment)

        Parameters:
            begin (float or None): axis new From or Begin value.
            end (float or None): axis new To or End value.
            step (float or None): axis new Step or Increment value.

        Returns:
            New axis limits

        Examples:
            g = op.new_graph()
            g[0].set_zlim(0, 5)
            g[0].set_zlim(step=1)
        """
        return self.axis('z').set_limits(begin, end, step)


    @property
    def xscale(self):
        """
        Property getter for X axis scale type.

        Parameters:

        Returns:
            Scale type of axis

        Examples:
            st = lay.xscale
        """
        return self.axis('x').scale

    @xscale.setter
    def xscale(self, scaletype):
        """
        Property setter for X axis scale type.

        Parameters:
            scaletype (int or str): Supported string value of scaltype:
                ['linear', 'log10', 'probability', 'probit', 'reciprocal', 'offset_reciprocal', 'logit', 'ln', 'log2']

        Returns:
            New scale type of x axis

        Examples:
            lay.xscale = 'log10'
        """
        self.axis('x').scale = scaletype
        return self.xscale

    @property
    def yscale(self):
        """
        Property getter for Y axis scale type.
        Parameters:
            none
        Returns:
            Scale type of axis
        Examples:
            st = lay.yscale
        """
        return self.axis('y').scale

    @yscale.setter
    def yscale(self, scaletype):
        """
        Property setter for Y axis scale type.
        Parameters:
            scaletype (int or str): Supported string value of scaltype:
                ['linear', 'log10', 'probability', 'probit', 'reciprocal', 'offset_reciprocal', 'logit', 'ln', 'log2']
        Returns:
            New scale type of y axis
        Examples:
            lay.yscale = 'log10'
        """
        self.axis('y').scale = scaletype
        return self.yscale

    @property
    def zscale(self):
        """
        Property getter for Y axis scale type.
        Parameters:
            none
        Returns:
            Scale type of axis
        Examples:
            st = lay.yscale
        """
        return self.axis('z').scale

    @zscale.setter
    def zscale(self, scaletype):
        """
        Property setter for Z axis scale type.
        Parameters:
            scaletype (int or str): Supported string value of scaltype:
                ['linear', 'log10', 'probability', 'probit', 'reciprocal', 'offset_reciprocal', 'logit', 'ln', 'log2']
        Returns:
            New scale type of z axis
        Examples:
            lay.zscale = 'log10'
        """
        self.axis('z').scale = scaletype
        return self.axis('z').scale

    def label(self, name):
        """
        Get a Label instance by name.

        Parameters:
            name (str): name of the label to be attached
        Returns:
            (Label)

        Examples:
            g = op.new_graph()
            g[0].label('XB').remove()
        """
        lb = self.obj.GraphObjects(name)
        if lb is None:
            return None
        return Label(lb, self.obj)

    def remove_label(self, label):
        """
        Remove a label from a layer.

        Parameters:
            label (Label or str): Instance of Label or name of label to remove

        Returns:
            None

        Examples:
            g = op.new_graph()
            g[0].remove_label('xb') # g[0] is 1st layer.
        """
        if isinstance(label, Label):
            label.remove()
        elif isinstance(label, str):
            self.remove_label(self.label(label))
        else:
            raise TypeError('"label"" must ba an instance of either str or Label.')

    def remove(self, obj: any):
        """
        remove object in the layer.

        Parameters:
            obj: Can be graph object or plot object

        Returns:
            None

        Examples:
            gl=op.find_graph()[0]
            label = gl.label('xb')
            label.remove()
        """
        if isinstance(obj, Label):
            self.remove_label(obj)
        elif isinstance(obj, Plot):
            self.remove_plot(obj)

    def plot_list(self):
        """
        Returns list of Plot objects in the layer.

        Parameters:

        Returns:
            (list)

        Examples:
            items = lay.plot_list()
            item = lay.plot_list()[0]
        """
        plist = []
        for dp in self.obj.DataPlots:
            plist.append(Plot(dp, self.obj))
        return plist

    def remove_plot(self, plot):
        """
        Removes plot from layer.

        Parameters:
            plot (Plot or int) Instance of Plot or index of plot to remove

        Returns:
            None

        Examples:
            lay.remove_plot(3)
        """
        if isinstance(plot, Plot):
            plot.remove()
        elif isinstance(plot, int):
            self.remove_plot(self.plot_list()[plot])
        else:
            raise TypeError('"plot"" must ba an instance of either Plot or int.')
    @staticmethod
    def _plot_type(type):
        if isinstance(type, int):
            return type
        if len(type) > 1:
            plttypes = {
                "line":'l',
                "scatter":'s',
                "linesymbol":'y',
                "column":'c',
                "contour":'contour',
                }
            type = plttypes[type]

        plottypes = {
            "?": 230,
            "l": 200,
            "s": 201,
            "y": 202,
            "c": 203,
            "contour": 226,
            }
        return plottypes[type]

    def _add_plot(self, ranges, type):
        if isinstance(ranges, str):
            return self.obj.AddPlotFromString(ranges, self._plot_type(type))
        return self.obj.AddPlot(ranges, self._plot_type(type), True)

    @staticmethod
    def _to_lt_str(col, wks):
        """return empty str if not valid, otherwise return LabTalk column index as str"""
        if isinstance(col,str):
            if len(col) == 0 or col == '#':
                return col
            temp = wks.lt_col_index(col)
            if temp < 1:
                return ''
            return str(temp)
        if not isinstance(col,int):
            raise ValueError('invalid column specification')
        if col < 0:
            return ''
        return str(col + 1)

    def add_plot(self, obj, coly=-1, colx=-1, colz=-1, type = '?', colyerr=-1, colxerr=-1):
        """
        Add plot to graph layer
        Parameters:
            obj(WSheet): worksheet to plot from, or a DataRange
            coly(int or str): Y column to plot
            colx(int or str): X column, it not specified, X column on the left, can use '#' to indicate use row number as X
            colz(int or str): Z column to plot
            type(str): 'l'(Line Plot) 's'(Scatter Plot) 'y' (Line Symbols) 'c' (Column) '?' auto(template)
            colyerr(int or str): Y Error column to plot
            colxerr(int or str): X Error column to plot
        Returns:
            (Plot): the newly added Plot object

        Examples:
            gl = op.find_graph()[0]
            wks = op.find_sheet('w','Book1')
            p = gl.add_plot(wks,'C')
            p.color = '#5f0'
            gl.rescale()
            gl.add_plot(wks,1,3)#C(x), B(y)
            gl.add_plot(wks,1,'#')#B(y) vs Row Numbers
        """
        wks = None
        if isinstance(obj, (origin_class('DataRange'), str)):
            dp = self._add_plot(obj, type)
        else:
            wks = obj
            colx = self._to_lt_str(colx, wks)
            coly = self._to_lt_str(coly, wks)
            colz = self._to_lt_str(colz, wks)
            colyerr = self._to_lt_str(colyerr, wks)
            colxerr = self._to_lt_str(colxerr, wks)
            if colz:
                if coly:
                    colspec = f'({colx}, {coly}, {colz})'
                else:
                    colspec = colz
            elif colyerr or colxerr:
                colspec = f'({colx}, {coly}, {colyerr}, {colxerr})'
            else:
                colspec = f'({colx}, {coly})'
            srange = wks.lt_range(False)
            dp = self._add_plot(f'{srange}!{colspec}', type)
        if dp is None:
            return None
        return Plot(dp, self.obj)

    def add_mplot(self, ms, z, x=-1, y=-1, cm=-1, type=103):
        '''
        plot a 3D parametric surface

        Parameters:
            ms (MSheet): matrix sheet with the data to plot
            z (int): matrix object index for Z
            x (int): matrix object index for X, must be > z
            y (int): matrix object index for Y, must be > z

        Examples:
            #assmues X,Y,Z contains the mesh grid data
            data=[]
            data.append(Z)
            data.append(X)
            data.append(Y)
            ms = op.new_sheet('m')
            ms.from_np(np.array(data))
            gl = op.new_graph(template='GLparafunc')[0]
            gl.add_mplot(ms, 0, 1, 2)
        '''
        plotadded = self.add_plot(ms, colz=z, type=type)
        if type != 103:
            return plotadded

        mo = ms.obj[z]
        moname = mo.DatasetName
        x = 0 if x < 0 else x + 1
        y = 0 if y < 0 else y + 1
        self.obj.LT_execute(f'set {moname} -zx {x};set {moname} -zy {y};')

        colormapname = ''
        if cm >= 0:
            mcm = ms.obj[cm]
            colormapname = mcm.DatasetName
            self.obj.LT_execute(f'set {moname} -b3c {colormapname};')

        return plotadded


class GPage(BasePage):
    """
    This class represent an Origin Graph Page, it holds an instance of a PyOrigin GraphPage
    """
    def __repr__(self):
        return 'GPage: ' + self.obj.GetName()

    def __getitem__(self, index):
        return GLayer(self.obj.Layers(index))

    def __iter__(self):
        for elem in self.obj.Layers:
            yield GLayer(elem)

    def save_fig(self, path='', type='auto', replace=True, width=0, ratio=0):
        """
        export to a file

        Parameters:
        -------
        path(str): if not specified, then to UFF, or if graph has theme, then last exported location in that graph.
                    If specifed, can include file name with extention, which will then control image type
        type(str): if auto, then use graph last exported settings, otherwise 'png', 'emf' etc
        replace(bool): if file existed, silently replace or not
        width(int): Pixcels. 0 will use last exported setting only if type=auto, if not auto, better specify this.
        ratio (int): Size Factor (%), for emf and svg

        Return:
        -------
            if success, returns the fullpath file name generated, otherwise an empty string

        Examples
        -------
        >>> g = op.find_graph('graph1')
        >>> g.save_fig(op.path() + 'test1.png', width=500)
        >>> g.save_fig()#use last GUI export graph settings remembered inside graph, which may include path

        """
        fname=''
        if path:
            path0 = path
            path, fname, ext=get_file_parts(path)
            if ext:
                if type not in ['auto', ext[1:]]:
                    raise ValueError('must not specify type and different from file extension')
                type = ext[1:]
            else:
                path = path0#d:\\test\\test, need to restore
                path = last_backslash(path,'t')#expgraph has trouble with path ending with \\
                fname=''
        exp = 'expgraph -sw'#silent warning messages
        if type=='auto':
            exp += ' -t <book>'
        else:
            exp += ' type:=' + str(type)

        if fname:
            exp += f' filename:="{fname}"'
        if replace:
            exp += ' overwrite:=replace'
        else:
            exp += ' overwrite:=skip'
        if width > 0:
            exp += f' tr1.Unit:=2 tr1.Width:={width}'
        elif ratio > 0 and type.lower() in ['emf', 'svg']:
            exp += f' tr.Advanced.Resolution:=1 tr1.Unit:=3 tr1.Width:={ratio}'
        if path:
            exp += f' path:="{path}"'
        LASTEXP = '__LASTEXP'
        po.LT_set_str(LASTEXP, '')
        self.obj.LT_execute(exp)
        return po.LT_get_str(LASTEXP)

    def add_layer(self, type = 0):
        """
        Adds a new layer to GPage. Type is based on types specified here:https://www.originlab.com/doc/X-Function/ref/layadd
        but should use the index equivalent of listed types (e.g. `righty` would be 2)

        Parameters:
            type (int): Type of layer to add. See description above foir how to deduce

        Returns:
            (GLayer): the newly added graph layer

        Examples:
            g = op.find_graph('graph1')
            gl=g.add_layer(2) # righty
            gl.xlim=[-2,1]
        """
        lt = 'layadd type:=' + str(type)
        self.obj.LT_execute(lt)
        nlayers = self.obj.Layers.GetCount()
        return GLayer(self.obj.Layers(nlayers-1))

    def copy_page(self, fmt, res=300, ratio=100, tb=False):
        '''
        Copy Graph Page as OLE object or Image

        Parameters:
            fmt (str): Image Format, can be PNG, EMF, DIB, HTML, JPG, or OLE
            res (int): DPI
            ratio (int): Size Factor (%)
            tb (bool): Background Transparency, for PNG only

        Returns:
            None
        examples:
            gl = op.find_graph('graph1')
            gl.copy_page('png', 600,100, True)
        '''
        if fmt.upper() == 'OLE':
            with CopyPageRatio(ratio) as _:
                self.method_int('copy', 'OLE')
        else:
            self.lt_exec(f'copyimg igp:={self.name} type:={fmt.lower()} tb:={1 if tb else 0} res:={res} ratio:={ratio}')
