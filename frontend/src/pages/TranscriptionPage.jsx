import React, { useState } from 'react';
import { Layout, Typography, Divider, Alert, Card, Form, Radio, Collapse, List, Empty, Button } from 'antd';
import AudioCapture from '../components/AudioCapture';
import TranscriptionResults from '../components/TranscriptionResults';
import '../styles/TranscriptionPage.css';

const { Content } = Layout;
const { Title, Paragraph } = Typography;
const { Panel } = Collapse;

const TranscriptionPage = () => {
  const [transcriptionData, setTranscriptionData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [transcriptionHistory, setTranscriptionHistory] = useState([]);
  const [summaryOptions, setSummaryOptions] = useState({
    length: 'medium',
    format: 'paragraph'
  });
  
  const handleTranscriptionComplete = (data) => {
    if (data.success) {
      const newTranscription = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        transcription: data.transcription,
        summary: data.summary
      };
      
      setTranscriptionData(newTranscription);
      setTranscriptionHistory(prev => [newTranscription, ...prev]);
      setError(null);
    } else {
      setError(data.error || 'An unknown error occurred');
    }
    setIsLoading(false);
  };
  
  const handleStartTranscription = () => {
    setIsLoading(true);
    setError(null);
  };
  
  const handleOptionChange = (field, value) => {
    setSummaryOptions(prev => ({
      ...prev,
      [field]: value
    }));
  };
  
  return (
    <Layout>
      <Content style={{ padding: '50px 50px', maxWidth: 1200, margin: '0 auto' }}>
        <Title level={2}>Video Transcription & Summarization</Title>
        <Paragraph>
          Record audio from a video, upload an audio file, or capture audio from a browser tab to generate a transcription and summary.
        </Paragraph>
        
        <Divider />
        
        <Card title="Summarization Options" style={{ marginBottom: 20 }}>
          <Form layout="inline">
            <Form.Item label="Summary Length">
              <Radio.Group 
                value={summaryOptions.length}
                onChange={e => handleOptionChange('length', e.target.value)}
              >
                <Radio.Button value="short">Short</Radio.Button>
                <Radio.Button value="medium">Medium</Radio.Button>
                <Radio.Button value="long">Long</Radio.Button>
              </Radio.Group>
            </Form.Item>
            
            <Form.Item label="Format">
              <Radio.Group 
                value={summaryOptions.format}
                onChange={e => handleOptionChange('format', e.target.value)}
              >
                <Radio.Button value="paragraph">Paragraph</Radio.Button>
                <Radio.Button value="bullets">Bullet Points</Radio.Button>
              </Radio.Group>
            </Form.Item>
          </Form>
        </Card>
        
        <AudioCapture 
          onTranscriptionComplete={handleTranscriptionComplete}
          onStartTranscription={handleStartTranscription}
          summaryOptions={summaryOptions}
        />
        
        {error && (
          <Alert
            message="Error"
            description={error}
            type="error"
            showIcon
            style={{ marginTop: 20 }}
          />
        )}
        
        <TranscriptionResults
          transcription={transcriptionData?.transcription}
          summary={transcriptionData?.summary}
          isLoading={isLoading}
          error={error}
        />
        
        <Collapse style={{ marginTop: 30 }}>
          <Panel header="Transcription History" key="history">
            {transcriptionHistory.length === 0 ? (
              <Empty description="No transcription history" />
            ) : (
              <List
                dataSource={transcriptionHistory}
                renderItem={item => (
                  <List.Item 
                    actions={[
                      <Button onClick={() => setTranscriptionData(item)}>View</Button>
                    ]}
                  >
                    <List.Item.Meta
                      title={`Transcription from ${new Date(item.timestamp).toLocaleString()}`}
                      description={item.summary.substring(0, 100) + '...'}
                    />
                  </List.Item>
                )}
              />
            )}
          </Panel>
        </Collapse>
      </Content>
    </Layout>
  );
};

export default TranscriptionPage; 