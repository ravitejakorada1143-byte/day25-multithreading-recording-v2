
import cv2
import pyaudio
import threading
import wave
import os

# Stop event
stop_event = threading.Event()

# Synchronize main thread and two worker threads
start_barrier = threading.Barrier(3)

# Output folder
OUTPUT_FOLDER = "output"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

VIDEO_FILE = os.path.join(OUTPUT_FOLDER, "recorded_video.avi")
AUDIO_FILE = os.path.join(OUTPUT_FOLDER, "recorded_audio.wav")

frame_count = 0


# Thread 1: Webcam recording
def webcam_task():
    global frame_count

    camera = cv2.VideoCapture(0)
    video_writer = None

    try:
        if not camera.isOpened():
            raise RuntimeError("Unable to access webcam")

        # Initialize video writer before synchronization
        success, frame = camera.read()

        if not success:
            raise RuntimeError("Unable to capture initial video frame")

        height, width = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"XVID")

        video_writer = cv2.VideoWriter(
            VIDEO_FILE,
            fourcc,
            20.0,
            (width, height)
        )

        if not video_writer.isOpened():
            raise RuntimeError("Unable to create video file")

        print("Webcam initialized and ready")

        # Wait until microphone and main thread are ready
        start_barrier.wait()

        print("Webcam recording started")

        while not stop_event.is_set():

            success, frame = camera.read()

            if not success:
                print("Unable to capture webcam frame")
                stop_event.set()
                break

            video_writer.write(frame)
            frame_count += 1

            cv2.imshow("Day 25 - Video Recording", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                stop_event.set()
                break

    except Exception as error:
        print("Webcam error:", error)
        stop_event.set()

        if start_barrier.n_waiting < 3:
            try:
                start_barrier.abort()
            except Exception:
                pass

    finally:
        camera.release()

        if video_writer is not None:
            video_writer.release()

        cv2.destroyAllWindows()
        print("Webcam thread stopped")


# Thread 2: Microphone recording
def microphone_task():
    audio = pyaudio.PyAudio()
    stream = None
    audio_file = None

    try:
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )

        audio_file = wave.open(AUDIO_FILE, "wb")
        audio_file.setnchannels(1)
        audio_file.setsampwidth(
            audio.get_sample_size(pyaudio.paInt16)
        )
        audio_file.setframerate(16000)

        print("Microphone initialized and ready")

        # Wait until webcam and main thread are ready
        start_barrier.wait()

        print("Microphone recording started")

        chunk_count = 0

        while not stop_event.is_set():

            audio_data = stream.read(
                1024,
                exception_on_overflow=False
            )

            audio_file.writeframes(audio_data)
            chunk_count += 1

            if chunk_count % 10 == 0:
                print("Audio chunks saved:", chunk_count)

    except Exception as error:
        print("Microphone error:", error)
        stop_event.set()

        if start_barrier.n_waiting < 3:
            try:
                start_barrier.abort()
            except Exception:
                pass

    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()

        if audio_file is not None:
            audio_file.close()

        audio.terminate()
        print("Microphone thread stopped")


# Create threads
webcam_thread = threading.Thread(target=webcam_task)
microphone_thread = threading.Thread(target=microphone_task)

# Start both threads
webcam_thread.start()
microphone_thread.start()

print("Waiting for audio and video devices...")

# Main thread also waits at the barrier
try:
    start_barrier.wait()
    print("Both devices are ready. Recording started!")

except threading.BrokenBarrierError:
    print("Recording could not start because a device failed.")

# Wait for both threads
webcam_thread.join()
microphone_thread.join()

# Final result
print("\nDay 25 Version 2 execution completed")
print("Total video frames saved:", frame_count)
print("Video saved at:", VIDEO_FILE)
print("Audio saved at:", AUDIO_FILE)
