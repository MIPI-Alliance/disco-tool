import wx

class PanelBase(wx.Panel):
    """
    PanelBase hosts shared functionality between panels.
    """

    def __init__(self, *args, **kw):
        # ensure the required properties are overridden when instantiated
        self.edit_column_index
        self.grid

        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    @property
    def edit_column_index(self):
        """
        The index (0- based) of the main column edited by the user.
        """
        raise TypeError("Not implemented - you must override this property in the child class")

    @property
    def grid(self):
        """
        The wx.Grid object that is contained within the panel.
        """
        raise TypeError("Not implemented - you must override this property in the child class")

    def OnKeyDown(self, event):
        """
        Event that handles keystrokes while focus is in the grid.
        TAB/shift-TAB functionality overwritten to instead move vertically to the next/previous row,
        if focus is currently in the main edit column (see edit_column_index).
        """
        keyCode = event.GetKeyCode()
        row = self.grid.GetGridCursorRow()
        col = self.grid.GetGridCursorCol()

        if keyCode == wx.WXK_TAB:
            if col == self.edit_column_index:
                if event.ShiftDown() and row > 0:
                    self.grid.SetGridCursor(row - 1, self.edit_column_index)
                elif not event.ShiftDown() and row < self.grid.GetNumberRows() - 1:
                    self.grid.SetGridCursor(row + 1, self.edit_column_index)
        else:
            event.Skip()