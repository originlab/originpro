"""
originpro
A package for interacting with Origin software via Python.
Copyright (c) 2021 OriginLab Corporation
"""
# pylint: disable=C0103,C0301
try:
    from .config import np, orgdtype_to_npdtype
except ImportError:
    pass
from .base import BasePage
from .graph import GLayer
from .config import po

class IPage(BasePage):
    """
    This class represents an Origin Image Window, it holds an instance of a PyOrigin ImagePage
    """
    def __repr__(self):
        return 'IPage: ' + self.obj.GetName()

    def from_np(self, arr, dstack=False):
        """
        Set an Image page data from a multi-dimensional numpy array.

        Parameters:
            arr (numpy array):
            dstack (bool):  True if arr as row,col,frames, False if frames,row,col

        Returns:
            None

        Notes:
            It must first call setup() method to initialize the image window

        Examples:
            img = op.new_image()
            data = np.array([[[1.0, 2.0],[3.0, 4.0]],[[5.0, 6.0],[7.0, 8.0]],[[9.0, 10.0],[11.0, 12.0]]])
            #print(data.shape)
            img.setup(1, True, 0)
            img.from_np(data, False)
        """
        options = po.IMGSETDATAOPTS_FRAMESDIMENSION_IS_LAST if dstack else 0
        if not self.obj.SetData(arr, options):
            raise ValueError('ImagePage set data error')

    def to_np(self):
        """
        Transfers data from an ImagePage to a numpy array.

        Parameters:

        Returns:
            (numpy array)

        Examples:
            npimg = im.to_np()
        """
        retlist, ndf = self.obj.GetData()
        return np.asarray(retlist, orgdtype_to_npdtype[ndf])

    def to_np2d(self, frame):
        """
        Transfers data from one frame of an ImagePage to a 2D numpy array.
        The image must be multiframe, otherwise nothing is returned.

        Parameters:
            frame (int) the index of the image frame

        Returns:
            (numpy array)

        Examples:
            im2=iw.to_np2d(1)
        """
        retlist, ndf = self.obj.GetData(frame)
        return np.asarray(retlist, orgdtype_to_npdtype[ndf])

    def from_np2d(self, arr, frame):
        """
        Transfers data from a 2D numpy array into one frame of an ImagePage.
        The image must be multiframe, otherwise nothing is returned.
        The size (width, height) of the supplied data must match the size of the image.

        Parameters:
            frame (int) the index of the image frame

        Returns:
            (bool) success or failure

        Examples:
            im2=iw.to_np2d(1)
            im2*=10
            iw.from_np2d(im2,2)
        """
        return self.obj.SetData(arr, 0, frame)


    def from_file(self, fname):
        r"""
        load image(s) into the image window

        Parameters:
            fname(str): file path to an image file or with wildcard to a group of image files to be loaded into an image stack

        Returns:
            success of failure

        Examples:
            im = op.find_image('Image1')
            folder = op.path('e') + r'Samples\Image Processing and Analysis'
            fn = folder + r'\Flower.jpg'
            im.from_file(fn)
            #load image stack simply by wildcard
            im2 = op.find_image('Image2')
            fn = folder + r'\*.tif'
            im2.from_file(fn)
        """
        if fname and fname[0] != '"':
            fname = f'"{fname}"'
        self.lt_exec(f'img.Load({fname})')
        return self.get_int('Width') > 0

    def rgb2gray(self):
        r"""
        convert image window to grayscale
        Parameters:
            none
        Returns:
            none
        Examples:
            img=op.new_image()
            fn=op.path('e') + r'Samples\Image Processing and Analysis\Flower.jpg'
            img.from_file(fn)
            img.rgb2gray()
        """
        self.lt_exec('cvGray')

    def split(self):
        r"""
        split a color image into RGB channels
        Parameters:
            none
        Returns:
            none
        Examples:
            img=op.new_image()
            fn=op.path('e') + r'Samples\Image Processing and Analysis\Flower.jpg'
            img.from_file(fn)
            img.split()
        """
        self.lt_exec('cvSplit')

    def merge(self):
        """
        merge a image with 3 or 4 frames in Image Window to a single image
        Parameters:
            none
        Returns:
            none
        Examples:
            img=op.find_image()#you should use imgstack.xfc to prepare a image with 3 or 4 frames first
            img.merge()
        """
        self.lt_exec('cvMerge')

    @property
    def layer(self):
        '''
        Parameters:
            none
        Returns:
            Graph layer as image holder
        Examples:
            img=op.new_image()
            print(img.layer)
        '''
        return GLayer(self.obj.GetLayer())

    def setup(self, channels, multiframe, channelType=-1):
        """
        It allows simple initialization by specifying the number of channels
        and whether it should be multiframe or not. The existing image
        held in the object (if present) is wiped out.

        Parameters:
            channels(int): the number of channels (1, 3 or 4).
            multiframe(bool): whethwer it should be multiframe (Image Stack) or not.
            channelType (int, optional): the variable type of the channel.
                                        Possible values are:
                                            0 : float64
                                            1 : float32
                                            8 : uint16
                                        For all the other values the channel size will be set
                                        to uint8.

        Returns (bool): success or not

        Examples:
            img = op.new_image()
            data = np.array([[[1.0, 2.0],[3.0, 4.0]],[[5.0, 6.0],[7.0, 8.0]],[[9.0, 10.0],[11.0, 12.0]]])
            #print(data.shape)
            img.setup(1, True, 0)
            img.from_np(data, False)
        """
        strArgs = f'{channels},{int(multiframe)},{int(channelType)}'
        return self.obj.DoMethod('Setup', strArgs) == 1

    @property
    def size(self):
        r"""
        width and height of the image
        Parameters:
            none
        Returns:
            (tuple) width, height value
        Examples:
            img=op.new_image()
            fn=op.path('e') + r'Samples\Image Processing and Analysis\Flower.jpg'
            img.from_file(fn)
            print(img.size)
        """
        return self.get_int('Width'), self.get_int('Height')

    @property
    def channels(self):
        r"""
        Parameters:
            none
        Returns:
            image number of channels
        Examples:
            img=op.new_image()
            fn=op.path('e') + r'Samples\Image Processing and Analysis\Flower.jpg'
            img.from_file(fn)
            print(img.channels)
        """
        return self.get_int('Channels')

    @property
    def frames(self):
        r"""
        Parameters:
            none
        Returns:
            number of frames for an image stack, or return 1 if not multi-frames
        Examples:
            img=op.new_image()
            fn=op.path('e') + r'Samples\Image Processing and Analysis\Flower.jpg'
            img.from_file(fn)
            print(img.frames)
        """
        return self.get_int("Frames")

    @property
    def type(self):
        r"""
        Parameters:
            none
        Returns:
            image media type, 1=single image, 2=multi-frame, 3=video
        Examples:
            img=op.new_image()
            fn=op.path('e') + r'Samples\Image Processing and Analysis\Flower.jpg'
            img.from_file(fn)
            print(img.type)
        """
        return self.get_int("Media")
