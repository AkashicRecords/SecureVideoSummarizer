## Automated Demo Generation

The project includes several scripts to automate the creation of demo videos and animations. These scripts are located in the `backend` directory and can be used to quickly generate various types of demos.

### Available Scripts

1. **Main Demo Generator**
   - Script: `backend/generate_demos.py`
   - Description: Comprehensive script that manages the entire demo generation process
   - Usage:
     ```bash
     python backend/generate_demos.py [--video-path VIDEO_PATH] [--skip-sample] [--skip-readme]
     ```
   - This script will:
     - Create a sample video if none is provided
     - Generate terminal-based and UI-based animated GIFs
     - Create a console demo
     - Update the README.md with demo links

2. **Sample Video Generator**
   - Script: `backend/create_sample_video.py`
   - Description: Creates a simple sample video with scrolling text about data security
   - Usage:
     ```bash
     python backend/create_sample_video.py [--output-dir OUTPUT_DIR] [--duration DURATION] [--suite]
     ```
   - The `--suite` option creates multiple videos with different durations

3. **Console Demo Generator**
   - Script: `backend/create_demo_video.py`
   - Description: Creates a console-based demo of the video summarization process
   - Usage:
     ```bash
     python backend/create_demo_video.py VIDEO_PATH [--output-dir OUTPUT_DIR] [--mode {console,api}]
     ```

4. **Animated GIF Generator**
   - Script: `backend/create_gif_demo.py`
   - Description: Creates animated GIFs showing the summarization process
   - Usage:
     ```bash
     python backend/create_gif_demo.py VIDEO_PATH [--output-dir OUTPUT_DIR] [--mode {ui,terminal}] [--no-mp4]
     ```
   - Creates both GIF and MP4 formats by default

### Required Dependencies

To use these demo scripts, you'll need the following dependencies:

1. **FFmpeg**
   - For video processing and creation
   - Installation:
     - macOS: `brew install ffmpeg`
     - Ubuntu/Debian: `sudo apt install ffmpeg`
     - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

2. **ImageMagick**
   - For creating animated GIFs and image manipulation
   - Installation:
     - macOS: `brew install imagemagick`
     - Ubuntu/Debian: `sudo apt install imagemagick`
     - Windows: Download from [imagemagick.org](https://imagemagick.org/script/download.php)

### Quick Start

To quickly generate a complete set of demos:

```bash
# Navigate to the project root
cd /path/to/SecureVideoSummarizer

# Run the main demo generator
python backend/generate_demos.py

# Or use an existing video
python backend/generate_demos.py --video-path /path/to/your/video.mp4
```

The generated demos will be organized in the following directory structure:

- `docs/videos/overview/` - Terminal-based GIFs showing processing steps
- `docs/videos/features/` - UI-based demo GIFs showing the interface
- `docs/videos/tutorials/` - Longer demonstration videos
- `docs/videos/demos/` - Output from console demos

### Demo Customization

You can customize aspects of the demo generation:

1. **Video Content**
   - Create your own sample video with specific content:
     ```bash
     python backend/create_sample_video.py --duration 20 --output-dir custom_videos
     ```

2. **Demo Appearance**
   - Modify UI elements in `create_gif_demo.py` to match your branding
   - Adjust animation timing by modifying the delay parameters

3. **Readme Integration**
   - The demos will be automatically added to your project README
   - You can disable this with `--skip-readme` if you prefer manual integration 