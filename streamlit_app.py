import streamlit as st
import cv2
import os
import zipfile
from tempfile import TemporaryDirectory
import psutil
import concurrent.futures

# Function to extract frames at the selected FPS
def extract_frames(video_path, output_path, target_fps):
    cap = cv2.VideoCapture(video_path)
    original_fps = cap.get(cv2.CAP_PROP_FPS)

    if not original_fps or original_fps == 0:
        st.warning(f"Skipping {os.path.basename(video_path)}, unable to determine FPS.")
        return 0

    video_name = os.path.basename(video_path).split('.')[0]
    frame_interval = max(1, int(original_fps / target_fps))  # Ensure non-zero interval
    success, frame = cap.read()
    frame_count, saved_frames = 0, 0

    while success:
        if frame_count % frame_interval == 0:
            image_filename = f"{video_name}_frame_{int(frame_count // original_fps)}.jpg"
            cv2.imwrite(os.path.join(output_path, image_filename), frame)
            saved_frames += 1
        frame_count += 1
        success, frame = cap.read()

    cap.release()
    return saved_frames

# Function to hide Streamlit UI elements
def hide_streamlit_elements():
    st.markdown("""
        <style>
            #MainMenu, header, footer, .css-1kyxreq, .css-18ni7ap {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

# Function to display server metrics
def display_server_metrics():
    st.sidebar.header("Server Resource Usage")
    st.sidebar.metric("CPU Usage", f"{psutil.cpu_percent(interval=1)}%")
    mem = psutil.virtual_memory()
    st.sidebar.metric("RAM Usage", f"{mem.percent}%")
    disk = psutil.disk_usage('/')
    st.sidebar.metric("Disk Usage", f"{disk.percent}%")

# Main Streamlit app
def main():
    hide_streamlit_elements()
    
    st.title("Video Frame Extractor")
    st.write("Upload your videos, select FPS, and frames will be extracted.")

    display_server_metrics()

    uploaded_files = st.file_uploader(
        "Upload video files", type=["mp4", "avi", "mkv", "mov"], accept_multiple_files=True
    )
    
    target_fps = st.slider("Select FPS", min_value=1, max_value=30, value=1)

    if uploaded_files:
        with TemporaryDirectory() as temp_dir:
            output_folder = os.path.join(temp_dir, "screenshots")
            os.makedirs(output_folder, exist_ok=True)

            saved_file_paths = []
            for uploaded_file in uploaded_files:
                temp_file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.read())
                saved_file_paths.append(temp_file_path)

            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(
                        extract_frames,
                        file_path,
                        output_folder,
                        target_fps
                    )
                    for file_path in saved_file_paths
                ]

            total_saved_frames = sum(f.result() for f in concurrent.futures.as_completed(futures))
            st.success(f"Extracted {total_saved_frames} frames.") if total_saved_frames else st.warning("No frames extracted.")

            if total_saved_frames > 0:
                zip_path = os.path.join(temp_dir, "frames.zip")
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    for root, _, files in os.walk(output_folder):
                        for file in files:
                            zipf.write(os.path.join(root, file), arcname=file)

                with open(zip_path, "rb") as zipf:
                    st.download_button("Download Extracted Frames", zipf, "extracted_frames.zip", "application/zip")

    # Self-hosting and Source Code link
    st.markdown(
        """
        ### Self-Hosting
        If you want to self-host this application or download the source code, please visit:  
        👉 [Download Source Code](https://dhruvbansal8.gumroad.com/l/olsspn)
        """
    )

if __name__ == "__main__":
    main()
