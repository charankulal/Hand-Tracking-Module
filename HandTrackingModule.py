import cv2
import mediapipe as mp
import time
import math
from google.protobuf.json_format import MessageToDict

class HandDetector():
    def __init__(self, mode=False, maxHands=2, detectionCon=1, trackCon=1):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands()
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        if self.results.multi_hand_landmarks:
            # Both Hands are present in image(frame)
            if len(self.results.multi_handedness) == 2:
                # Display 'Both Hands' on the image
                cv2.putText(img, 'Both Hands', (250, 50),
                            cv2.FONT_HERSHEY_COMPLEX,
                            0.9, (0, 255, 0), 2)

            # If any hand present
            else:
                for i in self.results.multi_handedness:

                    # Return whether it is Right or Left Hand
                    label = MessageToDict(i)['classification'][0]['label']

                    if label == 'Left':

                        # Display 'Left Hand' on
                        # left side of window
                        cv2.putText(img, label+' Hand',
                                    (20, 50),
                                    cv2.FONT_HERSHEY_COMPLEX,
                                    0.9, (0, 255, 0), 2)
                        return img,'Left'

                    if label == 'Right':

                        # Display 'Left Hand'
                        # on left side of window
                        cv2.putText(img, label+' Hand', (460, 50),
                                    cv2.FONT_HERSHEY_COMPLEX,
                                    0.9, (0, 255, 0), 2)
                        return img,'Right'
                # for handLms in self.results.multi_hand_landmarks:
                #     if draw:
                #         self.mpDraw.draw_landmarks(
                #             img, handLms, self.mpHands.HAND_CONNECTIONS)

        return img,"Both"

    def findPosition(self, img, handNo=0, draw=True):
        xList = []
        yList = []
        boundingBox = []
        self.lmList = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x*w), int(lm.y*h)
                xList.append(cx)
                yList.append(cy)
                self.lmList.append([id, cx, cy])
                # if draw:
                #     cv2.circle(img,(cx,cy),10,(255,0,255),cv2.FILLED)
            xMin, xMax = min(xList), max(xList)
            yMin, yMax = min(yList), max(yList)
            boundingBox = xMin, yMin, xMax, yMax

            if draw:
                cv2.rectangle(img, (boundingBox[0]-20, boundingBox[1]-20),
                              (boundingBox[2]+20, boundingBox[3]+20), (0, 255, 0), 2)
        return self.lmList, boundingBox

    def fingersUp(self):
        fingers = []
        # For thumb
        if self.lmList[self.tipIds[0]][1] < self.lmList[self.tipIds[0]-1][1]:
            fingers.append(1)
        else:
            fingers.append(0)
        for id in range(1, 5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id]-2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers

    def findDistance(self, p1, p2, img, draw=True):
        x1, y1 = self.lmList[p1][1], self.lmList[p1][2]
        x2, y2 = self.lmList[p2][1], self.lmList[p2][2]
        cx, cy = (x1+x2)//2, (y1+y2)//2

        if draw:
            cv2.circle(img, (x1, y1), 8, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 8, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 2)
            cv2.circle(img, (cx, cy), 8, (255, 0, 255), cv2.FILLED)

        length = math.hypot(x2-x1, y2-y1)

        return length, img, [x1, y1, x2, y2, cx, cy]
