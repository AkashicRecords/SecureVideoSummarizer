import unittest
from app.summarizer.processor import VideoSummarizer

class TestVideoSummarizer(unittest.TestCase):
    
    def setUp(self):
        self.summarizer = VideoSummarizer(trust_remote_code=True)
    
    def test_valid_audio_transcription_and_summarization(self):
        # Test with a valid audio file path
        audio_path = 'tests/test_audio.wav'  # Use a valid test audio file for testing
        options = {
            'length': 'medium',
            'format': 'bullets',
            'focus': ['key_points']
        }
        result = self.summarizer.process_video(audio_path, options)
        self.assertIn('transcript', result)
        self.assertIn('summary', result)
        self.assertGreater(len(result['transcript']), 0)
        self.assertGreater(len(result['summary']), 0)

    def test_invalid_audio_file(self):
        # Test with an invalid audio file path
        audio_path = 'tests/test_invalid_audio.wav'  # Use an invalid test audio file for testing
        options = {}
        with self.assertRaises(Exception):
            self.summarizer.process_video(audio_path, options)

    # Additional tests can be added here

if __name__ == '__main__':
    unittest.main()
