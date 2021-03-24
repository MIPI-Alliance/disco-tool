#  ------------------------------------------------------------------------------
#
#  Copyright (C) Microsoft Corporation. All rights reserved.
#
#  Module Name:
#
#    view.py
#
#  Abstract:
#
#    Main class for displaying the graphical user interface.
#
#  -------------------------------------------------------------------------------

import wx
import os
import xml.etree.ElementTree as et
import wx.grid as grid
from pubsub import pub
import re

#This class displays the app's UI for the Main Frame using wxPython widgets. When events occur in the UI that change the
#app's data, this class sends out messages to the Controller. 
class MainFrame(wx.Frame):

    #initializes the Main Frame with the appropraite wxPython widgets 
    def __init__(self):
        #data_changed variable keeps track of whether or not current data has been saved (decides if user should be asked to save when they close the window)
        self.data_changed = False

        #this variable keeps track of whether or not there is currently a project path (set to True if the user opens up an existing project or once
        # they save their files)
        #Print statement for debugging purposes:
        self.has_project_path = False
        print("initializing data changed to false")
        
        #keeps track of the model's tree_list (updated whenever refresh_tree is called)
        self.tree_list = None

        #keeps track of the model's curr_tree (updated whenever refresh is called)
        self.curr_tree = None

        #initializes the frame for the main window
        wx.Frame.__init__(self, None, title="DisCo Creation Tool", size = (750,650))

        #the main panel holds all of the other windows and panels within the main window
        mainPanel = wx.Panel(self)

        #creating status bar
        self.statusBar = self.CreateStatusBar(1)

        #adds a vertical splitter window as a child of the main panel and a horizontal splitter window as a child of that
        #vertical splitter window
        vSplitter = wx.SplitterWindow(mainPanel)
        hSplitter = wx.SplitterWindow(vSplitter)

        #the propsPanel displays the list of properties for the current package
        self.propsPanel = wx.Panel(hSplitter)
        self.propsPanel.SetBackgroundColour("white")

        #the packsPanel displays the list of hierarchical properties for the current package
        packsPanel = wx.Panel(hSplitter)
        packsPanel.SetBackgroundColour("white")

        #splits the properties and packages panels horizontally (each taking up equal amounts of space)
        hSplitter.SplitHorizontally(self.propsPanel, packsPanel)
        hSplitter.SetSashGravity(0.5)

        #the tree panel displays the hierarchical tree of packages for the current device
        treePanel = wx.Panel(vSplitter)
        treePanel.SetBackgroundColour("white")

        #splits the tree panel and the props/packs panel combination vertically (with the tree panel taking up less space)
        vSplitter.SplitVertically(treePanel, hSplitter)
        vSplitter.SetSashGravity(0.25)

        #sets the sizer for the main panel to include three panels (which are children of the vertical splitter window)
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(vSplitter, 1, wx.EXPAND)
        mainPanel.SetSizer(self.mainSizer)

        self.SetMinSize(wx.Size(750, 650))

        #setting up the menu bar at the top of the window that has a list of buttons the user can click to start a new
        #project/open an existing project/save/save as/generate ASL
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
        fileMenu.Append(wx.MenuItem(fileMenu, wx.ID_EXIT, text = "E&xit"))

        self.item_save.Enable(False)
        self.item_save_as.Enable(False)
        self.item_generate_asl.Enable(False)

        self.SetMenuBar(menuBar)
        self.Bind(wx.EVT_MENU, self.menuHandler)

        #getting the initial width and height of the frame (in order to size the grid columns correctly)
        w, h = self.GetClientSize()

        #adding the properties grid and the add property button to the properties panel
        self.props_grid = grid.Grid(self.propsPanel, size=(5000, 300))
        self.props_grid.CreateGrid(0, 3)

        #sets the initial sizes for the property grid columns
        self.props_grid.SetColSize(0, (w-80)/3)
        self.props_grid.SetColSize(1, 80)
        self.props_grid.SetColSize(2, (w-80)/3)
        
        self.props_grid.SetColLabelValue(0, "Property Name")
        self.props_grid.SetColLabelValue(1, "Data Type")
        self.props_grid.SetColLabelValue(2, "Value")

        #calls certain functions when user changes a properties grid cell or right clicks on a properties grid cell
        self.props_grid.Bind(grid.EVT_GRID_CELL_CHANGED, self.OnPropsGridCellChange)
        self.props_grid.Bind(grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnPropsGridRightClick)
        self.props_grid.GetGridWindow().Bind(wx.EVT_MOTION, self.onPropsGridMouseOver)

        self.addPropBtn = wx.Button(parent = self.propsPanel, label="Add Property")
        self.addPropBtn.Bind(wx.EVT_BUTTON, self.open_property_frame)
        self.addPropBtn.Disable()

        #creates sizer for properties panel
        self.propsSizer = wx.BoxSizer(wx.VERTICAL)
        self.propsSizer.Add(self.props_grid, wx.EXPAND)
        self.propsSizer.Add(self.addPropBtn)
        self.propsPanel.SetSizer(self.propsSizer)
        self.propsPanel.Layout()
        
        #adding the hierarchical properties grid and the add hierarchical property button to the properties panel
        self.packs_grid = grid.Grid(packsPanel, size=(5000, 300))
        self.packs_grid.CreateGrid(0, 3)

        #sets the initial sizes for the hierarchical property grid columns
        self.packs_grid.SetColSize(0, (w-80)/3)
        self.packs_grid.SetColSize(1, 80)
        self.packs_grid.SetColSize(2, (w-80)/3)

        self.packs_grid.SetColLabelValue(0, "Property Name")
        self.packs_grid.SetColLabelValue(1, "Data Type")
        self.packs_grid.SetColLabelValue(2, "Package Name")

        #calls certain functions when user changes a hierarchical properties grid cell or right clicks on a hierarchical properties grid cell
        self.packs_grid.Bind(grid.EVT_GRID_CELL_CHANGED, self.OnPacksGridCellChange)
        self.packs_grid.Bind(grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnPacksGridRightClick)
        self.packs_grid.GetGridWindow().Bind(wx.EVT_MOTION, self.onPacksGridMouseOver)

        self.addHierPropBtn = wx.Button(parent = packsPanel, label="Add Hierarchical Property")
        self.addHierPropBtn.Bind(wx.EVT_BUTTON, self.open_hierarchical_property_frame)
        self.addHierPropBtn.Disable()

        #creates sizer for hierarchical properties panel
        self.packsSizer = wx.BoxSizer(wx.VERTICAL)
        self.packsSizer.Add(self.packs_grid, wx.EXPAND)
        self.packsSizer.Add(self.addHierPropBtn)
        packsPanel.SetSizer(self.packsSizer)
        packsPanel.Layout()

        #adding all of the widgets to the tree panel
        self.hier_tree = wx.TreeCtrl(parent = treePanel, size=(4000,6000))
        self.hier_tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnTreeItemActivated)
        self.hier_tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeItemSelectionChanged)
        self.Show()

        #when user resizes the frame, methods will be called to appropriately resize the grids
        self.props_grid.Bind(wx.EVT_SIZE, self.resize_props_grids)
        self.packs_grid.Bind(wx.EVT_SIZE, self.resize_packs_grids)

        #when user closes main window, the tool will first check if their data is saved
        self.Bind(wx.EVT_CLOSE, self.close_main_window)

    #called when the user closes the main window: if there are any unsaved changes, the tool will ask the user if they want to save these before
    #exiting and will call "Save" in the controller if they say yes
    def close_main_window(self, event):
        #result variable corresponds to how the user responds to the message box warning
        result = wx.ID_NONE

        if self.data_changed == True:
            result = wx.MessageBox(message = 'There are some unsaved changes. Would you like to save these before closing the application?', caption='Unsaved Changes',style = wx.YES_NO | wx.ICON_WARNING)
            if result == wx.YES:

                #will save to previous location or use a dialog box to get location from user if files haven't been saved yet
                if self.has_project_path == False: 
                    self.save_dir_dialog()
                else: 
                    pub.sendMessage("save", message=None)
        self.Destroy()

    #updates the value of data_changed variable - called when some data is updated by user
    def set_data_changed(self, value):
        self.data_changed = value
        print("data changed set to "+ str(value))

    #called when the user resizes the frame - resizes the properties grid accordingly 
    def resize_props_grids(self, event):
        w, h = self.GetClientSize()
        self.props_grid.SetColSize(0, (w-80)/(3))
        self.props_grid.SetColSize(1, 80)
        self.props_grid.SetColSize(2,(w-80)/(3))
        self.Layout()

    #called when the user resizes the frame - resizes the hierarchical properties grid accordingly 
    def resize_packs_grids(self, event):
        w, h = self.GetClientSize()
        self.packs_grid.SetColSize(0, (w-80)/(3))
        self.packs_grid.SetColSize(1, 80)
        self.packs_grid.SetColSize(2,(w-80)/(3))
        self.Layout()

    #called when the user moves the mouse over the screen
    def onPropsGridMouseOver(self, event):
        #gets position of the mouse on the screen and converts this to row and column
        x, y = self.props_grid.CalcUnscrolledPosition(event.GetX(), event.GetY())
        coordinates = self.props_grid.XYToCell(x, y)
        row = coordinates[0]
        column = coordinates[1] 

        #gets the total number of rows and columns
        num_rows = self.props_grid.GetNumberRows()
        num_cols = self.props_grid.GetNumberCols()

        #if the mouse is over an actual row and column in the grid, find that row's property and data type and display its description to the user
        if (column >= 0) & (column < num_cols) & (row >= 0) & (row < num_rows):
            data_type = self.props_grid.GetCellValue(row, 1)
            prop_name = self.props_grid.GetCellValue(row, 0)

            #find the description for the property the user is hoering over
            for prop in self.curr_tree.getroot().find('Properties').iter('Property'):
                if prop.find('Name').text == prop_name:
                    description = prop.find('Description').text
                    if description == None:
                        description = ""
                    
                    #add a string that gives information on how the current property's data type should be entered
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
                    msg = description + "\n\n" + data_mssg
                    event.GetEventObject().SetToolTip(msg)

    #called when the user moves the mouse over the screen
    def onPacksGridMouseOver(self, event):
        #gets position of the mouse on the screen and converts this to row and column
        x, y = self.packs_grid.CalcUnscrolledPosition(event.GetX(), event.GetY())
        coordinates = self.packs_grid.XYToCell(x, y)
        row = coordinates[0]
        column = coordinates[1] 

        #gets the total number of rows and columns
        num_rows = self.packs_grid.GetNumberRows()
        num_cols = self.packs_grid.GetNumberCols()

        #if the mouse is over an actual row and column in the grid, find that row's property and data type and display its description to the user
        if (column >= 0) & (column < num_cols) & (row >= 0) & (row < num_rows):
            data_type = self.packs_grid.GetCellValue(row, 1)
            prop_name = self.packs_grid.GetCellValue(row, 0)

            for prop in self.curr_tree.getroot().find('HierarchicalProperties').iter('HierarchicalProperty'):
                if prop.find('Name').text == prop_name:
                    description = prop.find('Description').text
                    if description == None:
                        description = ""
                    msg = description + "\n\n" + "String can be entered in any format."
                    event.GetEventObject().SetToolTip(msg)

    #called when user right clicks on a property in the properties grid - opens a pop up menu with the option to delete that property
    def OnPropsGridRightClick(self, event):
        
        #gets the current width and height of the window and the position where the user clicked
        w, h = self.GetClientSize()
        point = event.GetPosition()

        #takes the x position of where the user clicked and offsets it by .25*w (to account for tree panel on the left)
        point.x = (w *0.25) + point.x

        #finds the name of the property to be deleted (to be used in the delete_property function)
        self.delete_property_name = self.props_grid.GetCellValue(event.GetRow(), 0)

        #creates a pop up menu with the option to delete and opens this menu at the correct screen position 
        popUpMenu = wx.Menu()
        deleteItem = wx.MenuItem(popUpMenu, wx.NewId(), "Remove " + self.delete_property_name)
        popUpMenu.Append(deleteItem)
        popUpMenu.Bind(wx.EVT_MENU, self.delete_property, deleteItem)
        self.PopupMenu(popUpMenu, point)
    
    #called if user right clicks on a property and chooses "delete" from the pop up menu 
    def delete_property(self, event):
        pub.sendMessage("property_deleted", message = self.delete_property_name)

    #called when user right clicks on a property in the hierarchical properties grid - opens a pop up menu with the option to delete that property
    def OnPacksGridRightClick(self, event):
        
        #gets the current width and height of the window and the position where the user clicked
        w, h = self.GetClientSize()
        point = event.GetPosition()

        #takes the x position of where the user clicked and offsets it by .25*w (to account for tree panel on the left)
        point.x = (w * 0.25) + point.x
        point.y = (h * 0.5) + point.y

        #finds the name of the property to be deleted (to be used in the delete_property function)
        self.delete_property_name = self.packs_grid.GetCellValue(event.GetRow(), 0)

        #creates a pop up menu with the option to delete and opens this menu at the correct screen position 
        popUpMenu = wx.Menu()
        deleteItem = wx.MenuItem(popUpMenu, wx.NewId(), "Remove " + self.delete_property_name)
        popUpMenu.Append(deleteItem)
        popUpMenu.Bind(wx.EVT_MENU, self.delete_hier_property, deleteItem)
        self.PopupMenu(popUpMenu, point)
    
    #called if user right clicks on a property and chooses "delete" from the pop up menu 
    def delete_hier_property(self, event):
        pub.sendMessage("hier_property_deleted", message = [self.delete_property_name, None, None, self.curr_tree])

    #called when the user single clicks on an item in the treectrl
    def OnTreeItemSelectionChanged(self, event):
        #collects the text of the treeCtrl item that was clicked on as well as the root of the treeCtrl
        text = self.hier_tree.GetItemText(event.GetItem())
        root = self.hier_tree.GetRootItem()

        #expands and colors the treeCtrl item that was clicked on and sets the focus (highlight) to that item as well
        self.ExpandAndColorTreeItem(root, text)
        self.hier_tree.SetFocusedItem(event.GetItem())

    #called when the user double clicks or uses keyboard on a new item in the hierarchical list of packages
    def OnTreeItemActivated(self, event):
        #collects the text of the treeCtrl item that was clicked on as well as the root of the treeCtrl
        text = self.hier_tree.GetItemText(event.GetItem())
        root = self.hier_tree.GetRootItem()

        #expands and colors the treeCtrl item that was clicked on and sets the focus (highlight) to that item as well
        self.ExpandAndColorTreeItem(root, text)
        self.hier_tree.SetFocusedItem(event.GetItem())
        
        #sends message to the Controller that a new item in the treeCtrl was chosen
        pub.sendMessage("new_tree_chosen", message = text)

    #Expands and colors green the treeCtrl item that corresponds to the text value passed in and its children 
    def ExpandAndColorTreeItem(self, root, text):

        #finds the child of the current root
        child, cookie = self.hier_tree.GetFirstChild(root)

        #if child item matches the given text value, set its color to green and expand it - then recursively call function with the child 
        #set as the root and continue the loop with the next child of the current root
        while child.IsOk():
            if self.hier_tree.GetItemText(child) == text:
                self.hier_tree.EnsureVisible(child)
                self.hier_tree.SetItemTextColour(child, wx.Colour(0,255,0))
                self.hier_tree.SetItemBackgroundColour(child, wx.Colour(0, 0, 255))
            else:
                self.hier_tree.SetItemTextColour(child, wx.Colour(0,0,0))
                self.hier_tree.SetItemBackgroundColour(child, wx.Colour(255, 255, 255))
            self.ExpandAndColorTreeItem(child, text)
            child, cookie = self.hier_tree.GetNextChild(child, cookie)

    #called when the user changes the value cell for a hierarchical property in the hierarchical properties grid - prevents the user from 
    #entering a value that is not four characters and warns the user if their value already exists (meaning this package would have several parents)
    def OnPacksGridCellChange(self, event):

        #collects the new property value and the previous property value
        old_value = event.GetString()
        value = self.packs_grid.GetCellValue(event.GetRow(), event.GetCol())

        #initializes variables to starting values
        over_four = False
        ancestor = False
        result_new = wx.ID_NONE
        result_old = wx.ID_NONE

        #if user changes a property's name, that property name is updated in the model
        if event.GetCol() == 0: 
            message = [value, old_value]
            pub.sendMessage("hier_property_name_changed", message=message)
        #if user changes a property's value:
        else: 
            #TODO: currently, this function is being called multiple times when a user only changes a grid cell once - after the first correct
            #function call, the old_value is equal to the new value. This if statement is to prevent the warning dialogs to show up more than 
            #once when the function is called with these incorrect values. 
            if old_value != value:

                #if the new value is over four characters, an error message is shown and the over_four variable is set to true
                if len(value) > 4:
                    wx.MessageBox(message = value + ' is over 4 characters. Please choose a name that is less than or equal to 4 characters.', caption='Package name error',style=wx.OK | wx.ICON_ERROR)
                    over_four = True
                
                #iterates through the current element tree list to see if the new value already has an associated element tree or if the old 
                #value had several parents (not just curr_tree).
                for tree in self.tree_list:
                    
                    #TODO: move the following data validation to the Controller (checking if tree is an ancestor of curr_tree)

                    #enters this if statement if the new value already has an element tree - in this case send an error message if this element
                    #tree is an ancestor of the curr_tree (because this would cause an infinite loop) and send a warning message telling the user
                    #if they use this value, they will be sharing this package among other parents. 
                    if tree.getroot().find('Name').text == value:
                        ancestor = self.is_ancestor(tree, self.curr_tree)

                        if ancestor == True:
                            wx.MessageBox(message = 'Circular reference found. One of the parent packages has the same name.', caption='Package name error',style=wx.OK | wx.ICON_ERROR)
                        else:
                            result_new = wx.MessageBox(message = value + ' is an existing package. Do you want to re-use existing package or rename current package?', caption='Package name warning',style = wx.YES_NO | wx.ICON_WARNING)
                    
                    #enters this if statement when the element tree is found that was associated with the previous value. Counter variable is used
                    #to count how many parents this tree has - if it has more than one, send a warning message telling the user if they use this 
                    #value, the new package will no longer be shared with these other parents. 
                    if tree.getroot().find('Name').text == old_value:
                        counter = 0
                        for parent in tree.getroot().find('Header').find('Parents').iter('Parent'):
                            counter += 1
                        
                        if counter > 1:
                            result_old = wx.MessageBox(message = old_value + ' had several parent packages. If you continue, new data associated with this property will no longer affect other instances of the previous package. Would you like to continue?', caption='Package name warning',style = wx.YES_NO | wx.ICON_WARNING)

                #if the new value is not an ancestor of the current tree, has equal or less than four characters, and the user did not reply "no" to any
                #warning messages they might have gotten, then the hierarchical property is changed in the Model. Otherwise, the property
                #is not changed in the model and the grid cell value returns to its previous value. 
                if (ancestor == False) & (over_four == False) & (result_new != wx.NO) & (result_old != wx.NO):
                    #Print statement for debugging purposes:
                    print(" publishing property ")

                    message = [self.packs_grid.GetCellValue(event.GetRow(), 0), value, old_value]
                    pub.sendMessage("hier_property_value_changed", message=message)
                else:
                    #Print statement for debugging purposes:
                    print("\n setting cell value "+old_value+" "+value)
                    self.packs_grid.SetCellValue(event.GetRow(), event.GetCol(), old_value)
            
            else:
                #Print statement for debugging purposes:
                print("skipping event")
    
    #helper function for OnPacksGridCellChange - returns true if higher_tree is an ancestor of lower_tree and returns false otherwise
    def is_ancestor(self, higher_tree, lower_tree):
        #find hier_props and loop through - for each one, find that tree and if it matches lower_tree, return true. otherwise, call this
        #function again but with (new tree, lower_tree)

        higher_name = higher_tree.getroot().find('Name').text
        lower_name = lower_tree.getroot().find('Name').text
        
        #Base case: if the trees are the same, return true 
        if higher_name == lower_name:
            return True
        
        #Recursive case: loop through the hierarchical properties of the higher_tree. For each one, find its associated element tree
        #and call this function again with this element tree as the higher_tree. 
        for hier_prop in higher_tree.getroot().find('HierarchicalProperties').iter('HierarchicalProperty'):
            name = hier_prop.find('Value').text
            for tree in self.tree_list:
                if tree.getroot().find('Name').text == name:
                    result = self.is_ancestor(tree, lower_tree)
                    if result == True:
                        return True
        
        #If the function goes through all of the trees under higher_tree and does not find a match to lower_tree, return False
        return False

    #called when the user changes a cell in the properties grid (the value cell)
    def OnPropsGridCellChange(self, event):
        #collects the new property value, the previous value, the property's name, and initializes user_choice (used for warning box) to none
        value = self.props_grid.GetCellValue(event.GetRow(), event.GetCol())
        old_value = event.GetString()
        prop_name = self.props_grid.GetCellValue(event.GetRow(), 0)
        user_choice = wx.ID_NONE

        #defines the message to be sent if property value is updated in the model
        message = [prop_name, value, old_value]

        #TODO: currently, this function is being called multiple times when a user only changes a grid cell once - after the first correct
        #function call, the old_value is equal to the new value. This if statement is to prevent the warning dialogs to show up more than 
        #once when the function is called with these incorrect values.
        if old_value != value:

            #if user changes a property's name, that property name is updated in the model
            if event.GetCol() == 0: 
                message = [value, old_value]
                pub.sendMessage("property_name_changed", message=message)
            #if user changes a property's value:
            else:
                #iterates through the current tree's properties to find the one that was just edited by the user - once it finds this it then 
                #finds the list of dependent packages (if any) that are attached to this property
                for prop in self.curr_tree.getroot().find('Properties').iter('Property'):
                    if prop.find('Name').text == prop_name:

                        #TODO: move the following data validation to the Controller (checking data type matches what the user entered)

                        #if new value is not the correct data type, an error message is shown and value won't be updated
                        ret, msg = self.check_type(prop.find('DataType').text, value)
                        if ret != True:
                            wx.MessageBox(message = msg, caption='Property value type check failed.',style=wx.OK | wx.ICON_ERROR)
                            self.props_grid.SetCellValue(event.GetRow(), event.GetCol(), old_value)
                        else:
                            pckg_list = prop.find('DependentPackages').findall('Package')

                            #if there is at least one dependent package in this property, the tool checks if the new value is different than the previous value-
                            #if so, the user is warned that some of their hierarchical properties might be deleted. If they decide to continue, then the 
                            #property value is changed in the model. If not, the value is chagned back to the previous value. 
                            if len(pckg_list) > 0:
                                if (value != old_value) & (old_value != ''):
                                    user_choice = wx.MessageBox(message = value + ' is different than your previous value for this property. If you continue, some hierarchical properties and their data may be automatically deleted. Do you want to continue?', caption='Property value warning',style = wx.YES_NO | wx.ICON_WARNING)
                                
                                if user_choice != wx.NO:
                                    pub.sendMessage("property_value_changed", message = message)
                                else:
                                    self.props_grid.SetCellValue(event.GetRow(), event.GetCol(), old_value)
                            
                            #if there are no dependent packages in this property, the property value is changed in the model
                            else:
                                pub.sendMessage("property_value_changed", message = message)
    
    #TODO: move this type checking to the Controller
    # this function takes in a data type and a value that was just chosen for a property and will return True if the value is of the correct
    #data type and returns false otherwise
    def check_type(self, data_type, val):
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
            #TODO: Allow for {} values since packages could contain more packages
            pattern = '^([0-9a-zA-Z]*\s?,?)*$'
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
            # Integer - can either be in decimal or hex (either a series of numbers or a series of numbers and letters A-F)
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
    
    #enables the buttons and certain menu items in the main window, disables other menu items in the main window
    def enable_buttons(self):
        self.addHierPropBtn.Enable()
        self.addPropBtn.Enable()
        self.item_save.Enable(True)
        self.item_save_as.Enable(True)
        self.item_generate_asl.Enable(True)
        self.item_new.Enable(False)
        self.item_open.Enable(False)
    
    #defines what function the program calls when a particular menu item is chosen
    def menuHandler(self, event):
        id = event.GetId()
        if id == wx.ID_FILE:
            status = self.open_file_dialog()
            if status == True:
                self.enable_buttons()
        if id == wx.ID_OPEN:
            status = self.open_dir_dialog()
            if status == True:
                self.enable_buttons()
        if id == wx.ID_SAVE:
            #TODO: if they created a new project, need to open a dialog box the first time they save 
            if self.has_project_path == False: 
                self.save_dir_dialog()
            else: 
                pub.sendMessage("save", message=None)
        if id == wx.ID_SAVEAS:
            self.save_dir_dialog()
        if id == wx.ID_NEW:
            #open up an ASL generator window where user enters the device name/_HID or _CID or _ADR and then ASL is generated
            self.Disable()
            new_frame = GenerateASLFrame(self)
            new_frame.Show()
        if id == wx.ID_EXIT:
            self.Close()
            #when user closes main window, the tool will first check if their data is saved
            #self.Bind(wx.EVT_CLOSE, self.close_main_window)

    #temporarily disables the Main Frame and opens the Property Frame (where user can add a new property to the 
    #current Element Tree)
    def open_property_frame(self, event):
        self.Disable()

        new_frame = PropertyFrame(self)
        new_frame.Show()

    #temporarily disables the Main Frame and opens the Hierarchical Property Frame (where user can add a new hier prop to the 
    #current Element Tree)
    def open_hierarchical_property_frame(self, event):
        self.Disable()

        new_frame = HierarchicalPropertyFrame(self, self.tree_list, self.curr_tree)
        new_frame.Show()
    
    #opens the file dialog where the user chooses the directory with all of the intermediate files for the project
    #the user wants to continue editing. This directory's path is then sent in a message to the rest of the program.
    def open_dir_dialog(self):
        status = False

        dlg = wx.DirDialog(self, "Choose existing project", style = wx.DD_DEFAULT_STYLE)

        if dlg.ShowModal() == wx.ID_OK:

            path = os.path.join(dlg.GetPath(), "_DSD.xml")
            f = open(path, 'r')

            with f:
                data = f.read()
                pub.sendMessage("new_project_chosen", message = dlg.GetPath())

                status = True
                self.has_project_path = True

        dlg.Destroy()
        return status

    #opens a file dialog where the user chooses where they want to save their project (when they are doing save as or save for the first time)
    def save_dir_dialog(self):

        dlg = wx.DirDialog(self, "Choose directory to save to", style = wx.DD_DEFAULT_STYLE)

        if dlg.ShowModal() == wx.ID_OK:
            self.has_project_path = True
            pub.sendMessage("save_as", message=dlg.GetPath())

        dlg.Destroy()

    #opens the file dialog where the user chooses the xml file to use as the starting template. This file's path
    #is then sent in a message to the rest of the program.
    def open_file_dialog(self):
        wildcard = "XML Files (*.xml)|*.xml"
        dlg = wx.FileDialog(self, "Open file", os.getcwd(), "", wildcard, wx.FD_OPEN)
        status = False

        if dlg.ShowModal() == wx.ID_OK:
            f = open(dlg.GetPath(),'r')

            with f:
                data = f.read()
                pub.sendMessage("new_file_chosen", message = dlg.GetPath())
                status = True

        dlg.Destroy()
        return status

    #updates the hierarchy of packages (in the form of a treeCtrl) on the left side of the screen - starts by clearing this treeCtrl, 
    #then adds _DSD as the root, then recursively adds new packages based on hierarchical properties. Also adjusts the package labels'
    #color and expansion based on the current element tree selected.
    def refresh_tree(self, tree_list):
        #updates the tree_list variable for the View
        self.tree_list = tree_list

        #clears out the treeCtrl before re-adding packages
        self.hier_tree.DeleteAllItems()

        #iterate through all element trees
        for tree in tree_list:
            name = tree.getroot().find('Name').text

            #if the element tree's name is '_DSD', set this as the root, expand this tree item, and call recursive helper function to add its
            #children to the treeCtrl
            if name == '_DSD':
                self.root = self.hier_tree.AddRoot(name)
                self.hier_tree.EnsureVisible(self.root)
                self.add_tree_items(self.root, tree, tree_list, False)

            #expands all of the children nodes to '_DSD' (i.e. first level nodes) - must do this because otherwise no other children are visible
            child, cookie = self.hier_tree.GetFirstChild(self.root)
            while child.IsOk():
                self.hier_tree.EnsureVisible(child)
                child, cookie = self.hier_tree.GetNextChild(self.root, cookie)
        
        #expands the root and colors it green to show it is the current tree selected
        self.ExpandAndColorTreeItem(self.root, self.curr_tree.getroot().find('Name').text)

    #recursive helper function for refresh_tree - adds hierarchical properties of the curr_tree as children nodes to the treeCtrl
    def add_tree_items(self, curr_root, curr_tree, curr_tree_list, visible):

        #iterate through the current tree's hierarchical properties found within the dependent packages section of other properties
        for prop in curr_tree.getroot().find('Properties').iter('Property'):
            for package in prop.find('DependentPackages').iter('Package'):
                for hier_prop in package.find('HierarchicalProperties').iter('HierarchicalProperty'):
                    name = hier_prop.find('Value').text

                    #find the element tree corresponding to the current hierarchical property 
                    for tree in curr_tree_list:
                        if tree.getroot().find('Name').text == name:

                            #appends this element tree as a child to the current root and sets EnsureVisible variable (which keeps track of whether or
                            # not the loop has reached the current element tree or not - if so, EnsureVisible is True and method will set all of the 
                            # following children to be expanded)
                            new_tree_item = self.hier_tree.AppendItem(curr_root, name)
                            EnsureVisible = visible

                            #if the loop has reached the current element tree, EnsureVisible is set to True and the current treeCtrl item is expanded
                            if tree.getroot().find('Name').text == self.curr_tree.getroot().find('Name').text:
                                EnsureVisible = True
                            if(EnsureVisible == True):    
                                self.hier_tree.EnsureVisible(new_tree_item)

                            #recursive call to function with the new treeCtrl item as the current root and EnsureVisible set to new value
                            self.add_tree_items(new_tree_item, tree, curr_tree_list, EnsureVisible) 
        
        #iterate through the current tree's hierarchical properties 
        for hier_prop in curr_tree.getroot().find('HierarchicalProperties').iter('HierarchicalProperty'):
            name = hier_prop.find('Value').text

            #find the element tree corresponding to the current hierarchical property 
            for tree in curr_tree_list:
                if tree.getroot().find('Name').text == name:

                    #appends this element tree as a child to the current root and sets EnsureVisible variable (which keeps track of whether or
                    # not the loop has reached the current element tree or not - if so, EnsureVisible is True and method will set all of the 
                    # following children to be expanded)
                    new_tree_item = self.hier_tree.AppendItem(curr_root, name)
                    EnsureVisible = visible

                    #if the loop has reached the current element tree, EnsureVisible is set to True and the current treeCtrl item is expanded
                    if tree.getroot().find('Name').text == self.curr_tree.getroot().find('Name').text:
                        EnsureVisible = True
                    if(EnsureVisible == True):    
                        self.hier_tree.EnsureVisible(new_tree_item)

                    #recursive call to function with the new treeCtrl item as the current root and EnsureVisible set to new value
                    self.add_tree_items(new_tree_item, tree, curr_tree_list, EnsureVisible)  

    #updates the Main Window UI to display the current Element Tree's properties and hierarchical properties. 
    def refresh(self, tree):
        #updates the curr_tree variable
        self.curr_tree = tree

        #adjusts number of rows in properties grid to match the current tree
        num = self.props_grid.GetNumberRows()
        root = tree.getroot()
        
        row_counter = 0
        for prop in root.iter('Property'):
            row_counter +=1
        
        if row_counter < num:
            self.props_grid.DeleteRows(0, num-row_counter)
        
        if num < row_counter:
            self.props_grid.AppendRows(row_counter-num)

        #counter is used to keep track of what row the loop is in as properties are added to the grid
        counter = 0

        #updates properties grid
        for prop in root.iter('Property'):
            name = prop.find('Name').text
            val = prop.find('Value').text

            dType = prop.find('DataType').text

            if val is not None:
                self.props_grid.SetCellValue(counter, 2, val)
            else:
                self.props_grid.SetCellValue(counter, 2, "")

            self.props_grid.SetCellValue(counter, 0, name)
            self.props_grid.SetCellValue(counter, 1, dType)
            self.props_grid.SetReadOnly(counter, 0, isReadOnly=False)
            self.props_grid.SetReadOnly(counter, 1, isReadOnly=True)

            counter += 1

        #adjusts number of rows in hierarchical properties grid to match the current tree
        num = self.packs_grid.GetNumberRows()
        root = tree.getroot()
        
        row_counter = 0
        for prop in root.iter('HierarchicalProperty'):
            row_counter +=1
        
        if row_counter < num:
            self.packs_grid.DeleteRows(0, num-row_counter)
        
        if num < row_counter:
            self.packs_grid.AppendRows(row_counter-num)

        #counter is used to keep track of what row the loop is in as properties are added to the grid
        counter = 0

        #updates hierarchical properties grid with hierarchical properties that aren't associated with other properties (these have editable names)
        for hier_prop in root.find('HierarchicalProperties').iter('HierarchicalProperty'):
            name = hier_prop.find('Name').text
            prefix = hier_prop.find('PackageNamePrefix').text 
            dType = hier_prop.find('DataType').text 
            val = hier_prop.find('Value').text

            if val is not None:
                prefix = val

            self.packs_grid.SetCellValue(counter, 0, name)
            self.packs_grid.SetCellValue(counter, 1, dType)
            self.packs_grid.SetCellValue(counter, 2, prefix)
            self.packs_grid.SetReadOnly(counter, 0, isReadOnly=False)
            self.packs_grid.SetReadOnly(counter, 1, isReadOnly=True)
            self.packs_grid.SetReadOnly(counter, 2, isReadOnly=False)
            counter += 1

        #updates hierarchical properties grid with hierarchical properties that are associated with other properties (these have non-editable names)
        for prop in root.find('Properties').iter('Property'):
            for pack in prop.find('DependentPackages').iter('Package'):
                for hier_prop in pack.find('HierarchicalProperties').iter('HierarchicalProperty'):

                    name = hier_prop.find('Name').text
                    prefix = hier_prop.find('PackageNamePrefix').text 
                    dType = hier_prop.find('DataType').text 
                    val = hier_prop.find('Value').text

                    if val is not None:
                        prefix = val

                    self.packs_grid.SetCellValue(counter, 0, name)
                    self.packs_grid.SetCellValue(counter, 1, dType)
                    self.packs_grid.SetCellValue(counter, 2, prefix)
                    self.packs_grid.SetReadOnly(counter, 0, isReadOnly=True)
                    self.packs_grid.SetReadOnly(counter, 1, isReadOnly=True)
                    self.packs_grid.SetReadOnly(counter, 2, isReadOnly=True)
                    counter += 1

