from video2midi.prefs import prefs
from video2midi.settings import *
from video2midi.views.gl import *
from utils import v_rotate

class SettingsWindow(GLWindow):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, "Settings")
        self.root = self

        self.key_sensitivity_slider.setvalue(prefs.keyp_delta)
        self.minimal_duration_slider.setvalue(prefs.minimal_duration * 100)
        self.tempo_slider.setvalue(prefs.tempo)
        self.key_count_slider.setvalue(prefs.keys_pos_cnt)

        self.rollcheck_button.switch_status = prefs.rollcheck
        self.rollcheck_priority_button.switch_status = prefs.rollcheck_priority

        self.addButtons()
        self.addSliders()

    def addButtons(self):
        self.root.appendChild( GLButton(260, 20 ,140,20,0    , [128,128,128], "start recreate midi"               , self.start_recreate_midi             , hint = "q - hot key") )
        self.root.appendChild( GLButton(260, 40 ,140,20,0    , [128,128,128], "set start frame"                   , self.set_start_frame_to_current_frame, hint = "s - hot key, (mods : shift + s, set processing start frame to the beginning)" ) )
        self.root.appendChild( GLButton(260+141, 40 ,140,20,0, [128,128,128], "set end frame"                     , self.set_end_frame_to_current_frame  , hint = "e - hot key, (mods : shift + e, set processing end frame to the ending)" ) )

        notes_overlap_btn = GLButton(260, 80 ,140,20,0, [128,128,128],  "notes overlap"                     , self.switch_notes_overlap            , hint = "o - hot key", switch=1, switch_status=0)
        ignore_notes_with_minimal_duration_btn = GLButton(260,100 ,272,20,0, [128,128,128],  "ignore notes with minimal duration", self.switch_ignore_notes_with_minimal_duration, hint = "i - hot key", switch=1, switch_status=0)
        self.root.appendChild( notes_overlap_btn )
        self.root.appendChild( ignore_notes_with_minimal_duration_btn )

        self.root.appendChild( GLButton(260+141, 80 ,140,20,0, [128,128,128],  "sync notes"                    , self.switch_sync_notes_start_pos     , hint = "sync notes start pos", switch=1, switch_status=0) )
        self.root.appendChild( GLButton(260,120 ,140,20,0, [128,128,128],  "resize window"                     , self.switch_resize_windows           , hint = "r - hot key") )

        exit_switch = GLButton(260+141, 120 ,140,20,1, [128,128,128], "auto-close" ,self.change_autoclose,switch=1, switch_status= prefs.autoclose, hint = "exit after the completion of the midi reconstruction" )
        self.root.appendChild( exit_switch )

        self.root.appendChild( GLButton(260    , 140 ,140,20,0, [128,128,128], "save settings"                  , self.btndown_save_settings  , hint = "F2 - hot key, save current settings" ) )
        self.root.appendChild( GLButton(260+141, 140 ,140,20,0, [128,128,128], "load settings"                  , self.btndown_load_settings  , hint = "F3 - hot key, load saved settings" ) )

        self.rollcheck_button = GLButton(260,160 ,140,22,1, [128,128,128], "roll check" ,self.change_rollcheck,switch=1, switch_status=prefs.rollcheck )
        self.root.appendChild(self.rollcheck_button)

        self.root.appendChild( GLButton(260+141, 160 ,140,20,1, [128,128,128], "per channel save" ,self.change_save_to_disk_per_channel,switch=1, switch_status= prefs.save_to_disk_per_channel, hint = "split the output midi per channels" ) )

        self.rollcheck_priority_button = GLButton(260,180 ,222,22,1, [128,128,128], "rollcheck white keys priority" ,self.change_rollcheck_priority,switch=1, switch_status=prefs.rollcheck_priority )
        self.root.appendChild(self.rollcheck_priority_button)

        label1 = GLLabel(1,0, "base octave: " + str(prefs.octave))
        # + "\nnotes overlap: " + str(prefs.notes_overlap) + "\nignore minimal duration: " + str(prefs.ignore_minimal_duration))
        self.root.appendChild(label1)

        self.root.appendChild( GLButton(130,0 ,20,20,1, [128,128,128],  "+", self.raise_octave, hint = "] - hot key, move up base octave (+12 tones)" ) )
        self.root.appendChild( GLButton(150,0 ,20,20,1, [128,128,128], " -", self.lower_octave, hint = "[ - hot key, move down base octave (-12 tones)" ) )

        navbtns_info = [
             {'name' : "[<", 'hint' : 'Home - hot key, go to first frame',
              'func' : self.scroll_to_start },
             {'name' : "<<", 'hint' : 'PageDown - hot key, fast scroll backward',
              'func' : self.scroll_fast_prev },
             {'name' : " <", 'hint' : 'Shift+PageDown - shortcut, scroll backward by frame',
              'func' : self.scroll_prev_by_frame },
             {'name' : " >", 'hint' : 'Shift+PageUp - shortcut, scroll forward by frame',
              'func' : self.scroll_forward_by_frame },
             {'name' : ">>", 'hint' : 'PageUp - hot key,fast scroll forward',
              'func' : self.scroll_fast_forward },
             {'name' : "  >]", 'hint' : 'End - hot key, go to last frame',
              'func' : self.scroll_to_end },
             {'name' : "R+", 'hint' : 'rotate the keys clockwise, hot key +',
              'func' : self.rotate_cw },
             {'name' : "R-", 'hint' : 'rotate the keys counterclockwise, hot key -',
              'func' : self.rotate_ccw }

           ]
        #btnfuncs = [ None,  None, None, None,  None, None ]
        for i in range(len( navbtns_info )):
            self.root.appendChild( GLButton(260 + i * 32,230 ,32,20,0, [128,128,128],  navbtns_info[i]['name'] , navbtns_info[i]['func'], hint = navbtns_info[i]['hint']) )

        self.root.appendChild( GLButton(260    , 295 ,140,20,0, [128,128,128], "update count", self.change_cnt  , hint = "Change keys count" ) )
        self.root.appendChild( GLButton(260+141, 295 ,70,20,0, [128,128,128], "v. align", self.valign  , hint = "vertical alignment of keys to the selected key" ) )
        self.root.appendChild( GLButton(260+141+70, 295 ,70,20,0, [128,128,128], "h. align", self.halign  , hint = "horizontal alignment of keys to the selected key" ) )



    def addSliders(self):
        self.key_sensitivity_slider = GLSlider(1,40, 240,18, 0,130,prefs.keyp_delta,label="Sensitivity")
        self.key_sensitivity_slider.round=1
        self.root.appendChild(self.key_sensitivity_slider)

        self.minimal_duration_slider = GLSlider(1,90, 240,18, 0,200,prefs.minimal_duration*100,label="Minimal note duration (sec)")
        self.minimal_duration_slider.round=0
        self.root.appendChild(self.minimal_duration_slider)

        self.tempo_slider = GLSlider(1,133, 240,18, 30,240,prefs.tempo,label="Output tempo for midi")
        self.tempo_slider.round=0
        self.root.appendChild(self.tempo_slider)

        self.midi_format_slider = GLSlider(1,175, 240,18, 1,2,prefs.midi_file_format,label="Output midi format type")
        self.midi_format_slider.round=0
        self.root.appendChild(self.midi_format_slider)

        self.black_key_relative_pos_slider = GLSlider(1,215, 240,18, 0,1000,prefs.blackkey_relative_position * 1000, update_blackkey_relative_position, label="black key relative pos")
        self.black_key_relative_pos_slider.round=0
        self.root.appendChild(self.black_key_relative_pos_slider)

        self.notes_time_delta_slider = GLSlider(1,255, 240,18, 0,1000,prefs.sync_notes_start_pos_time_delta, update_sync_notes_start_pos_time_delta, label="sync notes time delta (ms)")
        self.notes_time_delta_slider.round=0
        self.root.appendChild(self.notes_time_delta_slider)

        self.key_count_slider = GLSlider(1,295, 240,18, 12,144,prefs.keys_pos_cnt,update_keys_pos_cnt, label="Keys count")
        self.key_count_slider.round=0
        self.root.appendChild(self.key_count_slider)

    #TODO MOVE RUNNING TO UI AND PASS REFERENCE TO MAIN WINDOW
    def start_recreate_midi(sender):
        global running
        if prefs.autoclose == 1:
            running = False
        else:
            #reconstruct()
            pass

    def set_start_frame_to_current_frame(sender):
        if sender.index == 0:
            prefs.startframe = int(round(video.vidcap.get(1)))
        else:
            prefs.startframe = 0
        print("set start frame = "+ str(prefs.startframe))

    def set_end_frame_to_current_frame(sender):
        global endframe
        if sender.index == 0:
            endframe = int(round(video.vidcap.get(1)))
        else:
            endframe = video.length
        print("set end frame = "+ str(endframe), sender.index)

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
        appView.resize_window()

    def change_autoclose(sender):
        prefs.autoclose = sender.switch_status

    def btndown_save_settings(sender):
        settings.savesettings(settingsfile)

    def btndown_load_settings(sender):
        old_resize = prefs.resize
        loadsettings( settingsfile )
        update_alternate_label()
        if (prefs.resize != old_resize):
            appView.resize_window()

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

    def scroll_by_steps( steps ):
        video.currentFrame += steps
        if (video.currentFrame > video.length *0.99):
            video.currentFrame = math.trunc(video.length *0.99)
        if (video.currentFrame < 1):
            video.currentFrame=1
        appView.loadImage(video.loadImage(video.currentFrame))

    def scroll_forward_by_frame(sender):
        scroll_by_steps(1)

    def scroll_fast_forward(sender):
        scroll_by_steps(100)

    def scroll_prev_by_frame(sender):
        scroll_by_steps(-1)

    def scroll_fast_prev(sender):
        scroll_by_steps(-100)

    def scroll_to_start(sender):
        video.currentFrame=0
        appView.loadImage(video.loadImage(video.currentFrame))

    def scroll_to_end(sender):
        video.currentFrame=video.length-100
        appView.loadImage(video.loadImage(video.currentFrame))

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
        vertical_align_keys(align=1)

    def halign(sender):
        vertical_align_keys(align=0)

    def update_keys_pos_cnt(sender,value):
        prefs.keys_pos_cnt=int(value)

    def update_blackkey_relative_position(sender,value):
        prefs.blackkey_relative_position = value * 0.001
        update_key_positions()

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