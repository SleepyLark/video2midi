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

# processmidi and reconstruct will be moved here from v2m.py
# Example stub for processmidi:
def processmidi(self):
 global separate_note_id
 global outputmid



 self.basenote = prefs.octave * 12
 midiOutFile = midinotes(prefs.midi_file_format)
 track = 0 # the only track
 time = 0 # start at the beginning

 midiOutFile.setup_track(time, prefs.miditrackname, prefs.tempo)
 first_note_time=0

 channel_has_note = [ 0 for x in range(16) ]
 for i in range(len(prefs.keyp_colors_channel)):
  midiOutFile.addProgramChange(track, prefs.keyp_colors_channel[i], prefs.keyp_colors_channel_prog[i])

 print("starting from frame:" + str(prefs.startframe))
 video.getFrame( prefs.startframe )
 notecnt=0
 lastimage = video.image.copy()
 while video.success:

  if (video.currentFrame % 10 == 0):
   glBindTexture(GL_TEXTURE_2D, Gl.bgImgGL)
   if (video.currentFrame % 200 == 0):
     appView.loadImage(video.loadImage(video.currentFrame))
     lastimage = video.image.copy()
   #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
   #glTexImage2D(GL_TEXTURE_2D, 0, 3, video_width, video_height, 0, GL_BGR, GL_UNSIGNED_BYTE, image )
   #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
   glEnable(GL_TEXTURE_2D)
   drawframe( lastimage )

   glColor4f(1.0, 0.5, 1.0, 0.5)
   glDisable(GL_TEXTURE_2D)
   p= video.currentFrame / float( video.length )
   DrawQuad(0,appView.height *0.5 -10, p  * appView.width ,appView.height *0.5 +10)
 #  glPopMatrix();:
   pygame.display.flip()

#  if (frame % 100 == 0):
   print("processing frame: " + str(video.currentFrame) + " / " + str(video.length) + " % " + str( math.trunc(p * 100)))

#  if ( resize == 1 ):
#    image=cv2.resize(image, (width , height))

  # processing white keys
  for i in range( len(prefs.keys_pos) ):
    pixpos = getkeyp_pixel_pos(prefs.keys_pos[i][0],prefs.keys_pos[i][1])

    if (pixpos[0] == -1) and (pixpos[1] == -1):
      continue
    key_BGR = video.image[ pixpos[1], pixpos[0] ]
    key= [ key_BGR[2], key_BGR[1],key_BGR[0] ]

    key_BGR=[0,0,0]
    sparkkey=[0,0,0]
    if prefs.use_sparks:
     sh = int(sparks_slider_height.value)
     if sh == 0:
        sh = 1
     for spark_y_add_pos in range (sh):
       sparkpixpos = getkeyp_pixel_pos(prefs.keys_pos[i][0],prefs.keyp_spark_y_pos - spark_y_add_pos )
       if not ((sparkpixpos[0] == -1) and (sparkpixpos[1] == -1)):
         key_BGR   = video.image[ sparkpixpos[1], sparkpixpos[0] ]
         sparkkey = [ sparkkey[0] + key_BGR[2],
                      sparkkey[1] + key_BGR[1],
                      sparkkey[2] + key_BGR[0] ]
     sparkkey = [ sparkkey[0] / sh,  sparkkey[1] / sh,sparkkey[2] / sh]
    else:
      sparkkey = [0,0,0]

    note=i
    if ( note > 144 ):
      print("skip note > 144")
      continue


    keypressed=0
    note_channel=0

