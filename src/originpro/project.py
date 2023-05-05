"""
originpro
A package for interacting with Origin software via Python.
Copyright (c) 2020 OriginLab Corporation
"""
# pylint: disable=C0301,C0103,W0622
from typing import Union, List
from .config import po, oext
from .utils import get_file_ext, active_obj, path, origin_class
from .worksheet import WSheet, WBook
from .matrix import MSheet, MBook
from .graph import GPage, GLayer
from .base import BasePage
from .image import IPage

_WBOOK_TYPE = 'w'
_MBOOK_TYPE = 'm'
_GPAGE_TYPE = 'g'
_IPAGE_TYPE = 'i'
_PAGE_CLS = {
    _WBOOK_TYPE: WBook,
    _MBOOK_TYPE: MBook,
    _GPAGE_TYPE: GPage,
    _IPAGE_TYPE: IPage,
}
_LAYER_CLS = {
    _WBOOK_TYPE: WSheet,
    _MBOOK_TYPE: MSheet,
    _GPAGE_TYPE: GLayer,
}
_PAGE_TYPES = {
    _WBOOK_TYPE: po.OPT_WORKSHEET if oext else po.PGTYPE_WKS,
    _MBOOK_TYPE: po.OPT_MATRIX if oext else po.PGTYPE_MATRIX,
    _GPAGE_TYPE: po.OPT_GRAPH if oext else po.PGTYPE_GRAPH,
}
try:
    _PAGE_TYPES[_IPAGE_TYPE] = po.OPT_IMAGE if oext else po.PGTYPE_IMAGE
except AttributeError:
    pass
_PO_PAGE_TYPES = {v:k for k, v in _PAGE_TYPES.items()}
def _get_from_type(items, type):
    item = items.get(type)
    if item is None:
        raise ValueError("Book/Sheet type can only be 'w'(Worksheet) or 'm'(Matrix)")
    return item

def _type_from_ext(ext):
    ext = ext.lower()
    if ext in ['.ogw', '.ogwu']:
        return _WBOOK_TYPE
    if ext in ['.ogm', '.ogmu']:
        return _MBOOK_TYPE
    if ext in ['.ogg', '.oggu']:
        return _GPAGE_TYPE
    raise ValueError("Invalid file extension")

def _is_good_sn(name):
    nn = len(name)
    if nn == 0 or nn > 21:
        return False
    if '_' in name:
        return False

    return name.isidentifier()

#return PyOrigin Page
def _new_page(type, lname, template, hidden):
    type2 = _get_from_type(_PAGE_TYPES, type)
    if template is None:
        template = ''
    elif not template:
        template = 'Origin'
    else:
        ext = get_file_ext(template)
        if len(ext) > 0 and ext[1:3] != 'ot':
            raise ValueError('extension specfiied is not a template file')
    visible = po.CREATEOPT_HIDDEN if hidden else po.CREATEOPT_VISIBLE
    CREATE_NO_DEFAULT_TEMPLATE = 0x00080000
    visible |= CREATE_NO_DEFAULT_TEMPLATE
    sname = lname if _is_good_sn(lname) else ''
    book = po.CreatePage(type2, sname, template, visible)
    if oext:
        book = po.Pages[book]
    if book is not None:
        if len(lname) > 0 and len(sname)==0:
            book.SetLongName(lname)
    return book

def _new_page2(type, lname, template, hidden):
    cls = _get_from_type(_PAGE_CLS, type)
    page = _new_page(type, lname, template, hidden)
    return cls(page) if page else None

def _make_page(page, type_=''):
    try:
        ptype = _PO_PAGE_TYPES[page.GetType()]
        if not type_ or type_ == ptype:
            if isinstance(page, origin_class('PageBase')):
                page = po.Pages(page.GetName())
            return _PAGE_CLS[ptype](page)
    except KeyError:
        pass
    return None

def new_book(type=_WBOOK_TYPE, lname='', template='', hidden=False) -> Union[WBook, MBook]:
    """
    Create a new workbook or matrixbook.

    Parameters:
        type(str): Specify 'w' for WBook object or 'm' for MBook object
        lname (str): Long Name of the book
        template (str): Template name. May exclude extension. Does not support OGWU files (e.g. analysis templates). In that case, use load_book.
        hidden (bool): True makes newly created book hidden

    Returns:
        (WBook or MBook or None)

    Examples:
        wb1 = op.new_book()
        wb2 = op.new_book('w', 'My Template')
        mb = op.new_book('m', hidden=True)

    See Also:
        load_book
    """
    return _new_page2(type, lname, template, hidden)

