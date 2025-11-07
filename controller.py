from video2midi.prefs import prefs
from video2midi.settings import *
from video_io import VideoHandler
from utils import *
import os
from cli import get_video_filepath, get_ini_filepath
from ui import MainWindow
from midi_proc import MidiHandler

import logging
logger = logging.getLogger(__name__)

import math
import ntpath
import time
from os.path import expanduser
from ui import *
from midi_proc import *

class AppController:
    def __init__(self):
        self.filepath = get_video_filepath()

        self.outputmid = ntpath.basename(self.filepath) + '_output.mid'
        self.settingsfile = self.filepath + '.ini'
        self.inifile = get_ini_filepath()

        self.video = VideoHandler(self.filepath)
        self.appView = MainWindow(self, self.video.video_width, self.video.video_height)

        self.endframe = self.video.length
        self.running = True

        # set starting image
        self.appView.loadImage(self.video.get_image())
        self.appView.fit_to_the_screen()

    def start(self):
        while self.running:
            self.appView.drawframe()
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
                    self.appView.resize_window()

    def loadsettings(self, cfgfile: str):
        settings.loadsettings(cfgfile)
        settings.compatibleColors(self.appView.get_colorBtn_list())
        
        self.appView.loadImage(self.video.get_image(prefs.startframe))
        self.appView.update_values_from_settings()
        self.appView.update_size()          

    def start_recreate_midi(self, sender):
        if prefs.autoclose == 1:
            self.running = False
        else:
            #reconstruct()
            pass
    
    def show_or_hide_all_windows(self,sender):
        self.appView.toggle_windows()


    def set_start_frame_to_current_frame(self,sender):
        prefs.startframe = self.video.get_current_frame_int()
        logger.debug(f"set start frame = {prefs.startframe}")

    def set_end_frame_to_current_frame(self, sender):
        endframe = self.video.get_current_frame_int()
        logger.debug(f"set end frame = {endframe}")

    def switch_notes_overlap(sender):
        if sender is None:
            prefs.notes_overlap = not prefs.notes_overlap
            notes_overlap_btn.switch_status = prefs.notes_overlap
        else:
            prefs.notes_overlap = notes_overlap_btn.switch_status
    def switch_ignore_notes_with_minimal_duration(sender):
        if sender is None:
            prefs.ignore_minimal_duration = not prefs.ignore_minimal_duration
            ignore_notes_with_minimal_duration_btn.switch_status = prefs.ignore_minimal_duration
        else:
            prefs.ignore_minimal_duration = ignore_notes_with_minimal_duration_btn.switch_status
    
    def switch_sync_notes_start_pos(sender):
        prefs.sync_notes_start_pos = sender.switch_status

    def switch_resize_windows(sender):
        prefs.resize = not prefs.resize
        self.appView.resize_window()

    def change_autoclose(sender):
        prefs.autoclose = sender.switch_status

    def btndown_save_settings(sender):
        self.settings.savesettings(settingsfile)

    def btndown_load_settings(sender):
        old_resize = prefs.resize
        loadsettings( settingsfile )
        update_alternate_label()
        if (prefs.resize != old_resize):
            self.appView.resize_window()

    def change_rollcheck(sender):
        prefs.rollcheck = sender.switch_status

    def change_rollcheck_priority(sender):
        prefs.rollcheck_priority = sender.switch_status

    def change_save_to_disk_per_channel(sender):
        prefs.save_to_disk_per_channel = sender.switch_status

    def raise_octave(*args):
        prefs.octave += 1
        if (prefs.octave > 7): 
            prefs.octave = 7
        midiHandler.basenote = prefs.octave * 12
    
    def lower_octave(*args):
        prefs.octave -= 1
        if (prefs.octave < 0): 
            prefs.octave = 0
        midiHandler.basenote = prefs.octave * 12

    def scroll_by_steps(self, steps ):
        self.video.currentFrame += steps
        if (self.video.currentFrame > self.video.length *0.99):
            self.video.currentFrame = math.trunc(self.video.length *0.99)
        if (self.video.currentFrame < 1):
            self.video.currentFrame=1
        
        self.appView.loadImage(self.video.get_image(self.video.currentFrame))

    def scroll_forward_by_frame(sender):
        scroll_by_steps(1)

    def scroll_fast_forward(sender):
        scroll_by_steps(100)

    def scroll_prev_by_frame(sender):
        scroll_by_steps(-1)

    def scroll_fast_prev(sender):
        scroll_by_steps(-100)

    def scroll_to_start(self, sender):
        self.video.currentFrame=0
        self.appView.loadImage(self.video.get_image())

    def scroll_to_end(self, sender):
        self.video.currentFrame = self.video.length-100
        self.appView.loadImage(self.video.get_image())

    def rotate_cw(sender):
        prefs.keys_angle -= 5
        update_key_positions()

    def rotate_ccw(sender):
        prefs.keys_angle += 5
        update_key_positions()

    def change_cnt(sender):
        print('change count')
        update_key_positions(True)


    def vertical_align_keys( separate_black_keys = 1, align = 1 ):
        print(f"lastkeygrabid {lastkeygrabid}")
        if lastkeygrabid < 0 or lastkeygrabid > len(prefs.keys_pos):
            return

        y = prefs.keys_pos[lastkeygrabid][align]
        selected_black_key = is_black_key(lastkeygrabid)
        
        for idx in range (len(prefs.keys_pos)):
            if separate_black_keys == 1:
                if selected_black_key:
                    if is_black_key(idx):
                        prefs.keys_pos[idx][align] = y
                else:
                    if not is_black_key(idx):
                        prefs.keys_pos[idx][align] = y
            else:
                prefs.keys_pos[idx][align] = y
                
    def valign(sender):
        AppController.vertical_align_keys(align=1)

    def halign(sender):
        AppController.vertical_align_keys(align=0)

    def update_keys_pos_cnt(sender,value):
        prefs.keys_pos_cnt=int(value)

    def update_blackkey_relative_position(sender,value):
        prefs.blackkey_relative_position = value * 0.001
        self.update_key_positions()

    def update_sync_notes_start_pos_time_delta(sender,value):
        prefs.sync_notes_start_pos_time_delta = value *0.001

    
    def update_key_positions(append=False):
        current_x = 0
        if append:
            print(f'clear keys, set to {prefs.keys_pos_cnt}')
            prefs.keys_pos = []

        for key_index in range(prefs.keys_pos_cnt):
            octave_index = key_index // 12
            semitone_index = key_index % 12
            if (append) or (octave_index * 12 + semitone_index > len(prefs.keys_pos) - 1):
                prefs.keys_pos.append([0, 0])
            prefs.keys_pos[octave_index * 12 + semitone_index][0] = int(round(current_x))
            prefs.keys_pos[octave_index * 12 + semitone_index][1] = 0
            if is_black_key(semitone_index):
                prefs.keys_pos[octave_index * 12 + semitone_index][1] = prefs.yoffset_blackkeys
                current_x += -prefs.whitekey_width
            if (semitone_index == 1) or (semitone_index == 6):
                prefs.keys_pos[octave_index * 12 + semitone_index][0] = int(round(current_x + prefs.whitekey_width * prefs.blackkey_relative_position))
            if (semitone_index == 8):
                prefs.keys_pos[octave_index * 12 + semitone_index][0] = int(round(current_x + prefs.whitekey_width * 0.5))
            if (semitone_index == 3) or (semitone_index == 10):
                prefs.keys_pos[octave_index * 12 + semitone_index][0] = int(round(current_x + prefs.whitekey_width * (1.0 - prefs.blackkey_relative_position)))
            current_x += prefs.whitekey_width
        for octave_index in range(len(prefs.keys_pos)):
            prefs.keys_pos[octave_index] = v_rotate(prefs.keys_pos[octave_index], prefs.keys_angle)
            prefs.keys_pos[octave_index][0] = -prefs.keys_pos[octave_index][0]

    def onPallete_click(sender, index):
        selected_color_delta.color = sender.color
        if index < len(prefs.percolor_delta):
            selected_color_delta.setvalue( prefs.percolor_delta[ index ] )
            sparks_slider_delta.id    = Gl.keyp_colormap_id
            sparks_slider_delta.color = prefs.keyp_colors[Gl.keyp_colormap_id]
            sparks_slider_delta.setvalue( prefs.keyp_colors_sparks_sensitivity[Gl.keyp_colormap_id] )

    def update_channels(sender):
        print( 'update_channels...' +str(sender.index))
        i=abs(sender.index) -1
        if (sender.index > 0):
            prefs.keyp_colors_channel[i]= prefs.keyp_colors_channel[i] + 1
        else:
            prefs.keyp_colors_channel[i]= prefs.keyp_colors_channel[i] - 1
        if (prefs.keyp_colors_channel[i] > 15):
            prefs.keyp_colors_channel[i] = 15
        if (prefs.keyp_colors_channel[i] < 0):
            prefs.keyp_colors_channel[i] = 0
        colorWindow_colorBtns_channel_labels[i].text = "Ch:" + str(prefs.keyp_colors_channel[i]+1)

    def disable_color(sender):
        print( 'disabled color...' +str(sender.index))
        if sender.index < len(prefs.keyp_colors):
            prefs.keyp_colors[ sender.index ] = [0,0,0]
        #   prefs.keyp_colors_channel[i]= prefs.keyp_colors_channel[i] + 1

    def readkeycolor(i):
        pix_x=int(prefs.xoffset_whitekeys + prefs.keys_pos[i][0])
        pix_y=int(prefs.yoffset_whitekeys + prefs.keys_pos[i][1])

        if ( pix_x >= appView.width ) or ( pix_y >= appView.height ) or ( pix_x < 0 ) or ( pix_y < 0 ): return
        if ( prefs.resize == True ):
            og_pix_x=pix_x
            og_pix_y=pix_y

            pix_x= int(round( pix_x * ( video.video_width / float(prefs.resize_width) )))
            pix_y= int(round( pix_y * ( video.video_height / float(prefs.resize_height) )))
            if ( pix_x > video.video_width -1 ): pix_x = video.video_width-1
            if ( pix_y > video.video_height-1 ): pix_y= video.video_height-1
            #      print "original x:"+str(pixxo) + "x" +str(pixyo) + " mapped :" +str(pixx) +"x"+str(pixy)

        key_BGR = video.image[pix_y,pix_x]
        key=[ key_BGR[2], key_BGR[1],key_BGR[0] ]

        prefs.keyp_colors_alternate[i] = key


    def readcolors(sender):
        for i in range( len(prefs.keys_pos) ):
            readkeycolor(i)

    def updatecolor(sender):
        if (lastkeygrabid != -1):
            readkeycolor(lastkeygrabid)
    
    def change_use_alternate_keys(sender):
        global extra_label1
        prefs.use_alternate_keys = not prefs.use_alternate_keys
        update_alternate_label()

    
    def update_alternate_label():
        extra_label1.text = "Use alternate:"+str(prefs.use_alternate_keys)

    def snap_notes_to_the_grid(sender):
        global use_snap_notes_to_grid
        use_snap_notes_to_grid = sender.switch_status

    def update_alternate_sensitivity(sender,value):
        global lastkeygrabid
        if ( lastkeygrabid != -1 ):
            prefs.keyp_colors_alternate_sensitivity[ lastkeygrabid ] = value

    def change_use_sparks(sender):
        prefs.use_sparks = sender.switch_status
    #   sender.text = "use sparks:"+str(use_sparks)

    def update_sparks_y_pos (sender):
        if (sender.text == 'y+'):
            prefs.keyp_spark_y_pos = prefs.keyp_spark_y_pos -1
        else:
            prefs.keyp_spark_y_pos = prefs.keyp_spark_y_pos +1

    def update_sparks_delta(sender,value):
        if (sender.id == -1):
            return
        if (sender.id < len(prefs.keyp_colors))  :
            prefs.keyp_colors_sparks_sensitivity[sender.id] = sender.value
            #print("keyp_colors_sparks_sensitivity["+str(sender.id)+"] = "+ str(sender.value) )

    def change_use_percolor_delta(sender):
        prefs.use_percolor_delta = sender.switch_status

    def update_percolor_delta(sender,value):
        if (Gl.keyp_colormap_id == -1):
            return
        if (Gl.keyp_colormap_id < len(prefs.percolor_delta)):
            prefs.percolor_delta[ Gl.keyp_colormap_id ] = sender.value
            #print("changed percolor delta for color with id ["+str(sender.id)+"] = "+ str(sender.value) )
