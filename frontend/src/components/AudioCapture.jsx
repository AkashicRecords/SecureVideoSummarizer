import React, { useState, useRef, useEffect } from 'react';
import { Button, Card, Progress, Alert, Typography, Space, Upload, Tabs, Radio } from 'antd';
import { 
  AudioOutlined, 
  PauseOutlined, 
  SendOutlined, 
  UploadOutlined,
  ChromeOutlined
} from '@ant-design/icons';
import '../styles/AudioCapture.css';

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { Dragger } = Upload;

const AudioCapture = ({ onTranscriptionComplete, onStartTranscription, summaryOptions = {} }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [activeTab, setActiveTab] = useState('microphone');
  const [audioFile, setAudioFile] = useState(null);
  const [audioVisualization, setAudioVisualization] = useState([]);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const visualizationTimerRef = useRef(null);
  
  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (visualizationTimerRef.current) {
        clearInterval(visualizationTimerRef.current);
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);
  
  const startRecording = async () => {
    try {
      setError(null);
      audioChunksRef.current = [];
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      
      // Set up audio visualization
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);
      
      // Start visualization
      const bufferLength = analyserRef.current.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      
      visualizationTimerRef.current = setInterval(() => {
        analyserRef.current.getByteFrequencyData(dataArray);
        // Use only a subset of the data for visualization
        const visualizationData = Array.from(dataArray).filter((_, i) => i % 4 === 0);
        setAudioVisualization(visualizationData);
      }, 100);
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(audioBlob);
        
        // Stop all tracks to release the microphone
        stream.getTracks().forEach(track => track.stop());
        
        // Stop visualization
        if (visualizationTimerRef.current) {
          clearInterval(visualizationTimerRef.current);
          setAudioVisualization([]);
        }
      };
      
      // Start recording
      mediaRecorderRef.current.start(1000);
      setIsRecording(true);
      
      // Start timer
      setRecordingTime(0);
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
    } catch (err) {
      setError(`Could not start recording: ${err.message}`);
      console.error('Error starting recording:', err);
    }
  };
  
  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Stop timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  };
  
  const captureTabAudio = async () => {
    try {
      setError(null);
      
      // Check if Chrome extension is available
      if (!window.chrome || !window.chrome.runtime) {
        throw new Error("Chrome extension not available. Please install the extension first.");
      }
      
      // Request the extension to capture tab audio
      const response = await window.chrome.runtime.sendMessage({
        action: "captureAudioStream"
      });
      
      if (!response || !response.success) {
        throw new Error(response?.error || "Failed to capture tab audio");
      }
      
      // The extension will handle the audio processing
      // We just need to show a loading state
      setIsProcessing(true);
      if (onStartTranscription) {
        onStartTranscription();
      }
      
      // The extension will call back when done via a message listener
      window.chrome.runtime.onMessage.addListener((message) => {
        if (message.action === "transcriptionComplete") {
          setIsProcessing(false);
          if (onTranscriptionComplete) {
            onTranscriptionComplete(message.data);
          }
        }
      });
      
    } catch (err) {
      setError(`Failed to capture tab audio: ${err.message}`);
      console.error('Error capturing tab audio:', err);
    }
  };
  
  const handleFileUpload = (info) => {
    if (info.file.status === 'done') {
      setAudioFile(info.file.originFileObj);
      setAudioBlob(info.file.originFileObj);
    } else if (info.file.status === 'error') {
      setError(`${info.file.name} file upload failed.`);
    }
  };
  
  const sendForTranscription = async () => {
    const blobToSend = audioBlob || audioFile;
    
    if (!blobToSend) {
      setError('No audio recorded or uploaded');
      return;
    }
    
    setIsProcessing(true);
    setProgress(10);
    
    if (onStartTranscription) {
      onStartTranscription();
    }
    
    try {
      const formData = new FormData();
      formData.append('audio', blobToSend, 'recording.webm');
      
      // Add summary options if provided
      if (summaryOptions) {
        Object.entries(summaryOptions).forEach(([key, value]) => {
          formData.append(`options[${key}]`, value);
        });
      }
      
      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 5, 90));
      }, 500);
      
      const response = await fetch('/api/transcribe', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });
      
      clearInterval(progressInterval);
      
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setProgress(100);
      
      // Call the callback with the transcription result
      if (onTranscriptionComplete) {
        onTranscriptionComplete(data);
      }
      
    } catch (err) {
      setError(`Transcription failed: ${err.message}`);
      console.error('Error during transcription:', err);
    } finally {
      setIsProcessing(false);
    }
  };
  
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
  
  const renderAudioVisualizer = () => {
    return (
      <div className="audio-visualizer">
        {audioVisualization.map((value, index) => (
          <div 
            key={index} 
            className="visualizer-bar" 
            style={{ 
              height: `${value / 2}px`,
              opacity: value / 255
            }}
          />
        ))}
      </div>
    );
  };
  
  return (
    <Card title="Audio Capture" style={{ width: '100%', maxWidth: 600, margin: '0 auto' }}>
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="Microphone" key="microphone">
          <Space direction="vertical" style={{ width: '100%' }}>
            {error && <Alert message={error} type="error" showIcon closable />}
            
            <div style={{ textAlign: 'center', margin: '20px 0' }}>
              {isRecording ? (
                <div>
                  <Title level={4}>Recording... {formatTime(recordingTime)}</Title>
                  {renderAudioVisualizer()}
                  <Button 
                    type="primary" 
                    danger
                    icon={<PauseOutlined />} 
                    size="large" 
                    onClick={stopRecording}
                    style={{ height: 80, width: 80, borderRadius: 40, marginTop: 20 }}
                  />
                </div>
              ) : (
                <div>
                  <Title level={4}>Ready to Record</Title>
                  <Button 
                    type="primary" 
                    icon={<AudioOutlined />} 
                    size="large" 
                    onClick={startRecording}
                    disabled={isProcessing}
                    style={{ height: 80, width: 80, borderRadius: 40 }}
                  />
                </div>
              )}
            </div>
            
            {audioBlob && !isRecording && (
              <div style={{ marginTop: 20 }}>
                <audio controls src={URL.createObjectURL(audioBlob)} style={{ width: '100%' }} />
                
                <Button 
                  type="primary" 
                  icon={<SendOutlined />}
                  onClick={sendForTranscription}
                  loading={isProcessing}
                  style={{ marginTop: 10, width: '100%' }}
                >
                  Transcribe Audio
                </Button>
                
                {isProcessing && (
                  <div style={{ marginTop: 10 }}>
                    <Text>Processing audio...</Text>
                    <Progress percent={progress} status="active" />
                  </div>
                )}
              </div>
            )}
          </Space>
        </TabPane>
        
        <TabPane tab="Upload File" key="upload">
          <Space direction="vertical" style={{ width: '100%' }}>
            {error && <Alert message={error} type="error" showIcon closable />}
            
            <Dragger
              name="file"
              multiple={false}
              action="/"
              customRequest={({ onSuccess }) => setTimeout(() => onSuccess("ok"), 0)}
              onChange={handleFileUpload}
              accept="audio/*"
              showUploadList={false}
              disabled={isProcessing}
            >
              <p className="ant-upload-drag-icon">
                <UploadOutlined />
              </p>
              <p className="ant-upload-text">Click or drag audio file to this area to upload</p>
              <p className="ant-upload-hint">
                Support for single audio file upload. MP3, WAV, and other audio formats.
              </p>
            </Dragger>
            
            {audioFile && (
              <div style={{ marginTop: 20 }}>
                <audio controls src={URL.createObjectURL(audioFile)} style={{ width: '100%' }} />
                
                <Button 
                  type="primary" 
                  icon={<SendOutlined />}
                  onClick={sendForTranscription}
                  loading={isProcessing}
                  style={{ marginTop: 10, width: '100%' }}
                >
                  Transcribe Audio
                </Button>
                
                {isProcessing && (
                  <div style={{ marginTop: 10 }}>
                    <Text>Processing audio...</Text>
                    <Progress percent={progress} status="active" />
                  </div>
                )}
              </div>
            )}
          </Space>
        </TabPane>
        
        <TabPane tab="Browser Tab" key="browser">
          <Space direction="vertical" style={{ width: '100%' }}>
            {error && <Alert message={error} type="error" showIcon closable />}
            
            <div style={{ textAlign: 'center', margin: '20px 0' }}>
              <Title level={4}>Capture Audio from Browser Tab</Title>
              <p>
                This feature requires the Chrome extension to be installed.
                It will capture audio from the currently active tab.
              </p>
              
              <Button 
                type="primary" 
                icon={<ChromeOutlined />} 
                size="large" 
                onClick={captureTabAudio}
                disabled={isProcessing}
                style={{ marginTop: 20 }}
              >
                Start Capturing Tab Audio
              </Button>
              
              {isProcessing && (
                <div style={{ marginTop: 20 }}>
                  <Text>Processing audio from browser tab...</Text>
                  <Progress percent={progress} status="active" />
                </div>
              )}
            </div>
          </Space>
        </TabPane>
      </Tabs>
    </Card>
  );
};

export default AudioCapture; 