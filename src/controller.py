from src.prefs import prefs
import src.settings as settings
from src.models.video_io import VideoHandler
from src.cli import get_video_filepath, get_ini_filepath
from src.views.ui import MainWindow
from src.models.midi_proc import MidiHandler

import logging

logger = logging.getLogger(__name__)

import math
import ntpath

import pygame

from enum import IntEnum

class DragMode(IntEnum):
    IDLE = 0
    DRAG_SINGLE = 1
    DRAG_ALL = 2


class AppController:
    def __init__(self):

        self.prefs = prefs

        self.use_snap_notes_to_grid = False
        self.notes_grid_size = 32

        self.file_path = get_video_filepath()

        self.settings_file = self.file_path + ".ini"
        self.ini_file = get_ini_filepath()

        self.use_snap_notes_to_grid = False
        self.line_height = 20

        self.video = VideoHandler(self.file_path)
        self.app_view = MainWindow(
            self, self.file_path, self.video.get_image(0)
        )

        self.end_frame = self.video.length
        self.running = True
        self.debug_keys = False

        self.midi_handler = MidiHandler()

        self.key_grab = DragMode.IDLE
        self.key_grab_id = -1
        self.key_grab_add_x = 0 

        self.last_key_grab_id = -1
        self.printed_for_frame = 0

        self.separate_note_id = -1

    def start(self):
        self.load_settings(self.ini_file)
        if prefs.end_frame <= prefs.start_frame:
            prefs.end_frame = self.video.length

        while self.running:
            self.handle_events()
            self.app_view.draw_frame()

    # === INPUT HANDLE ===
    def handle_events(self):
        """Process inputs from mouse and keyboard using PyGame."""
        mouse_x, mouse_y = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                quit()
            elif event.type == pygame.VIDEORESIZE:
                prefs.resize = 1
                prefs.resize_width = event.w
                prefs.resize_height = event.h
                self.app_view.reshape(event.w, event.h)
            elif event.type == pygame.KEYDOWN:
                self.keyboard_event(event.key)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.app_view.mouse_up_event(mouse_x, mouse_y, event.button)

                if event.button == pygame.BUTTON_LEFT:
                    self.key_grab = DragMode.IDLE
                    self.key_grab_id = -1
                if event.button == pygame.BUTTON_RIGHT:
                    self.key_grab = DragMode.IDLE

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_event(event.button)

            # === KEY DRAGGING LOGIC ===
            if (self.key_grab == DragMode.DRAG_SINGLE) and (self.key_grab_id > -1):
                # Convert screen mouse position to video space
                video_x, video_y = self.app_view.screen_to_video_coords(mouse_x, mouse_y)
                
                # Update key position in video space
                prefs.keys_pos[self.key_grab_id][0] = int(video_x - prefs.x_offset_whitekeys)
                prefs.keys_pos[self.key_grab_id][1] = int(video_y - prefs.y_offset_whitekeys)
                
            if self.key_grab == DragMode.DRAG_ALL:
                # Convert screen mouse position to video space for offset dragging
                video_x, video_y = self.app_view.screen_to_video_coords(mouse_x, mouse_y)
                
                prefs.x_offset_whitekeys = int(video_x - self.key_grab_add_x)
                prefs.y_offset_whitekeys = int(video_y)

            self.app_view.mouse_move(mouse_x, mouse_y)

    def keyboard_event(self, key):
        """Handle inputs from keyboard"""
        mods = pygame.key.get_mods()
        mouse_x, mouse_y = pygame.mouse.get_pos()

        self.app_view.key_down_event(key)

        if key == pygame.K_q:
            if prefs.autoclose == 1:
                self.running = False
            else:
                # reconstruct()
                pass

        if key == pygame.K_o:
            # notes overlap
            self.switch_notes_overlap(None)

        if key == pygame.K_i:
            # ignore notes with minimal duration
            self.switch_ignore_notes_with_minimal_duration(None)

        if key == pygame.K_s:
            # set start frame
            if mods & pygame.KMOD_SHIFT:
                prefs.start_frame = 0
            else:
                prefs.start_frame = self.video.get_current_frame_int()
                logger.debug("set start frame = " + str(prefs.start_frame))

        if key == pygame.K_e:
            # set end frame
            if mods & pygame.KMOD_SHIFT:
                self.end_frame = self.video.length
            else:
                self.end_frame = self.video.get_current_frame_int()
                logger.debug("set end frame = " + str(self.end_frame))

        if key == pygame.K_ESCAPE:
            # quit
            self.running = False
            pygame.quit()
            quit()

        if key == pygame.K_F2:
            self.btndown_save_settings(None)

        if key == pygame.K_F3:
            self.btndown_load_settings(None)

        # center windows to mouse cursor
        # if key == pygame.K_F4:
        #   for i in range(len(glwindows)):
        #       glwindows[i].x = mouse_x
        #       glwindows[i].y = mouse_y

        if key == pygame.K_r:
            self.switch_resize_windows(None)

        if key == pygame.K_RIGHTBRACKET:
            self.raise_octave()

        if key == pygame.K_LEFTBRACKET:
            self.lower_octave()

        if key == pygame.K_PLUS or key == pygame.K_KP_PLUS or key == pygame.K_EQUALS:
            prefs.keys_angle -= 5
            self.midi_handler.update_key_positions()

        if key == pygame.K_MINUS or key == pygame.K_KP_MINUS:
            prefs.keys_angle += 5
            self.midi_handler.update_key_positions()

        if key == pygame.K_UP:
            if mods & pygame.KMOD_ALT:
                prefs.keyp_spark_y_pos -= 1

            else:
                if mods & pygame.KMOD_SHIFT:
                    prefs.yoffset_blackkeys -= 1
                else:
                    prefs.yoffset_blackkeys -= 2
                self.midi_handler.update_key_positions()

        if key == pygame.K_DOWN:
            if mods & pygame.KMOD_ALT:
                prefs.keyp_spark_y_pos += 1
            else:
                if mods & pygame.KMOD_SHIFT:
                    prefs.yoffset_blackkeys += 1
                else:
                    prefs.yoffset_blackkeys += 2
                self.midi_handler.update_key_positions()

        if key == pygame.K_TAB:
            self.show_or_hide_all_windows(None)

        if key == pygame.K_LEFT:
            if mods & pygame.KMOD_SHIFT:
                prefs.white_key_width -= 0.1
            else:
                prefs.white_key_width -= 1.0
            self.midi_handler.update_key_positions()

        if key == pygame.K_RIGHT:
            if mods & pygame.KMOD_SHIFT:
                prefs.white_key_width += 0.1
            else:
                prefs.white_key_width += 1.0
            self.midi_handler.update_key_positions()

        if key == pygame.K_HOME:
            self.scroll_to_start(None)

        if key == pygame.K_END:
            self.scroll_to_end(None)

        if key == pygame.K_0:
            if mods & pygame.KMOD_CTRL:
                self.app_view.reset_color_picker()


        # if key == pygame.K_PAGEUP:
        #     if mods & pygame.KMOD_SHIFT:
        #         scroll_forward_by_frame(None)
        #     else:
        #         scroll_fast_forward(None)

        # if key == pygame.K_PAGEDOWN:
        #     if mods & pygame.KMOD_SHIFT:
        #         scroll_prev_by_frame(None)
        #     else:
        #         scroll_fast_prev(None)

        if key == pygame.K_p:
            size = 5
            self.separate_note_id = -1
            
            for i in range(len(prefs.keys_pos)):
                # Get screen position for hit testing
                screen_pos = self.app_view.get_key_screen_position(i)
                if screen_pos is None:
                    continue

                key_screen_x, key_screen_y = screen_pos
                    
                if abs(mouse_x - key_screen_x) < size and abs(mouse_y - key_screen_y) < size:
                    self.separate_note_id = i
                    logger.debug(f"Marked key {i} for channel separation")
                    break

        if key == pygame.K_KP4:
            if self.last_key_grab_id > 0 and self.last_key_grab_id < len(prefs.keys_pos):
                prefs.keys_pos[self.last_key_grab_id][0] -= 1
            
        if key == pygame.K_KP6:
            if self.last_key_grab_id > 0 and self.last_key_grab_id < len(prefs.keys_pos):
                prefs.keys_pos[self.last_key_grab_id][0] += 1
                
        if key == pygame.K_KP8:
            if self.last_key_grab_id > 0 and self.last_key_grab_id < len(prefs.keys_pos):
                prefs.keys_pos[self.last_key_grab_id][1] -= 1
                
        if key == pygame.K_KP2:
            if self.last_key_grab_id > 0 and self.last_key_grab_id < len(prefs.keys_pos):
                prefs.keys_pos[self.last_key_grab_id][1] += 1

        # if key == pygame.K_KP1:
        #     vertical_align_keys(1, 1)
        # if key == pygame.K_KP3:
        #     vertical_align_keys(1, 0)

    def mouse_event(self, button):
        """Handle inputs from mouse (excluding movement)"""
        mods = pygame.key.get_mods()
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.app_view.mouse_down_event(mouse_x, mouse_y, button)

        # Handle Mouse Wheel (Scale white key width)
        if button in (pygame.BUTTON_WHEELUP, pygame.BUTTON_WHEELDOWN):
            adjustment = 0.05 if button == pygame.BUTTON_WHEELUP else -0.05

            prefs.white_key_width += adjustment
            self.midi_handler.update_key_positions()
            return

        # Perform Hit Test for Left/Right clicks
        key_id = self._get_key_at_mouse(mouse_x, mouse_y)

        if button == pygame.BUTTON_LEFT:
            if mods & pygame.KMOD_CTRL:
                self.last_key_grab_id = -1
                self.app_view.color_picker(mouse_x, mouse_y)
            
            if key_id is not None:
                self.key_grab = DragMode.DRAG_SINGLE
                if not (mods & pygame.KMOD_CTRL):
                    self.key_grab_id = key_id
                
                self.last_key_grab_id = key_id
                self.app_view.update_alternate_sensitivity(
                    prefs.keyp_colors_alternate_sensitivity[key_id]
                )
                logger.debug(f"Grabbed key: {key_id}")

        elif button == pygame.BUTTON_RIGHT:
            self.key_grab = DragMode.DRAG_ALL
            self.key_grab_add_x = 0
            
            if key_id is not None:
                self.key_grab_add_x = prefs.keys_pos[key_id][0]
                logger.debug(f"Right-click grabbed key: {key_id}")

    def _get_key_at_mouse(self, mouse_x, mouse_y, hitbox=5):
        """Returns the key_id if found within the hitbox, otherwise None."""
        for key_id in range(len(prefs.keys_pos)):
            screen_pos = self.app_view.get_key_screen_position(key_id)
            
            # Standardized check for invalid/off-screen positions
            if screen_pos is None or screen_pos[0] == -1:
                continue
                
            kx, ky = screen_pos
            if abs(mouse_x - kx) < hitbox and abs(mouse_y - ky) < hitbox:
                return key_id
        return None
    

    def start_recreate_midi(self, sender):
        if prefs.autoclose is True:
            self.running = False
        else:
            self.reconstruct()

    def reconstruct(self):
        """Wrapper for MIDI reconstruction process"""
        import time
        
        self.app_view.helpWindow.hidden = True
        t1 = time.time()
        
        status = self.midi_handler.process_midi(self)
        
        t2 = time.time()
        logger.info(f"Processing time: {t2 - t1:.2f} seconds")
        
        # Reset to start frame
        self.app_view.load_image(self.video.get_image(prefs.start_frame))
        
        return status

    def load_settings(self, config_file: str):
        settings.loadsettings(config_file)
        settings.compatibleColors(self.app_view.get_colorBtn_list())

        self.app_view.load_image(self.video.get_image(prefs.start_frame))
        self.app_view.update_values_from_settings()
        self.app_view.resize_window()

