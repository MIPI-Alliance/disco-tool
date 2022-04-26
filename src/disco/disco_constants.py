#  ------------------------------------------------------------------------------
#
#  Copyright 2021, MIPI Alliance and its contributors.
#  SPDX-License-Identifier: BSD-3-Clause
#
#  Module Name:
#
#    disco_constants.py
#
#  Abstract:
#
#    To maintain all GUI constants.
#
#  -------------------------------------------------------------------------------

import wx

app =  wx.App(False)


#Color Palette
COLOR_WHITE = wx.Colour(255, 255, 255)
COLOR_BLACK= wx.Colour(0, 0, 0)
COLOR_ERROR_MESSAAGE = wx.Colour(237,28,36)
COLOR_PURPLE4 = wx.Colour(85,26,129)

#AUI Manager Constants
MAIN_FRAME_SIZE_WxH = (1150, int(wx.GetDisplaySize()[1]/2))
LOGO_PANEL_BEST_SIZE = (-1, 75)
LOGO_PANEL_MIN_SIZE = (-1, 75)
NAV_PANEL_BEST_SIZE = (-1, wx.GetDisplaySize()[1]-LOGO_PANEL_BEST_SIZE[1]) 
NAV_PANEL_BEST_SIZE = (-1, wx.GetDisplaySize()[1]-LOGO_PANEL_MIN_SIZE[1]) 
INFOBAR_PANEL_MIN_SIZE = (-1, 42)
INFOBAR_PANEL_BEST_SIZE = (-1, 42)
MASTHEAD_WIDTH = 150
GUI_MAIN_FRAME_MIN_SIZE_WxH = (1150, wx.GetDisplaySize()[1]/2)#

def set_button_font(targetobject):
    """
    __init__(targetobject)
    sets title font
    :param Text object:
    :returns: none
    """
    targetobject.SetFont(wx.Font(12.5, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0))
    targetobject.SetForegroundColour(COLOR_WHITE)
    targetobject.SetBackgroundColour(COLOR_PURPLE4)

def set_title_font(targetobject):
    """
    __init__(targetobject)
    sets title font
    :param Text object:
    :returns: none
    """
    targetobject.SetFont(wx.Font(12.5, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0))
    targetobject.SetForegroundColour(COLOR_PURPLE4)

def set_text_font(targetobject):
    """
    __init__(targetobject)
    sets text font
    :param Text object:
    :returns: none
    """

    targetobject.SetFont(wx.Font(12.5, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0))
    targetobject.SetForegroundColour(COLOR_BLACK)
