import React from 'react';
import { Search } from 'lucide-react';

export default function ImageGrid({ images, onPreview }) {
  if (!images || images.length === 0) return null;
  
  return (
    <div style={{ 
      display: 'grid', 
      gridTemplateColumns: 'repeat(auto-fill, minmax(80px, 1fr))', 
      gap: '0.5rem', 
      marginTop: '0.5rem' 
    }}>
      {images.map(img => (
        <div key={img.image_id} className="image-thumbnail" style={{ height: '80px' }}>
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
