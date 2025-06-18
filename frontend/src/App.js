import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [spiders, setSpiders] = useState([]);
  const [pipelineStatus, setPipelineStatus] = useState({});
  const [serviceStatus, setServiceStatus] = useState({});
  const [scrapingResults, setScrapingResults] = useState({});
  const [logs, setLogs] = useState([]);
  const [missingTaxonomy, setMissingTaxonomy] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedSpider, setSelectedSpider] = useState('');
  const [maxItems, setMaxItems] = useState(50);
  const [activeTab, setActiveTab] = useState('dashboard');

  // Fetch initial data
  useEffect(() => {
    fetchSpiders();
    fetchPipelineStatus();
    fetchServiceStatus();
    
    // Set up polling for status updates
    const interval = setInterval(() => {
      fetchPipelineStatus();
    }, 3000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchSpiders = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/spiders`);
      setSpiders(response.data.spiders);
      if (response.data.spiders.length > 0) {
        setSelectedSpider(response.data.spiders[0]);
      }
    } catch (error) {
      console.error('Failed to fetch spiders:', error);
    }
  };

  const fetchPipelineStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/status`);
      setPipelineStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch pipeline status:', error);
    }
  };

  const fetchServiceStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/test-services`);
      setServiceStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch service status:', error);
    }
  };

  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/logs?lines=100`);
      setLogs(response.data.logs);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    }
  };

  const fetchMissingTaxonomy = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/missing-taxonomy`);
      setMissingTaxonomy(response.data.missing_items);
    } catch (error) {
      console.error('Failed to fetch missing taxonomy:', error);
    }
  };

  const fetchScrapingResults = async (spiderName) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/scraping-results/${spiderName}`);
      setScrapingResults(prev => ({
        ...prev,
        [spiderName]: response.data
      }));
    } catch (error) {
      console.error('Failed to fetch scraping results:', error);
    }
  };

  const startScrapingJob = async () => {
    if (!selectedSpider) {
      alert('Please select a spider');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/start-scraping`, {
        spider_name: selectedSpider,
        max_items: maxItems
      });

      if (response.data.success) {
        alert(`Scraping job started: ${response.data.job_id}`);
        fetchPipelineStatus();
      } else {
        alert(`Failed to start scraping: ${response.data.message}`);
      }
    } catch (error) {
      alert(`Error starting scraping job: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const StatusIndicator = ({ status, label }) => {
    const getStatusColor = (status) => {
      if (status === 'success') return 'bg-green-500';
      if (status === 'error') return 'bg-red-500';
      return 'bg-yellow-500';
    };

    return (
      <div className="flex items-center space-x-2">
        <div className={`w-3 h-3 rounded-full ${getStatusColor(status)}`}></div>
        <span className="text-sm font-medium">{label}</span>
      </div>
    );
  };

  const ServiceStatusCard = ({ title, status }) => (
    <div className="bg-white p-4 rounded-lg shadow-md border-l-4 border-blue-500">
      <h3 className="font-semibold text-gray-800 mb-2">{title}</h3>
      <StatusIndicator status={status.status} label={status.status} />
      {status.error && (
        <p className="text-red-600 text-sm mt-2">{status.error}</p>
      )}
      {status.categories_count && (
        <p className="text-gray-600 text-sm mt-1">Categories: {status.categories_count}</p>
      )}
      {status.tags_loaded && (
        <p className="text-gray-600 text-sm">Tags: {status.tags_loaded}</p>
      )}
      {status.features_loaded && (
        <p className="text-gray-600 text-sm">Features: {status.features_loaded}</p>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">AI Navigator Scrapers</h1>
              <p className="text-gray-600">Automated data collection for AI tools directory</p>
            </div>
            <div className="flex items-center space-x-4">
              {pipelineStatus.is_running && (
                <div className="flex items-center space-x-2 bg-green-100 px-3 py-2 rounded-lg">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-green-800 text-sm font-medium">Running</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {['dashboard', 'scraping', 'results', 'logs', 'taxonomy'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Object.entries(serviceStatus).map(([service, status]) => (
                <ServiceStatusCard 
                  key={service}
                  title={service.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  status={status}
                />
              ))}
            </div>

            {/* Current Job Status */}
            {pipelineStatus.current_job && (
              <div className="bg-white p-6 rounded-lg shadow-md">
                <h3 className="text-lg font-semibold mb-4">Current Job Status</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {pipelineStatus.stats?.total_processed || 0}
                    </div>
                    <div className="text-sm text-gray-600">Processed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {pipelineStatus.stats?.successful_submissions || 0}
                    </div>
                    <div className="text-sm text-gray-600">Successful</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">
                      {pipelineStatus.stats?.failed_submissions || 0}
                    </div>
                    <div className="text-sm text-gray-600">Failed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-600">
                      {pipelineStatus.stats?.duplicates_skipped || 0}
                    </div>
                    <div className="text-sm text-gray-600">Skipped</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Scraping Tab */}
        {activeTab === 'scraping' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="text-lg font-semibold mb-4">Start Scraping Job</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Spider
                  </label>
                  <select
                    value={selectedSpider}
                    onChange={(e) => setSelectedSpider(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {spiders.map((spider) => (
                      <option key={spider} value={spider}>
                        {spider}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Items
                  </label>
                  <input
                    type="number"
                    value={maxItems}
                    onChange={(e) => setMaxItems(parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="1"
                    max="1000"
                  />
                </div>
                <div className="flex items-end">
                  <button
                    onClick={startScrapingJob}
                    disabled={loading || pipelineStatus.is_running}
                    className={`w-full px-4 py-2 rounded-md font-medium ${
                      loading || pipelineStatus.is_running
                        ? 'bg-gray-400 cursor-not-allowed'
                        : 'bg-blue-600 hover:bg-blue-700'
                    } text-white`}
                  >
                    {loading ? 'Starting...' : 'Start Scraping'}
                  </button>
                </div>
              </div>
              
              {pipelineStatus.is_running && (
                <div className="bg-blue-50 p-4 rounded-md">
                  <p className="text-blue-800">
                    Job is currently running: {pipelineStatus.current_job}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Results Tab */}
        {activeTab === 'results' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">Scraping Results</h3>
                <div className="flex space-x-2">
                  {spiders.map((spider) => (
                    <button
                      key={spider}
                      onClick={() => fetchScrapingResults(spider)}
                      className="px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200"
                    >
                      Load {spider}
                    </button>
                  ))}
                </div>
              </div>
              
              {Object.entries(scrapingResults).map(([spiderName, results]) => (
                <div key={spiderName} className="mb-6">
                  <h4 className="font-medium text-gray-800 mb-2">
                    {spiderName} ({results.results_count} results)
                  </h4>
                  <div className="max-h-64 overflow-y-auto bg-gray-50 p-4 rounded-md">
                    {results.results.map((result, index) => (
                      <div key={index} className="mb-2 p-2 bg-white rounded border">
                        <div className="font-medium">{result.tool_name_on_directory}</div>
                        <div className="text-sm text-gray-600 truncate">
                          {result.external_website_url}
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(result.scraped_date).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Logs Tab */}
        {activeTab === 'logs' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">System Logs</h3>
                <button
                  onClick={fetchLogs}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Refresh Logs
                </button>
              </div>
              <div className="bg-gray-900 text-green-400 p-4 rounded-md max-h-96 overflow-y-auto font-mono text-sm">
                {logs.map((log, index) => (
                  <div key={index} className="mb-1">
                    {log}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Taxonomy Tab */}
        {activeTab === 'taxonomy' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">Missing Taxonomy Items</h3>
                <button
                  onClick={fetchMissingTaxonomy}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Refresh
                </button>
              </div>
              
              {missingTaxonomy.length > 0 ? (
                <div className="max-h-64 overflow-y-auto">
                  {missingTaxonomy.map((item, index) => (
                    <div key={index} className="mb-2 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                      <div className="flex justify-between items-center">
                        <div>
                          <span className="font-medium text-yellow-800">{item.type}</span>
                          <span className="ml-2 text-gray-700">{item.name}</span>
                        </div>
                        <span className="text-sm text-gray-500">{item.timestamp}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">No missing taxonomy items found.</p>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;