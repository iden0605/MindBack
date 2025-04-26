import React, { useState, useEffect, useRef } from 'react';
import './CustomYearDropdown.css';

function CustomYearDropdown({ selectedYear, years, onYearSelect }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [dropdownRef]);

  const handleOptionClick = (year) => {
    onYearSelect(year);
    setIsOpen(false);
  };

  const toggleDropdown = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div className="custom-year-dropdown" ref={dropdownRef}>
      <button
        type="button"
        className="dropdown-toggle-btn"
        onClick={toggleDropdown}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span>{selectedYear}</span>
        <span className={`dropdown-arrow ${isOpen ? 'open' : ''}`}>▼</span>
      </button>
      {isOpen && (
        <ul className="dropdown-options-list" role="listbox">
          {years.map(year => (
            <li
              key={year}
              className={`dropdown-option ${year === selectedYear ? 'selected' : ''}`}
              onClick={() => handleOptionClick(year)}
              role="option"
              aria-selected={year === selectedYear}
            >
              {year}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default CustomYearDropdown;
