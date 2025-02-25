import streamlit as st
import cv2
import os
import zipfile
from tempfile import TemporaryDirectory
import psutil
import concurrent.futures
import numpy as np

# Function to extract frames at the selected FPS
def extract_frames(video_path, output_path, target_fps):
    cap = cv2.VideoCapture(video_path)
    original_fps = cap.get(cv2.CAP_PROP_FPS)  # Original frames per second

    if not original_fps or original_fps == 0:
        st.warning(f"Skipping {os.path.basename(video_path)}, unable to determine FPS.")
        return

    video_name = os.path.basename(video_path).split('.')[0]
    
    # Calculate frame interval for target FPS
    frame_interval = int(original_fps / target_fps)  # Interval in frames
    success, frame = cap.read()
    frame_count = 0
    saved_frames = 0

    while success:
        # Save frame if it's the correct interval for target FPS
        if frame_count % frame_interval == 0:
            image_filename = f"{video_name}_frame_{int(frame_count // original_fps)}.jpg"
            image_path = os.path.join(output_path, image_filename)
            cv2.imwrite(image_path, frame)
            saved_frames += 1

        frame_count += 1
        success, frame = cap.read()

    cap.release()
    return saved_frames

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
    # Hide the top-right GitHub, Share, and Star buttons using custom CSS
    hide_streamlit_elements = """
    <style>
        .css-1d391kg {
            visibility: hidden;
        }
        .css-1w3aw3n {
            visibility: hidden;
        }
    </style>
    """
    st.markdown(hide_streamlit_elements, unsafe_allow_html=True)

    # Display message for self-hosting and source code
    st.markdown("""
    ## For self hosting and downloading the source code, please visit [this link](https://dhruvbansal8.gumroad.com/l/olsspn)
    """)

    st.title("Video Frame Extractor")
    st.write("Upload your videos, select FPS, and frames will be extracted.")

    # Display server metrics in the sidebar
    display_server_metrics()

    # Upload video files
    uploaded_files = st.file_uploader(
        "Upload video files (supports .mp4, .avi, .mkv, .mov)", 
        type=["mp4", "avi", "mkv", "mov"], 
        accept_multiple_files=True
    )

    # FPS selection
    target_fps = st.slider("Select FPS for extraction", min_value=1, max_value=30, value=1)

    if uploaded_files:
        with TemporaryDirectory() as temp_dir:
            output_folder = os.path.join(temp_dir, "screenshots")
            os.makedirs(output_folder, exist_ok=True)

            # Prepare parallel processing using ThreadPoolExecutor for multiple videos
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []
                for uploaded_file in uploaded_files:
                    video_path = os.path.join(temp_dir, uploaded_file.name)

                    # Save the uploaded file to a temporary directory
                    with open(video_path, "wb") as f:
                        f.write(uploaded_file.read())

                    futures.append(
                        executor.submit(extract_frames, video_path, output_folder, target_fps)
                    )

                # Wait for all videos to be processed
                total_saved_frames = 0
                for future in concurrent.futures.as_completed(futures):
                    saved_frames = future.result()
                    total_saved_frames += saved_frames
                    st.write(f"Extracted {saved_frames} frames.")

            # Provide feedback to user
            if total_saved_frames > 0:
                st.success(f"Successfully extracted {total_saved_frames} frames.")
            else:
                st.warning("No frames were extracted. Please check the video files.")

            # Create a ZIP file for the output folder
            zip_path = os.path.join(temp_dir, "frames.zip")
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for root, _, files in os.walk(output_folder):
                    for file in files:
                        zipf.write(
                            os.path.join(root, file), 
                            arcname=os.path.relpath(os.path.join(root, file), output_folder)
                        )

            # Provide download link for the ZIP file
            with open(zip_path, "rb") as zipf:
                st.download_button(
                    label="Download Extracted Frames",
                    data=zipf,
                    file_name="extracted_frames.zip",
                    mime="application/zip"
                )

if __name__ == "__main__":
    main()
