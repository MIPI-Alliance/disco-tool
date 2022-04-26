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
#    DisCo info page.
#
#  -------------------------------------------------------------------------------

VERSION = (1, 0, 0, "beta", 0)

import wx
import sys
import wx
import wx.html
import wx.lib.wxpTag

#---------------------------------------------------------------------------

class DisCoInfo(wx.Dialog):
    text = '''
<html>
<body bgcolor="#FFFFFF">
<center><table bgcolor="#551A81" width="100%%" cellspacing="0"
cellpadding="0" border="1">
<tr>
    <td align="center">
    <h1>DisCo %s</h1>
    </td>
</tr>
</table>

<p><wxp module="wx" class="Button">
    <param name="label" value="OK">
    <param name="id"    value="ID_OK">
</wxp></p>
</center>
</body>
</html>
'''
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, 'About the DisCo creation tool',)
        wxhtml = wx.html.HtmlWindow(self, -1, size=(420, -1))
        if "gtk2" in wx.PlatformInfo or "gtk3" in wx.PlatformInfo:
            html.SetStandardFonts()
        py_version = sys.version.split()[0]
        disco_txt = self.text % (str(VERSION))
        wxhtml.SetPage(disco_txt)
        button = wxhtml.FindWindowById(wx.ID_OK)
        internalrep = wxhtml.GetInternalRepresentation()
        wxhtml.SetSize( (internalrep.GetWidth()+25, internalrep.GetHeight()+25) )
        self.SetClientSize(wxhtml.GetSize())
        self.CentreOnParent(wx.BOTH)
