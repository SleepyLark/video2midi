"""
video_io.py - Video input/output and frame handling for video2midi
Handles OpenCV VideoCapture, frame extraction, and video metadata.
"""

# Video IO logic will be moved here from v2m.py

import cv2

class VideoHandler:
    def __init__(self, filepath):
        self.filepath = filepath
        self.vidcap = cv2.VideoCapture(filepath)
        self.length = int(self.vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_width = int(self.vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.video_height = int(self.vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = float(self.vidcap.get(cv2.CAP_PROP_FPS))
        self.frame = 0
        self.success = False
        self.image = None
        self.convertCvtColor = True
        self.COLOR_BGR2RGB = cv2.COLOR_BGR2RGB
        # set start frame
        self.vidcap.set(cv2.CAP_PROP_POS_FRAMES, self.frame)
        self.vidcap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        self.success, self.image = self.vidcap.read()

        print("OpenCV version:" + cv2.__version__ )
        if cv2.__version__.startswith('2.'):
            self.CAP_PROP_FRAME_COUNT  = cv2.cv.CV_CAP_PROP_FRAME_COUNT
            self.CAP_PROP_POS_FRAMES   = cv2.cv.CV_CAP_PROP_POS_FRAMES
            self.CAP_PROP_POS_MSEC     = cv2.cv.CV_CAP_PROP_POS_MSEC
            self.CAP_PROP_FRAME_WIDTH  = cv2.cv.CV_CAP_PROP_FRAME_WIDTH
            self.CAP_PROP_FRAME_HEIGHT = cv2.cv.CV_CAP_PROP_FRAME_HEIGHT
            self.CAP_PROP_FPS          = cv2.cv.CV_CAP_PROP_FPS
        else:
        # 3, 4 , etc ...
            self.CAP_PROP_FRAME_COUNT  = cv2.CAP_PROP_FRAME_COUNT
            self.CAP_PROP_POS_FRAMES   = cv2.CAP_PROP_POS_FRAMES
            self.CAP_PROP_POS_MSEC     = cv2.CAP_PROP_POS_MSEC
            self.CAP_PROP_FRAME_WIDTH  = cv2.CAP_PROP_FRAME_WIDTH
            self.CAP_PROP_FRAME_HEIGHT = cv2.CAP_PROP_FRAME_HEIGHT
            self.CAP_PROP_FPS          = cv2.CAP_PROP_FPS

        self.COLOR_BGR2RGB         = cv2.COLOR_BGR2RGB

    def getFrame(self, framenum=-1):
        if self.fps == 0:
            return False, None

        goto_frame_by_msec = False
        if framenum != -1:
            if goto_frame_by_msec:
                oldframenum = int(round(self.vidcap.get(1)))
                frametime = framenum * 1000.0 / self.fps
                self.success = self.vidcap.set(cv2.CAP_PROP_POS_MSEC, frametime)

                if not self.success:
                    self.success = self.vidcap.set(cv2.CAP_PROP_POS_FRAMES, int(oldframenum))
            else:
                self.success = self.vidcap.set(cv2.CAP_PROP_POS_FRAMES, framenum)

            curframe = self.vidcap.get(cv2.CAP_PROP_POS_FRAMES)

            if curframe != framenum:
                print(f"OpenCV bug, Requesting frame {framenum} but get position on {curframe}")

        self.success, self.image = self.vidcap.read()
        if not self.success:
            print(f"Failed to read frame {framenum if framenum != -1 else 'current'}")
            self.image = None
            return False, None

        return self.success, self.image

    def loadImage(self, idframe=130):
        if self.image is None:
            return None
        self.getFrame(idframe)
        print(f"load image from video {self.video_width}x{self.video_height} frame: {idframe}")
        # For OpenGL texture upload, return RGB image
        if self.convertCvtColor:
            return cv2.cvtColor(self.image, self.COLOR_BGR2RGB)
        else:
            return self.image