#    deltaclr = abs( int(key[0]) - keyp_colors[0][0] ) +  abs( int(key[1]) - keyp_colors[0][1] ) + abs( int(key[2]) - keyp_colors[0][2] )
    deltaclr = prefs.keyp_delta*prefs.keyp_delta*prefs.keyp_delta

    deltaid = 0
    if prefs.use_alternate_keys:
      delta = prefs.keyp_delta + prefs.keyp_colors_alternate_sensitivity[i]
      if ( abs( int(key[0]) - prefs.keyp_colors_alternate[i][0] ) > delta ) and ( abs( int(key[1]) - prefs.keyp_colors_alternate[i][1] ) > delta ) and ( abs( int(key[2]) - prefs.keyp_colors_alternate[i][2] ) > delta ):
        keypressed = 1
        pressedcolor = prefs.keyp_colors_alternate[i]
    else:
      for j in range(len(prefs.keyp_colors)):
       delta = prefs.keyp_delta
       if prefs.use_percolor_delta:
         if j < len( prefs.percolor_delta ):
           delta =  prefs.percolor_delta[ j ]
       deltaclr = delta*delta*delta

       if (prefs.keyp_colors[j][0] != 0 ) or ( prefs.keyp_colors[j][1] != 0 ) or ( prefs.keyp_colors[j][2] != 0 ):
        if ( abs( int(key[0]) - prefs.keyp_colors[j][0] ) < delta ) and ( abs( int(key[1]) - prefs.keyp_colors[j][1] ) < delta ) and ( abs( int(key[2]) - prefs.keyp_colors[j][2] ) < delta ):
         delta = abs( int(key[0]) - prefs.keyp_colors[j][0] ) +  abs( int(key[1]) - prefs.keyp_colors[j][1] ) + abs( int(key[2]) - prefs.keyp_colors[j][2] )
         if ( delta < deltaclr ):
          deltaclr = delta
          deltaid = j
         keypressed=1
         if prefs.use_sparks:
           has_spark_delta = ((sparkkey[0] - prefs.keyp_colors[j][0] ) > prefs.keyp_colors_sparks_sensitivity[j] ) or ((sparkkey[1] - prefs.keyp_colors[j][1] ) > prefs.keyp_colors_sparks_sensitivity[j] ) or ((sparkkey[2] - prefs.keyp_colors[j][2] ) > prefs.keyp_colors_sparks_sensitivity[j] )
           #if ( abs( int(sparkkey[0]) - keyp_colors[j][0] ) < keyp_colors_sparks_sensitivity[j] ) and ( abs( int(sparkkey[1]) - keyp_colors[j][1] ) < keyp_colors_sparks_sensitivity[j] ) and ( abs( int(sparkkey[2]) - keyp_colors[j][2] ) < keyp_colors_sparks_sensitivity[j] ):
           if ( not has_spark_delta ):
             keypressed=0


    if ( keypressed != 0 ):
       note_channel=prefs.keyp_colors_channel[ deltaid ]

    if ( prefs.debug == 1 ):
      if (keypressed == 1 ):
        cv2.rectangle(video.image, (pixx-5,pixy-5), (pixx+5,pixy+5), (128,128,255), -1 )
        cv2.putText(video.image, str(note_channel), (pixx-5,pixy-10), 0, 0.3, (64,128,255))
#      cv2.rectangle(image, (pixx-5,pixy-5), (pixx+5,pixy+5), (255,0,255))
      cv2.rectangle(video.image, (pixx-1,pixy-1), (pixx+1,pixy+1), (255,0,255))
