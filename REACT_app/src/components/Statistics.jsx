import React from 'react';

export default function Statistics({ report }) {
  if (!report || report.length === 0) return null;

  const totalMetrics = report.length;

  // Calculate for Top Side
  const topFetched = report.filter(row => row.Mould_Top && row.Mould_Top !== 'NF').length;
  const topPercentage = Math.round((topFetched / totalMetrics) * 100) || 0;

  // Calculate for Bottom Side
  const bottomFetched = report.filter(row => row.Mould_Bottom && row.Mould_Bottom !== 'NF').length;
  const bottomPercentage = Math.round((bottomFetched / totalMetrics) * 100) || 0;
  
  // Calculate Overall Fetched (Found on either Top OR Bottom)
  const overallFetched = report.filter(row => 
    (row.Mould_Top && row.Mould_Top !== 'NF') || 
    (row.Mould_Bottom && row.Mould_Bottom !== 'NF')
  ).length;
  const overallPercentage = Math.round((overallFetched / totalMetrics) * 100) || 0;

  return (
    <div className="grid-3" style={{ marginBottom: '2rem' }}>
      <div className="card" style={{ textAlign: 'center' }}>
        <h3 style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Top Side Extraction</h3>
        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--primary)', margin: '0.5rem 0' }}>
          {topPercentage}%
        </div>
        <p>{topFetched} / {totalMetrics} metrics fetched</p>
      </div>

      <div className="card" style={{ textAlign: 'center' }}>
        <h3 style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Bottom Side Extraction</h3>
        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--info)', margin: '0.5rem 0' }}>
          {bottomPercentage}%
        </div>
        <p>{bottomFetched} / {totalMetrics} metrics fetched</p>
      </div>

      <div className="card" style={{ textAlign: 'center', background: 'rgba(16, 185, 129, 0.1)', borderColor: 'var(--success)' }}>
        <h3 style={{ color: 'var(--success)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Overall Extraction</h3>
        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--success)', margin: '0.5rem 0' }}>
          {overallPercentage}%
        </div>
        <p>{overallFetched} / {totalMetrics} metrics found</p>
      </div>
    </div>
  );
}
