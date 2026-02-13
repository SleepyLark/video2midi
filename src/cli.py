"""
cli.py - CLI and entrypoint logic for video2midi
Handles argument parsing, file dialog, and video download via pytube.
"""

import sys
import os
import re
from os.path import expanduser


import logging
logger = logging.getLogger(__name__)

def get_video_filepath():
    """
    Handles CLI argument parsing, file dialog (Windows), and pytube download fallback.
    Returns the path to the video file to process.
    """
    filepath = ''
    if len(sys.argv) < 2:
        if sys.platform.startswith('win'):
            from tkinter import Tk
            from tkinter import filedialog as fd
            root = Tk()
            root.withdraw()
            filepath = fd.askopenfilename(filetypes=(
                ("Video Files", ".mpg .mkv .avi .webm .mp4"),
                ("All Files", "*.*")
            ))
            root.destroy()
            logger.debug(f"Get file [{filepath}]")
        else:
            logger.debug("Halt, no args")
            sys.exit(0)
    else:
        filepath = sys.argv[1]

    if not os.path.exists(filepath):
        has_pytube = False
        try:
            from pytube import YouTube
            has_pytube = True
        except ImportError:
            pass
        if has_pytube:
            logger.info(f"Downloading video by url: {filepath} ...")
            yt = YouTube(filepath)
            videos = [
                {
                    'itag': i.itag,
                    'res': int(re.sub('[^0-9]', '', i.resolution)),
                    'progressive': int(i.is_progressive)
                }
                for i in yt.streams.filter(file_extension='mp4')
                if i.mime_type and i.mime_type.find("video") != -1
            ]
            print(videos)
            videos = sorted(videos, key=lambda d: (-d['progressive'], -d['res']))
            logger.debug('sorted by progressive (has video & audio in same file) and video resolution')
            for i in videos:
                logger.info(f'processing: {i}')
                filepath = f"{re.sub(r'[\W_]', '_', yt.title)}_{i['itag']}_{i['res']}.mp4"
                yt.streams.get_by_itag(i['itag']).download("./", filepath, skip_existing=True)
                break
        else:
            logger.info(f"File does not exist [{filepath}], and pytube isn't installed. Exiting...")
            sys.exit(0)
    return filepath

def get_ini_filepath():
    home = expanduser("~")
    inifile = os.path.join( home, '.v2m.ini')

    if os.path.exists( 'v2m.ini' ):
        inifile="v2m.ini"
        logger.debug("local config file exists.")
    return inifile