#This class displays the app's UI for the Generate ASL Frame using wxPython widgets. In this frame, the user can define their 
#device name/vendor name/vendor type before generating the ASL file. 
class GenerateASLFrame(wx.Frame):

    def __init__(self, MainWindow):
        self.main_window = MainWindow
        wx.Frame.__init__(self, None, title="Generate ASL Frame", size = (400, 400))
        asl_panel = wx.Panel(self)
        asl_panel.SetBackgroundColour("white")

        deviceLabel = wx.StaticText(parent = asl_panel, label="Device Name: ")
        self.device = wx.TextCtrl(parent = asl_panel, value = "")
        self.device.SetMaxLength(4)
        my_list = ['_HID', '_ADR']
        self.combo = wx.ComboBox(parent = asl_panel, choices = my_list)
        self.HIDValueLabel = wx.StaticText(parent = asl_panel, label="_HID Value:")
        self.HIDValue = wx.TextCtrl(parent = asl_panel, value = "")
        self.CIDValueLabel = wx.StaticText(parent = asl_panel, label="_CID Value:")
        self.CIDValue = wx.TextCtrl(parent = asl_panel, value = "")
        self.ADRValueLabel = wx.StaticText(parent = asl_panel, label="_ADR Value:")
        self.ADRValue = wx.TextCtrl(parent = asl_panel, value = "")
        closeBtn = wx.Button(parent = asl_panel, label="Generate ASL")
        closeBtn.Bind(wx.EVT_BUTTON, self.open_main)

        #adds all widgets to the main panel using a box sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(deviceLabel, 0, wx.ALL, border=10)
        self.sizer.Add(self.device,  0, wx.ALL, border=10)
        self.sizer.Add(self.combo,  0, wx.ALL, border=10)
        self.sizer.Add(self.HIDValueLabel,  0, wx.ALL, border=10)
        self.sizer.Add(self.HIDValue,  0, wx.ALL, border=10)
        self.sizer.Add(self.CIDValueLabel, 0, wx.ALL, border=10)
        self.sizer.Add(self.CIDValue, 0, wx.ALL, border=10)
        self.sizer.Add(self.ADRValueLabel, 0, wx.ALL, border=10)
        self.sizer.Add(self.ADRValue, 0, wx.ALL, border=10)
        self.sizer.Add(closeBtn, 0, wx.ALL, border=10)
        asl_panel.SetSizer(self.sizer)

        #hides the text boxes for _HID/_CID/_ADR until the user selects one from the combo box
        self.HIDValueLabel.Hide()
        self.HIDValue.Hide()
        self.CIDValueLabel.Hide()
        self.CIDValue.Hide()
        self.ADRValueLabel.Hide()
        self.ADRValue.Hide()

        self.combo.Bind(wx.EVT_COMBOBOX, self.type_selected)
        self.Bind(wx.EVT_CLOSE, self.close_window)
    
    #called when a type has been selected from the combo box - will show the appropriate text boxes for _HID, _CID, or _ADR
    def type_selected(self, event):
        choice = self.combo.GetValue()
        if choice == '_HID':
            self.HIDValueLabel.Show()
            self.HIDValue.Show()
            self.CIDValueLabel.Show()
            self.CIDValue.Show()
            self.ADRValueLabel.Hide()
            self.ADRValue.Hide()
        else:
            self.ADRValueLabel.Show()
            self.ADRValue.Show()
            self.HIDValueLabel.Hide()
            self.HIDValue.Hide()
            self.CIDValueLabel.Hide()
            self.CIDValue.Hide()
        
        self.sizer.Layout()

    #called when the user exits the window - does not add any new property
    def close_window(self, event):
        self.main_window.Enable()
        self.Destroy()

    def open_main(self, event):
        #creates a list with all of the tag values to be passed to generate ASL function
        deviceMsg = self.device.GetValue()
        hidMsg = self.HIDValue.GetValue()
        cidMsg = self.CIDValue.GetValue()
        adrMsg = self.ADRValue.GetValue()

        #TODO: before sending the message to generate the asl file, check every property (in current tree as well as all of its child
        # trees) and make sure it has a value if it is required - if not, show an error message and do not generate the asl file

        #first check that HID or ADR are filled in - if not, show a messagebox in the view and do not proceed
        #otherwise, open up a filedialog and pass that path here so that asl file is saved somewhere specific
        if (hidMsg == '') & (adrMsg == ''):
            wx.MessageBox(message = 'Please either enter a _HID or _ADR value.', caption='Generate ASL error',style=wx.OK | wx.ICON_ERROR)
        else:
            #shows file dialog to chose path, closes current window, and returns to the main window

            dlg = wx.DirDialog(self, "Choose folder to save to", style = wx.DD_DEFAULT_STYLE)

            if dlg.ShowModal() == wx.ID_OK:

                path = os.path.join(dlg.GetPath(), deviceMsg + '.asl')
                self.main_window.Enable()
                self.Close()
                pub.sendMessage("generate_asl", message = [deviceMsg, hidMsg, cidMsg, adrMsg, path])

            dlg.Destroy()

