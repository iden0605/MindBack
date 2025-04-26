import { useState } from 'react';

function Timeline({ memories, selectedYear, onMemorySelect }) {
  const filteredMemories = memories.filter(memory => {
    const date = new Date(memory.date);
    return date.getFullYear() === selectedYear;
  });

  const getTypeIcon = (type) => {
    switch(type) {
      case 'social': return '👥';
      case 'email': return '✉️';
      case 'journal': return '📓';
      case 'family': return '👨‍👩‍👧‍👦';
      case 'photo': return '📷';
      default: return '📌';
    }
  };

  const formatDate = (dateString) => {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  return (
    <div className="timeline">
      <div className="timeline-line"></div>

      {filteredMemories.length > 0 ? (
        filteredMemories.map(memory => (
          <div
            key={memory.id}
            className="memory-card"
            onClick={() => onMemorySelect(memory)}
          >
            <div className={`memory-type-icon memory-type-${memory.type}`}>
              {getTypeIcon(memory.type)}
            </div>
            <div className="memory-date">{formatDate(memory.date)}</div>
            <div className="memory-content">{memory.content}</div>
            {memory.media && (
              <div className="memory-media">
                <img
                  src={memory.media.url}
                  alt={memory.media.caption || 'Memory media'}
                />
                {memory.media.caption && (
                  <p className="media-caption">{memory.media.caption}</p>
                )}
              </div>
            )}
          </div>
        ))
      ) : (
        <div className="no-memories">
          <p>No memories found for this year.</p>
          <p>Try selecting a different year or import more data.</p>
        </div>
      )}
    </div>
  );
}

export default Timeline;
