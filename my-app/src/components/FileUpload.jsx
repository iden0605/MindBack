import React, { useState, useCallback, useRef, useEffect } from 'react';
import './FileUpload.css';

function FileUpload({
  onClose,
  uploadedFiles = [],
  onFilesUpdate,
  onUploadCompleteAndProcess
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFilesForUpload, setSelectedFilesForUpload] = useState([]);
  const [filesToDelete, setFilesToDelete] = useState([]);

  const MAX_FILES = 5;

  const handleSelectFiles = (newFiles) => {
    if (newFiles.length === 0) return;

    const filesToAdd = newFiles.filter(newFile =>
      !selectedFilesForUpload.some(existingFile => existingFile.name === newFile.name) &&
      !uploadedFiles.some(existingFile => existingFile.name === newFile.name) &&
      newFile.name.toLowerCase().endsWith('.zip')
    );

    const currentTotalFiles = selectedFilesForUpload.length + uploadedFiles.length - filesToDelete.length + filesToAdd.length;

    if (currentTotalFiles > MAX_FILES) {
        alert(`You can have a maximum of ${MAX_FILES} files in total.`);
        const filesAllowed = MAX_FILES - (selectedFilesForUpload.length + uploadedFiles.length - filesToDelete.length);
        if (filesAllowed > 0) {
             setSelectedFilesForUpload(prevFiles => [...prevFiles, ...filesToAdd.slice(0, filesAllowed)]);
        }
    } else {
        setSelectedFilesForUpload(prevFiles => [...prevFiles, ...filesToAdd]);
    }
  };

  const handleRemoveSelectedFile = (fileNameToRemove) => {
    setSelectedFilesForUpload(prevFiles => prevFiles.filter(file => file.name !== fileNameToRemove));
  };

  const handleMarkFileForDeletion = (fileName) => {
      setFilesToDelete(prevFilesToDelete => {
          if (prevFilesToDelete.includes(fileName)) {
              return prevFilesToDelete.filter(name => name !== fileName);
          } else {
              return [...prevFilesToDelete, fileName];
          }
      });
  };

  const handleSaveChanges = async () => {
    if (selectedFilesForUpload.length === 0 && filesToDelete.length === 0) {
      console.log("No changes to save.");
      onClose();
      return;
    }

    let uploadSuccess = true;
    let deleteSuccess = true;

    if (selectedFilesForUpload.length > 0) {
        const formData = new FormData();
        selectedFilesForUpload.forEach(file => {
          formData.append('files', file);
        });

        try {
          const xhr = new XMLHttpRequest();
          xhr.open('POST', 'http://127.0.0.1:5000/api/upload');

          xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              console.log('Upload successful:', xhr.responseText);
              const successfullyAddedFiles = selectedFilesForUpload.map(file => ({ name: file.name }));
              onFilesUpdate({ action: 'add', files: successfullyAddedFiles });
              setSelectedFilesForUpload([]);
              uploadSuccess = true;
            } else {
              console.error('Upload failed:', xhr.responseText);
              alert(`Upload failed: ${xhr.responseText}`);
              uploadSuccess = false;
            }
            processDeletions();
          };

          xhr.onerror = () => {
            console.error('Network error during upload:', xhr.statusText);
            alert(`Network error during upload: ${xhr.statusText}`);
            uploadSuccess = false;
            processDeletions();
          };

          xhr.send(formData);

        } catch (error) {
          console.error('Error setting up upload:', error);
          alert(`Error setting up upload: ${error}`);
          uploadSuccess = false;
          processDeletions();
        }
    } else {
        processDeletions();
    }

    const processDeletions = async () => {
        if (filesToDelete.length > 0 && uploadSuccess) {
            for (let i = 0; i < filesToDelete.length; i++) {
                const fileName = filesToDelete[i];
                try {
                    const deleteResponse = await fetch('http://127.0.0.1:5000/api/delete_file', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ filename: fileName }),
                    });

                    const deleteData = await deleteResponse.json();

                    if (deleteResponse.ok) {
                        console.log(`Deletion successful for ${fileName}:`, deleteData.message);
                        onFilesUpdate({ action: 'remove', fileName: fileName });
                    } else {
                        console.error(`Deletion failed for ${fileName}:`, deleteData.error);
                        alert(`Deletion failed for ${fileName}: ${deleteData.error}`);
                        deleteSuccess = false;
                    }
                } catch (error) {
                    console.error(`Network error during deletion for ${fileName}:`, error);
                    alert(`Network error during deletion for ${fileName}: ${error}`);
                    deleteSuccess = false;
                }
            }
            setFilesToDelete([]);
        }

        const initialChangesMade = selectedFilesForUpload.length > 0 || filesToDelete.length > 0;

        if (initialChangesMade && uploadSuccess && deleteSuccess) {
            if (onUploadCompleteAndProcess) {
                console.log("Triggering data processing after save changes.");
                onUploadCompleteAndProcess();
            }
            onClose();
        } else if (!uploadSuccess || !deleteSuccess) {
            console.log("Save changes failed. Processing not triggered.");
        } else {
             console.log("No changes were actually processed.");
             onClose();
        }
    };
  };

  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    if (droppedFiles.length > 0) {
      handleSelectFiles(droppedFiles);
    }
  }, [selectedFilesForUpload, uploadedFiles, filesToDelete]);

  const handleFileInputChange = (e) => {
    const browserFiles = Array.from(e.target.files);
    if (browserFiles.length > 0) {
      handleSelectFiles(browserFiles);
    }
    e.target.value = null;
  };

  const isSaveDisabled = selectedFilesForUpload.length === 0 && filesToDelete.length === 0;

  return (
    <div className="file-upload-overlay">
      <div className="file-upload-modal">
        <div className="file-upload-header">
          <h2>Edit Uploaded Data</h2>
          <button onClick={onClose} className="close-btn" aria-label="Close">&times;</button>
        </div>

        <>
          <div
            className={`file-drop-area ${isDragging ? 'dragging' : ''}`}
            onDragEnter={handleDragEnter}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input
              id="file-upload-input"
              type="file"
              multiple
              onChange={handleFileInputChange}
              style={{ display: 'none' }}
              accept=".zip"
            />
            <label htmlFor="file-upload-input" className="drop-message">
              {isDragging ? (
                "Drop files here..."
              ) : (
                <>Drag & drop zip files here, or <span className="browse-link">browse</span></>
              )}
            </label>
          </div>

          {selectedFilesForUpload.length > 0 && (
            <div className="selected-files">
              <h3>Files to Upload ({selectedFilesForUpload.length}):</h3>
              <ul className="file-list">
                {selectedFilesForUpload.map((file, index) => (
                  <li key={file.name || index} className="file-item">
                     <span className="file-icon">📄</span>
                     <span className="file-name" title={file.name}>{file.name}</span>
                     <button
                       onClick={() => handleRemoveSelectedFile(file.name)}
                       className="remove-file-btn"
                       aria-label={`Remove ${file.name}`}
                     >
                       &times;
                     </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {uploadedFiles.length > 0 && (
            <div className="uploaded-files">
              <h3>Currently Uploaded Files ({uploadedFiles.length}):</h3>
              <ul className="file-list">
                {uploadedFiles.map((file, index) => (
                  <li key={file.name || index} className="file-item">
                     <span className="file-name" title={file.name}>{file.name}</span>
                     <button
                       onClick={() => handleMarkFileForDeletion(file.name)}
                       className={`remove-file-btn ${filesToDelete.includes(file.name) ? 'marked-for-deletion' : ''}`}
                       aria-label={`Mark ${file.name} for deletion`}
                       title={filesToDelete.includes(file.name) ? 'Unmark for deletion' : 'Mark for deletion'}
                     >
                       {filesToDelete.includes(file.name) ? 'Undo' : '×'}
                     </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

        </>

        <div className="upload-actions">
           <button
               onClick={handleSaveChanges}
               className="btn-primary action-btn"
               disabled={isSaveDisabled}
           >
               Save Changes
           </button>
          <button onClick={onClose} className="btn-secondary action-btn">Close</button>
        </div>

      </div>
    </div>
  );
}

export default FileUpload;