#This class displays the app's UI for the Hierarchical Property Frame using wxPython widgets. In this frame, the user can type in
#all of the fields for a new property and then add that property to the current element tree.
class HierarchicalPropertyFrame(wx.Frame):

    #initializes the Hierarchical Property Frame with the appropraite wxPython widgets
    def __init__(self, MainWindow, tree_list, curr_tree):

        #saves reference to the Main Window to reopen it once the Property Frame is closed. 
        self.main_window = MainWindow
        self.tree_list = tree_list
        self.curr_tree = curr_tree

        wx.Frame.__init__(self, None, title="Hierarchical Property Frame", size = (400, 570))
        hier_prop_panel = wx.Panel(self)
        hier_prop_panel.SetBackgroundColour("white")

        nameLabel = wx.StaticText(parent = hier_prop_panel, label="Name: ")
        self.name = wx.TextCtrl(parent = hier_prop_panel, value = "")
        dataLabel = wx.StaticText(parent = hier_prop_panel, label="Data Type:")
        self.data = wx.TextCtrl(parent = hier_prop_panel, value = "String", style = wx.TE_READONLY)
        descriptionLabel = wx.StaticText(parent = hier_prop_panel, label="Description:")
        self.description = wx.TextCtrl(parent = hier_prop_panel, value = "")
        requiredLabel = wx.StaticText(parent = hier_prop_panel, label="Required:")
        self.required = wx.CheckBox(parent = hier_prop_panel)
        modifyLabel = wx.StaticText(parent = hier_prop_panel, label="OEM modifiable:")
        self.modify = wx.CheckBox(parent = hier_prop_panel)
        prefixLabel = wx.StaticText(parent = hier_prop_panel, label="Package name prefix:")
        self.prefix = wx.TextCtrl(parent = hier_prop_panel, value = "")
        fileLabel = wx.StaticText(parent = hier_prop_panel, label="File name:")
        self.file = wx.TextCtrl(parent = hier_prop_panel, value = "")
        valueLabel = wx.StaticText(parent = hier_prop_panel, label="Package Name:")
        self.value = wx.TextCtrl(parent = hier_prop_panel, value = "")

        closeBtn = wx.Button(parent = hier_prop_panel, label="Add")
        closeBtn.Bind(wx.EVT_BUTTON, self.open_main)
        self.Bind(wx.EVT_CLOSE, self.close_window)

        #adds all widgets to the main panel using a box sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(nameLabel, 0, wx.ALL, border=5)
        sizer.Add(self.name, 0, wx.ALL, border=5)
        sizer.Add(dataLabel, 0, wx.ALL, border=5)
        sizer.Add(self.data, 0, wx.ALL, border=5)
        sizer.Add(descriptionLabel, 0, wx.ALL, border=5)
        sizer.Add(self.description, 0, wx.ALL, border=5)
        sizer.Add(requiredLabel, 0, wx.ALL, border=5)
        sizer.Add(self.required, 0, wx.ALL, border=5)
        sizer.Add(modifyLabel, 0, wx.ALL, border=5)
        sizer.Add(self.modify, 0, wx.ALL, border=5)
        sizer.Add(prefixLabel, 0, wx.ALL, border=5)
        sizer.Add(self.prefix, 0, wx.ALL, border=5)
        sizer.Add(valueLabel, 0, wx.ALL, border=5)
        sizer.Add(self.value, 0, wx.ALL, border=5)
        sizer.Add(fileLabel, 0, wx.ALL, border=5)
        sizer.Add(self.file, 0, wx.ALL, border=5)
        sizer.Add(closeBtn, 0, wx.ALL, border=5)
        hier_prop_panel.SetSizer(sizer)

    #called when the user exits the window - does not add any new property
    def close_window(self, event):
        self.main_window.Enable()
        self.Destroy()
    
    #opens up the main window, closes the hierarchical properties window, and adds the appropriate hierarchical property to the current tree
    def open_main(self, event):
        #creates a list with all of the tag values for the new property
        nameMsg = self.name.GetValue()
        dataMsg = self.data.GetValue()
        descriptionMsg = self.description.GetValue()
        requiredMsg = self.required.GetValue()
        modifyMsg = self.modify.GetValue()
        valueMsg = self.value.GetValue()
        fileMsg = self.file.GetValue()
        prefixMsg = self.prefix.GetValue()
        messageList = [nameMsg, dataMsg, str(int(requiredMsg)), descriptionMsg, str(int(modifyMsg)), prefixMsg, valueMsg, fileMsg, None, None]

        result_new = wx.ID_NONE
        ancestor = False
        over_four = False

        #if the new value is not four characters, an error message is shown and the over_four variable is set to true
        if len(valueMsg) > 4:
            wx.MessageBox(message = valueMsg + ' is over 4 characters. Please choose a name that is less than or equal to 4 characters.', caption='Package name error',style=wx.OK | wx.ICON_ERROR)
            over_four = True

        #TODO: move the following data validation to the Controller (checking if tree is an ancestor of curr_tree)
            
        #this loop determines if there is an existing element tree associated with the new hierarchical property value - if there is, an 
        #error message is sent if the existing tree is an ancestor of the curr_tree (because this would cause an infinite loop) and a 
        #warning message pops up telling the user if they use this value, they will be sharing this package among other parents.
        for tree in self.tree_list:
            if tree.getroot().find('Name').text == valueMsg:
                ancestor = self.is_ancestor(tree, self.curr_tree)
                if ancestor == True:
                    wx.MessageBox(message = 'Circular reference found. One of the parent packages has the same name.' , caption='Package name error',style=wx.OK | wx.ICON_ERROR)
                else:
                    result_new = wx.MessageBox(message = valueMsg + ' is an existing package. Do you want to re-use existing package?', caption='Package name warning',style = wx.YES_NO|wx.WARNING)

        #if the user does not get the warning message or replies "yes" to it, the new value is not an ancestor of the current element tree,
        #the value is equal or less than four characters, and the name/data/value/file are filled out, the new hierarchical property is added to the model
        if (result_new != wx.NO) & (ancestor == False) & (over_four == False):
            if (nameMsg == '') | (dataMsg == '') | (valueMsg == '') | (fileMsg == ''):
                wx.MessageBox(message = 'Please fill out all information for the hierarchical property before adding it.' , caption='Property error',style=wx.OK | wx.ICON_ERROR)
            else:
                pub.sendMessage("new_hier_property_added", message=messageList)
                self.main_window.Enable()
                self.Close()

    #move this function to the Controller
    #TODO: this function is repeat code from the MainFrame class. Define an interface to share between all three
    #windows with common code.
    #helper function for OnPacksGridCellChange - returns true if higher_tree is an ancestor of lower_tree and returns false otherwise
    def is_ancestor(self, higher_tree, lower_tree):
        #find hier_props and loop through - for each one, find that tree and if it matches lower_tree, return true. otherwise, call this
        #function again but with (new tree, lower_tree)

        higher_name = higher_tree.getroot().find('Name').text
        lower_name = lower_tree.getroot().find('Name').text

        #Base case: if the trees are the same, return true 
        if higher_name == lower_name:
            return True
        
        #Recursive case: loop through the hierarchical properties of the higher_tree. For each one, find its associated element tree
        #and call this function again with this element tree as the higher_tree; return True if the function returns True.
        for hier_prop in higher_tree.getroot().find('HierarchicalProperties').iter('HierarchicalProperty'):
            name = hier_prop.find('Value').text
            for tree in self.tree_list:
                if tree.getroot().find('Name').text == name:
                    result = self.is_ancestor(tree, lower_tree)
                    if result == True:
                        return True
        
        #If the function goes through all of the trees under higher_tree and does not find a match to lower_tree, return False
        return False

