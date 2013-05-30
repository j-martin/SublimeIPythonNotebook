"""Base classes and utilities for readers and writers.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from base64 import encodestring, decodestring
import pprint

from . import py3compat

str_to_bytes = py3compat.str_to_bytes

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def restore_bytes(nb):
    """Restore bytes of image data from unicode-only formats.
    
    Base64 encoding is handled elsewhere.  Bytes objects in the notebook are
    always b64-encoded. We DO NOT encode/decode around file formats.
    """
    for ws in nb.worksheets:
        for cell in ws.cells:
            if cell.cell_type == 'code':
                for output in cell.outputs:
                    if 'png' in output:
                        output.png = str_to_bytes(output.png, 'ascii')
                    if 'jpeg' in output:
                        output.jpeg = str_to_bytes(output.jpeg, 'ascii')
    return nb

# output keys that are likely to have multiline values
_multiline_outputs = ['text', 'html', 'svg', 'latex', 'javascript', 'json']


# FIXME: workaround for old splitlines()
def _join_lines(lines):
    """join lines that have been written by splitlines()
    
    Has logic to protect against `splitlines()`, which
    should have been `splitlines(True)`
    """
    if lines and lines[0].endswith(('\n', '\r')):
        # created by splitlines(True)
        return ''.join(lines)
    else:
        # created by splitlines()
        return '\n'.join(lines)


def rejoin_lines(nb):
    """rejoin multiline text into strings
    
    For reversing effects of ``split_lines(nb)``.
    
    This only rejoins lines that have been split, so if text objects were not split
    they will pass through unchanged.
    
    Used when reading JSON files that may have been passed through split_lines.
    """
    for ws in nb.worksheets:
        for cell in ws.cells:
            if cell.cell_type == 'code':
                if 'input' in cell and isinstance(cell.input, list):
                    cell.input = _join_lines(cell.input)
                for output in cell.outputs:
                    for key in _multiline_outputs:
                        item = output.get(key, None)
                        if isinstance(item, list):
                            output[key] = _join_lines(item)
            else: # text, heading cell
                for key in ['source', 'rendered']:
                    item = cell.get(key, None)
                    if isinstance(item, list):
                        cell[key] = _join_lines(item)
    return nb


def split_lines(nb):
    """split likely multiline text into lists of strings
    
    For file output more friendly to line-based VCS. ``rejoin_lines(nb)`` will
    reverse the effects of ``split_lines(nb)``.
    
    Used when writing JSON files.
    """
    for ws in nb.worksheets:
        for cell in ws.cells:
            if cell.cell_type == 'code':
                if 'input' in cell and isinstance(cell.input, str):
                    cell.input = cell.input.splitlines(True)
                for output in cell.outputs:
                    for key in _multiline_outputs:
                        item = output.get(key, None)
                        if isinstance(item, str):
                            output[key] = item.splitlines(True)
            else: # text, heading cell
                for key in ['source', 'rendered']:
                    item = cell.get(key, None)
                    if isinstance(item, str):
                        cell[key] = item.splitlines(True)
    return nb

# b64 encode/decode are never actually used, because all bytes objects in
# the notebook are already b64-encoded, and we don't need/want to double-encode

def base64_decode(nb):
    """Restore all bytes objects in the notebook from base64-encoded strings.
    
    Note: This is never used
    """
    for ws in nb.worksheets:
        for cell in ws.cells:
            if cell.cell_type == 'code':
                for output in cell.outputs:
                    if 'png' in output:
                        if isinstance(output.png, str):
                            output.png = output.png.encode('ascii')
                        output.png = decodestring(output.png)
                    if 'jpeg' in output:
                        if isinstance(output.jpeg, str):
                            output.jpeg = output.jpeg.encode('ascii')
                        output.jpeg = decodestring(output.jpeg)
    return nb


def base64_encode(nb):
    """Base64 encode all bytes objects in the notebook.
    
    These will be b64-encoded unicode strings
    
    Note: This is never used
    """
    for ws in nb.worksheets:
        for cell in ws.cells:
            if cell.cell_type == 'code':
                for output in cell.outputs:
                    if 'png' in output:
                        output.png = encodestring(output.png).decode('ascii')
                    if 'jpeg' in output:
                        output.jpeg = encodestring(output.jpeg).decode('ascii')
    return nb


class NotebookReader(object):
    """A class for reading notebooks."""

    def reads(self, s, **kwargs):
        """Read a notebook from a string."""
        raise NotImplementedError("loads must be implemented in a subclass")

    def read(self, fp, **kwargs):
        """Read a notebook from a file like object"""
        nbs = fp.read()
        if not py3compat.PY3 and not isinstance(nbs, str):
            nbs = py3compat.str_to_unicode(nbs)
        return self.reads(nbs, **kwargs)


class NotebookWriter(object):
    """A class for writing notebooks."""

    def writes(self, nb, **kwargs):
        """Write a notebook to a string."""
        raise NotImplementedError("loads must be implemented in a subclass")

    def write(self, nb, fp, **kwargs):
        """Write a notebook to a file like object"""
        nbs = self.writes(nb,**kwargs)
        if not py3compat.PY3 and not isinstance(nbs, str):
            # this branch is likely only taken for JSON on Python 2
            nbs = py3compat.str_to_unicode(nbs)
        return fp.write(nbs)



