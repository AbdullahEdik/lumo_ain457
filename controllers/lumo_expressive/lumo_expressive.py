# lumo_expressive.py
#
# NAO controller reacts based on your physical webcam and recognized emotion.



from controller import Robot, Motor, LED
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
# 4. DEVICE SETUP: MOTORS + LEDs + Lines
# ─────────────────────────────────────────────────────────────────────────────

# 4.1. Head joints
head_yaw:   Motor = robot.getDevice("HeadYaw")
head_pitch: Motor = robot.getDevice("HeadPitch")

# 4.2. Shoulder joints
l_shoulder_pitch: Motor = robot.getDevice("LShoulderPitch")
l_shoulder_roll:  Motor = robot.getDevice("LShoulderRoll")
r_shoulder_pitch: Motor = robot.getDevice("RShoulderPitch")
r_shoulder_roll:  Motor = robot.getDevice("RShoulderRoll")

# 4.3. Elbow joints
r_elbow_yaw: Motor = robot.getDevice("RElbowYaw")
l_elbow_yaw: Motor = robot.getDevice("LElbowYaw")
r_elbow_roll: Motor = robot.getDevice("RElbowRoll")
l_elbow_roll: Motor = robot.getDevice("LElbowRoll")

# 4.4 Wrist joints
r_wrist_yaw: Motor = robot.getDevice("RWristYaw")
l_wrist_yaw: Motor = robot.getDevice("LWristYaw")

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

# 4.6. Initialize all joints to neutral positions
# Head neutral
head_yaw.setPosition(0.0);   head_yaw.setVelocity(0.0)
head_pitch.setPosition(0.0); head_pitch.setVelocity(0.0)

# Arms down (shoulderPitch = +1.0 rad places arms alongside body)
l_shoulder_pitch.setPosition(1.0); l_shoulder_pitch.setVelocity(0.0)
l_shoulder_roll.setPosition(0.0);   l_shoulder_roll.setVelocity(0.0)
r_shoulder_pitch.setPosition(1.0); r_shoulder_pitch.setVelocity(0.0)
r_shoulder_roll.setPosition(0.0);  r_shoulder_roll.setVelocity(0.0)

# 4.7. Turn all LEDs off initially
for led in ALL_LEDS:
    led.set(0x000000)  # LED.set(rgb) uses 0xRRGGBB

# 4.8 Lines for reactions
happy_lines = [
    "You look so cheerful today!",
    "That smile suits you!",
    "Happiness detected — and it’s contagious!",
    "Whoa! Someone’s in a good mood!",
    "Joy detected. Activating celebration mode.",
]

sad_lines = [
    ("You look a little down.", "I'm here if you need someone."),
    ("Is everything okay?", "I'm always ready to listen."),
    ("I sense you're feeling sad.", "Do you want to talk about it?"),
    ("You seem upset.", "Let me know if I can assist."),
    ("It’s okay to feel sad sometimes.", "You’re not alone."),
]

angry_lines = [
    "I'm here to help, not to upset you.",
    "I see you're angry. Let's take a deep breath.",
    "Please, let’s try to stay calm.",
    "I didn’t mean to make you upset.",
    "It’s okay to feel angry. Let’s work through it.",
]

frightened_lines = [
    ("Just a moment, I'm making sure everything's safe for you.", "There's nothing to be afraid of."),
    ("Scanning the area for any danger.", "Looks safe to me!"),
    ("Wait... Did you hear that?", "Never mind, must've been my circuits buzzing."),
    ("Something feels off.", "Actually... I think we're okay."),
    ("Initiating safety check.", "Nothing suspicious found."),
    ("Hold on, I'm making sure the coast is clear.","You're good to go!")
]

