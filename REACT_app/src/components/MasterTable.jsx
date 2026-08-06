import React, { useState } from 'react';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { Download } from 'lucide-react';
import Statistics from './Statistics';

export default function MasterTable({ report }) {
  const [tweaks, setTweaks] = useState({});

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

  const handleTweak = (rowIndex, col, newValue) => {
    setTweaks(prev => ({
      ...prev,
      [`${rowIndex}-${col}`]: newValue
    }));
  };

  const statusOptions = ['OK', 'NF'];
  const columns = Object.keys(report[0]);

  const tweakedReport = report.map((row, i) => {
    let newRow = { ...row };
    columns.forEach(col => {
      let tweakKey = `${i}-${col}`;
      if (tweaks.hasOwnProperty(tweakKey)) {
        newRow[col] = tweaks[tweakKey];
      }
    });
    return newRow;
  });

  const handleDownloadPDF = () => {
    const doc = new jsPDF('landscape');
    
    doc.setFontSize(18);
    doc.text('Master Compliance Report', 14, 22);
    
    doc.setFontSize(11);
    doc.setTextColor(100);
    doc.text(`Generated on ${new Date().toLocaleString()}`, 14, 30);
    
    const tableRows = [];

    report.forEach((row, i) => {
      const rowData = [];
      columns.forEach(col => {
        let originalVal = row[col];
        let isStatusCol = col === 'Mould_Top' || col === 'Mould_Bottom';
        let tweakKey = `${i}-${col}`;
        
        let hasTweak = tweaks.hasOwnProperty(tweakKey) && tweaks[tweakKey] !== originalVal;
        let currentVal = tweaks.hasOwnProperty(tweakKey) ? tweaks[tweakKey] : originalVal;

        if (isStatusCol && hasTweak) {
          rowData.push(`${currentVal} *`);
        } else {
          rowData.push(currentVal !== undefined && currentVal !== null ? String(currentVal) : '');
        }
      });
      tableRows.push(rowData);
    });

    autoTable(doc, {
      head: [columns],
      body: tableRows,
      startY: 35,
      styles: { fontSize: 8, cellPadding: 2 },
      headStyles: { fillColor: [79, 138, 255] }
    });

    doc.save('master_compliance_report.pdf');
  };

  return (
    <div>
      <Statistics report={tweakedReport} />
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
        <button className="btn btn-primary" onClick={handleDownloadPDF} style={{ padding: '0.5rem 1rem' }}>
          <Download size={16} /> Download PDF
        </button>
      </div>
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
                let originalVal = row[col];
                let isStatusCol = col === 'Mould_Top' || col === 'Mould_Bottom';
                let tweakKey = `${i}-${col}`;
                
                let hasTweak = tweaks.hasOwnProperty(tweakKey) && tweaks[tweakKey] !== originalVal;
                let currentVal = tweaks.hasOwnProperty(tweakKey) ? tweaks[tweakKey] : originalVal;

                let optionsToRender = statusOptions.includes(originalVal) 
                  ? statusOptions 
                  : Array.from(new Set([originalVal, ...statusOptions]));

                return (
                  <td key={col}>
                    {isStatusCol ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <select
                          value={currentVal}
                          onChange={(e) => handleTweak(i, col, e.target.value)}
                          className={`status-badge ${getStatusClass(currentVal)}`}
                          style={{
                            border: '1px solid transparent',
                            outline: 'none',
                            cursor: 'pointer',
                            appearance: 'none',
                            paddingRight: '1.25rem',
                            backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E")`,
                            backgroundRepeat: 'no-repeat',
                            backgroundPosition: 'right 0.25rem center',
                            fontFamily: 'inherit'
                          }}
                          title="Manually override status"
                        >
                          {optionsToRender.map(opt => (
                            <option key={opt} value={opt} style={{ background: 'var(--surface)', color: 'var(--text)' }}>
                              {opt}
                            </option>
                          ))}
                        </select>
                        {hasTweak && (
                          <span 
                            style={{ color: 'var(--primary)', fontWeight: 'bold', fontSize: '1.2rem', lineHeight: '1' }} 
                            title="Manually verified/tweaked by human"
                          >
                            *
                          </span>
                        )}
                      </div>
                    ) : (
                      currentVal
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    </div>
  );
}
