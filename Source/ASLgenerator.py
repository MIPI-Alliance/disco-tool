#  ------------------------------------------------------------------------------
#
#  Copyright (C) Microsoft Corporation. All rights reserved.
#
#  Module Name:
#
#    ASLgenerator.py
#
#  Abstract:
#
#    Main class for creating an ASL file representing the current device.
#
#  -------------------------------------------------------------------------------

import re

#This class contains all the necessary logic to generate an ASL file from the current element trees. 
class ASLgenerator():

    #initializing the ASLgenerator with the current model in order to access the model's data and functions
    def __init__(self, model):
        self.my_model = model

    #fills the device asl file with all of the correct properties/hierarchical properties and packages
    def generate_asl(self, start_package_name, device_name, hid_value, cid_value, adr_value, file_path):

        #hierarchical list keeps track of the hierarchical properties in the current element tree
        trees = self.my_model.get_tree_list()
        self.curr_tree = None
        hierarchical_list = []

        #finds element tree corresponding to the start package name
        for tree in trees:
            if tree.getroot().find('Name').text == start_package_name:
                self.curr_tree = tree

        #if starting package name is _DSD (if this is the start of the asl file), create the asl file (named with the device name) and then add the 
        # device name and hid/cid/adr to that file 
        if start_package_name == '_DSD':
            print('creating file: ' + file_path)

            open(file_path, 'w').close()
            self.asl_file = open(file_path, 'a+')

            # open(device_name + '.asl', 'w').close()
            # self.asl_file = open(device_name + '.asl', 'a+')

            self.asl_file.write('Device('+device_name+') {\n')

            if hid_value != "":
                self.asl_file.write('   Name(_HID, "'+hid_value+'")\n')
                
                if cid_value != "":
                    self.asl_file.write('   Name(_CID, "'+cid_value+'")\n')
                self.asl_file.write('\n')
            if adr_value != "":
                self.asl_file.write('   Name(_ADR, '+adr_value+')\n\n')

            #master hierarchical list keeps track of the hierarchical properties from all of the element trees added to the asl file so far
            self.master_hierarchical_list = []

        #all normal properties are added to the current package section in the file and any hierarchical properties
        #found are stored in the hierarchical list
        self.asl_file.write('   Name('+start_package_name+', Package() {\n')
        
        counter = 0
        props_tag = self.curr_tree.find('Properties')
        for prop in props_tag.iter('Property'):

            name = prop.find('Name').text
            val = prop.find('Value').text
            dtype = prop.find('DataType').text

            #if user does not enter a value for a property, it is not included in the ASL file
            if val != None:
                if counter == 0:
                    self.asl_file.write('        ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),\n        Package () {\n')
                counter += 1

                #uses a regular expression to parse a value if it is of type package (user will write that as numbers each with a comma and a space in between)
                if dtype == 'Package':
                    x = re.findall('([0-9a-zA-Z]*)', val)
                    new_val = ""
                    counter = 0
                    entries = []
                    for entry in x:
                        if entry != "":
                            entries.append(entry)
                    for entry in entries:
                        if entry != "":
                            if counter == len(entries)-1:
                                new_val += entry
                            else:
                                new_val += entry+", "
                        counter += 1
                    self.asl_file.write('           Package (2) {"'+name+'",\n            Package() {'+new_val+'} },\n')
                
                #uses values "One" and "Zero" for properties of type boolean
                elif dtype == 'Boolean':
                    if val == '0':
                        val = 'Zero'
                    else:
                        val = 'One'
                    self.asl_file.write('           Package (2) {"'+name+'", '+val+"},\n")
                
                #converts bitmap to hex when displayed in the ASL
                elif dtype == 'BitMap':
                    val = hex(int(val, 2))
                    self.asl_file.write('           Package (2) {"'+name+'", '+val+"},\n")
                
                elif dtype == 'Integer':
                    self.asl_file.write('           Package (2) {"'+name+'", '+val.lower()+"},\n")

                #writes value normally if it is not of type package or boolean 
                else:
                    self.asl_file.write('           Package (2) {"'+name+'", '+val+"},\n")

                #hierarchical properties are added to hierarchical list as tuples (with the name and the value for each)
                packs = prop.find('DependentPackages')
                for pack in packs.iter('Package'):
                    hier_props = pack.find('HierarchicalProperties')
                    for hier_prop in hier_props.iter('HierarchicalProperty'):
                        hierarchical_list.append((hier_prop.find('Name').text, hier_prop.find('Value').text))

        #hierarchical properties at the bottom of the xml file are added to hierarchical list as tuples (with the name and the value for each)
        packs_tag = self.curr_tree.find('HierarchicalProperties')
        for prop in packs_tag.iter('HierarchicalProperty'):
            hierarchical_list.append((prop.find('Name').text, prop.find('Value').text))

        #gets rid of any hierarchical properties that the user did not input a value for - CHECK THE REQUIRED TAG TO SEE IF THIS IS OK
        new_hierarchical_list = []
        for hier_prop in hierarchical_list:
            if hier_prop[1] is not None:
                new_hierarchical_list.append((hier_prop[0], hier_prop[1]))

        #if there are hierarchical properties in the current etree, they are added to the current package section in the asl file
        if len(new_hierarchical_list) > 0:

            if counter > 0:
                self.asl_file.write('        },\n')

            self.asl_file.write('        ToUUID("dbb8e3e6-5886-4ba6-8795-1319f52a966b"),\n        Package () {\n')

            for hier_prop in new_hierarchical_list:
                self.asl_file.write('           Package (2) {"'+ hier_prop[0] +'", "'+ hier_prop[1] +'"},\n')
        
            self.asl_file.write('        }\n')
        else: 
            if counter > 0:
                self.asl_file.write('        }\n')

        self.asl_file.write('   }) //End ' + device_name + '.' + start_package_name + '\n\n')

        #this method is recursively called on any hierarchical properties in order to add those packages to the asl file
        for hier_prop in new_hierarchical_list:

            #if a hierarchical property from this tree doesn't exist in master_hierarchical_list, add it there and then generate the asl-
            #this is to prevent shared packages from being included more than once in the asl file
            if hier_prop[1] not in self.master_hierarchical_list:
                self.master_hierarchical_list.append(hier_prop[1])
                self.generate_asl(hier_prop[1], device_name, None, None, None, None)

        #ends the asl file once all hierarchical properties have been recursively added
        if start_package_name == '_DSD':
            self.asl_file.write('}')
            self.asl_file.close()
