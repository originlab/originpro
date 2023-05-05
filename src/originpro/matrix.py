"""
originpro
A package for interacting with Origin software via Python.
Copyright (c) 2020 OriginLab Corporation
"""
# pylint: disable=C0301,C0103,R0914,R0912
try:
    from .config import np, npdtype_to_orgdtype, orgdtype_to_npdtype
except ImportError:
    pass
from .config import oext, po
from .base import DSheet, DBook

class MSheet(DSheet):
    """
    This class represents an Origin Matrix Sheet, it holds an instance of a PyOrigin MatrixSheet.
    """
    def get_book(self):
        """
        Returns parent book of sheet.

        Parameters:

        Returns:
            (MBook)

        Examples:
            mb = ma.get_book().add_sheet()
        """
        return MBook(self._get_book())

    @property
    def depth(self):
        """
        Parameters:
            none
        Returns:
            return the number of matrix objects in the matrix sheet
        Examples:
            >>>ms = op.find_sheet('m')
            >>>ms.depth
        """
        return self.obj.GetNumMats()

    @depth.setter
    def depth(self, z):
        """
        set the number of matrix objects in the matrix sheet
        Parameters:
            z(int):number of matrix objects in the matrix sheet
        Returns:
            number of matrix objects in the matrix sheet
        Examples:
            ms=op.new_sheet('m', hidden=True)
            ms.depth = 100
            print(ms.depth)
        """
        self.obj.SetNumMats(z)
        return self.obj.GetNumMats()

    def from_np(self, arr, dstack=False, mv=None):
        """
        Set a matrix sheet data from a multi-dimensional numpy array. Existing data and MatrixObjects will be deleted.

        Parameters:
            arr (numpy array): 2D for a single MatrixObject, and 3D for multiple MatrixObjects (rows, cols, N)
            dstack (bool):   True if arr as row,col,depth, False if depth,row,col
            mv(float, int): if specified, to set the internal missing value for each MatrixObject. This is needed when arr contains nan and not double type
        Returns:
            None

        Examples:
            ms = op.new_sheet('m')
            arr = np.array([[[1, 2, 3], [4, 5, 6]], [[11, 12, 13], [14, 15, 16]]])
            ms.from_np(arr)
        """
        is_seq = isinstance(arr, (list, tuple))
        fmt = arr[0].dtype.type if is_seq else arr.dtype.type
        dfmt = npdtype_to_orgdtype.get(fmt)
        if dfmt is None:
            raise ValueError('Array Data Type not supported')
        if is_seq:
            if arr[0].ndim != 2:
                raise ValueError('Multiframe only not supported 2D array')
            depth = len(arr)
            rows, cols = arr[0].shape
        else:
            if arr.ndim < 2:
                raise ValueError('1D array not supported')
            if arr.ndim == 2:
                self.depth = 1
                row,col = arr.shape
                mat = self.obj.MatrixObjects(0)
                mat.DataFormat = dfmt
                if mv is not None:
                    self.set_float('col1.missing', mv)
                self.shape = row,col
                ret = mat.SetData(arr)
                if ret == 0:
                    print('matrix set data error')
                return
            if arr.ndim != 3:
                raise ValueError('array greater then 3D not supported')
            if dstack:
                rows, cols, depth = arr.shape
            else:
                depth, rows, cols = arr.shape
        self.depth = 1
        self.shape = rows, cols
        self.obj[0].DataFormat = dfmt
        if mv is not None:
            self.set_float('col1.missing', mv)
        self.depth = depth
        for i in range(depth):
            mo = self.obj[i]
            if dstack:
                mo.SetData(arr[:,:,i])
            else:
                mo.SetData(arr[i])

    def to_np2d(self, index=0, order='C'):
        """
        Transfers data from a single MatrixObject to a numpy 2D array.

        Parameters:
            index (int): MatrixObject index in the MatrixLayer
            order (str): Order of numpy array. 'C' for C-style row major order, 'F' for Fortran-style column major order

        Returns:
            (numpy array) 2D

        Examples:
            arr = ms.to_np2d(0)
            print(arr)
            arr = ms.to_np2d(0, 'R')
            print(arr)
        """
        mo = self.obj.MatrixObjects(index)
        return np.asarray(mo.GetData(), orgdtype_to_npdtype[mo.DataFormat], order)

    def from_np2d(self, arr, index=0):
        """
        Transfers data from a numpy 2D array into a single MatrixObject.

        Parameters:
            arr (numpy array) 2D
            index (int): MatrixObject index in the MatrixLayer

        Returns:
            None

        Examples:
            index = 0
            ms = op.find_sheet('m')         # a matrix must be active
            npdata = ms.to_np2d(index)      # get as numpy array the data from one matrix object
            npdata *= 10                    # multiply every element by 10
            ms.from_np2d(npdata, index)     # set the modified array into the matrix object
        """
        mo = self.obj.MatrixObjects(index)
        mo.SetData(arr)

    def to_np3d(self, dstack=False, order='C'):
        """
        Transfers data from a MatrixSheet to a numpy 3D array.

        Parameters:
            dstack (bool): True output arrays as row,col,depth, False if depth,row,col
            order (str): Order of numpy array. 'C' for C-style row major order, 'F' for Fortran-style column major order

        Returns:
            (numpy array) 3D

        Examples:
            arr=[]
            for i in range(10):
                tmp = np.arange(1,13).reshape(3,4)
                arr.append(tmp*(i+1))
            aa = np.dstack(arr)
            print(aa.shape)
            ma = op.new_sheet('m')
            ma.from_np(aa, True)

            bb = ma.to_np3d()
            print(bb.shape)
            mb = op.new_sheet('m')
            mb.from_np(bb)

            cc = ma.to_np3d(True)
            print(cc.shape)
            mc = op.new_sheet('m')
            mc.from_np(cc)
            mc.show_thumbnails()
        """
        m2d = []
        for mo in self.obj.MatrixObjects:
            m2d.append(np.asarray(mo.GetData(), orgdtype_to_npdtype[mo.DataFormat], order))
        if dstack:
            return np.dstack(m2d)
        return np.array(m2d)

    def show_image(self, show = True):
        """
        Show MatrixObjects as images or as numeric values.

        Parameters:
            show (bool): If True, show as images

        Returns:
            None

        Examples:
            ms.show_image()
            ms.show_image(False)
        """
        self.set_int("Image", show)

    def __show_contrll(self, show, slider):
        mbook = self.obj.GetParent()
        if not show:
            mbook.SetNumProp("Selector", 0)
        else:
            mbook.SetNumProp("Selector", 1)
            mbook.SetNumProp("Slider", slider)

    def show_thumbnails(self, show = True):
        """
        Show thumbnail images for a MatrixObjects.

        Parameters:
            show (bool): If True, show thumbnails

        Returns:
            None

        Examples:
            ms.show_thumbnails()
            ms.show_thumbnails(False)
        """
        self.__show_contrll(show, 0)


    def show_slider(self, show = True):
        """
        Show image slider for MatrixObjects.

        Parameters:
            show (bool): If True, show slider

        Returns:
            None

        Examples:
            mat.show_slider()
            mat.show_slider(False)
        """
        self.__show_contrll(show, 1)

    def get_missing_value(self, index=0):
        """
        get the internal missing value, which is needed when data type is not double.
        Parameters:
            index(int): matrix object index
        Returns:
            (float) missing value
        Examples:
            ms=op.find_sheet('m')
            print(ms.get_missing_value())
        """
        return self.get_float(f'col{index+1}.missing')

    def _xyobj(self):
        return self.obj if oext else self.obj[0]

    @property
    def xymap(self):
        """
        Get Matrix xy values.
        Parameters:
            none
        Returns:
            (list): x1, x2, y1, y2

        Examples:
            ms=op.find_sheet('M')
            x1, x2, y1, y2 = ms.xymap
        """
        return self._xyobj().GetXY()

    @xymap.setter
    def xymap(self, xy):
        """
        Set Matrix xy values.

        Parameters:
            xy(list): x1, x2, y1, y2
        Returns:
            (list): x1, x2, y1, y2
        Examples:
            ms=op.find_sheet('M')
            ms.xymap = x1, x2, y1, y2
        """
        return self._xyobj().SetXY(xy)

    @staticmethod
    def _getlabel(mo, type_ = 'L'):
        if len(type_) > 1:
            raise ValueError('Invalid label row character')
        dd = {
            'L': mo.GetLongName,
            'C': mo.GetComments,
            }
        func = dd[type_]
        return func()

    @staticmethod
    def _get_LT_label_name(type_):
        dd = {
            'L': 'LongName',
            'U': 'Units',
            'C': 'Comments',
            }
        return dd[type_]

    def get_label(self, index, type_ = 'L'):
        """
        Return a Matrix object label text.

        Parameters:
            index (int ): Matrix object index or 'x', 'y' for sheet XY labels
            type_ (str): A column label row character (see https://www.originlab.com/doc/LabTalk/ref/Column-Label-Row-Characters) or a user defined parameter name

        Returns:
            (str)

        Examples:
            ms=op.find_sheet('m')
            comment = ms.get_label('y','C')
        """
        if isinstance(index, int):
            mo = self.obj[index]
            return self._getlabel(mo, type_)
        if index in ['x','y']:
            name = self._get_LT_label_name(type_)
            return self.get_str(f'{index}.{name}')
        return ''

    def get_labels(self, type_ = 'L'):
        '''
        Return Matrix Objects label text.

        Parameters:
            type_ (str): A column label row character (see https://www.originlab.com/doc/LabTalk/ref/Column-Label-Row-Characters) or a user defined parameter name

        Returns:
            (list)

        Examples:
            ms=op.find_sheet('M')
            comments = ms.get_labels('C')
        '''
        return [self._getlabel(mo, type_) for mo in self.obj]

    @staticmethod
    def _setlabel(mo, val, type_ = 'L'):
        if len(type_) > 1:
            raise ValueError('Invalid label row character')
        dd = {
            'L': mo.SetLongName,
            'C': mo.SetComments,
            }
        func = dd[type_]
        return func(val)

    def set_label(self, index, val, type_ = 'L'):
        """
        Set Matrix object label text.

        Parameters:
            index (int): Matrix object index or 'x', 'y' for sheet XY labels
            val   (list): the text to set
            type_  (str): A column label row character (see https://www.originlab.com/doc/LabTalk/ref/Column-Label-Row-Characters) or a user defined parameter name
        Returns:
            none
        Examples:
            ms=op.find_sheet('m')
            ms.set_label('y', 'Lattitude')
        """
        if isinstance(index, int):
            mo = self.obj[index]
            self._setlabel(mo, val, type_)
            return
        if index in ['x','y']:
            name = self._get_LT_label_name(type_)
            self.set_str(f'{index}.{name}', val)
            return

    def set_labels(self, labels, type_ = 'L', offset=0):
        """
        Set Matrix objects label text.

        Parameters:
            labels (list): the text to set
            type_ (str): A column label row character (see https://www.originlab.com/doc/LabTalk/ref/Column-Label-Row-Characters) or a user defined parameter name
        Returns:
            none
        Examples:
            ms=op.find_sheet('m')
            ms.set_labels(['long name for col A', 'long name for col B'], 'L')
        """
        for ii, val in enumerate(labels[:self.depth]):
            self.set_label(ii + offset, val, type_)

    def from_img(self, img):
        """
        ss

        Parameters:
            img(IPage): input image page
        Returns:
            None
        Examples:
            ms = op.find_sheet('m')
            img = op.find_image('Image1')
            ms.from_img(img)
        """
        po.LT_execute(f'cv2mat img:=[{img.name}]1! mat:={self.lt_range(False)}')

class MBook(DBook):
    """
    This class represents an Origin Matrix Book, it holds an instance of a PyOrigin MatrixPage.
    """
    def _sheet(self, obj):
        return MSheet(obj)

    def add_sheet(self, name='', active=True):
        """
        add a new matrix sheet to the matrix book

        Parameters:
            name (str): the name of the new sheet. If not specified, default names will be used
            active (bool): Activate the newly added sheet or not

        Return:
            (MSheet)

        Examples:
            mb = ma.get_book().add_sheet('Dot Product')
            print(mb.shape)
        """
        return MSheet(self._add_sheet(name, active))

    def show_image(self, show = True):
        """
        similar to MSheet, but set all sheets in matrix book

        Parameters:
            show (bool): If True, show as images

        Returns:
            None

        Examples:
            mb = op.find_book('m', 'MBook1')
            mb.show_image()
        """
        self.set_int("Image", show)
