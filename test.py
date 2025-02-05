import cv2
from picamera2 import Picamera2

if __name__ == '__main__':
    print('start')

    cam = Picamera2()
    cam.configure(cam.create_preview_configuration({'size': (1920, 1080),
                                                    'format': 'RGB888'}))
    cam.start()

    backSub = cv2.bgsegm.createBackgroundSubtractorMOG()

    prev_frame = cam.capture_array()
    prev_frame = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

    while True:
        frame = cam.capture_array()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # mask = backSub.apply(frame)

        diff = cv2.absdiff(frame_gray, prev_frame)
        blur = cv2.GaussianBlur(diff, (5, 5), 0)
        _, mask = cv2.threshold(blur, 30, 255, cv2.THRESH_BINARY)
        prev_frame = frame_gray

        # cv2.imshow("test", mask)

        # retval, mask_thr = cv2.threshold(mask, 170, 255,
        #                                  cv2.THRESH_BINARY)

        # kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        # mask_eroded = cv2.morphologyEx(mask_thr, cv2.MORPH_OPEN, kernel)

        mask_for_ct = mask

        contours, hierarchy = cv2.findContours(mask_for_ct,
                                               cv2.RETR_EXTERNAL,
                                               cv2.CHAIN_APPROX_SIMPLE)

        min_contour_area = 100
        large_contours = [ct for ct in contours if
                          cv2.contourArea(ct) > min_contour_area]

        frame_ct = cv2.drawContours(frame, large_contours, -1, (0, 255, 0), 2)

        cv2.imshow("test", frame_ct)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.stop()
    cam.close()

    print('end')
