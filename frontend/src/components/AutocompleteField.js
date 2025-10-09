// frontend/src/components/AutocompleteField.js
import React, { useState, useEffect, useRef } from 'react';

function AutocompleteField({ 
  label, 
  value, 
  onChange, 
  suggestions = [], 
  onSearch,
  placeholder = '',
  required = false,
  clearOnSelect = false
}) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filteredSuggestions, setFilteredSuggestions] = useState(suggestions);
  const [inputValue, setInputValue] = useState(value);
  const wrapperRef = useRef(null);

  useEffect(() => {
    setInputValue(value);
  }, [value]);

  useEffect(() => {
    if (onSearch && inputValue && inputValue.length > 1) {
      onSearch(inputValue).then(results => {
        setFilteredSuggestions(results);
      });
    } else {
      const filtered = suggestions.filter(s => 
        s.toLowerCase().includes(inputValue.toLowerCase())
      );
      setFilteredSuggestions(filtered);
    }
  }, [inputValue, suggestions, onSearch]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleChange = (e) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    onChange(newValue);
  };

  const handleSelect = (suggestion) => {
    if (clearOnSelect) {
      setInputValue('');
      onChange('');
    } else {
      setInputValue(suggestion);
      onChange(suggestion);
    }
    setShowSuggestions(false);
  };

  return (
    <div className="relative" ref={wrapperRef}>
      {label && (
        <label className="block text-sm font-medium mb-2">
          {label} {required && <span className="text-red-500">*</span>}
        </label>
      )}
      <input
        type="text"
        value={inputValue}
        onChange={handleChange}
        onFocus={() => setShowSuggestions(true)}
        placeholder={placeholder}
        required={required}
        className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      {showSuggestions && filteredSuggestions.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-gray-700 border border-gray-600 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {filteredSuggestions.slice(0, 50).map((suggestion, idx) => (
            <div
              key={idx}
              onMouseDown={(e) => e.preventDefault()} // Prevent blur
              onClick={() => handleSelect(suggestion)}
              className="px-3 py-2 hover:bg-gray-600 cursor-pointer border-b border-gray-600 last:border-b-0"
            >
              {suggestion}
            </div>
          ))}
          {filteredSuggestions.length > 50 && (
            <div className="px-3 py-2 text-xs text-gray-400 text-center bg-gray-800">
              Showing 50 of {filteredSuggestions.length} results. Keep typing to narrow down.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default AutocompleteField;