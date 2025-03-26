# Popup UI Wireframe

```
+------------------------------------------+
|  [LOGO] Secure Video Summarizer          |
+------------------------------------------+
|                                          |
|  [Platform Icon] Platform Name           |
|                                          |
+------------------------------------------+
|                                          |
|  🎬 Video Title                          |
|  Duration: XX:XX                         |
|                                          |
+------------------------------------------+
|  Playback Controls                       |
|  [Play] [Pause]                         |
|  [⏪] [⏩] [-] [1.0x] [+]                 |
|                                          |
+------------------------------------------+
|  Summary Options                         |
|  Length: [Short/Medium/Long ▼]           |
|  Format: [Paragraph/Bullets ▼]           |
|  Focus On:                               |
|  [✓] Key Points                          |
|  [ ] Detailed Content                    |
|                                          |
+------------------------------------------+
|  Platform-Specific Options               |
|  [Summarize YouTube Video]               |
|  or                                      |
|  [Summarize Olympus Video]               |
|  [Capture Transcript]                    |
|                                          |
+------------------------------------------+
|  [Summarize This Video] [Open App]       |
|                                          |
+------------------------------------------+
|  Summary Result (when available)         |
|  Summary:                                |
|  [Summary text appears here...]          |
|  [Copy Text]                             |
|                                          |
+------------------------------------------+
|  v1.0.2                    🐞            |
+------------------------------------------+

## Element Hierarchy

1. Header
   - Logo
   - Title

2. Platform Section
   - Platform Icon
   - Platform Name

3. Status Messages
   - Loading State
   - No Video State
   - Error State
   - Video Detection

4. Playback Controls
   - Basic Controls (Play/Pause)
   - Advanced Controls (Seek/Rate)

5. Options Section
   - Length Selector
   - Format Selector
   - Focus Options

6. Platform-Specific Options
   - YouTube Options
   - Olympus Options

7. Action Buttons
   - Summarize Button
   - Open App Button

8. Results Section
   - Summary Content
   - Copy Button

9. Footer
   - Version
   - Debug Toggle

## Notes
- Width: 400px
- Height: 600px
- Scrollable content
- Responsive layout
- Platform-specific elements show/hide based on context
- Status messages appear conditionally
- Debug section hidden by default 