#      cv2.putText(image, str(note), (pixx-5,pixy+20), 0, 0.5, (255,0,255))

    # reg pressed key; when keypressed==2 and previous keypressed state is 0 or 2 we should also goes here
    if keypressed==1 or (keypressed==2 and notes[note] != 1):
      # if key is not pressed
      if ( notes[note] == 0 ):
        if ( debug_keys == True ):
          print("note pressed on :" + str( note ))
        notes_db[ note ] = video.currentFrame
        if (first_note_time == 0):
          first_note_time = video.currentFrame / video.fps
        notes_channel[ note ] = note_channel
        if ( separate_note_id != -1 ):
          if ( separate_note_id < note ):
            notes_channel[ note ] = 0
          else:
            notes_channel[ note ] = 1

      # always update to last press state
      notes[ note ] = keypressed
    notes_tmp[ note] = keypressed
 # save fall notes and then we can check for a near keys with priority...
  if prefs.rollcheck:
    for i in range(1, len( prefs.keys_pos)-1 ):
      if notes[ i ] != 0:
        if prefs.rollcheck_priority == 0:
          if not is_white_key(i):
          # Priority on Black keys
            if notes[i+1] >0 and notes_tmp[i] >0: notes[i] = 0
            if notes[i-1] >0 and notes_tmp[i] >0: notes[i] = 0
        else:
          if is_white_key(i):
          # Priority on White keys
            if notes[i+1] >0 and notes_tmp[i] >0: notes[i] = 0
            if notes[i-1] >0 and notes_tmp[i] >0: notes[i] = 0
  #
  for i in range( len( prefs.keys_pos) ):
    note=i
    keypressed =  notes[ note ]
    if notes_tmp[ i ] != 0:
      if ( notes[note] != 0 ) and ( notes_channel[ note ] != note_channel ) and ( prefs.notes_overlap == 1 ):
        # case if one key over other
        time = notes_db[note] / video.fps
        duration = ( video.currentFrame - notes_db[note] ) / video.fps
        if (use_snap_notes_to_grid == 1):
          #print ("1 time:", time , "first_note_time:",first_note_time)
          time = snap_to_grid( time - first_note_time , notes_grid_size ) + 1
          duration = snap_to_grid( duration , notes_grid_size )
          #print ("1 time after:", time , "after before:",duration)


        ignore = 0
        if ( duration < prefs.minimal_duration ):
          if ( debug_keys == True ):
            print(" duration:" + str(duration) + " < minimal_duration:" + str(prefs.minimal_duration))
          duration = prefs.minimal_duration
          if ( prefs.ignore_minimal_duration == 1 ):
            ignore=1


        if ( debug_keys == True ):
          print("keys (one over other), note released :" + str(note) + " de = " + str(notes_de[note]) + "- db =" + str(notes_db[note]))
          print("midi add white keys, note : " +str(note) + " time:" +str(time) + " duration:" + str(duration))

        if ( not ignore ):
          midiOutFile.addNote(track, notes_channel[note] , self.basenote + note, time * prefs.tempo / 60.0 , duration * prefs.tempo / 60.0 , volume )
          channel_has_note[ note_channel ] = 1
          notecnt+=1

        notes_db[ note ] = video.currentFrame
        notes_channel[ note ] = note_channel
    else:
      # if key been presed and released: two cases goes here keypressed==0 or (keypressed==2 and previous state is keypressed==1)
      if ( notes[note] != 0):
        notes[ note ] = 0
        notes_de[ note ] = video.currentFrame
        time = notes_db[note] / video.fps
        duration = ( notes_de[note] - notes_db[note] ) / video.fps

        if (use_snap_notes_to_grid):
          if (first_note_time == 0):
            first_note_time = time
          #print ("2 time:", time , "first_note_time:",first_note_time)
          time = snap_to_grid( time - first_note_time , notes_grid_size ) + 1
          duration = snap_to_grid( duration , notes_grid_size )

        ignore=0
        if ( duration < prefs.minimal_duration ):
          if ( debug_keys == True ):
            print(" duration:" + str(duration) + " < minimal_duration:" + str(prefs.minimal_duration))
          duration = prefs.minimal_duration
          if ( prefs.ignore_minimal_duration == 1 ):
            ignore=1

        if ( debug_keys == True ):
          print("keys, note released :" + str(note ) + " de = " + str(notes_de[note]) + "- db =" + str(notes_db[note]))
          print("midi add white keys, note : " +str(note) + " time:" +str(time) + " duration:" + str(duration))
        if ( not ignore ):
          midiOutFile.addNote(track, notes_channel[note] , midiHandler.basenote+ note, time * prefs.tempo / 60.0 , duration * prefs.tempo / 60.0 , volume )

          channel_has_note[ note_channel ] = 1
          notecnt+=1
        # coming here when use sparks is true and previous state is keypressed==1. We consider the key is released and then pressed again
        if (keypressed==2):
          notes[ note ] = keypressed
          notes_db[ note ] = video.currentFrame
          notes_channel[ note ] = note_channel

  xapp=0
  if ( prefs.debug == 1 ):
    cv2.imwrite("/tmp/frame%d.jpg" % video.currentFrame, video.image)  # save frame as JPEG file

#  success,image = vidcap.read()
  video.getFrame()

  video.currentFrame += 1
  framerate()

  if ( video.currentFrame > endframe ):
    video.success = False

  for event in pygame.event.get():
   if event.type == pygame.QUIT:
     video.success = False
     pygame.quit()
     quit()
   elif event.type == pygame.KEYDOWN:
    if event.key == pygame.K_SPACE:
     video.success = False
    if event.key == pygame.K_ESCAPE:
     running = False
     pygame.quit()
     quit()

 print("saved notes: " + str(notecnt))

 #search free id for name ...
 fileid=0
 while os.path.exists( outputmid ):
  outputmid = ntpath.basename( filepath ) + "_"+str(fileid)+ "_output.mid"
  fileid+=1
  if ( fileid > 999 ): break
 if prefs.sync_notes_start_pos:
   midiOutFile.sync_start_pos(prefs.sync_notes_start_pos_time_delta, False)

 if prefs.save_to_disk_per_channel:
   status, prefs.save_to_disk_message = midiOutFile.save_to_disk_per_channel(outputmid)
 else:
   status, prefs.save_to_disk_message = midiOutFile.save_to_disk(outputmid)
 return status


def reconstruct():
    # ... (full reconstruct code from v2m.py, unchanged)
    pass  # Replace with actual code