surprised_lines = [
    ("Why are you so surprised?", "Did something good happen?"),
    ("You look startled.", "Everything okay?"),
    ("Hmm, that face says 'surprise!'", "Is it something I did?"),
    ("You look shocked.", "Want to talk about it?"),
    ("I noticed your expression changed suddenly.", "What happened?"),
    ("Did something unexpected occur?", "I'm here if you need me."),
    ("Is there something I missed?", "Tell me what's going on!"),
    ("Oh, did I do something strange?", "Or is it something else?"),
    ("Surprised, are we?", "I'm curious too now."),
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

# Hand controls
phalange_names = [
    "RPhalanx1", "RPhalanx2", "RPhalanx3", "RPhalanx4", "RPhalanx5", "RPhalanx6", "RPhalanx7", "RPhalanx8",
    "LPhalanx1", "LPhalanx2", "LPhalanx3", "LPhalanx4", "LPhalanx5", "LPhalanx6", "LPhalanx7", "LPhalanx8"
]

phalanges = [robot.getDevice(name) for name in phalange_names]
for m in phalanges:
    m.setVelocity(4.0)

def set_hands(open: bool):
    """
    Open or close all phalanx joints.
      open=True  → set to 1.0 (fully open)
      open=False → set to 0.0 (fully closed)
    """
    target = 1.0 if open else 0.0
    for m in phalanges:
        m.setPosition(target)
    # wait for the motion to complete
    for _ in range(int(500 / TIME_STEP)):
        robot.step(TIME_STEP)


# ─────────────────────────────────────────────────────────────────────────────
# 8. EMOTION‐BASED SEQUENCES (motion + LED color + speech)
# ─────────────────────────────────────────────────────────────────────────────

def do_happy_sequence():
    
    print("[LED] HAPPY: setting LEDs → GREEN")
    for led in ALL_LEDS:
        led.set(LED_COLORS["happy"])

    speak(random.choice(happy_lines))

    
    set_hands(True)
    l_shoulder_pitch.setPosition(-1.0); l_shoulder_pitch.setVelocity(1.5)
    r_shoulder_pitch.setPosition(-1.0); r_shoulder_pitch.setVelocity(1.5)
    for _ in range(int(1500 / TIME_STEP)):
        robot.step(TIME_STEP)

    for i in range(2):
        l_shoulder_roll.setPosition( 0.5); l_shoulder_roll.setVelocity(1.0)
        r_shoulder_roll.setPosition( 0.5); r_shoulder_roll.setVelocity(1.0)
        for _ in range(int(500 / TIME_STEP)):
            robot.step(TIME_STEP)

        l_shoulder_roll.setPosition(-0.5); l_shoulder_roll.setVelocity(1.0)
        r_shoulder_roll.setPosition(-0.5); r_shoulder_roll.setVelocity(1.0)
        for _ in range(int(500 / TIME_STEP)):
            robot.step(TIME_STEP)

    set_hands(False)

    l_shoulder_roll.setPosition(0.0); l_shoulder_roll.setVelocity(1.0)
    r_shoulder_roll.setPosition(0.0); r_shoulder_roll.setVelocity(1.0)
    for _ in range(int(400 / TIME_STEP)):
        robot.step(TIME_STEP)

    l_shoulder_pitch.setPosition(1.0); l_shoulder_pitch.setVelocity(1.5)
    r_shoulder_pitch.setPosition(1.0); r_shoulder_pitch.setVelocity(1.5)
    
    for _ in range(int(1700 / TIME_STEP)):
        robot.step(TIME_STEP)

    print("[LED] HAPPY: turning LEDs OFF")
    leds_off()

def do_sad_sequence():

    print("[LED] SAD: setting LEDs → BLUE")
    for led in ALL_LEDS:
        led.set(LED_COLORS["sad"])

    sad_line1, sad_line2 = random.choice(sad_lines)
    speak(sad_line1)

    head_pitch.setPosition(0.5); head_pitch.setVelocity(1.0)
    for _ in range(int(1500 / TIME_STEP)):
        robot.step(TIME_STEP)

    head_pitch.setPosition(0.0); head_pitch.setVelocity(1.0)
    for _ in range(int(500 / TIME_STEP)):
        robot.step(TIME_STEP)

    set_hands(True)
    l_elbow_yaw.setPosition(-2.0); l_elbow_yaw.setVelocity(2.2)
    r_elbow_yaw.setPosition(2.0); r_elbow_yaw.setVelocity(2.2)
    for _ in range(int(1000 / TIME_STEP)):
        robot.step(TIME_STEP)

    l_shoulder_pitch.setPosition(0.6); l_shoulder_pitch.setVelocity(1.5)
    r_shoulder_pitch.setPosition(0.6); r_shoulder_pitch.setVelocity(1.5)
    l_shoulder_roll.setPosition(0.3); l_shoulder_roll.setVelocity(1.5)
    r_shoulder_roll.setPosition(-0.3); r_shoulder_roll.setVelocity(1.5)
    for _ in range(int(1000 / TIME_STEP)):
        robot.step(TIME_STEP)

    l_elbow_roll.setPosition(-0.4); l_elbow_roll.setVelocity(2.0)
    r_elbow_roll.setPosition(0.4); r_elbow_roll.setVelocity(2.0)
    for _ in range(int(1000 / TIME_STEP)):
        robot.step(TIME_STEP)

    speak(sad_line2)

    set_hands(False)
    l_elbow_yaw.setPosition(0.0); l_elbow_yaw.setVelocity(2.2)
    r_elbow_yaw.setPosition(0.0); r_elbow_yaw.setVelocity(2.2)
    for _ in range(int(1000 / TIME_STEP)):
        robot.step(TIME_STEP)

    l_shoulder_pitch.setPosition(1.0); l_shoulder_pitch.setVelocity(1.5)
    r_shoulder_pitch.setPosition(1.0); r_shoulder_pitch.setVelocity(1.5)
    l_shoulder_roll.setPosition(0.0); l_shoulder_roll.setVelocity(1.5)
    r_shoulder_roll.setPosition(0.0); r_shoulder_roll.setVelocity(1.5)
    for _ in range(int(1000 / TIME_STEP)):
        robot.step(TIME_STEP)

    l_elbow_roll.setPosition(0.0); l_elbow_roll.setVelocity(2.0)
    r_elbow_roll.setPosition(0.0); r_elbow_roll.setVelocity(2.0)
    for _ in range(int(1000 / TIME_STEP)):
        robot.step(TIME_STEP)

    print("[LED] SAD: turning LEDs OFF")
    leds_off()

def do_angry_sequence():

    print("[LED] ANGRY: setting LEDs → RED")
    for led in ALL_LEDS:
        led.set(LED_COLORS["angry"])

    speak(random.choice(angry_lines))
    
    l_shoulder_pitch.setPosition(0.1); l_shoulder_pitch.setVelocity(1.0)
    r_shoulder_pitch.setPosition(0.1); r_shoulder_pitch.setVelocity(1.0)
    for _ in range(int(500 / TIME_STEP)):
        robot.step(TIME_STEP)

    set_hands(True)

    l_elbow_yaw.setPosition(-1.0); l_elbow_yaw.setVelocity(1.0)
    l_wrist_yaw.setPosition(1.0); l_wrist_yaw.setVelocity(1.0)
    r_elbow_yaw.setPosition(1.0); r_elbow_yaw.setVelocity(1.0)
    r_wrist_yaw.setPosition(-1.0); r_wrist_yaw.setVelocity(1.0)
    for _ in range(int(1000 / TIME_STEP)):
        robot.step(TIME_STEP)

    l_elbow_roll.setPosition(-0.2); l_elbow_roll.setVelocity(1.0)
    l_shoulder_roll.setPosition(0.2); l_shoulder_roll.setVelocity(1.0)
    r_elbow_roll.setPosition(0.2); r_elbow_roll.setVelocity(1.0)
    r_shoulder_roll.setPosition(-0.2); r_shoulder_roll.setVelocity(1.0)
    for _ in range(int(500 / TIME_STEP)):
        robot.step(TIME_STEP)

    l_elbow_roll.setPosition(0.0); l_elbow_roll.setVelocity(1.0)
    l_shoulder_roll.setPosition(0.0); l_shoulder_roll.setVelocity(1.0)
    r_elbow_roll.setPosition(0.0); r_elbow_roll.setVelocity(1.0)
    r_shoulder_roll.setPosition(0.0); r_shoulder_roll.setVelocity(1.0)
    for _ in range(int(500 / TIME_STEP)):
        robot.step(TIME_STEP)

    l_elbow_roll.setPosition(-0.2); l_elbow_roll.setVelocity(1.0)
    l_shoulder_roll.setPosition(0.2); l_shoulder_roll.setVelocity(1.0)
    r_elbow_roll.setPosition(0.2); r_elbow_roll.setVelocity(1.0)
    r_shoulder_roll.setPosition(-0.2); r_shoulder_roll.setVelocity(1.0)
    for _ in range(int(500 / TIME_STEP)):
        robot.step(TIME_STEP)

    l_elbow_roll.setPosition(0.0); l_elbow_roll.setVelocity(1.0)
    l_shoulder_roll.setPosition(0.0); l_shoulder_roll.setVelocity(1.0)
    r_elbow_roll.setPosition(0.0); r_elbow_roll.setVelocity(1.0)
    r_shoulder_roll.setPosition(0.0); r_shoulder_roll.setVelocity(1.0)
    for _ in range(int(500 / TIME_STEP)):
        robot.step(TIME_STEP)
    
    l_shoulder_pitch.setPosition(1.0); l_shoulder_pitch.setVelocity(1.0)
    r_shoulder_pitch.setPosition(1.0); r_shoulder_pitch.setVelocity(1.0)
    l_elbow_yaw.setPosition(0.0); l_elbow_yaw.setVelocity(1.0)
    l_wrist_yaw.setPosition(0.0); l_wrist_yaw.setVelocity(1.0)
    r_elbow_yaw.setPosition(0.0); r_elbow_yaw.setVelocity(1.0)
    r_wrist_yaw.setPosition(0.0); r_wrist_yaw.setVelocity(1.0)
    for _ in range(int(500 / TIME_STEP)):
        robot.step(TIME_STEP)

    set_hands(False)

    print("[LED] ANGRY: turning LEDs OFF")
    leds_off()

def do_frightened_sequence():

    print("[LED] FRIGHTENED: setting LEDs → YELLOW")
    for led in ALL_LEDS:
        led.set(LED_COLORS["frightened"])

    frightened_line1, frightened_line2 = random.choice(frightened_lines)
    speak(frightened_line1)

    for i in range(2):
        head_yaw.setPosition( 0.7); head_yaw.setVelocity(1.0)
        for _ in range(int(1000 / TIME_STEP)):
            robot.step(TIME_STEP)

        head_yaw.setPosition(-0.7); head_yaw.setVelocity(1.0)
        for _ in range(int(1000 / TIME_STEP)):
            robot.step(TIME_STEP)

    head_yaw.setPosition(0.0); head_yaw.setVelocity(1.0)
    for _ in range(int(500 / TIME_STEP)):
        robot.step(TIME_STEP)

    speak(frightened_line2)

    print("[LED] FRIGHTENED: turning LEDs OFF")
    leds_off()

def do_surprised_sequence():

    print("[LED] SURPRISED: setting LEDs → MAGENTA")
    for led in ALL_LEDS:
        led.set(LED_COLORS["surprise"])

    surprised_line1, surprised_line2 = random.choice(surprised_lines)
    speak(surprised_line1)

    r_wrist_yaw.setPosition(1.0); r_wrist_yaw.setVelocity(1.0)
    l_shoulder_pitch.setPosition(0.4); l_shoulder_pitch.setVelocity(1.0)
    l_elbow_yaw.setPosition(-0.5); l_elbow_yaw.setVelocity(1.0)
    l_wrist_yaw.setPosition(-0.5); l_wrist_yaw.setVelocity(1.0)
    for _ in range(int(1000 / TIME_STEP)):
        robot.step(TIME_STEP)

    set_hands(True)

    r_shoulder_roll.setPosition(-0.3); r_shoulder_roll.setVelocity(1.0)
    r_elbow_roll.setPosition(0.6); r_elbow_roll.setVelocity(1.0)
    l_elbow_roll.setPosition(-1.0); l_elbow_roll.setVelocity(1.0)
    for _ in range(int(1500 / TIME_STEP)):
        robot.step(TIME_STEP)

    speak(surprised_line2)

    l_shoulder_pitch.setPosition(1.0); l_shoulder_pitch.setVelocity(1.0)
    r_shoulder_roll.setPosition(0.0); r_shoulder_roll.setVelocity(1.0)
    l_elbow_roll.setPosition(0.0); l_elbow_roll.setVelocity(1.0)
    r_elbow_roll.setPosition(0.0); r_elbow_roll.setVelocity(1.0)
    for _ in range(int(500 / TIME_STEP)):
        robot.step(TIME_STEP)
        

    l_wrist_yaw.setPosition(0.0); l_wrist_yaw.setVelocity(1.0)
    r_wrist_yaw.setPosition(0.0); r_wrist_yaw.setVelocity(1.0)
    l_elbow_yaw.setPosition(0.0); l_elbow_yaw.setVelocity(1.0)
    for _ in range(int(500 / TIME_STEP)):
        robot.step(TIME_STEP)
    
    print("[LED] SURPRISED: turning LEDs OFF")
    leds_off()

# ─────────────────────────────────────────────────────────────────────────────
# 9. MAIN CONTROL LOOP
# ─────────────────────────────────────────────────────────────────────────────

print("[INFO] Entering main control loop. Press ESC in the 'Webcam Feed' window to exit.")
while robot.step(TIME_STEP) != -1:
    # 9.1. Grab one frame from the webcam
    frame = get_webcam_frame()
    if frame is None:
        print("[WARN] Frame read failed. Keeping joints & LEDs neutral.")
        # Reset everything to neutral
        head_yaw.setPosition(0.0); head_yaw.setVelocity(0.0)
        head_pitch.setPosition(0.0); head_pitch.setVelocity(0.0)
        l_shoulder_pitch.setPosition(1.0); l_shoulder_pitch.setVelocity(0.0)
        l_shoulder_roll.setPosition(0.0);   l_shoulder_roll.setVelocity(0.0)
        r_shoulder_pitch.setPosition(1.0); r_shoulder_pitch.setVelocity(0.0)
        r_shoulder_roll.setPosition(0.0);  r_shoulder_roll.setVelocity(0.0)
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
        head_yaw.setPosition(0.0); head_yaw.setVelocity(0.0)
        head_pitch.setPosition(0.0); head_pitch.setVelocity(0.0)
        l_shoulder_pitch.setPosition(1.0); l_shoulder_pitch.setVelocity(0.0)
        l_shoulder_roll.setPosition(0.0);   l_shoulder_roll.setVelocity(0.0)
        r_shoulder_pitch.setPosition(1.0); r_shoulder_pitch.setVelocity(0.0)
        r_shoulder_roll.setPosition(0.0);  r_shoulder_roll.setVelocity(0.0)
        leds_off()
        for _ in range(int(500 / TIME_STEP)):
            robot.step(TIME_STEP)

# ─────────────────────────────────────────────────────────────────────────────
# 10. CLEAN UP (on exit)
# ─────────────────────────────────────────────────────────────────────────────

print("[INFO] Cleaning up: releasing webcam and closing windows.")
cap.release()
cv2.destroyAllWindows()
