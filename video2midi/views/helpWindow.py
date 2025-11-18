from ..prefs import prefs
from ..settings import *
from .gl import *

class HelpWindow(GLWindow):
    def __init__(self, app, x, y, w, h):
        super().__init__(x, y, w, h, "Help")
        self.root = self
        self.app = app

        self.root.hidden = True

        manual = GLLabel(0,0, """h - on window title, show/hide the window
q - begin to recreate midi
s - set start frame, (mods : shift, set processing start frame to the beginning)
e - set end frame, (mods : shift, set processing end frame to the ending)
p - if key is set, force separate to 2 channels (on single color video)
o - enable or disable overlap notes
i - enable or disable ignore/lengthening of notes with minimal duration
r - enable or disable resize function
Mouse wheel - keys adjustment
Left mouse button - dragging the selected key / select color from the color map
CTRL + Left mouse button - update selected color in the color map
CTRL + 0 - disable selected color in the color map
Right mouse button - dragging all keys, if the key is selected, the transfer is carried out relative to it.
Arrows - keys adjustment (mods : shift) ( Atl+Arrows UP/Down - sparks position adjustment )
+(PLUS) / - (MINUS) - rotate keys by 5*
PageUp/PageDown - scrolling video (mods : shift)
Home/End - go to the beginning or end of the video
[ / ] - change base octave
F2 / F3 - save / load settings, F4 - move all windows to the mouse point
Escape - quit, TAB - Show/Hide all windows
Space - abort re-creation and save midi file to disk
4,6,8,2 on numpad - move the selected key by 1 pixel on each axis
1,3 - vertical / horizontal alignment""")
        
        self.root.appendChild(manual)