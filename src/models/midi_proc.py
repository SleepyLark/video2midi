"""
midi_proc.py - MIDI processing and export logic for video2midi
Handles MIDI file creation, note extraction, and saving.
"""

# MIDI processing logic for video2midi
import os
import ntpath
import math
from src.prefs import prefs
from src.models.midi import midinotes

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
            prefs.keys_pos[octave_index] = self.v_rotate(prefs.keys_pos[octave_index], prefs.keys_angle)
            prefs.keys_pos[octave_index][0] = -prefs.keys_pos[octave_index][0]

    def process_midi(self, app_controller):
        """Process the video frame by frame and generate MIDI file."""
        import pygame
        import numpy as np

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

        # Initialize program changes
        for i in range(len(prefs.keyp_colors_channel)):
            midiOutFile.addProgramChange(track, prefs.keyp_colors_channel[i], prefs.keyp_colors_channel_prog[i])

        logger.info(f"Starting from frame: {prefs.startframe}")
        img = video.get_image(prefs.startframe)
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
        
        # 1. Pre-calc Main Key Positions
        cached_key_pixels = []
        for i in range(len(prefs.keys_pos)):
            # Calculate pixel position ONCE
            pix = appView.getkeyp_pixel_pos(prefs.keys_pos[i][0], prefs.keys_pos[i][1])
            cached_key_pixels.append(pix) # Stores (x, y) or None

        # 2. Pre-calc Spark Slices (Vectorization setup)
        # Instead of a loop for sparks, we will use numpy array slicing
        cached_spark_slices = []
        use_sparks = prefs.use_sparks
        if use_sparks:
            sh = max(1, int(appView.sparksWindow.sparks_slider_height.value))
            for i in range(len(prefs.keys_pos)):
                # We need the top and bottom Y coordinates of the spark column
                # Note: 'spark_y_add_pos' subtraction implies we go UP the image (lower Y index)
                # We calculate the range [y_start, y_end]
                p_start = appView.getkeyp_pixel_pos(prefs.keys_pos[i][0], prefs.keyp_spark_y_pos)
                p_end   = appView.getkeyp_pixel_pos(prefs.keys_pos[i][0], prefs.keyp_spark_y_pos - sh + 1)
                
                if p_start and p_end:
                    # Numpy slices need y_min:y_max. p_end is physically higher (lower index)
                    y_min = min(p_start[1], p_end[1])
                    y_max = max(p_start[1], p_end[1]) + 1 # +1 for exclusive upper bound
                    cached_spark_slices.append((p_start[0], y_min, y_max))
                else:
                    cached_spark_slices.append(None)

        # Cache length for speed
        num_keys = len(prefs.keys_pos)

        # detection loop
        while success and current_frame <= prefs.endframe:
            # TODO: REMOVE REFERENCES TO APPVIEW
            # Update display every 10 frames
            if (current_frame % 10 == 0):
                progress = current_frame / (prefs.endframe if prefs.endframe > 0 else 1)
                logger.info(f"Processing frame: {current_frame} / {prefs.endframe} ({int(progress * 100)}%)")
                appView.loadImage(img)
                appView.draw_processing_progress(current_frame - prefs.startframe, 
                                        prefs.endframe - prefs.startframe)
        
                pygame.event.pump()
                
                # Check for abort only periodically to save time
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        success = False
                        pygame.quit()
                        quit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            logger.info("User aborted MIDI reconstruction")
                            success = False
                            break

            # --- FRAME PROCESSING ---
            
            # Access the numpy image directly
            # Ensure we have a valid image
            if video.image is None:
                break
                
            img = video.image 
            
            for i in range(num_keys):
                # OPTIMIZATION: Use cached pixel coordinate
                pixpos = cached_key_pixels[i]
                
                if pixpos is None:
                    continue

                # Direct NumPy access (Faster than try/except inside loop)
                # pixpos is (x, y). Img is [y, x]
                try:
                    # Get BGR color
                    keybgr = img[pixpos[1], pixpos[0]]
                    # Convert to [R, G, B]
                    key = [int(keybgr[2]), int(keybgr[1]), int(keybgr[0])]
                except IndexError:
                    continue

                # OPTIMIZATION: Vectorized Spark Sampling
                sparkkey = [0, 0, 0]
                if use_sparks:
                    sl = cached_spark_slices[i] # (x, y_min, y_max)
                    if sl:
                        try:
                            # Slicing: Extract the vertical column of pixels at once
                            # img[y_min:y_max, x] returns shape (height, 3)
                            spark_area = img[sl[1]:sl[2], sl[0]]
                            
                            if spark_area.size > 0:
                                # Calculate mean color across the vertical slice
                                # axis=0 averages down the column
                                avg_bgr = np.mean(spark_area, axis=0)
                                sparkkey = [int(avg_bgr[2]), int(avg_bgr[1]), int(avg_bgr[0])]
                        except IndexError:
                            pass
                
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
                            
                            if use_sparks:
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
                # Optimized rollcheck: direct list access, no function calls
                for i in range(1, num_keys - 1):
                    if self.notes[i] != 0:
                        # Pre-calculating black key check is hard here without cached boolean, 
                        # but this logic is fast enough as-is usually.
                        is_black = self.is_black_key(i)
                        
                        if prefs.rollcheck_priority == 0:
                            if not is_black:
                                if self.notes[i + 1] > 0 and self.notes_tmp[i] > 0:
                                    self.notes[i] = 0
                                if self.notes[i - 1] > 0 and self.notes_tmp[i] > 0:
                                    self.notes[i] = 0
                        else:
                            if is_black:
                                if self.notes[i + 1] > 0 and self.notes_tmp[i] > 0:
                                    self.notes[i] = 0
                                if self.notes[i - 1] > 0 and self.notes_tmp[i] > 0:
                                    self.notes[i] = 0
            
            # Process note on/off events
            for i in range(num_keys):
                note = i
                keypressed = self.notes[note]
                
                if self.notes_tmp[i] != 0:
                    if (self.notes[note] != 0 and 
                        self.notes_channel[note] != note_channel and 
                        prefs.notes_overlap):
                        
                        time_val = self.notes_db[note] / video.fps
                        duration = (current_frame - self.notes_db[note]) / video.fps
                        
                        if app_controller.use_snap_notes_to_grid:
                            time_val = self.snap_to_grid(time_val - first_note_time, 
                                                app_controller.notes_grid_size) + 1
                            duration = self.snap_to_grid(duration, app_controller.notes_grid_size)
                        
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
                            time_val = self.snap_to_grid(time_val - first_note_time,
                                                app_controller.notes_grid_size) + 1
                            duration = self.snap_to_grid(duration, app_controller.notes_grid_size)
                        
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
            
            # Next frame
            current_frame += 1
            if current_frame <= prefs.endframe:
                video.read_next_frame()
        
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
    
    def snap_to_grid(self,input_value, input_grid_size):
        quantized = int((input_value - int(input_value)) * input_grid_size) / input_grid_size
        result = (quantized + int(input_value))
        return result
    
    def v_rotate(self,v, ang):
        radAng = ang * math.pi / 180
        return [
            (v[1] * math.cos(radAng)) - (v[0] * math.sin(radAng)),
            (v[1] * math.sin(radAng)) + (v[0] * math.cos(radAng))
        ]