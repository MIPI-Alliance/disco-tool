#  ------------------------------------------------------------------------------
#
#  Copyright (C) Microsoft Corporation. All rights reserved.
#
#  Module Name:
#
#    controller.py
#
#  Abstract:
#
#    Main class for handling the communication between the GUI and the model.
#
#  -------------------------------------------------------------------------------

from pubsub import pub
import model
import view
import ASLgenerator
import wx
import xml.dom.minidom as md
import xml.etree.ElementTree as et
import os

#This class takes care of communication between the view and the model. It has listeners for when events occur in the UI 
#and the View sends out corresponding messages. When the Controller receives these, it calls the appropriate method to update the 
#model's data and the view's GUI. It is also respondible for other program logic, including generating the final ASL
#file and correctly saving different versions of intermediate xml files. 
class controller():

    #called when the starting xml template is chosen by the user - updates model's data and view's UI with this data (message is the file path)
    def new_file_chosen(self, message):
        self.view.set_data_changed(True)
        print("setting data changed to true")

        #starting file template name is always set to _DSD
        templateName = '_DSD'
        #new_mssg = message

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
        self.view.refresh(new_tree)
        tree_list = self.model.get_tree_list()
        self.view.refresh_tree(tree_list)

    #called when an existing project is chosen by the user to continue working on - updates model's data and view's UI with this data and adds
    #any existing element trees in the intermediate xml files (message is the directory path)
    def new_project_chosen(self, message):
        #finds the starting template in this directory
        path = os.path.join(message, '_DSD.xml')
        tree = et.parse(path)

        #tree = et.parse(message + "\\_DSD.xml")
        print(message + "\\_DSD.xml")

        #adds all of the existing element trees and sets the project path to be the same location the user just chose
        self.model.set_project_path(message)
        self.model.add_element_trees(tree, '_DSD', '1')

        #sets this starting xml file as the current element tree and refreshes both the tree and the tree_list in the View
        self.model.set_curr_tree('_DSD')
        new_tree = self.model.get_curr_tree()
        self.view.refresh(new_tree)
        tree_list = self.model.get_tree_list()
        self.view.refresh_tree(tree_list)

    #called when the user clicks on a new package in the hierarchy on the left of the screen - changes the current tree and refreshes the view.
    #message is the name of the new package chosen.
    def new_tree_chosen(self, message):
        self.model.set_curr_tree(message)
        new_tree = self.model.get_curr_tree()
        self.view.refresh(new_tree)

    #called when a new property is added by the user - updates model's data and view's UI with this data
    def property_added(self, message):
        #Print statement for debugging purposes:
        self.view.set_data_changed(True)
        print("setting data changed to true")

        self.model.add_property(message)
        new_tree = self.model.get_curr_tree()
        self.view.refresh(new_tree)

    #called when user inputs a value for a property that does not have dependent packages - updates model's data and view's UI with this data
    def property_value_changed(self, message):
        #Print statement for debugging purposes:
        self.view.set_data_changed(True)
        print("setting data changed to true")

        self.model.update_property_value(message)
        new_tree = self.model.get_curr_tree()
        self.view.refresh(new_tree)

        new_tree_list = self.model.get_tree_list()
        self.view.refresh_tree(new_tree_list)

    #called when user inputs a value for a hierarchical property - updates model's data and view's UI with this data
    def hier_property_value_changed(self, message):
        #Print statement for debugging purposes:
        self.view.set_data_changed(True)
        print("setting data changed to true")

        self.model.update_hier_property_value(message)

        new_tree = self.model.get_curr_tree()
        self.view.refresh(new_tree)

        tree_list = self.model.get_tree_list()
        self.view.refresh_tree(tree_list)

    #called when user presses the 'save' button (saves all element trees as files named with their template names)
    def save_files(self, message):
        #changes the set_data_changed variable to False because we just saved
        self.view.set_data_changed(False)
        print("initializing data changed to false")

        tree_list = self.model.get_tree_list()
        
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
            with open(path,'w') as my_file:
                tree_str_pretty = tree_str_parsed.toprettyxml(indent='\t', newl='\n')
                tree_str_pretty = os.linesep.join([s for s in tree_str_pretty.splitlines() if s.strip()])
                my_file.write(tree_str_pretty)

    #called when user presses the "save as" button or when they save their work for the first time (message is the path the user chose to save to)
    def save_as(self, message):
        #changes the set_data_changed variable to False because we just saved
        self.view.set_data_changed(False)
        print("initializing data changed to false")

        tree_list = self.model.get_tree_list()
        
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
            with open(path,'w') as my_file:
                tree_str_pretty = tree_str_parsed.toprettyxml(indent='\t', newl='\n')
                tree_str_pretty = os.linesep.join([s for s in tree_str_pretty.splitlines() if s.strip()])
                my_file.write(tree_str_pretty)

        #updating the project path to be the path the user just chose
        self.model.set_project_path(message)

    #called when user pressed the "generate ASL" button 
    def generate_asl(self, message):
        generator = ASLgenerator.ASLgenerator(self.model)
        generator.generate_asl('_DSD', message[0], message[1], message[2], message[3], message[4])

    #called when the user is adding a NEW hierarchical property - message consists of property name/data type/required
    #/description/OEMmodify/packagenameprefix/value/filename
    def new_hier_property_added(self, message):
        #Print statement for debugging purposes:
        self.view.set_data_changed(True)
        print("setting data changed to true")

        self.model.add_new_hier_property(message)
        new_tree = self.model.get_curr_tree()
        self.view.refresh(new_tree)

        tree_list = self.model.get_tree_list()
        self.view.refresh_tree(tree_list)

    #called when the user deletes a property - message consists of that property's name
    def property_deleted(self, message):
        #Print statement for debugging purposes:
        self.view.set_data_changed(True)
        print("setting data changed to true")

        self.model.delete_property(message)
        new_tree = self.model.get_curr_tree()
        self.view.refresh(new_tree)

        tree_list = self.model.get_tree_list()
        self.view.refresh_tree(tree_list)

    #called when the user deletes a hierarchical property - message consists of property name, property location, package location, current tree (locations will be None
    # if the hierarchical property does not come from a property's dependent package)
    def hier_property_deleted(self, message):
        #Print statement for debugging purposes:
        self.view.set_data_changed(True)
        print("setting data changed to true")

        self.model.delete_hier_property(message)
        new_tree = self.model.get_curr_tree()
        self.view.refresh(new_tree)

        new_tree_list = self.model.get_tree_list()
        self.view.refresh_tree(new_tree_list)

    #called when the user cahnges the name of a property (message = value, old_value)
    def property_name_changed(self, message):
        #Print statement for debugging purposes:
        self.view.set_data_changed(True)
        print("setting data changed to true")

        self.model.update_property_name(message)
        new_tree = self.model.get_curr_tree()
        self.view.refresh(new_tree)

    #called when the user changes the name of a hierarchical property (message = value, old_value)
    def hier_property_name_changed(self, message):
        #Print statement for debugging purposes:
        self.view.set_data_changed(True)
        print("setting data changed to true")

        self.model.update_hier_property_name(message)
        new_tree = self.model.get_curr_tree()
        self.view.refresh(new_tree)

        new_tree_list = self.model.get_tree_list()
        self.view.refresh_tree(new_tree_list)
    
    #called when the View needs to get the current tree list
    def get_tree_list(self, message):
        self.model.get_tree_list()

    #declares the model and view for this controller and lists all of the listeners this controller has for UI events
    def __init__(self):
        pub.subscribe(self.new_file_chosen, "new_file_chosen")
        pub.subscribe(self.new_project_chosen, "new_project_chosen")
        pub.subscribe(self.new_tree_chosen, "new_tree_chosen")

        pub.subscribe(self.property_added, "property_added")
        pub.subscribe(self.property_value_changed , "property_value_changed")
        pub.subscribe(self.hier_property_value_changed , "hier_property_value_changed")
        pub.subscribe(self.hier_property_name_changed, "hier_property_name_changed")
        pub.subscribe(self.property_name_changed, "property_name_changed")
        pub.subscribe(self.save_files , "save")

        pub.subscribe(self.new_hier_property_added, "new_hier_property_added")
        pub.subscribe(self.hier_property_deleted, "hier_property_deleted")

        pub.subscribe(self.property_deleted, "property_deleted")
        pub.subscribe(self.save_as, "save_as")
        pub.subscribe(self.generate_asl, "generate_asl")
        pub.subscribe(self.get_tree_list, "get_tree_list")
        self.model = model.model()
        self.view = view.MainFrame()

        # self.test_view = test.TestModel()
        # self.test_view.test_create_hier_props_list_1()

#declares the controller and initializes the application
if __name__ == '__main__':
    app = wx.App()
    myController = controller()
    app.MainLoop()
