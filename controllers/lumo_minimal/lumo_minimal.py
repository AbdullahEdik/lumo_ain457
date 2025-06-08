# lumo_minimal.py
#
# NAO controller reacts based on your physical webcam and recognized emotion.



from controller import Robot, LED
import numpy as np
import cv2
from deepface import DeepFace
import pyttsx3
import sys
import random

# ─────────────────────────────────────────────────────────────────────────────
# 1. CONFIGURABLE PARAMETERS
# ─────────────────────────────────────────────────────────────────────────────

TIME_STEP    = 32   # [ms] Webots control loop
WEBCAM_ID    = 0    # Index of your physical USB/webcam
DISPLAY_W    = 320  # Window width (pixels)
DISPLAY_H    = 240  # Window height (pixels)

# LED colors for each emotion (hex)
LED_COLORS = {
    "happy":      0x00FF00,  # green
    "sad":        0x0000FF,  # blue
    "angry":      0x9DD8E6,  # light blue
    "frightened": 0xFFFF00,  # yellow
    "surprise":   0xFF00FF,  # magenta
}

# ─────────────────────────────────────────────────────────────────────────────
# 2. SET UP PC WEBCAM
# ─────────────────────────────────────────────────────────────────────────────

cap = cv2.VideoCapture(WEBCAM_ID)
if not cap.isOpened():
    print(f"[ERROR] Cannot open webcam at index {WEBCAM_ID}")
    sys.exit(1)
print(f"[INFO] Webcam (ID={WEBCAM_ID}) opened successfully.")

# Lower capture resolution to reduce DeepFace load:
cap.set(cv2.CAP_PROP_FRAME_WIDTH, DISPLAY_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, DISPLAY_H)
cv2.namedWindow("Webcam Feed", cv2.WINDOW_AUTOSIZE)
cv2.moveWindow("Webcam Feed", 0, 0)

# ─────────────────────────────────────────────────────────────────────────────
# 3. INITIALIZE THE ROBOT
# ─────────────────────────────────────────────────────────────────────────────

robot = Robot()
print("[INFO] Webots Robot node initialized.")

# ─────────────────────────────────────────────────────────────────────────────
# 4. DEVICE SETUP: LEDs + Lines
# ─────────────────────────────────────────────────────────────────────────────

# 4.5. LEDs
face_left_led:  LED = robot.getDevice("Face/Led/Left")
face_right_led: LED = robot.getDevice("Face/Led/Right")
chest_led:      LED = robot.getDevice("ChestBoard/Led")
lfoot_led:      LED = robot.getDevice("LFoot/Led")
rfoot_led:      LED = robot.getDevice("RFoot/Led")

ALL_LEDS = [
    face_left_led, face_right_led,
    chest_led,
    lfoot_led, rfoot_led
]

# 4.7. Turn all LEDs off initially
for led in ALL_LEDS:
    led.set(0x000000)  # LED.set(rgb) uses 0xRRGGBB

# 4.8 Lines for reactions
happy_lines = [
    "System status: positive.",
    "Emotion detected: happiness.",
    "Cheerfulness level elevated.",
    "Mood: operationally optimal.",
    "Acknowledged: user is content.",
]

sad_lines = [
    ("Alert: low mood detected.", "Awaiting further instructions."),
    ("Emotion: sadness registered.", "Monitoring system for support."),
    ("Status: user appears down.", "Standing by for assistance."),
    ("Signal: sadness input.", "No action required unless specified."),
    ("Sadness noted.", "Maintaining operational readiness."),
]

angry_lines = [
    "Warning: elevated agitation detected.",
    "Calm protocols recommended.",
    "Aggression signal received.",
    "System advises relaxation.",
    "User anger logged, monitoring.",
]

frightened_lines = [
    ("Safety check initiated.", "No threats detected."),
    ("Alert: fear response active.", "System scanning environment."),
    ("Potential hazard evaluation ongoing.", "Status: secure."),
    ("User fear noted.", "Continuing surveillance."),
    ("Threat level: negligible.", "User safety confirmed."),
    ("Initiating reassurance protocol.", "No anomalies found."),
]

surprised_lines = [
    ("Unexpected input detected.", "Assessing situation."),
    ("Surprise signal received.", "No immediate changes."),
    ("Sudden change in expression noted.", "Awaiting further data."),
    ("Anomaly detected in user status.", "Monitoring continues."),
    ("Unexpected event logged.", "No action necessary."),
]


# ─────────────────────────────────────────────────────────────────────────────
# 5. INITIALIZE PYTTSX3 FOR SPEECH (PC speaker)
# ─────────────────────────────────────────────────────────────────────────────

tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 150)  # words per minute
print("[INFO] pyttsx3 TTS engine initialized.")

def speak(text: str):
    """Speak via PC speaker (pyttsx3)."""
    print(f"[TTS] {text}")
    tts_engine.say(text)
    tts_engine.runAndWait()

# ─────────────────────────────────────────────────────────────────────────────
# 6. HELPER: GRAB A FRAME FROM WEBCAM
# ─────────────────────────────────────────────────────────────────────────────

def get_webcam_frame():
    """
    Capture one frame from the PC webcam and return it as a BGR image.
    Returns None if frame read fails.
    """
    ret, frame = cap.read()
    if not ret:
        return None
    return cv2.resize(frame, (DISPLAY_W, DISPLAY_H))

# ─────────────────────────────────────────────────────────────────────────────
# 7. UTILITY: RESET ALL LEDs TO “OFF”
# ─────────────────────────────────────────────────────────────────────────────

