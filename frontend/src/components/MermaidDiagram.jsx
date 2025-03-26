import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

// Initialize mermaid with default configuration
mermaid.initialize({
  startOnLoad: true,
  theme: 'default',
  securityLevel: 'loose',
  logLevel: 'error'
});

const MermaidDiagram = ({ diagram }) => {
  const elementRef = useRef(null);

  useEffect(() => {
    if (elementRef.current) {
      mermaid.render('mermaid-diagram', diagram).then(({ svg }) => {
        elementRef.current.innerHTML = svg;
      });
    }
  }, [diagram]);

  return (
    <div className="mermaid-diagram" ref={elementRef}>
      {/* Mermaid will render here */}
    </div>
  );
};

export default MermaidDiagram; 