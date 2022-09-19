#  ------------------------------------------------------------------------------
#
#  Copyright 2022, MIPI Alliance and its contributors.
#  SPDX-License-Identifier: BSD-3-Clause
#
#  Module Name:
#
#    bufferdata_properties.py
#
#  Abstract:
#
#    Buffer type data properties panel class.
#    This class displays the app's UI for the Hierarchical Property Frame using wxPython widgets.
#    In this frame, the user can type in all of the fields for a new property and 
#    then add that property to the current element tree
#  -------------------------------------------------------------------------------

import os
import wx
import multiprocessing
import sys
import re
import wx.grid as grid
import logging
import xml.dom.minidom as md
import xml.etree.ElementTree as et

try:
    import  disco.disco_constants as app_constants
    import disco.disco_strings as disco_str
    import disco.model as model
except:
    import disco_constants as app_constants
    import disco_strings as disco_str
    import model


class BufferDataPropertyPanel(wx.Panel):

    # initializes the Hierarchical Property Frame with the appropriate wxPython widgets
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour("white")
        # saves reference to the Main Window to reopen it once the Property Frame is closed.
        self.main_window = parent.GetParent()
        self.vbox_main = wx.BoxSizer(wx.VERTICAL)

        w, h = self.main_window.GetClientSize()
        # adding the hierarchical properties grid and the add hierarchical property button to the properties panel
        self.packs_grid = grid.Grid(self, size=(5000, 300))
        self.packs_grid.CreateGrid(0, 3)

        # sets the initial sizes for the hierarchical property grid columns
        self.packs_grid.SetColSize(0, (w - 80) / 3)
        self.packs_grid.SetColSize(1, 80)
        self.packs_grid.SetColSize(2, (w - 80) / 3)

        self.packs_grid.SetColLabelValue(0, "Property Name")
        self.packs_grid.SetColLabelValue(1, "Data Type")
        self.packs_grid.SetColLabelValue(2, "Package Name")
        self.packs_grid.SetLabelFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Intel Clear"))
        self.packs_grid.SetLabelTextColour(app_constants.COLOR_PURPLE4)

        # calls certain functions when user changes a hierarchical properties grid cell or
        # right clicks on a hierarchical properties grid cell
        self.packs_grid.Bind(grid.EVT_GRID_CELL_CHANGED, self.OnPacksGridCellChange)
        self.packs_grid.Bind(grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnPacksGridRightClick)
        self.packs_grid.GetGridWindow().Bind(wx.EVT_MOTION, self.onPacksGridMouseOver)

        self.addbufferdataBtn = wx.Button(parent=self, label="Add Buffer Properties", size=(-1, 35))
        app_constants.set_button_font(self.addbufferdataBtn)
        self.addbufferdataBtn.Bind(wx.EVT_BUTTON, self.open_bufferdata_property_frame)
        self.addbufferdataBtn.Disable()

        # creates sizer for hierarchical properties panel
        self.packsSizer = wx.BoxSizer(wx.VERTICAL)
        self.packsSizer.Add(self.packs_grid, wx.EXPAND)
        self.packsSizer.Add(self.addbufferdataBtn)
        self.SetSizer(self.packsSizer)
        self.Layout()

        self.SetAutoLayout(True)

        # when user resizes the frame, methods will be called to appropriately resize the grids
        self.packs_grid.Bind(wx.EVT_SIZE, self.resize_packs_grids)

    # temporarily disables the Main Frame and opens the Hierarchical Property Frame
    # (where user can add a new hier prop to the current Element Tree)
    def open_bufferdata_property_frame(self, event):
        new_bufferdata_property = AddBufferDataProperty(self, -1, "Add Buffer Properties", size=(450, 800),
                                                            style=wx.DEFAULT_DIALOG_STYLE)
        new_bufferdata_property.CenterOnScreen()
        val = new_bufferdata_property.ShowModal()

        if val == wx.ID_OK:
            # creates a list with all of the tag values for the new property
            messageList = []
            nameMsg = new_bufferdata_property.name.GetValue()
            messageList.append(nameMsg)

            descriptionMsg = new_bufferdata_property.description.GetValue()
            messageList.append(descriptionMsg)


            valueMsg = new_bufferdata_property.datatype.GetValue()
            messageList.append(valueMsg)

            packagename = new_bufferdata_property.packagename.GetValue()
            messageList.append(packagename)
            messageList.append(None)
            messageList.append(None)

            result_new = wx.ID_NONE
            ancestor = False
            over_four = False

             

    # called when the user resizes the frame - resizes the hierarchical properties grid accordingly
    def resize_packs_grids(self, event):
        try:
            w, h = self.GetClientSize()
            self.packs_grid.SetColSize(0, (w - 80) / (3))
            self.packs_grid.SetColSize(1, 80)
            self.packs_grid.SetColSize(2, (w - 80) / (3))
            event.Skip()
        except:
            print(w)

    # called when the user exits the window - does not add any new property
    def close_window(self, event):
        self.main_window.Enable()
        self.Destroy()

    def OnPacksGridCellChange(self, event):
        pass

    def OnPacksGridRightClick(self, event):
        pass


    def onPacksGridMouseOver(self, event):
        pass

