"""
originpro
A package for interacting with Origin software via Python.
Copyright (c) 2020 OriginLab Corporation
"""
# pylint: disable=C0301
import os
from .config import po
from .base import BaseObject
from .utils import org_ver


class Notes(BaseObject):
    ''' Origin Notes Window'''
    def __repr__(self):
        return self.name

    @property
    def text(self):
        """
        Get Notes window text

        Parameters:

        Returns:
            (str) Notes window text

        Examples:
            text = nt.text
        """
        return self.obj.GetText()
    @text.setter
    def text(self, value):
        """
        Set Notes window text

        Parameters:
            value (str): Text to set

        Returns:
            None

        Examples:
            nt.text = 'hello world'
        """
        self.obj.SetText(value)

    @property
    def syntax(self):
        """
        Get Notes syntax

        Parameters:

        Returns:
            (int) Notes syntax, can be 0(Normal Text), 1(HTML), 2(Markdown), 3(Origin Rich Text)

        Examples:
            syntax = nt.syntax
        """
        return self.get_int('syntax')
    @syntax.setter
    def syntax(self, value):
        """
        Set Notes syntax

        Parameters:
            value (int): Syntax to set, can be 0(Normal Text), 1(HTML), 2(Markdown), 3(Origin Rich Text)

        Returns:
            None

        Examples:
            nt.syntax = 2
        """
        self.set_int('syntax', value)

    @property
    def view(self):
        """
        Get Notes view mode

        Parameters:

        Returns:
            (int) Notes view mode, can be 0(Text Mode), 1(Render Mode)

        Examples:
            syntax = nt.syntax
        """
        return self.get_int('view')
    @view.setter
    def view(self, value):
        """
        Set Notes view mode

        Parameters:
            value (int): View mode to set, can be 0(Text Mode), 1(Render Mode)

        Returns:
            None

        Examples:
            nt.view = 1
        """
        self.set_int('view', value)

    def append(self, text, newline=True):
        """
        Append text to Notes window.

        Parameters:
            text (str): Text to append.
            newline (bool): Add new line character if true.
        Returns:
            None

        Examples:
            nt.append('hello world')
        """
        text = self.text + text
        if newline:
            text += os.linesep
        self.text = text

    def load(self, fname, askreplace=False):
        """
        Load file into Notes window.

        Parameters:
            fname (str): Input file full path.
            askreplace (bool): Ask if replace current content if True
        Returns:
            Error code, 0 for success.

        Examples:
            nt.load('D:/hello.html')
        """
        if fname and fname[0] != '"':
            fname = f'"{fname}"'
        arg = f'{fname}'
        if org_ver() > 10.1:
            arg += f', {int(askreplace)}'
        return self.method_int('load', arg)

    def exp_html(self, fname):
        """
        Export Notes window as HTML files.

        Parameters:
            fname (str): Output HTML file name.
        Returns:
            Error code, 0 for success.

        Examples:
            nt.exp_html('D:/hello.html')
        """
        if fname and fname[0] != '"':
            fname = f'"{fname}"'
        return self.method_int('exporthtml', fname)

    def destroy(self):
        """
        Destroy Notes window.

        Parameters:

        Returns:
            None

        Examples:
            nt.destroy()
        """
        po.LT_execute(f'win -cn {self.name}')
