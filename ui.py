"""
ui.py - Pygame/OpenGL UI and widget logic for video2midi
Handles window creation, event loop, and drawing routines.
"""

# UI logic will be moved here from v2m.py

import pygame
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from pygame.locals import *
from video2midi.prefs import prefs
from video2midi.settings import *
from video2midi.views.gl import *
from settingsWindow import *
from colorWindow import *
from helpWindow import *
from extraWindow import *
from sparksWindow import *
import cv2
import time, math, os, ntpath

import logging
logger = logging.getLogger(__name__)

class MainWindow:
    def __init__(self, app, project_name, width = 640, height = 480):
        self.app = app
        
        self.width = width
        self.height = height
        self.defaultWidth = width
        self.defaultHeight = height
        self.currentImage = None
        self.screen = None
        
        logger.debug("Initialize pygame")
        pygame.init()
        # Create an OpenGL-capable window BEFORE calling any OpenGL functions.
        # This ensures an active GL context so gl* calls (like glPixelStorei)
        # inside doinitGl() won't raise GL_INVALID_OPERATION (1282).
        self.screen = pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL | pygame.RESIZABLE)
        pygame.display.set_caption(project_name)
        # Now it's safe to initialize GL objects
        doinitGl()

        self.ShowHideButton = GLButton(0,0 ,13,13, 1, [128,128,128], "" , app.show_or_hide_all_windows ,switch=1, switch_status=0 )
        self.ShowHideButton.active = 2

        logger.debug("Creating subwindows")
        self.settingsWindow = SettingsWindow(self.app,24+275, 80, 550, 380)
        wh = ( (len(prefs.keyp_colors) // 2)+2 ) * 24 - 24
        self.colorWindow = ColorWindow(self.app,24, 50, 274, wh)
        self.helpWindow = HelpWindow(self.app,24+270, 50, 750, 535)
        self.extraWindow = ExtraWindow(self.app,24+270+550+6, 80, 510, 250)
        self.sparksWindow = SparksWindow(self.app, 24+270+550+6, 300, 510, 185)

        self.glwindows=[]

        self.glwindows.append(self.ShowHideButton)
        self.glwindows.append(self.settingsWindow)
        self.glwindows.append(self.colorWindow)
        self.glwindows.append(self.extraWindow)
        
    def fit_to_the_screen(self) -> None:
        infoObject = pygame.display.Info()
        if (self.width > infoObject.current_w) or ( self.height > infoObject.current_h):
            logger.debug("Try fit window to the screen...")
            logger.debug("Current window size: %sx%s" %(self.width, self.height))
            logger.debug("Current screen size: %sx%s" %(infoObject.current_w, infoObject.current_h))

            ratio  = ( self.width / infoObject.current_w)
            self.width = int(self.width / ratio * 0.9 )
            self.height = int(self.height / ratio *0.9)

            logger.debug("New window size: %sx%s" %(self.width,self.height))

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

    def new_loadImage(self, image):
        if image is None:
            return
        self.currentImage = image
        rgb = np.ascontiguousarray(self.currentImage)
        h, w = rgb.shape[:2]
        glBindTexture(GL_TEXTURE_2D, Gl.bgImgGL)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, rgb)
        logger.debug("image loaded")


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
            logger.exception(f"Can't load image from video to OpenGL: {E}")
        if error_on_load:
            rvideo_width, rvideo_height = 512, 512
            logger.debug(f"Trying resize video image to {rvideo_width}x{rvideo_height}")
            try:
                rimage = cv2.resize(image, (rvideo_width, rvideo_height))
                rgb_image = cv2.cvtColor(rimage, cv2.COLOR_BGR2RGB)
                glTexImage2D(GL_TEXTURE_2D, 0, 3, rvideo_width, rvideo_height, 0, GL_RGB, GL_UNSIGNED_BYTE, rgb_image)
            except Exception as E:
                logger.exception(f"Can't load image from video to OpenGL: {E}")

    def doinit(self):
        doinitGl()
        self.loadImage(self.currentImage)
        GenFontTexture()

    # UI widget/window setup, drawframe, and event loop will be moved here from v2m.py
    # Example stub for drawframe:
    def drawframe(self, lastimage=None):
        scale=1.0

        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glViewport (0, 0, self.width, self.height)
        glMatrixMode (GL_PROJECTION)
        glLoadIdentity ()
        glOrtho(0, self.width, self.height, 0, -1, 100)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)

        glScale(scale,scale,1)
        glColor4f(1.0, 1.0, 1.0, 1.0)

        glBindTexture(GL_TEXTURE_2D, Gl.bgImgGL)
        glEnable(GL_TEXTURE_2D)
        DrawQuad(0,0,self.width,self.height)


        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glColor4f(1.0, 0.5, 1.0, 0.5)

        glPushMatrix()
        glTranslatef(prefs.xoffset_whitekeys,prefs.yoffset_whitekeys,0)
        glDisable(GL_TEXTURE_2D)
        glPopMatrix()

        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)

        for window in self.glwindows:
            window.draw()

        # drawing hints over all windows
        for window in self.glwindows:
            window.drawhint()

    # Example stub for main event loop:
    def main_event_loop():
        # ... (event loop and window/widget setup from v2m.py)
        pass  # Replace with actual code

    def get_colorBtn_list(self):
        return self.colorWindow.colorBtns
    
    def toggle_windows(self):
        self.ShowHideButton.switch_status = not self.ShowHideButton.switch_status
        
        logger.debug('Hide all windows')
        for i in self.glwindows:
            #print("i.type =%s" % (str(type(i))) )
            if isinstance(i, GLWindow ):
                i.fullhidden = self.ShowHideButton.switch_status

    def toggle_notes_overlap(self):
        self.settingsWindow.notes_overlap_btn.switch_status = not self.settingsWindow.notes_overlap_btn.switch_status
    
    def toggle_ignore_notes_minimal(self):
        self.settingsWindow.ignore_notes_with_minimal_duration_btn.switch_status = not self.settingsWindow.ignore_notes_with_minimal_duration_btn.switch_status

    def update_alternate_label(self):
        self.extraWindow.extra_label1.text = "Use alternate:"+str(prefs.use_alternate_keys)

    def update_values_from_settings(self):
        if len(self.colorWindow.colorBtns_channel_labels) > 0:
            for i in range(len(self.colorWindow.colorBtns)):
                self.colorWindow.colorBtns_channel_labels[i].text = "Ch:" + str(prefs.keyp_colors_channel[i]+1)

        self.settingsWindow.key_sensitivity_slider.setvalue(prefs.keyp_delta)
        self.settingsWindow.minimal_duration_slider.setvalue(prefs.minimal_duration * 100)
        self.settingsWindow.tempo_slider.setvalue(prefs.tempo)
        self.settingsWindow.key_count_slider.setvalue(prefs.keys_pos_cnt)
        self.settingsWindow.rollcheck_button.switch_status = prefs.rollcheck
        self.settingsWindow.rollcheck_priority_button.switch_status = prefs.rollcheck_priority
        self.settingsWindow.notes_overlap_btn.switch_status = prefs.notes_overlap
        self.settingsWindow.ignore_notes_with_minimal_duration_btn.switch_status = prefs.ignore_minimal_duration
        
        self.sparksWindow.use_percolor_delta.switch_status = prefs.use_percolor_delta
        self.sparksWindow.sparks_switch.switch_status = prefs.use_sparks
        self.sparksWindow.sparks_slider_delta.value = 0
        self.sparksWindow.sparks_slider_delta.id =-1

    import time
    from math import sin, cos, radians

    def draw_test_pattern(self):
        """Simple test: clear, draw background and a rotating colored quad, then flip."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glViewport(0, 0, self.width, self.height)

        # Setup orthographic projection with origin at top-left (matches your drawframe)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 100)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)

        # Background
        glDisable(GL_TEXTURE_2D)
        glColor4f(0.12, 0.12, 0.12, 1.0)
        DrawQuad(0, 0, self.width, self.height)

        # Draw a rotating quad in the center
        cx, cy = self.width // 2, self.height // 2
        size = min(self.width, self.height) * 0.25
        angle = (time.time() * 60) % 360  # degrees

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glPushMatrix()
        try:
            glTranslatef(cx, cy, 0)
            glRotatef(angle, 0, 0, 1)
            glColor4f(0.2, 0.7, 1.0, 0.9)

            # Draw quad centered at origin
            half = size / 2
            DrawQuad(-half, -half, size, size)
        finally:
            glPopMatrix()

        # Draw a small static square at top-left to mimic a button
        glColor4f(0.8, 0.3, 0.2, 1.0)
        DrawQuad(10, 10, 40, 24)

        # Present
        pygame.display.flip()
