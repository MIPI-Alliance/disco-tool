#  ------------------------------------------------------------------------------
#
#  Copyright 2022, MIPI Alliance and its contributors.
#  SPDX-License-Identifier: BSD-3-Clause
#
#  Module Name:
#
#    init.py
#
#  Abstract:
#
#    DisCo package entry point.
#
#  -------------------------------------------------------------------------------

VERSION = (1, 0, 0, "beta", 0)

__version__ = get_version(VERSION)

from   disco.disco_aui_manager import  controller
import wx
import sys
import wx
import wx.html
import wx.lib.wxpTag

#---------------------------------------------------------------------------

class DisCoInfo(wx.Dialog):
    text = '''
<html>
<body bgcolor="#AC76DE">
<center><table bgcolor="#458154" width="100%%" cellspacing="0"
cellpadding="0" border="1">
<tr>
    <td align="center">
    <h1>wxPython %s</h1>
    (%s)<br>
    Running on Python %s<br>
    </td>
</tr>
</table>

<p><b>wxPython</b> is a Python extension module that
encapsulates the wxWindows GUI classes.</p>

<p>This demo shows off some of the capabilities
of <b>wxPython</b>.  Select items from the menu or tree control,
sit back and enjoy.  Be sure to take a peek at the source code for each
demo item so you can learn how to use the classes yourself.</p>

<p><b>wxPython</b> is brought to you by <b>Robin Dunn</b> and<br>
<b>Total Control Software,</b> Copyright (c) 1997-2020.</p>

<p>
<font size="-1">Please see <i>license.txt</i> for licensing information.</font>
</p>

<p><wxp module="wx" class="Button">
    <param name="label" value="Okay">
    <param name="id"    value="ID_OK">
</wxp></p>
</center>
</body>
</html>
'''
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, 'About the DisCo creation tool',)
        html = wx.html.HtmlWindow(self, -1, size=(420, -1))
        if "gtk2" in wx.PlatformInfo or "gtk3" in wx.PlatformInfo:
            html.SetStandardFonts()
        py_version = sys.version.split()[0]
        disco_txt = self.text % (VERSION)
        html.SetPage(disco_txt)
        btn = html.FindWindowById(wx.ID_OK)
        ir = html.GetInternalRepresentation()
        html.SetSize( (ir.GetWidth()+25, ir.GetHeight()+25) )
        self.SetClientSize(html.GetSize())
        self.CentreOnParent(wx.BOTH)

def main():
    """Entry point for the application script"""
    app = wx.App()
    myController = DiscoToolApp(redirect=False)
    app.MainLoop()	
    
