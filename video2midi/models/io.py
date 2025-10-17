import sys
import os
import re

filepath = ""

def open_windows_explorer():
    if sys.platform.startswith("win"):
        from tkinter import Tk
        from tkinter import filedialog as fd

        root = Tk()
        root.withdraw()
        filepath = fd.askopenfilename(
            filetypes=(
                ("Video Files", ".mpg .mkv .avi .webm .mp4"),
                ("All Files", "*.*"),
            )
        )
        
        root.destroy()
        print("get file [" + filepath + "]")
    else:
        print("halt, no args")
        sys.exit(0)
        
    return filepath

def download_youtube_link(url):
    has_pytube = False

    try:
        from pytube import YouTube
        has_pytube = True
        
    except:
        pass

    if has_pytube:
        print("Downloading video by url: %s ..." % filepath)
        yt = YouTube(filepath)
        videos = [
            {
                "itag": i.itag,
                "res": int(re.sub("[^0-9]", "", i.resolution)),
                "progressive": int(i.is_progressive),
            }
            for i in yt.streams.filter(file_extension="mp4")
            if i.mime_type.find("video") != -1
        ]
        print(videos)
        videos = sorted(videos, key=lambda d: (-d["progressive"], -d["res"]))
        print(
            "sorted by progressive (has video & audio in same file) and video resolution"
        )
        for i in videos:
            print("processing: %s" % i)
            filepath = "%s_%s_%s.mp4" % (
                re.sub(r"[\W_]", "_", yt.title),
                i["itag"],
                i["res"],
            )
            yt.streams.get_by_itag(i["itag"]).download(
                "./", filepath, skip_existing=True
            )
            break
    else:
        print(
            "file not exists [" + filepath + "], and no pytube has installed..., exit."
        )
        sys.exit(0)
            
    return filepath
