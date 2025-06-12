# Lumo Robot Controller for Webots

This repository contains two Python controllers for the Lumo robot (a NAO robot variant with emotional detection):

* **lumo\_expressive.py**: Uses a physical webcam and DeepFace to detect user emotions, then moves the robot, changes LED colors, and speaks contextual phrases.
* **lumo\_minimal.py**: A simplified version that only speaks lines and changes LED colors without any physical motion.

---
## Demo Videos

Watch Lumo in action on YouTube:

* **Minimal Controller Demo**: [https://youtu.be/okjG8tlLNMI](https://youtu.be/okjG8tlLNMI)
* **Expressive Controller Demo**: [https://youtu.be/rI5xfDDLBXU](https://youtu.be/rI5xfDDLBXU)

---

## Features

* Real-time emotion recognition via webcam using DeepFace.
* Expressive robot animations for five basic emotions: happy, sad, angry, frightened, surprise.
* LED color feedback corresponding to detected emotion.
* Text-to-speech responses via `pyttsx3`.
* Configurable parameters for webcam resolution, time step, LED colors, and speech rate.

---

## Prerequisites

* [Webots](https://cyberbotics.com/) (simulation environment)
* Python 3.8 or higher
* USB webcam compatible with OpenCV

---

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/AbdullahEdik/lumo_ain457.git
   cd lumo_ain457
   ```

2. (Optional) Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Open the Webots world containing the Lumo robot and set the controller to one of the following paths:

   ```
   controllers/lumo_expressive/lumo_expressive.py
   controllers/lumo_minimal/lumo_minimal.py
   ```

---

## Usage

1. Launch Webots and open the Lumo world.
2. Select the Lumo robot in the scene tree.
3. In the Controller field, choose either:

   * `lumo_expressive.py`
   * `lumo_minimal.py`
4. Start the simulation.
5. A window named **Webcam Feed** will open showing the live camera.
6. Emotions detected will trigger robot actions.

   * Press **ESC** in the camera window to end the simulation.

---

## Configuration

Inside each script, you can adjust the following parameters:

```python
TIME_STEP    = 32      # Webots control loop interval in ms
WEBCAM_ID    = 0       # System index of your webcam
DISPLAY_W    = 320     # Webcam display width
DISPLAY_H    = 240     # Webcam display height

# Customize LED colors for emotions (hex RGB)
LED_COLORS = {
    "happy":      0x00FF00,
    "sad":        0x0000FF,
    "angry":      0x9DD8E6,
    "frightened": 0xFFFF00,
    "surprise":   0xFF00FF,
}

# Speech rate (words per minute)
tts_engine.setProperty("rate", 150)
```

Feel free to modify the emotion lines for personalized responses.

---

## lumo\_expressive.py vs. lumo\_minimal.py

| Feature              | lumo\_expressive | lumo\_minimal  |
| -------------------- | ---------------- | -------------- |
| Motion sequences     | Yes              | No             |
| LED color feedback   | Yes              | Yes            |
| Text-to-speech (TTS) | Yes              | Yes            |
| Emotion detection    | Yes              | Yes -          |
| Simulation in Webots | Yes              | Yes            |

Use **lumo\_minimal.py** when motion is not required or to test speech/LED logic more quickly.

---

## File Structure

```
lumo_ain457/
├── controllers/
│   ├── lumo_expressive/
│   │   └── lumo_expressive.py   # Main expressive controller
│   └── lumo_minimal/
│       └── lumo_minimal.py      # Simplified controller (LED+speech only)
├── requirements.txt             # Python dependencies
└── README.md                    # Project overview and instructions
```

---

## Requirements.txt

```
controller             # Webots Python API
opencv-python          # OpenCV for webcam handling
deepface               # Emotion detection
numpy                  # Array operations
pyttsx3                # Text-to-speech
```

---


**Author:** Abdullah

**Date:** June 8, 2025
