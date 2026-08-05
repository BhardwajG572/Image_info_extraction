import React, { useState, useEffect } from 'react';
import ImageUploader from './components/ImageUploader';
import ImageGrid from './components/ImageGrid';
import ZoomPanViewer from './components/ZoomPanViewer';
import ExtractionResults from './components/ExtractionResults';
import MasterTable from './components/MasterTable';
import Statistics from './components/Statistics';
import SkuUploader from './components/SkuUploader';
import { Trash2, Cpu } from 'lucide-react';

const BACKEND_URL = 'http://127.0.0.1:8000';

function App() {
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  
  const [rawTopImages, setRawTopImages] = useState([]);
  const [preprocessedTopImages, setPreprocessedTopImages] = useState([]);
  
  const [rawBottomImages, setRawBottomImages] = useState([]);
  const [preprocessedBottomImages, setPreprocessedBottomImages] = useState([]);
  
  const [extractions, setExtractions] = useState({});
  const [mergeResult, setMergeResult] = useState(null);
  
  const [customSkuSpec, setCustomSkuSpec] = useState(null);
  
  const [previewTarget, setPreviewTarget] = useState(null); // { image_b64, title }
  
  const [isExtracting, setIsExtracting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressText, setProgressText] = useState('');

  useEffect(() => {
    fetch(`${BACKEND_URL}/models`)
      .then(res => res.json())
      .then(data => {
        setModels(Object.keys(data.models));
        setSelectedModel(data.default);
      })
      .catch(err => console.error("Failed to load models", err));
  }, []);

  const fileToBase64 = (file) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      // Remove data:image/png;base64, part
      const b64 = reader.result.split(',')[1];
      resolve(b64);
    };
    reader.onerror = error => reject(error);
  });

  const generateId = () => Math.random().toString(36).substring(2, 10);

  const handleUpload = async (side, files) => {
    const newImages = [];
    const existingNames = new Set(
      (side === 'Top' ? rawTopImages : rawBottomImages).map(img => img.filename)
    );

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (existingNames.has(file.name)) continue;
      
      const b64 = await fileToBase64(file);
      newImages.push({
        image_id: generateId(),
        filename: file.name,
        image_b64: b64,
        side
      });
    }

    if (newImages.length === 0) return;

    if (side === 'Top') setRawTopImages(prev => [...prev, ...newImages]);
    else setRawBottomImages(prev => [...prev, ...newImages]);

    // Preprocess immediately
    try {
      const res = await fetch(`${BACKEND_URL}/preprocess`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ images: newImages })
      });
      const data = await res.json();
      
      // Preserve filename in processed images
      const processed = data.results.map(r => {
        const orig = newImages.find(im => im.image_id === r.image_id);
        return { ...r, filename: orig?.filename };
      });
      
      if (side === 'Top') setPreprocessedTopImages(prev => [...prev, ...processed]);
      else setPreprocessedBottomImages(prev => [...prev, ...processed]);
    } catch (err) {
      console.error("Preprocessing failed", err);
      alert("Preprocessing failed. Ensure backend is running.");
    }
  };

  const handleClear = () => {
    setRawTopImages([]);
    setPreprocessedTopImages([]);
    setRawBottomImages([]);
    setPreprocessedBottomImages([]);
    setExtractions({});
    setMergeResult(null);
  };

  const handlePreview = (img) => {
    setPreviewTarget({
      image_b64: img.image_b64 || img.b64,
      title: `${img.side} Side: ${img.filename}`
    });
  };

  const handleExtract = async () => {
    const allPreprocessed = [...preprocessedTopImages, ...preprocessedBottomImages];
    if (allPreprocessed.length === 0) return;

    setIsExtracting(true);
    setProgress(0);
    setProgressText('Starting extraction...');
    
    const newExtractions = { ...extractions };
    const batchSize = 2;
    let processedCount = 0;

    for (let i = 0; i < allPreprocessed.length; i += batchSize) {
      const batch = allPreprocessed.slice(i, i + batchSize);
      try {
        const res = await fetch(`${BACKEND_URL}/extract_batch`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            images: batch.map(img => ({
              image_id: img.image_id,
              image_b64: img.image_b64,
              side: img.side,
              model_key: selectedModel
            }))
          })
        });
        const data = await res.json();
        
        data.results.forEach(item => {
          newExtractions[item.image_id] = item;
        });
      } catch (err) {
        console.error("Batch extraction error", err);
        batch.forEach(img => {
          newExtractions[img.image_id] = { error: err.toString() };
        });
      }

      processedCount += batch.length;
      setProgress(processedCount / allPreprocessed.length);
      setProgressText(`Processed ${processedCount}/${allPreprocessed.length} images`);
      setExtractions({ ...newExtractions });
    }

    setProgressText('Checking specifications...');
    
    // Merge Phase
    const validExtractions = [];
    Object.keys(newExtractions).forEach(iid => {
      const ext = newExtractions[iid];
      if (ext && ext.parsed) {
        const img = allPreprocessed.find(im => im.image_id === iid);
        if (img) {
          validExtractions.push({
            image_id: iid,
            side: img.side,
            parsed: ext.parsed
          });
        }
      }
    });

    if (validExtractions.length > 0) {
      try {
        const res = await fetch(`${BACKEND_URL}/merge`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            extractions: validExtractions,
            sku_specifications: customSkuSpec
          })
        });
        const data = await res.json();
        setMergeResult(data);
      } catch (err) {
        console.error("Merge failed", err);
        alert(`Compliance check failed: ${err.message}`);
      }
    }

    setIsExtracting(false);
  };

  const hasUploads = rawTopImages.length > 0 || rawBottomImages.length > 0;
  const allPreprocessed = [...preprocessedTopImages, ...preprocessedBottomImages];

  return (
    <div className="container">
      <div className="header">
        <h1>🛞 Vulcan Inspect</h1>
        <p>Every marking read, cross-checked, and verified — nothing guessed, nothing hidden.</p>
      </div>

      <section>
        <SkuUploader customSkuSpec={customSkuSpec} setCustomSkuSpec={setCustomSkuSpec} backendUrl={BACKEND_URL} />
      </section>

      <section>
        <h2>1. Upload Tire Images</h2>
        <div className="grid-2">
          <div>
            <ImageUploader side="Top" onUpload={handleUpload} />
            <ImageGrid images={rawTopImages} onPreview={handlePreview} />
          </div>
          <div>
            <ImageUploader side="Bottom" onUpload={handleUpload} />
            <ImageGrid images={rawBottomImages} onPreview={handlePreview} />
          </div>
        </div>

        {hasUploads ? (
          <div style={{ marginTop: '2rem', textAlign: 'center' }}>
            <button className="btn" onClick={handleClear}>
              <Trash2 size={18} /> Clear all uploads
            </button>
          </div>
        ) : (
          <div className="card" style={{ marginTop: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            Upload at least one image in either Top or Bottom side to begin.
          </div>
        )}
      </section>

      <div className="divider" />

      <section>
        <h2>2. Preprocessed Images (Strictly Flipped)</h2>
        {allPreprocessed.length > 0 ? (
          <div className="grid-2">
            <div>
              <h3>Preprocessed Top Side</h3>
              <ImageGrid images={preprocessedTopImages} onPreview={handlePreview} />
            </div>
            <div>
              <h3>Preprocessed Bottom Side</h3>
              <ImageGrid images={preprocessedBottomImages} onPreview={handlePreview} />
            </div>
          </div>
        ) : (
          <div className="card" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
            Upload images above to see the preprocessed versions here.
          </div>
        )}
      </section>

      <div className="divider" />

      <section>
        <h2>3. Run Extraction</h2>
        <div className="card" style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Model</label>
            <select 
              className="btn" 
              style={{ background: 'var(--surface)' }}
              value={selectedModel} 
              onChange={e => setSelectedModel(e.target.value)}
            >
              {models.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          
          <div style={{ flex: 1 }}>
             <button 
                className="btn btn-primary" 
                onClick={handleExtract} 
                disabled={isExtracting || allPreprocessed.length === 0}
                style={{ marginTop: '1.75rem' }}
             >
                <Cpu size={18} /> {isExtracting ? 'Processing...' : 'Extract Data From All Images'}
             </button>
          </div>
        </div>

        {isExtracting && (
          <div style={{ marginTop: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
              <span>{progressText}</span>
              <span>{Math.round(progress * 100)}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress * 100}%` }} />
            </div>
          </div>
        )}
      </section>

      <section>
        <h2>4. Master Table</h2>
        {mergeResult && mergeResult.compliance_report ? (
           <>
             <Statistics report={mergeResult.compliance_report} />
             <MasterTable report={mergeResult.compliance_report} />
           </>
        ) : (
          <div className="card" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
            Run extraction above to generate the compliance report.
          </div>
        )}
      </section>

      {previewTarget && (
        <ZoomPanViewer 
          imageB64={previewTarget.image_b64} 
          title={previewTarget.title}
          onClose={() => setPreviewTarget(null)} 
        />
      )}
    </div>
  );
}

export default App;
