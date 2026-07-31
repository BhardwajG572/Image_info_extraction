import React from 'react';

export default function MasterTable({ report }) {
  if (!report || report.length === 0) {
    return <div className="card" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No data found to populate the compliance table.</div>;
  }

  const getStatusClass = (status) => {
    switch (status) {
      case 'OK': return 'status-ok';
      case 'NF': return 'status-nf';
      case 'Mismatch': return 'status-mismatch';
      case 'Wrong Side': return 'status-wrong-side';
      case 'Discrepancy': return 'status-discrepancy';
      default: return '';
    }
  };

  const columns = Object.keys(report[0]);

  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            {columns.map(col => <th key={col}>{col}</th>)}
          </tr>
        </thead>
        <tbody>
          {report.map((row, i) => (
            <tr key={i}>
              {columns.map(col => {
                let val = row[col];
                let isStatusCol = col === 'Mould_Top' || col === 'Mould_Bottom';
                return (
                  <td key={col}>
                    {isStatusCol ? (
                      <span className={`status-badge ${getStatusClass(val)}`}>{val}</span>
                    ) : (
                      val
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
