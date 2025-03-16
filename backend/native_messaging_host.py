#!/usr/bin/env python3

import sys
import json
import struct
import os
import tempfile
import subprocess
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    filename='native_host.log',
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)

def send_message(message):
    """Send a message to the browser extension."""
    encoded_message = json.dumps(message).encode('utf-8')
    sys.stdout.buffer.write(struct.pack('I', len(encoded_message)))
    sys.stdout.buffer.write(encoded_message)
    sys.stdout.buffer.flush()

def read_message():
    """Read a message from the browser extension."""
    # Read the message length (first 4 bytes)
    length_bytes = sys.stdin.buffer.read(4)
    if len(length_bytes) == 0:
        return None
    
    # Unpack the message length
    message_length = struct.unpack('I', length_bytes)[0]
    
    # Read the message
    message_bytes = sys.stdin.buffer.read(message_length)
    message = json.loads(message_bytes.decode('utf-8'))
    return message

def main():
    """Main function to handle native messaging."""
    try:
        # Create a temporary directory for audio chunks
        temp_dir = tempfile.mkdtemp()
        audio_chunks = []
        
        # Process messages
        while True:
            message = read_message()
            if not message:
                break
                
            if message.get('type') == 'audio_data':
                # Save audio chunk to temporary file
                chunk_path = os.path.join(temp_dir, f"chunk_{len(audio_chunks)}.webm")
                with open(chunk_path, 'wb') as f:
                    f.write(bytes(message['data']))
                audio_chunks.append(chunk_path)
                
                # Let the extension know we received the chunk
                send_message({'status': 'chunk_received', 'count': len(audio_chunks)})
                
            elif message.get('type') == 'recording_complete':
                # Combine audio chunks and process
                if audio_chunks:
                    # Path for the combined audio file
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    output_path = os.path.join(temp_dir, f"recording_{timestamp}.webm")
                    
                    # Combine chunks using ffmpeg
                    chunk_list_path = os.path.join(temp_dir, "chunks.txt")
                    with open(chunk_list_path, 'w') as f:
                        for chunk in audio_chunks:
                            f.write(f"file '{chunk}'\n")
                    
                    # Run ffmpeg to concatenate files
                    subprocess.run([
                        'ffmpeg', '-f', 'concat', '-safe', '0', 
                        '-i', chunk_list_path, '-c', 'copy', output_path
                    ])
                    
                    # Now launch the main application with the audio file
                    subprocess.Popen([
                        'python', 'app/main.py', 
                        '--audio-file', output_path,
                        '--mode', 'summarize'
                    ])
                    
                    send_message({
                        'status': 'processing_started',
                        'message': 'Audio processing has started in the main application'
                    })
                else:
                    send_message({
                        'status': 'error',
                        'message': 'No audio chunks received'
                    })
                
                # Clean up
                for chunk in audio_chunks:
                    try:
                        os.remove(chunk)
                    except:
                        pass
                break
    except Exception as e:
        logging.error(f"Error in native messaging host: {str(e)}")
        send_message({'status': 'error', 'message': str(e)})
    finally:
        # Clean up temporary directory
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass

if __name__ == "__main__":
    main() 