import React, { useRef, useState } from 'react';
import { UploadCloud } from 'lucide-react';

export default function ImageUploader({ side, onUpload }) {
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onUpload(side, e.dataTransfer.files);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files.length > 0) {
      onUpload(side, e.target.files);
    }
  };

  return (
    <div className="card" style={{ padding: '1rem' }}>
      <h3 style={{ fontSize: '1rem', margin: '0 0 0.5rem 0' }}>{side === 'Top' ? '⬆️' : '⬇️'} {side} Side Upload</h3>
      <div 
        className={`uploader ${isDragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current.click()}
        style={{ padding: '0.75rem', minHeight: '80px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}
      >
        <UploadCloud className="uploader-icon" size={24} style={{ marginBottom: '0.25rem' }} />
        <p style={{ fontSize: '0.85rem', margin: 0, fontWeight: 500 }}>Click or drag to upload</p>
        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
          {side.toLowerCase()} side image
        </p>
        <input 
          ref={fileInputRef}
          type="file" 
          multiple 
          accept=".png,.jpg,.jpeg,.bmp,.webp" 
          onChange={handleChange} 
          style={{ display: 'none' }}
        />
      </div>
    </div>
  );
}
