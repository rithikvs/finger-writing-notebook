import cv2
import mediapipe as mp
import numpy as np
import time
import math

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

canvas = np.zeros((480, 640, 3), dtype=np.uint8)

# Undo/Redo stacks
canvas_history = [canvas.copy()]
history_index = 0
MAX_HISTORY = 50
last_undo_time = 0
last_redo_time = 0
UNDO_REDO_COOLDOWN = 0.3
fist_ready_state = False

prev_x, prev_y = None, None
smooth_x, smooth_y = None, None

color = (255, 0, 0)
mode = "draw"
thickness = 5

# Stability controls
SMOOTHING = 0.65
MIN_MOVE = 1
UI_HOVER_TIME = 0.6
last_hover_time = 0
current_hover = None
writing_active = False
hand_was_visible = False
gesture_stable_count = 0
GESTURE_STABILITY_THRESHOLD = 2
GESTURE_STOP_THRESHOLD = 5

buttons = {
    "blue":   (10, 10, 110, 60),
    "green":  (120, 10, 220, 60),
    "red":    (230, 10, 330, 60),
    "eraser": (340, 10, 460, 60),
    "clear":  (470, 10, 630, 60),
}

def draw_buttons(frame):
    cv2.rectangle(frame, buttons["blue"][:2], buttons["blue"][2:], (255,0,0), -1)
    cv2.rectangle(frame, buttons["green"][:2], buttons["green"][2:], (0,255,0), -1)
    cv2.rectangle(frame, buttons["red"][:2], buttons["red"][2:], (0,0,255), -1)
    cv2.rectangle(frame, buttons["eraser"][:2], buttons["eraser"][2:], (60,60,60), -1)
    cv2.rectangle(frame, buttons["clear"][:2], buttons["clear"][2:], (120,120,120), -1)
    cv2.putText(frame, "ERASE", (355,45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
    cv2.putText(frame, "CLEAR", (485,45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

def inside(box, x, y):
    x1,y1,x2,y2 = box
    return x1 < x < x2 and y1 < y < y2

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    draw_buttons(frame)

    now = time.time()
    
    if result.multi_hand_landmarks:
        hand = result.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

        h, w, _ = frame.shape
        ix = int(hand.landmark[8].x * w)
        iy = int(hand.landmark[8].y * h)
        index_tip_y = iy
        index_pip_y = int(hand.landmark[6].y * h)
        index_mcp_y = int(hand.landmark[5].y * h)

        thumb_tip_x = int(hand.landmark[4].x * w)
        thumb_tip_y = int(hand.landmark[4].y * h)
        thumb_ip_x = int(hand.landmark[3].x * w)
        thumb_ip_y = int(hand.landmark[3].y * h)
        thumb_mcp_x = int(hand.landmark[2].x * w)
        thumb_mcp_y = int(hand.landmark[2].y * h)
        
        # Check other fingers
        middle_tip_y = int(hand.landmark[12].y * h)
        middle_pip_y = int(hand.landmark[10].y * h)
        ring_tip_y = int(hand.landmark[16].y * h)
        ring_pip_y = int(hand.landmark[14].y * h)
        pinky_tip_y = int(hand.landmark[20].y * h)
        pinky_pip_y = int(hand.landmark[18].y * h)

        # Strict gesture detection - ONLY index extended
        index_extended = index_tip_y < index_pip_y - 20
        middle_extended = middle_tip_y < middle_pip_y - 20
        ring_extended = ring_tip_y < ring_pip_y - 20
        pinky_extended = pinky_tip_y < pinky_pip_y - 20
        
        # Very strict thumb tracking - thumb MUST be completely closed
        thumb_horizontal_dist = abs(thumb_tip_x - thumb_ip_x)
        thumb_extended_from_palm = abs(thumb_tip_x - thumb_mcp_x)
        
        # Relax thumb detection slightly if already writing (prevent breaks mid-stroke)
        if writing_active:
            thumb_closed = (thumb_horizontal_dist < 35 and thumb_extended_from_palm < 50)
        else:
            thumb_closed = (thumb_horizontal_dist < 25 and thumb_extended_from_palm < 40)
        
        middle_closed = middle_tip_y > middle_pip_y - 10
        ring_closed = ring_tip_y > ring_pip_y - 10
        pinky_closed = pinky_tip_y > pinky_pip_y - 10
        
        # Fist gesture: All fingers closed including thumb (ready state)
        thumb_fist = abs(thumb_tip_x - thumb_mcp_x) < 50 and abs(thumb_tip_y - thumb_mcp_y) < 80
        all_fingers_closed = not index_extended and middle_closed and ring_closed and pinky_closed
        fist_gesture = thumb_fist and all_fingers_closed
        
        # Peace sign: Index + middle extended, others closed (undo from fist)
        peace_sign = index_extended and middle_extended and ring_closed and pinky_closed
        thumb_neutral = abs(thumb_tip_x - thumb_mcp_x) < 60
        peace_gesture = peace_sign and thumb_neutral
        
        # Open hand: All 5 fingers extended (redo from fist)
        all_fingers_open = index_extended and middle_extended and ring_extended and pinky_extended
        thumb_open = abs(thumb_tip_x - thumb_mcp_x) > 40
        open_hand_gesture = all_fingers_open and thumb_open
        
        # State machine: Fist activates ready state, then peace/open hand trigger actions
        if fist_gesture:
            fist_ready_state = True
        elif fist_ready_state:
            # Undo: Peace sign after fist
            if peace_gesture and now - last_undo_time > UNDO_REDO_COOLDOWN:
                if history_index > 0:
                    history_index -= 1
                    canvas = canvas_history[history_index].copy()
                    last_undo_time = now
                    prev_x, prev_y = None, None
                    writing_active = False
                fist_ready_state = False
            
            # Redo: Open hand after fist
            elif open_hand_gesture and now - last_redo_time > UNDO_REDO_COOLDOWN:
                if history_index < len(canvas_history) - 1:
                    history_index += 1
                    canvas = canvas_history[history_index].copy()
                    last_redo_time = now
                    prev_x, prev_y = None, None
                    writing_active = False
                fist_ready_state = False
        
        # Writing gesture detected (only if not undo/redo gestures)
        gesture_detected = index_extended and thumb_closed and middle_closed and ring_closed and pinky_closed and not peace_gesture and not open_hand_gesture and not fist_gesture
        
        # Stabilize gesture - easier to start, harder to stop (prevents breaks)
        if gesture_detected:
            gesture_stable_count = min(gesture_stable_count + 1, GESTURE_STOP_THRESHOLD + 1)
        else:
            # Decrease slowly if writing is active
            if writing_active:
                gesture_stable_count = max(gesture_stable_count - 1, 0)
            else:
                gesture_stable_count = max(gesture_stable_count - 2, 0)
        
        # Only change writing state if gesture is stable
        writing_gesture = gesture_stable_count >= GESTURE_STABILITY_THRESHOLD

        # --------- SMOOTHING ----------
        if smooth_x is None:
            smooth_x, smooth_y = ix, iy
        else:
            smooth_x = int(SMOOTHING * smooth_x + (1 - SMOOTHING) * ix)
            smooth_y = int(SMOOTHING * smooth_y + (1 - SMOOTHING) * iy)

        # --------- UI HOVER (NON-BLOCKING) ----------
        hovered = None
        if smooth_y < 70 and index_extended:
            for name, box in buttons.items():
                if inside(box, smooth_x, smooth_y):
                    hovered = name
                    break

            if hovered == current_hover:
                if now - last_hover_time > UI_HOVER_TIME:
                    if hovered == "blue":   color=(255,0,0); mode="draw"
                    if hovered == "green":  color=(0,255,0); mode="draw"
                    if hovered == "red":    color=(0,0,255); mode="draw"
                    if hovered == "eraser": mode="erase"
                    if hovered == "clear":
                        canvas[:] = 0
                        prev_x, prev_y = None, None
                        # Save clear action to history
                        canvas_history = canvas_history[:history_index + 1]
                        canvas_history.append(canvas.copy())
                        if len(canvas_history) > MAX_HISTORY:
                            canvas_history.pop(0)
                        else:
                            history_index += 1
                    last_hover_time = now + 1
            else:
                current_hover = hovered
                last_hover_time = now

        # --------- WRITE LOGIC ----------
        # If hand just became visible, start fresh stroke
        if not hand_was_visible:
            prev_x, prev_y = None, None
            writing_active = False
            gesture_stable_count = 0
        
        hand_was_visible = True
        
        if writing_gesture and smooth_y > 70:
            if prev_x is not None and prev_y is not None:
                dist = math.hypot(smooth_x - prev_x, smooth_y - prev_y)
                # Draw for almost any movement, very forgiving
                if dist >= MIN_MOVE and dist < 100:
                    if mode == "draw":
                        cv2.line(canvas, (prev_x, prev_y), (smooth_x, smooth_y), color, thickness)
                    else:
                        cv2.circle(canvas, (smooth_x, smooth_y), 22, (0,0,0), -1)
                # Always update position to maintain continuity
                prev_x, prev_y = smooth_x, smooth_y
            else:
                # Start new stroke - save canvas state for undo
                if writing_active == False:
                    # Remove future history when starting new action
                    canvas_history = canvas_history[:history_index + 1]
                    canvas_history.append(canvas.copy())
                    # Limit history size
                    if len(canvas_history) > MAX_HISTORY:
                        canvas_history.pop(0)
                    else:
                        history_index += 1
                prev_x, prev_y = smooth_x, smooth_y
            writing_active = True
        else:
            if writing_active and gesture_stable_count == 0:
                # Only end stroke when gesture completely stops
                prev_x, prev_y = None, None
                writing_active = False

    else:
        # Hand lost - immediately reset to prevent connecting lines
        hand_was_visible = False
        prev_x, prev_y = None, None
        writing_active = False
        gesture_stable_count = 0
        # Keep smooth_x, smooth_y for display continuity

    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    _, inv = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY_INV)
    inv = cv2.cvtColor(inv, cv2.COLOR_GRAY2BGR)
    frame = cv2.bitwise_and(frame, inv)
    frame = cv2.bitwise_or(frame, canvas)

    cv2.imshow("Finger Writing Notebook (Smooth & Stable)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
