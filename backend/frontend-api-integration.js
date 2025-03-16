/**
 * API integration functions for the SecureVideoSummarizer frontend
 * 
 * This file contains the API functions that should be integrated into the frontend
 * to communicate with the backend endpoints, including the new video summarization endpoint.
 */

// Base API URL - adjust according to your environment
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

/**
 * Get the authentication token from localStorage
 * @returns {string} The authentication token
 */
const getAuthToken = () => {
  return localStorage.getItem('authToken');
};

/**
 * Common headers for API requests
 * @returns {Object} Headers object
 */
const getHeaders = () => {
  const token = getAuthToken();
  return {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : '',
  };
};

/**
 * Upload a video file to the server
 * @param {File} file - The video file to upload
 * @returns {Promise<Object>} Promise resolving to the response data
 */
export const uploadVideo = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE_URL}/video/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`,
      // Do not include Content-Type, as it will be automatically set with the boundary
    },
    body: formData,
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to upload video');
  }
  
  return response.json();
};

/**
 * Get a list of all uploaded videos
 * @returns {Promise<Object>} Promise resolving to the response data
 */
export const listVideos = async () => {
  const response = await fetch(`${API_BASE_URL}/video/list`, {
    method: 'GET',
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to list videos');
  }
  
  return response.json();
};

/**
 * Delete a video by ID
 * @param {string} videoId - The ID of the video to delete
 * @returns {Promise<Object>} Promise resolving to the response data
 */
export const deleteVideo = async (videoId) => {
  const response = await fetch(`${API_BASE_URL}/video/${videoId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to delete video');
  }
  
  return response.json();
};

/**
 * Summarize a video by ID
 * @param {string} videoId - The ID of the video to summarize
 * @param {Object} options - Summarization options
 * @param {string} options.length - Length of the summary ('short', 'medium', 'long')
 * @param {string} options.format - Format of the summary ('paragraph', 'bullets', 'numbered', 'key_points')
 * @param {Array<string>} options.focus - Focus areas for the summary (['key_points'], ['detailed'])
 * @returns {Promise<Object>} Promise resolving to the summarization result
 */
export const summarizeVideo = async (videoId, options = {}) => {
  const defaultOptions = {
    length: 'medium',
    format: 'bullets',
    focus: ['key_points'],
  };
  
  const summarizationOptions = { ...defaultOptions, ...options };
  
  const response = await fetch(`${API_BASE_URL}/api/summarize/video/${videoId}`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(summarizationOptions),
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to summarize video');
  }
  
  return response.json();
};

/**
 * Transcribe an audio blob
 * @param {Blob} audioBlob - The audio blob to transcribe
 * @returns {Promise<Object>} Promise resolving to the transcription result
 */
export const transcribeAudio = async (audioBlob) => {
  const formData = new FormData();
  formData.append('audio', audioBlob);
  
  const response = await fetch(`${API_BASE_URL}/api/transcribe`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`,
    },
    body: formData,
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to transcribe audio');
  }
  
  return response.json();
};

// Example frontend component to implement video upload and summarization
/*
import React, { useState } from 'react';
import { uploadVideo, summarizeVideo } from './api';

const VideoUploader = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [videoId, setVideoId] = useState(null);
  const [summarizing, setSummarizing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    
    setUploading(true);
    setError(null);
    
    try {
      const response = await uploadVideo(file);
      setVideoId(response.video_id);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleSummarize = async () => {
    if (!videoId) return;
    
    setSummarizing(true);
    setError(null);
    
    try {
      const options = {
        length: 'medium',
        format: 'bullets',
        focus: ['key_points'],
      };
      
      const response = await summarizeVideo(videoId, options);
      setResult(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setSummarizing(false);
    }
  };

  return (
    <div>
      <h2>Upload and Summarize Video</h2>
      
      <div>
        <input type="file" accept="video/*" onChange={handleFileChange} />
        <button onClick={handleUpload} disabled={!file || uploading}>
          {uploading ? 'Uploading...' : 'Upload Video'}
        </button>
      </div>
      
      {videoId && (
        <div>
          <p>Video uploaded successfully! ID: {videoId}</p>
          <button onClick={handleSummarize} disabled={summarizing}>
            {summarizing ? 'Summarizing...' : 'Summarize Video'}
          </button>
        </div>
      )}
      
      {error && (
        <div className="error">
          <p>Error: {error}</p>
        </div>
      )}
      
      {result && (
        <div className="result">
          <h3>Summarization Result</h3>
          
          <div className="transcript">
            <h4>Transcript</h4>
            <p>{result.transcript}</p>
          </div>
          
          <div className="summary">
            <h4>Summary</h4>
            <div dangerouslySetInnerHTML={{ __html: result.summary.replace(/\n/g, '<br>') }} />
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoUploader;
*/ 