class AddBufferDataProperty(wx.Dialog):

    def __init__(self, parent, ID, title, size=wx.DefaultSize, pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):
        wx.Dialog.__init__(self, parent, ID, title, pos, size, style)
        self.parent = parent
        pre = wx.Dialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        pre.Create(parent, ID, title, pos, size, style)

        vbox_main = wx.BoxSizer(wx.VERTICAL)

        nameLabel = wx.StaticText(self, label="Name: ")
        app_constants.set_title_font(nameLabel)
        self.name = wx.TextCtrl(self, value="", size=(300, -1))

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(nameLabel, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT | wx.TOP, 10)
        self.SetSizer(vbox_main)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.name, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT, 10)
        self.SetSizer(vbox_main)

        dataLabel = wx.StaticText(self, label="Data Type:")
        app_constants.set_title_font(dataLabel)
        self.datatype = wx.TextCtrl(self, value="Buffer", style=wx.TE_READONLY)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(dataLabel, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT | wx.TOP, 10)
        self.SetSizer(vbox_main)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.datatype, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT, 10)
        self.SetSizer(vbox_main)

        descriptionLabel = wx.StaticText(self, label="Description:")
        app_constants.set_title_font(descriptionLabel)
        self.description = wx.TextCtrl(self, value="", size=(300, 100))

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(descriptionLabel, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT | wx.TOP, 10)
        self.SetSizer(vbox_main)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.description, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT, 10)
        self.SetSizer(vbox_main)

        pkgnameLabel = wx.StaticText(self, label="Package Name:")
        app_constants.set_title_font(pkgnameLabel)
        self.packagename = wx.TextCtrl(self, value="", size=(300, -1))

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(pkgnameLabel, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT | wx.TOP, 10)
        self.SetSizer(vbox_main)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.packagename, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT, 10)
        self.SetSizer(vbox_main)

        line = wx.StaticLine(self, -1, size=(500, -1), style=wx.LI_HORIZONTAL)
        vbox_main.Add(line, 0, wx.GROW | wx.RIGHT | wx.TOP, 15)

        buttonsizer = wx.StdDialogButtonSizer()

        ok_button = wx.Button(self, wx.ID_OK, size=(85, 35))
        app_constants.set_button_font(ok_button)
        ok_button.SetDefault()
        buttonsizer.AddButton(ok_button)

        cancel_button = wx.Button(self, wx.ID_CANCEL, size=(85, 35))
        app_constants.set_button_font(cancel_button)
        buttonsizer.AddButton(cancel_button)
        buttonsizer.Realize()
        vbox_main.Add(buttonsizer, 0, wx.ALL, 5)
        self.SetSizer(vbox_main)
        vbox_main.Fit(self)
                    
                    