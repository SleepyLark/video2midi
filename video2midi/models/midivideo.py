import cv2
import time

class MIDIVideo:
    vidcap = None
    
    frame= 0
    printed_for_frame=0
    convertCvtColor=1
    
    # For OpenCV 2.X ..
    CAP_PROP_FRAME_COUNT =0
    CAP_PROP_POS_FRAMES  =0
    CAP_PROP_POS_MSEC    =0
    CAP_PROP_FRAME_WIDTH =0
    CAP_PROP_FRAME_HEIGHT=0
    CAP_PROP_FPS         =0
    COLOR_BGR2RGB        =0

    length = 0
    video_width = 0
    video_height = 0
    fps = 0
    success,image = False

    debug_keys = 0

    width = 0
    height = 0
    
    def __init__(self,filepath):
        self.vidcap = cv2.VideoCapture( filepath )

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
        
        self.length = int(self.vidcap.get(self.CAP_PROP_FRAME_COUNT))
        self.video_width  = int(self.vidcap.get(self.CAP_PROP_FRAME_WIDTH))
        self.video_height = int(self.vidcap.get(self.CAP_PROP_FRAME_HEIGHT))
        self.fps    = float(self.vidcap.get(self.CAP_PROP_FPS))
        
        self.width = self.video_width
        self.height = self.video_height
        
        self.success,self.image = self.vidcap.read()
        
        self.vidcap.set(self.CAP_PROP_POS_FRAMES, self.frame)
        self.vidcap.set(cv2.CAP_PROP_BUFFERSIZE, 2)

    def getFrame(self, framenum:int = -1) -> None:
        if ( self.fps == 0 ):
            return
        goto_frame_by_msec=False

        if ( framenum != -1 ):
            #vidcap.set(CAP_PROP_POS_FRAMES, int(framenum) )
            # problems with mpeg formats ...
            if goto_frame_by_msec:
                oldframenum = int(round(self.vidcap.get(1)))
                frametime =  framenum * 1000.0 / fps
                print("go to frame time :" + str(frametime))
                success = self.vidcap.set(self.CAP_PROP_POS_MSEC, frametime)
                if not success:
                    print("Cannot set frame position from video file at " + str(framenum))
                    success = self.vidcap.set(self.CAP_PROP_POS_FRAMES, int(oldframenum) )
            else:
                success = self.vidcap.set(self.CAP_PROP_POS_FRAMES, framenum )

            curframe = self.vidcap.get(self.CAP_PROP_POS_FRAMES)
            if (curframe != framenum ):
                print("OpenCV bug, Requesting frame " + str(framenum) + " but get position on " +str(curframe))

        self.success,self.image = self.vidcap.read()
        #  if ( resize == 1 ):
        #    image = cv2.resize(image, (resize_width , resize_height))
        #    print "resize to "+str(resize_width) + "x"+ str(resize_height)