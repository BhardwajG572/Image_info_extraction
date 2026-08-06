import React, { useState, useEffect } from 'react';
import { Settings, Save, RefreshCw, Box, ChevronDown, ChevronUp } from 'lucide-react';

export default function SkuUploader({ customSkuSpec, setCustomSkuSpec, backendUrl, onSkuNameChange }) {
  const [fields, setFields] = useState([]);
  const [defaultSpecs, setDefaultSpecs] = useState({});
  const [availableSkus, setAvailableSkus] = useState({});
  const [selectedSku, setSelectedSku] = useState('');
  const [formData, setFormData] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    fetch(`${backendUrl}/fields`)
      .then(res => res.json())
      .then(data => {
        setFields(data.canonical_fields || []);
        setDefaultSpecs(data.default_specs || {});
        
        const skus = data.available_skus || {};
        setAvailableSkus(skus);
        
        const skuNames = Object.keys(skus);
        const initialSku = skuNames.length > 0 ? skuNames[0] : 'Dynamic / Custom';
        setSelectedSku(initialSku);
        if (onSkuNameChange) onSkuNameChange(initialSku);

        const initialSpecs = skus[initialSku] || data.default_specs || {};
        // Initialize form with defaults if custom specs haven't been set yet
        setFormData(customSkuSpec || initialSpecs);
        setIsLoading(false);
        // Automatically apply the default configuration initially so it works even without changes
        if (!customSkuSpec) {
           setCustomSkuSpec(initialSpecs);
        }
      })
      .catch(err => {
        console.error("Failed to load fields", err);
        setIsLoading(false);
      });
  }, [backendUrl]); // Removed customSkuSpec dependency to prevent loop

  const handleSkuChange = (e) => {
    const skuName = e.target.value;
    setSelectedSku(skuName);
    if (onSkuNameChange) onSkuNameChange(skuName);
    
    if (skuName !== 'Dynamic / Custom' && availableSkus[skuName]) {
      setFormData(availableSkus[skuName]);
      setCustomSkuSpec(availableSkus[skuName]);
      setIsExpanded(false);
    } else {
      setIsExpanded(true); // Auto expand when switching to dynamic
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleApply = () => {
    // Only pass non-empty fields to avoid strict LLM matching on empty strings
    const cleanData = {};
    for (const key of Object.keys(formData)) {
      if (formData[key] !== undefined && formData[key] !== null && formData[key].toString().trim() !== '') {
        cleanData[key] = formData[key];
      }
    }
    setCustomSkuSpec(cleanData);
    setIsExpanded(false); // Collapse on save
  };
  
  const handleReset = () => {
     setFormData({});
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
              ? "Configure a custom set of specifications to cross-reference against extracted tire markings."
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
                Use commas to specify multiple acceptable variants (e.g. <code>APTERRA CROSS, AP TERRA CROSS</code>). 
                Leave fields blank to ignore them.
              </p>
            </div>

            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', 
              gap: '1.25rem',
              marginBottom: '2.5rem'
            }}>
              {fields.map(field => (
                <div key={field} className="sku-item-card">
                  <label className="form-label">{field}</label>
                  <input
                    type="text"
                    className="form-control"
                    value={formData[field] || ''}
                    onChange={(e) => handleChange(field, e.target.value)}
                    placeholder={`e.g. Variant 1...`}
                  />
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', gap: '1rem', paddingTop: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
              <button className="btn btn-primary" onClick={handleApply}>
                <Save size={18} /> Save & Apply Configuration
              </button>
              <button className="btn" onClick={handleReset} style={{ color: 'var(--text-muted)' }}>
                <RefreshCw size={18} /> Clear All Fields
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
