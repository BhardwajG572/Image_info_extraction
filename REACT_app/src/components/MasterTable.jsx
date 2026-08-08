import React, { useState } from 'react';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { Download, Check, X } from 'lucide-react';
import Statistics from './Statistics';

const PAGE_2_STEPUP_DATA = [
  ["Press size / type", "", "", "46 & 52 \" BOM"],
  ["Shaping pressure", "", "", "-"],
  ["VCL CENTERING", "", "", "-"],
  ["VCL CHUCK EXP PADDLE DIST", "", "", "-"],
  ["VCL DOWN HEIGHT", "", "", "-"],
  ["Cycle Type", "", "", "-"],
  ["Cure Code Conv Press", "", "", "NTC 7A 11.50 E"],
  ["Cure Code", "", "", "-"],
  ["Ledge Width", "", "", "14 MM"],
  ["Item 1- BOM/Hyd", "", "", "EX1189-17\" #1"],
  ["Item 2- BOM/Hyd", "", "", "CK938"],
  ["Item 3- BOM/Hyd", "", "", "CK938"],
  ["Item 4- BOM/Hyd", "", "", "CA938"],
  ["Item 5- Hyd", "", "", "CA938"],
  ["Item 6 - BOM/ 6 Hyd", "", "", "EX1189-17\" #1"],
  ["Mould Container Size", "", "", "PCNARC4"],
  ["Bladder code", "", "", "RP17/1 LC - 600"],
  ["Bladder Size", "", "", "-"],
  ["Bladder Life Ceiling", "", "", "-"],
  ["Bladder stacking height", "mm", "± 5", "510"],
  ["Bladder ring down height", "mm", "± 5", "310"],
  ["BLADDER DWG NO BOM/HYD", "", "", "-"],
  ["1st shaping pressure", "bar", "± 0.05", "0.45"],
  ["2nd shaping pressure", "bar", "± 0.05", "0.55"],
  ["3rd shaping pressure", "bar", "± 0.05", "0.65"],
  ["Closing Force", "", "+ 5000/- 0", "217000"],
  ["Open Shaping", "", "", "-"],
  ["Post Cure Hanging", "", "", "REQUIRED"],
  ["Open shaping time", "", "", "-"],
  ["Open shaping pressure", "", "", "-"],
  ["Pause time", "", "", "-"],
  ["Pause height", "", "", "-"],
  ["Press Squeeze Pressure HYD", "", "", "-"],
  ["Pci Rim Dwg No", "", "", "-"],
  ["PCI Rim width", "mm", "", "-"],
  ["PCI pressure", "bar", "", "-"],
  ["PCI time", "min", "", "-"]
];

const PAGE_2_POINTS_DATA = [
  ["Tread", "Sipe bend / missing"],
  ["Tread", "Tread Chipping"],
  ["Cured Tyre", "Step OFF shoulder, Lateral and Radial"],
  ["Cured Tyre", "Flash Shoulder, Segment, Slug & Bead"],
  ["Cured Tyre", "Vent Condition"],
  ["Cured Tyre", "Mould condition (Free from dirty)"],
  ["Cured Tyre", "Tyre free from Visual defects as per OSC"],
  ["Curing Mould", "Check the mould number in tyre vs WCS"],
  ["FTC Barcode", ""],
  ["Air Leak test result", "OK / Not OK"],
  ["Remarks on FTC", ""],
  ["Others (If any)", ""]
];

