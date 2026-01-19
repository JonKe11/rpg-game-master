


import React, { useState, useEffect, useRef } from 'react';
import useDebounce from '../hooks/useDebounce'; 

function AutocompleteField({ 
  label, 
  value, 
  onChange, 
  onSearch, 
  placeholder = '',
  required = false,
  clearOnSelect = false
}) {
  
  
  const [inputValue, setInputValue] = useState(value || '');
  const [filteredSuggestions, setFilteredSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const wrapperRef = useRef(null);

  const debouncedSearchTerm = useDebounce(inputValue, 300); 

  
  
  useEffect(() => {
    if (value !== inputValue) {
        setInputValue(value || '');
    }
  }, [value]); 

  
  useEffect(() => {
    
    
    
    
    
    if (onSearch && debouncedSearchTerm && showSuggestions) {
      setIsLoading(true);
      const fetchSuggestions = async () => {
        const results = await onSearch(debouncedSearchTerm);
        setFilteredSuggestions(results);
        setIsLoading(false);
      };
      fetchSuggestions();
    } else {
      setFilteredSuggestions([]);
    }
  }, [debouncedSearchTerm, onSearch, showSuggestions]); 

  
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
    setShowSuggestions(true);   
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
        <label className="block text-sm font-medium text-gray-300 mb-2">
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
      
      {/* Loader */}
      {isLoading && (
          <div className="absolute right-3 top-9">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-400"></div>
          </div>
      )}

      {/* Sugestie */}
      {showSuggestions && (filteredSuggestions.length > 0) && (
        <div className="absolute z-10 w-full mt-1 bg-gray-700 border border-gray-600 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {filteredSuggestions.slice(0, 50).map((suggestion, idx) => (
            <div
              key={idx}
              onMouseDown={(e) => e.preventDefault()} 
              onClick={() => handleSelect(suggestion)}
              className="px-3 py-2 hover:bg-blue-600 cursor-pointer border-b border-gray-600 last:border-b-0 text-white"
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