def leds_off():
    """Turn every LED in ALL_LEDS to black (off)."""
    for led in ALL_LEDS:
        led.set(0x000000)


# ─────────────────────────────────────────────────────────────────────────────
# 8. EMOTION‐BASED SEQUENCES (motion + LED color + speech)
# ─────────────────────────────────────────────────────────────────────────────

def do_happy_sequence():
    
    print("[LED] HAPPY: setting LEDs → GREEN")
    for led in ALL_LEDS:
        led.set(LED_COLORS["happy"])
    robot.step(TIME_STEP)    

    speak(random.choice(happy_lines))

    print("[LED] HAPPY: turning LEDs OFF")
    leds_off()
    robot.step(TIME_STEP)

def do_sad_sequence():

    print("[LED] SAD: setting LEDs → BLUE")
    for led in ALL_LEDS:
        led.set(LED_COLORS["sad"])
    robot.step(TIME_STEP)

    sad_line1, sad_line2 = random.choice(sad_lines)
    speak(sad_line1)

    speak(sad_line2)

    print("[LED] SAD: turning LEDs OFF")
    leds_off()
    robot.step(TIME_STEP)

def do_angry_sequence():

    print("[LED] ANGRY: setting LEDs → RED")
    for led in ALL_LEDS:
        led.set(LED_COLORS["angry"])
    robot.step(TIME_STEP)

    speak(random.choice(angry_lines))

    print("[LED] ANGRY: turning LEDs OFF")
    leds_off()
    robot.step(TIME_STEP)

def do_frightened_sequence():

    print("[LED] FRIGHTENED: setting LEDs → YELLOW")
    for led in ALL_LEDS:
        led.set(LED_COLORS["frightened"])
    robot.step(TIME_STEP)

    frightened_line1, frightened_line2 = random.choice(frightened_lines)
    speak(frightened_line1)

    speak(frightened_line2)

    print("[LED] FRIGHTENED: turning LEDs OFF")
    leds_off()
    robot.step(TIME_STEP)

def do_surprised_sequence():

    print("[LED] SURPRISED: setting LEDs → MAGENTA")
    for led in ALL_LEDS:
        led.set(LED_COLORS["surprise"])
    robot.step(TIME_STEP)

    surprised_line1, surprised_line2 = random.choice(surprised_lines)
    speak(surprised_line1)
    
    print("[LED] SURPRISED: turning LEDs OFF")
    leds_off()
    robot.step(TIME_STEP)

# ─────────────────────────────────────────────────────────────────────────────
# 9. MAIN CONTROL LOOP
# ─────────────────────────────────────────────────────────────────────────────

print("[INFO] Entering main control loop. Press ESC in the 'Webcam Feed' window to exit.")
while robot.step(TIME_STEP) != -1:
    # 9.1. Grab one frame from the webcam
    frame = get_webcam_frame()
    if frame is None:
        print("[WARN] Frame read failed. Keeping joints & LEDs neutral.")
        leds_off()
        continue

    print("[DEBUG] Frame acquired from webcam.")

    # 9.2. Display raw frame & check for ESC key
    cv2.imshow("Webcam Feed", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC
        print("[INFO] ESC pressed. Exiting controller.")
        break

    # 9.3. Run DeepFace only every full loop (block until sequence completes)
    dominant_emotion = None
    try:
        small = cv2.resize(frame, (160, 120))
        analytics = DeepFace.analyze(small, actions=["emotion"], enforce_detection=False)
        print(f"[DEBUG] Raw DeepFace output: {analytics}")
        if isinstance(analytics, list) and len(analytics) > 0:
            analytics = analytics[0]
        if isinstance(analytics, dict) and "dominant_emotion" in analytics:
            dominant_emotion = analytics["dominant_emotion"]
            print(f"[DEBUG] Extracted dominant_emotion: {dominant_emotion}")
        else:
            print("[WARN] DeepFace output missing 'dominant_emotion'.")
    except Exception as e:
        print(f"[WARN] DeepFace analysis error: {e}. No emotion detected.")

    # 9.4. Overlay detected emotion on the frame
    annotated = frame.copy()
    if dominant_emotion:
        cv2.putText(annotated,
                    f"Emotion: {dominant_emotion}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2)
    cv2.imshow("Webcam Feed", annotated)

    # 9.5. Execute the full sequence for the detected emotion
    if dominant_emotion == "happy":
        print("[ACTION] Detected: HAPPY")
        do_happy_sequence()

    elif dominant_emotion == "sad":
        print("[ACTION] Detected: SAD")
        do_sad_sequence()

    elif dominant_emotion == "angry":
        print("[ACTION] Detected: ANGRY")
        do_angry_sequence()

    elif dominant_emotion in ["fear", "fearful", "frightened"]:
        print("[ACTION] Detected: FRIGHTENED")
        do_frightened_sequence()

    elif dominant_emotion == "surprise":
        print("[ACTION] Detected: SURPRISED")
        do_surprised_sequence()

    else:
        # No face or unhandled emotion ⇒ keep everything neutral
        if dominant_emotion is None:
            print("[INFO] No emotion detected this frame.")
        else:
            print(f"[INFO] Emotion '{dominant_emotion}' not handled; resetting posture & LEDs.")
        leds_off()
        for _ in range(int(500 / TIME_STEP)):
            robot.step(TIME_STEP)

# ─────────────────────────────────────────────────────────────────────────────
# 10. CLEAN UP (on exit)
# ─────────────────────────────────────────────────────────────────────────────

print("[INFO] Cleaning up: releasing webcam and closing windows.")
cap.release()
cv2.destroyAllWindows()
