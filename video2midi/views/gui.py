from gl import *
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from pygame.locals import *

def fit_to_the_screen() -> None:
  global width, height
  infoObject = pygame.display.Info()
  if (width > infoObject.current_w) or ( height > infoObject.current_h):
    print("try fit window to the screen")
    print("current window size: %sx%s" %(width,height))
    print("current screen size: %sx%s" %(infoObject.current_w, infoObject.current_h))
    ratio  = ( width / infoObject.current_w)
    width = int(width / ratio * 0.9 )
    height = int(height / ratio *0.9)
    print("new window size: %sx%s" %(width,height))

def resize_window() -> None:
  global screen, width, height

  if prefs.resize:
    width = prefs.resize_width
    height = prefs.resize_height
  else:
    width = video_width
    height = video_height
    fit_to_the_screen()
  screen = pygame.display.set_mode((width,height), DOUBLEBUF|OPENGL|pygame.RESIZABLE)

  doinit()

def loadImage(idframe=130):
  global image
  global convertCvtColor
  if running != 0:
    getFrame(idframe)
  #image2=cv2.resize(image, (int(video_width/4) , int(video_height/4)))

  print("load image from video " + str(width) + "x" + str(height) + " frame: "+ str(idframe))
  glPixelStorei(GL_UNPACK_ALIGNMENT,1)

  glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
  glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
  glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)
  error_on_load=False
  try:
    if ( convertCvtColor == 1 ):
      #print ("Loading RGB texture")
      glTexImage2D(GL_TEXTURE_2D, 0, 3, video_width, video_height, 0, GL_RGB, GL_UNSIGNED_BYTE, cv2.cvtColor(image,COLOR_BGR2RGB) )
    else:
      #print ("Loading BGR texture")
      glTexImage2D(GL_TEXTURE_2D, 0, 3, video_width, video_height, 0, GL_BGR, GL_UNSIGNED_BYTE, image )
    return
  except Exception as E:
     error_on_load=True
     print("Can't load image from video to OpenGL: %s" % E);

  if error_on_load:
    rvideo_width, rvideo_height = 512, 512
    print("Trying resize video image to %sx%s" % (rvideo_width, rvideo_height));
    try:
       rimage = cv2.resize(image  , (rvideo_width, rvideo_height))
       if ( convertCvtColor == 1 ):
         glTexImage2D(GL_TEXTURE_2D, 0, 3, rvideo_width, rvideo_height, 0, GL_RGB, GL_UNSIGNED_BYTE, cv2.cvtColor(rimage,COLOR_BGR2RGB) )
       else:
         glTexImage2D(GL_TEXTURE_2D, 0, 3, rvideo_width, rvideo_height, 0, GL_BGR, GL_UNSIGNED_BYTE, rimage )
    except Exception as E:
      print("Can't load image from video to OpenGL: %s" % E);
      