def new_graph(lname='', template='', hidden=False) -> GPage:
    """
    Create a new empty graph optionally from a template.

    Parameters:
        lname (str): Long Name of the graph
        template (str): Template name. May exclude extension. If not specified, use origin.otp.
        hidden (bool): True makes newly created graph hidden

    Returns:
        (GPage or None)

    Examples:
        g1 = op.new_graph()
        g2 = op.new_graph('My Graph')
        g3 = op.new_graph(template=op.path('e') + '3Ys_Y-Y-Y.otp')
    """
    return _new_page2(_GPAGE_TYPE, lname, template, hidden)

def new_image(lname='', hidden=False) -> IPage:
    """
    Create a new image window

    Parameters:
        lname (str): Long Name of the new window
        hidden (bool): True makes newly created window hidden
    Returns:
        IPage or None
    Examples:
        im = op.new_image()
    """
    return _new_page2(_IPAGE_TYPE, lname, None, hidden)

def new_sheet(type=_WBOOK_TYPE, lname='', template='', hidden=False) -> Union[WSheet, MSheet]:
    """
    Create a new work or matrixbook and return the first sheet as a WSheet or MSheet.

    Parameters:
        type (str): Specify 'w' for WBook object or 'm' for MBook object
        lname (str): Long Name of the book
        template (str): Template name. May exclude extension
        hidden (bool): True makes newly created book hidden

    Returns:
        (WSheet or MSheet or None)

    Examples:
        wks1 = op.new_sheet()
        wks2 = op.new_sheet('w', 'My Template.otwu')
        mxs = op.new_sheet('m', hidden=True)
    """
    book = _new_page(type, lname, template, hidden)
    return _LAYER_CLS[type](book.Layers(0)) if book else None

def _get_item(coll, index):
    """WorksheetPages etc has no index, and no slice"""
    i=0
    for x in coll:
        if i==index:
            return x
        i+=1
    return None

def _get_page(type, index):
    if type ==_WBOOK_TYPE:
        fnGetPages = po.GetWorksheetPages
    elif type ==_MBOOK_TYPE:
        fnGetPages = po.GetMatrixPages
    elif type ==_GPAGE_TYPE:
        fnGetPages = po.GetGraphPages
    elif type ==_IPAGE_TYPE:
        fnGetPages = po.GetImagePages
    else:
        raise ValueError('Invalid page type')
    return _get_item(fnGetPages(), index)

def _get_sheet(index, type):
    bk = _get_page(type, index)
    return bk.Layers(0) if bk else None

def get_page(type, index=0) -> Union[WBook, MBook, GPage, IPage]:
    """
    get WBook, MBook, GPage, IPage by index
    Parameters:
        none
    Returns:
        WBook or MBook or GPage or IPage None
    Examples:
        w=op.get_page('w', 0)//there should a workbook exist

    """
    page = _get_page(type, index)
    if page is None:
        return None
    cls = _get_from_type(_PAGE_CLS, type)
    return cls(page)

def find_sheet(type=_WBOOK_TYPE, ref='') -> Union[WSheet, MSheet]:
    """
    Find the Sheet referenced by ref (an Origin range string). Default will return active worksheet.

    Parameters:
        type (str): Specify 'w' for WBook object or 'm' for MBook object
        ref (str or int): [book]sheet, an Origin range specification. Can also be just book name to assume active sheet,
                    so the following are the same if book has only one sheet
                    '[book1]1', '[book1]1!', 'book1'

                    You may also pass in an integer for the book index, like 0 for the first book

    Returns:
        (WSheet or MSheet or None)

    Examples:
        wks1 = op.find_sheet()   #when active book that is a workbook
        wks2 = op.find_sheet('w', '[Book1]Sheet2')   #when you need a specific sheet
        m1 = op.find_sheet('m')   #when active is a matrix book
        m2 = op.find_sheet('m','MBook1')   #when there is only one sheet, use simpler notation
        wks3 = op.find_sheet('w',0)# see if there is any workbook at all
    """
    if isinstance(ref, int):
        ms = _get_sheet(ref, type)
    else:
        find = _get_from_type({
            _WBOOK_TYPE: po.FindWorksheet,
            _MBOOK_TYPE: po.FindMatrixSheet,
        }, type)
        ms= find(ref)
    return _LAYER_CLS[type](ms) if ms else None

def find_book(type=_WBOOK_TYPE, name='') -> Union[WBook, MBook]:
    """
    Find the work or matrixbook by name (short name) and return a WBook or MBook object.

    Parameters:
        type (str): Specify 'w' for WBook object or 'm' for MBook object
        name (str or int): Name of book. If empty, then active book. If int, then from the collection of books by index

    Returns:
        (WBook or MBook or None)

    Examples:
        wb = op.find_book()#if active book is a workbook
        mb = op.find_book('m', 'MBook2')
    """
    s=find_sheet(type,name)
    return s.get_book() if s else None

def _find_page(name, typestr, type_, pagecls):
    if isinstance(name, int):
        page = _get_page(typestr, name)
    else:
        if name:
            page = po.Pages(name)
        else:
            page = active_obj('Page')

    if page is None or page.GetType() != type_:
        return None

    return pagecls(page)

