import React from 'react';

export default function Statistics({ report }) {
  if (!report || report.length === 0) return null;

  const totalMetrics = report.length;

  // Calculate for Top Side (out of metrics expected on Top)
  const expectedTop = report.filter(row => row['Location Requirement'] === 'Top' || row['Location Requirement'] === 'Top & Bottom');
  const totalTopMetrics = expectedTop.length; // e.g. 25
  const topFetched = expectedTop.filter(row => row.Mould_Top && row.Mould_Top !== 'NF').length;
  const topPercentage = totalTopMetrics > 0 ? Math.round((topFetched / totalTopMetrics) * 100) : 0;

  // Calculate for Bottom Side (out of metrics expected on Bottom)
  const expectedBottom = report.filter(row => row['Location Requirement'] === 'Bottom' || row['Location Requirement'] === 'Top & Bottom');
  const totalBottomMetrics = expectedBottom.length; // e.g. 25
  const bottomFetched = expectedBottom.filter(row => row.Mould_Bottom && row.Mould_Bottom !== 'NF').length;
  const bottomPercentage = totalBottomMetrics > 0 ? Math.round((bottomFetched / totalBottomMetrics) * 100) : 0;

  // Calculate Overall Fetched (Sum of Top and Bottom successes out of 50 total expected locations)
  const totalOverallMetrics = totalTopMetrics + totalBottomMetrics; // e.g. 50
  const overallFetched = topFetched + bottomFetched;
  const overallPercentage = totalOverallMetrics > 0 ? Math.round((overallFetched / totalOverallMetrics) * 100) : 0;

  return (
    <div className="grid-3" style={{ marginBottom: '2rem' }}>
      <div className="card" style={{ textAlign: 'center' }}>
        <h3 style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Top Side Extraction</h3>
        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--primary)', margin: '0.5rem 0' }}>
          {topPercentage}%
        </div>
        <p>{topFetched} / {totalTopMetrics} metrics fetched</p>
      </div>

      <div className="card" style={{ textAlign: 'center' }}>
        <h3 style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Bottom Side Extraction</h3>
        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--info)', margin: '0.5rem 0' }}>
          {bottomPercentage}%
        </div>
        <p>{bottomFetched} / {totalBottomMetrics} metrics fetched</p>
      </div>

      <div className="card" style={{ textAlign: 'center', background: 'rgba(16, 185, 129, 0.1)', borderColor: 'var(--success)' }}>
        <h3 style={{ color: 'var(--success)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Overall Extraction</h3>
        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--success)', margin: '0.5rem 0' }}>
          {overallPercentage}%
        </div>
        <p>{overallFetched} / {totalOverallMetrics} metrics found</p>
      </div>
    </div>
  );
}
