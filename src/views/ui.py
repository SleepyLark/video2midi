"""
ui.py - Pygame/OpenGL UI and widget logic for video2midi
Handles window creation, event loop, and drawing routines with proper coordinate transformation.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
import pygame
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from pygame.locals import *
from src.views.gl import *
from src.views.settingsWindow import SettingsWindow
from src.views.colorWindow import ColorWindow
from src.views.extraWindow import ExtraWindow
from src.views.sparksWindow import SparksWindow
from src.views.helpWindow import HelpWindow
import cv2
import time, math, os, ntpath

import logging

if TYPE_CHECKING:
    from ..controller import AppController

logger = logging.getLogger(__name__)


class MainWindow:
    def __init__(self, app: AppController, project_name, first_frame):
        self.app = app

        frame_w = first_frame.shape[1]
        frame_h = first_frame.shape[0]
        # default is set to video's original resolution
        self.default_width = frame_w
        self.default_height = frame_h
        self.currentImage = None
        self.renderedFrame = None
        self.screen = None

        # Video display transform (for letterboxing/pillarboxing)
        self.video_draw_w = frame_w
        self.video_draw_h = frame_h
        self.video_offset_x = 0
        self.video_offset_y = 0

        os.environ["SDL_VIDEO_CENTERED"] = "1"

        logger.debug("Initialize pygame")
        pygame.init()
        
        self.width, self.height = self.get_best_window_size(frame_w, frame_h)
        self.flags = pygame.RESIZABLE | pygame.OPENGL | pygame.DOUBLEBUF

        self.screen = pygame.display.set_mode((self.width, self.height), self.flags)
        pygame.display.set_caption(project_name)
        
        # Initialize GL objects
        doinitGl()
        self.reshape(self.width, self.height)
        self.loadImage(first_frame)

        self.ShowHideButton = GLButton(
            0, 0, 13, 13, 1, [128, 128, 128], "",
            app.show_or_hide_all_windows,
            switch=1, switch_status=False,
        )
        self.ShowHideButton.active = 2

        logger.debug("Creating subwindows")
        self.settingsWindow = SettingsWindow(self.app, 24 + 275, 80, 500, 380)
        wh = ((len(self.app.prefs.keyp_colors) // 2) + 2) * 24 - 24
        self.colorWindow = ColorWindow(self.app, 24, 50, 274, wh)
        self.helpWindow = HelpWindow(self.app, 24 + 270, 50, 750, 535)
        self.extraWindow = ExtraWindow(self.app, 24 + 270 + 550 + 6, 80, 510, 250)
        self.sparksWindow = SparksWindow(self.app, 24 + 270 + 550 + 6, 300, 510, 185)

        self.glwindows = [
            self.ShowHideButton,
            self.helpWindow,
            self.settingsWindow,
            self.colorWindow,
            self.extraWindow,
            self.sparksWindow,
        ]

        GenFontTexture()
        
    def get_best_window_size(self, video_w, video_h, margin=120):
        """Returns optimal window size based on video and display dimensions."""
        display_info = pygame.display.Info()
        screen_w, screen_h = display_info.current_w, display_info.current_h

        work_w = screen_w - margin
        work_h = screen_h - margin

        if video_w <= work_w and video_h <= work_h:
            return video_w, video_h

        aspect = video_w / video_h
        scaled_w = work_w
        scaled_h = int(work_w / aspect)

        if scaled_h > work_h:
            scaled_h = work_h
            scaled_w = int(work_h * aspect)

        return scaled_w, scaled_h

    def get_aspect_fit_size(self, src_w, src_h, dst_w, dst_h):
        """Return (draw_w, draw_h, offset_x, offset_y) for aspect-fit rendering."""
        src_aspect = src_w / src_h
        dst_aspect = dst_w / dst_h

        if src_aspect > dst_aspect:
            draw_w = dst_w
            draw_h = int(dst_w / src_aspect)
        else:
            draw_h = dst_h
            draw_w = int(dst_h * src_aspect)

        offset_x = (dst_w - draw_w) // 2
        offset_y = (dst_h - draw_h) // 2

        return draw_w, draw_h, offset_x, offset_y

    def reshape(self, w=None, h=None):
        """Update OpenGL viewport / projection when the window size changes."""
        if w is None:
            w = self.width
        if h is None:
            h = self.height

        self.width = w
        self.height = h

        # Update video display transform
        self.video_draw_w, self.video_draw_h, self.video_offset_x, self.video_offset_y = \
            self.get_aspect_fit_size(self.default_width, self.default_height, w, h)

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
        self.reshape()

    def update_size(self) -> None:
        """Switch window size between config settings and what's the best screen resolution"""
        if self.app.prefs.resize:
            updated_w = self.app.prefs.resize_width
            updated_h = self.app.prefs.resize_height
            logger.debug(f"self.app.prefs resize -> {updated_w}x{updated_h}")
        else:
            updated_w = self.default_width
            updated_h = self.default_height
            logger.debug(f"Default video size -> {updated_w}x{updated_h}")

            best_w, best_h = self.get_best_window_size(updated_w, updated_h)
            updated_w, updated_h = best_w, best_h
            logger.debug(f"Fitted to screen -> {updated_w}x{updated_h}")

        self.width, self.height = updated_w, updated_h

    def loadImage(self, image):
        """Upload the video frame to the GPU as a texture."""
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

    def video_to_screen_coords(self, video_x, video_y):
        """
        Convert coordinates from video space to current screen space.
        Accounts for window resizing and letterboxing/pillarboxing.
        
        Args:
            video_x, video_y: Coordinates in original video resolution
            
        Returns:
            screen_x, screen_y: Coordinates in current window space
        """
        # Scale factor from video to displayed video
        scale_x = self.video_draw_w / self.default_width
        scale_y = self.video_draw_h / self.default_height
        
        # Apply scale and offset
        screen_x = video_x * scale_x + self.video_offset_x
        screen_y = video_y * scale_y + self.video_offset_y
        
        return screen_x, screen_y

    def screen_to_video_coords(self, screen_x, screen_y):
        """
        Convert coordinates from screen space to video space.
        Inverse of video_to_screen_coords.
        
        Args:
            screen_x, screen_y: Coordinates in current window space
            
        Returns:
            video_x, video_y: Coordinates in original video resolution
        """
        # Remove offset
        x = screen_x - self.video_offset_x
        y = screen_y - self.video_offset_y
        
        # Scale back to video resolution
        scale_x = self.default_width / self.video_draw_w
        scale_y = self.default_height / self.video_draw_h
        
        video_x = x * scale_x
        video_y = y * scale_y
        
        return video_x, video_y

    def getkeyp_pixel_pos(self, x: int, y: int) -> tuple[int, int]:
        """
        Convert key position to pixel coordinates in the original image.
        
        The key positions (self.app.prefs.keys_pos) are in video coordinate space,
        but with offsets applied. This function returns the actual pixel
        coordinates in the original video frame for sampling.
        """
        # Key positions are stored relative to the video, so add offsets
        video_x = self.app.prefs.xoffset_whitekeys + x
        video_y = self.app.prefs.yoffset_whitekeys + y

        # Bounds check against original video dimensions
        if video_x < 0 or video_x >= self.default_width or \
           video_y < 0 or video_y >= self.default_height:
            return None

        return (int(video_x), int(video_y))

    def get_key_screen_position(self, key_index):
        """
        Get the screen position where a key should be drawn.
        Transforms from video space to current screen space.
        
        Returns:
            (screen_x, screen_y) or None if out of bounds
        """
        if key_index >= len(self.app.prefs.keys_pos):
            return None
            
        # Get key position in video space (with offsets)
        video_x = self.app.prefs.xoffset_whitekeys + self.app.prefs.keys_pos[key_index][0]
        video_y = self.app.prefs.yoffset_whitekeys + self.app.prefs.keys_pos[key_index][1]
        
        # Transform to screen space
        screen_x, screen_y = self.video_to_screen_coords(video_x, video_y)
        
        return (screen_x, screen_y)

    def detect_key_presses(self):
        """
        Core detection logic: samples pixels at key positions and determines
        which keys are pressed based on color matching.
        Returns a list of (key_index, keypressed_state, pressedcolor)
        """
        if self.currentImage is None:
            return []

        detected_keys = []

        for i in range(len(self.app.prefs.keys_pos)):
            # Get pixel position in original video for sampling
            pix_pos = self.getkeyp_pixel_pos(self.app.prefs.keys_pos[i][0], self.app.prefs.keys_pos[i][1])
            if pix_pos is None:
                continue

            # Sample the pixel color at key position
            keybgr = self.currentImage[pix_pos[1], pix_pos[0]]
            # Convert numpy values to Python ints to avoid overflow warnings
            key = [int(keybgr[2]), int(keybgr[1]), int(keybgr[0])]  # BGR to RGB

            # Spark-level sampling (for fade detection)
            sparkkey = [0, 0, 0]
            if self.app.prefs.use_sparks:
                sh = max(1, int(self.sparksWindow.sparks_slider_height.value))
                for spark_y_add_pos in range(sh):
                    sparkpixpos = self.getkeyp_pixel_pos(
                        self.app.prefs.keys_pos[i][0],
                        self.app.prefs.keyp_spark_y_pos - spark_y_add_pos
                    )
                    if sparkpixpos is not None:
                        spark_bgr = self.currentImage[sparkpixpos[1], sparkpixpos[0]]
            
                        sparkkey[0] += int(spark_bgr[2])
                        sparkkey[1] += int(spark_bgr[1])
                        sparkkey[2] += int(spark_bgr[0])

                # Convert to int after averaging
                sparkkey = [int(sparkkey[0] / sh), int(sparkkey[1] / sh), int(sparkkey[2] / sh)]

            if i > 144:
                continue

            keypressed = 0
            pressedcolor = [0, 0, 0]

            # === COLOR MATCHING LOGIC ===
            if self.app.prefs.use_alternate_keys:
                # Alternate mode: detect by color CHANGE from baseline
                delta = self.app.prefs.keyp_delta + self.app.prefs.keyp_colors_alternate_sensitivity[i]
                if (abs(key[0] - self.app.prefs.keyp_colors_alternate[i][0]) > delta and
                    abs(key[1] - self.app.prefs.keyp_colors_alternate[i][1]) > delta and
                    abs(key[2] - self.app.prefs.keyp_colors_alternate[i][2]) > delta):
                    keypressed = 1
                    pressedcolor = self.app.prefs.keyp_colors_alternate[i]
            else:
                # Normal mode: match against defined colors
                for key_id in range(len(self.app.prefs.keyp_colors)):
                    keyc = self.app.prefs.keyp_colors[key_id]
                    delta = self.app.prefs.keyp_delta

                    # Per-color sensitivity override
                    if self.app.prefs.use_percolor_delta and key_id < len(self.app.prefs.percolor_delta):
                        delta = self.app.prefs.percolor_delta[key_id]

                    # Skip undefined colors
                    if keyc == [0, 0, 0]:
                        continue

                    # Color match found
                    if (abs(key[0] - keyc[0]) < delta and
                        abs(key[1] - keyc[1]) < delta and
                        abs(key[2] - keyc[2]) < delta):

                        keypressed = 1
                        pressedcolor = keyc
                        self.app.midiHandler.notes_pressed_color[i] = keyc

                        # Spark fade detection (keypressed=2 means sustain/fade)
                        if self.app.prefs.use_sparks:
                            spark_delta = self.app.prefs.keyp_colors_sparks_sensitivity[key_id]
                            has_spark_delta = (
                                (sparkkey[0] - keyc[0]) > spark_delta or
                                (sparkkey[1] - keyc[1]) > spark_delta or
                                (sparkkey[2] - keyc[2]) > spark_delta
                            )
                            if not has_spark_delta:
                                keypressed = 2  # Sustain state

            detected_keys.append((i, keypressed, pressedcolor))

        return detected_keys
    def apply_rollcheck_filter(self, detected_keys):
        """
        Rollcheck: prevents adjacent keys from triggering simultaneously.
        Modifies the detected_keys list in place based on priority rules.
        """
        if not self.app.prefs.rollcheck:
            return

        # Convert to dict for easier manipulation
        notes_tmp = {i: state for i, state, _ in detected_keys}

        for i in range(1, len(self.app.prefs.keys_pos) - 1):
            if i not in notes_tmp:
                continue

            if self.app.prefs.rollcheck_priority == 0:
                # Black keys have priority
                if not self.app.midiHandler.is_black_key(i):
                    if notes_tmp.get(i + 1, 0) > 0:
                        notes_tmp[i] = 0
                    if notes_tmp.get(i - 1, 0) > 0:
                        notes_tmp[i] = 0
            else:
                # White keys have priority
                if self.app.midiHandler.is_black_key(i):
                    if notes_tmp.get(i + 1, 0) > 0:
                        notes_tmp[i] = 0
                    if notes_tmp.get(i - 1, 0) > 0:
                        notes_tmp[i] = 0

        # Update the detected_keys list with filtered results
        for idx, (i, _, color) in enumerate(detected_keys):
            detected_keys[idx] = (i, notes_tmp.get(i, 0), color)

    def draw_key_overlays(self, detected_keys):
        """
        Renders the visual key indicators on top of the video.
        This is the visualization layer - shows boxes, highlights, etc.
        Properly scales and positions keys based on current window size.
        """
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_TEXTURE_2D)

        # Calculate scale factors for key size
        scale_x = self.video_draw_w / self.width
        scale_y = self.video_draw_h / self.height
        scale = min(scale_x, scale_y)  # Use uniform scale for keys

        # Convert detected_keys to dict for easier lookup
        key_states = {i: (state, color) for i, state, color in detected_keys}

        for i in range(len(self.app.prefs.keys_pos)):
            keypressed, pressedcolor = key_states.get(i, (0, [0, 0, 0]))

            # Get screen position for this key
            screen_pos = self.get_key_screen_position(i)
            if screen_pos is None:
                continue
    
            screen_x, screen_y = screen_pos  

            glPushMatrix()
            glTranslatef(screen_x, screen_y, 0)
            
            # Scale the key visualization
            glScalef(scale, scale, 1.0)

            # === DRAW VERTICAL GUIDE LINE ===
            glColor4f(1, 1, 1, 0.5)
            if not self.app.midiHandler.is_black_key(i):
                glColor4f(0.57, 0.57, 0.57, 0.55)
            DrawQuad(-0.5, -self.app.line_height, 0.5, self.app.line_height)

            # === DRAW KEY STATE ===
            if keypressed != 0:
                # PRESSED: Draw colored box
                glColor4f(
                    pressedcolor[0] / 255.0,
                    pressedcolor[1] / 255.0,
                    pressedcolor[2] / 255.0,
                    0.9
                )
                DrawQuad(-6, -7, 6, 7)

                # Draw outline (different size for normal vs sustain)
                glColor4f(0, 0, 0, 1)
                if keypressed == 1:
                    DrawRect(-7, -9, 7, 9, 3)  # Normal press
                else:
                    DrawRect(-5, -7, 5, 7, 3)  # Sustain/fade
            else:
                # UNPRESSED: Draw empty box
                glColor4f(0, 0, 0, 1)
                DrawRect(-7, -7, 7, 7, 1)
                glColor4f(0.5, 1, 1.0, 0.7)
                DrawQuad(-5, -5, 5, 5)

            # === SPECIAL HIGHLIGHTS ===
            
            # Selected key highlight (blue)
            if self.app.lastkeygrabid == i:
                glColor4f(0.0, 0.5, 1.0, 0.7)
                DrawQuad(-4, -4, 4, 4)

            # Separate note channel marker (green)
            if self.app.separate_note_id == i:
                glColor4f(0, 1, 0, 1)
                DrawRect(-7, -12, 7, 12, 2)

            # Base octave marker (red)
            if self.app.prefs.octave * 12 == i:
                glColor4f(1, 0, 0, 1)
                DrawRect(-9, 9, 9, 12, 3)

            # Center dot
            DrawQuad(-1, -1, 1, 1)

            glPopMatrix()

            # === DRAW SPARK INDICATORS ===
            if self.app.prefs.use_sparks:
                # Get spark screen position
                spark_video_x = self.app.prefs.xoffset_whitekeys + self.app.prefs.keys_pos[i][0]
                spark_video_y = self.app.prefs.keyp_spark_y_pos
                spark_screen_x, spark_screen_y = self.video_to_screen_coords(
                    spark_video_x, spark_video_y
                )
                
                glPushMatrix()
                glTranslatef(spark_screen_x, spark_screen_y, 0)
                glScalef(scale, scale, 1.0)
                
                glColor4f(0.5, 1, 1.0, 0.7)
                DrawQuad(-1, -1, 1, 1)  # Spark sampling point
                DrawQuad(-0.5, -self.sparksWindow.sparks_slider_height.value, 0.5, 0)
                glPopMatrix()

        glDisable(GL_BLEND)

    def draw_processing_progress(self, current_frame, total_frames):
        """Draws a progress bar and updates the frame during MIDI reconstruction."""
        # 1. Clear and setup ortho
        # === SETUP ===
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)

        # === DRAW VIDEO BACKGROUND ===
        glEnable(GL_TEXTURE_2D)
        
        glBindTexture(GL_TEXTURE_2D, Gl.bgImgGL)
        glColor4f(1, 1, 1, 1)
        DrawQuad(self.video_offset_x, self.video_offset_y, 
                 self.video_offset_x + self.video_draw_w, 
                 self.video_offset_y + self.video_draw_h)

        # === KEY DETECTION & RENDERING ===
        detected_keys = self.detect_key_presses()
        self.apply_rollcheck_filter(detected_keys)
        
        # Update MIDI handler with current states
        for i, keypressed, _ in detected_keys:
            self.app.midiHandler.notes_tmp[i] = keypressed
        
        # Draw visual overlays
        self.draw_key_overlays(detected_keys)

        # 4. Draw Progress Bar background (Dark Gray)
        bar_height = 20
        glDisable(GL_TEXTURE_2D)
        glColor3f(0.2, 0.2, 0.2)
        DrawQuad(0, self.height - bar_height, self.width, self.height)
    
        # 5. Draw Progress Bar fill (Green)
        progress = current_frame / (total_frames if total_frames > 0 else 1)
        glColor3f(0.0, 0.8, 0.0)
        DrawQuad(0, self.height - bar_height, self.width * progress, self.height)
        
        glEnable(GL_TEXTURE_2D)
        
        # 6. Push to screen
        pygame.display.flip()

    def drawframe(self):
        """Main rendering function - draws everything each frame."""
        if self.currentImage is None:
            return

        # === SETUP ===
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)

        # === DRAW VIDEO BACKGROUND ===
        glEnable(GL_TEXTURE_2D)
        
        glBindTexture(GL_TEXTURE_2D, Gl.bgImgGL)
        glColor4f(1, 1, 1, 1)
        DrawQuad(self.video_offset_x, self.video_offset_y, 
                 self.video_offset_x + self.video_draw_w, 
                 self.video_offset_y + self.video_draw_h)

        # === KEY DETECTION & RENDERING ===
        detected_keys = self.detect_key_presses()
        self.apply_rollcheck_filter(detected_keys)
        
        # Update MIDI handler with current states
        for i, keypressed, _ in detected_keys:
            self.app.midiHandler.notes_tmp[i] = keypressed
        
        # Draw visual overlays
        self.draw_key_overlays(detected_keys)

        # === DRAW UI WINDOWS ===
        for window in self.glwindows:
            window.draw()

        # Draw hints over all windows
        for window in self.glwindows:
            window.drawhint()

        pygame.display.flip()

    # === EVENT HANDLERS ===

    def key_down_event(self, key):
        for window in self.glwindows:
            window.update_key_down(key)

    def mouse_up_event(self, mouse_x, mouse_y, button):
        for i in range(len(self.glwindows) - 1, -1, -1):
            if self.glwindows[i].update_mouse_up(mouse_x, mouse_y, button) == 1:
                break

    def mouse_down_event(self, mouse_x, mouse_y, button):
        resort = False
        for i in range(len(self.glwindows) - 1, -1, -1):
            if self.glwindows[i].update_mouse_down(mouse_x, mouse_y, button) == 1:
                resort = True
                break
        if resort:
            self.glwindows.sort(key=lambda x: x.active, reverse=False)

    def mouse_move(self, mouse_x, mouse_y):
        for wnd in self.glwindows:
            wnd.update_mouse_move(mouse_x, mouse_y)

    def get_colorBtn_list(self):
        return self.colorWindow.colorBtns

    # === UI TOGGLE FUNCTIONS ===

    def draw_toggle_windows(self, sender=None):
        logger.debug("Hide all windows")
        for i in self.glwindows:
            if isinstance(i, GLWindow):
                i.fullhidden = self.ShowHideButton.switch_status

    def toggle_window_button(self):
        self.ShowHideButton.switch_status = not self.ShowHideButton.switch_status

    def toggle_notes_overlap(self):
        self.settingsWindow.notes_overlap_btn.switch_status = (
            not self.settingsWindow.notes_overlap_btn.switch_status
        )

    def toggle_ignore_notes_minimal(self):
        self.settingsWindow.ignore_notes_with_minimal_duration_btn.switch_status = (
            not self.settingsWindow.ignore_notes_with_minimal_duration_btn.switch_status
        )

    # === SETTINGS UPDATE FUNCTIONS ===

    def update_selected_color_delta(self, sender, index):
        self.sparksWindow.selected_color_delta.color = sender.color
        if index < len(self.app.prefs.percolor_delta):
            self.sparksWindow.selected_color_delta.setvalue(self.app.prefs.percolor_delta[index])
            self.sparksWindow.sparks_slider_delta.id = Gl.keyp_colormap_id
            self.sparksWindow.sparks_slider_delta.color = self.app.prefs.keyp_colors[Gl.keyp_colormap_id]
            self.sparksWindow.sparks_slider_delta.setvalue(
                self.app.prefs.keyp_colors_sparks_sensitivity[Gl.keyp_colormap_id]
            )

    def update_color_channels(self, sender):
        i = abs(sender.index) - 1
        if sender.index > 0:
            self.app.prefs.keyp_colors_channel[i] = self.app.prefs.keyp_colors_channel[i] + 1
        else:
            self.app.prefs.keyp_colors_channel[i] = self.app.prefs.keyp_colors_channel[i] - 1
        
        self.app.prefs.keyp_colors_channel[i] = max(0, min(15, self.app.prefs.keyp_colors_channel[i]))
        self.colorWindow.colorBtns_channel_labels[i].text = "Ch:" + str(
            self.app.prefs.keyp_colors_channel[i] + 1
        )

    def update_alternate_label(self):
        self.extraWindow.extra_label1.text = "Use alternate:" + str(
            self.app.prefs.use_alternate_keys
        )

    def update_alternate_sensitivity(self, new_value):
        self.extraWindow.extra_slider1.setvalue(new_value)

    def update_values_from_settings(self):
        """Sync all UI controls with current preference values."""
        if len(self.colorWindow.colorBtns_channel_labels) > 0:
            for i in range(len(self.colorWindow.colorBtns)):
                self.colorWindow.colorBtns_channel_labels[i].text = "Ch:" + str(
                    self.app.prefs.keyp_colors_channel[i] + 1
                )

        self.settingsWindow.key_sensitivity_slider.set_and_callback(self.app.prefs.keyp_delta)
        self.settingsWindow.minimal_duration_slider.set_and_callback(
            self.app.prefs.minimal_duration * 100
        )
        self.settingsWindow.tempo_slider.set_and_callback(self.app.prefs.tempo)
        self.settingsWindow.key_count_slider.set_and_callback(self.app.prefs.keys_pos_cnt)
        self.settingsWindow.rollcheck_button.switch_status = self.app.prefs.rollcheck
        self.settingsWindow.rollcheck_priority_button.switch_status = (
            self.app.prefs.rollcheck_priority
        )
        self.settingsWindow.notes_overlap_btn.switch_status = self.app.prefs.notes_overlap
        self.settingsWindow.ignore_notes_with_minimal_duration_btn.switch_status = (
            self.app.prefs.ignore_minimal_duration
        )

        self.sparksWindow.use_percolor_delta.switch_status = self.app.prefs.use_percolor_delta
        self.sparksWindow.sparks_switch.switch_status = self.app.prefs.use_sparks
        self.sparksWindow.sparks_slider_delta.value = 0
        self.sparksWindow.sparks_slider_delta.id = -1