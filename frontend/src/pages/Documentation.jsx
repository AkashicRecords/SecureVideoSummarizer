import React, { useEffect } from 'react';
import { Card, Typography } from 'antd';

const { Title, Paragraph } = Typography;

const Documentation = () => {
  useEffect(() => {
    // Load Mermaid from CDN
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js';
    script.async = true;
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, []);

  return (
    <div className="documentation-container p-4">
      <Card>
        <Title level={2}>System Documentation</Title>
        
        <Title level={3}>Logical Data Flow</Title>
        <div className="mermaid">
          {`
            graph TD
              A[User] -->|1. Clicks Extension Icon| B[Extension Popup]
              B -->|2. Clicks Summarize| C[Content Script]
              
              subgraph Extension Layer
                C -->|3. Detects Video| D[Background Script]
                D -->|4. Prepares Data| E[Frontend API]
              end
              
              subgraph Frontend Layer
                E -->|5. Validates Request| F[Frontend Service]
                F -->|6. Forwards Request| G[Backend API]
              end
              
              subgraph Backend Layer
                G -->|7. Processes Video| H[Video Processor]
                H -->|8. Generates Summary| I[Summary Service]
                I -->|9. Returns Result| G
              end
              
              G -->|10. Response| F
              F -->|11. Response| D
              D -->|12. Updates UI| B
              B -->|13. Shows Summary| A

              style A fill:#f9f,stroke:#333,stroke-width:2px
              style B fill:#bbf,stroke:#333,stroke-width:2px
              style C fill:#bbf,stroke:#333,stroke-width:2px
              style D fill:#bbf,stroke:#333,stroke-width:2px
              style E fill:#bfb,stroke:#333,stroke-width:2px
              style F fill:#bfb,stroke:#333,stroke-width:2px
              style G fill:#fbb,stroke:#333,stroke-width:2px
              style H fill:#fbb,stroke:#333,stroke-width:2px
              style I fill:#fbb,stroke:#333,stroke-width:2px
          `}
        </div>

        <Title level={3}>Architecture Overview</Title>
        <Paragraph>
          The Secure Video Summarizer follows a three-tier architecture:
        </Paragraph>
        <ul>
          <li>Browser Extension (Chrome)</li>
          <li>Frontend Application (Port 8080)</li>
          <li>Backend Service (Port 8081)</li>
        </ul>

        <Title level={3}>Component Communication</Title>
        <div className="mermaid">
          {`
            sequenceDiagram
              participant User
              participant Extension
              participant Frontend
              participant Backend
              
              User->>Extension: Click Summarize
              Extension->>Frontend: Send Video Data
              Frontend->>Backend: Process Request
              Backend-->>Frontend: Return Summary
              Frontend-->>Extension: Update UI
              Extension-->>User: Show Result
          `}
        </div>
      </Card>
    </div>
  );
};

export default Documentation; 