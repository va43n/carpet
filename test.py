import cv2
from picamera2 import Picamera2

if __name__ == '__main__':
    print('start')

    print(input("sgkdfhgl: "))

    while True:
        print('video')

        cam = Picamera2()
        cam.configure(cam.create_preview_configuration(
                      main={'size': (1920, 1080)}))
        cam.start()
        while True:
            frame = cam.capture_array()
            flipped_frame = cv2.flip(frame, 0)
            cv2.imshow("test", flipped_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cam.stop()
        cam.close()
        cv2.destroyAllWindows()

        if input("input: ") == 'q':
            break
        else:
            continue

    print('end')
