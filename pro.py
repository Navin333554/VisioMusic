import os
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import io
import base64
from PIL import Image
import cv2
import numpy as np
from fer import FER
from collections import Counter

app = Flask(__name__)
app.secret_key = 'your_super_secret_key' 

DUMMY_USERS = {
    "user": "password123"
}

songs = {
    "happy": "/static/Music/happy1.mp3",
    "sad": "/static/Music/sad1.mp3",
    "neutral": "/static/Music/neutral1.mp3",
    "angry": "/static/Music/neutral1.mp3",
    "surprise": "/static/Music/happy1.mp3",
    "fear": "/static/Music/sad1.mp3",
    "disgust": "/static/Music/neutral1.mp3"
}

detector = FER(mtcnn=True)

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def handle_login():
    username = request.form.get('username')
    password = request.form.get('password')

    if DUMMY_USERS.get(username) == password:
        session['logged_in'] = True
        return redirect(url_for('player'))
    else:
        return render_template('login.html', error="Invalid username or password.")

@app.route('/player')
def player():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    return render_template('player.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login_page'))

@app.route('/detect_mood', methods=['POST'])
def detect_mood():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data or "frames" not in data:
        return jsonify({"error": "No frames data received"}), 400
    
    frames = data.get("frames", [])
    detected_moods = []

    for frame_b64 in frames:
        image_data = base64.b64decode(frame_b64.split(",")[1])
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        try:
            result = detector.detect_emotions(img)
            if result:
                emotions = result[0]['emotions']
                
                # --- NEW, MORE SENSITIVE MOOD DETECTION LOGIC ---
                # This prioritizes happy and sad expressions to make detection more reliable.
                
                # Priority check 1: If happiness is strong, confirm it.
                if emotions.get('happy', 0) > 0.50:
                    top_emotion = 'happy'
                # Priority check 2: If sadness has a notable score, prioritize it over neutral.
                elif emotions.get('sad', 0) > 0.20: # A low threshold makes it sensitive.
                    top_emotion = 'sad'
                # Fallback: If no priority moods are detected, just pick the highest score.
                else:
                    top_emotion = max(emotions, key=emotions.get)
                
                detected_moods.append(top_emotion)
                print(f"Scores: {emotions} -> Chosen: {top_emotion}") # For debugging
        except Exception as e:
            print(f"Error processing a frame: {e}")
            continue

    if detected_moods:
        final_mood = Counter(detected_moods).most_common(1)[0][0]
    else:
        final_mood = "neutral"
        
    print(f"Final determined mood: {final_mood}")
    
    song_path = songs.get(final_mood, songs["neutral"])
    return jsonify({"mood": final_mood, "song": song_path})

if __name__ == '__main__':
    app.run(debug=True)