# === UI LINK ===
    def show_or_hide_all_windows(self, sender=None):
        if sender is None:
            self.app_view.toggle_window_button()

        self.app_view.draw_toggle_windows()

    def set_start_frame_to_current_frame(self, sender):
        prefs.start_frame = self.video.get_current_frame_int()
        logger.debug(f"set start frame = {prefs.start_frame}")

    def set_end_frame_to_current_frame(self, sender):
        prefs.end_frame = self.video.get_current_frame_int()
        logger.debug(f"set end frame = {prefs.end_frame}")

    def switch_notes_overlap(self, sender):
        if sender is None:
            self.app_view.toggle_notes_overlap()
        prefs.notes_overlap = not prefs.notes_overlap

    def switch_ignore_notes_with_minimal_duration(self, sender=None):
        if sender is None:        
            self.app_view.toggle_ignore_notes_minimal()
        prefs.ignore_minimal_duration = not prefs.ignore_minimal_duration

    def switch_sync_notes_start_pos(self,sender):
        prefs.sync_notes_start_pos = sender.switch_status

    def switch_resize_windows(self, sender):
        prefs.resize = not prefs.resize
        self.app_view.resize_window()

    def change_autoclose(self,sender):
        prefs.autoclose = sender.switch_status

    def btndown_save_settings(self, sender):
        settings.savesettings(self.settings_file)

    def btndown_load_settings(self, sender):
        old_resize = prefs.resize
        self.load_settings(self.settings_file)

        self.app_view.update_alternate_label()
        if prefs.resize != old_resize:
            self.app_view.resize_window()

    def change_rollcheck(self, sender):
        prefs.rollcheck = sender.switch_status

    def change_rollcheck_priority(self,sender):
        prefs.rollcheck_priority = sender.switch_status

    def change_save_to_disk_per_channel(self,sender):
        prefs.save_to_disk_per_channel = sender.switch_status

    def raise_octave(self, *args):
        prefs.octave += 1
        if prefs.octave > 7:
            prefs.octave = 7
        self.midi_handler.basenote = prefs.octave * 12

    def lower_octave(self, *args):
        prefs.octave -= 1
        if prefs.octave < 0:
            prefs.octave = 0
        self.midi_handler.basenote = prefs.octave * 12

    def scroll_by_steps(self, steps):
        currentFrame = self.video.get_current_frame_int() - 1  + steps

        if currentFrame > self.video.length * 0.99:
            currentFrame = math.trunc(self.video.length * 0.99)

        if currentFrame < 1:
            currentFrame = 1

        self.app_view.load_image(self.video.get_image(currentFrame))

    def scroll_forward_by_frame(self, sender):
        self.scroll_by_steps(1)

    def scroll_fast_forward(self, sender):
        self.scroll_by_steps(100)

    def scroll_prev_by_frame(self, sender):
        self.scroll_by_steps(-1)

    def scroll_fast_prev(self, sender):
        self.scroll_by_steps(-100)

    def scroll_to_start(self, sender):
        currentFrame = 0
        self.app_view.load_image(self.video.get_image(currentFrame))

    def scroll_to_end(self, sender):
        currentFrame = self.video.length - 100
        self.app_view.load_image(self.video.get_image(currentFrame))

    def rotate_clockwise(self,sender):
        prefs.keys_angle -= 5
        self.midi_handler.update_key_positions()

    def rotate_counter_clockwise(self,sender):
        prefs.keys_angle += 5
        self.midi_handler.update_key_positions()

    def change_key_count(self,sender):
        logger.debug("change count")
        self.midi_handler.update_key_positions(True)

    def vertical_align_keys(self, separate_black_keys=1, align=1):
        logger.debug(f"lastkeygrabid {self.last_key_grab_id}")
        if self.last_key_grab_id < 0 or self.last_key_grab_id > len(prefs.keys_pos):
            return

        y = prefs.keys_pos[self.last_key_grab_id][align]
        selected_black_key = self.midi_handler.is_black_key(self.last_key_grab_id)

        for idx in range(len(prefs.keys_pos)):
            if separate_black_keys == 1:
                if selected_black_key:
                    if self.midi_handler.is_black_key(idx):
                        prefs.keys_pos[idx][align] = y
                else:
                    if not self.midi_handler.is_black_key(idx):
                        prefs.keys_pos[idx][align] = y
            else:
                prefs.keys_pos[idx][align] = y

    def btndown_vertical_align_keys(self, sender):
        self.vertical_align_keys(align=1)

    def btndown_halign_align_keys(self, sender):
        self.vertical_align_keys(align=0)

    def update_keys_pos_count(self, sender, value):
        prefs.keys_pos_cnt = int(value)

    def update_black_key_relative_position(self, sender, value):
        prefs.black_key_relative_position = value * 0.001
        self.midi_handler.update_key_positions()

    def update_sync_notes_start_pos_time_delta(self,sender, value):
        prefs.sync_notes_start_pos_time_delta = value * 0.001

    def on_pallete_click(self, sender, index):
        self.app_view.update_selected_color_delta(sender, index)

    def update_channels(self, sender):
        logger.debug("update_channels..." + str(sender.index))
        self.app_view.update_color_channels(sender)
        

    def disable_color(self, sender):
        logger.debug("disabled color..." + str(sender.index))
        if sender.index < len(prefs.keyp_colors):
            prefs.keyp_colors[sender.index] = [0, 0, 0]
        #   prefs.keyp_colors_channel[i]= prefs.keyp_colors_channel[i] + 1

    def read_key_color(self, i):
        pix_x = int(prefs.x_offset_whitekeys + prefs.keys_pos[i][0])
        pix_y = int(prefs.y_offset_whitekeys + prefs.keys_pos[i][1])

        if (
            (pix_x >= self.app_view.width)
            or (pix_y >= self.app_view.height)
            or (pix_x < 0)
            or (pix_y < 0)
        ):
            return
        if prefs.resize == True:
            pix_x = int(
                round(pix_x * (self.video.video_width / float(prefs.resize_width)))
            )
            pix_y = int(
                round(pix_y * (self.video.video_height / float(prefs.resize_height)))
            )
            if pix_x > self.video.video_width - 1:
                pix_x = self.video.video_width - 1
            if pix_y > self.video.video_height - 1:
                pix_y = self.video.video_height - 1

        key_BGR = self.video.image[pix_y, pix_x]
        key = [key_BGR[2], key_BGR[1], key_BGR[0]]

        prefs.keyp_colors_alternate[i] = key

    def read_colors(self, sender):
        for i in range(len(prefs.keys_pos)):
            self.read_key_color(i)

    def update_color(self, sender):
        if self.last_key_grab_id != -1:
            self.read_key_color(self.last_key_grab_id)

    def change_use_alternate_keys(self, sender):
        prefs.use_alternate_keys = not prefs.use_alternate_keys
        self.app_view.update_alternate_label()

    def snap_notes_to_the_grid(self, sender):
        global use_snap_notes_to_grid
        use_snap_notes_to_grid = sender.switch_status

    def update_alternate_sensitivity(self, sender, value):
        if self.last_key_grab_id != -1:
            prefs.keyp_colors_alternate_sensitivity[self.last_key_grab_id] = value

    def change_use_sparks(self, sender):
        prefs.use_sparks = sender.switch_status

    #   sender.text = "use sparks:"+str(use_sparks)

    def update_sparks_y_pos(self, sender):
        if sender.text == "y+":
            prefs.keyp_spark_y_pos = prefs.keyp_spark_y_pos - 1
        else:
            prefs.keyp_spark_y_pos = prefs.keyp_spark_y_pos + 1

    def update_sparks_delta(self, sender, value):
        if sender.id == -1:
            return
        if sender.id < len(prefs.keyp_colors):
            prefs.keyp_colors_sparks_sensitivity[sender.id] = sender.value
            # print("keyp_colors_sparks_sensitivity["+str(sender.id)+"] = "+ str(sender.value) )

    def change_use_percolor_delta(self, sender):
        prefs.use_percolor_delta = sender.switch_status

    def update_percolor_delta(self, sender, value):
        if Gl.keyp_colormap_id == -1:
            return
        if Gl.keyp_colormap_id < len(prefs.percolor_delta):
            prefs.percolor_delta[Gl.keyp_colormap_id] = sender.value
            # print("changed percolor delta for color with id ["+str(sender.id)+"] = "+ str(sender.value) )

    def update_line_height(self, sender, value):
        self.line_height = value