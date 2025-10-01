// frontend/src/components/AutocompleteField.js
import React, { useState, useEffect } from 'react';

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
    <div className="relative">
      <label className="block text-sm font-medium mb-2">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      <input
        type="text"
        value={inputValue}
        onChange={handleChange}
        onFocus={() => setShowSuggestions(true)}
        onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
        placeholder={placeholder}
        required={required}
        className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      {showSuggestions && filteredSuggestions.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-gray-700 rounded-lg shadow-lg max-h-48 overflow-y-auto">
          {filteredSuggestions.map((suggestion, idx) => (
            <div
              key={idx}
              onClick={() => handleSelect(suggestion)}
              className="px-3 py-2 hover:bg-gray-600 cursor-pointer"
            >
              {suggestion}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default AutocompleteField;