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
#     Properties panel class.This class displays the app's UI for the Property Frame using wxPython widgets. 
#     In this frame, the user can type in all of the fields for a new property and then add that property to the current element tree.
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

class PropertyPanel(wx.Panel):

    # initializes the Property Frame with the appropriate wxPython widgets
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour("white")
        # saves reference to the Main Window to reopen it once the Property Frame is closed.
        self.main_window = parent.GetParent()
        self.vbox_main = wx.BoxSizer(wx.VERTICAL)
        # getting the initial width and height of the frame (in order to size the grid columns correctly)
        w, h = self.main_window.GetClientSize()

        # adding the properties grid and the add property button to the properties panel
        self.props_grid = grid.Grid(self, size=(5000, 300))
        self.props_grid.CreateGrid(0, 3)

        # sets the initial sizes for the property grid columns
        self.props_grid.SetColSize(0, (w - 80) / 3)
        self.props_grid.SetColSize(1, 80)
        self.props_grid.SetColSize(2, (w - 80) / 3)

        self.props_grid.SetColLabelValue(0, "Property Name")
        self.props_grid.SetColLabelValue(1, "Data Type")
        self.props_grid.SetColLabelValue(2, "Value")
        self.props_grid.SetLabelFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Intel Clear"))
        self.props_grid.SetLabelTextColour(app_constants.COLOR_PURPLE4)
        

        # calls certain functions when user changes a properties grid cell or right clicks on a properties grid cell
        self.props_grid.Bind(grid.EVT_GRID_CELL_CHANGED, self.OnPropsGridCellChange)
        self.props_grid.Bind(grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnPropsGridRightClick)
        self.props_grid.GetGridWindow().Bind(wx.EVT_MOTION, self.onPropsGridMouseOver)

        self.addPropBtn = wx.Button(self, label="Add Property", size=(-1, 35))
        app_constants.set_button_font(self.addPropBtn)
        self.addPropBtn.Bind(wx.EVT_BUTTON, self.open_property_frame)
        self.addPropBtn.Disable()

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.props_grid, 0, wx.LEFT, 5)
        self.vbox_main.Add(hbox, 0, wx.TOP, 10)
        self.SetSizer(self.vbox_main)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.addPropBtn, 0, wx.LEFT, 5)
        self.vbox_main.Add(hbox, 0, wx.TOP, 10)
        self.SetSizer(self.vbox_main)

        self.SetAutoLayout(True)
        self.props_grid.Bind(wx.EVT_SIZE, self.resize_props_grids)

    # called when the user changes a cell in the properties grid (the value cell)
    def OnPropsGridCellChange(self, event):
        # collects the new property value, the previous value, the property's name,
        # and initializes user_choice (used for warning box) to none
        value = self.props_grid.GetCellValue(event.GetRow(), event.GetCol())
        
        old_value = event.GetString()
        prop_name = self.props_grid.GetCellValue(event.GetRow(), 0)
        user_choice = wx.ID_NONE

        # defines the message to be sent if property value is updated in the model
        message = [prop_name, value, old_value]

        # TODO: currently, this function is being called multiple times when a
        # user only changes a grid cell once - after the first correct function call,
        # the old_value is equal to the new value. This if statement is to prevent the warning dialogs
        # to show up more than once when the function is called with these incorrect values.
        if old_value != value:

            # if user changes a property's name, that property name is updated in the model
            if event.GetCol() == 0:
                message = [value, old_value]
                self.main_window.property_name_changed(message=message)
            # if user changes a property's value:
            else:
                # iterates through the current tree's properties to find the one that was just edited by the user -
                # once it finds this it then finds the list of dependent packages (if any)-
                # that are attached to this property
                for prop in self.main_window.curr_tree.getroot().find('Properties').iter('Property'):
                    if prop.find('Name').text == prop_name:

                        # TODO: move the following data validation to the Controller
                        # (checking data type matches what the user entered)

                        # if new value is not the correct data type, an error message is shown and
                        # value won't be updated
                        # For properties with dependent packages, check_type does not allow duplicates
                        has_dependant_packages = bool(prop.find('DependentPackages'))
                        ret, msg, value = self.check_type(prop.find('DataType').text, value, has_dependant_packages)
                        if ret is not True:
                            wx.MessageBox(message=msg, caption='Property value type check failed.',
                                          style=wx.OK | wx.ICON_ERROR)
                            self.props_grid.SetCellValue(event.GetRow(), event.GetCol(), old_value)
                        else:
                            self.props_grid.SetCellValue(event.GetRow(), event.GetCol(), value)
                            pckg_list = prop.find('DependentPackages').findall('Package')

                            # if there is at least one dependent package in this property,
                            # the tool checks if the new value is different than the previous value-
                            # if so, the user is warned that some of their hierarchical properties might be deleted.
                            # If they decide to continue, then the property value is changed in the model.
                            # If not, the value is chagned back to the previous value.
                            if len(pckg_list) > 0:
                                if (value != old_value) & (old_value != ''):
                                    user_choice = wx.MessageBox(message=value + ' is different than your previous value for this property. If you continue, some hierarchical properties and their data may be automatically deleted. Do you want to continue?',
                                                                caption='Property value warning',
                                                                style=wx.YES_NO | wx.ICON_WARNING)

                                if user_choice != wx.NO:
                                    self.property_value_changed(message=message)
                                else:
                                    self.props_grid.SetCellValue(event.GetRow(), event.GetCol(), old_value)

                            # if there are no dependent packages in this property,
                            # the property value is changed in the model
                            else:
                                self.property_value_changed(message=message)

    #called when user inputs a value for a property that does not have dependent packages - updates model's data and view's UI with this data
    def property_value_changed(self, message):
        #Print statement for debugging purposes:
        self.set_data_changed(True)
        print("setting data changed to true")

        self.main_window.model.update_property_value(message)
        new_tree = self.main_window.model.get_curr_tree()
        self.main_window.refresh(new_tree)

        new_tree_list = self.main_window.model.get_tree_list()
        self.main_window.refresh_tree(new_tree_list)

    # updates the value of data_changed variable - called when some data is updated by user
    def set_data_changed(self, value):
        self.data_changed = value
        print("data changed set to " + str(value))

    # called when the user resizes the frame - resizes the properties grid accordingly
    def resize_props_grids(self, event):
        w, h = self.main_window.GetClientSize()
        self.props_grid.SetColSize(0, (w - 80) / (3))
        self.props_grid.SetColSize(1, 80)
        self.props_grid.SetColSize(2, (w - 80) / (3))
        event.Skip()

    # called when the user exits the window - does not add any new property
    def close_window(self, event):
        self.main_window.Enable()
        self.Destroy()

    # re-opens the Main Window, sends out all of the information for the new property the user just added in a message
    # to the rest of the program, and closes the Property Window
    def open_main(self, event):

        # creates a list with all of the tag values for the new property
        nameMsg = self.name.GetValue()
        dataMsg = self.combo.GetValue()
        descriptionMsg = self.description.GetValue()
        requiredMsg = self.required.GetValue()
        modifyMsg = self.modify.GetValue()
        valueMsg = self.value.GetValue()
        messageList = [nameMsg, dataMsg, int(requiredMsg), descriptionMsg, int(modifyMsg), valueMsg]

        if (nameMsg == '') | (dataMsg == '') | (valueMsg == ''):
            wx.MessageBox(message='Please fill out all information for the property before adding it.',
                          caption='Property error',
                          style=wx.OK | wx.ICON_ERROR)

        else:
            self.property_added(message=messageList)
            self.main_window.Enable()
            self.Close()

    def check_type(self, data_type, val, has_dependent_packages):
        """
        Takes a data type and a value that was just chosen for a property and
        Args:
            data_type (string): the data type of the value
            val (any): the value to be validated
            has_dependent_packages (bool): if a package property has dependent packages, do not allow duplicates in the value
        Returns:
            (bool): if the value is valid given the data type
            msg (string): the error message, if invalid
            val (any): the value passed in that was checked
        """
        # TODO: move this type checking to the Controller
        msg = ""
        valid_data = False
        if data_type == 'String':
            # String can have any format
            return True, msg, val

        if data_type == 'BitMap':
            # Bitmap - '0b' and then up to 32 binary values or a hexadecimal value

            if val == "":
                return True, msg, val

            if val[:2]=="0b":
                pattern = '^0[bB][0-1]+$'
                match = re.match(pattern, val)

                if match == None: 
                    msg = "Bitmap should be 64bit binary value starts with 0b (as a series of 0's or 1's from MSB to LSB) or a hexadecimal value starts with 0x."
                    return False, msg, val

                pattern = re.compile('[^01]')
                if len(val[2:])<65 and not len(pattern.findall(val[2:])):
                    valid_data = True
                else:
                    msg = "Not a valid binary value."
                    valid_data = False
            elif val[:2]=="0x":
                pattern = '^0[xX][0-9a-fA-F]+$'
                match = re.match(pattern, val)

                if match == None: 
                    msg = "Bitmap should be 64bit binary value starts with 0b (as a series of 0's or 1's from MSB to LSB) or a hexadecimal value starts with 0x.)"
                    return False, msg, val

                if hex(int(val[2:],16))<hex(int("FFFFFFFF",16)):
                    valid_data = True
                else:
                    msg = "Input value larger than 0xFFFFFFFF."
                    valid_data = False
            else:
                msg = "Bitmap should be 64bit binary value starts with 0b (as a series of 0's or 1's from MSB to LSB) or a hexadecimal value starts with 0x."
                valid_data = False
            return valid_data, msg, val

        if data_type == 'Package':
            # Package - a series of values (decimal to hexadecimal) separated by a comma and a space

            if val == "":
                return True, msg, val

            #check the input matches what a package should look like (list of values seperated by a comma and a space)
            # TODO: Allow for {} values since packages could contain more packages
            pattern = '^(((0x[a-zA-Z0-9]+)|([0-9]+)),\s)*((0x[a-zA-Z0-9]+)|([0-9]+))$'
            match = re.match(pattern, val)

            if match == None: 
                msg = "Package should list its values with a comma and a space in between each one (i.e. 4, 0x16, 12)"
                return False, msg, val

            if has_dependent_packages:
                #check there are no repeating values in the list (decimal or hexadecimal)
                decimal_value = []
                seen = []
                value_list = val.split(", ")
                for value in value_list:
                    if value[:2]=="0x":
                        value = value[2:]
                        value = int(value, 16)
                        decimal_value.append(int(value))
                    else:
                        decimal_value.append(int(value))
                for value in decimal_value:
                    if value in seen:
                        msg = "Package should not contain two or more of the same value (i.e. 0xA, 12, 10)."
                        return False, msg, val
                    seen.append(value)

            return True, msg, val

        if data_type == 'Boolean':

            if val == "":
                return True, msg, val

            # Boolean - either 1 or 0
            pattern = '^[0-1]$'
            match = re.match(pattern, val)
            if match:
                return True, msg, val
            else:
                msg = "Boolean should be entered in format either 0 or 1. Where 0: False 1:True"
                return False, msg, val

        if data_type == 'Integer':
            # Integer - can either be in decimal or hex
            # (either a series of numbers or a series of numbers and letters A-F)
            # can match integers against multiple regexes (one for hex - '0x[A-F0-9]', one for decimal)
            pattern_dec = '^[0-9]*$'
            pattern_hex = '^0x[a-fA-F0-9]*$'
            match_hex = re.match(pattern_hex, val)
            match_dec = re.match(pattern_dec, val)

            if match_hex:
                return True, msg, val
            elif match_dec:
                return True, msg, val
            else:
                msg = "Integer should be entered in decimal (12) or hexidecimal (0xF)"
                return False, msg, val

    # enables the buttons and certain menu items in the main window, disables other menu items in the main window

    # called when user right clicks on a property in the properties grid -
    # opens a pop up menu with the option to delete that property
    def OnPropsGridRightClick(self, event):

        # gets the current width and height of the window and the position where the user clicked
        w, h = self.GetClientSize()
        point = event.GetPosition()

        # takes the x position of where the user clicked and offsets it by .25*w (to account for tree panel on the left)
        point.x = (w * 0.25) + point.x

        # finds the name of the property to be deleted (to be used in the delete_property function)
        self.delete_property_name = self.props_grid.GetCellValue(event.GetRow(), 0)

        # creates a pop up menu with the option to delete and opens this menu at the correct screen position
        popUpMenu = wx.Menu()
        deleteItem = wx.MenuItem(popUpMenu, wx.NewId(), "Remove " + self.delete_property_name)
        popUpMenu.Append(deleteItem)
        popUpMenu.Bind(wx.EVT_MENU, self.main_window.delete_property, deleteItem)
        self.PopupMenu(popUpMenu, point)

    # called when the user moves the mouse over the screen
    def onPropsGridMouseOver(self, event):
        # gets position of the mouse on the screen and converts this to row and column
        x, y = self.props_grid.CalcUnscrolledPosition(event.GetX(), event.GetY())
        coordinates = self.props_grid.XYToCell(x, y)
        row = coordinates[0]
        column = coordinates[1]

        # gets the total number of rows and columns
        num_rows = self.props_grid.GetNumberRows()
        num_cols = self.props_grid.GetNumberCols()

        # if the mouse is over an actual row and column in the grid, find that row's property and
        # data type and display its description to the user
        if (column >= 0) & (column < num_cols) & (row >= 0) & (row < num_rows):
            data_type = self.props_grid.GetCellValue(row, 1)
            prop_name = self.props_grid.GetCellValue(row, 0)

            # find the description for the property the user is hoering over
            for prop in self.main_window.curr_tree.getroot().find('Properties').iter('Property'):
                if prop.find('Name').text == prop_name:
                    description = prop.find('Description').text
                    if description is None:
                        description = ""

                    # add a string that gives information on how the current property's data type should be entered
                    data_mssg = ''
                    if data_type == 'Integer':
                        data_mssg = "Integer should be entered in decimal (i.e. 12) or hexidecimal (i.e. 0xF)"
                    if data_type == 'String':
                        data_mssg = "String can be entered in any format."
                    if data_type == 'Boolean':
                        data_mssg = "Boolean should be entered in format either 0 or 1. Where 0: False 1:True"
                    if data_type == 'Package':
                        data_mssg = "Package should be entered as a list of values with a comma and a space in between each one (i.e. 4, 1, 12)"
                    if data_type == 'BitMap':
                        data_mssg = "Bitmap should be entered as a series of 0's or 1's (up to 64 bits). Value goes from MSB to LSB."
                    msg = description + ":" + "\n\n" + data_mssg
                    # event.GetEventObject().SetToolTip(msg)
                    self.main_window.description_panel.SetValue(msg)

    # temporarily disables the Main Frame and opens the Property Frame (where user can add a new property to the
    # current Element Tree)
    def open_property_frame(self, event):

        dlg = AddProperty(self, -1, "Add property", size=(450, 800),
                          style=wx.DEFAULT_DIALOG_STYLE)
        dlg.CenterOnScreen()
        val = dlg.ShowModal()

        if val == wx.ID_OK:
            # creates a list with all of the tag values for the new property
            nameMsg = dlg.name.GetValue()
            dataMsg = dlg.combo.GetValue()
            descriptionMsg = dlg.description.GetValue()
            requiredMsg = dlg.required.GetValue()
            modifyMsg = dlg.modify.GetValue()
            valueMsg = dlg.value.GetValue()
            messageList = [nameMsg, dataMsg, int(requiredMsg), descriptionMsg, int(modifyMsg), valueMsg]

            if (nameMsg == '') | (dataMsg == '') | (valueMsg == ''):
                wx.MessageBox(message='Please fill out all information for the property before adding it.',
                              caption='Property error', style=wx.OK | wx.ICON_ERROR)
            else:
                self.main_window.property_added(message=messageList)
                
