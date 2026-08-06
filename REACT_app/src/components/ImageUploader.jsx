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
    <div className="card">
      <h3>{side === 'Top' ? '⬆️' : '⬇️'} {side} Side Upload</h3>
      <div 
        className={`uploader ${isDragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current.click()}
      >
        <UploadCloud className="uploader-icon" size={32} />
        <p style={{ fontSize: '0.9rem', margin: 0 }}>Click or drag to upload {side.toLowerCase()}-side images</p>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
          Supports: PNG, JPG, JPEG, BMP, WEBP
        </p>
        <input 
          ref={fileInputRef}
          type="file" 
          multiple 
          accept=".png,.jpg,.jpeg,.bmp,.webp" 
          onChange={handleChange} 
        />
      </div>
    </div>
  );
}
