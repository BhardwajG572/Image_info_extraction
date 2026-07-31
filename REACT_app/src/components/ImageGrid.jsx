import React from 'react';
import { Search } from 'lucide-react';

export default function ImageGrid({ images, onPreview }) {
  if (!images || images.length === 0) return null;
  
  return (
    <div className="grid-3" style={{ marginTop: '1rem' }}>
      {images.map(img => (
        <div key={img.image_id} className="image-thumbnail">
          <img src={`data:image/png;base64,${img.image_b64 || img.b64}`} alt={img.filename} />
          <div style={{ padding: '0.5rem', background: 'rgba(0,0,0,0.4)', textAlign: 'center' }}>
            <button className="btn btn-primary" onClick={() => onPreview(img)} style={{ width: '100%', justifyContent: 'center' }}>
              <Search size={16} /> Preview
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
