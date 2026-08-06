import React, { useState } from 'react';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { Download } from 'lucide-react';
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

export default function MasterTable({ report }) {
  const [tweaks, setTweaks] = useState({});
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
        ['Material Code', 'Description', 'Rev.', 'Date', 'GT Code', 'GT Iden.', 'GT wgt.', 'Plant'],
        ['RLGIW0APC3AH2', '215/60 R17 APTERRA CROSS', '1', '-', 'GT8048', 'WHITE', '10.015+- 0.3 KG', '1007-Apollo Chennai'],
        [{ content: '13 Digit Code', colSpan: 2, styles: { fontStyle: 'bold' } }, { content: digitCode || '-', colSpan: 6 }]
      ],
      theme: 'grid',
      styles: { fontSize: 8, cellPadding: 2, lineColor: [0, 0, 0], lineWidth: 0.1 },
      headStyles: { fillColor: [240, 240, 240], textColor: [0, 0, 0] }
    });

    const tableRows = [];

    report.forEach((row, i) => {
      let originalTop = row['Mould_Top'];
      let originalBot = row['Mould_Bottom'];
      let tweakTopKey = `${i}-Mould_Top`;
      let tweakBotKey = `${i}-Mould_Bottom`;
      
      let currentTop = tweaks.hasOwnProperty(tweakTopKey) ? tweaks[tweakTopKey] : originalTop;
      let currentBot = tweaks.hasOwnProperty(tweakBotKey) ? tweaks[tweakBotKey] : originalBot;
      
      let hasTweakTop = tweaks.hasOwnProperty(tweakTopKey) && tweaks[tweakTopKey] !== originalTop;
      let hasTweakBot = tweaks.hasOwnProperty(tweakBotKey) && tweaks[tweakBotKey] !== originalBot;

      tableRows.push([
        row['Parameters'] || row['Parameter'] || '',
        '-',
        row['Location Requirement'] || row['Location'] || '',
        row['Specification'] || '',
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
    doc.addPage('a4', 'portrait');
    doc.setFontSize(18);
    doc.setTextColor(0);
    doc.text('Curing RC - FIRST PRODUCT CHECK CARD', 14, 22);
    doc.setFontSize(14);
    doc.text('CURING PRESS STEPUP VERIFICATION', 14, 30);
    
    autoTable(doc, {
      startY: 35,
      head: [['Parameters', 'UOM', 'Tol', 'Specification', 'Mould Shop', 'Engg', 'Quality']],
      body: PAGE_2_STEPUP_DATA.map(row => [...row, '', '', '']), // Pad empty cols
      theme: 'grid',
      styles: { fontSize: 8, cellPadding: 2, lineColor: [0, 0, 0], lineWidth: 0.1 },
      headStyles: { fillColor: [240, 240, 240], textColor: [0, 0, 0], halign: 'center' }
    });

    autoTable(doc, {
      startY: doc.lastAutoTable.finalY + 10,
      head: [['Parameter', 'Points to be verified', 'Observation']],
      body: PAGE_2_POINTS_DATA.map(row => [...row, '']), // Pad empty observation
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
        {/* Top Header Block */}
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
                 <td>RLGIW0APC3AH2</td>
                 <td>215/60 R17 APTERRA CROSS</td>
                 <td>1</td>
                 <td>-</td>
                 <td>GT8048</td>
                 <td>WHITE</td>
                 <td>10.015+- 0.3 KG</td>
                 <td>1007-Apollo Chennai</td>
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

        {/* Main Data Table */}
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
              {report.map((row, i) => {
                const param = row['Parameters'] || row['Parameter'] || '';
                const location = row['Location Requirement'] || row['Location'] || '';
                const spec = row['Specification'] || '';
                
                // Extract tweaks
                const originalTop = row['Mould_Top'];
                const originalBot = row['Mould_Bottom'];
                
                const currentTop = tweaks.hasOwnProperty(`${i}-Mould_Top`) ? tweaks[`${i}-Mould_Top`] : originalTop;
                const currentBot = tweaks.hasOwnProperty(`${i}-Mould_Bottom`) ? tweaks[`${i}-Mould_Bottom`] : originalBot;
                
                const hasTweakTop = tweaks.hasOwnProperty(`${i}-Mould_Top`) && tweaks[`${i}-Mould_Top`] !== originalTop;
                const hasTweakBot = tweaks.hasOwnProperty(`${i}-Mould_Bottom`) && tweaks[`${i}-Mould_Bottom`] !== originalBot;

                let optionsTop = statusOptions.includes(originalTop) ? statusOptions : Array.from(new Set([originalTop, ...statusOptions]));
                let optionsBot = statusOptions.includes(originalBot) ? statusOptions : Array.from(new Set([originalBot, ...statusOptions]));

                return (
                  <tr key={i}>
                    <td style={{ fontWeight: '600' }}>{param}</td>
                    <td>-</td>
                    <td>{location}</td>
                    <td>{spec}</td>
                    
                    {/* MOULD SHOP - TOP */}
                    <td style={{ textAlign: 'center', padding: '0.25rem' }}>
                      {currentTop ? (
                       <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.25rem' }}>
                         <select
                            value={currentTop}
                            onChange={(e) => handleTweak(i, 'Mould_Top', e.target.value)}
                            className={`status-badge ${getStatusClass(currentTop)}`}
                            style={{
                              border: '1px solid transparent',
                              outline: 'none',
                              cursor: 'pointer',
                              appearance: 'none',
                              paddingRight: '1rem',
                              backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E")`,
                              backgroundRepeat: 'no-repeat',
                              backgroundPosition: 'right center',
                              fontFamily: 'inherit',
                              margin: 0
                            }}
                            title="Manually override status"
                          >
                            {optionsTop.map(opt => (
                              <option key={opt} value={opt} style={{ background: 'var(--surface)', color: 'var(--text)' }}>
                                {opt}
                              </option>
                            ))}
                          </select>
                          {hasTweakTop && (
                            <span style={{ color: 'var(--primary)', fontWeight: 'bold' }}>*</span>
                          )}
                       </div>
                      ) : null}
                    </td>
                    
                    {/* MOULD SHOP - BOTTOM */}
                    <td style={{ textAlign: 'center', padding: '0.25rem' }}>
                      {currentBot ? (
                       <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.25rem' }}>
                         <select
                            value={currentBot}
                            onChange={(e) => handleTweak(i, 'Mould_Bottom', e.target.value)}
                            className={`status-badge ${getStatusClass(currentBot)}`}
                            style={{
                              border: '1px solid transparent',
                              outline: 'none',
                              cursor: 'pointer',
                              appearance: 'none',
                              paddingRight: '1rem',
                              backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E")`,
                              backgroundRepeat: 'no-repeat',
                              backgroundPosition: 'right center',
                              fontFamily: 'inherit',
                              margin: 0
                            }}
                            title="Manually override status"
                          >
                            {optionsBot.map(opt => (
                              <option key={opt} value={opt} style={{ background: 'var(--surface)', color: 'var(--text)' }}>
                                {opt}
                              </option>
                            ))}
                          </select>
                          {hasTweakBot && (
                            <span style={{ color: 'var(--primary)', fontWeight: 'bold' }}>*</span>
                          )}
                       </div>
                      ) : null}
                    </td>
                    
                    {/* QUALITY - TOP */}
                    <td></td>
                    {/* QUALITY - BOTTOM */}
                    <td></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* --- PAGE 2 DATA --- */}
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
