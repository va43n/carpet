import numpy as np
from numpy.linalg import norm
import cv2
from picamera2 import Picamera2


cam = Picamera2()
cam.configure(cam.create_preview_configuration(
    {'size': (1920, 1080), 'format': 'RGB888'}))
cam.start()

backSub = cv2.bgsegm.createBackgroundSubtractorMOG()

while True:
    frame = cam.capture_array()

    # frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    fg_mask = backSub.apply(frame)

    # cv2.imshow('Frame_final', fg_mask)

    # Отсечение на маске пикселей, насыщенность которых меньше 220
    retval, mask_thr = cv2.threshold(fg_mask, 170, 255,
                                     cv2.THRESH_BINARY)

    # Фильтрация очень маленьких объектов
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask_eroded = cv2.morphologyEx(mask_thr, cv2.MORPH_OPEN, kernel)

    mask_for_ct = mask_eroded

    # Нахождение контуров
    contours, hierarchy = cv2.findContours(mask_for_ct,
                                           cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)

    # Фильтрация контуров, количество пикселей в которых меньше 100
    min_contour_area = 200
    large_contours = [ct for ct in contours if
                      cv2.contourArea(ct) > min_contour_area]

    # frame_ct = cv2.drawContours(frame, large_contours, -1, (0, 255, 0), 2)

    frame_out = frame.copy()
    for cnt in large_contours:
        x, y, w, h = cv2.boundingRect(cnt)
        frame_out = cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 200), 3)

    cv2.imshow('Frame_final', frame)

    if cv2.waitKey(10) == 27:
        break

cam.stop()
cam.close()
