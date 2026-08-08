import React, { useState, useEffect } from 'react';
import { Settings, Save, RefreshCw, Box, ChevronDown, ChevronUp, Plus, Trash2, X } from 'lucide-react';

export default function SkuUploader({ customSkuSpec, setCustomSkuSpec, backendUrl, onSkuNameChange }) {
  const [availableSkus, setAvailableSkus] = useState({});
  const [selectedSku, setSelectedSku] = useState('Dynamic / Custom');
  const [newSkuName, setNewSkuName] = useState('My Custom SKU');
  
  const [metadata, setMetadata] = useState({
    material_code: "",
    description: "",
    rev: "",
    date: "",
    gt_code: "",
    gt_iden: "",
    gt_wgt: "",
    plant: ""
  });
  
  const [parameters, setParameters] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);

    useEffect(() => {
    fetch(`${backendUrl}/skus`)
      .then(res => res.json())
      .then(data => {
        const skus = data.skus || {};
        setAvailableSkus(skus);
        
        const skuNames = Object.keys(skus);
        let initialSku = 'Dynamic / Custom';
        
        if (skuNames.length > 0) {
            initialSku = skuNames[0];
            setSelectedSku(initialSku);
            setNewSkuName(initialSku);
            if (onSkuNameChange) onSkuNameChange(initialSku);
            loadTemplate(skus[initialSku]);
        }
        
        setIsLoading(false);
      })
      .catch(err => {
        console.error("Failed to load SKUs", err);
        setIsLoading(false);
      });
  }, [backendUrl]);

  const loadTemplate = (template) => {
    if (!template) return;
    
    setMetadata(template.metadata || {
      material_code: "", description: "", rev: "", date: "",
      gt_code: "", gt_iden: "", gt_wgt: "", plant: ""
    });
    
    const loadedParams = (template.parameters || []).map(p => ({
        name: p.name || "",
        uom: p.uom || "",
        location: p.location || "Top & Bottom",
        specification: p.specification || "",
        variants: p.variants || [],
        variantInput: ""
    }));
    
    setParameters(loadedParams);
    
    // Convert back for the app state
    setCustomSkuSpec(template);
  };

  const handleSkuChange = (e) => {
    const skuName = e.target.value;
    setSelectedSku(skuName);
    if (onSkuNameChange) onSkuNameChange(skuName);
    
    if (skuName !== 'Dynamic / Custom' && availableSkus[skuName]) {
      const template = availableSkus[skuName];
      loadTemplate(template);
      setNewSkuName(skuName);
      setIsExpanded(false);
    } else {
      loadTemplate({
        metadata: {
          material_code: "", description: "", rev: "", date: "",
          gt_code: "", gt_iden: "", gt_wgt: "", plant: ""
        },
        parameters: []
      });
      setNewSkuName('');
      setIsExpanded(true);
    }
  };

  const handleMetadataChange = (field, val) => {
    setMetadata(prev => ({ ...prev, [field]: val }));
  };

  const handleParamChange = (index, field, val) => {
    const newParams = [...parameters];
    newParams[index][field] = val;
    setParameters(newParams);
  };

  const addParameter = () => {
    setParameters([...parameters, { name: '', uom: '', location: 'Top & Bottom', specification: '', variants: [], variantInput: '' }]);
  };

  const removeParameter = (index) => {
    const newParams = [...parameters];
    newParams.splice(index, 1);
    setParameters(newParams);
  };

  const handleApply = async () => {
    const nameToSave = newSkuName.trim();
    
    if (!nameToSave) {
        alert("Please enter a name for the SKU template.");
        return;
    }
    
    if (selectedSku === 'Dynamic / Custom' && availableSkus[nameToSave]) {
        alert("A template with this name already exists. Please choose a unique name for the new template.");
        return;
    }
    
    const cleanParams = parameters.filter(p => p.name.trim() !== '').map(p => ({
        name: p.name.trim(),
        uom: p.uom.trim(),
        location: p.location,
        specification: p.specification.trim(),
        variants: (p.variants || []).map(v => v.trim()).filter(v => v !== "")
    }));
    
    const newTemplate = {
        metadata: metadata,
        parameters: cleanParams
    };
    
    setCustomSkuSpec(newTemplate);
    if (onSkuNameChange) onSkuNameChange(nameToSave);
    
    // Save to backend
    try {
        await fetch(`${backendUrl}/skus`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: nameToSave,
                metadata: metadata,
                parameters: cleanParams
            })
        });
        
        // Optimistically update the dropdown options
        setAvailableSkus(prev => ({
            ...prev,
            [nameToSave]: newTemplate
        }));
        
        // Refresh available SKUs from backend without caching
        const res = await fetch(`${backendUrl}/skus`, { cache: 'no-store' });
        const data = await res.json();
        setAvailableSkus(data.skus || {});
        
        if (selectedSku !== nameToSave) {
            setSelectedSku(nameToSave);
        }
        
        setIsExpanded(false);
    } catch (err) {
        console.error("Failed to save SKU", err);
        alert("Failed to save SKU. Check console.");
    }
  };

  if (isLoading) {
    return (
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
          <RefreshCw size={18} className="loading-spinner" /> 
          <span>Loading specifications...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{ marginBottom: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1.5rem' }}>
        <div style={{ flex: '1 1 300px' }}>
          <h2 style={{ fontSize: '1.35rem', margin: 0, display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#fff' }}>
            <Box size={24} color="var(--primary)" /> 
            SKU Template Builder
          </h2>
          <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem', fontSize: '0.95rem', marginBottom: 0 }}>
            Configure metadata, parameter definitions, expected variants, and location constraints.
          </p>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flex: '1 1 300px', justifyContent: 'flex-end' }}>
          <div style={{ position: 'relative', flex: '1', maxWidth: '350px' }}>
            <select 
              value={selectedSku} 
              onChange={handleSkuChange}
              className="form-control"
              style={{ fontWeight: 500, fontSize: '0.95rem', boxShadow: 'var(--shadow)' }}
            >
              <optgroup label="Saved SKUs">
                {Object.keys(availableSkus).map(sku => (
                  <option key={sku} value={sku}>{sku}</option>
                ))}
              </optgroup>
              <optgroup label="Custom">
                <option value="Dynamic / Custom">Create New SKU...</option>
              </optgroup>
            </select>
          </div>

          <button 
            className="btn" 
            onClick={() => setIsExpanded(!isExpanded)}
            style={{ padding: '0.75rem', height: '44px', width: '44px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            title={isExpanded ? 'Collapse Form' : 'Edit Specifications'}
          >
            {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </button>
        </div>
      </div>

      <div className={`collapsible-wrapper ${isExpanded ? 'open' : ''}`}>
        <div className="collapsible-inner">
          <div style={{ paddingTop: '2rem' }}>
            
            {selectedSku === 'Dynamic / Custom' && (
              <div style={{ marginBottom: '1.5rem', background: 'rgba(79, 138, 255, 0.05)', padding: '1rem', borderRadius: 'var(--radius)', border: '1px solid rgba(79, 138, 255, 0.3)' }}>
                <h3 style={{ marginTop: 0, fontSize: '1rem', color: 'var(--primary)', marginBottom: '1rem' }}>How would you like to start?</h3>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
                  <button 
                    className="btn" 
                    onClick={() => loadTemplate({ metadata: { material_code: "", description: "", rev: "", date: "", gt_code: "", gt_iden: "", gt_wgt: "", plant: "" }, parameters: [] })}
                  >
                    Start with Empty Form
                  </button>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>— OR —</span>
                  <select 
                    className="form-control" 
                    style={{ flex: 1, minWidth: '200px' }}
                    onChange={(e) => {
                      if(e.target.value && availableSkus[e.target.value]) {
                        loadTemplate(availableSkus[e.target.value]);
                        e.target.value = "";
                      }
                    }}
                  >
                    <option value="">Clone from existing template...</option>
                    {Object.keys(availableSkus).map(sku => (
                      <option key={sku} value={sku}>{sku}</option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            <div style={{ marginBottom: '1.5rem', background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: 'var(--radius)', border: '1px solid var(--primary)' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--primary)', fontSize: '0.85rem', fontWeight: 600 }}>Save Template As:</label>
              <input 
                type="text" 
                className="form-control" 
                value={newSkuName} 
                onChange={(e) => setNewSkuName(e.target.value)} 
                placeholder="Enter a unique name for this SKU template"
                style={{ fontSize: '1.1rem', fontWeight: 600 }}
              />
              {selectedSku !== 'Dynamic / Custom' ? (
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem', marginBottom: 0 }}>
                  Tip: Change this name and click "Save & Apply" to clone your edits into a brand new template!
                </p>
              ) : (
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem', marginBottom: 0 }}>
                  This name must be unique. It will appear in the dropdown once saved.
                </p>
              )}
            </div>

            <div className="rc-container">
              <div className="rc-header-title">SKU Template Builder - Header Metadata</div>
              
              <div className="rc-table-wrapper" style={{ marginBottom: '2rem' }}>
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
                      <td>
                        <input type="text" className="form-control" title={metadata.material_code || '-'} value={metadata.material_code || ''} onChange={(e) => handleMetadataChange('material_code', e.target.value)} style={{ width: '100%', border: 'none', background: 'transparent', textAlign: 'center', padding: 0 }} placeholder="-" />
                      </td>
                      <td>
                        <input type="text" className="form-control" title={metadata.description || '-'} value={metadata.description || ''} onChange={(e) => handleMetadataChange('description', e.target.value)} style={{ width: '100%', border: 'none', background: 'transparent', textAlign: 'center', padding: 0 }} placeholder="-" />
                      </td>
                      <td>
                        <input type="text" className="form-control" title={metadata.rev || '-'} value={metadata.rev || ''} onChange={(e) => handleMetadataChange('rev', e.target.value)} style={{ width: '100%', border: 'none', background: 'transparent', textAlign: 'center', padding: 0 }} placeholder="-" />
                      </td>
                      <td>
                        <input type="text" className="form-control" title={metadata.date || '-'} value={metadata.date || ''} onChange={(e) => handleMetadataChange('date', e.target.value)} style={{ width: '100%', border: 'none', background: 'transparent', textAlign: 'center', padding: 0 }} placeholder="-" />
                      </td>
                      <td>
                        <input type="text" className="form-control" title={metadata.gt_code || '-'} value={metadata.gt_code || ''} onChange={(e) => handleMetadataChange('gt_code', e.target.value)} style={{ width: '100%', border: 'none', background: 'transparent', textAlign: 'center', padding: 0 }} placeholder="-" />
                      </td>
                      <td>
                        <input type="text" className="form-control" title={metadata.gt_iden || '-'} value={metadata.gt_iden || ''} onChange={(e) => handleMetadataChange('gt_iden', e.target.value)} style={{ width: '100%', border: 'none', background: 'transparent', textAlign: 'center', padding: 0 }} placeholder="-" />
                      </td>
                      <td>
                        <input type="text" className="form-control" title={metadata.gt_wgt || '-'} value={metadata.gt_wgt || ''} onChange={(e) => handleMetadataChange('gt_wgt', e.target.value)} style={{ width: '100%', border: 'none', background: 'transparent', textAlign: 'center', padding: 0 }} placeholder="-" />
                      </td>
                      <td>
                        <input type="text" className="form-control" title={metadata.plant || '-'} value={metadata.plant || ''} onChange={(e) => handleMetadataChange('plant', e.target.value)} style={{ width: '100%', border: 'none', background: 'transparent', textAlign: 'center', padding: 0 }} placeholder="-" />
                      </td>
                    </tr>
                    <tr>
                      <th colSpan={2} style={{ textAlign: 'left', paddingLeft: '0.5rem' }}>13 Digit Code</th>
                      <td colSpan={6} style={{ padding: '0.25rem' }}>
                         <div style={{ color: 'var(--text-muted)' }}>Filled during inspection</div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h3 style={{ fontSize: '1.1rem', margin: 0, color: 'var(--primary)' }}>Inspection Parameters</h3>
                  <button className="btn" onClick={addParameter} style={{ fontSize: '0.85rem', padding: '0.25rem 0.75rem' }}>
                     <Plus size={16} /> Add Parameter
                  </button>
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
                      <th rowSpan={2} style={{ width: '5%' }}></th>
                    </tr>
                    <tr>
                      <th style={{ width: '8.75%', textAlign: 'center' }}>TOP</th>
                      <th style={{ width: '8.75%', textAlign: 'center' }}>BOTTOM</th>
                      <th style={{ width: '8.75%', textAlign: 'center' }}>TOP</th>
                      <th style={{ width: '8.75%', textAlign: 'center' }}>BOTTOM</th>
                    </tr>
                  </thead>
                  <tbody>
                    {parameters.map((item, index) => (
                      <React.Fragment key={index}>
                        <tr>
                          <td title={item.name}>
                            <input
                              type="text"
                              className="form-control"
                              title={item.name}
                              value={item.name}
                              onChange={(e) => handleParamChange(index, 'name', e.target.value)}
                              placeholder="Parameter Name"
                              style={{ width: '100%', border: 'none', background: 'transparent', padding: '0', fontWeight: 'bold' }}
                            />
                          </td>
                          <td title={item.uom}>
                            <input
                              type="text"
                              className="form-control"
                              title={item.uom}
                              value={item.uom}
                              onChange={(e) => handleParamChange(index, 'uom', e.target.value)}
                              placeholder="-"
                              style={{ width: '100%', border: 'none', background: 'transparent', textAlign: 'center', padding: '0' }}
                            />
                          </td>
                          <td title={item.location}>
                            <select
                              className="form-control"
                              title={item.location}
                              value={item.location}
                              onChange={(e) => handleParamChange(index, 'location', e.target.value)}
                              style={{ width: '100%', border: 'none', background: 'transparent', padding: '0' }}
                            >
                                <option value="">-</option>
                                <option value="Top & Bottom">Top & Bottom</option>
                                <option value="Top">Top</option>
                                <option value="Bottom">Bottom</option>
                            </select>
                          </td>
                          <td title={item.specification}>
                            <input
                              type="text"
                              className="form-control"
                              title={item.specification}
                              value={item.specification}
                              onChange={(e) => handleParamChange(index, 'specification', e.target.value)}
                              placeholder="Specification"
                              style={{ width: '100%', border: 'none', background: 'transparent', padding: '0' }}
                            />
                          </td>
                          <td></td>
                          <td></td>
                          <td></td>
                          <td></td>
                          <td style={{ textAlign: 'center' }}>
                            <div style={{ display: 'flex', gap: '0.25rem', justifyContent: 'center' }}>
                              <button onClick={() => {
                                  const newParams = [...parameters];
                                  newParams[index].expanded = !newParams[index].expanded;
                                  setParameters(newParams);
                              }} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--primary)' }}>
                                {item.expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                              </button>
                              <button onClick={() => removeParameter(index)} style={{ background: 'none', border: 'none', color: 'var(--error)', cursor: 'pointer' }}>
                                 <Trash2 size={16} />
                              </button>
                            </div>
                          </td>
                        </tr>
                        {item.expanded && (
                          <tr>
                            <td colSpan={9} style={{ background: 'rgba(0,0,0,0.1)', padding: '0.5rem 1rem' }}>
                               <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                  <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Allowed Variants (type and press Enter):</label>
                                  
                                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                                    {(item.variants || []).map((variant, vIdx) => (
                                      <div key={vIdx} style={{ display: 'flex', alignItems: 'center', background: 'var(--primary)', color: '#fff', padding: '0.2rem 0.6rem', borderRadius: '1rem', fontSize: '0.85rem', gap: '0.4rem' }}>
                                        <span>{variant}</span>
                                        <button onClick={() => {
                                          const newParams = [...parameters];
                                          newParams[index].variants = newParams[index].variants.filter((_, i) => i !== vIdx);
                                          setParameters(newParams);
                                        }} style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center', opacity: 0.8 }} title="Remove variant"><X size={14} /></button>
                                      </div>
                                    ))}
                                  </div>

                                  <input
                                    type="text"
                                    className="form-control"
                                    value={item.variantInput || ''}
                                    onChange={(e) => handleParamChange(index, 'variantInput', e.target.value)}
                                    onKeyDown={(e) => {
                                      if (e.key === 'Enter') {
                                        e.preventDefault();
                                        const val = (item.variantInput || '').trim();
                                        if (val && !(item.variants || []).includes(val)) {
                                          const newParams = [...parameters];
                                          newParams[index].variants = [...(newParams[index].variants || []), val];
                                          newParams[index].variantInput = '';
                                          setParameters(newParams);
                                        }
                                      }
                                    }}
                                    placeholder="Type a variant and press Enter..."
                                    style={{ flex: 1, padding: '0.4rem 0.6rem', marginTop: '0.25rem' }}
                                  />
                               </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    ))}
                    {parameters.length === 0 && (
                      <tr>
                        <td colSpan={9} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                           No parameters added. Click "Add Parameter" to start.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', paddingTop: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
              <button className="btn btn-primary" onClick={handleApply}>
                <Save size={18} /> Save & Apply Template
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
