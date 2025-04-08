#  ------------------------------------------------------------------------------
#
#  Copyright 2021, MIPI Alliance and its contributors.
#  SPDX-License-Identifier: BSD-3-Clause
#
#  Module Name:
#
#    disco_strings.py
#
#  Abstract:
#
#    disco UI strings  for localization.
#
#  -------------------------------------------------------------------------------

DISCO_STR_INFO_INSTANCE = "Another instance of the  Disco Tool  is currently running. Click OK to use that instance. "

DISCO_STR_GENERAL_INFOSTR = "Information "

DISCO_STR_TITLE = u"DisCo Creation Tool"

DISCO_STR_CLOSE_MSG = 'There are some unsaved changes. Would you like to save these before closing the application?'

DISCO_STR_GRIDPROP_MSG = '''
is different than your previous value for this property.
If you continue, some hierarchical properties and their data may be automatically deleted.
Do you want to continue?
'''

DISCO_STR_GRIDCELL_DUPLICATE_MSG = 'Circular reference found. One of the parent packages has the same name.'

DISCO_STR_GRIDCELL_REUSE_MSG = '''
is an existing package. Do you want to re-use existing package or cancel renaming the current package?
'''

DISCO_STR_GRIDCELL_OLD_SHARED_MSG = '''
  had several parent packages. If you continue,
  new data associated with this property will no longer affect other instances of the previous package.
  Would you like to continue?
'''

DISCO_STR_GRIDCELL_MAXCHAR_MSG = '''
 is over 4 characters. Please choose a name that is less than or equal to 4 characters.
 '''

DISCO_STR_PKG_REUSE_MSG = ' is an existing package. Do you want to re-use existing package?'
