import cv2, time, pandas
from datetime import datetime
import pyaudio
import math
import pyaudio



def playTone( freq , length): 

    bit_rate = 15000 #number of frames per second/frameset.      

    frequency = freq #in Hz, waves per second
    play_time = length #in seconds to play sound

    if frequency > bit_rate:
        bit_rate = frequency+100

    num_frames = int(bit_rate * play_time)
    total_frames = num_frames % bit_rate
    wave_info = ''    

    for x in range(num_frames):
     wave_info = wave_info+chr(int(math.sin(x/((bit_rate/frequency)/math.pi))*127+128))    

    for x in range(total_frames): 
     wave_info = wave_info+chr(128)

    p = PyAudio()
    stream = p.open(format = p.get_format_from_width(1), 
                    channels = 1, 
                    rate = bit_rate, 
                    output = True)
    stream.write(wave_info)
    


if __name__ == '__main__':
    frequency = 1500 #Hz
    duration = 0.4 #seconds

    PyAudio = pyaudio.PyAudio

    #Function to play frequency for given duration

    playTone(frequency , duration)


    first_frame = None
    status_list = [None, None]
    times = []
    df = pandas.DataFrame(columns=["Start","End"])

    video = cv2.VideoCapture(0)

    video.open(0)
    if video.isOpened():
        time.sleep(2)

    while True:
        check, frame = video.read()

        status = 0

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21,21), 0)

        if first_frame is None:
            first_frame = gray
            continue

        # this calculates difference between current frame and first frame
        delta_frame = cv2.absdiff(first_frame, gray)

        # this is to emphasize changes (black vs white)
        thresh_frame = cv2.threshold(delta_frame, 30, 255, cv2.THRESH_BINARY)[1]

        # this is for removing black holes, smooth out thresh frames
        thresh_frame = cv2.dilate(thresh_frame, None, iterations=2)

        # finds contours, detects if there is any change
        (_, cnts, _) = cv2.findContours(thresh_frame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in cnts:
            if cv2.contourArea(contour) < 20000:
                continue


            status = 1


            (x, y, w, h) = cv2.boundingRect(contour)
            centerLoc = [x + w/2, y + h/2]

            if centerLoc[0] > 400:
                if centerLoc[0] < 600:
                    newFreq = int((centerLoc[1]/40) * centerLoc[1])
                    print("(%i, %i)" %(centerLoc[0],centerLoc[1]))
                    print("freq played: %fhz" %newFreq)
                    playTone(newFreq , duration)
            
            #cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)

        status_list.append(status)

        # check for changes and record the time it happened
        if status_list[-1] == 1 and status_list[-2] == 0:
            times.append(datetime.now())

        if status_list[-1] == 0 and status_list[-2] == 1:
            times.append(datetime.now())


        cv2.imshow("Capturing", gray)
        cv2.imshow("Delta Frame", delta_frame)
        cv2.imshow("Threshold Frame", thresh_frame)
        cv2.imshow("Color Frame", frame)

        key = cv2.waitKey(1)
        # print(gray)

        if key == ord('q'):
            if status == 1:
                stream.stop_stream()
                stream.close()
                p.terminate()
                times.append(datetime.now())
            break

    print(status_list)
    print(times)

    for i in range(0, len(times), 2):
        df = df.append({"Start":times[i],"End":times[i+1]},ignore_index=True)

    df.to_csv("Times.csv")

    video.release()
    cv2.destroyAllWindows

