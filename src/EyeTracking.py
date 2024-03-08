import cv2
import pyautogui

SMOOTHING_FACTOR = 0.5
prev_x, prev_y = pyautogui.size()


def smooth_movement(x, y):
    global prev_x, prev_y
    smooth_x = prev_x + SMOOTHING_FACTOR * (x - prev_x)
    smooth_y = prev_y + SMOOTHING_FACTOR * (y - prev_y)
    prev_x, prev_y = smooth_x, smooth_y
    return int(smooth_x), int(smooth_y)


def track_gaze():
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_eye.xml')

    screen_width, screen_height = pyautogui.size()
    center_x, center_y = screen_width // 2, screen_height // 2

    cap = cv2.VideoCapture(1)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]

            eyes = eye_cascade.detectMultiScale(roi_gray)

            for (ex, ey, ew, eh) in eyes:
                eye_roi_gray = roi_gray[ey:ey+eh, ex:ex+ew]

                _, pupil_thresh = cv2.threshold(
                    eye_roi_gray, 40, 255, cv2.THRESH_BINARY_INV)
                contours, _ = cv2.findContours(
                    pupil_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                if contours:
                    pupil_contour = max(contours, key=cv2.contourArea)
                    moment = cv2.moments(pupil_contour)

                    if moment["m00"] != 0:
                        pupil_center = (
                            int(moment["m10"] / moment["m00"]) + ex, int(moment["m01"] / moment["m00"]) + ey)

                        dx = pupil_center[0] - center_x
                        dy = pupil_center[1] - center_y

                        mouse_x, mouse_y = smooth_movement(
                            center_x + dx, center_y + dy)
                        pyautogui.moveTo(mouse_x, mouse_y)

                        cv2.circle(roi_color, pupil_center,
                                   2, (0, 255, 255), -1)

        cv2.imshow('Gaze Tracker', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    track_gaze()
