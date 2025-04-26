import React, { useState, useEffect } from 'react';
import './ParticipantDropdown.css';

function ParticipantDropdown({ availableParticipants, selectedUserNames, onUpdateSelectedUserNames }) {
  const [isOpen, setIsOpen] = useState(false);
  const [tempSelected, setTempSelected] = useState({});

  useEffect(() => {
    setTempSelected(selectedUserNames || {});
  }, [availableParticipants, selectedUserNames]);


  const handleSourceSelect = (source, participant) => {
    setTempSelected(prev => ({
      ...prev,
      [source]: participant
    }));
  };

  const handleApply = () => {
    onUpdateSelectedUserNames(tempSelected);
    setIsOpen(false);
  };

  const handleCancel = () => {
    setTempSelected(selectedUserNames || {});
    setIsOpen(false);
  };

  return (
    <div className="participant-dropdown">
      <button className="dropdown-toggle" onClick={() => setIsOpen(!isOpen)}>
        Select Persona
      </button>

      {isOpen && (
        <div className="dropdown-menu">
          {Object.entries(availableParticipants).map(([source, participants]) => (
            <div key={source} className="source-group">
              <h4>{source.charAt(0).toUpperCase() + source.slice(1)}</h4>
              <select
                value={tempSelected[source] || ''}
                onChange={(e) => handleSourceSelect(source, e.target.value)}
              >
                <option value="">Select {source} User</option>
                {participants.map(participant => (
                  <option key={participant} value={participant}>{participant}</option>
                ))}
              </select>
            </div>
          ))}
          <div className="dropdown-actions">
            <button onClick={handleApply}>Apply</button>
            <button onClick={handleCancel}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ParticipantDropdown;
