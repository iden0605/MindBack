import React, { useState } from 'react';
import FileUpload from './FileUpload';

function Sidebar({
  uploadedFiles,
  handleFilesUpdate,
  onUploadCompleteAndProcess
}) {
  const [showUploadModal, setShowUploadModal] = useState(false);

  const groupFilesBySourceType = (files) => {
    if (!files) return {};
    return files.reduce((acc, file) => {
      const sourceType = file.sourceType || 'Unknown';
      if (!acc[sourceType]) {
        acc[sourceType] = [];
      }
      acc[sourceType].push(file);
      return acc;
    }, {});
  };

  const groupedFiles = groupFilesBySourceType(uploadedFiles);

  return (
    <div className="sidebar">

      <div className="uploaded-files-section">
        <h3>Processed Files</h3>
        {uploadedFiles.length > 0 ? (
          <ul className="uploaded-file-list">
            {uploadedFiles.map((file, index) => (
              <li key={file.name || index} className="uploaded-file-item">
                <span className="file-icon">📄</span>
                <span className="file-name" title={file.name}>{file.name}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="no-files-message">No processed files found.</p>
        )}
      </div>

      <div className="sidebar-section edit-data-section">
        <button
          className="btn-secondary action-btn edit-data-btn"
          onClick={() => setShowUploadModal(true)}
          style={{ width: '100%' }}
        >
          Uploaded Data
        </button>
      </div>

      {showUploadModal && (
        <FileUpload
          uploadedFiles={uploadedFiles}
          onFilesUpdate={handleFilesUpdate}
          onClose={() => setShowUploadModal(false)}
          onUploadCompleteAndProcess={onUploadCompleteAndProcess}
        />
      )}
    </div>
  );
}

export default Sidebar;