def find_graph(name='') -> GPage:
    """
    Find the named graph (short name) and return a GPage object.

    Parameters:
        name (str or int) Name of graph. If empty, then active graph, if int, then index into graph page collection

    Returns:
        (GPage or None)

    Examples:
        g = op.find_graph('Graph2')
        glayer=op.find_graph()[0]
    """
    return _find_page(name, _GPAGE_TYPE, po.OPT_GRAPH, GPage)

def find_image(name='') -> IPage:
    """
    Find the named Image Window and return a IPage object.

    Parameters:
        name (str or int) Name of Image Window. If empty, then active Image Page, int, then index into Image Page collection

    Returns:
        (IPage or None)

    Examples:
        import numpy as np
        im = op.find_image('Image1')
        data = im.to_np()
        dataUpsideDown = np.flip(data, 1)
        im.from_np(dataUpsideDown)
    """
    return _find_page(name, _IPAGE_TYPE, po.OPT_IMAGE, IPage)


def load_book(fname) -> Union[WBook, MBook]:
    r"""
    Loads a work or matrixbook from file and returns a WBook or MBook object.

    Parameters:
        fname (str): File path and name. If file name only, the load from UFF

    Returns:
        (WBook or MBook or None)

    Examples:
        wb1 = op.load_book('My Analysis Template.ogwu')#from user file folder
        wb2 = op.load_book(op.path('e')+r'Samples\Batch Processing\Peak Analysis.ogw')
    """
    ext = get_file_ext(fname)
    type = _type_from_ext(ext)
    if type == _GPAGE_TYPE:
        raise ValueError('not supported to load a graph, use open instead')
    book = po.LoadPage(fname)
    return _PAGE_CLS[type](book) if book else None

def graph_list(select='f', inc_embed=False) -> List[GPage]:
    """
    Returns a list object of GPages representing graphs in the current folder, graphs open in current folder, or graphs in project.

     Parameters:
        select (str): Specify 'f' for current folder, 'o' for graphs open in current folder, or 'p' for graphs in project
        inc_embed (bool): Include embedded graphs in the list, this is supported for 'p' only

    Returns:
        (list) list of GPage objects

    Examples:
        graphs1 = op.graph_list('p', True)
        graphs2 = op.graph_list('f')
    """
    if select not in ['f', 'p', 'o']:
        raise ValueError("select 'f'(folder) 'p'(project) 'o'(open in folder) only")
    glist=[]
    if select in ['f', 'o']:
        if inc_embed:
            raise ValueError("inc_embed only if select 'p'.")

        Folder = active_obj('Folder')
        for page in Folder.PageBases():
            if not inc_embed and page.GetNumProp('isEmbedded'):
                continue
            if select == 'o' and not BasePage(page).is_open():
                continue
            if page.GetType() == po.OPT_GRAPH:
                glist.append(GPage(page))
    else:
        for page in po.GraphPages:
            if not inc_embed and page.GetNumProp('isEmbedded'):
                continue

            glist.append(GPage(page))

    return glist

def pages(type_='') -> Union[WBook, MBook, GPage, IPage]:
    """
    All pages in project.
    Parameters:
        type_ (str): Page type, can be 'w', 'm', 'g', 'i'
    Returns:
        Page Objects
    Examples:
        wps=op.pages('w')
        w1=next(wps)
        wshet=w1[0]
    """
    for page in po.GetPages():
        try:
            ptype = _PO_PAGE_TYPES[page.GetType()]
        except KeyError:
            continue
        if not type_ or type_ == ptype:
            yield _PAGE_CLS[ptype](page)

def open(file, readonly=False, asksave=False):
    r"""
    Opens an Origin project file.

    Parameters:
        file (str): File path and name
        readonly (bool): Opern the file as read-only
        asksave (bool): If True, prompt user to save current project is it is modified

    Returns:
        (bool) True if project is successfully loaded

    Examples:
        op.open('C:\path\to\My Project.opju')
    """
    if not asksave:
        po.LT_execute('doc -s')

    return po.Load(file, readonly)

def new(asksave=False):
    """
    Starts a new project.

    Parameters:
        asksave (bool)P: If True, prompt user to save current project is it is modified

    Returns:
        None

    Examples:
        op.new()
        op.new(True)
    """
    if not asksave:
        po.LT_execute('doc -s')

    po.LT_execute('doc -nt')

def save(file=''):
    R"""
    Saves the current project. If no file name given, prompt to Save As.

    Parameters:
        file (str): Path and file name to save the project as. If blank, the prompt with Save As...

    Returns:
        (bool) True if project is successfully saved

    Examples
        op.save('C:\path\to\My Project.opju')
        op.save()
    """
    if len(file)==0:
        if len(path('p'))==0:
            raise ValueError('must supplied a path if project not saved yet')
        po.LT_execute('save')
        return False
    return po.Save(file)
