#  ------------------------------------------------------------------------------
#
#  Copyright 2021, MIPI Alliance and its contributors.
#  SPDX-License-Identifier: BSD-3-Clause
#
#  Module Name:
#
#    disco_main.py
#
#  Abstract:
#
#    Main AuiManager class for handling the communication between the GUI  and the model.
#
#  -------------------------------------------------------------------------------

from __future__ import absolute_import

import os
import wx
import multiprocessing
import wx.lib.agw.aui as aui
import sys
import re
import wx.grid as grid
import logging
import xml.dom.minidom as md
import xml.etree.ElementTree as et
import numpy as np
import json

try:
    import disco
    import  disco.disco_constants as app_constants
    import disco.disco_strings as disco_str
    import disco.model as model
    from disco.properties import PropertyPanel
    from disco.hierarchical_properties import HierarchicalPropertyPanel
    from disco.bufferdata_properties import BufferDataPropertyPanel, EditBufferDataPropertyValue
    from disco.ASLgenerator import GenerateASLFrame
    from disco.disco_help import DisCoInfo
except:
    import disco_constants as app_constants
    import disco_strings as disco_str
    import model
    from properties import PropertyPanel
    from hierarchical_properties import HierarchicalPropertyPanel
    from bufferdata_properties import BufferDataPropertyPanel, EditBufferDataPropertyValue
    from ASLgenerator import GenerateASLFrame
    from disco_help import DisCoInfo


