import sys
import os
import ntpath

from video2midi.models import *
def main():
  filepath = None
  
  if len(sys.argv) < 2:
    filepath = io.open_windows_explorer()
  else:
    filepath = sys.argv[1]
  
  if not os.path.exists(filepath):
    filepath = io.process_youtube_link(filepath)
    
  print(f'file opened [{filepath}]')
  
  # load video
  video = MIDIVideo(filepath)
  
  # create path for per-project settings and output MIDI
  outputmid= ntpath.basename( filepath ) + '_output.mid'
  settingsfile= filepath + '.ini'