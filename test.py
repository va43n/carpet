import cv2
from picamera2 import Picamera2
import copy
import json

if __name__ == '__main__':
    print('start')

    cam = Picamera2()
    cam.configure(cam.create_preview_configuration({'size': (1920, 1080),
                                                    'format': 'RGB888'}))
    cam.start()

    all_exes = []

    with open('/home/login/Desktop/prog/db/task1/task.json') as f:
        data = json.load(f)
        description = data['description']
        for ex in data['all_exes']:
            all_exes.append([ex['img'], []])
            for fig in ex['ex_figs']:
                all_exes[-1][1].append([fig['name'],
                                        [fig['center'],
                                         fig['radius'],
                                         fig['angle']]])

    figures = {}
    new_figures = {}
    all_exes_count = len(all_exes)

    for key in all_exes[0][1]:
        figures[key[0]] = key[1]

    prev_frame = cam.capture_array()
    prev_frame = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

    while True:
        frame = cam.capture_array()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        diff = cv2.absdiff(frame_gray, prev_frame)
        blur = cv2.GaussianBlur(diff, (5, 5), 0)
        _, mask = cv2.threshold(blur, 30, 255, cv2.THRESH_BINARY)
        prev_frame = copy.deepcopy(frame_gray)

        mask_for_ct = mask

        contours, hierarchy = cv2.findContours(mask_for_ct,
                                               cv2.RETR_EXTERNAL,
                                               cv2.CHAIN_APPROX_SIMPLE)

        min_contour_area = 100
        large_contours = [ct for ct in contours if
                          cv2.contourArea(ct) > min_contour_area]

        frame_ct = cv2.drawContours(frame, large_contours, -1, (0, 255, 0), 2)

        ellipse = cv2.ellipse(frame_ct, figures['rect'][0], figures['rect'][1], 
           figures['rect'][2], 0, 360, (0, 255, 255), 2) 

        cv2.imshow("test", frame_ct)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.stop()
    cam.close()

    print('end')
