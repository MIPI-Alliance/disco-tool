#  ------------------------------------------------------------------------------
#
#  Copyright (C) Microsoft Corporation. All rights reserved.
#
#  Module Name:
#
#    test.py
#
#  Abstract:
#
#    Unit testing for elements of the Controller class.
#
#  -------------------------------------------------------------------------------

import unittest
from pubsub import pub
import model
import xml.etree.ElementTree as et
import os
import logging
import sys

#TODO: test data validation, certain functions in the Controller (save_files/save_as/new_file_chosen/new_project_chosen),
#and generate_asl in ASLgenerator

#this class creates a log_file.txt with information on what test cases passed, what test cases and failed, and what the specific
#failures were

#all xml templates as well as testFile1, testFolder2, and testFolder3 must be in the same directory as the file's source code (i.e. the
# same directory as .vscode)

#unit tests for the Model class (i.e. for manipulating element tree data)
class TestModel(unittest.TestCase):

    #local path to the xml templates folder and the predfined test xml files
    #TEST_TEMPLATE_PATH = "C:\\Users\\t-judzmu\\Desktop\\discoToolMockups\\"
    TEST_TEMPLATE_PATH = ""
    TEST_FILE_1_PATH = TEST_TEMPLATE_PATH + "testFile1.xml"
    TEST_FOLDER_2_PATH = TEST_TEMPLATE_PATH + "testFolder2"
    TEST_FOLDER_3_PATH = TEST_TEMPLATE_PATH + "testFolder3"

    #tests create_hier_props_list when the interpret type is integer
    def test_create_hier_props_list_1(self):
        my_model = model.model()

        result = my_model.create_hier_props_lists('Integer', '5', '3')
        to_add = result[0]
        to_delete = result[1]

        self.assertEqual(to_add, [], "incorrect list of hierarchical properties to add (interpret type = Integer)")
        self.assertEqual(to_delete, [3, 4], "incorrect list of hierarchical properties to delete (interpret type = Integer)")
    
    #tests create_hier_props_list when the interpret type is package 
    def test_create_hier_props_list_2(self):
        my_model = model.model()

        result = my_model.create_hier_props_lists('Package', '1, 7, 3, 8, 9', '1, 6, 2, 3')
        to_add = result[0]
        to_delete = result[1]

        self.assertEqual(to_add, [6, 2], "incorrect list of hierarchical properties to add (interpret type = Package)")
        self.assertEqual(to_delete, [7, 8, 9], "incorrect list of hierarchical properties to delete (interpret type = Package)")
    
    #tests create_hier_props_list when the interpret type is bitmap 
    def test_create_hier_props_list_3(self):
        my_model = model.model()

        result = my_model.create_hier_props_lists('BitMap', '1110', '01')
        to_add = result[0]
        to_delete = result[1]

        self.assertEqual(to_add, [0], "incorrect list of hierarchical properties to add (interpret type = BitMap)")
        self.assertEqual(to_delete, [3, 2, 1], "incorrect list of hierarchical properties to delete (interpret type = BitMap)")

    #tests update_property_value function when user changes the value of a property with no dependent packages
    def test_update_property_value_1(self):

        my_model = model.model()

        #creates element tree based off of testFile1 xml file and adds it as the current element tree
        tree = et.parse(TestModel.TEST_FILE_1_PATH)
        my_model.add_element_tree(tree, '_DSD', 1)
        my_model.set_template_path(TestModel.TEST_TEMPLATE_PATH)
        my_model.set_curr_tree('_DSD')

        #calls the update_property_value function on the element tree
        my_model.update_property_value(["property-2", "0", ""])
        tree = my_model.get_curr_tree()

        #checks that value was adjusted correctly
        for t in tree.getroot().find('Properties').iter('Property'):
            if t.find('Name') == "property-2":
                self.assertEqual(t.find('Value'), "0", "property value is incorrect")

    #tests update_property_value function when user changes the value of a property with a dependent package whose interpret value is a bitmap
    def test_update_property_value_2(self):

        my_model = model.model()

        #creates element tree based off of testFile1 xml file and adds it as the current element tree
        tree = et.parse(TestModel.TEST_FILE_1_PATH)
        my_model.add_element_tree(tree, '_DSD', 1)
        my_model.set_template_path(TestModel.TEST_TEMPLATE_PATH)
        my_model.set_curr_tree('_DSD')

        #calls the update_property_value function twice on the element tree
        my_model.update_property_value(["property-3", "1110", ""])
        my_model.update_property_value(["property-3", "010", "1110"])
        tree = my_model.get_curr_tree()
        tree_list = my_model.get_tree_list()

        #checks that the correct hierarchical property was created for the property's dependent package (and the correct ones were deleted)
        self.assertEqual(True, self.element_tree_exists('SK01', tree_list), 'SK01 was not created as an element tree')
        self.assertEqual(False, self.element_tree_exists('SK02', tree_list), 'the element tree for SK02 was not deleted')
        self.assertEqual(False, self.element_tree_exists('SK03', tree_list), 'the element tree for SK03 was not deleted')
    
    #tests update_property_name function when user changes the name of a normal property 
    def test_update_property_name(self):

        my_model = model.model()

        #creates element tree based off of testFile1 xml file and adds it as the current element tree
        tree = et.parse(TestModel.TEST_FILE_1_PATH)
        my_model.add_element_tree(tree, '_DSD', 1)
        my_model.set_template_path(TestModel.TEST_TEMPLATE_PATH)
        my_model.set_curr_tree('_DSD')

        #calls the update_property_name function on the element tree
        my_model.update_property_name(['new-name', 'property-1'])
        tree = my_model.get_curr_tree()

        found = False

        #sets found to true if the new property name is found 
        for t in tree.getroot().find('Properties').iter('Property'):
            if t.find('Name').text == "new-name":
                found = True

        #if new property name is found, test passes
        self.assertEqual(True, found, 'property name not updated')

    #tests update_hier_proeprty_name function when user changes the name of a hierarchical property 
    def test_update_hier_property_name(self):

        my_model = model.model()

        #creates element tree based off of testFile1 xml file and adds it as the current element tree
        tree = et.parse(TestModel.TEST_FILE_1_PATH)
        my_model.add_element_tree(tree, '_DSD', 1)
        my_model.set_template_path(TestModel.TEST_TEMPLATE_PATH)
        my_model.set_curr_tree('_DSD')

        #calls the update_hier_property_name function on the element tree
        my_model.update_hier_property_name(['new-name', 'hier-property-1'])
        tree = my_model.get_curr_tree()

        found = False

        #sets found to true if the new property name is found 
        for t in tree.getroot().find('HierarchicalProperties').iter('HierarchicalProperty'):
            if t.find('Name').text == "new-name":
                found = True
        
        #if new property name is found, test passes
        self.assertEqual(True, found, 'hierarchical property name not updated')

    #test delete_tree when user deletes an element tree with several children trees, both shared and unshared
    def test_delete_tree(self):

        my_model = model.model()

        #uploads existing element trees from the given path and sets the _DSD as the current tree
        
        path = os.path.join(TestModel.TEST_FOLDER_3_PATH, '_DSD.xml')
        tree = et.parse(path)
        my_model.set_project_path(TestModel.TEST_FOLDER_3_PATH)
        my_model.add_element_trees(tree, '_DSD', '1')

        my_model.set_template_path(TestModel.TEST_TEMPLATE_PATH)
        my_model.set_curr_tree('_DSD')

        #calls the delete_tree function on the element tree to delete DP00
        to_delete = None
        for tree in my_model.get_tree_list():
            if tree.find('Name').text == 'DP00':
                to_delete = tree

        my_model.delete_tree(to_delete)
        
        #makes sure that DP00 and its unshared children, BA00 and MS00, were deleted but its shared child, BA01, was not
        tree_list = my_model.get_tree_list()
        self.assertEqual(False, self.element_tree_exists('DP00', tree_list), 'the element tree for DP00 was not deleted')
        self.assertEqual(False, self.element_tree_exists('BA00', tree_list), 'the element tree for BA00 was not deleted')
        self.assertEqual(False, self.element_tree_exists('MS00', tree_list), 'the element tree for MS00 was not deleted')
        self.assertEqual(True, self.element_tree_exists('BA01', tree_list), 'the element tree for BA01 was deleted')

    #tests add_parent function 
    def test_add_parent(self):

        my_model = model.model()

        #creates element tree based off of testFile1 xml file and adds it as the current element tree
        tree = et.parse(TestModel.TEST_FILE_1_PATH)
        my_model.add_element_tree(tree, '_DSD', 1)
        my_model.set_template_path(TestModel.TEST_TEMPLATE_PATH)
        my_model.set_curr_tree('_DSD')

        #calls the add_parent function on the element tree
        my_model.add_parent(tree, 'my_parent')
        tree = my_model.get_curr_tree()
        tree_list = my_model.get_tree_list()

        #confirms parent tag was added to the correct element tree
        for tree in tree_list:
            if tree.getroot().find('Name').text == '_DSD':
                self.assertEqual(tree.getroot().find('Header').find('Parents').find('Parent').text, 'my_parent', 'parent tag was not added')

    #tests update_hier_property_value when user changes the value of a hierarchical property and the new value is shared and old value was not
    def test_update_hier_property_value_1(self):

        my_model = model.model()

        #uploads existing element trees from the given path and sets the _DSD as the current tree
        path = os.path.join(TestModel.TEST_FOLDER_2_PATH, '_DSD.xml')
        tree = et.parse(path)
        my_model.set_project_path(TestModel.TEST_FOLDER_2_PATH)
        my_model.add_element_trees(tree, '_DSD', '1')

        my_model.set_template_path(TestModel.TEST_TEMPLATE_PATH)
        my_model.set_curr_tree('_DSD')

        #calls the update_hier_property_value function on the element tree (changes DP02 - an unshared package - to DP00 - a shared package)
        my_model.update_hier_property_value(['hier-property-2', 'DP00', 'DP02'])
        tree = my_model.get_curr_tree() 
        tree_list = my_model.get_tree_list()

        #checks that DP02's element tree was deleted
        self.assertEqual(False, self.element_tree_exists('DP02', tree_list), 'the element tree for DP02 was not deleted')

        for tree in tree_list:

            #checks that DP00 now has two parents, each _DSD
            if tree.find('Name').text == 'DP00':
                parents = []
                for p in tree.find('Header').find('Parents').iter('Parent'):
                    parents.append(p.text)
                self.assertEqual(parents, ['_DSD', '_DSD'], 'DP00 does not have two parent tags')

            #checks that BA01 now only has one parent (DP03)
            if tree.find('Name').text == 'BA01':
                parents = []
                for p in tree.find('Header').find('Parents').iter('Parent'):
                    parents.append(p.text)
                self.assertEqual(parents, ['DP03'], 'DP03 does not have one parent tag')

    #tests update_hier_property_value when user changes the value of a hierarchical property and the new value is shared and old value was also shared
    def test_update_hier_property_value_2(self):

        my_model = model.model()

        #uploads existing element trees from the given path and sets DP03 as the current tree
        path = os.path.join(TestModel.TEST_FOLDER_2_PATH, '_DSD.xml')
        tree = et.parse(path)
        my_model.set_project_path(TestModel.TEST_FOLDER_2_PATH)
        my_model.add_element_trees(tree, '_DSD', '1')

        my_model.set_template_path(TestModel.TEST_TEMPLATE_PATH)
        my_model.set_curr_tree('DP03')

        #calls the update_hier_property_value function on the element tree (changes BA01 - a shared package - to BA00 - another shared package)
        my_model.update_hier_property_value(['mipi-sdw-port-bra-mode-m', 'BA00', 'BA01'])
        tree = my_model.get_curr_tree() 
        tree_list = my_model.get_tree_list()

        for tree in tree_list:

            #checks that BA00 now has three parents
            if tree.find('Name').text == 'BA00':
                parents = []
                for p in tree.find('Header').find('Parents').iter('Parent'):
                    parents.append(p.text)
                self.assertEqual(parents, ['DP01', 'DP00', 'DP03'], 'BA00 does not have three parent tags')

            #checks that BA01 now only has one parent
            if tree.find('Name').text == 'BA01':
                parents = []
                for p in tree.find('Header').find('Parents').iter('Parent'):
                    parents.append(p.text)
                self.assertEqual(parents, ['DP02'], 'BA01 does not have one parent tag')

    #tests update_hier_property_value when user changes the value of a hierarchical property and the new value is unshared and old value was also unshared
    def test_update_hier_property_value_3(self):

        my_model = model.model()

        #uploads existing element trees from the given path and sets DP03 as the current tree
        path = os.path.join(TestModel.TEST_FOLDER_2_PATH, '_DSD.xml')
        tree = et.parse(path)
        my_model.set_project_path(TestModel.TEST_FOLDER_2_PATH)
        my_model.add_element_trees(tree, '_DSD', '1')

        my_model.set_template_path(TestModel.TEST_TEMPLATE_PATH)
        my_model.set_curr_tree('_DSD')

        #calls the update_hier_property_value function on the element tree (changes BA01 - a shared package - to BA00 - another shared package)
        my_model.update_hier_property_value(['hier-property-1', 'DP04', 'DP01'])
        tree = my_model.get_curr_tree() 
        tree_list = my_model.get_tree_list()

        #checks that DP01's element tree was deleted
        self.assertEqual(False, self.element_tree_exists('DP01', tree_list), 'the element tree for DP01 was not deleted')

        for tree in tree_list:

            #checks that DP04 now exists and still has BA00 as its only hierarchical property
            if tree.find('Name').text == 'DP04':
                hier_props = []
                for h in tree.find('HierarchicalProperties').iter('HierarchicalProperty'):
                    hier_props.append(h.find('Value').text)
                self.assertEqual(hier_props, ['BA00'], 'the element tree for DP04 was not created correctly')

    #tests update_hier_property_value when user changes the value of a hierarchical property and the new value is unshared but the old value was shared
    def test_update_hier_property_value_4(self):

        my_model = model.model()

        #uploads existing element trees from the given path and sets DP03 as the current tree
        path = os.path.join(TestModel.TEST_FOLDER_2_PATH, '_DSD.xml')
        tree = et.parse(path)
        my_model.set_project_path(TestModel.TEST_FOLDER_2_PATH)
        my_model.add_element_trees(tree, '_DSD', '1')

        my_model.set_template_path(TestModel.TEST_TEMPLATE_PATH)
        my_model.set_curr_tree('DP00')

        #calls the update_hier_property_value function on the element tree (changes BA00 - a shared package - to BA02 - a new package)
        my_model.update_hier_property_value(['mipi-sdw-port-bra-mode-m', 'BA02', 'BA00'])
        tree = my_model.get_curr_tree() 
        tree_list = my_model.get_tree_list()

        for tree in tree_list:
            
            #checks that BA00 now has one parent
            if tree.find('Name').text == 'BA00':
                parents = []
                for p in tree.find('Header').find('Parents').iter('Parent'):
                    parents.append(p.text)
                self.assertEqual(parents, ['DP01'], 'BA00 does not have one parent')

            #checks that BA02 now exists and has the same data as BA00
            if tree.find('Name').text == 'BA02':
                for prop in tree.find('Properties').iter('Property'):
                    if prop.find('Name').text == 'mipi-sdw-bra-mode-max-bus-frequency':
                        self.assertEqual('1', prop.find('Value').text, 'the element tree for BA02 was not created correctly')

    #tests the delete_property function when the property does not have any dependent packages associated with it
    def test_delete_property_1(self):

        my_model = model.model()

        #uploads existing element trees from the given path and sets the _DSD as the current tree
        path = os.path.join(TestModel.TEST_FOLDER_2_PATH, '_DSD.xml')
        tree = et.parse(path)
        my_model.set_project_path(TestModel.TEST_FOLDER_2_PATH)
        my_model.add_element_trees(tree, '_DSD', '1')

        my_model.set_template_path(TestModel.TEST_TEMPLATE_PATH)
        my_model.set_curr_tree('_DSD')

        #calls the delete_property function on the element tree
        my_model.delete_property('mipi-sdw-port15-read-behavior')
        tree = my_model.get_curr_tree()
        tree_list = my_model.get_tree_list()

        found = False

        #makes sure the property that was just deleted no longer exists in the element tree
        for prop in tree.getroot().find('Properties').iter('Property'):
            if prop.find('Name').text == 'mipi-sdw-port15-read-behavior':
                found = True
        
        self.assertEqual(False, found, 'property was not deleted')

    #tests the delete_property function when the property does have a dependent package associated with it
    def test_delete_property_2(self):

        my_model = model.model()

        #uploads existing element trees from the given path and sets the _DSD as the current tree
        path = os.path.join(TestModel.TEST_FOLDER_2_PATH, '_DSD.xml')
        tree = et.parse(path)
        my_model.set_project_path(TestModel.TEST_FOLDER_2_PATH)
        my_model.add_element_trees(tree, '_DSD', '1')

        my_model.set_template_path(TestModel.TEST_TEMPLATE_PATH)
        my_model.set_curr_tree('_DSD')

        #calls the delete_property function on the element tree
        my_model.delete_property('mipi-sdw-master-count')
        tree = my_model.get_curr_tree()
        tree_list = my_model.get_tree_list()

        #makes sure the element trees associated with the property's dependent package are deleted
        self.assertEqual(False, self.element_tree_exists('MS00', tree_list), 'the element tree for MS00 was not deleted')
        self.assertEqual(False, self.element_tree_exists('MS01', tree_list), 'the element tree for MS01 was not deleted')

        found = False

        #makes sure the property that was just deleted no longer exists in the element tree
        for prop in tree.getroot().find('Properties').iter('Property'):
            if prop.find('Name').text == 'mipi-sdw-master-count':
                found = True

        self.assertEqual(False, found, 'property was not deleted')

    #test the delete_hier_property function when the user deletes a hierarchical property with a shared child package
    def test_delete_hier_property_1(self):

        my_model = model.model()

        #uploads existing element trees from the given path and sets the _DSD as the current tree
        path = os.path.join(TestModel.TEST_FOLDER_2_PATH, '_DSD.xml')
        tree = et.parse(path)
        my_model.set_project_path(TestModel.TEST_FOLDER_2_PATH)
        my_model.add_element_trees(tree, '_DSD', '1')

        my_model.set_template_path(TestModel.TEST_TEMPLATE_PATH)
        my_model.set_curr_tree('_DSD')

        #calls the delete_hier_property function on the element tree
        my_model.delete_hier_property(['hier-property-1', None, None, my_model.get_curr_tree()])
        tree = my_model.get_curr_tree()
        tree_list = my_model.get_tree_list()

        #check that DP01's element tree has been deleted
        self.assertEqual(False, self.element_tree_exists('DP01', tree_list), 'the element tree for DP01 was not deleted')

        for tree in tree_list:

            #checks that BA00 now has one parent
            if tree.find('Name').text == 'BA00':
                parents = []
                for p in tree.find('Header').find('Parents').iter('Parent'):
                    parents.append(p.text)
                self.assertEqual(parents, ['DP00'], 'BA00 does not have one parent tag')

    #test the delete_hier_property function when the user deletes a hierarchical property with a shared child package and an unshared child package
    def test_delete_hier_property_2(self):

        my_model = model.model()

        #uploads existing element trees from the given path and sets the _DSD as the current tree
        path = os.path.join(TestModel.TEST_FOLDER_3_PATH, '_DSD.xml')
        tree = et.parse(path)
        my_model.set_project_path(TestModel.TEST_FOLDER_3_PATH)
        my_model.add_element_trees(tree, '_DSD', '1')

        my_model.set_template_path(TestModel.TEST_TEMPLATE_PATH)
        my_model.set_curr_tree('_DSD')

        #calls the delete_hier_property function on the element tree
        my_model.delete_hier_property(['mipi-sdw-dp-0-subproperties', None, None, my_model.get_curr_tree()])
        tree = my_model.get_curr_tree()
        tree_list = my_model.get_tree_list()

        #check that MS00's element tree was deleted but MS01's element tree still exists
        self.assertEqual(False, self.element_tree_exists('DP00', tree_list), 'the element tree for DP01 was not deleted')
        self.assertEqual(False, self.element_tree_exists('BA00', tree_list), 'the element tree for BA00 was not deleted')
        self.assertEqual(True, self.element_tree_exists('BA01', tree_list), 'the element tree for BA01 was deleted')

    #test the add_new_hier_property function when the user adds an instance of an unshared hierarchical property to the current element tree
    def test_add_new_hier_property_1(self):

        my_model = model.model()

        #uploads existing element trees from the given path and sets the _DSD as the current tree
        path = os.path.join(TestModel.TEST_FOLDER_2_PATH, '_DSD.xml')
        tree = et.parse(path)
        my_model.set_project_path(TestModel.TEST_FOLDER_2_PATH)
        my_model.add_element_trees(tree, '_DSD', '1')

        my_model.set_template_path(TestModel.TEST_TEMPLATE_PATH)
        my_model.set_curr_tree('_DSD')

        #calls the add_hier_property function on the element tree
        my_model.add_new_hier_property(['new-property', 'String', '0', 'description', '0', 'DP', 'DP04', 'DP0.xml', None, None])
        tree = my_model.get_curr_tree()
        tree_list = my_model.get_tree_list()

        #check that DP04's element tree was created
        self.assertEqual(True, self.element_tree_exists('DP04', tree_list), 'the element tree for DP04 was not created')
    
    #test the add_new_hier_property function when the user adds an instance of a shared hierarchical property to the current element tree
    def test_add_new_hier_property_2(self):

        my_model = model.model()

        #uploads existing element trees from the given path and sets the _DSD as the current tree
        path = os.path.join(TestModel.TEST_FOLDER_2_PATH, '_DSD.xml')
        tree = et.parse(path)
        my_model.set_project_path(TestModel.TEST_FOLDER_2_PATH)
        my_model.add_element_trees(tree, '_DSD', '1')

        my_model.set_template_path(TestModel.TEST_TEMPLATE_PATH)
        my_model.set_curr_tree('_DSD')

        #calls the add_hier_property function on the element tree
        my_model.add_new_hier_property(['new-property', 'String', '0', 'description', '0', 'DP', 'DP01', 'DP0.xml', None, None])
        tree = my_model.get_curr_tree()
        tree_list = my_model.get_tree_list()

        for tree in tree_list:
            #checks that DP01 now has two parents (both _DSD)
            if tree.find('Name').text == 'DP01':
                parents = []
                for p in tree.find('Header').find('Parents').iter('Parent'):
                    parents.append(p.text)
                self.assertEqual(parents, ['_DSD', '_DSD'], 'DP01 does not have two parent tags')

    #test the add_new_hier_property function when tool needs to add a hierarchical property to an existing property's hierarchicalProperties tag
    def test_add_new_hier_property_3(self):

        my_model = model.model()

        #uploads existing element trees from the given path and sets the _DSD as the current tree
        path = os.path.join(TestModel.TEST_FOLDER_2_PATH, '_DSD.xml')
        tree = et.parse(path)
        my_model.set_project_path(TestModel.TEST_FOLDER_2_PATH)
        my_model.add_element_trees(tree, '_DSD', '1')

        my_model.set_template_path(TestModel.TEST_TEMPLATE_PATH)
        my_model.set_curr_tree('_DSD')

        #calls the add_hier_property function on the element tree
        my_model.add_new_hier_property(['new-property', 'String', '0', 'description', '0', 'MS', 'MS02', 'Master.xml', 'mipi-sdw-master-count', 'SDW_Master'])
        tree = my_model.get_curr_tree()
        tree_list = my_model.get_tree_list()

        #check that MS02's element tree was created
        self.assertEqual(True, self.element_tree_exists('MS02', tree_list), 'the element tree for MS02 was not created')
        
        #found variable will be True if MS02 was added as a hierarchical property to the right tag in the current element tree (this should be True)
        found = False
        for prop in tree.getroot().find('Properties').iter('Property'):
            if prop.find('Name').text == 'mipi-sdw-master-count':
                for hier_prop in prop.find('DependentPackages').find('Package').find('HierarchicalProperties').iter('HierarchicalProperty'):
                    if hier_prop.find('Value').text == 'MS02':
                        found = True

        self.assertEqual(True, found, 'the correct hierarchical property was not added to _DSD')

    #test the add_property function when the user adds a normal property to the current element tree
    def test_add_property(self):
        my_model = model.model()

        #creates element tree based off of testFile1 xml file and adds it as the current element tree
        tree = et.parse(TestModel.TEST_FILE_1_PATH)
        my_model.add_element_tree(tree, '_DSD', 1)
        my_model.set_template_path(TestModel.TEST_TEMPLATE_PATH)
        my_model.set_curr_tree('_DSD')

        #calls the add_property function on the element tree
        my_model.add_property(['new-property', 'Boolean', '0', 'description', '0', '0',])
        tree = my_model.get_curr_tree()
        
        #found variable will be True if the new property exists in the current element tree (this should be True)
        found = False
        for prop in tree.getroot().find('Properties').iter('Property'):
            if prop.find('Name').text == 'new-property':
                found = True
        
        self.assertEqual(True, found, 'property was not added to _DSD')

    #helper function for model unit test that returns True if the given element tree exists in the current list of element trees and False otherwise
    def element_tree_exists(self, name, tree_list):
        found = False
        for tree in tree_list:
            if tree.getroot().find('Name').text == name:
                found = True
        return found

if __name__ == '__main__':
    log_file = 'log_file.txt'
    with open(log_file, "w") as f:
       runner = unittest.TextTestRunner(f, verbosity = 2)
       unittest.main(testRunner=runner)
