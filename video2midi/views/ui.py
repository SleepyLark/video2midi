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
    def __init__(self, app, project_name, first_frame):
        self.app = app

        frame_w = first_frame.shape[1]
        frame_h = first_frame.shape[0]
        self.defaultWidth = frame_w
        self.defaultHeight = frame_h
        self.currentImage = None
        self.renderedFrame = None
        self.screen = None

        os.environ["SDL_VIDEO_CENTERED"] = "1"

        logger.debug("Initialize pygame")
        pygame.init()
        # Create an OpenGL-capable window BEFORE calling any OpenGL functions.
        # This ensures an active GL context so gl* calls (like glPixelStorei)
        # inside doinitGl() won't raise GL_INVALID_OPERATION (1282).

        self.width, self.height = self.get_best_window_size(frame_w, frame_h)

        self.flags = pygame.RESIZABLE | pygame.OPENGL | pygame.DOUBLEBUF

        self.screen = pygame.display.set_mode((self.width, self.height), self.flags)

        pygame.display.set_caption(project_name)
        # Now it's safe to initialize GL objects
        doinitGl()
        self.reshape(self.width, self.height)
        self.loadImage(first_frame)


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
        self.settingsWindow = SettingsWindow(self.app, 24 + 275, 80, 500, 380)
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

    def get_aspect_fit_size(self, src_w, src_h, dst_w, dst_h):
        """Return (draw_w, draw_h, offset_x, offset_y) so the source fits in the
        destination rectangle while keeping aspect ratio."""
        src_aspect = src_w / src_h
        dst_aspect = dst_w / dst_h

        if src_aspect > dst_aspect:
            # limited by width
            draw_w = dst_w
            draw_h = int(dst_w / src_aspect)
        else:
            # limited by height
            draw_h = dst_h
            draw_w = int(dst_h * src_aspect)

        offset_x = (dst_w - draw_w) // 2
        offset_y = (dst_h - draw_h) // 2

        return draw_w, draw_h, offset_x, offset_y

    def doinit(self):
        doinitGl()
        GenFontTexture()
        self.reshape()

    def reshape(self, w=None, h=None):
        """Update OpenGL viewport / projection when the window size changes."""
        if w is None:
            w = self.width
        if h is None:
            h = self.height

        self.width = w
        self.height = h

        glViewport(0, 0, w, h)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, w, h, 0, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def resize_window(self):
        """Toggle between user-defined size and auto-fit size."""
        logger.debug("Resizing window...")

        self.update_size()
        self.screen = pygame.display.set_mode((self.width, self.height), self.flags)

        logger.debug(f"Window resized to: {self.width}x{self.height}")

        # Update OpenGL viewport & projection
        self.reshape()        

    def update_size(self) -> None:
        if prefs.resize:
            # User-selected fixed size
            new_w = prefs.resize_width
            new_h = prefs.resize_height
            logger.debug(f"Prefs resize -> {new_w}x{new_h}")
        else:
            # Default to project video size, but fit to screen safely
            new_w = self.defaultWidth
            new_h = self.defaultHeight
            logger.debug(f"Default video size -> {new_w}x{new_h}")

            # Shrink if it would exceed desktop size
            best_w, best_h = self.get_best_window_size(new_w, new_h)
            new_w, new_h = best_w, best_h
            logger.debug(f"Fitted to screen -> {new_w}x{new_h}")

        # Apply the resize
        self.width, self.height = new_w, new_h

    def loadImage(self, image):
        """Upload the video frame to the GPU as a texture without resizing it."""
        self.currentImage = image
        self.tex_w = image.shape[1]
        self.tex_h = image.shape[0]

        glBindTexture(GL_TEXTURE_2D, Gl.bgImgGL)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB,
                    self.tex_w, self.tex_h,
                    0, GL_RGB, GL_UNSIGNED_BYTE, rgb_image)
        
    def doinit(self):
        doinitGl()
        GenFontTexture()
        self.reshape()

    def drawframe(self):
        if self.currentImage is None:
            return

        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()

        draw_w, draw_h, off_x, off_y = self.get_aspect_fit_size(
            self.tex_w, self.tex_h,
            self.width, self.height
        )

        # ------------------------------------------------------------------
        # 2. Draw the background image using the fitted rectangle
        # ------------------------------------------------------------------
        glBindTexture(GL_TEXTURE_2D, Gl.bgImgGL)
        glColor4f(1, 1, 1, 1)

        # Draw JUST the fitted quad, not the entire window
        DrawQuad(off_x, off_y, off_x + draw_w, off_y + draw_h)

        # ------------------------------------------------------------------
        # 3. Draw overlays/UI
        # ------------------------------------------------------------------
        glColor4f(1.0, 0.5, 1.0, 0.5)
        for window in self.glwindows:
            window.draw()

        # drawing hints over all windows
        for window in self.glwindows:
            window.drawhint()

        glPushMatrix()
        glTranslatef(prefs.xoffset_whitekeys, prefs.yoffset_whitekeys, 0)

        glDisable(GL_TEXTURE_2D)
        # draw your white-key outlines/shapes here

        glEnable(GL_TEXTURE_2D)

        glPopMatrix()

        pygame.display.flip()

    # === UI cosmetic changes and handlers ===

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
    
    def update_selected_color_delta(self, sender, index):
        self.sparksWindow.selected_color_delta.color = sender.color

        if index < len(prefs.percolor_delta):
            self.sparksWindow.selected_color_delta.setvalue(prefs.percolor_delta[index])
            self.sparksWindow.sparks_slider_delta.id = Gl.keyp_colormap_id
            self.sparksWindow.sparks_slider_delta.color = prefs.keyp_colors[Gl.keyp_colormap_id]
            self.sparksWindow.sparks_slider_delta.setvalue(
                prefs.keyp_colors_sparks_sensitivity[Gl.keyp_colormap_id]
            )

    def update_color_channels(self, sender):
        i = abs(sender.index) - 1
        if sender.index > 0:
            prefs.keyp_colors_channel[i] = prefs.keyp_colors_channel[i] + 1
        else:
            prefs.keyp_colors_channel[i] = prefs.keyp_colors_channel[i] - 1
        if prefs.keyp_colors_channel[i] > 15:
            prefs.keyp_colors_channel[i] = 15
        if prefs.keyp_colors_channel[i] < 0:
            prefs.keyp_colors_channel[i] = 0

        self.colorWindow.colorBtns_channel_labels[i].text = "Ch:" + str(
            prefs.keyp_colors_channel[i] + 1
        )

    def update_alternate_label(self):
        self.extraWindow.extra_label1.text = "Use alternate:" + str(
            prefs.use_alternate_keys
        )

    def update_alternate_sensitivity(self, new_value):
        self.extraWindow.extra_slider1.setvalue(new_value)

    def update_values_from_settings(self):
        if len(self.colorWindow.colorBtns_channel_labels) > 0:
            for i in range(len(self.colorWindow.colorBtns)):
                self.colorWindow.colorBtns_channel_labels[i].text = "Ch:" + str(
                    prefs.keyp_colors_channel[i] + 1
                )

        self.settingsWindow.key_sensitivity_slider.set_and_callback(prefs.keyp_delta)
        self.settingsWindow.minimal_duration_slider.set_and_callback(
            prefs.minimal_duration * 100
        )
        self.settingsWindow.tempo_slider.set_and_callback(prefs.tempo)
        self.settingsWindow.key_count_slider.set_and_callback(prefs.keys_pos_cnt)
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