export default function MasterTable({ report, metadata = {} }) {
  const [tweaks, setTweaks] = useState({});
  const [pendingTweaks, setPendingTweaks] = useState({});
  const [digitCode, setDigitCode] = useState('');

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

  const handlePendingChange = (rowIndex, col, newValue) => {
    setPendingTweaks(prev => ({
      ...prev,
      [`${rowIndex}-${col}`]: newValue
    }));
  };

  const commitTweak = (rowIndex, col) => {
    const key = `${rowIndex}-${col}`;
    if (pendingTweaks.hasOwnProperty(key)) {
      setTweaks(prev => ({
        ...prev,
        [key]: pendingTweaks[key]
      }));
      setPendingTweaks(prev => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
    }
  };

  const cancelTweak = (rowIndex, col) => {
    const key = `${rowIndex}-${col}`;
    setPendingTweaks(prev => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
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
    
    // ================= PAGE 1 =================
    doc.setFontSize(18);
    doc.text('Curing RC - FIRST PRODUCT CHECK CARD', 14, 22);
    
    doc.setFontSize(11);
    doc.setTextColor(100);
    doc.text(`Generated on ${new Date().toLocaleString()}`, 14, 30);
    
    // Header Info Table for PDF
    autoTable(doc, {
      startY: 35,
      head: [
        [{ content: 'Press number', colSpan: 2 }, { content: 'Mould Number', colSpan: 3 }, { content: 'Container Number', colSpan: 3 }]
      ],
      body: [
        ['', '', '', '', '', '', '', ''],
      ],
      theme: 'grid',
      styles: { fontSize: 8, cellPadding: 2, lineColor: [0, 0, 0], lineWidth: 0.1 },
      headStyles: { fillColor: [240, 240, 240], textColor: [0, 0, 0] },
      bodyStyles: { minCellHeight: 15 }
    });

    autoTable(doc, {
      startY: doc.lastAutoTable.finalY,
      head: [['Material Code', 'Description', 'Rev.', 'Date', 'GT Code', 'GT Iden.', 'GT wgt.', 'Plant']],
      body: [
        [
          metadata?.material_code || '-',
          metadata?.description || '-',
          metadata?.rev || '-',
          metadata?.date || '-',
          metadata?.gt_code || '-',
          metadata?.gt_iden || '-',
          metadata?.gt_wgt || '-',
          metadata?.plant || '-'
        ],
        [
          { content: '13 Digit Code', colSpan: 2, styles: { fontStyle: 'bold', fillColor: [240, 240, 240] } },
          { content: digitCode || '', colSpan: 6 }
        ]
      ],
      theme: 'grid',
      styles: { fontSize: 8, cellPadding: 2, lineColor: [0, 0, 0], lineWidth: 0.1 },
      headStyles: { fillColor: [240, 240, 240], textColor: [0, 0, 0], halign: 'center' }
    });

    const tableRows = [];

    tweakedReport.forEach((row, i) => {
      const hasTweakTop = tweaks.hasOwnProperty(`${i}-Mould_Top`);
      const hasTweakBot = tweaks.hasOwnProperty(`${i}-Mould_Bottom`);
      
      const currentTop = row.Mould_Top === 'Mismatch' ? 'NF' : row.Mould_Top;
      const currentBot = row.Mould_Bottom === 'Mismatch' ? 'NF' : row.Mould_Bottom;

      tableRows.push([
        row.Parameters || '',
        row.UOM || '-',
        row['Location Requirement'] || '',
        row.Specification || '',
        currentTop ? `${currentTop}${hasTweakTop ? ' *' : ''}` : '',
        currentBot ? `${currentBot}${hasTweakBot ? ' *' : ''}` : '',
        '',
        ''
      ]);
    });

    autoTable(doc, {
      head: [
        [
          { content: 'Parameters', rowSpan: 2 },
          { content: 'UOM', rowSpan: 2 },
          { content: 'Location', rowSpan: 2 },
          { content: 'Specification', rowSpan: 2 },
          { content: 'MOULD SHOP', colSpan: 2 },
          { content: 'QUALITY', colSpan: 2 }
        ],
        ['TOP', 'BOTTOM', 'TOP', 'BOTTOM']
      ],
      body: tableRows,
      startY: doc.lastAutoTable.finalY + 10,
      theme: 'grid',
      styles: { fontSize: 8, cellPadding: 2, lineColor: [0, 0, 0], lineWidth: 0.1 },
      headStyles: { fillColor: [240, 240, 240], textColor: [0, 0, 0], halign: 'center', valign: 'middle' },
      columnStyles: {
        4: { halign: 'center' },
        5: { halign: 'center' }
      }
    });

    // ================= PAGE 2 =================
    doc.addPage('a4', 'landscape');
    doc.setFontSize(18);
    doc.setTextColor(0);
    doc.text('Curing RC - FIRST PRODUCT CHECK CARD', 14, 22);
    doc.setFontSize(14);
    doc.text('CURING PRESS STEPUP VERIFICATION', 14, 30);
    
    autoTable(doc, {
      startY: 35,
      head: [['Parameters', 'UOM', 'Tol', 'Specification', 'Mould Shop', 'Engg', 'Quality']],
      body: PAGE_2_STEPUP_DATA.map(row => [...row, '', '', '']),
      theme: 'grid',
      styles: { fontSize: 8, cellPadding: 2, lineColor: [0, 0, 0], lineWidth: 0.1 },
      headStyles: { fillColor: [240, 240, 240], textColor: [0, 0, 0], halign: 'center' }
    });

    autoTable(doc, {
      startY: doc.lastAutoTable.finalY + 10,
      head: [['Parameter', 'Points to be verified', 'Observation']],
      body: PAGE_2_POINTS_DATA.map(row => [...row, '']),
      theme: 'grid',
      styles: { fontSize: 8, cellPadding: 2, lineColor: [0, 0, 0], lineWidth: 0.1 },
      headStyles: { fillColor: [240, 240, 240], textColor: [0, 0, 0] }
    });

    autoTable(doc, {
      startY: doc.lastAutoTable.finalY + 10,
      head: [['Department', 'Mould Shop', 'Engineering', 'Quality']],
      body: [
        ['Date & Shift', '', '', ''],
        ['Name & Signature', '', '', '']
      ],
      theme: 'grid',
      styles: { fontSize: 8, cellPadding: 2, lineColor: [0, 0, 0], lineWidth: 0.1 },
      headStyles: { fillColor: [240, 240, 240], textColor: [0, 0, 0], halign: 'center' }
    });

    doc.save('Curing_RC_Check_Card.pdf');
  };

  return (
    <div>
      <Statistics report={tweakedReport} />
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
        <button className="btn btn-primary" onClick={handleDownloadPDF} style={{ padding: '0.5rem 1rem' }}>
          <Download size={16} /> Download PDF
        </button>
      </div>
      
      <div className="rc-container">
        <div className="rc-header-title">Curing RC - FIRST PRODUCT CHECK CARD</div>
        
        <div className="rc-table-wrapper" style={{ marginBottom: '1rem' }}>
           <table className="rc-table">
             <tbody>
               <tr>
                 <th colSpan={2} style={{ width: '25%' }}>Press number</th>
                 <th colSpan={3} style={{ width: '37.5%' }}>Mould Number</th>
                 <th colSpan={3} style={{ width: '37.5%' }}>Container Number</th>
               </tr>
               <tr>
                 <td colSpan={2}>&nbsp;</td>
                 <td colSpan={3}>&nbsp;</td>
                 <td colSpan={3}>&nbsp;</td>
               </tr>
               <tr>
                 <th>Material Code</th>
                 <th>Description</th>
                 <th>Rev.</th>
                 <th>Date</th>
                 <th>GT Code</th>
                 <th>GT Iden.</th>
                 <th>GT wgt.</th>
                 <th>Plant</th>
               </tr>
               <tr>
                 <td><div title={metadata?.material_code || '-'}>{metadata?.material_code || '-'}</div></td>
                 <td><div title={metadata?.description || '-'}>{metadata?.description || '-'}</div></td>
                 <td><div title={metadata?.rev || '-'}>{metadata?.rev || '-'}</div></td>
                 <td><div title={metadata?.date || '-'}>{metadata?.date || '-'}</div></td>
                 <td><div title={metadata?.gt_code || '-'}>{metadata?.gt_code || '-'}</div></td>
                 <td><div title={metadata?.gt_iden || '-'}>{metadata?.gt_iden || '-'}</div></td>
                 <td><div title={metadata?.gt_wgt || '-'}>{metadata?.gt_wgt || '-'}</div></td>
                 <td><div title={metadata?.plant || '-'}>{metadata?.plant || '-'}</div></td>
               </tr>
               <tr>
                 <th colSpan={2} style={{ textAlign: 'left', paddingLeft: '0.5rem' }}>13 Digit Code</th>
                 <td colSpan={6} style={{ padding: '0.25rem' }}>
                   <input
                     type="text"
                     value={digitCode}
                     onChange={(e) => setDigitCode(e.target.value)}
                     placeholder="Enter 13 Digit Code here..."
                     className="form-control"
                     style={{ width: '100%', border: 'none', background: 'transparent', textAlign: 'left' }}
                   />
                 </td>
               </tr>
             </tbody>
           </table>
        </div>

        <div className="rc-table-wrapper">
          <table className="rc-table">
            <thead>
              <tr>
                <th rowSpan={2} style={{ width: '25%' }}>Parameters</th>
                <th rowSpan={2} style={{ width: '5%' }}>UOM</th>
                <th rowSpan={2} style={{ width: '15%' }}>Location</th>
                <th rowSpan={2} style={{ width: '20%' }}>Specification</th>
                <th colSpan={2} style={{ textAlign: 'center' }}>MOULD SHOP</th>
                <th colSpan={2} style={{ textAlign: 'center' }}>QUALITY</th>
              </tr>
              <tr>
                <th style={{ width: '8.75%', textAlign: 'center' }}>TOP</th>
                <th style={{ width: '8.75%', textAlign: 'center' }}>BOTTOM</th>
                <th style={{ width: '8.75%', textAlign: 'center' }}>TOP</th>
                <th style={{ width: '8.75%', textAlign: 'center' }}>BOTTOM</th>
              </tr>
            </thead>
            <tbody>
              {tweakedReport.map((row, i) => {
                const keyTop = `${i}-Mould_Top`;
                const isPendingTop = pendingTweaks.hasOwnProperty(keyTop);
                const displayValTop = isPendingTop ? pendingTweaks[keyTop] : row.Mould_Top;
                const isMismatchTop = displayValTop === 'NF' || displayValTop === 'Mismatch';

                const keyBot = `${i}-Mould_Bottom`;
                const isPendingBot = pendingTweaks.hasOwnProperty(keyBot);
                const displayValBot = isPendingBot ? pendingTweaks[keyBot] : row.Mould_Bottom;
                const isMismatchBot = displayValBot === 'NF' || displayValBot === 'Mismatch';
                
                return (
                  <tr key={i}>
                    <td title={row.Parameters}>{row.Parameters}</td>
                    <td title={row.UOM || '-'}>{row.UOM || '-'}</td>
                    <td title={row['Location Requirement']}>{row['Location Requirement']}</td>
                    <td title={row.Specification}>{row.Specification}</td>
                    <td className={`status-cell ${getStatusClass(displayValTop)}`} title={displayValTop}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <select 
                          value={displayValTop} 
                          onChange={(e) => handlePendingChange(i, 'Mould_Top', e.target.value)}
                          className={`status-select ${isMismatchTop ? 'mismatch-text' : ''}`}
                        >
                          <option value={displayValTop}>{displayValTop}</option>
                          {statusOptions.filter(o => o !== displayValTop).map(opt => (
                            <option key={opt} value={opt}>{opt}</option>
                          ))}
                        </select>
                        {isPendingTop && (
                           <div style={{ display: 'flex', gap: '2px' }}>
                             <button onClick={() => commitTweak(i, 'Mould_Top')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--success)' }} title="Save Change"><Check size={16}/></button>
                             <button onClick={() => cancelTweak(i, 'Mould_Top')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--error)' }} title="Cancel"><X size={16}/></button>
                           </div>
                        )}
                        {!isPendingTop && tweaks.hasOwnProperty(keyTop) && <span className="tweak-indicator">*</span>}
                      </div>
                    </td>
                    <td className={`status-cell ${getStatusClass(displayValBot)}`} title={displayValBot}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <select 
                          value={displayValBot} 
                          onChange={(e) => handlePendingChange(i, 'Mould_Bottom', e.target.value)}
                          className={`status-select ${isMismatchBot ? 'mismatch-text' : ''}`}
                        >
                          <option value={displayValBot}>{displayValBot}</option>
                          {statusOptions.filter(o => o !== displayValBot).map(opt => (
                            <option key={opt} value={opt}>{opt}</option>
                          ))}
                        </select>
                        {isPendingBot && (
                           <div style={{ display: 'flex', gap: '2px' }}>
                             <button onClick={() => commitTweak(i, 'Mould_Bottom')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--success)' }} title="Save Change"><Check size={16}/></button>
                             <button onClick={() => cancelTweak(i, 'Mould_Bottom')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--error)' }} title="Cancel"><X size={16}/></button>
                           </div>
                        )}
                        {!isPendingBot && tweaks.hasOwnProperty(keyBot) && <span className="tweak-indicator">*</span>}
                      </div>
                    </td>
                    <td></td>
                    <td></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="rc-header-title" style={{ marginTop: '4rem', fontSize: '1.25rem' }}>CURING PRESS STEPUP VERIFICATION</div>
        <div className="rc-table-wrapper" style={{ marginBottom: '2rem' }}>
          <table className="rc-table">
            <thead>
              <tr>
                <th style={{ width: '25%' }}>Parameters</th>
                <th style={{ width: '5%' }}>UOM</th>
                <th style={{ width: '10%' }}>Tol</th>
                <th style={{ width: '20%' }}>Specification</th>
                <th style={{ width: '13%' }}>Mould Shop</th>
                <th style={{ width: '13%' }}>Engg</th>
                <th style={{ width: '14%' }}>Quality</th>
              </tr>
            </thead>
            <tbody>
              {PAGE_2_STEPUP_DATA.map((row, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: '500' }}>{row[0]}</td>
                  <td>{row[1]}</td>
                  <td>{row[2]}</td>
                  <td>{row[3]}</td>
                  <td></td>
                  <td></td>
                  <td></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="rc-table-wrapper" style={{ marginBottom: '2rem' }}>
          <table className="rc-table">
            <thead>
              <tr>
                <th style={{ width: '25%' }}>Parameter</th>
                <th style={{ width: '45%' }}>Points to be verified</th>
                <th style={{ width: '30%' }}>Observation</th>
              </tr>
            </thead>
            <tbody>
              {PAGE_2_POINTS_DATA.map((row, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: '500' }}>{row[0]}</td>
                  <td>{row[1]}</td>
                  <td></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="rc-table-wrapper">
          <table className="rc-table">
            <thead>
              <tr>
                <th style={{ width: '25%' }}>Department</th>
                <th style={{ width: '25%', textAlign: 'center' }}>Mould Shop</th>
                <th style={{ width: '25%', textAlign: 'center' }}>Engineering</th>
                <th style={{ width: '25%', textAlign: 'center' }}>Quality</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ fontWeight: '500', height: '3rem' }}>Date & Shift</td>
                <td></td>
                <td></td>
                <td></td>
              </tr>
              <tr>
                <td style={{ fontWeight: '500', height: '4rem' }}>Name & Signature</td>
                <td></td>
                <td></td>
                <td></td>
              </tr>
            </tbody>
          </table>
        </div>

      </div>
    </div>
  );
}
