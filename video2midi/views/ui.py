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
from ..prefs import prefs
from ..settings import *
from .gl import *
from .settingsWindow import SettingsWindow
from .colorWindow import ColorWindow
from .extraWindow import ExtraWindow
from .sparksWindow import SparksWindow
from .helpWindow import HelpWindow
import cv2
import time, math, os, ntpath

import logging

logger = logging.getLogger(__name__)


class MainWindow:
    def __init__(self, app, project_name, width=640, height=480):
        self.app = app

        self.defaultWidth = width
        self.defaultHeight = height
        self.currentImage = None
        self.renderedFrame = None
        self.screen = None

        os.environ["SDL_VIDEO_CENTERED"] = "1"

        logger.debug("Initialize pygame")
        pygame.init()
        # Create an OpenGL-capable window BEFORE calling any OpenGL functions.
        # This ensures an active GL context so gl* calls (like glPixelStorei)
        # inside doinitGl() won't raise GL_INVALID_OPERATION (1282).

        self.width, self.height = self.get_best_window_size(width, height)

        self.flags = pygame.RESIZABLE | pygame.OPENGL | pygame.DOUBLEBUF

        self.screen = pygame.display.set_mode((self.width, self.height), self.flags)

        pygame.display.set_caption(project_name)
        # Now it's safe to initialize GL objects
        doinitGl()
        self.reshape()

        self.ShowHideButton = GLButton(
            0,
            0,
            13,
            13,
            1,
            [128, 128, 128],
            "",
            app.show_or_hide_all_windows,
            switch=1,
            switch_status=False,
        )
        self.ShowHideButton.active = 2

        logger.debug("Creating subwindows")
        self.settingsWindow = SettingsWindow(self.app, 24 + 275, 80, 550, 380)
        wh = ((len(prefs.keyp_colors) // 2) + 2) * 24 - 24
        self.colorWindow = ColorWindow(self.app, 24, 50, 274, wh)
        self.helpWindow = HelpWindow(self.app, 24 + 270, 50, 750, 535)
        self.extraWindow = ExtraWindow(self.app, 24 + 270 + 550 + 6, 80, 510, 250)
        self.sparksWindow = SparksWindow(self.app, 24 + 270 + 550 + 6, 300, 510, 185)

        self.glwindows = []

        self.glwindows.append(self.ShowHideButton)
        self.glwindows.append(self.helpWindow)
        self.glwindows.append(self.settingsWindow)
        self.glwindows.append(self.colorWindow)
        self.glwindows.append(self.extraWindow)

        GenFontTexture()


    def get_best_window_size(self,video_w, video_h, margin=120):
        """
        Returns an optimal window size:
        - If the video's resolution is larger than the display area → use available display size.
        - Else → use the video size.
        """
        # Get monitor resolution
        display_info = pygame.display.Info()
        screen_w, screen_h = display_info.current_w, display_info.current_h

        # Work area: leave room for window borders, OS UI, etc.
        work_w = screen_w - margin
        work_h = screen_h - margin

        # If video is SMALLER than work area → return video dimensions
        if video_w <= work_w and video_h <= work_h:
            return video_w, video_h

        # Otherwise, scale to best fit while keeping aspect ratio
        aspect = video_w / video_h

        # Fit to width
        scaled_w = work_w
        scaled_h = int(work_w / aspect)

        if scaled_h > work_h:
            # Fit to height instead
            scaled_h = work_h
            scaled_w = int(work_h * aspect)

        return scaled_w, scaled_h

    def fit_to_the_screen(self) -> None:
        display_info = pygame.display.Info()
        logger.debug(
            f"Current window size:{display_info.current_w}x{display_info.current_h}"
        )
        if (self.width > display_info.current_w) or (
            self.height > display_info.current_h
        ):
            logger.debug("Try fit window to the screen...")
            logger.debug("Current window size: %sx%s" % (self.width, self.height))
            logger.debug(
                "Current screen size: %sx%s"
                % (display_info.current_w, display_info.current_h)
            )

            ratio = self.width / display_info.current_w
            self.width = int(self.width / ratio * 0.9)
            self.height = int(self.height / ratio * 0.9)

            logger.debug("New window size: %sx%s" % (self.width, self.height))

    def doinit(self):
        doinitGl()
        GenFontTexture()
        self.reshape()

    def reshape(self):
        """Resize viewport and draw current frame immediately."""
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 100)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)

        # Draw current image if available
        if self.currentImage is not None:
            self._upload_texture_for_current_size()
            self.drawframe()

    def resize_window(self):
        """Called when window size changes."""
        logger.debug("Resizing...")
        if prefs.resize:
            self.width = prefs.resize_width
            self.height = prefs.resize_height
        else:
            self.width = self.defaultWidth
            self.height = self.defaultHeight
            self.fit_to_the_screen()

        # Recreate display with new size
        self.screen = pygame.display.set_mode((self.width, self.height), self.flags)
        logger.debug("New window size: %sx%s" % (self.width, self.height))

        # Update GL and redraw
        self.doinit()

    def old_resize_window(self) -> None:
        if prefs.resize:
            self.width = prefs.resize_width
            self.height = prefs.resize_height
        else:
            self.width = self.defaultWidth
            self.height = self.defaultHeight
            self.fit_to_the_screen()
        # Recreate display with new size and reinitialize GL state
        pygame.display.set_mode((self.width, self.height), self.flags)

        logger.debug("New window size: %sx%s" % (self.width, self.height))

        self.doinit()
        

    def update_size(self) -> None:
        if prefs.resize == 1:
            self.width = prefs.resize_width
            self.height = prefs.resize_height
        else:
            self.fit_to_the_screen()

    def loadImage(self, image):
        """Load a new video frame (full resolution)."""
        if image is None or image.size == 0:
            return
        self.currentImage = image
        self._upload_texture_for_current_size()

    def _upload_texture_for_current_size(self):
        """Resize original image to current window size and upload to OpenGL."""
        img = self.currentImage
        if img.shape[1] != self.width or img.shape[0] != self.height:
            img = cv2.resize(img, (self.width, self.height), interpolation=cv2.INTER_LINEAR)

        rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        rgb_image = np.ascontiguousarray(rgb_image)

        glBindTexture(GL_TEXTURE_2D, Gl.bgImgGL)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)
        glTexImage2D(GL_TEXTURE_2D, 0, 3, rgb_image.shape[1], rgb_image.shape[0], 0, GL_RGB, GL_UNSIGNED_BYTE, rgb_image)

        self.renderedFrame = img
        pygame.display.flip()  # Update immediately

    def old_loadImage(self, image):
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
            glTexImage2D(
                GL_TEXTURE_2D,
                0,
                3,
                self.defaultWidth,
                self.defaultHeight,
                0,
                GL_RGB,
                GL_UNSIGNED_BYTE,
                rgb_image,
            )
            logger.debug("image loaded to 2D texture")
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
                glTexImage2D(
                    GL_TEXTURE_2D,
                    0,
                    3,
                    rvideo_width,
                    rvideo_height,
                    0,
                    GL_RGB,
                    GL_UNSIGNED_BYTE,
                    rgb_image,
                )
            except Exception as E:
                logger.exception(f"Can't load image from video to OpenGL: {E}")

    def doinit(self):
        doinitGl()
        GenFontTexture()
        self.reshape()

    # UI widget/window setup, drawframe, and event loop will be moved here from v2m.py
    # Example stub for drawframe:
    def drawframe(self, lastimage=None):

        scale = 1.0

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glScale(scale, scale, 1)
        glColor4f(1.0, 1.0, 1.0, 1.0)

        glBindTexture(GL_TEXTURE_2D, Gl.bgImgGL)
        glEnable(GL_TEXTURE_2D)
        DrawQuad(0, 0, self.width, self.height)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glColor4f(1.0, 0.5, 1.0, 0.5)

        glPushMatrix()
        glTranslatef(prefs.xoffset_whitekeys, prefs.yoffset_whitekeys, 0)
        glDisable(GL_TEXTURE_2D)
        glPopMatrix()

        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)

        for window in self.glwindows:
            window.draw()

        # drawing hints over all windows
        for window in self.glwindows:
            window.drawhint()

        pygame.display.flip()

    def key_down_event(self, key):
        for window in self.glwindows:
            window.update_key_down(key)

    # TODO:This function may not even do anything
    def mouse_up_event(self, mouse_x, mouse_y, button):
        for i in range(len(self.glwindows) - 1, -1, -1):
            # print("process mouse up on windiws id: ", i)
            if self.glwindows[i].update_mouse_up(mouse_x, mouse_y, button) == 1:
                mouseOnWindows = True
                resort = True
                break

    def mouse_down_event(self, mouse_x, mouse_y, button):
        resort = False
        for i in range(len(self.glwindows) - 1, -1, -1):
            # print("process mouse down on windiws id: ", i)
            if self.glwindows[i].update_mouse_down(mouse_x, mouse_y, button) == 1:
                mouseOnWindows = True
                resort = True
                break
        if resort:
            self.glwindows.sort(key=lambda x: x.active, reverse=False)

    def mouse_move(self, mouse_x, mouse_y):
        for wnd in self.glwindows:
            wnd.update_mouse_move(mouse_x, mouse_y)

    def get_colorBtn_list(self):
        return self.colorWindow.colorBtns

    def flip_switch_on_keypress(sender):
        sender.switch_status = not sender.switch_status

    def draw_toggle_windows(self, sender=None):

        logger.debug("Hide all windows")

        for i in self.glwindows:
            # print("i.type =%s" % (str(type(i))) )
            if isinstance(i, GLWindow):
                i.fullhidden = self.ShowHideButton.switch_status

    def toggle_window_button(self):
        # Functions that allow hotkeys for buttons need to manually flip button's switch status
        self.ShowHideButton.switch_status = not self.ShowHideButton.switch_status

    def toggle_notes_overlap(self):
        self.settingsWindow.notes_overlap_btn.switch_status = (
            not self.settingsWindow.notes_overlap_btn.switch_status
        )

    def toggle_ignore_notes_minimal(self):
        self.settingsWindow.ignore_notes_with_minimal_duration_btn.switch_status = (
            not self.settingsWindow.ignore_notes_with_minimal_duration_btn.switch_status
        )

    def update_alternate_label(self):
        self.extraWindow.extra_label1.text = "Use alternate:" + str(
            prefs.use_alternate_keys
        )

    def update_values_from_settings(self):
        if len(self.colorWindow.colorBtns_channel_labels) > 0:
            for i in range(len(self.colorWindow.colorBtns)):
                self.colorWindow.colorBtns_channel_labels[i].text = "Ch:" + str(
                    prefs.keyp_colors_channel[i] + 1
                )

        self.settingsWindow.key_sensitivity_slider.setvalue(prefs.keyp_delta)
        self.settingsWindow.minimal_duration_slider.setvalue(
            prefs.minimal_duration * 100
        )
        self.settingsWindow.tempo_slider.setvalue(prefs.tempo)
        self.settingsWindow.key_count_slider.setvalue(prefs.keys_pos_cnt)
        self.settingsWindow.rollcheck_button.switch_status = prefs.rollcheck
        self.settingsWindow.rollcheck_priority_button.switch_status = (
            prefs.rollcheck_priority
        )
        self.settingsWindow.notes_overlap_btn.switch_status = prefs.notes_overlap
        self.settingsWindow.ignore_notes_with_minimal_duration_btn.switch_status = (
            prefs.ignore_minimal_duration
        )

        self.sparksWindow.use_percolor_delta.switch_status = prefs.use_percolor_delta
        self.sparksWindow.sparks_switch.switch_status = prefs.use_sparks
        self.sparksWindow.sparks_slider_delta.value = 0
        self.sparksWindow.sparks_slider_delta.id = -1
