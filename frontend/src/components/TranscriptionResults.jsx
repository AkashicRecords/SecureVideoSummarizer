import React, { useState } from 'react';
import { Card, Tabs, Typography, Button, Spin, Alert, Input } from 'antd';
import { 
  CopyOutlined, 
  DownloadOutlined, 
  FilePdfOutlined,
  SearchOutlined 
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { jsPDF } from 'jspdf';

const { TabPane } = Tabs;
const { Title, Paragraph } = Typography;

const TranscriptionResults = ({ transcription, summary, isLoading, error }) => {
  const [activeTab, setActiveTab] = useState('summary');
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [copySuccess, setCopySuccess] = useState('');
  
  if (isLoading) {
    return (
      <Card style={{ width: '100%', textAlign: 'center', padding: '40px 0' }}>
        <Spin size="large" />
        <Paragraph style={{ marginTop: 20 }}>Generating summary...</Paragraph>
      </Card>
    );
  }
  
  if (error) {
    return (
      <Alert
        message="Error"
        description={error}
        type="error"
        showIcon
      />
    );
  }
  
  if (!transcription && !summary) {
    return null;
  }
  
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
      .then(() => {
        setCopySuccess('Copied!');
        setTimeout(() => setCopySuccess(''), 2000);
      })
      .catch(err => {
        console.error('Failed to copy text: ', err);
      });
  };
  
  const downloadText = (text, filename) => {
    const element = document.createElement('a');
    const file = new Blob([text], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = filename;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };
  
  const exportToPDF = (title, content) => {
    const doc = new jsPDF();
    
    // Add title
    doc.setFontSize(16);
    doc.text(title, 20, 20);
    
    // Add content with word wrap
    doc.setFontSize(12);
    const splitText = doc.splitTextToSize(content, 170);
    doc.text(splitText, 20, 30);
    
    // Save the PDF
    doc.save(`${title.toLowerCase().replace(/\s+/g, '_')}.pdf`);
  };
  
  const handleSearch = (text, term) => {
    if (!term.trim()) {
      setSearchResults([]);
      return;
    }
    
    const regex = new RegExp(`(${term})`, 'gi');
    const matches = [...text.matchAll(regex)];
    setSearchResults(matches.map(match => ({
      text: match[0],
      index: match.index
    })));
  };
  
  const highlightText = (text, term) => {
    if (!term.trim()) return text;
    
    const parts = text.split(new RegExp(`(${term})`, 'gi'));
    return (
      <>
        {parts.map((part, i) => 
          part.toLowerCase() === term.toLowerCase() 
            ? <mark key={i} style={{ backgroundColor: '#FFEB3B' }}>{part}</mark> 
            : part
        )}
      </>
    );
  };
  
  return (
    <Card title="Transcription Results" style={{ width: '100%', marginTop: 20 }}>
      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        aria-label="Transcription results tabs"
      >
        <TabPane 
          tab={<span aria-label="Summary tab">Summary</span>} 
          key="summary"
          role="tabpanel"
          aria-labelledby="summary-tab"
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
            <Title level={4}>Summary</Title>
            <div>
              <Button 
                icon={<CopyOutlined />} 
                onClick={() => copyToClipboard(summary)}
                style={{ marginRight: 8 }}
                aria-label="Copy summary to clipboard"
              >
                {copySuccess && activeTab === 'summary' ? copySuccess : 'Copy'}
              </Button>
              <Button 
                icon={<DownloadOutlined />} 
                onClick={() => downloadText(summary, 'summary.txt')}
                style={{ marginRight: 8 }}
                aria-label="Download summary as text file"
              >
                Download
              </Button>
              <Button 
                icon={<FilePdfOutlined />} 
                onClick={() => exportToPDF('Summary', summary)}
                aria-label="Export summary as PDF"
              >
                PDF
              </Button>
            </div>
          </div>
          <div className="markdown-content">
            <ReactMarkdown>{summary}</ReactMarkdown>
          </div>
        </TabPane>
        
        <TabPane 
          tab={<span aria-label="Full transcript tab">Full Transcript</span>} 
          key="transcript"
          role="tabpanel"
          aria-labelledby="transcript-tab"
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
            <Title level={4}>Full Transcript</Title>
            <div>
              <Button 
                icon={<CopyOutlined />} 
                onClick={() => copyToClipboard(transcription)}
                style={{ marginRight: 8 }}
                aria-label="Copy transcript to clipboard"
              >
                {copySuccess && activeTab === 'transcript' ? copySuccess : 'Copy'}
              </Button>
              <Button 
                icon={<DownloadOutlined />} 
                onClick={() => downloadText(transcription, 'transcript.txt')}
                style={{ marginRight: 8 }}
                aria-label="Download transcript as text file"
              >
                Download
              </Button>
              <Button 
                icon={<FilePdfOutlined />} 
                onClick={() => exportToPDF('Transcript', transcription)}
                aria-label="Export transcript as PDF"
              >
                PDF
              </Button>
            </div>
          </div>
          
          <div style={{ marginBottom: 16 }}>
            <Input
              prefix={<SearchOutlined />}
              placeholder="Search in transcript..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                handleSearch(transcription, e.target.value);
              }}
              style={{ width: 300 }}
              aria-label="Search within transcript"
            />
            {searchResults.length > 0 && (
              <span style={{ marginLeft: 8 }}>
                {searchResults.length} matches found
              </span>
            )}
          </div>
          
          <div className="transcript-content">
            {searchTerm && searchResults.length > 0 
              ? highlightText(transcription, searchTerm)
              : transcription}
          </div>
        </TabPane>
      </Tabs>
    </Card>
  );
};

export default TranscriptionResults; 
export default TranscriptionResults; 