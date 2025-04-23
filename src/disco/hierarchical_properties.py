#  ------------------------------------------------------------------------------
#
#  Copyright 2022, MIPI Alliance and its contributors.
#  SPDX-License-Identifier: BSD-3-Clause
#
#  Module Name:
#
#    model.py
#
#  Abstract:
#
#    Hierarchical properties panel class.
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


class HierarchicalPropertyPanel(wx.Panel):

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

        self.addHierPropBtn = wx.Button(parent=self, label="Add Hierarchical Property", size=(-1, 35))
        app_constants.set_button_font(self.addHierPropBtn)
        self.addHierPropBtn.Bind(wx.EVT_BUTTON, self.open_hierarchical_property_frame)
        self.addHierPropBtn.Disable()

        # creates sizer for hierarchical properties panel
        self.packsSizer = wx.BoxSizer(wx.VERTICAL)
        self.packsSizer.Add(self.packs_grid, wx.EXPAND)
        self.packsSizer.Add(self.addHierPropBtn)
        self.SetSizer(self.packsSizer)
        self.Layout()

        self.SetAutoLayout(True)

        # when user resizes the frame, methods will be called to appropriately resize the grids
        self.packs_grid.Bind(wx.EVT_SIZE, self.resize_packs_grids)

    # temporarily disables the Main Frame and opens the Hierarchical Property Frame
    # (where user can add a new hier prop to the current Element Tree)
    def open_hierarchical_property_frame(self, event):
        new_hierarchical_property = AddHierarchicalProperty(self, -1, "Add Hierarchical Property", size=(450, 800),
                                                            style=wx.DEFAULT_DIALOG_STYLE)
        new_hierarchical_property.CenterOnScreen()
        val = new_hierarchical_property.ShowModal()

        if val == wx.ID_OK:
            # creates a list with all of the tag values for the new property
            messageList = []
            nameMsg = new_hierarchical_property.name.GetValue()
            messageList.append(nameMsg)

            dataMsg = new_hierarchical_property.data.GetValue()
            messageList.append(dataMsg)

            requiredMsg = 0 # removed from add hierarchical window, see https://github.com/MIPI-Alliance/private-disco-tool/issues/69
            messageList.append(str(int(requiredMsg)))

            descriptionMsg = new_hierarchical_property.description.GetValue()
            messageList.append(descriptionMsg)

            modifyMsg = 0 # removed from add hierarchical window, see https://github.com/MIPI-Alliance/private-disco-tool/issues/69
            messageList.append(str(int(modifyMsg)))

            prefixMsg = new_hierarchical_property.prefix.GetValue()
            messageList.append(prefixMsg)

            valueMsg = new_hierarchical_property.value.GetValue()
            messageList.append(valueMsg)

            fileMsg = new_hierarchical_property.file.GetValue()
            messageList.append(fileMsg)
            messageList.append(None)
            messageList.append(None)

            result_new = wx.ID_NONE
            ancestor = False
            over_four = False

            # if the new value is not four characters, an error message is shown
            # and the over_four variable is set to true
            if len(valueMsg) > 4:
                wx.MessageBox(message=valueMsg + disco_str.DISCO_STR_GRIDCELL_MAXCHAR_MSG,
                              caption='Package name error', style=wx.OK | wx.ICON_ERROR)
                over_four = True

            # TODO: move the following data validation to the Controller
            # (checking if tree is an ancestor of curr_tree) this loop determines if there is an existing
            # element tree associated with the new hierarchical property value -
            # if there is, an error message is sent if the existing tree is an ancestor of the curr_tree
            # (because this would cause an infinite loop) and a
            # warning message pops up telling the user if they use this value,
            # they will be sharing this package among other parents.
            for tree in self.main_window.tree_list:
                if tree.getroot().find('Name').text == valueMsg:
                    ancestor = self.is_ancestor(tree, self.main_window.curr_tree)
                    if ancestor is True:
                        wx.MessageBox(message='Circular reference found. One of the parent packages has the same name.',
                                      caption='Package name error',
                                      style=wx.OK | wx.ICON_ERROR)
                    else:
                        result_new = wx.MessageBox(message=valueMsg + disco_str.DISCO_STR_PKG_REUSE_MSG,
                                                   caption='Package name warning',
                                                   style=wx.YES_NO | wx.ICON_WARNING)

            # if the user does not get the warning message or replies "yes" to it,
            # the new value is not an ancestor of the current element tree,
            # the value is equal or less than four characters, and the name/data/value/file are filled out,
            # the new hierarchical property is added to the model
            if (result_new != wx.NO) & (ancestor is False) & (over_four is False):
                if (nameMsg == '') | (dataMsg == '') | (valueMsg == '') | (fileMsg == ''):
                    wx.MessageBox(message='Please fill out all information for the hierarchical property before adding it.',
                                  caption='Property error',
                                  style=wx.OK | wx.ICON_ERROR)
                else:
                    self.main_window.new_hier_property_added(message=messageList)

    # called when the user resizes the frame - resizes the hierarchical properties grid accordingly
    def resize_packs_grids(self, event):
        w, h = self.GetClientSize()
        self.packs_grid.SetColSize(0, (w - 80) / (3))
        self.packs_grid.SetColSize(1, 80)
        self.packs_grid.SetColSize(2, (w - 80) / (3))
        event.Skip()

    # called when the user exits the window - does not add any new property
    def close_window(self, event):
        self.main_window.Enable()
        self.Destroy()

    # opens up the main window, closes the hierarchical properties window,
    # and adds the appropriate hierarchical property to the current tree
    def open_main(self, event):
        # creates a list with all of the tag values for the new property
        nameMsg = self.name.GetValue()
        dataMsg = self.data.GetValue()
        descriptionMsg = self.description.GetValue()
        requiredMsg = self.required.GetValue()
        modifyMsg = self.modify.GetValue()
        valueMsg = self.value.GetValue()
        fileMsg = self.file.GetValue()
        prefixMsg = self.prefix.GetValue()
        messageList = [nameMsg, dataMsg, str(int(requiredMsg)), descriptionMsg, str(int(modifyMsg)), prefixMsg,
                       valueMsg, fileMsg, None, None]

        result_new = wx.ID_NONE
        ancestor = False
        over_four = False

        # if the new value is not four characters, an error message is shown and the over_four variable is set to true
        if len(valueMsg) > 4:
            wx.MessageBox(message=valueMsg + disco_str.DISCO_STR_GRIDCELL_MAXCHAR_MSG,
                          caption='Package name error', style=wx.OK | wx.ICON_ERROR)
            over_four = True

        # TODO: move the following data validation to the Controller (checking if tree is an ancestor of curr_tree)

        # this loop determines if there is an existing element tree associated with the
        # new hierarchical property value - if there is, an error message is sent if
        # the existing tree is an ancestor of the curr_tree (because this would cause an infinite loop) and a
        # warning message pops up telling the user if they use this value,
        # they will be sharing this package among other parents.
        for tree in self.main_window.tree_list:
            if tree.getroot().find('Name').text == valueMsg:
                ancestor = self.is_ancestor(tree, self.main_window.curr_tree)
                if ancestor is True:
                    wx.MessageBox(message='Circular reference found. One of the parent packages has the same name.',
                                  caption='Package name error',
                                  style=wx.OK | wx.ICON_ERROR)
                else:
                    result_new = wx.MessageBox(message=valueMsg + ' is an existing package. Do you want to re-use existing package?',
                                               caption='Package name warning',
                                               style=wx.YES_NO | wx.ICON_WARNING)

        # if the user does not get the warning message or replies "yes" to it,
        # the new value is not an ancestor of the current element tree,
        # the value is equal or less than four characters, and the name/data/value/file are filled out,
        # the new hierarchical property is added to the model
        if (result_new != wx.NO) & (ancestor is False) & (over_four is False):
            if (nameMsg == '') | (dataMsg == '') | (valueMsg == '') | (fileMsg == ''):
                wx.MessageBox(message='Please fill out all information for the hierarchical property before adding it.',
                              caption='Property error',
                              style=wx.OK | wx.ICON_ERROR)
            else:
                self.main_window.new_hier_property_added(message=messageList)
                self.main_window.Enable()
                self.Close()

    # move this function to the Controller
    # TODO: this function is repeat code from the MainFrame class. Define an interface to share between all three
    # windows with common code.
    # helper function for OnPacksGridCellChange - returns true if
    # higher_tree is an ancestor of lower_tree and returns false otherwise
    def is_ancestor(self, higher_tree, lower_tree):
        # find hier_props and loop through - for each one, find that tree and if it matches lower_tree, return true.
        # otherwise, call this function again but with (new tree, lower_tree)

        higher_name = higher_tree.getroot().find('Name').text
        lower_name = lower_tree.getroot().find('Name').text

        # Base case: if the trees are the same, return true
        if higher_name == lower_name:
            return True

        # Recursive case: loop through the hierarchical properties of the higher_tree.
        # For each one, find its associated element tree and call this function again
        # with this element tree as the higher_tree; return True if the function returns True.
        for hier_prop in higher_tree.getroot().find('HierarchicalProperties').iter('HierarchicalProperty'):
            name = hier_prop.find('Value').text
            for tree in self.main_window.tree_list:
                if tree.getroot().find('Name').text == name:
                    result = self.is_ancestor(tree, lower_tree)
                    if result is True:
                        return True

        # If the function goes through all of the trees under higher_tree and
        # does not find a match to lower_tree, return False
        return False

    # called when the user changes the value cell for a hierarchical property in the hierarchical properties grid -
    # prevents the user from entering a value that is not four characters and
    # warns the user if their value already exists (meaning this package would have several parents)
    def OnPacksGridCellChange(self, event):

        # collects the new property value and the previous property value
        old_value = event.GetString()
        value = self.packs_grid.GetCellValue(event.GetRow(), event.GetCol())

        # initializes variables to starting values
        over_four = False
        is_ancestor = False
        result_new = wx.ID_NONE
        result_old = wx.ID_NONE

        # if user changes a property's name, that property name is updated in the model
        if event.GetCol() == 0:
            message = [value, old_value]
            self.main_window.hier_property_name_changed(message=message)
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

                    # TODO: move the following data validation to the Controller
                    # (checking if tree is an ancestor of curr_tree)
                    # enters this if statement if the new value already has an element tree -
                    # in this case send an error message if this element
                    # tree is an ancestor of the curr_tree (because this would cause an infinite loop)
                    # and send a warning message telling the user
                    # if they use this value, they will be sharing this package among other parents.
                    if tree.getroot().find('Name').text == value:
                        is_ancestor = self.is_ancestor(tree, self.main_window.curr_tree)

                        if is_ancestor:
                            wx.MessageBox(
                                message=disco_str.DISCO_STR_GRIDCELL_DUPLICATE_MSG,
                                caption='Package name error',
                                style=wx.OK | wx.ICON_ERROR,
                            )
                        else:
                            dialog = wx.MessageDialog(
                                self,
                                message=value + disco_str.DISCO_STR_GRIDCELL_REUSE_MSG,
                                caption='Package name warning',
                                style=wx.YES_NO | wx.ICON_WARNING,
                            )
                            dialog.SetYesNoLabels("Re-use existing", "Cancel rename")
                            result_new = dialog.ShowModal()
                            dialog.Destroy()

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

                # if the new value is not an ancestor of the current tree, has equal or less than four characters,
                # and the user did not reply "no" to any warning messages they might have gotten,
                # then the hierarchical property is changed in the Model. Otherwise, the property
                # is not changed in the model and the grid cell value returns to its previous value.
                if (not is_ancestor) & (not over_four) & (result_new != wx.ID_NO) & (result_old != wx.NO):
                    # Print statement for debugging purposes:
                    print("publishing property " + value)

                    message = [self.packs_grid.GetCellValue(event.GetRow(), 0), value, old_value]
                    self.main_window.hier_property_value_changed(message=message)

                else:
                    # Print statement for debugging purposes:
                    print("\n setting cell value " + old_value + " " + value)
                    self.packs_grid.SetCellValue(event.GetRow(), event.GetCol(), old_value)

            else:
                # Print statement for debugging purposes:
                print("skipping event")

    # called when user right clicks on a property in the hierarchical properties grid -
    # opens a pop up menu with the option to delete that property
    def OnPacksGridRightClick(self, event):

        # gets the current width and height of the window and the position where the user clicked
        w, h = self.GetClientSize()
        point = event.GetPosition()

        # takes the x position of where the user clicked and offsets it by .25*w (to account for tree panel on the left)
        point.x = (w * 0.25) + point.x
        point.y = (h * 0.5) + point.y

        # finds the name of the property to be deleted (to be used in the delete_property function)
        self.delete_property_name = self.packs_grid.GetCellValue(event.GetRow(), 0)

        # creates a pop up menu with the option to delete and opens this menu at the correct screen position
        popUpMenu = wx.Menu()
        deleteItem = wx.MenuItem(popUpMenu, wx.NewId(), "Remove " + self.delete_property_name)
        popUpMenu.Append(deleteItem)
        popUpMenu.Bind(wx.EVT_MENU, self.main_window.delete_hier_property, deleteItem)
        self.PopupMenu(popUpMenu, point)

    # called when the user moves the mouse over the screen
    def onPacksGridMouseOver(self, event):
        # gets position of the mouse on the screen and converts this to row and column
        x, y = self.packs_grid.CalcUnscrolledPosition(event.GetX(), event.GetY())
        coordinates = self.packs_grid.XYToCell(x, y)
        row = coordinates[0]
        column = coordinates[1]

        # gets the total number of rows and columns
        num_rows = self.packs_grid.GetNumberRows()
        num_cols = self.packs_grid.GetNumberCols()

        # if the mouse is over an actual row and column in the grid, find that row's property and
        # data type and display its description to the user
        if (column >= 0) & (column < num_cols) & (row >= 0) & (row < num_rows):
            # data_type = self.packs_grid.GetCellValue(row, 1)
            prop_name = self.packs_grid.GetCellValue(row, 0)
            tree_root = self.main_window.curr_tree.getroot()
            for prop in tree_root.find('HierarchicalProperties').iter('HierarchicalProperty'):
                if prop.find('Name').text == prop_name:
                    description = prop.find('Description').text
                    if description is None:
                        description = ""
                    msg = description + ":" + "\n\n" + "String can be entered in any format."
                    # event.GetEventObject().SetToolTip(msg)
                    self.main_window.description_panel.SetValue(msg)