#This class displays the app's UI for the Property Frame using wxPython widgets. In this frame, the user can type in
#all of the fields for a new property and then add that property to the current element tree.
class PropertyFrame(wx.Frame):

    #initializes the Property Frame with the appropraite wxPython widgets
    def __init__(self, MainWindow):

        #saves reference to the Main Window to reopen it once the Property Frame is closed. 
        self.main_window = MainWindow

        wx.Frame.__init__(self, None, title="Property Frame", size = (400, 450))
        propertyPanel = wx.Panel(self)
        propertyPanel.SetBackgroundColour("white")

        nameLabel = wx.StaticText(parent = propertyPanel, label="Name: ")
        self.name = wx.TextCtrl(parent = propertyPanel, value = "")

        my_list = ['String', 'Integer', 'Package', 'Boolean', 'Bitmap']
        self.combo = wx.ComboBox(parent = propertyPanel, choices = my_list)

        dataLabel = wx.StaticText(parent = propertyPanel, label="Data Type:")
        descriptionLabel = wx.StaticText(parent = propertyPanel, label="Description:")
        self.description = wx.TextCtrl(parent = propertyPanel, value = "")
        requiredLabel = wx.StaticText(parent = propertyPanel, label="Required:")
        self.required = wx.CheckBox(parent = propertyPanel)
        modifyLabel = wx.StaticText(parent = propertyPanel, label="OEM modifiable:")
        self.modify = wx.CheckBox(parent = propertyPanel)
        valueLabel = wx.StaticText(parent = propertyPanel, label="Value:")
        self.value = wx.TextCtrl(parent = propertyPanel, value = "")

        closeBtn = wx.Button(parent = propertyPanel, label="Add")
        closeBtn.Bind(wx.EVT_BUTTON, self.open_main)

        self.Bind(wx.EVT_CLOSE, self.close_window)

        #adds all widgets to the main panel using a box sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(nameLabel, 0, wx.ALL, border=5)
        sizer.Add(self.name, 0, wx.ALL, border=5)
        sizer.Add(dataLabel, 0, wx.ALL, border=5)
        sizer.Add(self.combo, 0, wx.ALL, border=5)
        sizer.Add(descriptionLabel, 0, wx.ALL, border=5)
        sizer.Add(self.description, 0, wx.ALL, border=5)
        sizer.Add(requiredLabel, 0, wx.ALL, border=5)
        sizer.Add(self.required, 0, wx.ALL, border=5)
        sizer.Add(modifyLabel, 0, wx.ALL, border=5)
        sizer.Add(self.modify, 0, wx.ALL, border=5)
        sizer.Add(valueLabel, 0, wx.ALL, border=5)
        sizer.Add(self.value, 0, wx.ALL, border=5)
        sizer.Add(closeBtn, 0, wx.ALL, border=5)
        propertyPanel.SetSizer(sizer)

    #called when the user exits the window - does not add any new property
    def close_window(self, event):
        self.main_window.Enable()
        self.Destroy()
        
    #re-opens the Main Window, sends out all of the information for the new property the user just added in a message to 
    #the rest of the program, and closes the Property Window 
    def open_main(self, event):

        #creates a list with all of the tag values for the new property
        nameMsg = self.name.GetValue()
        dataMsg = self.combo.GetValue()
        descriptionMsg = self.description.GetValue()
        requiredMsg = self.required.GetValue()
        modifyMsg = self.modify.GetValue()
        valueMsg = self.value.GetValue()
        messageList = [nameMsg, dataMsg, int(requiredMsg), descriptionMsg, int(modifyMsg), valueMsg]

        if (nameMsg == '') | (dataMsg == '') | (valueMsg == ''):
            wx.MessageBox(message = 'Please fill out all information for the property before adding it.' , caption='Property error',style=wx.OK | wx.ICON_ERROR)

        else:
            pub.sendMessage("property_added", message=messageList)
            self.main_window.Enable()
            self.Close()