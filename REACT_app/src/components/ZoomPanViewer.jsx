import React, { useRef, useState, useEffect } from 'react';

export default function ZoomPanViewer({ imageB64, onClose, title }) {
  const imgRef = useRef(null);
  const wrapRef = useRef(null);
  
  const [scale, setScale] = useState(1);
  const [origin, setOrigin] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [start, setStart] = useState({ x: 0, y: 0 });

  const handleWheel = (e) => {
    e.preventDefault();
    if (!wrapRef.current) return;
    const rect = wrapRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    const delta = e.deltaY < 0 ? 1.12 : 0.89;
    const newScale = Math.min(Math.max(scale * delta, 0.5), 8);
    
    const newOriginX = mouseX - ((mouseX - origin.x) / scale) * newScale;
    const newOriginY = mouseY - ((mouseY - origin.y) / scale) * newScale;
    
    setScale(newScale);
    setOrigin({ x: newOriginX, y: newOriginY });
  };

  useEffect(() => {
    const wrap = wrapRef.current;
    if (wrap) {
      wrap.addEventListener('wheel', handleWheel, { passive: false });
      return () => wrap.removeEventListener('wheel', handleWheel);
    }
  }, [scale, origin]);

  const handleMouseDown = (e) => {
    setIsDragging(true);
    setStart({ x: e.clientX - origin.x, y: e.clientY - origin.y });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setOrigin({ x: e.clientX - start.x, y: e.clientY - start.y });
  };

  const handleMouseUp = () => setIsDragging(false);

  const handleDoubleClick = () => {
    setScale(1);
    setOrigin({ x: 0, y: 0 });
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="btn" onClick={onClose}>Close</button>
        </div>
        <div className="modal-body">
          <div 
            ref={wrapRef}
            style={{
              width: '100%', height: '560px', overflow: 'hidden', position: 'relative',
              background: '#111', borderRadius: '8px', cursor: isDragging ? 'grabbing' : 'grab',
              touchAction: 'none'
            }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onDoubleClick={handleDoubleClick}
          >
            <img 
              ref={imgRef}
              src={`data:image/png;base64,${imageB64}`} 
              style={{
                position: 'absolute', top: 0, left: 0, transformOrigin: '0 0',
                userSelect: 'none', WebkitUserDrag: 'none',
                transform: `translate(${origin.x}px, ${origin.y}px) scale(${scale})`
              }} 
              draggable="false"
              alt="preview"
            />
            <div style={{
              position: 'absolute', bottom: '8px', right: '8px', zIndex: 2,
              background: 'rgba(0,0,0,0.55)', color: '#fff', fontSize: '12px',
              padding: '4px 8px', borderRadius: '6px'
            }}>
              scroll = zoom | drag = pan | dbl-click = reset
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