def drawframe( lastimage = None):
 global pyfont
 global helptext
 global mousex, mousey
 global keyp_colormap_colors_pos
 global keyp_colormap_pos
 global frame, image
 global printed_for_frame
 global notes_tmp
 global notes_pressed_color
 #global old_spark_color
 #global cur_spark_color
 print_for_frame_debug = False
 if printed_for_frame != frame:
  print_for_frame_debug = True
 printed_for_frame = frame

 scale=1.0
 mousex, mousey = pygame.mouse.get_pos()

 glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
 glViewport (0, 0, width, height)
 glMatrixMode (GL_PROJECTION)
 glLoadIdentity ()
 glOrtho(0, width, height, 0, -1, 100)
 glMatrixMode(GL_MODELVIEW)
 glLoadIdentity()
 glDisable(GL_DEPTH_TEST)

 glScale(scale,scale,1)
 glColor4f(1.0, 1.0, 1.0, 1.0)

 glBindTexture(GL_TEXTURE_2D, Gl.bgImgGL)
 glEnable(GL_TEXTURE_2D)
 DrawQuad(0,0,width,height)


 glEnable(GL_BLEND)
 glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

 glColor4f(1.0, 0.5, 1.0, 0.5)
 glPushMatrix()
 glTranslatef(prefs.xoffset_whitekeys,prefs.yoffset_whitekeys,0)
 glDisable(GL_TEXTURE_2D)

 for i in range( len( prefs.keys_pos) ):
  pixpos = getkeyp_pixel_pos(prefs.keys_pos[i][0],prefs.keys_pos[i][1])

  if (pixpos[0] == -1) and (pixpos[1] == -1):
     continue
  if lastimage is not None:
    keybgr=lastimage[ pixpos[1], pixpos[0] ]
  else:
    keybgr=image[ pixpos[1], pixpos[0] ]
  key= [ keybgr[2], keybgr[1],keybgr[0] ]

  keybgr=[0,0,0]
  sparkkey=[0,0,0]
  if prefs.use_sparks:
    sh = int(sparks_slider_height.value)
    if sh == 0:
        sh = 1
    for spark_y_add_pos in range (sh):
     sparkpixpos = getkeyp_pixel_pos(prefs.keys_pos[i][0],prefs.keyp_spark_y_pos - spark_y_add_pos )
     if not ((sparkpixpos[0] == -1) and (sparkpixpos[1] == -1)):
       keybgr   = image[ sparkpixpos[1], sparkpixpos[0] ]
       sparkkey = [ sparkkey[0] + keybgr[2],
                    sparkkey[1] + keybgr[1],
                    sparkkey[2] + keybgr[0] ]
    sparkkey = [ sparkkey[0] / sh,  sparkkey[1] / sh,sparkkey[2] / sh]
    #cur_spark_color[i] = sparkkey
  else:
    sparkkey = [0,0,0]

  note=i
  if ( note > 144 ):
    print("skip note > 144")
    continue
  keypressed=0

  pressedcolor=[0,0,0]
  if prefs.use_alternate_keys:
    delta = prefs.keyp_delta + prefs.keyp_colors_alternate_sensitivity[i]
    if ( abs( int(key[0]) - prefs.keyp_colors_alternate[i][0] ) > delta ) and ( abs( int(key[1]) - prefs.keyp_colors_alternate[i][1] ) > delta ) and ( abs( int(key[2]) - prefs.keyp_colors_alternate[i][2] ) > delta ):
      keypressed=1
      pressedcolor=prefs.keyp_colors_alternate[i]
  else:
      for key_id in range( len(prefs.keyp_colors) ):
       keyc = prefs.keyp_colors[key_id]
       spark_delta = prefs.keyp_colors_sparks_sensitivity[key_id]
       delta = prefs.keyp_delta
       if prefs.use_percolor_delta:
         if key_id < len( prefs.percolor_delta ):
           delta =  prefs.percolor_delta[ key_id ]


       if (keyc[0] != 0 ) or (keyc[1] != 0 ) or (keyc[2] != 0 ) :
         if ( abs( int(key[0]) - keyc[0] ) < delta ) and ( abs( int(key[1]) - keyc[1] ) < delta ) and ( abs( int(key[2]) - keyc[2] ) < delta ):
          keypressed=1
          pressedcolor = keyc
          notes_pressed_color[i] = keyc
          if prefs.use_sparks:
            #unpressed_by_spark_delta = ( abs( int(sparkkey[0]) - keyc[0] ) < spark_delta ) and ( abs( int(sparkkey[1]) - keyc[1] ) < spark_delta ) and ( abs( int(sparkkey[2]) - keyc[2] ) < spark_delta )
            has_spark_delta = ((sparkkey[0] - keyc[0] ) > spark_delta ) or ((sparkkey[1] - keyc[1] ) > spark_delta ) or ((sparkkey[2] - keyc[2] ) > spark_delta )
            #unpressed_by_spark_fade = ( cur_spark_color[i][0] <  old_spark_color[i][0]) and ( cur_spark_color[i][1] <  old_spark_color[i][1]) and ( cur_spark_color[i][2] <  old_spark_color[i][2])
            #unpressed_by_spark_fade_delta = ( abs( cur_spark_color[i][0] - old_spark_color[i][0]) > 20 )
            if print_for_frame_debug:
             print("note %d key_id %d spark_delta %d sparkkey vs keyc %d %d, %d %d, %d %d" % (note, key_id, spark_delta, sparkkey[0], keyc[0], sparkkey[1], keyc[1], sparkkey[2], keyc[2]))
            if ( not has_spark_delta ):
             keypressed=2
  notes_tmp[i] = keypressed

 if prefs.rollcheck:
  for i in range(1, len( prefs.keys_pos) -1 ):
      if prefs.rollcheck_priority == 0:
        if not iswhitekey(i):
        # Priority on Black keys
          if notes_tmp[i+1] >0: notes_tmp[i] = 0
          if notes_tmp[i-1] >0: notes_tmp[i] = 0
      else:
        if iswhitekey(i):
        # Priority on White keys
          if notes_tmp[i+1] >0: notes_tmp[i] = 0
          if notes_tmp[i-1] >0: notes_tmp[i] = 0

 for i in range( len( prefs.keys_pos) ):
  keypressed = notes_tmp[i]
  pressedcolor = notes_pressed_color[i]

  glPushMatrix()
  glTranslatef(prefs.keys_pos[i][0],prefs.keys_pos[i][1],0)

  glColor4f(1,1,1,0.5)
  if iswhitekey(i):
    glColor4f(0.57,0.57,0.57,0.55)
  DrawQuad(-0.5,-line_height,0.5, line_height )
  if ( keypressed != 0 ):
    #glColor4f(1.0, 0.5, 1.0, 0.9)
    glColor4f(pressedcolor[0]/255.0,pressedcolor[1]/255.0,pressedcolor[2]/255.0,0.9)
    DrawQuad(-6,-7,6,7)
    glColor4f(0,0,0,1)
    if ( keypressed == 1):
      DrawRect(-7,-9,7,9,3)
    else:
      DrawRect(-5,-7,5,7,3)
  else:
    glColor4f(0,0,0,1)
    DrawRect(-7,-7,7,7,1)
    glColor4f(0.5, 1, 1.0, 0.7)
    DrawQuad(-5,-5,5,5)
  if ( lastkeygrabid == i ):
    glColor4f(0.0, 0.5, 1.0, 0.7)
    DrawQuad(-4,-4,4,4)

  if ( separate_note_id == i ):
    glColor4f(0,1,0,1)
    DrawRect(-7,-12,7,12,2)
  if prefs.octave * 12 == i:
    glColor4f(1,0,0,1)
    DrawRect(-9,9,9,12,3)


  DrawQuad(-1,-1,1,1)
  glPopMatrix()
  glColor4f(0.0, 1.0, 1.0, 0.7)
  # Sparks
  if prefs.use_sparks:
    glPushMatrix()
    glTranslatef(prefs.keys_pos[i][0], prefs.keyp_spark_y_pos ,0)
    glColor4f(0.5, 1, 1.0, 0.7)
    DrawQuad(-1,-1,1,1)
    DrawQuad(-0.5,-sparks_slider_height.value ,0.5,0)

    glPopMatrix()

 glPopMatrix()

 glDisable(GL_BLEND)
 glDisable(GL_TEXTURE_2D)

 for i in range(len(glwindows)):
   glwindows[i].draw()

 # drawing hints over all windows
 for i in range(len(glwindows)):
   glwindows[i].drawhint()

 prefs.keyp_delta = int(settingsWindow_slider1.value)
 prefs.minimal_duration = settingsWindow_slider2.value *0.01
 prefs.tempo = int(settingsWindow_slider3.value)

 settingsWindow_label1.text = "base octave: " + str(prefs.octave)
 # + "\nnotes overlap: " + str(prefs.notes_overlap) + "\nignore minimal duration: " + str(prefs.ignore_minimal_duration)
 #settingsWindow_label2.text = "Sensitivity:"+str(keyp_delta)+"\n\nMinimal note duration (sec):"+format(minimal_duration,'.2f' ) +   "\n\nOutput tempo for midi:" + str(tempo)
 for i in range(len(prefs.keyp_colors)):
     colorBtns[i].color = prefs.keyp_colors[i]

 glPushMatrix()
 glTranslatef(mousex,mousey,0)
 glColor4f(0.2, 0.5, 1, 0.9)
 DrawQuad(-1,-1,1,1)
 glPopMatrix()

 if showoutputpath > time.time():
  drawHint( width *0.5, height -20, prefs.save_to_disk_message, True)

