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

import wx
from disco.disco_help import VERSION   
__version__ = VERSION

from disco.disco_aui_manager import DiscoToolApp
def main():
    """Entry point for the application script"""
    app = wx.App()
    myController = DiscoToolApp(redirect=False)
    app.MainLoop()	
    
