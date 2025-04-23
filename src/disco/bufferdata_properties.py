# ------------------------------------------------------------------------------
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
    import disco.panel_base as panel_base
except:
    import disco_constants as app_constants
    import disco_strings as disco_str
    import model
    import panel_base


class BufferDataPropertyPanel(panel_base.PanelBase):

    # initializes the Hierarchical Property Frame with the appropriate wxPython widgets
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour("white")
        # saves reference to the Main Window to reopen it once the Property Frame is closed.
        self.main_window = parent.GetParent()
        self.vbox_main = wx.BoxSizer(wx.VERTICAL)

        w, h = self.main_window.GetClientSize()
        # adding the hierarchical properties grid and the add hierarchical property button to the properties panel
        self.props_grid = grid.Grid(self, size=(5000, 300))
        self.props_grid.CreateGrid(0, 3)

        # sets the initial sizes for the hierarchical property grid columns
        column_size = (w - app_constants.ROW_INDEX_COLUMN_WIDTH) / app_constants.COLUMN_COUNT
        self.props_grid.SetColSize(app_constants.PROPERTY_NAME_COLUMN_INDEX, column_size)
        self.props_grid.SetColSize(app_constants.DATA_TYPE_COLUMN_INDEX, column_size)
        self.props_grid.SetColSize(app_constants.BUFFER_NAME_COLUMN_INDEX, column_size)

        self.props_grid.SetColLabelValue(0, "Property Name")
        self.props_grid.SetColLabelValue(1, "Data Type")
        self.props_grid.SetColLabelValue(2, "Buffer Name")
        self.props_grid.SetLabelFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Intel Clear"))
        self.props_grid.SetLabelTextColour(app_constants.COLOR_PURPLE4)

        # calls certain functions when user changes a hierarchical properties grid cell or
        # right clicks on a hierarchical properties grid cell
        self.props_grid.Bind(grid.EVT_GRID_CELL_CHANGED, self.OnPropsGridCellChange)
        self.props_grid.Bind(grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnPropsGridRightClick)
        self.props_grid.GetGridWindow().Bind(wx.EVT_MOTION, self.onPropsGridMouseOver)

        self.addbufferdataBtn = wx.Button(parent=self, label="Add Buffer Property", size=(-1, 35))
        app_constants.set_button_font(self.addbufferdataBtn)
        self.addbufferdataBtn.Bind(wx.EVT_BUTTON, self.open_bufferdata_property_frame)
        self.addbufferdataBtn.Disable()

        # creates sizer for hierarchical properties panel
        self.packsSizer = wx.BoxSizer(wx.VERTICAL)
        self.packsSizer.Add(self.props_grid, wx.EXPAND)
        self.packsSizer.Add(self.addbufferdataBtn)
        self.SetSizer(self.packsSizer)
        self.Layout()

        self.SetAutoLayout(True)

        # when user resizes the frame, methods will be called to appropriately resize the grids
        self.props_grid.Bind(wx.EVT_SIZE, self.resize_props_grids)

        super().__init__()

    @property
    def edit_column_index(self):
        return app_constants.BUFFER_NAME_COLUMN_INDEX

    @property
    def grid(self):
        return self.props_grid

    # called when the user changes a cell in the buffer properties grid (the value cell)
    def OnPropsGridCellChange(self, event):
        # collects the new property value and the previous property value
        old_value = event.GetString()
        value = self.props_grid.GetCellValue(event.GetRow(), event.GetCol())

        # initializes variables to starting values
        over_four = False
        result_new = wx.ID_NONE
        result_old = wx.ID_NONE

        # if user changes a property's name, that property name is updated in the model
        if event.GetCol() == 0:
            message = [value, old_value]
            self.main_window.buff_property_name_changed(message=message)

        # if user changes a property's value:
        else:
            # TODO: currently, this function is being called multiple times when a user only changes a grid cell once -
            # after the first correct function call, the old_value is equal to the new value.
            # This if statement is to prevent the warning dialogs to show up more than
            # once when the function is called with these incorrect values.
            if old_value != value:
                # if the new value is over four characters, an error message is shown and
                # the over_four variable is set to true
                if len(value) > 4:
                    wx.MessageBox(message=value + disco_str.DISCO_STR_GRIDCELL_MAXCHAR_MSG,
                                  caption='Package name error',
                                  style=wx.OK | wx.ICON_ERROR)
                    over_four = True

                # iterates through the current element tree list to see if the new value already has an associated
                # element tree or if the old value had several parents (not just curr_tree).
                for tree in self.main_window.tree_list:

                    # enters this if statement if the new value already has an element tree
                    # and send a warning message telling the user
                    # if they use this value, they will be sharing this package among other parents.
                    if tree.getroot().find('Name').text == value:
                        result_new = wx.MessageBox(message=value + disco_str.DISCO_STR_GRIDCELL_REUSE_MSG,
                                                       caption='Package name warning',
                                                       style=wx.YES_NO | wx.ICON_WARNING)

                    # Condition when the element tree is found that was associated with the previous value.
                    # Counter variable is used to count how many parents this tree has -
                    # if it has more than one, send a warning message telling the user if they use this
                    # value, the new package will no longer be shared with these other parents.
                    if tree.getroot().find('Name').text == old_value:
                        counter = 0
                        for parent in tree.getroot().find('Header').find('Parents').iter('Parent'):
                            counter += 1

                        if counter > 1:
                            result_old = wx.MessageBox(message=old_value + disco_str.DISCO_STR_GRIDCELL_OLD_SHARED_MSG,
                                                       caption='Package name warning',
                                                       style=wx.YES_NO | wx.ICON_WARNING)

                # if the new value has equal or less than four characters
                # and the user did not reply "no" to any warning messages they might have gotten,
                # then the hierarchical property is changed in the Model. Otherwise, the property
                # is not changed in the model and the grid cell value returns to its previous value.
                if (over_four is False) & (result_new != wx.NO) & (result_old != wx.NO):
                    # Print statement for debugging purposes:
                    print("publishing property " + value)

                    message = [self.props_grid.GetCellValue(event.GetRow(), 0), value, old_value]
                    self.main_window.buff_property_value_changed(message=message)

                else:
                    # Print statement for debugging purposes:
                    print("\n setting cell value " + old_value + " " + value)
                    self.props_grid.SetCellValue(event.GetRow(), event.GetCol(), old_value)

            else:
                # Print statement for debugging purposes:
                print("skipping event")

    # temporarily disables the Main Frame and opens the Buffer Property Frame
    # (where user can add a new buffer prop to the current Element Tree)
    def open_bufferdata_property_frame(self, event):

        new_bufferdata_property = AddBufferDataProperty(self, -1, "Add Buffer Property", size=(450, 800),
                                                            style=wx.DEFAULT_DIALOG_STYLE)
        new_bufferdata_property.CenterOnScreen()
        val = new_bufferdata_property.ShowModal()

        if val == wx.ID_OK:
            # creates a list with all of the tag values for the new property
            messageList = []
            nameMsg = new_bufferdata_property.name.GetValue()
            messageList.append(nameMsg)

            dataMsg = new_bufferdata_property.datatype.GetValue()
            messageList.append(dataMsg)

            descriptionMsg = new_bufferdata_property.description.GetValue()
            messageList.append(descriptionMsg)

            packagename = new_bufferdata_property.packagename.GetValue()
            messageList.append(packagename)

            filename = "Sdca_Buffer.xml"
            messageList.append(filename)

            result_new = wx.ID_NONE
            over_four = False 
            
            # if the new buffer name is not four characters, an error message is shown
            # and the over_four variable is set to true
            if len(packagename) > 4:
                wx.MessageBox(message=disco_str.DISCO_STR_GRIDCELL_MAXCHAR_MSG,
                              caption='Package name error', style=wx.OK | wx.ICON_ERROR)
                over_four = True

            # this loop determines if there is an existing
            # element tree associated with the new buffer property value -
            # if there is, a warning message pops up telling the user if 
            # they use this value, they will be sharing this package among other parents.
            for tree in self.main_window.tree_list:
                if tree.getroot().find('Name').text == packagename:
                    result_new = wx.MessageBox(message=disco_str.DISCO_STR_PKG_REUSE_MSG,
                                               caption='Package name warning',
                                               style=wx.YES_NO | wx.ICON_WARNING)
            
            # if the user does not get the warning message or replies "yes" to it,
            # the value is equal or less than four characters, and the name/description/buff name are filled out,
            # the new buffer property is added to the model
            if (result_new != wx.NO) & (over_four is False):
                if (nameMsg == '') | (descriptionMsg == '') | (packagename == ''):
                    wx.MessageBox(message='Please fill out all information for the property before adding it.', 
                                  caption='Property error', style=wx.OK | wx.ICON_ERROR)
                else:
                    self.main_window.buff_property_added(message=messageList)

    # called when the user resizes the frame - resizes the hierarchical properties grid accordingly
    def resize_props_grids(self, event):
        try:
            w, h = self.main_window.GetClientSize()
            column_size = (w - (app_constants.SIDE_PANEL_WIDTH * 2 + app_constants.ROW_INDEX_COLUMN_WIDTH + app_constants.SIDE_PANEL_PADDING * 2)) / (app_constants.COLUMN_COUNT)
            self.props_grid.SetColSize(app_constants.PROPERTY_NAME_COLUMN_INDEX, column_size)
            self.props_grid.SetColSize(app_constants.DATA_TYPE_COLUMN_INDEX, column_size)
            self.props_grid.SetColSize(app_constants.BUFFER_NAME_COLUMN_INDEX, column_size)
            event.Skip()
        except:
            print(w)

    # called when the user exits the window - does not add any new property
    def close_window(self, event):
        self.main_window.Enable()
        self.Destroy()

    def OnPropsGridRightClick(self, event):
        pass


    def onPropsGridMouseOver(self, event):
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
        self.datatype = wx.TextCtrl(self, value="String", style=wx.TE_READONLY)

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

        pkgnameLabel = wx.StaticText(self, label="Buffer Name:")
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

class EditBufferDataPropertyValue(wx.Dialog):

    def __init__(self, parent, ID, currValue, title, size=wx.DefaultSize, pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):
        wx.Dialog.__init__(self, parent, ID, title, pos, size, style)
        self.parent = parent
        pre = wx.Dialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        pre.Create(parent, ID, title, pos, size, style)

        vbox_main = wx.BoxSizer(wx.VERTICAL)

        valueLabel = wx.StaticText(self, label="Value:")
        app_constants.set_title_font(valueLabel)
        self.value = wx.TextCtrl(self, value=currValue, size=(300, 100), style=wx.TE_MULTILINE)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(valueLabel, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT | wx.TOP, 10)
        self.SetSizer(vbox_main)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.value, 0, wx.LEFT, 10)
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
                    
                    
                    