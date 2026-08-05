import React from 'react';
import { Search } from 'lucide-react';

export default function ImageGrid({ images, onPreview }) {
  if (!images || images.length === 0) return null;
  
  return (
    <div style={{ 
      display: 'grid', 
      gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', 
      gap: '1rem', 
      marginTop: '1rem' 
    }}>
      {images.map(img => (
        <div key={img.image_id} className="image-thumbnail" style={{ height: '140px' }}>
          <img 
            src={`data:image/png;base64,${img.image_b64 || img.b64}`} 
            alt={img.filename} 
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
          <div className="image-overlay">
            <button className="btn btn-primary" onClick={() => onPreview(img)} style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}>
              <Search size={14} /> Preview
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
