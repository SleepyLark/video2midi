from __future__ import annotations
from typing import TYPE_CHECKING
from ..settings import *
from .gl import *

if TYPE_CHECKING:
    from ..controller import AppController

class SettingsWindow(GLWindow):
    def __init__(self, app: AppController, x, y, w, h):
        super().__init__(x, y, w, h, "Settings")
        self.root = self
        self.app = app

        self.addButtons()
        self.addSliders()

        self.rollcheck_button.switch_status = self.app.prefs.rollcheck
        self.rollcheck_priority_button.switch_status = self.app.prefs.rollcheck_priority


    def addButtons(self):
        self.root.appendChild( GLButton(200, 20 ,140,20,0    , [128,128,128], "Start recreate midi"               , self.app.start_recreate_midi             , hint = "q - hot key") )
        self.root.appendChild( GLButton(200, 40 ,140,20,0    , [128,128,128], "Set start frame"                   , self.app.set_start_frame_to_current_frame, hint = "s - hot key, (mods : shift + s, set processing start frame to the beginning)" ) )
        self.root.appendChild( GLButton(200+141, 40 ,140,20,0, [128,128,128], "Set end frame"                     , self.app.set_end_frame_to_current_frame  , hint = "e - hot key, (mods : shift + e, set processing end frame to the ending)" ) )

        self.notes_overlap_btn = GLButton(200, 80 ,140,20,0, [128,128,128],  "Permit Note Restrike"                     , self.app.switch_notes_overlap            , hint = "o - hot key", switch=1, switch_status=0)
        self.root.appendChild( self.notes_overlap_btn )
        self.root.appendChild( GLButton(200+141, 80 ,140,20,0, [128,128,128],  "Sync notes"                    , self.app.switch_sync_notes_start_pos     , hint = "sync notes start pos", switch=1, switch_status=0) )
        self.ignore_notes_with_minimal_duration_btn = GLButton(200,100 ,281,20,0, [128,128,128],  "Ignore notes with minimal duration", self.app.switch_ignore_notes_with_minimal_duration, hint = "i - hot key", switch=1, switch_status=0)
        self.root.appendChild( self.ignore_notes_with_minimal_duration_btn )

        self.root.appendChild( GLButton(200,120 ,140,20,0, [128,128,128],  "Resize window"                     , self.app.switch_resize_windows           , hint = "r - hot key") )

        exit_switch = GLButton(200+141, 120 ,140,20,1, [128,128,128], "Auto-close" ,self.app.change_autoclose,switch=1, switch_status= self.app.prefs.autoclose, hint = "exit after the completion of the midi reconstruction" )
        self.root.appendChild( exit_switch )

        self.root.appendChild( GLButton(200    , 140 ,140,20,0, [128,128,128], "Save settings"                  , self.app.btndown_save_settings  , hint = "F2 - hot key, save current settings" ) )
        self.root.appendChild( GLButton(200+141, 140 ,140,20,0, [128,128,128], "Load settings"                  , self.app.btndown_load_settings  , hint = "F3 - hot key, load saved settings" ) )

        self.rollcheck_button = GLButton(200,160 ,140,20,1, [128,128,128], "Single Key Priority" ,self.app.change_rollcheck,switch=1, switch_status=self.app.prefs.rollcheck )
        self.root.appendChild(self.rollcheck_button)

        self.root.appendChild( GLButton(200+141, 160 ,140,20,1, [128,128,128], "Per channel save" ,self.app.change_save_to_disk_per_channel,switch=1, switch_status= self.app.prefs.save_to_disk_per_channel, hint = "split the output midi per channels" ) )

        self.rollcheck_priority_button = GLButton(200,180 ,222,20,1, [128,128,128], "Prioritize White Keys" ,self.app.change_rollcheck_priority,switch=1, switch_status=self.app.prefs.rollcheck_priority )
        self.root.appendChild(self.rollcheck_priority_button)

        label1 = GLLabel(10,0, "Base octave: " + str(self.app.prefs.octave))
        # + "\nnotes overlap: " + str(self.app.prefs.notes_overlap) + "\nignore minimal duration: " + str(self.app.prefs.ignore_minimal_duration))
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
              'func' : self.app.rotate_clockwise },
             {'name' : "R-", 'hint' : 'rotate the keys counterclockwise, hot key -',
              'func' : self.app.rotate_counter_clockwise }

           ]
        #btnfuncs = [ None,  None, None, None,  None, None ]
        for i in range(len( navbtns_info )):
            self.root.appendChild( GLButton(200 + i * 32,230 ,32,20,0, [128,128,128],  navbtns_info[i]['name'] , navbtns_info[i]['func'], hint = navbtns_info[i]['hint']) )

        self.root.appendChild( GLButton(200    , 295 ,140,20,0, [128,128,128], "Update count", self.app.change_key_count  , hint = "Change keys count" ) )
        self.root.appendChild( GLButton(200+141, 295 ,70,20,0, [128,128,128], "V. align", self.app.btndown_vertical_align_keys  , hint = "vertical alignment of keys to the selected key" ) )
        self.root.appendChild( GLButton(200+141+70, 295 ,70,20,0, [128,128,128], "H. align", self.app.btndown_halign_align_keys  , hint = "horizontal alignment of keys to the selected key" ) )



    def addSliders(self):
        self.key_sensitivity_slider = GLSpinBox(10,40, 81,18, 0,130,self.app.prefs.keyp_delta,label="Detection Sensitivity")
        self.key_sensitivity_slider.round=1
        self.root.appendChild(self.key_sensitivity_slider)

        self.minimal_duration_slider = GLSpinBox(10,90, 81,18, 0,200,self.app.prefs.minimal_duration*100,label="Minimal note duration (sec)")
        self.minimal_duration_slider.round=0
        self.root.appendChild(self.minimal_duration_slider)

        self.tempo_slider = GLSpinBox(10,133, 81,18, 30,240,self.app.prefs.tempo,label="Output tempo for MIDI")
        self.tempo_slider.round=0
        self.root.appendChild(self.tempo_slider)

        self.midi_format_slider = GLSpinBox(10,175, 81,18, 1,2,self.app.prefs.midi_file_format,label="Output MIDI format type")
        self.midi_format_slider.round=0
        self.root.appendChild(self.midi_format_slider)

        self.black_key_relative_pos_slider = GLSpinBox(10,215, 81,18, 0,1000,self.app.prefs.black_key_relative_position * 1000, update_func=self.app.update_black_key_relative_position, label="Black key relative pos")
        self.black_key_relative_pos_slider.round=0
        self.root.appendChild(self.black_key_relative_pos_slider)

        self.notes_time_delta_slider = GLSpinBox(10,255, 81,18, 0,1000,self.app.prefs.sync_notes_start_pos_time_delta, update_func=self.app.update_sync_notes_start_pos_time_delta, label="Sync notes time delta (ms)")
        self.notes_time_delta_slider.round=0
        self.root.appendChild(self.notes_time_delta_slider)

        self.key_count_slider = GLSpinBox(10,295, 81,18, 12,144,self.app.prefs.keys_pos_cnt, update_func=self.app.update_keys_pos_count, label="Keys count")
        self.key_count_slider.round=0
        self.root.appendChild(self.key_count_slider)