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

from   disco.controller import  controller
import wx
def main():
    """Entry point for the application script"""
    app = wx.App()
    myController = controller()
    app.MainLoop()	
    
