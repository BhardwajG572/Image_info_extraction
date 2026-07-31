import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

export default function ExtractionResults({ side, rawImages, preprocessedImages, extractions }) {
  if (!preprocessedImages || preprocessedImages.length === 0) return null;

  return (
    <div style={{ marginBottom: '2rem' }}>
      <h3>{side === 'Top' ? '⬆️' : '⬇️'} {side} Side Results</h3>
      <div className="grid-3">
        {preprocessedImages.map(img => {
          const result = extractions[img.image_id];
          const rawImg = rawImages.find(r => r.image_id === img.image_id);
          return (
            <div key={img.image_id} className="card">
              <h4 style={{ fontSize: '1rem', wordBreak: 'break-all', marginBottom: '1rem' }}>[{side}] {img.filename}</h4>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '1rem' }}>
                {rawImg && (
                  <div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Original</div>
                    <img src={`data:image/png;base64,${rawImg.image_b64 || rawImg.b64}`} alt="Original" style={{ width: '100%', height: '120px', objectFit: 'cover', borderRadius: '4px', border: '1px solid var(--border)' }} />
                  </div>
                )}
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Preprocessed</div>
                  <img src={`data:image/png;base64,${img.image_b64 || img.b64}`} alt="Preprocessed" style={{ width: '100%', height: '120px', objectFit: 'cover', borderRadius: '4px', border: '1px solid var(--border)' }} />
                </div>
              </div>

              {result && result.parsed ? (
                <>
                  <div className="json-viewer">
                    {JSON.stringify(result.parsed, null, 2)}
                  </div>
                  {result.parsed.extracted_text && (
                    <RawTextExpander text={result.parsed.extracted_text} />
                  )}
                </>
              ) : result && result.error ? (
                <div style={{ color: 'var(--error)' }}>Error: {result.error}</div>
              ) : (
                <div style={{ color: 'var(--text-muted)' }}>Pending extraction...</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function RawTextExpander({ text }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div style={{ marginTop: '1rem', borderTop: '1px solid var(--border)', paddingTop: '1rem' }}>
      <button 
        className="btn" 
        style={{ width: '100%', justifyContent: 'space-between' }}
        onClick={() => setExpanded(!expanded)}
      >
        Raw Text Lines {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>
      {expanded && (
        <div className="json-viewer" style={{ marginTop: '0.5rem' }}>
          {text.map((line, i) => <div key={i}>{line}</div>)}
        </div>
      )}
    </div>
  );
}
