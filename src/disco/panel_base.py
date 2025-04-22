import wx

try:
    import  disco.disco_constants as app_constants
except:
    import disco_constants as app_constants

class PanelBase(object):

    def __init__(self):
        self.grid = None
        self.edit_column_index = -1

    def init_grid_vars(self, grid, edit_column_index):
        self.grid = grid
        self.edit_column_index = edit_column_index
        self.grid.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    def OnKeyDown(self, event):
        keyCode = event.GetKeyCode()
        row = self.grid.GetGridCursorRow()
        col = self.grid.GetGridCursorCol()

        #TODO ENTER keystroke not handling, add appropriate event.Skip()
        #TODO also enable grid movement via arrow keys
        if keyCode == wx.WXK_TAB:
            # If TAB is pressed while focus is in the value column, move up/down to next/prev value column
            if col == self.edit_column_index:
                if event.ShiftDown() and row > 0:
                    self.grid.SetGridCursor(row - 1, self.edit_column_index)
                elif not event.ShiftDown() and row < self.grid.GetNumberRows() - 1:
                    self.grid.SetGridCursor(row + 1, self.edit_column_index)