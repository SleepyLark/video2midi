"""
midi_proc.py - MIDI processing and export logic for video2midi
Handles MIDI file creation, note extraction, and saving.
"""

# MIDI processing logic for video2midi
import os
import ntpath
import datetime
import math
from video2midi.prefs import prefs
from video2midi.models.midi import *
from utils import *

import logging
logger = logging.getLogger(__name__)

class MidiHandler:
    FORMAT_1 = 1
    FORMAT_2 = 2
    notes=[]
    notes_db=[]
    notes_de=[]
    notes_channel=[]
    notes_tmp=[]
    notes_pressed_color=[]

    def __init__(self):
        # May want to move this to prefs instead
        self.midi_file_format = self.FORMAT_1

        self.channel = 0
        self.volume = 100
        self.basenote = prefs.octave * 12

        # add some notes
        for i in range(144):
            self.notes.append(0)
            self.notes_db.append(0)
            self.notes_de.append(0)
            self.notes_channel.append(0)
            self.notes_tmp.append(0)
            self.notes_pressed_color.append([0,0,0])

            prefs.keyp_colors_alternate.append([0,0,0])
            prefs.keyp_colors_alternate_sensitivity.append(0)
        
        logger.debug(len(self.notes))
        self.update_key_positions(True)
        logger.debug(len(prefs.keys_pos))
    
    def is_black_key(self, key_id: int) -> bool:
      j = key_id % 12
      return (j == 1) or (j == 3) or (j == 6) or (j == 8) or (j == 10)

    def is_white_key(self, key_id: int) -> bool:
        return not self.is_black_key(key_id)

    def update_key_positions(self,append=False):
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
            
            if self.is_black_key(semitone_index):
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

    def process_midi(self, app_controller):
        """Process the video frame by frame and generate MIDI file."""
        import pygame
        
        logger.info("Starting MIDI reconstruction...")
        
        # Get references from controller
        video = app_controller.video
        appView = app_controller.appView
        
        # Setup MIDI file
        self.basenote = prefs.octave * 12
        midiOutFile = midinotes(int(self.midi_file_format))
        track = 0
        time = 0
        
        midiOutFile.setup_track(time, prefs.miditrackname, prefs.tempo)
        first_note_time = 0
        
        # Initialize program changes for each channel
        for i in range(len(prefs.keyp_colors_channel)):
            midiOutFile.addProgramChange(track, prefs.keyp_colors_channel[i], prefs.keyp_colors_channel_prog[i])
        
        logger.info(f"Starting from frame: {prefs.startframe}")
        video.get_image(prefs.startframe)
        notecnt = 0
        
        # Reset note states
        for i in range(144):
            self.notes[i] = 0
            self.notes_db[i] = 0
            self.notes_de[i] = 0
            self.notes_channel[i] = 0
            self.notes_tmp[i] = 0
        
        current_frame = prefs.startframe
        success = True
        
        while success and current_frame <= prefs.endframe:
            # Update display every 10 frames
            if (current_frame % 10 == 0):
                progress = current_frame / prefs.endframe
                logger.info(f"Processing frame: {current_frame} / {prefs.endframe} ({int(progress * 100)}%)")
            
            # Process each key
            for i in range(len(prefs.keys_pos)):
                pixpos = appView.getkeyp_pixel_pos(prefs.keys_pos[i][0], prefs.keys_pos[i][1])
                
                # CRITICAL FIX: Check MUST be here and MUST continue
                if pixpos is None:
                    # logger.debug(f"Key {i} out of bounds at frame {current_frame}")
                    continue
                
                # Now pixpos is guaranteed to be a valid tuple
                try:
                    keybgr = video.image[pixpos[1], pixpos[0]]
                    key = [int(keybgr[2]), int(keybgr[1]), int(keybgr[0])]
                except (IndexError, TypeError) as e:
                    logger.warning(f"Error sampling key {i} at {pixpos}: {e}")
                    continue
                
                # Sample spark if enabled
                sparkkey = [0, 0, 0]
                if prefs.use_sparks:
                    sh = max(1, int(appView.sparksWindow.sparks_slider_height.value))
                    for spark_y_add_pos in range(sh):
                        sparkpixpos = appView.getkeyp_pixel_pos(
                            prefs.keys_pos[i][0],
                            prefs.keyp_spark_y_pos - spark_y_add_pos
                        )
                        if sparkpixpos is not None:
                            try:
                                spark_bgr = video.image[sparkpixpos[1], sparkpixpos[0]]
                                sparkkey[0] += int(spark_bgr[2])
                                sparkkey[1] += int(spark_bgr[1])
                                sparkkey[2] += int(spark_bgr[0])
                            except (IndexError, TypeError) as e:
                                logger.warning(f"Error sampling spark for key {i}: {e}")
                                continue
                    
                    sparkkey = [int(sparkkey[0] / sh), int(sparkkey[1] / sh), int(sparkkey[2] / sh)]
                
                note = i
                if note > 144:
                    continue
                
                keypressed = 0
                note_channel = 0
                deltaid = 0
                
                # Color matching logic
                if prefs.use_alternate_keys:
                    delta = prefs.keyp_delta + prefs.keyp_colors_alternate_sensitivity[i]
                    if (abs(key[0] - prefs.keyp_colors_alternate[i][0]) > delta and
                        abs(key[1] - prefs.keyp_colors_alternate[i][1]) > delta and
                        abs(key[2] - prefs.keyp_colors_alternate[i][2]) > delta):
                        keypressed = 1
                else:
                    deltaclr = prefs.keyp_delta * prefs.keyp_delta * prefs.keyp_delta
                    
                    for j in range(len(prefs.keyp_colors)):
                        delta = prefs.keyp_delta
                        if prefs.use_percolor_delta and j < len(prefs.percolor_delta):
                            delta = prefs.percolor_delta[j]
                        
                        keyc = prefs.keyp_colors[j]
                        if keyc == [0, 0, 0]:
                            continue
                        
                        if (abs(key[0] - keyc[0]) < delta and
                            abs(key[1] - keyc[1]) < delta and
                            abs(key[2] - keyc[2]) < delta):
                            
                            delta_dist = (abs(key[0] - keyc[0]) + 
                                        abs(key[1] - keyc[1]) + 
                                        abs(key[2] - keyc[2]))
                            
                            if delta_dist < deltaclr:
                                deltaclr = delta_dist
                                deltaid = j
                            
                            keypressed = 1
                            
                            if prefs.use_sparks:
                                spark_delta = prefs.keyp_colors_sparks_sensitivity[j]
                                has_spark_delta = (
                                    (sparkkey[0] - keyc[0]) > spark_delta or
                                    (sparkkey[1] - keyc[1]) > spark_delta or
                                    (sparkkey[2] - keyc[2]) > spark_delta
                                )
                                if not has_spark_delta:
                                    keypressed = 0
                
                if keypressed != 0:
                    note_channel = prefs.keyp_colors_channel[deltaid]
                
                # Register key press
                if keypressed == 1 or (keypressed == 2 and self.notes[note] != 1):
                    if self.notes[note] == 0:
                        self.notes_db[note] = current_frame
                        if first_note_time == 0:
                            first_note_time = current_frame / video.fps
                        self.notes_channel[note] = note_channel
                        
                        if app_controller.separate_note_id != -1:
                            if app_controller.separate_note_id < note:
                                self.notes_channel[note] = 0
                            else:
                                self.notes_channel[note] = 1
                    
                    self.notes[note] = keypressed
                
                self.notes_tmp[note] = keypressed
            
            # Apply rollcheck filter
            if prefs.rollcheck:
                for i in range(1, len(prefs.keys_pos) - 1):
                    if self.notes[i] != 0:
                        if prefs.rollcheck_priority == 0:
                            if not self.is_black_key(i):
                                if self.notes[i + 1] > 0 and self.notes_tmp[i] > 0:
                                    self.notes[i] = 0
                                if self.notes[i - 1] > 0 and self.notes_tmp[i] > 0:
                                    self.notes[i] = 0
                        else:
                            if self.is_black_key(i):
                                if self.notes[i + 1] > 0 and self.notes_tmp[i] > 0:
                                    self.notes[i] = 0
                                if self.notes[i - 1] > 0 and self.notes_tmp[i] > 0:
                                    self.notes[i] = 0
            
            # Process note on/off events
            for i in range(len(prefs.keys_pos)):
                note = i
                keypressed = self.notes[note]
                
                if self.notes_tmp[i] != 0:
                    if (self.notes[note] != 0 and 
                        self.notes_channel[note] != note_channel and 
                        prefs.notes_overlap):
                        
                        time_val = self.notes_db[note] / video.fps
                        duration = (current_frame - self.notes_db[note]) / video.fps
                        
                        if app_controller.use_snap_notes_to_grid:
                            time_val = snap_to_grid(time_val - first_note_time, 
                                                app_controller.notes_grid_size) + 1
                            duration = snap_to_grid(duration, app_controller.notes_grid_size)
                        
                        ignore = False
                        if duration < prefs.minimal_duration:
                            duration = prefs.minimal_duration
                            if prefs.ignore_minimal_duration:
                                ignore = True
                        
                        if not ignore:
                            midiOutFile.addNote(track, self.notes_channel[note], 
                                            self.basenote + note,
                                            time_val * prefs.tempo / 60.0,
                                            duration * prefs.tempo / 60.0,
                                            self.volume)
                            notecnt += 1
                        
                        self.notes_db[note] = current_frame
                        self.notes_channel[note] = note_channel
                else:
                    if self.notes[note] != 0:
                        self.notes[note] = 0
                        self.notes_de[note] = current_frame
                        
                        time_val = self.notes_db[note] / video.fps
                        duration = (self.notes_de[note] - self.notes_db[note]) / video.fps
                        
                        if app_controller.use_snap_notes_to_grid:
                            if first_note_time == 0:
                                first_note_time = time_val
                            time_val = snap_to_grid(time_val - first_note_time,
                                                app_controller.notes_grid_size) + 1
                            duration = snap_to_grid(duration, app_controller.notes_grid_size)
                        
                        ignore = False
                        if duration < prefs.minimal_duration:
                            duration = prefs.minimal_duration
                            if prefs.ignore_minimal_duration:
                                ignore = True
                        
                        if not ignore:
                            midiOutFile.addNote(track, self.notes_channel[note],
                                            self.basenote + note,
                                            time_val * prefs.tempo / 60.0,
                                            duration * prefs.tempo / 60.0,
                                            self.volume)
                            notecnt += 1
                        
                        if keypressed == 2:
                            self.notes[note] = keypressed
                            self.notes_db[note] = current_frame
                            self.notes_channel[note] = note_channel
            
            # Check for abort
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    success = False
                    pygame.quit()
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        logger.info("User aborted MIDI reconstruction")
                        success = False
                    if event.key == pygame.K_ESCAPE:
                        app_controller.running = False
                        pygame.quit()
                        quit()
            
            # Next frame
            current_frame += 1
            if current_frame <= prefs.endframe:
                video.get_image(current_frame)
        
        logger.info(f"Saved {notecnt} notes")
        
        # Generate output filename
        outputmid = ntpath.basename(app_controller.filepath) + "_output.mid"
        fileid = 0
        while os.path.exists(outputmid):
            outputmid = ntpath.basename(app_controller.filepath) + f"_{fileid}_output.mid"
            fileid += 1
            if fileid > 999:
                break
        
        if prefs.sync_notes_start_pos:
            midiOutFile.sync_start_pos(prefs.sync_notes_start_pos_time_delta, False)
        
        if prefs.save_to_disk_per_channel:
            status, prefs.save_to_disk_message = midiOutFile.save_to_disk_per_channel(outputmid)
        else:
            status, prefs.save_to_disk_message = midiOutFile.save_to_disk(outputmid)
        
        logger.info(f"MIDI file saved: {prefs.save_to_disk_message}")
        
        return status