from ..prefs import prefs
from ..settings import *
from .gl import *

class ExtraWindow(GLWindow):
    def __init__(self, app, x, y, w, h):
        super().__init__(x, y, w, h, "Extra/Experimental")
        self.root = self
        self.app = app

        self.extra_label1 = GLLabel(6,0,  "Use alternate:"+str(prefs.use_alternate_keys)  )
        self.root.appendChild( self.extra_label1 )
        extra_label3 = GLLabel( 6,90,  """to select the key press ctrl + left mouse button on the key rect.
to deselect the key press ctrl + left mouse button on empty space.""" )
        self.root.appendChild( extra_label3 )

        self.addButtons()
        self.addSliders()

    def addButtons(self): 
        self.root.appendChild( GLButton(5,  20 ,128,25,1, [128,128,128], "read colors" ,self.app.readcolors) )
        self.root.appendChild( GLButton(135,20 ,128,25,1, [128,128,128], "update color" ,self.app.updatecolor) )
        self.root.appendChild( GLButton(265,20 ,138,25,1, [128,128,128], "enable/disable" ,self.app.change_use_alternate_keys) )
        self.root.appendChild( GLButton(265,45 ,155,22,1, [96 ,96 ,128], "snap notes to grid" ,self.app.snap_notes_to_the_grid,switch=1, switch_status=self.app.use_snap_notes_to_grid) )

    def addSliders(self):
        self.extra_slider1 = GLSlider(6,65, 240,18, -100,100,0,self.app.update_alternate_sensitivity, label="Selected key sensitivity")
        self.appendChild(self.extra_slider1)

        #TODO FIGURE OUT WHERE LINE_HEIGHT GOES
        extraWindow_slider2 = GLSlider(5,155, 240,18, 0,2000, self.app.line_height, self.app.update_line_height, label="length of vertical key lines")
        extraWindow_slider2.round=0
        self.appendChild(extraWindow_slider2)