class AddProperty(wx.Dialog):

    def __init__(self, parent, ID, title, size=wx.DefaultSize, pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):
        wx.Dialog.__init__(self, parent, ID, title, pos, size, style)
        self.parent = parent
        pre = wx.Dialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        pre.Create(parent, ID, title, pos, size, style)

        vbox_main = wx.BoxSizer(wx.VERTICAL)

        nameLabel = wx.StaticText(self, -1, label="Name: ")
        app_constants.set_title_font(nameLabel)
        self.name = wx.TextCtrl(self, -1, value="", size=(300, -1))

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(nameLabel, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT | wx.TOP, 10)
        self.SetSizer(vbox_main)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.name, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT, 10)
        self.SetSizer(vbox_main)

        dataLabel = wx.StaticText(parent=self, label="Data Type:")
        app_constants.set_title_font(dataLabel)
        my_list = ['String', 'Integer', 'Package', 'Boolean', 'Bitmap']
        self.combo = wx.ComboBox(self, choices=my_list)
        self.combo.Select(0)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(dataLabel, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT | wx.TOP, 10)
        self.SetSizer(vbox_main)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.combo, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT, 10)
        self.SetSizer(vbox_main)

        descriptionLabel = wx.StaticText(self, label="Description:")
        app_constants.set_title_font(descriptionLabel)
        self.description = wx.TextCtrl(self, -1, value="", size=(300, 100))

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(descriptionLabel, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT | wx.TOP, 10)
        self.SetSizer(vbox_main)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.description, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT, 10)
        self.SetSizer(vbox_main)

        requiredLabel = wx.StaticText(self, label="Required:")
        app_constants.set_title_font(requiredLabel)
        self.required = wx.CheckBox(self)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(requiredLabel, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT | wx.TOP, 10)
        self.SetSizer(vbox_main)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.required, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT, 10)
        self.SetSizer(vbox_main)

        modifyLabel = wx.StaticText(self, label="OEM modifiable:")
        app_constants.set_title_font(modifyLabel)
        self.modify = wx.CheckBox(self)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(modifyLabel, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT | wx.TOP, 10)
        self.SetSizer(vbox_main)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.modify, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT, 10)
        self.SetSizer(vbox_main)

        valueLabel = wx.StaticText(self, label="Value:")
        app_constants.set_title_font(valueLabel)
        self.value = wx.TextCtrl(self, -1, value="", size=(300, -1))

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
                
                