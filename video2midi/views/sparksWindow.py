from ..prefs import prefs
from ..settings import *
from .gl import *

class SparksWindow(GLWindow):
    def __init__(self, app, x, y, w, h):
        super().__init__(x, y, w, h, "Sparks & Color Settings")
        self.root = self
        self.app = app

        self.addButtons()
        self.addSliders()

    def addButtons(self):
        self.sparks_switch = GLButton(313,24 ,100,22,1, [128,128,128], "use sparks" ,self.app.change_use_sparks,switch=1, switch_status=prefs.use_sparks )
        self.root.appendChild( self.sparks_switch )

        self.root.appendChild( GLButton(413   ,24 ,32,22,1, [96,96,128], "y+" ,self.app.update_sparks_y_pos, hint="move sparks higher") )
        self.root.appendChild( GLButton(413+33,24 ,32,22,1, [96,96,128], "y-" ,self.app.update_sparks_y_pos, hint="move sparks lower") )
        self.root.appendChild( GLLabel( 6,50,  "alt + up / down - move sparks label up or down " ))

        self.use_percolor_delta = GLButton(313,100 ,190,22,1, [128,128,128], "use percolor sensitivity" ,self.app.change_use_percolor_delta,switch=1, switch_status=prefs.use_sparks )
        self.root.appendChild( self.use_percolor_delta )

    def addSliders(self):
        self.sparks_slider_delta = GLSlider(6,25, 150,18, -50,150,50,self.app.update_sparks_delta, label="Sparks delta")
        self.root.appendChild( self.sparks_slider_delta )

        sparks_slider_height = GLSlider(160,25, 150,18, 1,60,1,None, label="Sparks height")
        sparks_slider_height.round=0
        self.root.appendChild( sparks_slider_height )

        self.selected_color_delta = GLSlider(6,100, 200,18, 0,130,50,self.app.update_percolor_delta, label="percolor sensitivity")
        self.selected_color_delta.round=1
        self.root.appendChild( self.selected_color_delta )