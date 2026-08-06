import React, { useState, useEffect } from 'react';
import { Settings, Save, RefreshCw, Box, ChevronDown, ChevronUp, Plus, Trash2 } from 'lucide-react';

export default function SkuUploader({ customSkuSpec, setCustomSkuSpec, backendUrl, onSkuNameChange }) {
  const [defaultFields, setDefaultFields] = useState([]);
  const [availableSkus, setAvailableSkus] = useState({});
  const [selectedSku, setSelectedSku] = useState('');
  
  // Array of { key: string, value: string } for the dynamic form
  const [formData, setFormData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    fetch(`${backendUrl}/fields`)
      .then(res => res.json())
      .then(data => {
        setDefaultFields(data.canonical_fields || []);
        
        const skus = data.available_skus || {};
        setAvailableSkus(skus);
        
        const skuNames = Object.keys(skus);
        const initialSku = skuNames.length > 0 ? skuNames[0] : 'Dynamic / Custom';
        setSelectedSku(initialSku);
        if (onSkuNameChange) onSkuNameChange(initialSku);

        const initialSpecs = skus[initialSku] || data.default_specs || {};
        
        // Convert object specs to array format
        const specsToUse = customSkuSpec || initialSpecs;
        let initialForm = [];
        if (Object.keys(specsToUse).length > 0) {
           initialForm = Object.keys(specsToUse).map(k => ({ key: k, value: specsToUse[k] }));
        } else {
           initialForm = (data.canonical_fields || []).map(f => ({ key: f, value: '' }));
        }
        
        setFormData(initialForm);
        setIsLoading(false);
        
        if (!customSkuSpec) {
           setCustomSkuSpec(specsToUse);
        }
      })
      .catch(err => {
        console.error("Failed to load fields", err);
        setIsLoading(false);
      });
  }, [backendUrl]);

  const handleSkuChange = (e) => {
    const skuName = e.target.value;
    setSelectedSku(skuName);
    if (onSkuNameChange) onSkuNameChange(skuName);
    
    if (skuName !== 'Dynamic / Custom' && availableSkus[skuName]) {
      const specs = availableSkus[skuName];
      setFormData(Object.keys(specs).map(k => ({ key: k, value: specs[k] })));
      setCustomSkuSpec(specs);
      setIsExpanded(false);
    } else {
      setIsExpanded(true);
    }
  };

  const handleFieldChange = (index, field, val) => {
    const newForm = [...formData];
    newForm[index][field] = val;
    setFormData(newForm);
  };

  const addField = () => {
    setFormData([...formData, { key: '', value: '' }]);
  };

  const removeField = (index) => {
    const newForm = [...formData];
    newForm.splice(index, 1);
    setFormData(newForm);
  };

  const handleApply = () => {
    const cleanData = {};
    formData.forEach(item => {
      if (item.key.trim() !== '') {
         // Only pass non-empty values
         if (item.value !== undefined && item.value !== null && item.value.trim() !== '') {
            cleanData[item.key.trim()] = item.value;
         }
      }
    });
    setCustomSkuSpec(cleanData);
    setIsExpanded(false);
  };
  
  const handleReset = () => {
     const resetForm = defaultFields.map(f => ({ key: f, value: '' }));
     setFormData(resetForm);
     setCustomSkuSpec({});
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
            SKU Configuration
          </h2>
          <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem', fontSize: '0.95rem', marginBottom: 0 }}>
            {selectedSku === 'Dynamic / Custom' 
              ? "Configure a custom set of specifications to cross-reference against extracted tire markings. You can add or remove parameters."
              : `Currently validating against Ground Truth configuration for ${selectedSku}.`
            }
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
              <optgroup label="Predefined SKUs">
                {Object.keys(availableSkus).map(sku => (
                  <option key={sku} value={sku}>{sku}</option>
                ))}
              </optgroup>
              <optgroup label="Custom">
                <option value="Dynamic / Custom">Dynamic / Custom Specification</option>
              </optgroup>
            </select>
          </div>

          {selectedSku === 'Dynamic / Custom' && (
            <button 
              className="btn" 
              onClick={() => setIsExpanded(!isExpanded)}
              style={{ padding: '0.75rem', height: '44px', width: '44px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              title={isExpanded ? 'Collapse Form' : 'Edit Specifications'}
            >
              {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
            </button>
          )}
        </div>
      </div>

      <div className={`collapsible-wrapper ${isExpanded && selectedSku === 'Dynamic / Custom' ? 'open' : ''}`}>
        <div className="collapsible-inner">
          <div style={{ paddingTop: '2rem' }}>
            <div style={{ 
              background: 'rgba(79, 138, 255, 0.1)', 
              borderLeft: '4px solid var(--primary)', 
              padding: '1rem 1.25rem', 
              borderRadius: '0 8px 8px 0',
              marginBottom: '2rem' 
            }}>
              <p style={{ margin: 0, fontSize: '0.95rem', color: 'var(--text)', lineHeight: '1.6' }}>
                Enter the <strong>Ground Truth</strong> expected values. These are used to cross-reference the AI extracted data. 
                Use commas to specify multiple acceptable variants. You can edit parameter names, delete them, or add new custom parameters at the bottom.
              </p>
            </div>

            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', 
              gap: '1.25rem',
              marginBottom: '1.5rem',
              maxHeight: '400px',
              overflowY: 'auto',
              paddingRight: '0.5rem'
            }}>
              {formData.map((item, index) => (
                <div key={index} className="sku-item-card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <input
                      type="text"
                      className="form-control"
                      value={item.key}
                      onChange={(e) => handleFieldChange(index, 'key', e.target.value)}
                      placeholder="Parameter Name"
                      style={{ padding: '0.25rem 0.5rem', fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-muted)', border: 'none', borderBottom: '1px solid var(--border)', borderRadius: '0', background: 'transparent' }}
                    />
                    <button onClick={() => removeField(index)} style={{ background: 'none', border: 'none', color: 'var(--error)', cursor: 'pointer', padding: '0.25rem' }}>
                       <Trash2 size={16} />
                    </button>
                  </div>
                  <input
                    type="text"
                    className="form-control"
                    value={item.value}
                    onChange={(e) => handleFieldChange(index, 'value', e.target.value)}
                    placeholder={`e.g. Variant 1...`}
                  />
                </div>
              ))}
            </div>

            <div style={{ marginBottom: '2.5rem' }}>
              <button className="btn" onClick={addField} style={{ fontSize: '0.85rem', padding: '0.5rem 1rem' }}>
                 <Plus size={16} /> Add Custom Parameter
              </button>
            </div>

            <div style={{ display: 'flex', gap: '1rem', paddingTop: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
              <button className="btn btn-primary" onClick={handleApply}>
                <Save size={18} /> Save & Apply Configuration
              </button>
              <button className="btn" onClick={handleReset} style={{ color: 'var(--text-muted)' }}>
                <RefreshCw size={18} /> Reset to Default Template
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
