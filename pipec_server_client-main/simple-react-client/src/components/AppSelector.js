import React, { useState, useEffect } from 'react';

const AppSelector = ({ onAppSelected, serverUrl, apiKey }) => {
  const [apps, setApps] = useState([]);
  const [selectedApp, setSelectedApp] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Default app ID (custom app)
  const DEFAULT_APP_ID = '0';

  useEffect(() => {
    fetchAvailableApps();
  }, []);

  const fetchAvailableApps = async () => {
    setLoading(true);
    try {
      // Try to fetch from server first
      const response = await fetch(`${serverUrl}/api/v1/apps`, {
        headers: {
          'X-API-Key': apiKey
        }
      });

      if (response.ok) {
        const appsData = await response.json();
        setApps(appsData);
      } else {
        // Fallback to hardcoded apps including custom app
        const fallbackApps = [
          {
            app_id: '0',
            name: 'Custom Demo App',
            component_count: 3,
            intent_count: 5,
            has_interactive_elements: true,
            source: 'hardcoded'
          },
          {
            app_id: 'standalone-test-36a75d3c-f9df-4d0e-9384-14d3f420370a',
            name: 'Test App 1',
            component_count: 1,
            intent_count: 1,
            has_interactive_elements: true,
            source: 'mongodb'
          }
        ];
        setApps(fallbackApps);
      }

      // Set default selection
      setSelectedApp(DEFAULT_APP_ID);
      if (onAppSelected) {
        onAppSelected(DEFAULT_APP_ID);
      }

    } catch (err) {
      setError(err.message);
      // Still set fallback data
      const fallbackApps = [
        {
          app_id: '0',
          name: 'Custom Demo App',
          component_count: 3,
          intent_count: 5,
          has_interactive_elements: true,
          source: 'hardcoded'
        }
      ];
      setApps(fallbackApps);
      setSelectedApp(DEFAULT_APP_ID);
      if (onAppSelected) {
        onAppSelected(DEFAULT_APP_ID);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAppChange = (appId) => {
    setSelectedApp(appId);
    if (onAppSelected) {
      onAppSelected(appId);
    }
  };

  if (loading) {
    return (
      <div className="card">
        <h3>🏢 App Selection</h3>
        <div className="loading">Loading available apps...</div>
      </div>
    );
  }

  return (
    <div className="card">
      <h3>🏢 App Selection</h3>
      
      {error && (
        <div style={{ 
          background: '#fff3cd', 
          border: '1px solid #ffeaa7', 
          padding: '10px', 
          borderRadius: '4px', 
          marginBottom: '15px',
          fontSize: '14px'
        }}>
          ⚠️ Could not fetch apps from server, using fallback data
        </div>
      )}

      <div className="input-group">
        <label>Select App:</label>
        <select 
          value={selectedApp} 
          onChange={(e) => handleAppChange(e.target.value)}
          style={{ 
            width: '100%', 
            padding: '10px', 
            borderRadius: '6px', 
            border: '2px solid #e1e5e9',
            fontSize: '14px'
          }}
        >
          <option value="">Choose an app...</option>
          {apps.map(app => (
            <option key={app.app_id} value={app.app_id}>
              {app.app_id === '0' ? '⭐ ' : ''}{app.name || `App ${app.app_id.substring(0, 8)}...`} 
              ({app.component_count} components, {app.intent_count} intents)
              {app.source === 'hardcoded' ? ' - Custom' : ''}
            </option>
          ))}
        </select>
      </div>

      {selectedApp && (
        <div style={{ 
          marginTop: '15px', 
          padding: '15px', 
          background: '#f8f9fa', 
          borderRadius: '6px',
          fontSize: '14px'
        }}>
          <h4 style={{ margin: '0 0 10px 0', fontSize: '16px' }}>Selected App Details:</h4>
          {(() => {
            const app = apps.find(a => a.app_id === selectedApp);
            return app ? (
              <div>
                <p><strong>App ID:</strong> {app.app_id} {app.app_id === '0' ? '⭐' : ''}</p>
                <p><strong>Components:</strong> {app.component_count}</p>
                <p><strong>Intents:</strong> {app.intent_count}</p>
                <p><strong>Interactive Elements:</strong> {app.has_interactive_elements ? 'Yes' : 'No'}</p>
                <p><strong>Source:</strong> {app.source === 'hardcoded' ? '🔧 Custom Data' : '🗄️ MongoDB'}</p>
              </div>
            ) : (
              <p>App details not available</p>
            );
          })()}
        </div>
      )}

      <div style={{ 
        marginTop: '15px', 
        padding: '10px', 
        background: '#e8f5e8', 
        borderRadius: '4px',
        fontSize: '12px'
      }}>
        💡 <strong>Default:</strong> The first app with the most components is pre-selected
      </div>
    </div>
  );
};

export default AppSelector;