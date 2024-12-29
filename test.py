import cv2
from picamera2 import Picamera2

if __name__ == '__main__':
    print('start')

    cam = Picamera2()
    cam.configure(cam.create_preview_configuration(
                  main={'size': (1920, 1080)}))
    cam.start()

    backSub = cv2.createBackgroundSubtractorMOG2()

    while True:
        frame = cam.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        # flipped_frame = cv2.flip(frame, -1)

        fg_mask = backSub.apply(frame)

        retval, mask_thr = cv2.threshold(fg_mask, 220, 255,
                                        cv2.THRESH_BINARY)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask_eroded = cv2.morphologyEx(mask_thr, cv2.MORPH_OPEN, kernel)

        mask_for_ct = mask_eroded

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
    cv2.destroyAllWindows()

    print('end')
