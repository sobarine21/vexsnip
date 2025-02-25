import streamlit as st
import cv2
import os
import zipfile
from tempfile import TemporaryDirectory
import psutil
import concurrent.futures
import numpy as np
import shutil

# Function to extract frames at the selected FPS
def extract_frames(video_path, output_path, target_fps, interval_seconds=1, resize=None, quality=None):
    cap = cv2.VideoCapture(video_path)
    original_fps = cap.get(cv2.CAP_PROP_FPS)  # Original frames per second
    video_duration = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000  # Duration in seconds
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if not original_fps or original_fps == 0:
        st.warning(f"Skipping {os.path.basename(video_path)}, unable to determine FPS.")
        return

    video_name = os.path.basename(video_path).split('.')[0]

    # Calculate frame interval for target FPS
    frame_interval = int(original_fps / target_fps)  # Interval in frames
    frame_count = 0
    saved_frames = 0

    # Display video details
    st.write(f"Processing video: {video_name}")
    st.write(f"Video Duration: {video_duration} seconds | Resolution: {width}x{height}")

    # Create progress bar
    progress = st.progress(0)
    
    while True:
        success, frame = cap.read()

        if not success:
            break

        if frame_count % frame_interval == 0:
            # Resize frame if required
            if resize:
                frame = cv2.resize(frame, resize)

            # Optionally adjust frame quality (lower quality for faster processing)
            if quality:
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
                _, frame = cv2.imencode('.jpg', frame, encode_param)

            # Save frame
            image_filename = f"{video_name}_frame_{frame_count // original_fps}.jpg"
            image_path = os.path.join(output_path, image_filename)
            cv2.imwrite(image_path, frame)
            saved_frames += 1

        # Update progress bar
        progress.progress(int((frame_count / video_duration) * 100))

        frame_count += 1

    cap.release()
    return saved_frames, video_duration

# Function to display server usage metrics
def display_server_metrics():
    st.sidebar.header("Server Resource Usage")
    
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    st.sidebar.metric("CPU Usage", f"{cpu_percent}%")
    
    # Memory (RAM) usage
    mem = psutil.virtual_memory()
    st.sidebar.metric("RAM Usage", f"{mem.percent}%")
    
    # Disk (ROM) usage
    disk = psutil.disk_usage('/')
    st.sidebar.metric("Disk Usage", f"{disk.percent}%")
    
    # Network bandwidth usage
    net_io = psutil.net_io_counters()
    st.sidebar.metric("Bytes Sent", f"{net_io.bytes_sent / 1_000_000:.2f} MB")
    st.sidebar.metric("Bytes Received", f"{net_io.bytes_recv / 1_000_000:.2f} MB")

# Streamlit app
def main():
    st.title("Enhanced Video Frame Extractor")
    st.write("Upload videos, select FPS and interval, and extract frames efficiently.")
    
    # Display server metrics
    display_server_metrics()

    # Upload video files with drag and drop support
    uploaded_files = st.file_uploader(
        "Upload video files (supports .mp4, .avi, .mkv, .mov, .flv, .webm)", 
        type=["mp4", "avi", "mkv", "mov", "flv", "webm"], 
        accept_multiple_files=True
    )

    # FPS selection
    target_fps = st.slider("Select FPS for extraction", min_value=1, max_value=30, value=1)

    # Frame interval input (every X seconds)
    interval_seconds = st.number_input("Select interval in seconds between frames", min_value=1, value=1)

    # Frame resizing option
    resize_option = st.checkbox("Resize frames", value=False)
    if resize_option:
        width = st.number_input("Width", min_value=1, value=640)
        height = st.number_input("Height", min_value=1, value=480)
        resize = (width, height)
    else:
        resize = None

    # Quality adjustment option
    quality_option = st.slider("Select frame quality (1-100)", min_value=1, max_value=100, value=90)

    if uploaded_files:
        with TemporaryDirectory() as temp_dir:
            output_folder = os.path.join(temp_dir, "screenshots")
            os.makedirs(output_folder, exist_ok=True)

            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []
                for uploaded_file in uploaded_files:
                    video_path = os.path.join(temp_dir, uploaded_file.name)

                    # Save uploaded file
                    with open(video_path, "wb") as f:
                        f.write(uploaded_file.read())

                    # Submit the frame extraction task
                    futures.append(
                        executor.submit(extract_frames, video_path, output_folder, target_fps, interval_seconds, resize, quality_option)
                    )

                # Wait for all tasks to complete
                total_saved_frames = 0
                total_duration = 0
                for future in concurrent.futures.as_completed(futures):
                    saved_frames, video_duration = future.result()
                    total_saved_frames += saved_frames
                    total_duration += video_duration
                    st.write(f"Extracted {saved_frames} frames from a video of {video_duration:.2f} seconds.")

            # Display the results and create ZIP file
            st.success(f"Total frames extracted: {total_saved_frames}")
            st.write(f"Total video processing time: {total_duration:.2f} seconds.")
            
            # Create a ZIP file for the extracted frames
            zip_path = os.path.join(temp_dir, "frames.zip")
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for root, _, files in os.walk(output_folder):
                    for file in files:
                        zipf.write(
                            os.path.join(root, file),
                            arcname=os.path.relpath(os.path.join(root, file), output_folder)
                        )

            # Provide download button for ZIP file
            with open(zip_path, "rb") as zipf:
                st.download_button(
                    label="Download Extracted Frames",
                    data=zipf,
                    file_name="extracted_frames.zip",
                    mime="application/zip"
                )

if __name__ == "__main__":
    main()
