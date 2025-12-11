from flask import Flask, render_template, jsonify
from fer import FER
import cv2
import pygame
import threading
import time

app = Flask(__name__)

# Initialize FER detector
detector = FER(mtcnn=True)

# Initialize Pygame mixer
pygame.mixer.init()

# Songs mapping
songs = {
    "happy": "Music/happy1.mp3",
    "sad": "Music/sad1.mp3",
    "neutral": "Music/neutral1.mp3"
}

# Flag to prevent scanning while song is playing
is_playing = False

def play_song(mood):
    global is_playing
    is_playing = True
    pygame.mixer.music.load(songs[mood])
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(1)
    is_playing = False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/detect_mood')
def detect_mood():
    global is_playing
    if is_playing:
        return jsonify({"mood": "song_playing"})

    cap = cv2.VideoCapture(0)
    detected_moods = []
    start_time = time.time()

    while time.time() - start_time < 5:  # Scan for 5 seconds
        ret, frame = cap.read()
        if not ret:
            continue

        result = detector.top_emotion(frame)
        if result:
            mood, score = result
            if mood in songs:
                detected_moods.append(mood)

        cv2.imshow("Mood Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    final_mood = detected_moods[-1] if detected_moods else "neutral"
    threading.Thread(target=play_song, args=(final_mood,), daemon=True).start()
    return jsonify({"mood": final_mood})

@app.route('/pause', methods=['POST'])
def pause_song():
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
    return jsonify({"status": "paused"})

@app.route('/play', methods=['POST'])
def resume_song():
    pygame.mixer.music.unpause()
    return jsonify({"status": "playing"})

if __name__ == '__main__':
    app.run(debug=True)
