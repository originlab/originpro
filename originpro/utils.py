"""
originpro
A package for interacting with Origin software via Python.
Copyright (c) 2020 OriginLab Corporation
"""
# pylint: disable=C0103,W0622,W0621
import os
import xml.etree.ElementTree as ET
from .config import po, oext

PATHSEP = os.path.sep

def lt_float(formula):
    """
    get the result of a LabTalk expression

    Parameters:
        formula (str): any LaTalk expression

    Examples:
        #Origin Julian days value
        >>>op.lt_float('date(1/2/2020)')
        #get Origin version number
        >>>op.lt_float('@V')

    See Also:
        get_lt_str, lt_int
    """
    return po.LT_evaluate(formula)

def lt_int(formula):
    """
    get the result of a LabTalk expression as int, see lt_float()

    Examples:
        >>> op.lt_int('color("green")')

    See Also:
        get_lt_str, lt_float
    """
    try:
        return int(lt_float(formula))
    except ValueError:
        return 0

def get_lt_str(vname):
    """
    return a LabTalk string variable value. To get LabTalk numeric values, use lt_int or lt_float

    Examples:
        #AppData path for the installed Origin
        >>> op.get_lt_str('%@Y')
    See Also:
        lt_int, lt_float
    """
    return po.LT_get_str(vname)


def set_lt_str(vname, value):
    """
    sets a LabTalk string variable value.

    Examples:
        fpath = op.file_dialog('*.log')
        op.set_lt_str('fname', fpath)
        tmp=op.get_lt_str('fname')
        print(tmp)
    See Also:
        get_lt_str
    """
    return po.LT_set_str(vname, value)

def lt_exec(labtalk):
    """
    run LabTalk script
    """
    return po.LT_execute(labtalk)

def messagebox(msg, cancel=False):
    """
    open a message box
    Parameters:
        msg(str): the text to prompt
        cancel(bool): True if OK Cancel, False if just OK

    Return:
        False if has cancel button and user click Cancel

    Examples:
        nn = op.messagebox('this is a test', True)
        if not nn:
            op.messagebox('you clicked cancel')
        else:
            op.messagebox('you click ok')
    """
    if cancel:
        return lt_exec(f'type -c "{msg}"')
    return lt_exec(f'type -b "{msg}"')

def set_lt_var(name, value):
    """
    sets a LabTalk numeric variable value. This is usually used for setting system variables

    Example:
        op.set_lt_var("@IAS",5)#set import using multi-thread for files 5M or larger
    See Also:
        lt_float, set_lt_str
    """
    po.LT_set_var(name, value)

def attach():
    'Attach to exising Origin instance'
    if oext:
        po.Attach()

def detach():
    'Detach Origin instance'
    if oext:
        po.Detach()

def exit():
    """
    exit the application
    """
    if oext:
        po.Exit()
    else:
        lt_exec('exit')


def get_show():
    """
    If the Application is visible or not
    """
    return lt_int("@VIS") > 0

def set_show(show = True):
    """
    Show or Hide the Application
    """
    val = 100 if show else 0
    set_lt_var("@VIS", val)

def ocolor(rgb):
    """
    convert color to Origin's internal OColor

    Parameters:
        rgb: names or index of colors supported in Origin.
                      name          index    (Red, Green, Blue)
                      'Black'           1       000,000,000
                      'Red'             2       255,000,000
                      'Green'           3       000,255,000
                      'Blue'            4       000,000,255
                      'Cyan'            5       000,255,255
                      'Magenta'         6       255,000,255
                      'Yellow'          7       255,255,000
                      'Dark Yellow'     8       128,128,000
                      'Navy'            9       000,000,128
                      'Purple'          10       128,000,128
                      'Wine'            11      128,000,000
                      'Olive'           12      000,128,000
                      'Dark Cyan'       13      000,128,128
                      'Royal'           14      000,000,160
                      'Orange'          15      255,128,000
                      'Violet'          16      128,000,255
                      'Pink'            17      255,000,128
                      'White'           18      255,255,255
                      'LT Gray'         19      192,192,192
                      'Gray'            20      128,128,128
                      'LT Yellow'       21      255,255,128
                      'LT Cyan'         22      128,255,255
                      'LT Magenta'      23      255,128,255
                      'Dark Gray'       24      064,064,064
             it can be in formmat as well, for example, '#f00' for red.
             when the input is a tuple, it should be
             if rgb is tuple of intergers between 0 and 255,
             the color is set by RGB (Red, Green, Blue).

    Returns:
        (int) OColor
    """
    if isinstance(rgb, str):
        orgb = lt_int(f'color({rgb})')
    elif isinstance(rgb, int):
        orgb = rgb
    elif isinstance(rgb, (list, tuple)):
        orgb = lt_int(f'color({int(rgb[0])}, {rgb[1]}, {rgb[2]})')
    else:
        raise ValueError(f'the color value of {rgb} cannot be recognized.')

    return orgb
