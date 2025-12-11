document.addEventListener("DOMContentLoaded", () => {
    // Screen elements
    const startScreen = document.getElementById("start-screen");
    const scanningScreen = document.getElementById("scanning-screen");
    const resultsScreen = document.getElementById("results-screen");

    // Buttons
    const scanBtn = document.getElementById("scanBtn");
    const playPauseBtn = document.getElementById("playPauseBtn");
    const stopBtn = document.getElementById("stopBtn");
    const scanAgainBtn = document.getElementById("scanAgainBtn");

    // Display elements
    const moodDisplay = document.getElementById("mood-display");
    const moodResult = document.getElementById("mood-result");
    const songTitle = document.getElementById("song-title");
    const camera = document.getElementById("camera");
    const progressBar = document.querySelector(".progress-bar");

    // Audio
    const audioPlayer = document.getElementById("audio-player");
    let stream;

    // ---- UI State Management ----
    function showScreen(screen) {
        startScreen.classList.add("hidden");
        scanningScreen.classList.add("hidden");
        resultsScreen.classList.add("hidden");
        screen.classList.remove("hidden");
    }

    // ---- Camera and Scanning Logic ----
    async function startCamera() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            camera.srcObject = stream;
            await camera.play();
        } catch (err) {
            console.error("Could not access camera:", err);
            alert("Camera access is required. Please allow and refresh.");
            showScreen(startScreen);
        }
    }

    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
    }

    async function captureFrames() {
        const frames = [];
        const canvas = document.createElement("canvas");
        canvas.width = camera.videoWidth;
        canvas.height = camera.videoHeight;
        const ctx = canvas.getContext("2d");

        const captureInterval = 250;
        const duration = 5000;
        const framesToCapture = duration / captureInterval;

        for (let i = 0; i < framesToCapture; i++) {
            ctx.drawImage(camera, 0, 0, canvas.width, canvas.height);
            frames.push(canvas.toDataURL("image/jpeg"));
            await new Promise(r => setTimeout(r, captureInterval));
        }
        return frames;
    }

    // ---- Main Scan Process ----
    scanBtn.addEventListener("click", async () => {
        showScreen(scanningScreen);
        progressBar.style.transition = 'none'; // Disable transition for reset
        progressBar.style.width = "0%";
        
        await startCamera();
        await new Promise(r => setTimeout(r, 100));

        // Force a reflow before starting the animation
        progressBar.offsetHeight; 
        progressBar.style.transition = 'width 5s linear';
        progressBar.style.width = "100%";

        const frames = await captureFrames();
        stopCamera();
        moodDisplay.textContent = "Processing...";

        try {
            const response = await fetch("/detect_mood", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ frames })
            });
            const data = await response.json();
            if (response.ok) {
                displayResults(data.mood, data.song);
            } else {
                throw new Error(data.error || "Failed to detect mood.");
            }
        } catch (err) {
            console.error("Error detecting mood:", err);
            alert("Sorry, there was an error detecting your mood. Please try again.");
            showScreen(startScreen);
        }
    });

    // ---- Results and Audio Controls ----
    function displayResults(mood, songPath) {
        moodResult.textContent = mood;
        const filename = songPath.split('/').pop();
        songTitle.textContent = filename;

        audioPlayer.src = songPath;
        audioPlayer.play();
        playPauseBtn.textContent = "Pause";

        showScreen(resultsScreen);
    }

    playPauseBtn.addEventListener("click", () => {
        if (audioPlayer.paused) {
            audioPlayer.play();
            playPauseBtn.textContent = "Pause";
        } else {
            audioPlayer.pause();
            playPauseBtn.textContent = "Play";
        }
    });

    stopBtn.addEventListener("click", () => {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        playPauseBtn.textContent = "Play";
    });

    scanAgainBtn.addEventListener("click", () => {
        stopBtn.click();
        showScreen(startScreen);
    });
});