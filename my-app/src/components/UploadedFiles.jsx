import React from 'react';

function UploadedFiles({ files, onRemoveFile }) {
  if (!files || files.length === 0) {
    return null;
  }

  return (
    <div className="uploaded-files-container">
      <h3 className="uploaded-files-title">Uploaded Files</h3>
      <ul className="uploaded-files-list">
        {files.map((file, index) => (
          <li key={index} className="uploaded-file-item">
            <div className="file-info">
              <span className="file-icon">📄</span>
              <span className="file-name">{file.name}</span>
              <span className="file-size">({(file.size / 1024).toFixed(2)} KB)</span>
            </div>
            <button 
              className="remove-file-btn" 
              onClick={() => onRemoveFile(index)}
              aria-label="Remove file"
            >
              ×
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default UploadedFiles;
