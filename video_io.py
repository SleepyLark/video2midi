"""
video_io.py - Video input/output and frame handling for video2midi
Handles OpenCV VideoCapture, frame extraction, and video metadata.
"""

# Video IO logic will be moved here from v2m.py

import cv2

import logging
logger = logging.getLogger(__name__)

class VideoHandler:
    def __init__(self, filepath):
        self.filepath = filepath
        self.vidcap = cv2.VideoCapture(filepath)
        self.length = int(self.vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_width = int(self.vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.video_height = int(self.vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = float(self.vidcap.get(cv2.CAP_PROP_FPS))
        self.currentFrame = 0
        self.success = False
        self.image = None
        self.convertCvtColor = True
        self.COLOR_BGR2RGB = cv2.COLOR_BGR2RGB
        # set start frame
        self.vidcap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.vidcap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        self.success, self.image = self.vidcap.read()

        logger.debug("OpenCV version:" + cv2.__version__ )


        logger.debug("Video " + str(self.video_width) + "x" + str(self.video_height) +" fps: " + str(self.fps))

    def get_frame(self, framenum=-1):
        if self.fps == 0:
            return
        goto_frame_by_msec = False
        if framenum != -1:
            if goto_frame_by_msec:
                oldframenum = self.get_current_frame_int()
                frametime = framenum * 1000.0 / self.fps
                self.success = self.vidcap.set(cv2.CAP_PROP_POS_MSEC, frametime)

                if not self.success:
                    self.success = self.vidcap.set(cv2.CAP_PROP_POS_FRAMES, oldframenum)
            else:
                self.success = self.vidcap.set(cv2.CAP_PROP_POS_FRAMES, framenum)

            curframe = self.vidcap.get(cv2.CAP_PROP_POS_FRAMES)

            if curframe != framenum:
                logger.debug(f"OpenCV bug, Requesting frame {framenum} but get position on {curframe}")

        self.success, self.image = self.vidcap.read()

        return self.success, self.image

    def get_image(self, idframe=130):
        """image is a NumPy array with the shape [height, width, channels]"""
        if self.image is None:
            return None
        self.get_frame(idframe)
        logger.debug(f"Load image from video {self.video_width}x{self.video_height} frame: {idframe}")
        
        return self.image
        
    def get_current_frame_int(self) -> int:
        return int(round(self.vidcap.get(cv2.CAP_PROP_POS_FRAMES)))

