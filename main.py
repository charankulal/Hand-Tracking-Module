import sys
import threading
import time

from comtypes import CLSCTX_ALL

import HandTrackingModule as htm
import pyautogui
from videoCap import VideoGet, VideoShow, CountsPerSec, putIterationsPerSec
import cv2
from face_encoding import ref_img_face_encodings
import asyncio
from face_auth import check_auth
from config import get_auth, set_auth_frame, get_global_status
import pygetwindow as gw
import screen_brightness_control as sbc
import numpy as np
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

wCam = 640
hCam = 480



# declarations related to mouse control functionalities
wScreen, hScreen = pyautogui.size()
pyautogui.FAILSAFE = False
frameR = 100
smoothening = 3.5
plocX, plocY = 0, 0
clocX, clocY = 0, 0

video_getter = VideoGet().start()
video_shower = VideoShow(video_getter.frame).start()
cps = CountsPerSec().start()
face_auth_monitor = threading.Thread(target=check_auth)
face_auth_monitor.start()
# def main():
#     global video_getter,video_shower,cps
iterations = 0



devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = interface.QueryInterface(IAudioEndpointVolume)
volumeRange = volume.GetVolumeRange()
minimumVolume = volumeRange[0]
maximumVolume = volumeRange[1]
area = 0




def is_powerpoint_in_focus():
    windows = gw.getAllWindows()
    for window in windows:
        if "PowerPoint" in window.title:
            if window.isActive:
                return True
    return False


def is_powerpoint_in_presentation_mode():
    # Get a list of all open windows
    windows = gw.getAllWindows()

    # Iterate through the windows and check if any contain "PowerPoint Slide Show" in the title
    for window in windows:
        if "PowerPoint Slide Show" in window.title:
            return True
    return False  # If no PowerPoint presentation window is found



if len(ref_img_face_encodings) != 1:
    print("Multiple faces detected!. Single authority required.")
    video_getter.stop()
    video_shower.stop()
    face_auth_monitor.join(0.1)
    sys.exit()


detector = htm.HandDetector(maxHands=1)

while True:
    iterations += 1
    # print(iterations)
    if not get_global_status():
        continue

    if video_getter.stopped or video_shower.stopped:
        video_shower.stop()
        video_getter.stop()
        print("Video not rendering")
        break

    # Receive a frame
    frame = cv2.flip(video_getter.frame, 1)

    if iterations % 1000 == 0:
        set_auth_frame(frame)

    if not get_auth():
        cv2.putText(frame, "Not Authorized",(500, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255))
    else:
        img, which_hand = detector.findHands(frame)
        lmList, boundingBox = detector.findPosition(img, handNo=0, draw=True)
        if which_hand == "Right":
            if len(lmList) != 0:
                [x1, y1] = lmList[8][1:]
                [x2, y2] = lmList[12][1:]
                fingers = detector.fingersUp()
                cv2.rectangle(img, (frameR, frameR),
                              (wCam - frameR, hCam - frameR), (255, 0, 255), 2)

                # For hovering or pointer movement
                if fingers[1] == 1 and fingers[2] == 1 and fingers[0] == 0:
                    x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScreen))
                    y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScreen))

                    clocX = plocX + (x3 - plocX) / smoothening
                    clocY = plocY + (y3 - plocY) / smoothening

                    pyautogui.moveTo(clocX, clocY)
                    plocX, plocY = clocX, clocY

                if fingers[0] == 1 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
                    pyautogui.hotkey('win', 'a')
                    time.sleep(2)

                # Left click functionality

                if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0:
                    pyautogui.click()
                    cv2.putText(img, "Left Click", (170, 70),
                                cv2.FONT_HERSHEY_PLAIN, 2, (125, 125, 125), 3)
                    time.sleep(1)

                # Right click functionality
                if fingers[1] == 1 and fingers[2] == 1 and fingers[0] == 0:
                    if fingers[4] == 1:
                        cv2.putText(img, "Right Click", (170, 70),
                                    cv2.FONT_HERSHEY_PLAIN, 2, (125, 125, 125), 3)
                        pyautogui.rightClick()
                        time.sleep(1)

                area = (boundingBox[2] - boundingBox[0]) * \
                       (boundingBox[3] - boundingBox[1]) // 100
                # print(area)
                if not fingers[2]:
                    if 100 < area < 1000:

                        # Find the distance btwn index and thumb
                        length, img, lineInfo = detector.findDistance(4, 8, img=img)

                        # Converting length to volume
                        vol = np.interp(length, [10, 150], [0, 100])

                        # Reduce resolution to make smoother.
                        smoothness = 5
                        vol = smoothness * round(vol / smoothness)

                        # Check fingers which are up
                        fingers = detector.fingersUp()

                        # if pinky is down then set volume
                        if not fingers[4]:
                            volume.SetMasterVolumeLevelScalar(vol / 100, None)
        if which_hand == "Left":
            if len(lmList) != 0:
                [x1, y1] = lmList[8][1:]
                [x2, y2] = lmList[12][1:]
                fingers = detector.fingersUp()
                cv2.rectangle(img, (frameR, frameR),
                              (wCam - frameR, hCam - frameR), (255, 0, 255), 2)

                if is_powerpoint_in_presentation_mode():
                    if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[0] == 1:
                        pyautogui.press('backspace')
                        time.sleep(1)

                    elif fingers[1] == 1 and fingers[2] == 1 and fingers[0] == 1:
                        pyautogui.press('enter')
                        time.sleep(1)

                else:

                    # For hovering or pointer movement
                    if fingers[1] == 1 and fingers[2] == 1 and fingers[0] == 1:
                        x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScreen))
                        y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScreen))

                        clocX = plocX + (x3 - plocX) / smoothening
                        clocY = plocY + (y3 - plocY) / smoothening

                        pyautogui.moveTo(clocX, clocY)
                        plocX, plocY = clocX, clocY

                    # Left click functionality

                    if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0:
                        pyautogui.click()

                    # Right click functionality
                    if fingers[1] == 1 and fingers[2] == 1 and fingers[0] == 0:
                        if fingers[4] == 1:
                            pyautogui.rightClick()

                    area = (boundingBox[2] - boundingBox[0]) * \
                           (boundingBox[3] - boundingBox[1]) // 100
                    # print(area)
                    if not fingers[2]:
                        if 100 < area < 900:

                            # Find the distance btwn index and thumb
                            length, img, lineInfo = detector.findDistance(
                                4, 8, img=img)

                            # Converting length to volume
                            brightness = np.interp(length, [10, 150], [0, 100])

                            # Reduce resolution to make smoother.
                            smoothness = 5
                            brightness = smoothness * round(brightness / smoothness)

                            # if pinky is down then set volume
                            if not fingers[4]:
                                sbc.set_brightness(brightness)

    frame = putIterationsPerSec(frame, cps.countsPerSec())
    video_shower.frame = frame
    cps.increment()


