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


class AppController:
    def __init__(self):

        self.prefs = prefs

        self.use_snap_notes_to_grid = False
        self.notes_grid_size = 32
        self.showoutputpath = 0  # Timestamp for showing output message

        self.filepath = get_video_filepath()

        self.outputmid = ntpath.basename(self.filepath) + "_output.mid"
        self.settingsfile = self.filepath + ".ini"
        self.inifile = get_ini_filepath()

        self.use_snap_notes_to_grid = False
        self.line_height = 20

        self.video = VideoHandler(self.filepath)
        self.appView = MainWindow(
            self, self.filepath, self.video.get_image(0)
        )

        self.endframe = self.video.length
        self.running = True
        self.debug_keys = False

        self.midiHandler = MidiHandler()

        self.keygrab = 0
        self.keygrabid = -1
        self.keygrabaddx = 0 

        self.lastkeygrabid = -1
        self.printed_for_frame = 0

        self.separate_note_id = -1

    def start(self):
        self.loadsettings(self.inifile)
        if prefs.endframe <= prefs.startframe:
            prefs.endframe = self.video.length

        while self.running:
            self.handle_events()
            self.appView.drawframe()

    def handle_events(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mods = pygame.key.get_mods()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                quit()
            elif event.type == pygame.VIDEORESIZE:
                prefs.resize = 1
                prefs.resize_width = event.w
                prefs.resize_height = event.h
                self.appView.reshape(event.w, event.h)
            elif event.type == pygame.KEYDOWN:
                self.keyboard_event(event.key)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.appView.mouse_up_event(mouse_x, mouse_y, event.button)

                if event.button == 1:
                    self.keygrab = 0
                    self.keygrabid = -1
                if event.button == 3:
                    self.keygrab = 0

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_click_event(event.button)

            # === KEY DRAGGING LOGIC (FIXED) ===
            if (self.keygrab == 1) and (self.keygrabid > -1):
                # Convert screen mouse position to video space
                video_x, video_y = self.appView.screen_to_video_coords(mouse_x, mouse_y)
                
                # Update key position in video space
                prefs.keys_pos[self.keygrabid][0] = int(video_x - prefs.xoffset_whitekeys)
                prefs.keys_pos[self.keygrabid][1] = int(video_y - prefs.yoffset_whitekeys)
                
            if self.keygrab == 2:
                # Convert screen mouse position to video space for offset dragging
                video_x, video_y = self.appView.screen_to_video_coords(mouse_x, mouse_y)
                
                prefs.xoffset_whitekeys = int(video_x - self.keygrabaddx)
                prefs.yoffset_whitekeys = int(video_y)

            self.appView.mouse_move(mouse_x, mouse_y)

    def keyboard_event(self, key):
        mods = pygame.key.get_mods()
        mouse_x, mouse_y = pygame.mouse.get_pos()

        self.appView.key_down_event(key)

        if key == pygame.K_q:
            if prefs.autoclose == 1:
                self.running = False
            else:
                # reconstruct()
                pass

        if key == pygame.K_o:
            # prefs.notes_overlap = not prefs.notes_overlap
            self.switch_notes_overlap(None)

        if key == pygame.K_i:
            # prefs.ignore_minimal_duration = not prefs.ignore_minimal_duration
            self.switch_ignore_notes_with_minimal_duration(None)

        if key == pygame.K_s:
            if mods & pygame.KMOD_SHIFT:
                prefs.startframe = 0
            else:
                prefs.startframe = self.video.get_current_frame_int()
                logger.debug("set start frame = " + str(prefs.startframe))

        if key == pygame.K_e:
            if mods & pygame.KMOD_SHIFT:
                self.endframe = self.video.length
            else:
                self.endframe = self.video.get_current_frame_int()
                logger.debug("set end frame = " + str(self.endframe))

        if key == pygame.K_ESCAPE:
            self.running = False
            pygame.quit()
            quit()

        if key == pygame.K_F2:
            self.btndown_save_settings(None)

        if key == pygame.K_F3:
            self.btndown_load_settings(None)

        # center windows to mouse cursor
        # if key == pygame.K_F4:
        # for i in range(len(glwindows)):
        # glwindows[i].x = mouse_x
        # glwindows[i].y = mouse_y

        if key == pygame.K_r:
            self.switch_resize_windows(None)

        if key == pygame.K_RIGHTBRACKET:
            self.raise_octave()

        if key == pygame.K_LEFTBRACKET:
            self.lower_octave()

        if key == pygame.K_PLUS or key == pygame.K_KP_PLUS or key == pygame.K_EQUALS:
            prefs.keys_angle -= 5
            self.midiHandler.update_key_positions()

        if key == pygame.K_MINUS or key == pygame.K_KP_MINUS:
            prefs.keys_angle += 5
            self.midiHandler.update_key_positions()

        if key == pygame.K_UP:
            if mods & pygame.KMOD_ALT:
                prefs.keyp_spark_y_pos -= 1

            else:
                if mods & pygame.KMOD_SHIFT:
                    prefs.yoffset_blackkeys -= 1
                else:
                    prefs.yoffset_blackkeys -= 2
                self.midiHandler.update_key_positions()

        if key == pygame.K_DOWN:
            if mods & pygame.KMOD_ALT:
                prefs.keyp_spark_y_pos += 1
            else:
                if mods & pygame.KMOD_SHIFT:
                    prefs.yoffset_blackkeys += 1
                else:
                    prefs.yoffset_blackkeys += 2
                self.midiHandler.update_key_positions()

        if key == pygame.K_TAB:
            self.show_or_hide_all_windows(None)

        if key == pygame.K_LEFT:
            if mods & pygame.KMOD_SHIFT:
                prefs.whitekey_width -= 0.1
            else:
                prefs.whitekey_width -= 1.0
            self.midiHandler.update_key_positions()

        if key == pygame.K_RIGHT:
            if mods & pygame.KMOD_SHIFT:
                prefs.whitekey_width += 0.1
            else:
                prefs.whitekey_width += 1.0
            self.midiHandler.update_key_positions()

        if key == pygame.K_HOME:
            self.scroll_to_start(None)

        if key == pygame.K_END:
            self.scroll_to_end(None)

        if key == pygame.K_0:
            if mods & pygame.KMOD_CTRL and Gl.keyp_colormap_id != -1:
                prefs.keyp_colors[Gl.keyp_colormap_id][0] = 0
                prefs.keyp_colors[Gl.keyp_colormap_id][1] = 0
                prefs.keyp_colors[Gl.keyp_colormap_id][2] = 0

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
                screen_pos = self.appView.get_key_screen_position(i)
                if screen_pos is None:
                    continue

                key_screen_x, key_screen_y = screen_pos
                    
                if abs(mouse_x - key_screen_x) < size and abs(mouse_y - key_screen_y) < size:
                    self.separate_note_id = i
                    logger.debug(f"Marked key {i} for channel separation")
                    break

        if key == pygame.K_KP4:
            if self.lastkeygrabid > 0 and self.lastkeygrabid < len(prefs.keys_pos):
                prefs.keys_pos[self.lastkeygrabid][0] -= 1
            
        if key == pygame.K_KP6:
            if self.lastkeygrabid > 0 and self.lastkeygrabid < len(prefs.keys_pos):
                prefs.keys_pos[self.lastkeygrabid][0] += 1
                
        if key == pygame.K_KP8:
            if self.lastkeygrabid > 0 and self.lastkeygrabid < len(prefs.keys_pos):
                prefs.keys_pos[self.lastkeygrabid][1] -= 1
                
        if key == pygame.K_KP2:
            if self.lastkeygrabid > 0 and self.lastkeygrabid < len(prefs.keys_pos):
                prefs.keys_pos[self.lastkeygrabid][1] += 1

        # if key == pygame.K_KP1:
        #     vertical_align_keys(1, 1)
        # if key == pygame.K_KP3:
        #     vertical_align_keys(1, 0)

    def mouse_click_event(self, button):
        mods = pygame.key.get_mods()
        mouse_x, mouse_y = pygame.mouse.get_pos()

        self.appView.mouse_down_event(mouse_x, mouse_y, button)
        
        if button == 4:
            prefs.whitekey_width += 0.05
            self.midiHandler.update_key_positions()
            
        if button == 5:
            prefs.whitekey_width -= 0.05
            self.midiHandler.update_key_positions()
            
        if button == 1:
            if mods & pygame.KMOD_CTRL and Gl.keyp_colormap_id != -1:
                # Convert screen coordinates to video coordinates for color picking
                video_x, video_y = self.appView.screen_to_video_coords(mouse_x, mouse_y)
                
                # Bounds check
                if 0 <= video_x < self.video.video_width and 0 <= video_y < self.video.video_height:
                    pix_x = int(video_x)
                    pix_y = int(video_y)
                    
                    key_BGR = self.video.image[pix_y, pix_x]
                    prefs.keyp_colors[Gl.keyp_colormap_id][0] = key_BGR[2]
                    prefs.keyp_colors[Gl.keyp_colormap_id][1] = key_BGR[1]
                    prefs.keyp_colors[Gl.keyp_colormap_id][2] = key_BGR[0]
            
            # Key grabbing logic - now uses screen positions for hit testing
            size = 5
            if mods & pygame.KMOD_CTRL:
                self.lastkeygrabid = -1
                
            for i in range(len(prefs.keys_pos)):
                # Get screen position of this key for hit testing
                screen_pos = self.appView.get_key_screen_position(i)
                if screen_pos is None:
                    continue
                    
                key_screen_x, key_screen_y = screen_pos
                    
                # Check if mouse is near this key (in screen space)
                if abs(mouse_x - key_screen_x) < size and abs(mouse_y - key_screen_y) < size:
                    self.keygrab = 1
                    if not (mods & pygame.KMOD_CTRL):
                        self.keygrabid = i
                    self.lastkeygrabid = i
                    self.appView.update_alternate_sensitivity(
                        prefs.keyp_colors_alternate_sensitivity[i]
                    )
                    logger.debug(f"Grabbed key: {i}")
                    break
                    
        if button == 3:
            self.keygrab = 2
            size = 5
            logger.debug(
                f"x offset {prefs.xoffset_whitekeys} y offset: {prefs.yoffset_whitekeys}"
            )
            
            # Convert mouse to video space to get the grab offset
            video_x, video_y = self.appView.screen_to_video_coords(mouse_x, mouse_y)
            self.keygrabaddx = 0
            
            for i in range(len(prefs.keys_pos)):
                # Get screen position for hit testing
                key_screen_x, key_screen_y = self.appView.get_key_screen_position(i)
                
                if key_screen_x == -1:
                    continue
                    
                if abs(mouse_x - key_screen_x) < size and abs(mouse_y - key_screen_y) < size:
                    self.keygrab = 2
                    # Store the offset in video space
                    self.keygrabaddx = prefs.keys_pos[i][0]
                    logger.debug(f"Right-click grabbed key: {i}")
                    break
    
    def loadsettings(self, cfgfile: str):
        settings.loadsettings(cfgfile)
        settings.compatibleColors(self.appView.get_colorBtn_list())

        self.appView.loadImage(self.video.get_image(prefs.startframe))
        self.appView.update_values_from_settings()
        self.appView.resize_window()

    def start_recreate_midi(self, sender):
        if prefs.autoclose is True:
            self.running = False
        else:
            self.reconstruct()

    def reconstruct(self):
        """Wrapper for MIDI reconstruction process"""
        import time
        
        self.appView.helpWindow.hidden = True
        t1 = time.time()
        
        status = self.midiHandler.process_midi(self)
        
        t2 = time.time()
        logger.info(f"Processing time: {t2 - t1:.2f} seconds")
        
        # Reset to start frame
        self.appView.loadImage(self.video.get_image(prefs.startframe))
        
        # Show output message for 5 seconds
        self.showoutputpath = time.time() + 5
        
        return status


# === UI link ===
    def show_or_hide_all_windows(self, sender=None):
        if sender is None:
            self.appView.toggle_window_button()

        self.appView.draw_toggle_windows()

    def set_start_frame_to_current_frame(self, sender):
        prefs.startframe = self.video.get_current_frame_int()
        logger.debug(f"set start frame = {prefs.startframe}")

    def set_end_frame_to_current_frame(self, sender):
        prefs.endframe = self.video.get_current_frame_int()
        logger.debug(f"set end frame = {prefs.endframe}")

    def switch_notes_overlap(self, sender):
        if sender is None:
            self.appView.toggle_notes_overlap()
        prefs.notes_overlap = not prefs.notes_overlap

    def switch_ignore_notes_with_minimal_duration(self, sender=None):
        if sender is None:        
            self.appView.toggle_ignore_notes_minimal()
        prefs.ignore_minimal_duration = not prefs.ignore_minimal_duration

    def switch_sync_notes_start_pos(self,sender):
        prefs.sync_notes_start_pos = sender.switch_status

    def switch_resize_windows(self, sender):
        prefs.resize = not prefs.resize
        self.appView.resize_window()

    def change_autoclose(self,sender):
        prefs.autoclose = sender.switch_status

    def btndown_save_settings(self, sender):
        settings.savesettings(self.settingsfile)

    def btndown_load_settings(self, sender):
        old_resize = prefs.resize
        self.loadsettings(self.settingsfile)

        self.appView.update_alternate_label()
        if prefs.resize != old_resize:
            self.appView.resize_window()

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
        self.midiHandler.basenote = prefs.octave * 12

    def lower_octave(self, *args):
        prefs.octave -= 1
        if prefs.octave < 0:
            prefs.octave = 0
        self.midiHandler.basenote = prefs.octave * 12

    def scroll_by_steps(self, steps):
        currentFrame = self.video.get_current_frame_int() - 1  + steps

        if currentFrame > self.video.length * 0.99:
            currentFrame = math.trunc(self.video.length * 0.99)

        if currentFrame < 1:
            currentFrame = 1

        self.appView.loadImage(self.video.get_image(currentFrame))

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
        self.appView.loadImage(self.video.get_image(currentFrame))

    def scroll_to_end(self, sender):
        currentFrame = self.video.length - 100
        self.appView.loadImage(self.video.get_image(currentFrame))

    def rotate_cw(self,sender):
        prefs.keys_angle -= 5
        self.midiHandler.update_key_positions()

    def rotate_ccw(self,sender):
        prefs.keys_angle += 5
        self.midiHandler.update_key_positions()

    def change_cnt(self,sender):
        logger.debug("change count")
        self.midiHandler.update_key_positions(True)

    def vertical_align_keys(self, separate_black_keys=1, align=1):
        logger.debug(f"lastkeygrabid {self.lastkeygrabid}")
        if self.lastkeygrabid < 0 or self.lastkeygrabid > len(prefs.keys_pos):
            return

        y = prefs.keys_pos[self.lastkeygrabid][align]
        selected_black_key = self.midiHandler.is_black_key(self.lastkeygrabid)

        for idx in range(len(prefs.keys_pos)):
            if separate_black_keys == 1:
                if selected_black_key:
                    if self.midiHandler.is_black_key(idx):
                        prefs.keys_pos[idx][align] = y
                else:
                    if not self.midiHandler.is_black_key(idx):
                        prefs.keys_pos[idx][align] = y
            else:
                prefs.keys_pos[idx][align] = y

    def valign(self, sender):
        self.vertical_align_keys(align=1)

    def halign(self, sender):
        self.vertical_align_keys(align=0)

    def update_keys_pos_cnt(self, sender, value):
        prefs.keys_pos_cnt = int(value)

    def update_blackkey_relative_position(self, sender, value):
        prefs.blackkey_relative_position = value * 0.001
        self.midiHandler.update_key_positions()

    def update_sync_notes_start_pos_time_delta(self,sender, value):
        prefs.sync_notes_start_pos_time_delta = value * 0.001

    def onPallete_click(self, sender, index):
        self.appView.update_selected_color_delta(sender, index)

    def update_channels(self, sender):
        logger.debug("update_channels..." + str(sender.index))
        self.appView.update_color_channels(self, sender)
        

    def disable_color(self, sender):
        logger.debug("disabled color..." + str(sender.index))
        if sender.index < len(prefs.keyp_colors):
            prefs.keyp_colors[sender.index] = [0, 0, 0]
        #   prefs.keyp_colors_channel[i]= prefs.keyp_colors_channel[i] + 1

    def readkeycolor(self, i):
        pix_x = int(prefs.xoffset_whitekeys + prefs.keys_pos[i][0])
        pix_y = int(prefs.yoffset_whitekeys + prefs.keys_pos[i][1])

        if (
            (pix_x >= self.appView.width)
            or (pix_y >= self.appView.height)
            or (pix_x < 0)
            or (pix_y < 0)
        ):
            return
        if prefs.resize == True:
            og_pix_x = pix_x
            og_pix_y = pix_y

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
            #      print "original x:"+str(pixxo) + "x" +str(pixyo) + " mapped :" +str(pixx) +"x"+str(pixy)

        key_BGR = self.video.image[pix_y, pix_x]
        key = [key_BGR[2], key_BGR[1], key_BGR[0]]

        prefs.keyp_colors_alternate[i] = key

    def readcolors(self, sender):
        for i in range(len(prefs.keys_pos)):
            self.readkeycolor(i)

    def updatecolor(self, sender):
        if self.lastkeygrabid != -1:
            self.readkeycolor(self.lastkeygrabid)

    def change_use_alternate_keys(self, sender):
        prefs.use_alternate_keys = not prefs.use_alternate_keys
        self.appView.update_alternate_label()

    def snap_notes_to_the_grid(self, sender):
        global use_snap_notes_to_grid
        use_snap_notes_to_grid = sender.switch_status

    def update_alternate_sensitivity(self, sender, value):
        if self.lastkeygrabid != -1:
            prefs.keyp_colors_alternate_sensitivity[self.lastkeygrabid] = value

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