#  ------------------------------------------------------------------------------
#
#  Copyright 2021, MIPI Alliance and its contributors.
#  SPDX-License-Identifier: BSD-3-Clause
#
#  Module Name:
#
#    model.py
#
#  Abstract:
#
#    Main class for creating, deleting and modifying information about the current device.
#
#  -------------------------------------------------------------------------------

import xml.etree.ElementTree as et
import copy
import os
import random
import string
import numpy as np

#This class manages the app's data. It stores all of the xml files for the current device as ElementTree objects. It
#defines all of the methods to update these ElementTrees as the user interacts with the GUI. 
class model():

    #initializes model with no current element trees, no project path (which represents the path to the folder where all of the project files
    # are stored), and no template path (which represents the path to the folder where all of the generic templates are stored)
    def __init__(self):
        self.curr_tree = None
        self.project_path = None
        self.template_path = None
        self.tree_list = []
        self.property_dictionary = {}
        self.packageName_list = np.array([])
        
    #sets the current template path variable 
    def set_template_path(self, path):
        #Print statement for debugging purposes:
        print("setting template path to: " + str(path))
        self.template_path = path

        #goes through current list of element trees and if _DSD does not yet have a value in its TemplatePath tag, set it now
        for tree in self.tree_list:
            if tree.getroot().find('Name').text == '_DSD':
                if tree.getroot().find('Header').find('TemplatePath').text == None:
                    tree.getroot().find('Header').find('TemplatePath').text = path

    #sets the current project path variable - this variable keeps track of the path to where the current project files are being stored
    def set_project_path(self, path):
        print("setting project path to: " + str(path))
        self.project_path = path
    
    #returns current template path variable
    def get_template_path(self):
        return self.template_path

    #returns current project path variable
    def get_project_path(self):
        return self.project_path

    #sets current element tree variable based on the name passed in (what user chose in hierarchical list of packages)
    def set_curr_tree(self, name):
        for tree in self.tree_list:
            root = tree.getroot()
            if root.find('Name').text == name:
                self.curr_tree = tree

    #gets the property_dictionary array 
    def get_propertyDictionary(self):
        print("Getting the property dictionary: ", self.property_dictionary)

        return self.property_dictionary

    #sets the property_dictionary array 
    def set_propertyDictionary(self, dictionary):
        self.property_dictionary = dictionary

        for template_name, template_dict in dictionary.items():
            for properties_name, properties_dict in template_dict.items():
                # integer keys are read from json as strings, convert them back to int
                dictionary[template_name][properties_name] = {int(key): value for key, value in properties_dict.items()}

        print("Settings the property dictionary: ", self.property_dictionary)

    #gets the packageName_list array 
    def get_packageNameList(self):
        print("Getting the package Name List: ", self.packageName_list)

        return self.packageName_list

    #sets the packageName_list array 
    def set_packageNameList(self, list):
        self.packageName_list = list
    
        print("Setting the package Name List: ", self.packageName_list)

    #gets current element tree variable
    def get_curr_tree(self):
        return self.curr_tree

    #gets list of element trees defined for the current device
    def get_tree_list(self):
        return self.tree_list

    #prints current tree list for debugging purposes
    def print_tree_list(self):
        for tree in self.tree_list:
            print(tree.getroot().find('Name').text + " -> ")
        print("\n")

    #updates the name of a given tree - used for when user adds a new hierarchical property or changes a hierarchical
    #property's name
    def update_template_name(self, tree, name):
        root = tree.getroot()
        root.find('Name').text = name

    #updates all of the current trees to have the new version # (used when user "saves as")
    def update_version_num(self, message):
        for tree in self.tree_list:
            root = tree.getroot()
            root.find('Header').find('Version').text = message
    
    #updates the value for a specific property when user inputs this
    def update_property_value(self, message):

        #extracts the values for the property name, new property value, and old property value
        name = message[0]
        value = message[1]
        old_value = message[2]
        
        #finds the property in the current tree that is the one the user just updated
        root = self.curr_tree.getroot()
        propsTag = root.find('Properties')
        for prop in propsTag.iter('Property'):
            if prop.find('Name').text == name:

                #adjusts this property's value to be what the user just inputted
                prop.find('Value').text = value

                #iterates through each dependent package associated with the current property
                for package in prop.find('DependentPackages').findall('Package'):
                    pack_name = package.find('Name').text

                    #call helper method to get a list of hierarchical properties to be deleted and hierarchical properties to be added (properties
                    # are specified by their number identifier)
                    interpret_value = package.find('InterpretValue').text
                    hier_props_lists = self.create_hier_props_lists(interpret_value, old_value, value)
                    to_add = hier_props_lists[0]
                    to_delete = hier_props_lists[1]

                    #create the dictionary for the current property if it doesn't already exist (to keep track of its dependent package names)
                    if root.find('Name').text not in self.property_dictionary:
                        self.property_dictionary[root.find('Name').text] = {}

                    curr_property_dictionary = self.property_dictionary[root.find('Name').text]

                    if name not in curr_property_dictionary:
                        curr_property_dictionary[name] = {};

                    #delete appropriate hierarchical properties
                    for num in to_delete:
                        
                        converted_num = num
                        if interpret_value == 'Package':
                            if num[:2]=="0x":
                                converted_num = num[2:]
                                converted_num = int(converted_num, 16)

                        #before calling delete_hier_property, we should update the curr_property_dictionary to get rid of this value
                        package_name = curr_property_dictionary[name][num][1]
                        property_name = curr_property_dictionary[name][num][0]
                        del curr_property_dictionary[name][num]

                        #delete the hierarchical property
                        self.delete_hier_property([property_name, name, pack_name, self.curr_tree])

                    #add appropriate hierarchical properties
                    for num in to_add:
                        converted_num = num
                        if interpret_value == 'Package':
                            if num[:2]=="0x":
                                converted_num = num[2:]
                                converted_num = int(converted_num, 16)

                        property_name_prefix = package.find('PropertyNamePrefix').text if package.find('PropertyNamePrefix') is not None else f"{name}-"
                        property_name_postfix = package.find('PropertyNamePostfix').text if package.find('PropertyNamePostfix') is not None else ""

                        #call helper function that creates the package name
                        package_name = self.create_package_name(package, int(converted_num))
                        if package.find('PackageNameDataType').text=="Hex":
                            converted_num = hex(int(converted_num))
                            prefix0x = property_name_prefix.split("-")[-1]
                            if prefix0x=="0x" or "0X":
                                pkg_value_name = (str(converted_num))[2:]
                        else:
                            converted_num = int(converted_num)
                            prefix0x = property_name_prefix.split("-")[-1]
                            pkg_value_name = str(converted_num)

                        property_name = property_name_prefix + pkg_value_name.upper()  + property_name_postfix
                        property_data_type = 'String'
                        property_required = ''
                        property_description = ''
                        property_modify = ''
                        property_prefix = package.find('PackageNamePrefix').text
                        property_value = package_name
                        property_file = package.find('Filename').text
                        message = [property_name, property_data_type, property_required, property_description, property_modify, property_prefix, property_value, property_file, name, pack_name]
                        self.add_new_hier_property(message)

                        #update the curr_property_dictionary to keep track of the hierarchical properties
                        curr_property_dictionary[name][num] = (property_name, package_name);
    
    #when a hierarchical property is automatically created, this function will be called to define the package name based on the dependent package 
    #and the value the user defined for this specific property
    def create_package_name(self, package, num):
        #get the packageNamePrefix from the package (this prefix can be 1, 2, or 3 characters long)
        prefix = package.find('PackageNamePrefix').text
        prefix_length = len(prefix)
        name = None
        num_zeros = 1
        count = 0

        disableAuto = package.find('DisableAutoNameGeneration').text
        if disableAuto == "1":
            name = "EnterEntityPackageName"
            return name

        #figure out the number of digits in num
        if num == 0:
            count += 1

        temp_num = num 
        while (temp_num > 0):
            temp_num = temp_num//10
            count = count + 1

        #if value is 4 or more digits, then just use four random letters as the package name
        if count > 3:
            name = random.choice(string.ascii_letters) + random.choice(string.ascii_letters) + random.choice(string.ascii_letters) + random.choice(string.ascii_letters)
            return name

        #the package name should always be 4 characters, so it is defined differently based on how long the packageNamePrefix is
        if prefix_length == 1:
            num_zeros = 3 - count
            name = prefix 
            while (num_zeros > 0):
                name += str(0)
                num_zeros -= 1
            
            #define the name as the prefix, a fixed number of 0's, and the value
            name += str(num)

            #if this name already exists, try calling this function again with a larger value
            if name in self.packageName_list:
                return self.create_package_name(package, num+1)

        elif prefix_length == 2:
            #if the value is more than 2 digits, then just use four random letters as the package name
            if count > 2:
                name = random.choice(string.ascii_letters) + random.choice(string.ascii_letters) + random.choice(string.ascii_letters) + random.choice(string.ascii_letters)
                return name

            num_zeros = 2 - count
            name = prefix 
            while (num_zeros > 0):
                name += str(0)
                num_zeros -= 1
            
            #define the name as the prefix, a fixed number of 0's, and the value
            name += str(num)

            #if this name already exists, try calling this function again with a larger value
            if name in self.packageName_list:
                return self.create_package_name(package, num+1)

        else: 
            #if the value is more than 1 digit, then just use four random letters as the package name
            if count > 1:
                name = random.choice(string.ascii_letters) + random.choice(string.ascii_letters) + random.choice(string.ascii_letters) + random.choice(string.ascii_letters)
                return name

            num_zeros = 1 - count
            name = prefix 
            while (num_zeros > 0):
                name += str(0)
                num_zeros -= 1
            
            #define the name as the prefix, a fixed number of 0's, and the value
            name += str(num)

            #if this name already exists, try calling this function again with a larger value
            if name in self.packageName_list:
                return self.create_package_name(package, num+1)
       
        #if the name already exists or if the name is more than 4 characters, just assign 4 random letters to be the name
        if (name in self.packageName_list) or (len(name) > 4):
            name = random.choice(string.ascii_letters) + random.choice(string.ascii_letters) + random.choice(string.ascii_letters) + random.choice(string.ascii_letters)
        
        return name
    
    #when the user updates a property value and that property has correspondning dependent packages, this method is called for each package
    #to find out what hierarchical properties need to be added and deleted (this information is given in the form of a list of integers).
    def create_hier_props_lists(self, interpret_value, old_value, value):
        #method returns a tuple with a list of hierarchical properties to add and a list of hierarchical properties to delete (each property
        # is just defined by their integer value that follows the shared hierarchical property prefix)
        to_add = []
        to_delete = []

        #the to_add and to_delete lists are filled differently depending on the dependent package's interpret value (integer, package, or bitmap)
        if interpret_value == 'Integer':

            #converting new and old values to be integers
            if old_value == "":
                old_value = 0
            elif old_value[:2] == '0x':
                old_value = int(old_value, 16)
            if value == "":
                value = 0
            elif value[:2] == '0x':
                value = int(value, 16)

            old_value = int(old_value)            
            value = int(value)               

            #populates the to_add and to_delete lists accordingly
            if old_value == 0:
                to_add = list(range(1, value + 1))
            elif value > old_value:
                to_add = list(range(old_value + 1, value + 1))
            else:
                to_delete = list(range(value + 1, old_value + 1))

        if interpret_value == 'Package':

            #converting new and old values to be lists of numbers
            if old_value == "":
                old_value = []
            else: 
                old_value = old_value.split(", ")

            if value == "":
                value = []
            else: 
                value = value.split(", ")

            for val in value: 
                if val not in old_value: 
                    to_add.append(val)
            for val in old_value:
                if val not in value:
                    to_delete.append(val)

        if interpret_value == 'BitMap':

            #BitMap can be entered as a binary value or as a hexadecimal value, if it is hexadecimal then convert it to binary so that we can determine 
            #what bits are set in the new value
            if value[:2]=="0b":
                value = value[2:]
            elif value[:2]=="0x":
                value = value[2:]
                value = bin(int(value, 16))[2:]

            if old_value[:2]=="0b":
                old_value = old_value[2:]
            elif old_value[:2]=="0x":
                old_value = old_value[2:]
                old_value = bin(int(old_value, 16))[2:]

            #finding the length of the old and new values and creating a local variable for the new value
            old_len = len(old_value)
            new_len = len(value)
            new_value = value

            #finds the difference in characters between the new and old value 
            if (old_len < new_len):
                old_delta = new_len - old_len
                new_delta = 0
            else:
                new_delta = old_len - new_len
                old_delta = 0

            #concatenates zeros to the old value if it is shorter than the new value (so they are the same length)
            old_value += old_delta * '0'

            #concatenates zeros to the new value if it is shorter than the old value (so they are the same length)
            new_value += new_delta * '0'

            # create a list of tuples to compare the (old, new) bits
            # i.e. (0, 1) means a bit was added, (1, 0) means the bit was removed, and (1, 1) or (0, 0) is no change
            compare_zip = list(zip(old_value, new_value))

            # the "len(compare_zip) - index - 1" converts index, which is left->right, to bit ordering index, which is left<-right
            # e.g. given 0010, the index of '1' would be 2, but the bit ordered index would be 1
            to_add = [len(compare_zip) - index - 1 for index, (old, new) in enumerate(compare_zip) if int(new) and not int(old)]
            to_delete = [len(compare_zip) - index - 1 for index, (old, new) in enumerate(compare_zip) if int(old) and not int(new)]

            # Sort so that the items are added from LSB to MSB
            to_add.sort()

        return (to_add, to_delete)
    
    #updates the name for a specific property when user changes the corresponding grid cell in the View
    def update_property_name(self, message):
        name = message[0]
        old_name = message[1]
        found = False
        value = None
        root = self.curr_tree.getroot()

        #finds the correct property in the current tree and updates its value
        for prop in root.find('Properties').iter('Property'):
            if prop.find('Name').text == old_name:
                prop.find('Name').text = name

        curr_property_dictionary = self.property_dictionary[root.find('Name').text]

        for prop_name in curr_property_dictionary.keys():
            if prop_name == old_name:
                value = curr_property_dictionary[prop_name]
                found = True

        if found == True:
            curr_property_dictionary.pop(old_name)
            curr_property_dictionary[name] = value

    #updates the value for a specific buffer property when user updates it
    def update_buff_val(self, message):
        value = message[0]
        name = message[1]

        #finds the property in the current tree that is the one the user just updated
        root = self.curr_tree.getroot()
        propsTag = root.find('Properties')

        for prop in propsTag.iter('Property'):
            if prop.find('Name').text == name:

                #adjusts this property's value to be what the user just inputted
                prop.find('Value').text = value

    #updates the name for a specific buffer property when user changes the corresponding grid cell in the View
    def update_buff_property_name(self, message):
        name = message[0]
        old_name = message[1]
        found = False
        value = None

        #finds the correct property in the current tree and updates its value
        for prop in self.curr_tree.getroot().find('BufferProperties').iter('BufferProperty'):
            if prop.find('PropertyName').text == old_name:
                prop.find('PropertyName').text = name

        curr_property_dictionary = self.property_dictionary[root.find('Name').text]

        for prop_name in curr_property_dictionary.keys():
            if prop_name == old_name:
                value = curr_property_dictionary[prop_name]
                found = True

        if found == True:
            curr_property_dictionary.pop(old_name)
            curr_property_dictionary[name] = value

    #updates the value for a specific buffer property when user changes the corresponding grid cell in the View
    def update_buff_property_value(self, message):
        #if new value already belongs to an existing element tree: add the curr_tree as parent of that one and change the correct value in the 
        #curr_tree 
        #       if old element tree exists but was not shared: delete it
        #       if old element tree exists and was shared: delete appropriate parent tag
        #       if old element tree doesnt exist: do nothing else
        #if new value does not already exist: change the correct val in curr_tree
        #       if old element tree existed and was not shared: just change its name to new
        #       if old element tree exists and was shared: delete appropriate parent tag and copy old element tree and use that as base for new one
        #       if old element tree doesnt exist: create a whole new element tree

        #collects the buffer property name, the new property value, the previous property value, and the current tree name
        name = message[0]
        buffer_name = message[1]
        old_value = message[2]
        curr_tree_name = self.curr_tree.getroot().find("Name").text
        version_number = self.curr_tree.getroot().find('Header').find('Version').text

        #initializes variables to starting values
        file_name = ""
        self.found_old = False
        self.old_shared = False
        self.found_new = False
        self.old_tree = None
        self.new_tree = None

        #iterates through the current element tree list and sets found_old to true if previous value had an associated element tree (old_tree)-
        #old_shared is also set to true if this element tree was shared (had several parents).
        #also sets found_new to true if new value already has an associated element tree(new_tree).
        for tree in self.tree_list:
            if tree.getroot().find('Name').text == old_value:
                self.found_old = True
                self.old_tree = tree

                counter = 0
                for parent in tree.getroot().find('Header').find('Parents').iter('Parent'):
                    counter += 1

                if counter > 1:
                    self.old_shared = True

            if tree.getroot().find('Name').text == buffer_name:
                self.found_new = True
                self.new_tree = tree

        #changes the value of the buffer property in the current element tree to the new value
        buffProp_found = False
        root = self.curr_tree.getroot()
        buffPropsTag = root.find('BufferProperties')
        for prop in buffPropsTag.iter('BufferProperty'):
            if prop.find('PropertyName').text == name:
                buffProp_found = True
                prop.find('BufferName').text = buffer_name
                file_name = prop.find('Filename').text

        #if new value already has an associated element tree, the current element tree is added as a parent to this one
        if self.found_new == True:
            self.add_parent(self.new_tree, curr_tree_name)

            #if old value also was shared (had several parents), the current element tree is removed as a parent to that one.
            #if old value was not shared (current tree was its only parent), that tree and its children are deleted
            if self.found_old == True:
                if self.old_shared == True:
                    parents = self.old_tree.getroot().find('Header').find('Parents')
                    for p in parents:
                        if p.text == curr_tree_name:
                            parents.remove(p)
                else:
                    self.delete_tree(self.old_tree)
        else: 
            if self.found_old == True:

                #if new value does not already have an associated element tree and previous tree existed but was not shared, the previous
                #tree's name is simply changed to the new value
                if self.old_shared == False:
                    self.update_template_name(self.old_tree, buffer_name)
                
                #if new value does not already have an associated element tree and previous tree existed and was shared, a copy of the previous
                #tree is made to be the new tree (with adjusted template name and parent list) and curr_tree is removed as a parent from the previous
                #tree
                else:

                    #TODO: currently, the "copy" of the previous element tree is created by converting the old_tree to a string and then 
                    #convering that back to an element tree - used this hack becuase copy.deepcopy() was returning new_tree as None.
                    temp_string = et.tostring(self.old_tree.getroot()).decode()
                    new_root = et.fromstring(temp_string)
                    new_tree = et.ElementTree(element = new_root)

                    #Print statements for debugging purposes:
                    print("old tree\n")
                    print(self.old_tree)
                    print("\n new tree\n")
                    print(new_tree)

                    #variables for the parent tags of the new element tree and the old element tree
                    new_parents = new_tree.getroot().find('Header').find('Parents')
                    old_parents = self.old_tree.getroot().find('Header').find('Parents')

                    #new element tree's parent list is adjusted so that it only contains the current element tree
                    new_tree.getroot().find('Header').remove(new_parents)
                    et.SubElement(new_tree.getroot().find('Header'), 'Parents')
                    new_child = et.SubElement(new_tree.getroot().find('Header').find('Parents'), 'Parent')
                    new_child.text = curr_tree_name

                    #removes the current element tree from the old element tree's parent list
                    for p in old_parents:
                        if p.text == curr_tree_name:
                            old_parents.remove(p)

                    #adds the new element tree to the element tree list
                    self.add_element_tree(new_tree, buffer_name, version_number)

            #if new value does not already have an associated element tree and there was no previous element tree, a new element
            #tree is created based on associated filename (from the template) with the current tree as a parent
            else:
                path = os.path.join(self.template_path, file_name)
                print("new tree path is " + path)
                new_tree = et.parse(path)
                #new_tree = et.parse(self.template_path + file_name)
                self.add_parent(new_tree, curr_tree_name)
                self.add_element_tree(new_tree, buffer_name, self.curr_tree.getroot().find('Header').find('Version').text)
    
    #updates the name for a specific hierarchical property when user changes the corresponding grid cell in the View
    def update_hier_property_name(self, message):
        name = message[0]
        old_name = message[1]
        root = self.curr_tree.getroot()

        #changes the name of the hierarchical property in the current element tree to the new name
        hierProp_found = False
        for prop in root.find('HierarchicalProperties').iter('HierarchicalProperty'):
            if prop.find('Name').text == old_name:
                prop.find('Name').text = name
                hierProp_found = True

        #if the hierarchical property is not found in the HierarchicalProperties section, then search for it
        #in the DependentPackages section of the Properties.
        property_name = None

        if hierProp_found == False:
            for prop in root.find('Properties').iter('Property'):
                if prop.find('DependentPackages').iter('Package') != None:
                    for pack in prop.find('DependentPackages').iter('Package'):
                        if pack.find('HierarchicalProperties').iter('HierarchicalProperty') != None:
                            for hier_prop in pack.find('HierarchicalProperties').iter('HierarchicalProperty'):
                                if hier_prop.find('Name').text == old_name:
                                   hier_prop.find('Name').text = name

                                   property_name = prop.find('Name').text
                                   hier_prop_value = hier_prop.find('Value').text

                                   curr_property_dictionary = self.property_dictionary[root.find('Name').text]

                                   #update the property_dictionary to keep track of the hierarchical properties
                                   name_dictionary = curr_property_dictionary[property_name]
                                   for num_value in name_dictionary.keys():
                                       if curr_property_dictionary[property_name][num_value] == (old_name, hier_prop_value):
                                           curr_property_dictionary[property_name][num_value] = (name, hier_prop_value)

    #helper function for numpy arrays that deletes the first instance of value in the array
    def delete_array_value(self, array, value):
        index = 0
        for val in array:
            if val == value:
                self.packageName_list = np.delete(array, index)
                break
            index += 1

    #updates the value for a specific hierarchical property when user changes the corresponding grid cell in the View
    def update_hier_property_value(self, message):
        #if new value already belongs to an existing element tree: add the curr_tree as parent of that one and change the correct value in the 
        #curr_tree 
        #       if old element tree exists but was not shared: delete it
        #       if old element tree exists and was shared: delete appropriate parent tag
        #       if old element tree doesnt exist: do nothing else
        #if new value does not already exist: change the correct val in curr_tree
        #       if old element tree existed and was not shared: just change its name to new
        #       if old element tree exists and was shared: delete appropriate parent tag and copy old element tree and use that as base for new one
        #       if old element tree doesnt exist: create a whole new element tree

        #collects the hierarchical property name, the new property value, the previous property value, and the current tree name
        name = message[0]
        instance_name = message[1]
        old_value = message[2]
        curr_tree_name = self.curr_tree.getroot().find("Name").text
        version_number = self.curr_tree.getroot().find('Header').find('Version').text

        #initializes variables to starting values
        file_name = ""
        self.found_old = False
        self.old_shared = False
        self.found_new = False
        self.old_tree = None
        self.new_tree = None

        #iterates through the current element tree list and sets found_old to true if previous value had an associated element tree (old_tree)-
        #old_shared is also set to true if this element tree was shared (had several parents).
        #also sets found_new to true if new value already has an associated element tree(new_tree).
        for tree in self.tree_list:
            if tree.getroot().find('Name').text == old_value:
                self.found_old = True
                self.old_tree = tree

                counter = 0
                for parent in tree.getroot().find('Header').find('Parents').iter('Parent'):
                    counter += 1

                if counter > 1:
                    self.old_shared = True

            if tree.getroot().find('Name').text == instance_name:
                self.found_new = True
                self.new_tree = tree

        #changes the value of the hierarchical property in the current element tree to the new value
        hierProp_found = False
        root = self.curr_tree.getroot()
        hierPropsTag = root.find('HierarchicalProperties')
        for prop in hierPropsTag.iter('HierarchicalProperty'):
            if prop.find('Name').text == name:
                hierProp_found = True
                prop.find('Value').text = instance_name
                file_name = prop.find('Filename').text

        #if the hierarchical property is not found in the HierarchicalProperties section, then search for it
        #in the DependentPackages section of the Properties.
        property_name = None

        if hierProp_found == False:
            for prop in self.curr_tree.getroot().find('Properties').iter('Property'):
                if prop.find('DependentPackages').iter('Package') != None:
                    for pack in prop.find('DependentPackages').iter('Package'):
                        if pack.find('HierarchicalProperties').iter('HierarchicalProperty') != None:
                            for hier_prop in pack.find('HierarchicalProperties').iter('HierarchicalProperty'):
                                if hier_prop.find('Name').text == name:
                                    property_name = prop.find('Name').text
                                    hierProp_found = True
                                    hier_prop.find('Value').text = instance_name
                                    file_name = pack.find('Filename').text

            #update the packageName_list and property_dictionary to keep track of the hierarchical properties
            curr_property_dictionary = self.property_dictionary[self.curr_tree.getroot().find('Name').text]
            name_dictionary = curr_property_dictionary[property_name]

            for num_value in name_dictionary.keys():
                print(curr_property_dictionary[property_name][num_value])
                print((name, old_value))
                if curr_property_dictionary[property_name][num_value] == (name, old_value):
                    self.delete_array_value(self.packageName_list, old_value)
                    self.packageName_list = np.append(self.packageName_list, instance_name)
                    curr_property_dictionary[property_name][num_value] = (name, instance_name)

        #if new value already has an associated element tree, the current element tree is added as a parent to this one
        if self.found_new == True:
            self.add_parent(self.new_tree, curr_tree_name)

            #if old value also was shared (had several parents), the current element tree is removed as a parent to that one.
            #if old value was not shared (current tree was its only parent), that tree and its children are deleted
            if self.found_old == True:
                if self.old_shared == True:
                    parents = self.old_tree.getroot().find('Header').find('Parents')
                    for p in parents:
                        if p.text == curr_tree_name:
                            parents.remove(p)
                else:

                    self.delete_tree(self.old_tree)
        else: 
            if self.found_old == True:

                #if new value does not already have an associated element tree and previous tree existed but was not shared, the previous
                #tree's name is simply changed to the new value
                if self.old_shared == False:
                    self.update_template_name(self.old_tree, instance_name)
                
                #if new value does not already have an associated element tree and previous tree existed and was shared, a copy of the previous
                #tree is made to be the new tree (with adjusted template name and parent list) and curr_tree is removed as a parent from the previous
                #tree
                else:

                    #TODO: currently, the "copy" of the previous element tree is created by converting the old_tree to a string and then 
                    #convering that back to an element tree - used this hack becuase copy.deepcopy() was returning new_tree as None.
                    temp_string = et.tostring(self.old_tree.getroot()).decode()
                    new_root = et.fromstring(temp_string)
                    new_tree = et.ElementTree(element = new_root)

                    #Print statements for debugging purposes:
                    print("old tree\n")
                    print(self.old_tree)
                    print("\n new tree\n")
                    print(new_tree)

                    #variables for the parent tags of the new element tree and the old element tree
                    new_parents = new_tree.getroot().find('Header').find('Parents')
                    old_parents = self.old_tree.getroot().find('Header').find('Parents')

                    #new element tree's parent list is adjusted so that it only contains the current element tree
                    new_tree.getroot().find('Header').remove(new_parents)
                    et.SubElement(new_tree.getroot().find('Header'), 'Parents')
                    new_child = et.SubElement(new_tree.getroot().find('Header').find('Parents'), 'Parent')
                    new_child.text = curr_tree_name

                    #removes the current element tree from the old element tree's parent list
                    for p in old_parents:
                        if p.text == curr_tree_name:
                            old_parents.remove(p)

                    #adds the new element tree to the element tree list
                    self.add_element_tree(new_tree, instance_name, version_number)

            #if new value does not already have an associated element tree and there was no previous element tree, a new element
            #tree is created based on associated filename (from the template) with the current tree as a parent
            else:
                path = os.path.join(self.template_path, file_name)
                print("new tree path is " + path)
                new_tree = et.parse(path)
                #new_tree = et.parse(self.template_path + file_name)
                self.add_parent(new_tree, curr_tree_name)
                self.add_element_tree(new_tree, instance_name, self.curr_tree.getroot().find('Header').find('Version').text)

    #this helper function for update_hier_property_value deletes the given tree and all of its children from the current tree_list (as long as they are not shared)
    def delete_tree(self, tree):

        #removes current tree
        self.tree_list.remove(tree)

        #Print statement for debugging purposes:
        print("removing element\n")
        self.print_tree_list()

        #removes all of the element trees for the hierarchical properties that aren't associated with another property's dependent package
        if tree.getroot().find('HierarchicalProperties').iter("HierarchicalProperty") != None:
            for prop in tree.getroot().find('HierarchicalProperties').iter("HierarchicalProperty"):
                for other_tree in self.tree_list:
                    if other_tree.getroot().find('Name').text == prop.find("Value").text:

                        #counter variable keeps track of how many parent packages the current element tree has
                        counter = 0
                        for p in other_tree.getroot().find('Header').find('Parents').iter('Parent'):
                            counter += 1

                        #if the current element tree has more than one parent, it is not removed from the tree_list and the current tree is simply removed as a parent - otherwise,
                        #the tree is removed all together
                        if counter > 1:
                            for p in other_tree.getroot().find('Header').find('Parents').iter('Parent'):
                                if p.text == tree.getroot().find('Name').text:
                                    other_tree.getroot().find('Header').find('Parents').remove(p)
                        else:
                            self.delete_tree(other_tree)

        #removes all of the element trees for the hierarchical properties that are associated with another property's dependent package
        for prop in tree.getroot().find('Properties').iter('Property'):
            if prop.find('DependentPackages').iter('Package') != None:
                for pack in prop.find('DependentPackages').iter('Package'):
                    if pack.find('HierarchicalProperties').find('HierarchicalProperty') != None:
                        for hier_prop in pack.find('HierarchicalProperties').find('HierarchicalProperty'):
                            for other_tree in self.tree_list:
                                if other_tree.getroot().find('Name').text == hier_prop.find("Value").text:

                                    #counter variable keeps track of how many parent packages the current element tree has
                                    counter = 0
                                    parents = other_tree.getroot().find('Header').find('Parents').iter('Parent')
                                    for p in parents:
                                        counter += 1

                                     #if the current element tree has more than one parent, it is not removed from the tree_list and the current tree is simply removed as a parent 
                                     # - otherwise, the tree is removed all together
                                    if counter > 1:
                                        for p in parents:
                                            if p.text == tree.getroot().find('Name').text:
                                                parents.remove(p)
                                    else:
                                        self.delete_tree(other_tree)

    #called when the initial xml file is uploaded (template renamed to _DSD and saved in the list here) OR when 
    #an instance of a new package is created (template renamed to whatever the user chose and saved in the list here).
    #the existing hierarchical properties are automatically added as element trees to the current list of trees. 
    def add_element_tree(self, etree, name, version_num):
            #Print statement for debugging purposes:
            print("before adding element\n")
            self.print_tree_list()

            root = etree.getroot()
            root.find('Name').text = name
            root.find('Header').find('Version').text = version_num
            self.tree_list.append(etree)

            #Print statement for debugging purposes:
            print("adding element\n")
            self.print_tree_list()
    
    #called when the initial xml file is uploaded - adds this new element tree to the tree_list and also adds any other existing element trees
    #if the file is already partially filled out (i.e. already has some hierarchical properties defined)
    def add_element_trees(self, etree, templateName, version):

        #updates the template path variable if an existing project was loaded
        if (templateName == '_DSD') & (etree.getroot().find('Header').find('TemplatePath').text != None):
            self.set_template_path(etree.getroot().find('Header').find('TemplatePath').text)
            print("setting template path to " + etree.getroot().find('Header').find('TemplatePath').text)

        #exists variable is True if the element tree passed in already exists in the tree_list (and False otherwise)
        exists = False
        for tree in self.tree_list:
            if tree.getroot().find('Name').text == templateName:
                exists = True
        
        #if the element tree passed in does not already exist in the tree_list, it is added to the list and this method is recursively called
        #on all of its hierarchical properties that have a value filled out
        if exists == False:
            self.add_element_tree(etree, templateName, version)

            for hier_prop in etree.getroot().iter('HierarchicalProperty'):
                if hier_prop.find('Value').text != None:
                    file_name = hier_prop.find('Value').text + ".xml"

                    path = os.path.join(self.project_path, file_name)
                    new_tree = et.parse(path)

                    self.add_element_trees(new_tree, hier_prop.find('Value').text, version)

            for buff_prop in etree.getroot().iter('BufferProperty'):
                if buff_prop.find('BufferName').text != None:
                    file_name = buff_prop.find('BufferName').text + ".xml"

                    path = os.path.join(self.project_path, file_name)
                    new_tree = et.parse(path)

                    self.add_element_trees(new_tree, buff_prop.find('BufferName').text, version)

    #called either when a tree is first created and the parent needs to be added, or when another reference to an 
    #existing tree is made and the new parent needs to be added
    def add_parent(self, tree, parent_name):
        root = tree.getroot()
        parents = root.find('Header').find('Parents')
        child = et.SubElement(parents, "Parent")
        child.text = parent_name

    #deletes a normal property from current element tree
    def delete_property(self, message):
        root = self.curr_tree.getroot()
        propsTag = root.find('Properties')

        #finds the property that the user wants to delete
        for parent in propsTag.iter('Property'):
            if parent.find('Name').text == message:

                print("entered")

                #variable for the list of hierarchical properties that need to be deleted
                to_delete = []

                #deletes any hierarchical properties that exist if the property has dependent packages
                for package in parent.find('DependentPackages').iter('Package'):
                    for hier_prop in package.find('HierarchicalProperties').iter('HierarchicalProperty'):
                        to_delete.append(hier_prop.find('Name').text)
                
                if len(to_delete) > 0:
                    curr_property_dictionary = self.property_dictionary[root.find('Name').text]

                    for prop_name in curr_property_dictionary.keys():
                        if prop_name == message:
                            curr_property_dictionary.pop(prop_name)
                            break

                for prop in to_delete:
                    self.delete_hier_property([prop, message, package.find('Name').text, self.curr_tree])

                #deletes the property from the current element tree
                parent.remove(parent.find('Name'))
                parent.remove(parent.find('DataType'))
                parent.remove(parent.find('Required'))
                parent.remove(parent.find('Description'))
                parent.remove(parent.find('OEMModify'))
                parent.remove(parent.find('Value'))
                parent.remove(parent.find('Default'))
                parent.remove(parent.find('DependentPackages'))
                propsTag.remove(parent)

    #deletes a hierarchical property from current element tree (message = property name, property location, package location, current tree)
    def delete_hier_property(self, message):
        prop_name = message[0]
        hierPropsTag = None

        #if this hierarchical property is located within a specific property, that property's name and dependent package name will be 
        #extracted here - otherwise, these values will be None
        property_location = message[1]
        package_location = message[2]
        curr_tree = message[3]

        curr_tree_name = curr_tree.getroot().find('Name').text

        #finds the hierarchical properties section where the property to delete can be found
        if (property_location == None) & (package_location == None):
            hierPropsTag = curr_tree.getroot().find('HierarchicalProperties')
        else: 
            for prop in curr_tree.getroot().find('Properties').iter('Property'):
                if prop.find('Name').text == property_location:
                    for pack in prop.find('DependentPackages').iter('Package'):
                        if pack.find('Name').text == package_location:
                            hierPropsTag = pack.find('HierarchicalProperties')

        for parent in hierPropsTag.iter('HierarchicalProperty'):

            #finds the hierarchical property to be deleted
            if parent.find('Name').text == prop_name:
                for tree in self.tree_list:

                    #finds the element tree referenced by this hierarchical property
                    if tree.getroot().find('Name').text == parent.find('Value').text:

                        print("parent value: " + parent.find('Value').text)

                        parents = tree.getroot().find('Header').find('Parents')
                        to_remove = None

                        #deletes the appropriate parent tag from the etree and checks to see if there are other 
                        # parents still
                        counter = 0
                        for p in parents:
                            if p.text == curr_tree_name:
                                to_remove = p
                                counter += 1
                            else:
                                counter += 1
                        
                        parents.remove(to_remove)
                        
                        #if there was only one parent, this etree and all of its hierarchical prop.s are deleted
                        if counter == 1:

                            #deletes the hierarchical properties found in the HierarchicalProperties tag at the end of the tree
                            for prop in tree.getroot().find('HierarchicalProperties').iter('HierarchicalProperty'):
                                self.delete_hier_property([prop.find('Name').text, None, None, tree])
                            
                            #deletes the hierarchical properties found inside of properties that have dependent packages
                            for prop in tree.getroot().find('Properties').iter('Property'):
                                for pack in prop.find('DependentPackages').iter('Package'):
                                    for hier_prop in pack.find('HierarchicalProperties').iter('HierarchicalProperty'):
                                        self.delete_hier_property([hier_prop.find('Name').text, prop.find('Name').text, pack.find('Name').text, tree])
                            
                            #removes the etree from the element tree list
                            self.tree_list.remove(tree)
                            print("removing element " + tree.getroot().find('Name').text)
                            self.print_tree_list()

                        #update the list of package names
                        self.delete_array_value(self.packageName_list, parent.find('Value').text)
                        
                        #the hierarchical property is removed from the current etree
                        parent.remove(parent.find('Name'))
                        parent.remove(parent.find('DataType'))
                        parent.remove(parent.find('Required'))
                        parent.remove(parent.find('Description'))
                        parent.remove(parent.find('OEMModify'))
                        parent.remove(parent.find('PackageNamePrefix'))
                        parent.remove(parent.find('Value'))
                        parent.remove(parent.find('Filename'))
                        hierPropsTag.remove(parent)

                        break

    #adds a new buffer property to the current element tree (and creates the corresponding element tree if it doesn't already exist)
    def add_buff_property(self, message):

        #finds the current tree name and version number
        root = self.curr_tree.getroot()
        curr_tree_name = root.find('Name').text
        version_num = root.find('Header').find('Version').text 

        parent = root.find('BufferProperties')

        child = et.SubElement(parent, "BufferProperty")

        name_ch = et.SubElement(child, "PropertyName")
        name_ch.text = message[0]

        data_ch = et.SubElement(child, "DataType")
        data_ch.text = message[1]

        req_ch = et.SubElement(child, "Required")
        req_ch.text = "1"

        desc_ch = et.SubElement(child, "Description")
        desc_ch.text = message[2]

        mod_ch = et.SubElement(child, "OEMModify")
        mod_ch.text = "0"

        prefix_ch = et.SubElement(child, "BufferName")
        prefix_ch.text = message[3]

        val_ch = et.SubElement(child, "Value")
        val_ch.text = ""

        file_ch = et.SubElement(child, "Filename")
        file_ch.text = message[4]

        #found variable starts as false and represents whether or not the new value is already related to an element tree
        self.found = False

        #if there already is an element tree for the new value, the current tree is added as a parent to that tree and found variable is 
        #set to true
        for existing_tree in self.get_tree_list():
            if existing_tree.getroot().find('Name').text == message[3]:
                self.add_parent(existing_tree, curr_tree_name)
                self.found = True

        #if found is false (there is no element tree associated with the new value), a new element tree is created with the current tree
        #as its parent and the value as its name
        if self.found == False:
            path = os.path.join(self.template_path, message[4])
            print("new tree path is " + path)
            tree = et.parse(path)

            #tree = et.parse(self.template_path + message[7])
            self.update_template_name(tree, message[3])
            self.add_parent(tree, curr_tree_name)
            self.add_element_tree(tree, message[3], version_num)

    #adds a new hierarchical property to the current element tree (and creates the corresponding element tree if it doesn't already exist)
    def add_new_hier_property(self, message):

        #if this new hierarchical property is to be added within a specific property, that property's name and dependent package name will be 
        #extracted here - otherwise, these values will be None
        property_location = message[8]
        package_location = message[9]

        #finds the current tree name and version number
        root = self.curr_tree.getroot()
        curr_tree_name = root.find('Name').text
        version_num = root.find('Header').find('Version').text 

        #if these values are None, add the new hierarchical property to the HierarchicalProperties section at the end of the element tree
        if (property_location == None) & (package_location == None):

            parent = root.find('HierarchicalProperties')

            child = et.SubElement(parent, "HierarchicalProperty")

            name_ch = et.SubElement(child, "Name")
            name_ch.text = message[0]

            data_ch = et.SubElement(child, "DataType")
            data_ch.text = message[1]

            req_ch = et.SubElement(child, "Required")
            req_ch.text = message[2]

            desc_ch = et.SubElement(child, "Description")
            desc_ch.text = message[3]

            mod_ch = et.SubElement(child, "OEMModify")
            mod_ch.text = message[4]

            prefix_ch = et.SubElement(child, "PackageNamePrefix")
            prefix_ch.text = message[5]

            val_ch = et.SubElement(child, "Value")
            val_ch.text = message[6]

            file_ch = et.SubElement(child, "Filename")
            file_ch.text = message[7]
        #if these properties are not None, add the new hierarchical property to the hierarchicalProperties section within the specified
        #dependent package within the specified property
        else:
            for prop in root.find('Properties').iter('Property'):
                if prop.find('Name').text == property_location:
                    for pack in prop.find('DependentPackages').iter('Package'):
                        if pack.find('Name').text == package_location:
                            parent = pack.find('HierarchicalProperties')

                            child = et.SubElement(parent, "HierarchicalProperty")

                            name_ch = et.SubElement(child, "Name")
                            name_ch.text = message[0]

                            data_ch = et.SubElement(child, "DataType")
                            data_ch.text = message[1]

                            req_ch = et.SubElement(child, "Required")
                            req_ch.text = message[2]

                            desc_ch = et.SubElement(child, "Description")
                            desc_ch.text = message[3]

                            mod_ch = et.SubElement(child, "OEMModify")
                            mod_ch.text = message[4]

                            prefix_ch = et.SubElement(child, "PackageNamePrefix")
                            prefix_ch.text = message[5]

                            val_ch = et.SubElement(child, "Value")
                            val_ch.text = message[6]

                            file_ch = et.SubElement(child, "Filename")
                            file_ch.text = message[7]


        #adding the new hierarchical property package name to our list of package names
        self.packageName_list = np.append(self.packageName_list, message[6]);

        #found variable starts as false and represents whether or not the new value is already related to an element tree
        self.found = False

        #if there already is an element tree for the new value, the current tree is added as a parent to that tree and found variable is 
        #set to true
        for existing_tree in self.get_tree_list():
            if existing_tree.getroot().find('Name').text == message[6]:
                self.add_parent(existing_tree, curr_tree_name)
                self.found = True

        #if found is false (there is no element tree associated with the new value), a new element tree is created with the current tree
        #as its parent and the value as its name
        if self.found == False:
            path = os.path.join(self.template_path, message[7])
            print("new tree path is " + path)
            tree = et.parse(path)

            #tree = et.parse(self.template_path + message[7])
            self.update_template_name(tree, message[6])
            self.add_parent(tree, curr_tree_name)
            self.add_element_tree(tree, message[6], version_num)
        
    #adds a new property to the current element tree
    def add_property(self, message):
        root = self.curr_tree.getroot()
        parent = root.find('Properties')
        child = et.SubElement(parent, "Property")

        name_ch = et.SubElement(child, "Name")
        name_ch.text = message[0]

        data_ch = et.SubElement(child, "DataType")
        data_ch.text = message[1]

        required_ch = et.SubElement(child, "Required")
        required_ch.text = str(message[2])

        description_ch = et.SubElement(child, "Description")
        description_ch.text = message[3]

        modify_ch = et.SubElement(child, "OEMModify")
        modify_ch.text = str(message[4])

        val_ch = et.SubElement(child, "Value")
        val_ch.text = message[5]

        default_ch = et.SubElement(child, "Default")

        packs_ch = et.SubElement(child, "DependentPackages")