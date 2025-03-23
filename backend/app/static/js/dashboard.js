// SVS Admin Dashboard
// Simple React application without build tools

// Main CSS already loaded in the HTML template

// Create basic React components using React.createElement
// For simplicity, we're not using JSX since we don't have a build system

// Root component
function App() {
  const [page, setPage] = React.useState(window.location.pathname.split('/').pop() || 'home');
  const [data, setData] = React.useState({
    status: 'loading',
    metrics: {},
    logs: [],
    directories: [],
    jobs: []
  });
  const [error, setError] = React.useState(null);
  const [lastUpdated, setLastUpdated] = React.useState(new Date());
  const [autoRefresh, setAutoRefresh] = React.useState(true);
  const [jobRefreshInterval, setJobRefreshInterval] = React.useState(null);

  // Fetch data based on current page
  React.useEffect(() => {
    if (!autoRefresh) return;
    
    const fetchData = async () => {
      try {
        if (page === 'home' || page === 'dashboard') {
          const response = await fetch('/api/admin/status');
          const statusData = await response.json();
          
          if (statusData.status === 'error') {
            setError(statusData.message);
            return;
          }
          
          setData(prevData => ({
            ...prevData,
            status: statusData.status,
            metrics: statusData.metrics,
            lastChecked: statusData.last_checked
          }));
        } 
        else if (page === 'logs') {
          const response = await fetch('/api/admin/logs');
          const logsData = await response.json();
          
          if (logsData.status === 'error') {
            setError(logsData.message);
            return;
          }
          
          setData(prevData => ({
            ...prevData,
            logs: logsData.logs
          }));
        }
        else if (page === 'files') {
          const response = await fetch('/api/admin/files');
          const filesData = await response.json();
          
          if (filesData.status === 'error') {
            setError(filesData.message);
            return;
          }
          
          setData(prevData => ({
            ...prevData,
            directories: filesData.directories
          }));
        }
        else if (page === 'jobs') {
          const response = await fetch('/api/admin/jobs');
          const jobsData = await response.json();
          
          if (jobsData.status === 'error') {
            setError(jobsData.message);
            return;
          }
          
          setData(prevData => ({
            ...prevData,
            jobs: jobsData.jobs
          }));
        }
        else if (page === 'extension') {
          const response = await fetch('/api/admin/extension/logs');
          const extensionData = await response.json();
          
          if (extensionData.status === 'error') {
            setError(extensionData.message);
            return;
          }
          
          setData(prevData => ({
            ...prevData,
            extensionLogs: extensionData.logs
          }));
        }
        
        // Clear any previous errors
        setError(null);
        setLastUpdated(new Date());
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Failed to fetch data. Check console for details.');
      }
    };
    
    fetchData();
    
    // Set up auto-refresh
    const interval = setInterval(() => {
      fetchData();
    }, 30000); // Refresh every 30 seconds
    
    return () => clearInterval(interval);
  }, [page, autoRefresh]);

  // Set up more frequent refresh for jobs page
  React.useEffect(() => {
    // Clear any existing interval when changing pages
    if (jobRefreshInterval) {
      clearInterval(jobRefreshInterval);
      setJobRefreshInterval(null);
    }
    
    // If on jobs page and auto-refresh is enabled, set up more frequent refresh
    if (page === 'jobs' && autoRefresh) {
      const fetchJobData = async () => {
        try {
          const response = await fetch('/api/admin/jobs');
          const jobsData = await response.json();
          
          if (jobsData.status !== 'error') {
            setData(prevData => ({
              ...prevData,
              jobs: jobsData.jobs
            }));
            setLastUpdated(new Date());
          }
        } catch (err) {
          console.error('Error fetching job data:', err);
        }
      };
      
      // Create a new interval with more frequent updates
      const interval = setInterval(fetchJobData, 3000); // Refresh jobs every 3 seconds
      setJobRefreshInterval(interval);
      
      return () => {
        clearInterval(interval);
        setJobRefreshInterval(null);
      };
    }
  }, [page, autoRefresh]);
  
  // Update URL and page state when navigating
  const navigate = (newPage) => {
    window.history.pushState({}, '', `/dashboard/${newPage}`);
    setPage(newPage);
  };
  
  // Listen for browser back/forward buttons
  React.useEffect(() => {
    const handlePopState = () => {
      const newPage = window.location.pathname.split('/').pop() || 'home';
      setPage(newPage);
    };
    
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);
  
  // Render appropriate page content
  let content;
  if (error) {
    content = React.createElement(ErrorMessage, { message: error });
  } else {
    switch (page) {
      case 'home':
      case 'dashboard':
        content = React.createElement(Dashboard, { data });
        break;
      case 'logs':
        content = React.createElement(LogsPage, { logs: data.logs });
        break;
      case 'files':
        content = React.createElement(FilesPage, { directories: data.directories });
        break;
      case 'jobs':
        content = React.createElement(JobsPage, { jobs: data.jobs });
        break;
      case 'extension':
        content = React.createElement(ExtensionPage, { logs: data.extensionLogs });
        break;
      case 'docs':
        content = React.createElement(DocsPage, {});
        break;
      default:
        content = React.createElement(Dashboard, { data });
    }
  }
  
  return React.createElement(
    'div', 
    { className: 'app-container' },
    React.createElement(Header, { page, navigate }),
    React.createElement('div', { className: 'refresh-control' },
      React.createElement('span', {}, `Last updated: ${lastUpdated.toLocaleTimeString()}`),
      React.createElement('label', {},
        React.createElement('input', {
          type: 'checkbox',
          checked: autoRefresh,
          onChange: () => setAutoRefresh(!autoRefresh)
        }),
        'Auto-refresh'
      ),
      React.createElement('button', {
        className: 'refresh-button',
        onClick: () => {
          setLastUpdated(new Date());
          // Force refresh by changing page and changing back
          const currentPage = page;
          setPage('_temp_');
          setTimeout(() => setPage(currentPage), 0);
        }
      }, 'Refresh Now')
    ),
    content
  );
}

// Header component with navigation
function Header({ page, navigate }) {
  return React.createElement(
    'header', 
    { className: 'app-header' },
    React.createElement('h1', {}, 'SVS Admin Dashboard'),
    React.createElement(
      'nav',
      { className: 'main-nav' },
      React.createElement(
        'ul',
        {},
        React.createElement(
          'li',
          { className: page === 'home' || page === 'dashboard' ? 'active' : '' },
          React.createElement('a', { onClick: () => navigate('') }, 'Dashboard')
        ),
        React.createElement(
          'li',
          { className: page === 'logs' ? 'active' : '' },
          React.createElement('a', { onClick: () => navigate('logs') }, 'Logs')
        ),
        React.createElement(
          'li',
          { className: page === 'files' ? 'active' : '' },
          React.createElement('a', { onClick: () => navigate('files') }, 'Files')
        ),
        React.createElement(
          'li',
          { className: page === 'jobs' ? 'active' : '' },
          React.createElement('a', { onClick: () => navigate('jobs') }, 'Jobs')
        ),
        React.createElement(
          'li',
          { className: page === 'extension' ? 'active' : '' },
          React.createElement('a', { onClick: () => navigate('extension') }, 'Extension')
        ),
        React.createElement(
          'li',
          { className: page === 'docs' ? 'active' : '' },
          React.createElement('a', { onClick: () => navigate('docs') }, 'Docs')
        )
      )
    )
  );
}

// Error message component
function ErrorMessage({ message }) {
  return React.createElement(
    'div',
    { className: 'error-container' },
    React.createElement('h2', {}, 'Error'),
    React.createElement('p', {}, message)
  );
}

// Main Dashboard component
function Dashboard({ data }) {
  const { status, metrics, lastChecked } = data;
  
  return React.createElement(
    'div',
    { className: 'dashboard-container' },
    React.createElement('h2', {}, 'System Status'),
    React.createElement(
      'div',
      { className: 'metrics-grid' },
      React.createElement(
        'div',
        { className: 'metric-card' },
        React.createElement('h3', {}, 'Server Status'),
        React.createElement('p', { className: 'metric-value' }, status || 'Loading...'),
        React.createElement('small', {}, `Last checked: ${lastChecked || 'N/A'}`)
      ),
      React.createElement(
        'div',
        { className: 'metric-card' },
        React.createElement('h3', {}, 'Processed Videos'),
        React.createElement('p', { className: 'metric-value' }, metrics?.video_count || '0'),
        React.createElement('small', {}, 'Total videos processed')
      ),
      React.createElement(
        'div',
        { className: 'metric-card' },
        React.createElement('h3', {}, 'Active Jobs'),
        React.createElement('p', { className: 'metric-value' }, metrics?.active_jobs || '0'),
        React.createElement('small', {}, 'Currently running tasks')
      ),
      React.createElement(
        'div',
        { className: 'metric-card' },
        React.createElement('h3', {}, 'Disk Usage'),
        React.createElement('p', { className: 'metric-value' }, 
          metrics?.disk_used_percent ? `${metrics.disk_used_percent}%` : 'N/A'
        ),
        React.createElement('small', {}, 
          metrics?.disk_free_gb ? `Free space: ${metrics.disk_free_gb} GB` : 'N/A'
        )
      )
    )
  );
}

// Logs page component
function LogsPage({ logs = [] }) {
  return React.createElement(
    'div',
    { className: 'logs-container' },
    React.createElement('h2', {}, 'System Logs'),
    logs.length === 0 
      ? React.createElement('p', { className: 'no-data' }, 'No logs available')
      : React.createElement(
          'div',
          { className: 'logs-list' },
          logs.map((log, index) => 
            React.createElement(
              'div',
              { 
                key: index,
                className: `log-entry log-${log.level?.toLowerCase() || 'info'}`
              },
              React.createElement('span', { className: 'log-timestamp' }, log.timestamp),
              React.createElement('span', { className: 'log-level' }, log.level),
              React.createElement('span', { className: 'log-message' }, log.message)
            )
          )
        )
  );
}

// Files page component
function FilesPage({ directories = [] }) {
  return React.createElement(
    'div',
    { className: 'files-container' },
    React.createElement('h2', {}, 'File Storage'),
    directories.length === 0 
      ? React.createElement('p', { className: 'no-data' }, 'No directory information available')
      : React.createElement(
          'div',
          { className: 'directories-list' },
          directories.map((dir, index) => 
            React.createElement(
              'div',
              { 
                key: index,
                className: 'directory-card'
              },
              React.createElement('h3', {}, dir.name),
              React.createElement('p', {}, `Location: ${dir.path}`),
              React.createElement('p', {}, `Files: ${dir.file_count} (${dir.size_human})`),
              dir.files && dir.files.length > 0 
                ? React.createElement(
                    'table',
                    { className: 'files-table' },
                    React.createElement(
                      'thead',
                      {},
                      React.createElement(
                        'tr',
                        {},
                        React.createElement('th', {}, 'Filename'),
                        React.createElement('th', {}, 'Size'),
                        React.createElement('th', {}, 'Modified')
                      )
                    ),
                    React.createElement(
                      'tbody',
                      {},
                      dir.files.map((file, fileIndex) => 
                        React.createElement(
                          'tr',
                          { key: fileIndex },
                          React.createElement('td', {}, file.name),
                          React.createElement('td', {}, file.size_human),
                          React.createElement('td', {}, file.modified)
                        )
                      )
                    )
                  )
                : React.createElement('p', { className: 'no-data' }, 'No files')
            )
          )
        )
  );
}

// Jobs page component
function JobsPage({ jobs = [] }) {
  // Separate active and completed jobs
  const activeJobs = jobs.filter(job => job.status === 'running' || job.status === 'pending');
  const completedJobs = jobs.filter(job => job.status === 'completed' || job.status === 'failed');
  
  return React.createElement(
    'div',
    { className: 'jobs-container' },
    
    // Active Jobs Section
    React.createElement('h2', {}, 'Active Jobs'),
    activeJobs.length === 0 
      ? React.createElement('p', { className: 'no-data' }, 'No active jobs')
      : React.createElement(
          'div',
          { className: 'active-jobs-list' },
          activeJobs.map((job, index) => 
            React.createElement(
              'div',
              { 
                key: index,
                className: 'job-card'
              },
              React.createElement('div', { className: 'job-header' },
                React.createElement('h3', {}, `${job.type} - ${job.video_id}`),
                React.createElement('span', { className: `status-${job.status}` }, job.status)
              ),
              React.createElement('div', { className: 'job-progress-container' },
                React.createElement('div', { 
                  className: 'job-progress-bar',
                  style: { width: `${job.progress}%` }
                }),
                React.createElement('span', { className: 'job-progress-text' }, 
                  job.progress === 100 ? 'Done!' : `${job.progress}%`
                )
              ),
              React.createElement('div', { className: 'job-details' },
                React.createElement('span', {}, `Started: ${job.started}`),
                React.createElement(
                  'button',
                  { 
                    className: 'btn-details',
                    onClick: () => alert(JSON.stringify(job.metadata, null, 2))
                  },
                  'Details'
                )
              )
            )
          )
        ),
    
    // Completed Jobs Section
    React.createElement('h2', { className: 'mt-4' }, 'Completed Jobs'),
    completedJobs.length === 0 
      ? React.createElement('p', { className: 'no-data' }, 'No completed jobs')
      : React.createElement(
          'table',
          { className: 'jobs-table' },
          React.createElement(
            'thead',
            {},
            React.createElement(
              'tr',
              {},
              React.createElement('th', {}, 'ID'),
              React.createElement('th', {}, 'Type'),
              React.createElement('th', {}, 'Video'),
              React.createElement('th', {}, 'Status'),
              React.createElement('th', {}, 'Started'),
              React.createElement('th', {}, 'Duration'),
              React.createElement('th', {}, 'Details')
            )
          ),
          React.createElement(
            'tbody',
            {},
            completedJobs.map((job, index) => 
              React.createElement(
                'tr',
                { key: index },
                React.createElement('td', {}, job.id),
                React.createElement('td', {}, job.type),
                React.createElement('td', {}, job.video_id),
                React.createElement(
                  'td', 
                  { className: `status-${job.status}` }, 
                  job.status
                ),
                React.createElement('td', {}, job.started),
                React.createElement('td', {}, job.duration || 'N/A'),
                React.createElement(
                  'td',
                  {},
                  React.createElement(
                    'button',
                    { 
                      className: 'btn-details',
                      onClick: () => alert(JSON.stringify(job.metadata, null, 2))
                    },
                    'View Details'
                  )
                )
              )
            )
          )
        )
  );
}

// Extension page component
function ExtensionPage({ logs = [] }) {
  return React.createElement(
    'div',
    { className: 'extension-container' },
    React.createElement('h2', {}, 'Extension Monitoring'),
    React.createElement('div', { className: 'extension-status-cards' },
      React.createElement('div', { className: 'status-card' },
        React.createElement('h3', {}, 'Extension Status'),
        React.createElement('p', {}, 'Content script reporting is available'),
        React.createElement('p', {}, 'To report content script state, use the inspect_content_script.js tool')
      )
    ),
    React.createElement('h3', {}, 'Submitted Content Script Reports'),
    logs.length === 0 
      ? React.createElement('p', { className: 'no-data' }, 'No extension logs available')
      : React.createElement(
          'div',
          { className: 'extension-logs-list' },
          logs.map((log, index) => 
            React.createElement(
              'div',
              { 
                key: index,
                className: 'extension-log-entry'
              },
              React.createElement('div', { className: 'log-header' },
                React.createElement('span', { className: 'log-timestamp' }, log.timestamp),
                React.createElement('span', { className: 'log-browser' }, log.browser),
                React.createElement('span', { className: 'log-url' }, log.url)
              ),
              React.createElement('pre', { className: 'log-content' }, 
                JSON.stringify(log.content, null, 2)
              )
            )
          )
        )
  );
}

// Documentation page component
function DocsPage() {
  return React.createElement(
    'div',
    { className: 'docs-container' },
    React.createElement('h2', {}, 'Documentation'),
    React.createElement('div', { className: 'docs-section' },
      React.createElement('h3', {}, 'Content Script Inspection'),
      React.createElement('p', {}, 
        'To inspect a content script, open the browser console on a page where the extension ' +
        'is active and paste the code from extension/tools/inspect_content_script.js'
      ),
      React.createElement('p', {}, 
        'The inspection will show if the content script is loaded, what videos are detected, ' +
        'and the current state of the extension.'
      )
    ),
    React.createElement('div', { className: 'docs-section' },
      React.createElement('h3', {}, 'Troubleshooting'),
      React.createElement('p', {}, 'Common issues and their solutions:'),
      React.createElement('ul', {},
        React.createElement('li', {}, 
          React.createElement('strong', {}, 'Content script not detected: '),
          'Check that the extension is installed and the current URL matches the patterns in manifest.json'
        ),
        React.createElement('li', {}, 
          React.createElement('strong', {}, 'No video found: '),
          'The content script may not be able to find the video element. This can happen if the video is in an iframe or uses a non-standard player.'
        ),
        React.createElement('li', {}, 
          React.createElement('strong', {}, 'API connection issues: '),
          'Check that the backend server is running and CORS is properly configured.'
        )
      )
    )
  );
}

// Mount the React app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  const root = document.getElementById('root');
  
  // Add loading spinner while React initializes
  root.innerHTML = '<div class="loading-spinner"></div>';
  
  // Load React and ReactDOM from CDN
  const loadScripts = () => {
    const reactScript = document.createElement('script');
    reactScript.src = 'https://unpkg.com/react@17/umd/react.production.min.js';
    
    const reactDomScript = document.createElement('script');
    reactDomScript.src = 'https://unpkg.com/react-dom@17/umd/react-dom.production.min.js';
    
    reactScript.onload = () => {
      document.body.appendChild(reactDomScript);
    };
    
    reactDomScript.onload = () => {
      ReactDOM.render(React.createElement(App), root);
    };
    
    document.body.appendChild(reactScript);
  };
  
  loadScripts();
}); 