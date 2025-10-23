"""
ui.py - Pygame/OpenGL UI and widget logic for video2midi
Handles window creation, event loop, and drawing routines.
"""

# UI logic will be moved here from v2m.py

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from pygame.locals import *
from video2midi.prefs import prefs
from video2midi.settings import *
from video2midi.views.gl import *
import cv2
import time, math, os, ntpath

class MainWindow:
    def __init__(self, width = 640, height = 480):
        self.width = width
        self.height = height
        self.defaultWidth = width
        self.defaultHeight = height
        self.currentImage = None
        self.screen = 0
        pygame.init()
        # Create an OpenGL-capable window BEFORE calling any OpenGL functions.
        # This ensures an active GL context so gl* calls (like glPixelStorei)
        # inside doinitGl() won't raise GL_INVALID_OPERATION (1282).
        self.screen = pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL | pygame.RESIZABLE)
        # Now it's safe to initialize GL objects
        doinitGl()
        
    def fit_to_the_screen(self) -> None:
        infoObject = pygame.display.Info()
        if (self.width > infoObject.current_w) or ( self.height > infoObject.current_h):
            print("try fit window to the screen")
            print("current window size: %sx%s" %(self.width, self.height))
            print("current screen size: %sx%s" %(infoObject.current_w, infoObject.current_h))
            ratio  = ( self.width / infoObject.current_w)
            self.width = int(self.width / ratio * 0.9 )
            self.height = int(self.height / ratio *0.9)
            print("new window size: %sx%s" %(self.width,self.height))

    def resize_window(self) -> None:
        if prefs.resize:
            self.width = prefs.resize_width
            self.height = prefs.resize_height
        else:
            self.width = self.defaultWidth
            self.height = self.defaultHeight
            self.fit_to_the_screen()
        # Recreate display with new size and reinitialize GL state
        self.screen = pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL | pygame.RESIZABLE)
        self.doinit()

    
    def update_size(self) -> None:
        if ( prefs.resize == 1 ):
            self.width = prefs.resize_width
            self.height = prefs.resize_height
        else:
            self.fit_to_the_screen()

    def loadImage(self, image):
        # if running:
        #     video.getFrame(idframe)
        #     image = video.image
        self.currentImage = image
        glBindTexture(GL_TEXTURE_2D, Gl.bgImgGL)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)
        error_on_load = False
        try:
            rgb_image = image
            glTexImage2D(GL_TEXTURE_2D, 0, 3, self.defaultWidth, self.defaultHeight, 0, GL_RGB, GL_UNSIGNED_BYTE, rgb_image)
            return
        except Exception as E:
            error_on_load = True
            print(f"Can't load image from video to OpenGL: {E}")
        if error_on_load:
            rvideo_width, rvideo_height = 512, 512
            print(f"Trying resize video image to {rvideo_width}x{rvideo_height}")
            try:
                rimage = cv2.resize(image, (rvideo_width, rvideo_height))
                rgb_image = cv2.cvtColor(rimage, cv2.COLOR_BGR2RGB)
                glTexImage2D(GL_TEXTURE_2D, 0, 3, rvideo_width, rvideo_height, 0, GL_RGB, GL_UNSIGNED_BYTE, rgb_image)
            except Exception as E:
                print(f"Can't load image from video to OpenGL: {E}")

    def doinit(self):
        doinitGl()
        self.loadImage(self.currentImage)
        GenFontTexture()

    # UI widget/window setup, drawframe, and event loop will be moved here from v2m.py
    # Example stub for drawframe:
    def drawframe(lastimage=None):
        # ... (full drawframe code from v2m.py, unchanged)
        pass  # Replace with actual code

    # Example stub for main event loop:
    def main_event_loop():
        # ... (event loop and window/widget setup from v2m.py)
        pass  # Replace with actual code