class DiscoToolAuiManager(wx.Frame):
    """
    An DisCo tool AUI manager is used to do following tasks:
    Create aui manager based framework and displays the app's UI for the Main Frame.
    When events occur in the UI that change the  app's data, this class sends out messages to the Controller.
    """

    def __init__(self, parent, ID, argv, title=disco_str.DISCO_STR_TITLE,
                 pos=wx.DefaultPosition,
                 size=app_constants.MAIN_FRAME_SIZE_WxH,
                 style=wx.DEFAULT_FRAME_STYLE | wx.SUNKEN_BORDER):
        """
        __init__(self, Window parent,id,title,position,size,style)
            An DisCo tool AUI manager is used to do following tasks:
            Create aui manager based framework and displays the app's UI for the Main Frame.
            When events occur in the UI that change the  app's data, this class sends out messages to the Controller.
        """
        wx.Frame.__init__(self, parent, ID, title, pos, size, style)
        self.SetMinSize(app_constants.MAIN_FRAME_SIZE_WxH)
        self.SetBackgroundColour(app_constants.COLOR_WHITE)
        self.CurrentFrameSize = app_constants.MAIN_FRAME_SIZE_WxH
        self.data_changed = False
        self.has_project_path = False
        self.tree_list = None
        self.curr_tree = None
        self.app_data_path = None
        self.model = model.model()

        # Application path
        app_filepath = sys.argv[0]
        if app_filepath.startswith('"'):
            app_filepath = app_filepath[1:]
        if app_filepath.endswith('"'):
            app_filepath = app_filepath[:-1]
        uirealpath = os.path.realpath(app_filepath)
        self.app_data_path = os.path.dirname(uirealpath)
        try:
            self.SetIcon(wx.Icon(os.path.join(self.app_data_path,"images", "MIPIfavicon.ico"), wx.BITMAP_TYPE_ICO))
        except:
            self.app_data_path = os.path.dirname(disco.__file__)
            self.app_data_path = os.path.join(self.app_data_path, "disco")
            self.SetIcon(wx.Icon(os.path.join(self.app_data_path,"images", "MIPIfavicon.ico"), wx.BITMAP_TYPE_ICO))

        self.statusBar = self.CreateStatusBar(1)

        # setting up the menu bar at the top of the window that has a list of buttons the user can click to start a new
        # project/open an existing project/save/save as/generate ASL
        menuBar = wx.MenuBar()
        fileMenu = wx.Menu()
        menuBar.Append(fileMenu, "&File")

        self.item_new = wx.MenuItem(fileMenu, wx.ID_FILE, "&New...", "Create new project")
        fileMenu.Append(self.item_new)
        self.item_open = wx.MenuItem(fileMenu, wx.ID_OPEN, "&Open Project...", "Load existing project")
        fileMenu.Append(self.item_open)
        self.item_save = wx.MenuItem(fileMenu, wx.ID_SAVE, "&Save", "Save project")
        fileMenu.Append(self.item_save)
        self.item_save_as = wx.MenuItem(fileMenu, wx.ID_SAVEAS, "Save &As...", "Save project in new location")
        fileMenu.Append(self.item_save_as)
        self.item_generate_asl = wx.MenuItem(fileMenu, wx.ID_NEW, "&Generate ASL", "Generate ASL")
        fileMenu.Append(self.item_generate_asl)
        fileMenu.Append(wx.MenuItem(fileMenu, wx.ID_EXIT, text="E&xit"))

        #Help menu
        helpMenu = wx.Menu()
        menuBar.Append(helpMenu, "&Help")        
        self.item_about = wx.MenuItem(helpMenu, wx.ID_ABOUT, "&About DisCo", "About DisCo creation tool")
        helpMenu.Append(self.item_about)
        
        
        self.item_save.Enable(False)
        self.item_save_as.Enable(False)
        self.item_generate_asl.Enable(False)

        self.SetMenuBar(menuBar)
        self.Bind(wx.EVT_MENU, self.menuHandler)

        # Create panel for frame
        self.auimainpanel = wx.Panel(self)
        # Create aui manager for GUI frame
        self.aui_manager = aui.AuiManager()
        self.aui_manager.SetManagedWindow(self.auimainpanel)

        # Header
        self.headerpanel = HeaderPanel(self.auimainpanel)

        self.aui_manager.AddPane(self.headerpanel,
                                 aui.AuiPaneInfo().Name("top").BestSize((-1, 50)).MinSize((-1, 50)).
                                 Top().Layer(2).
                                 CloseButton(False).
                                 MaximizeButton(False).
                                 Resizable(False).
                                 CaptionVisible(visible=False).
                                 MinimizeButton(False).
                                 PaneBorder(False).
                                 Floatable(False).
                                 PaneBorder(False))

        self.tree_panel = wx.TreeCtrl(self.auimainpanel, -1, wx.Point(0, 0), wx.Size(160, 250),
                                       wx.TR_DEFAULT_STYLE | wx.NO_BORDER)
        self.tree_panel.SetBackgroundColour(app_constants.COLOR_WHITE)
        self.aui_manager.AddPane(self.tree_panel, aui.AuiPaneInfo().
                                 Name("treepanel").BestSize((app_constants.SIDE_PANEL_WIDTH, -1)).MinSize((app_constants.SIDE_PANEL_WIDTH, -1)).
                                 Left().Layer(2).
                                 CloseButton(False).
                                 MaximizeButton(False).
                                 MinimizeButton(False).
                                 PaneBorder(False).
                                 Floatable(False))

        self.properties_panel = PropertyPanel(self.auimainpanel)
        self.properties_panel.SetBackgroundColour(app_constants.COLOR_WHITE)
        self.aui_manager.AddPane(self.properties_panel, aui.AuiPaneInfo().
                                 Name("propertiespanel").BestSize((-1, 250)).MinSize((-1, 250)).
                                 CenterPane().CloseButton(False).MaximizeButton(False).
                                 MinimizeButton(False).
                                 PaneBorder(False).
                                 Floatable(False))

        self.packages_panel = HierarchicalPropertyPanel(self.auimainpanel)
        self.packages_panel.SetBackgroundColour(app_constants.COLOR_WHITE)
        self.aui_manager.AddPane(self.packages_panel, aui.AuiPaneInfo().
                                 Name("packagespanel").BestSize((-1, 250)).MinSize((-1, 250)).
                                 CenterPane().
                                 CloseButton(False).
                                 MaximizeButton(False).
                                 MinimizeButton(False).
                                 PaneBorder(False).
                                 Floatable(False))


        self.buffprops_panel = BufferDataPropertyPanel(self.auimainpanel)
        self.buffprops_panel.SetBackgroundColour(app_constants.COLOR_WHITE)
        self.aui_manager.AddPane(self.buffprops_panel, aui.AuiPaneInfo().
                                 Name("packagespanel2").BestSize((-1, 250)).MinSize((-1, 250)).
                                 CenterPane().
                                 CloseButton(False).
                                 MaximizeButton(False).
                                 MinimizeButton(False).
                                 PaneBorder(False).
                                 Floatable(False))

        self.description_panel = wx.TextCtrl(self.auimainpanel, value="",
                                             style=wx.TE_MULTILINE | wx.TE_READONLY)
        app_constants.set_text_font(self.description_panel)
        self.aui_manager.AddPane(self.description_panel, aui.AuiPaneInfo().
                                 Name("DescriptionPanel").Caption("Description").BestSize((app_constants.SIDE_PANEL_WIDTH, -1)).MinSize((app_constants.SIDE_PANEL_WIDTH, -1)).
                                 Right().CloseButton(False).MaximizeButton(False).
                                 MinimizeButton(False).PaneBorder(False).Floatable(False))

        # adding all of the widgets to the tree panel
        self.hier_tree = self.tree_panel
        self.hier_tree.SetFont(wx.Font(13, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Intel Clear"))
        self.hier_tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnTreeItemActivated)
        self.hier_tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeItemSelectionChanged)
        self.Show()

        # tell the manager to 'commit' all the changes just made
        self.aui_manager.Update()
        self.aui_manager.SetAGWFlags(self.aui_manager.GetAGWFlags() ^ aui.AUI_MGR_TRANSPARENT_DRAG)

        # main frame events
        self._bind_mainframe_events()

    def close_main_window(self, event):
        """
        Called when the user closes the main window: if there are any unsaved changes,
        the tool will ask the user if they want to save these before exiting
        and calls "Save" in the controller if they say yes
        """

        # result variable corresponds to how the user responds to the message box warning
        result = wx.ID_NONE

        if self.data_changed is True:
            result = wx.MessageBox(message=disco_str.DISCO_STR_CLOSE_MSG,
                                   caption='Unsaved Changes', style=wx.YES_NO | wx.ICON_WARNING)
            if result == wx.YES:
                # will save to previous location or use a dialog box
                # to get location from user if files haven't been saved yet
                if self.has_project_path is False:
                    self.save_dir_dialog()
                else:
                    self.save_files(message=None)
        self.Destroy()

    def delete_property(self, event):
        """Called if user right clicks on a property and chooses "delete" from the pop up menu"""
        self.property_deleted(message=self.properties_panel.delete_property_name)

    def delete_hier_property(self, event):
        """Called if user right clicks on a property and chooses "delete" from the pop up menu"""
        self.hier_property_deleted(message=[self.packages_panel.delete_property_name, None, None, self.curr_tree])

    def OnTreeItemSelectionChanged(self, event):
        """
        Called when the user single clicks on an item in the treectrl.
        Collects the text of the treeCtrl item that was clicked on as well as the root of the treeCtrl
        """
        text = self.hier_tree.GetItemText(event.GetItem())
        root = self.hier_tree.GetRootItem()

        # expands and colors the treeCtrl item that was clicked on and sets the focus (highlight) to that item as well
        self.ExpandAndColorTreeItem(root, text)
        self.hier_tree.SetFocusedItem(event.GetItem())

    def OnTreeItemActivated(self, event):
        """Called when the user double clicks or uses keyboard on a new item in the hierarchical list of packages"""
        # collects the text of the treeCtrl item that was clicked on as well as the root of the treeCtrl
        text = self.hier_tree.GetItemText(event.GetItem())
        root = self.hier_tree.GetRootItem()

        # expands and colors the treeCtrl item that was clicked on and sets the focus (highlight) to that item as well
        self.ExpandAndColorTreeItem(root, text)
        self.hier_tree.SetFocusedItem(event.GetItem())

        # sends message to the Controller that a new item in the treeCtrl was chosen
        self.new_tree_chosen(message=text)

    def ExpandAndColorTreeItem(self, root, text):
        """Expands and colors green the treeCtrl item that corresponds to the text value passed in and its children"""

        # finds the child of the current root
        child, cookie = self.hier_tree.GetFirstChild(root)

        # if child item matches the given text value, set its color to green and expand it -
        # then recursively call function with the child
        # set as the root and continue the loop with the next child of the current root
        while child.IsOk():
            if self.hier_tree.GetItemText(child) == text:
                self.hier_tree.EnsureVisible(child)
                self.hier_tree.SetItemTextColour(child, wx.Colour(0, 255, 0))
                self.hier_tree.SetItemBackgroundColour(child, wx.Colour(0, 0, 255))
            else:
                self.hier_tree.SetItemTextColour(child, wx.Colour(0, 0, 0))
                self.hier_tree.SetItemBackgroundColour(child, wx.Colour(255, 255, 255))
            self.ExpandAndColorTreeItem(child, text)
            child, cookie = self.hier_tree.GetNextChild(child, cookie)

    def is_ancestor(self, higher_tree, lower_tree):
        """
        Helper function for OnPacksGridCellChange.
        Returns True if higher_tree is an ancestor of lower_tree
        """

        higher_name = higher_tree.getroot().find('Name').text
        lower_name = lower_tree.getroot().find('Name').text

        # Base case: if the trees are the same, return true
        if higher_name == lower_name:
            return True

        # Recursive case: loop through the hierarchical properties of the higher_tree.
        # For each one, find its associated element tree
        # and call this function again with this element tree as the higher_tree.
        for hier_prop in higher_tree.getroot().find('HierarchicalProperties').iter('HierarchicalProperty'):
            name = hier_prop.find('Value').text
            for tree in self.tree_list:
                if tree.getroot().find('Name').text == name:
                    result = self.is_ancestor(tree, lower_tree)
                    if result is True:
                        return True

        # If the function goes through all of the trees under higher_tree and
        # does not find a match to lower_tree, return False
        return False

    # TODO: move this type checking to the Controller
    def check_type(self, data_type, val):
        """
        Takes in a data type and a value that was just chosen for a property
        Returns (True, "") if the value is of the correct data type,
        or (False, error_message) otherwise
        """
        msg = ""
        if data_type == 'String':
            # String - do we need a regex here?
            pattern = '^\S*$'
            match = re.match(pattern, val)
            if match:
                return True, msg
            else:
                msg = "String can have any format."
                return False, msg

        if data_type == 'BitMap':
            # Bitmap - '0b' and then up to 32 binary values
            pattern = '^[0-1]{1,32}$'
            match = re.match(pattern, val)
            if match:
                return True, msg
            else:
                msg = "Bitmap should be entered as a series of 0's or 1's (up to 64 bits). Value goes from MSB to LSB."
                return False, msg

        if data_type == 'Package':
            # Package - a series of values separated by a comma or a space or both
            # TODO: Allow for {} values since packages could contain more packages
            pattern = '^([0-9]+,\s)*([0-9]+)$'
            match = re.match(pattern, val)
            if match:
                return True, msg
            else:
                msg = "Package should list its values with a comma and a space in between each one (i.e. 4, 1, 12)"
                return False, msg

        if data_type == 'Boolean':
            # Boolean - either 1 or 0
            pattern = '^[0-1]$'
            match = re.match(pattern, val)
            if match:
                return True, msg
            else:
                msg = "Boolean should be entered in format either 0 or 1. Where 0: False 1:True"
                return False, msg

        if data_type == 'Integer':
            # Integer - can either be in decimal or hex
            # (either a series of numbers or a series of numbers and letters A-F)
            # can match integers against multiple regexes (one for hex - '0x[A-F0-9]', one for decimal)
            pattern_dec = '^[0-9]*$'
            pattern_hex = '^0x[a-fA-F0-9]*$'
            match_hex = re.match(pattern_hex, val)
            match_dec = re.match(pattern_dec, val)

            if match_hex:
                return True, msg
            elif match_dec:
                return True, msg
            else:
                msg = "Integer should be entered in decimal (12) or hexidecimal (0xF)"
                return False, msg

    def enable_buttons(self):
        """Enables the buttons and certain menu items in the main window, disables other menu items in the main window"""
        self.packages_panel.addHierPropBtn.Enable()
        self.properties_panel.addPropBtn.Enable()
        self.buffprops_panel.addbufferdataBtn.Enable()
        self.item_save.Enable(True)
        self.item_save_as.Enable(True)
        self.item_generate_asl.Enable(True)
        self.item_new.Enable(False)
        self.item_open.Enable(False)

    def menuHandler(self, event):
        """Defines what function the program calls when a particular menu item is chosen"""
        id = event.GetId()
        if id == wx.ID_ABOUT:
            about = DisCoInfo(self)
            about.ShowModal()
            about.Destroy()           
        if id == wx.ID_FILE:
            status = self.open_file_dialog()
            if status is True:
                self.enable_buttons()
        if id == wx.ID_OPEN:
            status = self.open_dir_dialog()
            if status is True:
                self.enable_buttons()
        if id == wx.ID_SAVE:
            # TODO: if they created a new project, need to open a dialog box the first time they save
            if self.has_project_path is False:
                self.save_dir_dialog()
            else:
                self.save_files(message=None)
        if id == wx.ID_SAVEAS:
            self.save_dir_dialog()
        if id == wx.ID_NEW:
            # open up an ASL generator window where user enters the device name/_HID or _CID or _ADR
            # and then ASL is generated
            self.Disable()
            new_frame = GenerateASLFrame(self)
            new_frame.Show()
        if id == wx.ID_EXIT:
            self.Close()
            # when user closes main window, the tool will first check if their data is saved
            # self.Bind(wx.EVT_CLOSE, self.close_main_window)

    def open_dir_dialog(self):
        """
        Opens the file dialog where the user chooses the directory with all of the intermediate files for the project
        the user wants to continue editing. This directory's path is then sent in a message to the rest of the program.
        """
        status = False

        dlg = wx.DirDialog(self, "Choose existing project", style=wx.DD_DEFAULT_STYLE)

        if dlg.ShowModal() == wx.ID_OK:

            path = os.path.join(dlg.GetPath(), "_DSD.xml")
            f = open(path, 'r', encoding='utf-8')

            with f:
                data = f.read()
                self.new_project_chosen(message=dlg.GetPath())
                status = True
                self.has_project_path = True

        dlg.Destroy()
        return status

    def save_dir_dialog(self):
        """
        Opens a file dialog where the user chooses where they want to save their project
        (when they 'save as' or 'save' for the first time)
        """

        dlg = wx.DirDialog(self, "Choose directory to save to", style=wx.DD_DEFAULT_STYLE)

        if dlg.ShowModal() == wx.ID_OK:
            self.has_project_path = True
            self.save_as(message=dlg.GetPath())

        dlg.Destroy()

    def open_file_dialog(self):
        """
        Opens the file dialog where the user chooses the xml file to use as the starting template.
        This file's path is then sent in a message to the rest of the program.
        """
        wildcard = "XML Files (*.xml)|*.xml"
        dlg = wx.FileDialog(self, "Open file", os.getcwd(), "", wildcard, wx.FD_OPEN)
        status = False

        if dlg.ShowModal() == wx.ID_OK:
            f = open(dlg.GetPath(), 'r', encoding='utf-8')

            with f:
                try:
                    data = f.read()
                    self.new_file_chosen(message=dlg.GetPath())
                except Exception as e:
                    wx.MessageBox(message=disco_str.DISCO_STR_TEMPLATE_ERROR_MSG, caption='Error reading template', style=wx.OK | wx.ICON_WARNING)
                    self.Destroy()

            status = True

        dlg.Destroy()
        return status

    def new_file_chosen(self, message):
        """Called when the starting xml template is chosen by the user. Updates model's data and view's UI with this data (message is the file path)"""
        self.properties_panel.set_data_changed(True)
        print("setting data changed to true")

        #starting file template name is always set to _DSD
        templateName = '_DSD'

        #gets directory name for the file the user just chose
        new_mssg = os.path.dirname(message)

        #creates element tree for starting xml file and calls helper function to add this element tree and any other ones already defined to the tree_list
        tree = et.parse(message)
        self.model.add_element_trees(tree, templateName, '1')

        #sets the template path to be the same location as the first template chosen
        self.model.set_template_path(new_mssg)

        #sets this starting xml file as the current element tree and refreshes both the tree and the tree_list in the View
        self.model.set_curr_tree(templateName)
        new_tree = self.model.get_curr_tree()
        self.refresh(new_tree)
        tree_list = self.model.get_tree_list()
        self.refresh_tree(tree_list)

    def new_project_chosen(self, message):
        """
        Called when an existing project is chosen by the user to continue working on.
        Updates model's data and view's UI with this data and adds any existing element trees in the intermediate xml files (message is the directory path)
        """
        #finds the starting template in this directory
        path = os.path.join(message, '_DSD.xml')
        tree = et.parse(path)

        #tree = et.parse(message + "\\_DSD.xml")
        print(message + "\\_DSD.xml")

        #adds all of the existing element trees and sets the project path to be the same location the user just chose
        self.model.set_project_path(message)
        self.model.add_element_trees(tree, '_DSD', '1')

        listPath = os.path.join(message, 'packageNameList.npy')
        with open(listPath, 'rb') as my_file:
            self.model.set_packageNameList(np.load(my_file))

        dictPath = os.path.join(message, 'propertyDict.json')
        with open(dictPath, 'r') as my_file:
            object = json.load(my_file)
            self.model.set_propertyDictionary(object)

        #sets this starting xml file as the current element tree and refreshes both the tree and the tree_list in the View
        self.model.set_curr_tree('_DSD')
        new_tree = self.model.get_curr_tree()
        self.refresh(new_tree)
        tree_list = self.model.get_tree_list()
        self.refresh_tree(tree_list)

    def new_tree_chosen(self, message):
        """
        Called when the user clicks on a new package in the hierarchy on the left of the screen.
        Changes the current tree and refreshes the view.
        message is the name of the new package chosen.
        """
        self.model.set_curr_tree(message)
        new_tree = self.model.get_curr_tree()
        self.refresh(new_tree)

    def property_added(self, message):
        """
        Called when a new property is added by the user.
        Updates model's data and view's UI with this data
        """
        #Print statement for debugging purposes:
        self.set_data_changed(True)
        print("setting data changed to true")

        self.model.add_property(message)
        new_tree = self.model.get_curr_tree()
        self.refresh(new_tree)

    def buff_property_added(self, message):
        """
        Called when a new buffer property is added by the user.
        Updates model's data and view's UI with this data
        """
        #Print statement for debugging purposes:
        self.set_data_changed(True)
        print("setting data changed to true")

        self.model.add_buff_property(message)
        new_tree = self.model.get_curr_tree()
        self.refresh(new_tree)

        tree_list = self.model.get_tree_list()
        self.refresh_tree(tree_list)

    def hier_property_value_changed(self, message):
        """
        Called when user inputs a value for a hierarchical property.
        Updates model's data and view's UI with this data
        """
        #Print statement for debugging purposes:
        self.set_data_changed(True)
        print("setting data changed to true")

        self.model.update_hier_property_value(message)

        new_tree = self.model.get_curr_tree()
        self.refresh(new_tree)

        tree_list = self.model.get_tree_list()
        self.refresh_tree(tree_list)

    def buff_property_value_changed(self, message):
        """
        Called when user inputs a value for a buffer property.
        Updates model's data and view's UI with this data
        """
        #Print statement for debugging purposes:
        self.set_data_changed(True)
        print("setting data changed to true")

        self.model.update_buff_property_value(message)

        new_tree = self.model.get_curr_tree()
        self.refresh(new_tree)

        tree_list = self.model.get_tree_list()
        self.refresh_tree(tree_list)

    def save_files(self, message):
        """
        Called when user presses the 'save' button.
        Saves all element trees as files named with their template names
        """
        #changes the set_data_changed variable to False because we just saved
        self.set_data_changed(False)
        print("initializing data changed to false")

        tree_list = self.model.get_tree_list()

        path = os.path.join(self.model.get_project_path(), "packageNameList.npy")
        with open(path, 'wb') as my_file:
            np.save(my_file, self.model.get_packageNameList())

        object = json.dumps(self.model.get_propertyDictionary(), indent=4)
        path = os.path.join(self.model.get_project_path(), "propertyDict.json")
        with open(path, "w") as my_file:
            my_file.write(object)
        
        #goes through the list of element trees and adds each one as an xml file to the current project path 
        for tree in tree_list:
            root = tree.getroot()
            file_name = root.find('Name').text + '.xml'

            #Print statement for debugging purposes:
            print("FILE NAME:" + file_name)

            #converting element tree to xml (adjust indents/newlines accordingly)
            tree_str = et.tostring(root)
            tree_str_parsed = md.parseString(tree_str)

            path = os.path.join(self.model.get_project_path(), file_name)

            #with open(self.model.get_project_path() +"\\" + file_name,'w') as my_file:
            with open(path, 'w', encoding="utf-8") as my_file:
                tree_str_pretty = tree_str_parsed.toprettyxml(indent='\t', newl='\n')
                tree_str_pretty = os.linesep.join([s for s in tree_str_pretty.splitlines() if s.strip()])
                my_file.write(tree_str_pretty)

    def save_as(self, message):
        """
        Called when user presses the "save as" button or when they save their work for the first time (message is the path the user chose to save to)
        """
        #changes the set_data_changed variable to False because we just saved
        self.set_data_changed(False)
        print("initializing data changed to false")

        tree_list = self.model.get_tree_list()

        path = os.path.join(message, "packageNameList.npy")
        with open(path, 'wb') as my_file:
            np.save(my_file, self.model.get_packageNameList())

        object = json.dumps(self.model.get_propertyDictionary(), indent=4)
        path = os.path.join(message, "propertyDict.json")
        with open(path, "w") as my_file:
            my_file.write(object)
        
        #goes through the list of element trees and adds each one as an xml file to the path the user chose
        for tree in tree_list:
            root = tree.getroot()
            file_name = root.find('Name').text + '.xml'

            #Print statement for debugging purposes:
            print("FILE NAME:" + file_name)

            #converting element tree to xml (adjust indents/newlines accordingly)
            tree_str = et.tostring(root)
            tree_str_parsed = md.parseString(tree_str)

            path = os.path.join(message, file_name)

            #with open(message + "\\" + file_name,'w') as my_file:
            with open(path, 'w', encoding="utf-8") as my_file:
                tree_str_pretty = tree_str_parsed.toprettyxml(indent='\t', newl='\n')
                tree_str_pretty = os.linesep.join([s for s in tree_str_pretty.splitlines() if s.strip()])
                my_file.write(tree_str_pretty)

        #updating the project path to be the path the user just chose
        self.model.set_project_path(message)

    def new_hier_property_added(self, message):
        """
        Called when the user is adding a new hierarchical property.
        message consists of property name/data type/required/description/OEMmodify/packagenameprefix/value/filename
        """

        #Print statement for debugging purposes:
        self.set_data_changed(True)
        print("setting data changed to true")

        self.model.add_new_hier_property(message)
        new_tree = self.model.get_curr_tree()
        self.refresh(new_tree)

        tree_list = self.model.get_tree_list()
        self.refresh_tree(tree_list)

    def property_deleted(self, message):
        """
        Called when the user deletes a property.
        Message consists of that property's name
        """
        #Print statement for debugging purposes:
        self.set_data_changed(True)
        print("setting data changed to true")

        self.model.delete_property(message)
        new_tree = self.model.get_curr_tree()
        self.refresh(new_tree)

        tree_list = self.model.get_tree_list()
        self.refresh_tree(tree_list)

    def hier_property_deleted(self, message):
        """
        Called when the user deletes a hierarchical property.
        message consists of property name, property location, package location, current tree
        (locations will be None if the hierarchical property does not come from a property's dependent package)
        """
        #Print statement for debugging purposes:
        self.set_data_changed(True)
        print("setting data changed to true")

        self.model.delete_hier_property(message)
        new_tree = self.model.get_curr_tree()
        self.refresh(new_tree)

        new_tree_list = self.model.get_tree_list()
        self.refresh_tree(new_tree_list)

    def property_name_changed(self, message):
        """Called when the user changes the name of a property (message = value, old_value)"""
        #Print statement for debugging purposes:
        self.set_data_changed(True)
        print("setting data changed to true")

        self.model.update_property_name(message)
        new_tree = self.model.get_curr_tree()
        self.refresh(new_tree)

    def hier_property_name_changed(self, message):
        """Called when the user changes the name of a hierarchical property (message = value, old_value)"""
        #Print statement for debugging purposes:
        self.set_data_changed(True)
        print("setting data changed to true")

        self.model.update_hier_property_name(message)
        new_tree = self.model.get_curr_tree()
        self.refresh(new_tree)

        new_tree_list = self.model.get_tree_list()
        self.refresh_tree(new_tree_list)

    def buff_property_name_changed(self, message):
        """Called when the user changes the name of a buffer property (message = value, old_value)"""
        #Print statement for debugging purposes:
        self.set_data_changed(True)
        print("setting data changed to true")

        self.model.update_buff_property_name(message)
        new_tree = self.model.get_curr_tree()
        self.refresh(new_tree)

    def set_data_changed(self, value):
        """Updates the value of data_changed variable. Called when some data is updated by user"""
        self.data_changed = value
        print("data changed set to "+ str(value))    

    def get_tree_list(self, message):
        """Called when the View needs to get the current tree list"""
        self.model.get_tree_list()

    def refresh_tree(self, tree_list):
        """
        Updates the hierarchy of packages (in the form of a treeCtrl) on the left side of the screen.
        Starts by clearing this treeCtrl,then adds _DSD as the root, then recursively adds new packages 
        based on hierarchical properties. Also adjusts the package labels,
        color and expansion based on the current element tree selected.
        """

        # updates the tree_list variable for the View
        self.tree_list = tree_list

        # clears out the treeCtrl before re-adding packages
        self.hier_tree.DeleteAllItems()

        # iterate through all element trees
        for tree in tree_list:
            name = tree.getroot().find('Name').text

            # if the element tree's name is '_DSD', set this as the root,
            # expand this tree item, and call recursive helper function to add its
            # children to the treeCtrl
            if name == '_DSD':
                self.root = self.hier_tree.AddRoot(name)
                self.hier_tree.EnsureVisible(self.root)
                self.add_tree_items(self.root, tree, tree_list, False)

            # expands all of the children nodes to '_DSD' (i.e. first level nodes) -
            # must do this because otherwise no other children are visible
            child, cookie = self.hier_tree.GetFirstChild(self.root)
            while child.IsOk():
                self.hier_tree.EnsureVisible(child)
                child, cookie = self.hier_tree.GetNextChild(self.root, cookie)

        # expands the root and colors it green to show it is the current tree selected
        self.ExpandAndColorTreeItem(self.root, self.curr_tree.getroot().find('Name').text)

    def add_tree_items(self, curr_root, curr_tree, curr_tree_list, visible):
        """
        Recursive helper function for refresh_tree. Adds hierarchical properties of the curr_tree as children nodes to the treeCtrl
        """
        # iterate through the current tree's hierarchical properties found-
        # within the dependent packages section of other properties
        for prop in curr_tree.getroot().find('Properties').iter('Property'):
            for package in prop.find('DependentPackages').iter('Package'):
                for hier_prop in package.find('HierarchicalProperties').iter('HierarchicalProperty'):
                    name = hier_prop.find('Value').text

                    # find the element tree corresponding to the current hierarchical property
                    for tree in curr_tree_list:
                        if tree.getroot().find('Name').text == name:

                            # appends this element tree as a child to the current root and
                            # sets EnsureVisible variable (which keeps track of whether or
                            # not the loop has reached the current element tree or not - if so,
                            # EnsureVisible is True and method will set all of the following children to be expanded)
                            new_tree_item = self.hier_tree.AppendItem(curr_root, name)
                            EnsureVisible = visible

                            # if the loop has reached the current element tree,
                            # EnsureVisible is set to True and the current treeCtrl item is expanded
                            if tree.getroot().find('Name').text == self.curr_tree.getroot().find('Name').text:
                                EnsureVisible = True
                            if EnsureVisible is True:
                                self.hier_tree.EnsureVisible(new_tree_item)

                            # recursive call to function with the new treeCtrl item as the current root and
                            # EnsureVisible set to new value
                            self.add_tree_items(new_tree_item, tree, curr_tree_list, EnsureVisible)

        # iterate through the current tree's hierarchical properties
        for hier_prop in curr_tree.getroot().find('HierarchicalProperties').iter('HierarchicalProperty'):
            name = hier_prop.find('Value').text

            # find the element tree corresponding to the current hierarchical property
            for tree in curr_tree_list:
                if tree.getroot().find('Name').text == name:

                    # appends this element tree as a child to the current root and
                    # sets EnsureVisible variable (which keeps track of whether or
                    # not the loop has reached the current element tree or not - if so,
                    # EnsureVisible is True and method will set all of the
                    # following children to be expanded)
                    new_tree_item = self.hier_tree.AppendItem(curr_root, name)
                    EnsureVisible = visible

                    # if the loop has reached the current element tree, EnsureVisible is set to True
                    # and the current treeCtrl item is expanded
                    if tree.getroot().find('Name').text == self.curr_tree.getroot().find('Name').text:
                        EnsureVisible = True
                    if EnsureVisible is True:
                        self.hier_tree.EnsureVisible(new_tree_item)

                    # recursive call to function with the new treeCtrl item as the current root
                    # and EnsureVisible set to new value
                    self.add_tree_items(new_tree_item, tree, curr_tree_list, EnsureVisible)

        # iterate through the current tree's buffer properties
        for buff_prop in curr_tree.getroot().find('BufferProperties').iter('BufferProperty'):
            name = buff_prop.find('BufferName').text

            # find the element tree corresponding to the current buffer property
            for tree in curr_tree_list:
                if tree.getroot().find('Name').text == name:

                    # appends this element tree as a child to the current root and
                    # sets EnsureVisible variable (which keeps track of whether or
                    # not the loop has reached the current element tree or not - if so,
                    # EnsureVisible is True and method will set all of the
                    # following children to be expanded)
                    new_tree_item = self.hier_tree.AppendItem(curr_root, name)
                    EnsureVisible = visible

                    # if the loop has reached the current element tree, EnsureVisible is set to True
                    # and the current treeCtrl item is expanded
                    if tree.getroot().find('Name').text == self.curr_tree.getroot().find('Name').text:
                        EnsureVisible = True
                    if EnsureVisible is True:
                        self.hier_tree.EnsureVisible(new_tree_item)

                    # recursive call to function with the new treeCtrl item as the current root
                    # and EnsureVisible set to new value
                    self.add_tree_items(new_tree_item, tree, curr_tree_list, EnsureVisible)

    def refresh(self, tree):
        """Updates the Main Window UI to display the current Element Tree's properties and hierarchical properties"""
        # updates the curr_tree variable
        self.curr_tree = tree

        # adjusts number of rows in properties grid to match the current tree
        num = self.properties_panel.props_grid.GetNumberRows()
        root = tree.getroot()

        row_counter = 0
        for prop in root.iter('Property'):
            if prop.find('DataType').text == 'Buffer':
                bufname = tree.getroot().find('Name').text
                currValue = prop.find('Value').text
                if currValue == None:
                    currValue = ''

                add_bufferdata_value = EditBufferDataPropertyValue(self, -1, currValue, bufname, size=(450, 800), style=wx.DEFAULT_DIALOG_STYLE)
                add_bufferdata_value.CenterOnScreen()
                val = add_bufferdata_value.ShowModal()

                if val == wx.ID_OK:
                    message = [add_bufferdata_value.value.GetValue(), prop.find('Name').text]
                    self.model.update_buff_val(message)

                # Set the parent node as the current element tree and refresh both the tree and the tree_list in the View
                self.model.set_curr_tree(tree.find(".//Parent").text)
                new_tree = self.model.get_curr_tree()
                self.refresh(new_tree)
                tree_list = self.model.get_tree_list()
                self.refresh_tree(tree_list)

                return

            row_counter += 1

        if row_counter < num:
            self.properties_panel.props_grid.DeleteRows(0, num - row_counter)

        if num < row_counter:
            self.properties_panel.props_grid.AppendRows(row_counter - num)

        # counter is used to keep track of what row the loop is in as properties are added to the grid
        counter = 0

        # updates properties grid
        for prop in root.iter('Property'):
            name = prop.find('Name').text
            val = prop.find('Value').text

            dType = prop.find('DataType').text

            if val is not None:
                self.properties_panel.props_grid.SetCellValue(counter, 2, val)
            else:
                self.properties_panel.props_grid.SetCellValue(counter, 2, "")

            self.properties_panel.props_grid.SetCellValue(counter, 0, name)
            self.properties_panel.props_grid.SetCellValue(counter, 1, dType)
            self.properties_panel.props_grid.SetReadOnly(counter, 0, isReadOnly=False)
            self.properties_panel.props_grid.SetReadOnly(counter, 1, isReadOnly=False)
            self.properties_panel.props_grid.SetCellFont(counter, 2, wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Intel Clear"))
            self.properties_panel.props_grid.SetCellFont(counter, 0, wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Intel Clear"))
            self.properties_panel.props_grid.SetCellFont(counter, 1, wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Intel Clear"))
            self.properties_panel.props_grid.SetRowSize(counter, 25)

            counter += 1

        # adjusts number of rows in hierarchical properties grid to match the current tree
        num = self.packages_panel.packs_grid.GetNumberRows()
        root = tree.getroot()

        row_counter = 0
        for prop in root.iter('HierarchicalProperty'):
            row_counter += 1

        if row_counter < num:
            self.packages_panel.packs_grid.DeleteRows(0, num - row_counter)

        if num < row_counter:
            self.packages_panel.packs_grid.AppendRows(row_counter - num)

        # counter is used to keep track of what row the loop is in as properties are added to the grid
        counter = 0

        # updates hierarchical properties grid with hierarchical properties
        # that aren't associated with other properties (these have editable names)
        for hier_prop in root.find('HierarchicalProperties').iter('HierarchicalProperty'):
            name = hier_prop.find('Name').text
            prefix = hier_prop.find('PackageNamePrefix').text
            dType = hier_prop.find('DataType').text
            val = hier_prop.find('Value').text

            if val is None:
                val = ""

            self.packages_panel.packs_grid.SetCellValue(counter, 0, name)
            self.packages_panel.packs_grid.SetCellValue(counter, 1, dType)
            self.packages_panel.packs_grid.SetCellValue(counter, 2, val)
            self.packages_panel.packs_grid.SetReadOnly(counter, 0, isReadOnly=False)
            self.packages_panel.packs_grid.SetReadOnly(counter, 1, isReadOnly=False)
            self.packages_panel.packs_grid.SetReadOnly(counter, 2, isReadOnly=False)
            self.packages_panel.packs_grid.SetCellFont(counter, 0, wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Intel Clear"))
            self.packages_panel.packs_grid.SetCellFont(counter, 1, wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Intel Clear"))
            self.packages_panel.packs_grid.SetCellFont(counter, 2, wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Intel Clear"))
            self.packages_panel.packs_grid.SetRowSize(counter, 25)
            counter += 1

        # updates hierarchical properties grid with hierarchical properties
        # that are associated with other properties (these have non-editable names)
        for prop in root.find('Properties').iter('Property'):
            for pack in prop.find('DependentPackages').iter('Package'):
                for hier_prop in pack.find('HierarchicalProperties').iter('HierarchicalProperty'):

                    name = hier_prop.find('Name').text
                    prefix = hier_prop.find('PackageNamePrefix').text
                    dType = hier_prop.find('DataType').text
                    val = hier_prop.find('Value').text

                    if val is not None:
                        prefix = val

                    self.packages_panel.packs_grid.SetCellValue(counter, 0, name)
                    self.packages_panel.packs_grid.SetCellValue(counter, 1, dType)
                    self.packages_panel.packs_grid.SetCellValue(counter, 2, prefix)
                    self.packages_panel.packs_grid.SetReadOnly(counter, 0, isReadOnly=False)
                    self.packages_panel.packs_grid.SetReadOnly(counter, 1, isReadOnly=False)
                    self.packages_panel.packs_grid.SetReadOnly(counter, 2, isReadOnly=False)
                    self.packages_panel.packs_grid.SetCellFont(counter, 0, wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Intel Clear"))
                    self.packages_panel.packs_grid.SetCellFont(counter, 1, wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Intel Clear"))
                    self.packages_panel.packs_grid.SetCellFont(counter, 2, wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Intel Clear"))
                    self.packages_panel.packs_grid.SetRowSize(counter, 25)
                    counter += 1

        # adjusts number of rows in buffer properties grid to match the current tree
        num = self.buffprops_panel.props_grid.GetNumberRows()
        root = tree.getroot()

        row_counter = 0
        for prop in root.iter('BufferProperty'):
            row_counter += 1

        if row_counter < num:
            self.buffprops_panel.props_grid.DeleteRows(0, num - row_counter)

        if num < row_counter:
            self.buffprops_panel.props_grid.AppendRows(row_counter - num)

        # counter is used to keep track of what row the loop is in as properties are added to the grid
        counter = 0

	    # updates buffer properties grid with buffer properties
        for buff_prop in root.find('BufferProperties').iter('BufferProperty'):
            name = buff_prop.find('PropertyName').text
            buffName = buff_prop.find('BufferName').text
            dType = buff_prop.find('DataType').text
            val = buff_prop.find('Value').text

            if buffName is None:
                buffName = ""

            self.buffprops_panel.props_grid.SetCellValue(counter, 0, name)
            self.buffprops_panel.props_grid.SetCellValue(counter, 1, dType)
            self.buffprops_panel.props_grid.SetCellValue(counter, 2, buffName)
            self.buffprops_panel.props_grid.SetReadOnly(counter, 0, isReadOnly=False)
            self.buffprops_panel.props_grid.SetReadOnly(counter, 1, isReadOnly=False)
            self.buffprops_panel.props_grid.SetReadOnly(counter, 2, isReadOnly=False)
            self.buffprops_panel.props_grid.SetCellFont(counter, 0, wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Intel Clear"))
            self.buffprops_panel.props_grid.SetCellFont(counter, 1, wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Intel Clear"))
            self.buffprops_panel.props_grid.SetCellFont(counter, 2, wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Intel Clear"))
            self.buffprops_panel.props_grid.SetRowSize(counter, 25)
            counter += 1

    def _bind_mainframe_events(self):
        """
        __init__(self, event)
        Navigation event handling on MiTiBug options
        :param page change event:
        :returns: none
        """
        self.Bind(wx.EVT_CLOSE, self._on_close_evt)
        self.Bind(wx.EVT_SIZE, self._on_size_evt)

    def _on_close_evt(self, event):
        """
        __init__(self, event)
        closing disco tool  aui manager and destroy it.
        :param disco tool main window close event:
        :returns: none
        """
        # result variable corresponds to how the user responds to the message box warning
        result = wx.ID_NONE

        if self.data_changed or self.properties_panel.data_changed:
            result = wx.MessageBox(message='There are some unsaved changes. Would you like to save these before closing the application?', 
                                   caption='Unsaved Changes',
                                   style=wx.YES_NO | wx.ICON_WARNING)
            if result == wx.YES:

                # will save to previous location or use a dialog box to get location from user
                # if files haven't been saved yet
                if self.has_project_path is False:
                    self.save_dir_dialog()
                else:
                    self.save_files(message=None)
        # deinitialize the frame manager
        self.aui_manager.UnInit()
        # delete the frame
        self.Destroy()
        event.Skip()

    def _on_size_evt(self, event):
        """
        __init__(self, event)
        Other sizing events handler to resize logo panel.
        :param disco tool main window resize event:
        :returns: none
        """
        mainframesize = self.GetSize()
        definedsize = app_constants.MAIN_FRAME_SIZE_WxH[0]
        if (app_constants.MAIN_FRAME_SIZE_WxH[0] == definedsize and mainframesize[0] == definedsize):
            pass
        else:
            app_constants.MAIN_FRAME_SIZE_WxH = mainframesize
            self.aui_manager.Update()
        event.Skip()

class DescriptionPanel(wx.Panel):

    # initializes the Hierarchical Property Frame with the appropriate wxPython widgets
    def __init__(self, parent, description_text=" "):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour("white")
        # saves reference to the Main Window to reopen it once the Property Frame is closed.
        self.main_window = parent.GetParent()
        self.description_txt = description_text
        self.vbox = wx.BoxSizer(wx.VERTICAL)

        self.descriptionLabel = wx.TextCtrl(self, value=description_text, style=wx.TE_MULTILINE | wx.TE_READONLY)
        app_constants.set_title_font(self.descriptionLabel)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.descriptionLabel, 0, wx.LEFT, 5)
        self.vbox.Add(hbox, 0, wx.TOP, 10)
        self.SetSizer(self.vbox)
        self.Layout()
        self.SetAutoLayout(True)

# This class displays the app's UI for the Generate ASL Frame using wxPython widgets.
# In this frame, the user can define their
# device name/vendor name/vendor type before generating the ASL file.
class GenerateASL(wx.Dialog):

    def __init__(self, parent, ID, title, size=wx.DefaultSize, pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):
        wx.Dialog.__init__(self, parent, ID, title, pos, size, style)
        self.parent = parent
        pre = wx.Dialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        pre.Create(parent, ID, title, pos, size, style)

        vbox_main = wx.BoxSizer(wx.VERTICAL)

        deviceLabel = wx.StaticText(self, label="Device Name: ")
        app_constants.set_title_font(deviceLabel)
        self.device = wx.TextCtrl(self, value="")
        self.device.SetMaxLength(4)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(deviceLabel, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT | wx.TOP, 10)
        self.SetSizer(vbox_main)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.device, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT, 10)
        self.SetSizer(vbox_main)

        my_list = ['_HID', '_ADR']
        self.combo = wx.ComboBox(self, choices=my_list)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.combo, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT | wx.TOP, 10)
        self.SetSizer(vbox_main)

        self.HIDValueLabel = wx.StaticText(self, label="_HID Value:")
        self.HIDValue = wx.TextCtrl(self, value="")

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.HIDValueLabel, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT, 10)
        self.SetSizer(vbox_main)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.HIDValue, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT | wx.TOP, 10)
        self.SetSizer(vbox_main)

        self.CIDValueLabel = wx.StaticText(self, label="_CID Value:")

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(deviceLabel, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT | wx.TOP, 10)
        self.SetSizer(vbox_main)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.device, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT, 10)
        self.SetSizer(vbox_main)

        self.CIDValue = wx.TextCtrl(self, value="")
        self.ADRValueLabel = wx.StaticText(self, label="_ADR Value:")
        self.ADRValue = wx.TextCtrl(self, value="")

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.CIDValue, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT | wx.TOP, 10)
        self.SetSizer(vbox_main)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.device, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT, 10)
        self.SetSizer(vbox_main)

        closeBtn = wx.Button(self, label="Generate ASL", size=(85, 35))
        closeBtn.Bind(wx.EVT_BUTTON, self.open_main)
        app_constants.set_button_font(closeBtn)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(closeBtn, 0, wx.LEFT, 10)
        vbox_main.Add(hbox, 0, wx.LEFT, 10)
        self.SetSizer(vbox_main)

        # hides the text boxes for _HID/_CID/_ADR until the user selects one from the combo box
        self.HIDValueLabel.Hide()
        self.HIDValue.Hide()
        self.CIDValueLabel.Hide()
        self.CIDValue.Hide()
        self.ADRValueLabel.Hide()
        self.ADRValue.Hide()

        self.combo.Bind(wx.EVT_COMBOBOX, self.type_selected)
        self.Bind(wx.EVT_CLOSE, self.close_window)



class HeaderPanel(wx.Panel):
    """
    Header display panel class
    """

    def __init__(self, parent):
        """
        __init__(self, Window parent)
        An HeaderPanel: Add Title.
        """
        wx.Panel.__init__(self, parent, -1)
        self.aui_mainframe = parent.GetParent()
        self.vbox_main = None

        self.PanelLayOut(app_constants.MAIN_FRAME_SIZE_WxH)

    def PanelLayOut(self, mainframesize):
        """
        __init__(self, mainframesize)
        creating layout based on window size.
        :param window size:
        :returns: none
        """
        self.frame_width = mainframesize[0]
        self.vbox = wx.BoxSizer(wx.VERTICAL)

        bmplogo = wx.Image(os.path.join(self.aui_mainframe.app_data_path, "images", "Stacked.bmp"), wx.BITMAP_TYPE_ANY).ConvertToBitmap()

        self.app_name = wx.StaticText(self, -1, "DisCo Creation Tool                            ",
                                      wx.DefaultPosition,
                                      wx.DefaultSize, 0)
        self.app_name.SetFont(wx.Font(20, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Intel Clear"))
        self.app_name.SetBackgroundColour(app_constants.COLOR_PURPLE4)
        self.app_name.SetForegroundColour(app_constants.COLOR_WHITE)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(wx.StaticBitmap(self, -1, bmplogo), 0, wx.LEFT | wx.TOP, 7)
        hbox.Add(self.app_name, 0, wx.LEFT, 5)
        self.vbox.Add(hbox, 0, wx.TOP, 7)  # self.vbox.Add(hbox, 0, wx.TOP, 7)
        self.SetSizer(self.vbox)

        # Setup Layout
        self.SetAutoLayout(True)
        self.Bind(wx.EVT_PAINT, self._on_paint_evt)

    def _on_paint_evt(self, evt):
        paintdc = wx.PaintDC(self)
        paintdc.SetPen(wx.Pen(app_constants.COLOR_PURPLE4, self.GetSize()[0]))
        paintdc.DrawLine(self.GetSize()[0], 0, 0, 0)
        evt.Skip()

    def DeleteLayout(self):
        """
        __init__(self)
        delete existing logo.
        :param none:
        :returns: none
        """
        self.vbox_main.Clear(delete_windows=True)


class DiscoToolApp(wx.App):

    def OnInit(self):
        self.app_name = "DiscoTool-%s" % wx.GetUserId()
        self.app_instance = wx.SingleInstanceChecker(self.app_name)
        if self.app_instance.IsAnotherRunning():
            wx.MessageBox(disco_str.DISCO_STR_INFO_INSTANCE, disco_str.DISCO_STR_GENERAL_INFOSTR)
            sys.exit(0)
        disco_frame = DiscoToolAuiManager(None, -1, sys.argv[1:])
        disco_frame.Show(True)
        disco_frame.Maximize()
        disco_frame.CenterOnScreen()
        return True


def main():
    app = DiscoToolApp(redirect=False)
    app.MainLoop()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