class AddHierarchicalProperty(wx.Dialog):

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
        self.data = wx.TextCtrl(self, value="String", style=wx.TE_READONLY)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(dataLabel, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT | wx.TOP, 10)
        self.SetSizer(vbox_main)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.data, 0, wx.LEFT, 10)
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

        prefixLabel = wx.StaticText(self, label="Package name prefix:")
        app_constants.set_title_font(prefixLabel)
        self.prefix = wx.TextCtrl(self, value="", size=(300, -1))

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(prefixLabel, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT | wx.TOP, 10)
        self.SetSizer(vbox_main)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.prefix, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT, 10)
        self.SetSizer(vbox_main)

        fileLabel = wx.StaticText(self, label="File name:")
        app_constants.set_title_font(fileLabel)
        self.file = wx.TextCtrl(self, value="", size=(300, -1))

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(fileLabel, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT | wx.TOP, 10)
        self.SetSizer(vbox_main)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.file, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT, 10)
        self.SetSizer(vbox_main)

        valueLabel = wx.StaticText(self, label="Package Name:")
        app_constants.set_title_font(valueLabel)
        self.value = wx.TextCtrl(self, value="", size=(300, -1))
        self.value.SetHint("e.g. A001 (must be exactly 4 characters)")

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
                    
                    
                    
                    