def update_size() -> None:
  global width, height
  if ( prefs.resize == 1 ):
    width = prefs.resize_width
    height = prefs.resize_height
  else:
    fit_to_the_screen()

def loadImage(idframe=130):
  global image
  global convertCvtColor
  if running != 0:
    getFrame(idframe)
  #image2=cv2.resize(image, (int(video_width/4) , int(video_height/4)))

  print("load image from video " + str(width) + "x" + str(height) + " frame: "+ str(idframe))
  glPixelStorei(GL_UNPACK_ALIGNMENT,1)

  glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
  glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
  glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)
  error_on_load=False
  try:
    if ( convertCvtColor == 1 ):
      #print ("Loading RGB texture")
      glTexImage2D(GL_TEXTURE_2D, 0, 3, video_width, video_height, 0, GL_RGB, GL_UNSIGNED_BYTE, cv2.cvtColor(image,COLOR_BGR2RGB) )
    else:
      #print ("Loading BGR texture")
      glTexImage2D(GL_TEXTURE_2D, 0, 3, video_width, video_height, 0, GL_BGR, GL_UNSIGNED_BYTE, image )
    return
  except Exception as E:
     error_on_load=True
     print("Can't load image from video to OpenGL: %s" % E);

  if error_on_load:
    rvideo_width, rvideo_height = 512, 512
    print("Trying resize video image to %sx%s" % (rvideo_width, rvideo_height));
    try:
       rimage = cv2.resize(image  , (rvideo_width, rvideo_height))
       if ( convertCvtColor == 1 ):
         glTexImage2D(GL_TEXTURE_2D, 0, 3, rvideo_width, rvideo_height, 0, GL_RGB, GL_UNSIGNED_BYTE, cv2.cvtColor(rimage,COLOR_BGR2RGB) )
       else:
         glTexImage2D(GL_TEXTURE_2D, 0, 3, rvideo_width, rvideo_height, 0, GL_BGR, GL_UNSIGNED_BYTE, rimage )
    except Exception as E:
      print("Can't load image from video to OpenGL: %s" % E);

def doinit():
  doinitGl()
  loadImage()
  GenFontTexture()