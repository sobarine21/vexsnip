import streamlit as st
import cv2
import os
import zipfile
from tempfile import TemporaryDirectory

# Function to extract frames every 1 second
def extract_frames(video_path, output_path, interval=1):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)  # Frames per second

    if not fps or fps == 0:
        st.warning(f"Skipping {os.path.basename(video_path)}, unable to determine FPS.")
        return

    video_name = os.path.basename(video_path).split('.')[0]
    frame_interval = int(fps * interval)  # Interval in frames (1 second = fps frames)

    success, frame = cap.read()
    frame_count = 0

    while success:
        # Save frame at every second (1 second interval)
        if frame_count % frame_interval == 0:
            image_filename = f"{video_name}_frame_{int(frame_count // fps)}.jpg"
            image_path = os.path.join(output_path, image_filename)
            cv2.imwrite(image_path, frame)

        # Increment frame count by 1 to proceed to the next frame
        frame_count += frame_interval
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)  # Set the next frame position
        success, frame = cap.read()

    cap.release()

# Streamlit app
def main():
    st.title("Video Frame Extractor")
    st.write("Upload your videos, and frames will be extracted every second.")

    # Upload video files
    uploaded_files = st.file_uploader(
        "Upload video files (supports .mp4, .avi, .mkv, .mov)", 
        type=["mp4", "avi", "mkv", "mov"], 
        accept_multiple_files=True
    )

    if uploaded_files:
        with TemporaryDirectory() as temp_dir:
            output_folder = os.path.join(temp_dir, "screenshots")
            os.makedirs(output_folder, exist_ok=True)

            for uploaded_file in uploaded_files:
                video_path = os.path.join(temp_dir, uploaded_file.name)
                
                # Save the uploaded file to a temporary directory
                with open(video_path, "wb") as f:
                    f.write(uploaded_file.read())

                st.write(f"Processing video: {uploaded_file.name}")
                extract_frames(video_path, output_folder)

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
