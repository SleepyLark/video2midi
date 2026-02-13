from __future__ import annotations
from typing import TYPE_CHECKING
from .gl import *

if TYPE_CHECKING:
    from ..controller import AppController

class ColorWindow(GLWindow):
    def __init__(self, app: AppController, x, y, w, h):
        super().__init__(x, y, w, h, "Color Map")
        self.root = self
        self.app = app

        self.colorBtns = []
        self.colorBtns_channel_labels=[]
        self.colorBtns_channel_btns=[]

        self.addButtons()

    def addButtons(self):
        for i in range( len( self.app.prefs.keyp_colors ) ):
            cx,cy = (i % 2) * 130,  ( i // 2 ) * 20
            offsetx,offsety=4,4

            self.colorBtns.append( GLColorButton(offsetx+cx,offsety+cy ,20,20,i, self.app.prefs.keyp_colors[i], self.app.onPallete_click ) )
            self.root.appendChild(self.colorBtns[i])
            color_channel_label = GLLabel(offsetx+25+cx,offsety+cy , "Ch:" + str(self.app.prefs.keyp_colors_channel[i]+1) )

            self.colorBtns_channel_labels.append( color_channel_label )
            self.root.appendChild(color_channel_label)

            self.colorBtns_channel_btns.append( GLButton(offsetx+cx+70,offsety+cy ,20,20,(i+1), [128,128,128], "+" ,self.app.update_channels) )
            self.colorBtns_channel_btns.append( GLButton(offsetx+cx+70+20,offsety+cy ,20,20,-(i+1), [128,128,128], "-" ,self.app.update_channels) )
            self.colorBtns_channel_btns.append( GLButton(offsetx+cx+70+40,offsety+cy ,20,20,i, [128,128,128], "x" ,self.app.disable_color, hint="ctrl+0 - shortcut, disable selected color") )

        for i in self.colorBtns_channel_btns:
            self.root.appendChild(i)