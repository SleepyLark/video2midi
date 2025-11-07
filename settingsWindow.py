from video2midi.prefs import prefs
from video2midi.settings import *
from video2midi.views.gl import *
from utils import v_rotate

class SettingsWindow(GLWindow):
    def __init__(self, app, x, y, w, h):
        super().__init__(x, y, w, h, "Settings")
        self.root = self
        self.app = app

        self.addButtons()
        self.addSliders()
        
        self.key_sensitivity_slider.setvalue(prefs.keyp_delta)
        self.minimal_duration_slider.setvalue(prefs.minimal_duration * 100)
        self.tempo_slider.setvalue(prefs.tempo)
        self.key_count_slider.setvalue(prefs.keys_pos_cnt)

        self.rollcheck_button.switch_status = prefs.rollcheck
        self.rollcheck_priority_button.switch_status = prefs.rollcheck_priority


    def addButtons(self):
        self.root.appendChild( GLButton(260, 20 ,140,20,0    , [128,128,128], "start recreate midi"               , self.app.start_recreate_midi             , hint = "q - hot key") )
        self.root.appendChild( GLButton(260, 40 ,140,20,0    , [128,128,128], "set start frame"                   , self.app.set_start_frame_to_current_frame, hint = "s - hot key, (mods : shift + s, set processing start frame to the beginning)" ) )
        self.root.appendChild( GLButton(260+141, 40 ,140,20,0, [128,128,128], "set end frame"                     , self.app.set_end_frame_to_current_frame  , hint = "e - hot key, (mods : shift + e, set processing end frame to the ending)" ) )

        self.notes_overlap_btn = GLButton(260, 80 ,140,20,0, [128,128,128],  "notes overlap"                     , self.app.switch_notes_overlap            , hint = "o - hot key", switch=1, switch_status=0)
        self.ignore_notes_with_minimal_duration_btn = GLButton(260,100 ,272,20,0, [128,128,128],  "ignore notes with minimal duration", self.app.switch_ignore_notes_with_minimal_duration, hint = "i - hot key", switch=1, switch_status=0)
        self.root.appendChild( self.notes_overlap_btn )
        self.root.appendChild( self.ignore_notes_with_minimal_duration_btn )

        self.root.appendChild( GLButton(260+141, 80 ,140,20,0, [128,128,128],  "sync notes"                    , self.app.switch_sync_notes_start_pos     , hint = "sync notes start pos", switch=1, switch_status=0) )
        self.root.appendChild( GLButton(260,120 ,140,20,0, [128,128,128],  "resize window"                     , self.app.switch_resize_windows           , hint = "r - hot key") )

        exit_switch = GLButton(260+141, 120 ,140,20,1, [128,128,128], "auto-close" ,self.app.change_autoclose,switch=1, switch_status= prefs.autoclose, hint = "exit after the completion of the midi reconstruction" )
        self.root.appendChild( exit_switch )

        self.root.appendChild( GLButton(260    , 140 ,140,20,0, [128,128,128], "save settings"                  , self.app.btndown_save_settings  , hint = "F2 - hot key, save current settings" ) )
        self.root.appendChild( GLButton(260+141, 140 ,140,20,0, [128,128,128], "load settings"                  , self.app.btndown_load_settings  , hint = "F3 - hot key, load saved settings" ) )

        self.rollcheck_button = GLButton(260,160 ,140,22,1, [128,128,128], "roll check" ,self.app.change_rollcheck,switch=1, switch_status=prefs.rollcheck )
        self.root.appendChild(self.rollcheck_button)

        self.root.appendChild( GLButton(260+141, 160 ,140,20,1, [128,128,128], "per channel save" ,self.app.change_save_to_disk_per_channel,switch=1, switch_status= prefs.save_to_disk_per_channel, hint = "split the output midi per channels" ) )

        self.rollcheck_priority_button = GLButton(260,180 ,222,22,1, [128,128,128], "rollcheck white keys priority" ,self.app.change_rollcheck_priority,switch=1, switch_status=prefs.rollcheck_priority )
        self.root.appendChild(self.rollcheck_priority_button)

        label1 = GLLabel(1,0, "base octave: " + str(prefs.octave))
        # + "\nnotes overlap: " + str(prefs.notes_overlap) + "\nignore minimal duration: " + str(prefs.ignore_minimal_duration))
        self.root.appendChild(label1)

        self.root.appendChild( GLButton(130,0 ,20,20,1, [128,128,128],  "+", self.app.raise_octave, hint = "] - hot key, move up base octave (+12 tones)" ) )
        self.root.appendChild( GLButton(150,0 ,20,20,1, [128,128,128], " -", self.app.lower_octave, hint = "[ - hot key, move down base octave (-12 tones)" ) )

        navbtns_info = [
             {'name' : "[<", 'hint' : 'Home - hot key, go to first frame',
              'func' : self.app.scroll_to_start },
             {'name' : "<<", 'hint' : 'PageDown - hot key, fast scroll backward',
              'func' : self.app.scroll_fast_prev },
             {'name' : " <", 'hint' : 'Shift+PageDown - shortcut, scroll backward by frame',
              'func' : self.app.scroll_prev_by_frame },
             {'name' : " >", 'hint' : 'Shift+PageUp - shortcut, scroll forward by frame',
              'func' : self.app.scroll_forward_by_frame },
             {'name' : ">>", 'hint' : 'PageUp - hot key,fast scroll forward',
              'func' : self.app.scroll_fast_forward },
             {'name' : "  >]", 'hint' : 'End - hot key, go to last frame',
              'func' : self.app.scroll_to_end },
             {'name' : "R+", 'hint' : 'rotate the keys clockwise, hot key +',
              'func' : self.app.rotate_cw },
             {'name' : "R-", 'hint' : 'rotate the keys counterclockwise, hot key -',
              'func' : self.app.rotate_ccw }

           ]
        #btnfuncs = [ None,  None, None, None,  None, None ]
        for i in range(len( navbtns_info )):
            self.root.appendChild( GLButton(260 + i * 32,230 ,32,20,0, [128,128,128],  navbtns_info[i]['name'] , navbtns_info[i]['func'], hint = navbtns_info[i]['hint']) )

        self.root.appendChild( GLButton(260    , 295 ,140,20,0, [128,128,128], "update count", self.app.change_cnt  , hint = "Change keys count" ) )
        self.root.appendChild( GLButton(260+141, 295 ,70,20,0, [128,128,128], "v. align", self.app.valign  , hint = "vertical alignment of keys to the selected key" ) )
        self.root.appendChild( GLButton(260+141+70, 295 ,70,20,0, [128,128,128], "h. align", self.app.halign  , hint = "horizontal alignment of keys to the selected key" ) )



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

        self.black_key_relative_pos_slider = GLSlider(1,215, 240,18, 0,1000,prefs.blackkey_relative_position * 1000, self.app.update_blackkey_relative_position, label="black key relative pos")
        self.black_key_relative_pos_slider.round=0
        self.root.appendChild(self.black_key_relative_pos_slider)

        self.notes_time_delta_slider = GLSlider(1,255, 240,18, 0,1000,prefs.sync_notes_start_pos_time_delta, self.app.update_sync_notes_start_pos_time_delta, label="sync notes time delta (ms)")
        self.notes_time_delta_slider.round=0
        self.root.appendChild(self.notes_time_delta_slider)

        self.key_count_slider = GLSlider(1,295, 240,18, 12,144,prefs.keys_pos_cnt,self.app.update_keys_pos_cnt, label="Keys count")
        self.key_count_slider.round=0
        self.root.appendChild(self.key_count_slider)