def to_rgb(orgb):
    """
    convert an Origin OColor to r, g, b

    Parameters:
        orgb(int): OColor from Origin's internal value

    Returns:
        (tuple) r,g,b
    """
    rgb = lt_int(f'ocolor2rgb({orgb})')
    return int(rgb%256), int(rgb//256%256), int(rgb//256//256%256)

def get_file_ext(fname):
    R"""
    Given a full path file name, return the file extension.

    Parameters:
        fname (str): Full path file name

    Returns:
        (str) File extension

    Examples:
        ext = op.get_file_ext('C:\path\to\somefile.dat')
    """
    if len(fname) == 0:
        return ''
    return os.path.splitext(fname)[1]

def get_file_parts(fname):
    R"""
    Given a full path file name, return the path, file name, and extension as a Python list object.

    Parameters:
        fname (str): Full path file name

    Returns:
        (list) Contains path, file name, and extension

    Examples:
        parts = op.get_file_parts('C:\path\to\somefile.dat')
    """
    if len(fname) == 0:
        return ['','','']
    path_, filename = os.path.split(fname)
    fname, ext = os.path.splitext(filename)
    return [path_, fname,  ext]


def last_backslash(fpath, action):
    """
    Add or trim a backslash to/from a path string.

    Parameters:
        fpath (str): Path
        action (str): Either 'a' for add backslash or 't' for trim backslash

    Returns:
        (str) Path either with added backslash or without trimmed backslash

    Examples:
        >>>op.last_backslash(op.path(), 't')
    """

    if len(fpath) < 3:
        raise ValueError('invalid file path')
    if not action in ['a', 't']:
        raise ValueError('invalid action')

    last_char = fpath[-1]
    if action == 'a':
        if last_char == PATHSEP:
            return fpath
        return fpath + PATHSEP
    assert action == 't'
    if not last_char == PATHSEP:
        return fpath
    return fpath[:-1]


def path(type = 'u'):
    r"""
    Returns one of the Origin pre-defned paths: User Files folder, Origin EXe folder,
    project folder, Project attached file folder.

    Parameters:
        type (str): 'u'(User Files folder), 'e'(Origin Exe folder), 'p'(project folder),
                    'a'(Attached file folder), 'c'(Learning Center)

    Returns:
        (str) Contains folder path

    Examples:
        uff = op.path()
        op.open(op.path('c')+ r'Graphing\Trellis Plots - Box Charts.opju')
    """
    if type == 'p':
        return get_lt_str('%X')
    if type == 'c':
        return os.path.join(get_lt_str('%@D'), 'Central' + PATHSEP)
    if type == 'a':
        return get_lt_str('SYSTEM.PATH.PROJECTATTACHEDFILESPATH$')
    path_types = {
        'u':po.APPPATH_USER if oext else po.PATHTYPE_USER,
        'e':po.APPPATH_PROGRAM if oext else po.PATHTYPE_SYSTEM,
        }
    otype = path_types.get(type, None)
    if otype is None:
        raise ValueError('Invalid path type')

    fnpath = po.Path if oext else po.GetPath
    return fnpath(otype)

def wait(type = 'r', sec=0):
    """
    Wait for recalculation to finish or a specified number of seconds.

    Parameters:
        type (str): Either 'r' to wait for recalculation to finish or
                    's' to wait for specified seconds
        sec (float): Number of seconds to wait is 's' specified for type

    Returns:
        None

    Examples:
        op.wait()#wait for Origin to update all the recalculations
        op.wait('s', 0.2)#gives 0.2 sec for graphs to finish updating
    """
    if type=='r':
        po.LT_execute('run -p au')
    elif type == 's':
        po.LT_execute(f'sec -p {sec}')
    else:
        raise ValueError('must be r or s')

def file_dialog(type, title=''):
    """
    open a file dialog to pick a single file
    Parameters:
        type (str): 'i' for image, 't' for text, 'o' for origin, or a file extension like '*.png'

    Returns:
        if user cancel, an empty str, otherwise the selected file path
    Examples:
        fn=op.file_dialog('o')
        fn=op.file_dialog('*.png;*.jpg;*.bmp')
    """
    if not isinstance(type, str) or len(type)==0:
        raise ValueError('type must be specified')
    if type.find('*') >= 0:
        type_ = type
    else:
        types = {'i': 'cvImageImp','t': 'ASCIIEXP','o':'OriginImport'}
        type_ = types[type]

    po.LT_execute(f'__fname_for_py$="";dlgfile fname:=__fname_for_py group:="{type_}"'
                   f' title:="{title}"')
    fname=get_lt_str('__fname_for_py$')
    po.LT_execute('del -vs __fname_for_py$')
    return fname

def origin_class(name):
    'Get Origin base class'
    if not oext:
        name = 'CPy' + name
    return getattr(po, name)

def active_obj(name):
    'Get active object'
    activeobj = getattr(po, 'Active' + name)
    return activeobj if oext else activeobj()

def color_col(offset=1, type='m'):
    """
    Generate Origin's internal OColor to use in data plot's color setting
    Parameters:
        offset (int): worksheet column offset to the plot's Y column
        type (str): 'm' for Colormap, 'n' = Indexing, 'r' = RGB
    Returns:
        OColor
    Examples:
        plot.color = op.color_col()# use next column to Y as color map values
        plot.color = op.color_col(1,'n') #use index color, column needs to contain 1,2,3 etc
        plot.colormap="fire"
    """
    return lt_int(f'color({offset}, {type})')

def modi_col(offset=1):
    """
    Generate Origin's internal modifier (uint) value to use in data plot's various setting
    Parameters:
        offset (int): worksheet column offset to the plot's Y column
    Returns:
        uint
    Examples:
        plot.symbol_size = op.modi_col(1)# use next column to Y as symbol size
        plot.symbol_kind = op.modi_col(2)
    """
    return lt_int(f'modifier({offset})')

def org_ver():
    'Origin Version as float'
    return po.LT_get_var('@V')

class _LTTMPOUTSTR:
    '''Receive temp string from Labtalk output'''
    def __init__(self, text='', suffix=''):
        self.name = '__PYLTOUTSTR' + suffix
        self.text = text

    def __enter__(self):
        po.LT_execute(f'string {self.name}{"=" + self.text if self.text else ""};')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        po.LT_execute(f'del -al {self.name}')

    def get(self):
        'Get temp string name'
        return po.LT_get_str(f'{self.name}')


def make_DataRange(*args, rows=None):
    'Make Origin DataRange object'
    ranges = po.NewDataRange() if oext else origin_class('DataRange')()
    subs = []
    subrows = None

    def addonerange():
        if subs:
            nonlocal subrows
            if subrows is None and rows is not None:
                subrows = rows
            r1_ = 0
            r2_ = -1
            if subrows:
                r1_, r2_ = subrows
                r1_ -= 1
                r2_ -= 1
            for sub in subs:
                stype = sub[0]
                col = sub[1]
                if isinstance(col, origin_class('MatrixObject')):
                    ranges.AddMatrix(col.GetParent(), col.GetIndex())
                else:
                    if isinstance(col, tuple):
                        wks, col = col
                        col = wks._find_col(col)
                        wks = wks.obj
                    else:
                        wks = col.GetParent()
                    ncol = col.GetIndex()
                    ranges.Add(stype, wks, r1_, ncol, r2_, ncol)
            ranges.Add("S", None, 0, 0, 0, 0)
            subs.clear()
            subrows = None

    numargs = len(args)
    i = 0
    while i < numargs:
        desig = args[i].upper()
        if desig in ('X', 'Y', 'Z'):
            i += 1
            subs.append((desig, args[i]))
        elif desig == 'S':
            addonerange()
        elif desig == 'ROWS':
            i += 1
            subrows = args[i]
        i += 1
    addonerange()

    return ranges

# something unlikely to be a real node's tag name prefix'
_TREE_NODE_GET_ATTRIBUTES_KEY_PREFIX = '___'

def attrib_key(name):
    'Make attribute key from name'
    return _TREE_NODE_GET_ATTRIBUTES_KEY_PREFIX + name

def _tree_node_get_attributes_key_for_root():
    return 'root'

def _tree_dict_is_key_attributes(key):
    if key.startswith(_TREE_NODE_GET_ATTRIBUTES_KEY_PREFIX):
        return key[len(_TREE_NODE_GET_ATTRIBUTES_KEY_PREFIX):]
    return ''

def _tree_node_name_to_attributes_key_name(nodename):
    strAttsKeyName = _TREE_NODE_GET_ATTRIBUTES_KEY_PREFIX + nodename
    return strAttsKeyName

def _dict_to_xml_element_atts(dd, parent, key):
    attkey = _tree_node_name_to_attributes_key_name(key)
    if attkey in dd:       # does the dictionary key with the attributes exist?
        parent.attrib = dd[attkey].copy()

def _dict_to_xml_element(dd, parent, bAttributes):
    for k, v in dd.items():
        if bAttributes:
            attr = _tree_dict_is_key_attributes(k)
            if attr:
                parent.set(attr, str(v))
                continue
        child = ET.SubElement(parent, k)
        if isinstance(v,  dict):
            _dict_to_xml_element(v, child, bAttributes)
        else:
            child.text = str(v)
        #if bAttributes:
            #_dict_to_xml_element_atts(dd, child, k)


def _dict_to_xml(dd, bAttributes = False):
    """
    Converts dictionary dd to an xml tree, then converts the xml tree to an xml string
    and returns it.
    Parameters:
        dd (dictionary)
    Returns:
        xml string obtained from xml tree obtained from dd
    Example:
    def prepare_dict():
        dictsub = {"KeyOne":"OneValue", "KeyTwo":-0.0987, "KeyThree":345678}
        dictret = {"FirstKey":"FirstValue", "SecondKey":99.88, "ThirdKey":dictsub, "FourthKey":-543}
        return dictret

    thedict = prepare_dict()
    xml = op._dict_to_xml(thedict)
    print(xml)
    """
    root = ET.Element('root')
    _dict_to_xml_element(dd, root, bAttributes)
    if bAttributes:
        _dict_to_xml_element_atts(dd, root, _tree_node_get_attributes_key_for_root())
    strxml = ET.tostring(root, encoding='utf8', method='xml').decode()
    return strxml

def lt_dict_to_tree(dd, treename, add_tree = False, check_attributes = False):
    """
    Converts dictionary dd to an xml tree string and sets the value of a LabTalk tree variable to
    to the xml tree string. If bAddTreeVar is False and the tree variable does not already exist,
    the tree variable will not be added. Pass True as bAddTreeVar if you want to make sure that
    the tree variable is added first if it does not exist.
    Parameters:
        dd (dictionary)
        treevarname (str) the name of the tree variable
        bAddTreeVar If True, the tree variable will be added if it does not exist
    """
    strxml = _dict_to_xml(dd, check_attributes)
    strTempLTStringVar = '__strpytempvar'
    po.LT_set_str(strTempLTStringVar, strxml)   # set the xml string into a temp. LT string variable
    if add_tree:
        po.LT_execute(f'tree {treename}')
    strLTexecute = (f'doc.settreevar({treename},'
                    f'{strTempLTStringVar}$);'
                    f'del -vs {strTempLTStringVar};')
    po.LT_execute(strLTexecute)


def _tree_node_attributes_to_dict(dd, node, bRoot = False):
    atts = node.attrib      # this is a dictionary of attributes
    if atts:
        dictAtts = atts.copy()
        name = _tree_node_get_attributes_key_for_root() if bRoot else node.tag
        dd[_tree_node_name_to_attributes_key_name(name)] = dictAtts


def _tree_to_dict(dd, node, bAttributes=False):
    if any(True for _ in node):
        dd2 = {}
        for child in node:
            _tree_to_dict(dd2, child, bAttributes)
        dd[node.tag] = dd2
    else:
        text = node.text
        if text is None:
            dd[node.tag]='' # /// ML 04/02/2021 Empty nodes need to be preserved
        else:
            try:
                dd[node.tag] = float(text)
            except ValueError:
                dd[node.tag] = text

    if bAttributes:
        _tree_node_attributes_to_dict(dd, node)

def lt_tree_to_dict(name, add_attributes=False):
    """
    Get Labtalk tree as dict
    Parameters:
        name (str): Name of the Labtalk tree
        add_attributes(bool): add the attributes from the tree as nodes
    Returns:
        dict to hold Labtalk tree content
    Examples:
        wks = op.new_sheet()
        data = [1,2,3,4,5]
        wks.from_list(0, data)
        wks.from_list(1, data)
        op.lt_exec('fitlr (1,2)')
        dd = op.lt_tree_to_dict('fitlr')
    """
    name = name.upper()
    with _LTTMPOUTSTR(name) as pp:
        xml = pp.get()
        if xml == name:
            return None
        tr = ET.fromstring(xml)
        dd = {}
        for node in tr:
            _tree_to_dict(dd, node, add_attributes)

        if add_attributes:
            # for root it cannot be a sibling of root since
            # root does not have siblings, so it must be a special
            # dictionary entry of the root dictionary
            _tree_node_attributes_to_dict(dd, tr, True)

        return dd

def lt_empty_tree():
    'An empty Labtalk tree'
    return ET.Element('OriginStorage')

def lt_delete_tree(name):
    'Delete a Labtalk tree'
    po.LT_execute(f'del -vt {name}')

def evaluate_FDF(ffname, indepvars, parameters):
    """
    Evaluate FDF function
    Parameters:
        ffname (str): Name of the Fitting Function
        indepvars(list): Independent Variables values, can be list of list if multiple independents
        parameters(list): Parameter values
    Returns:
        A list of Dependent Variable values
    Examples:
        vx = [1, 2, 3]
        vy = op.evaluate_FDF('Gauss', vx, [1, 2, 3, 4])
    """
    return po.EvaluateFDF(ffname, indepvars, parameters)
