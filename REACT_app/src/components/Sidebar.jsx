import React, { useState, useEffect } from 'react';
import { History, Clock, FileText, CheckCircle, AlertTriangle, FileSearch, ChevronRight, ChevronLeft } from 'lucide-react';

export default function Sidebar({ backendUrl, onSelectHistory, selectedHistoryId, refreshTrigger }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);

  const fetchHistory = () => {
    setLoading(true);
    fetch(`${backendUrl}/history`)
      .then(res => res.json())
      .then(data => {
        setHistory(data.history || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load history", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchHistory();
    // Poll every 10 seconds to keep history updated if backend changes
    const interval = setInterval(fetchHistory, 10000);
    return () => clearInterval(interval);
  }, [backendUrl, refreshTrigger]);

  const formatDate = (isoString) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleString([], {
        month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
      });
    } catch {
      return isoString;
    }
  };

  return (
    <aside className={`sidebar ${isExpanded ? 'expanded' : 'collapsed'}`}>
      <div 
        className="sidebar-header" 
        onClick={() => setIsExpanded(!isExpanded)}
        style={{ cursor: 'pointer', justifyContent: isExpanded ? 'space-between' : 'center', padding: isExpanded ? '1.5rem' : '1.5rem 0' }}
        title={isExpanded ? "Collapse Sidebar" : "Expand Extraction Logs"}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <History size={20} />
          {isExpanded && <h2>Extraction Logs</h2>}
        </div>
        {isExpanded && <ChevronLeft size={20} />}
      </div>
      
      {isExpanded && (
        <div className="sidebar-content">
          {loading && history.length === 0 ? (
            <div className="sidebar-empty">
              <span className="loading-spinner" style={{ display: 'inline-block' }}>⟳</span> Loading...
            </div>
          ) : history.length === 0 ? (
            <div className="sidebar-empty">
              <FileSearch size={24} style={{ marginBottom: '0.5rem', opacity: 0.5 }} />
              <p>No previous extractions found.</p>
            </div>
          ) : (
            history.map(item => {
              const isSelected = selectedHistoryId === item.id;
              
              // Calculate Overall Extraction Percentage exactly like Statistics.jsx
              let overallPercentage = 0;
              let hasData = false;
              
              if (item.result?.compliance_report) {
                hasData = true;
                const report = item.result.compliance_report;
                
                const expectedTop = report.filter(row => row['Location Requirement'] === 'Top' || row['Location Requirement'] === 'Top & Bottom');
                const totalTopMetrics = expectedTop.length;
                const topFetched = expectedTop.filter(row => row.Mould_Top && row.Mould_Top !== 'NF').length;

                const expectedBottom = report.filter(row => row['Location Requirement'] === 'Bottom' || row['Location Requirement'] === 'Top & Bottom');
                const totalBottomMetrics = expectedBottom.length;
                const bottomFetched = expectedBottom.filter(row => row.Mould_Bottom && row.Mould_Bottom !== 'NF').length;

                const totalOverallMetrics = totalTopMetrics + totalBottomMetrics;
                const overallFetched = topFetched + bottomFetched;
                
                overallPercentage = totalOverallMetrics > 0 ? Math.round((overallFetched / totalOverallMetrics) * 100) : 0;
              }

              // Use sku_name from backend, fallback if it's an older log
              const hasCustomSpecs = item.sku_specifications && Object.keys(item.sku_specifications).length > 0;
              const skuName = item.sku_name || (hasCustomSpecs ? 'Custom SKU' : 'Default SKU');

              return (
                <div 
                  key={item.id} 
                  className={`history-item ${isSelected ? 'selected' : ''}`}
                  onClick={() => onSelectHistory(item)}
                >
                  <div className="history-item-header">
                    <span className="history-sku-name" title={skuName}>{skuName}</span>
                    <span className="history-date">
                      <Clock size={12} style={{ marginRight: '4px' }} />
                      {formatDate(item.timestamp)}
                    </span>
                  </div>
                  
                  <div className="history-item-metrics">
                    {hasData ? (
                      <div className="metric-badge" title="Overall Extraction">
                        <CheckCircle size={12} className="success-icon" /> 
                        {overallPercentage}% Extracted
                      </div>
                    ) : (
                      <div className="metric-badge">
                        <AlertTriangle size={12} className="warning-icon" /> No Data
                      </div>
                    )}
                    
                    <div className="metric-details-btn">
                      <FileText size={12} /> View
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}
    </aside>
  );
}
