// frontend/src/components/AutocompleteField.js
// ✅ WERSJA 2.2 - Poprawiona logika 'onChange' i wyszukiwania

import React, { useState, useEffect, useRef } from 'react';
import useDebounce from '../hooks/useDebounce'; // ✅ POTRZEBUJEMY TEGO HOOKA

function AutocompleteField({ 
  label, 
  value, 
  onChange, 
  onSearch, // (query) => Promise<string[]>
  placeholder = '',
  required = false,
  clearOnSelect = false
}) {
  // 'value' to kanoniczny stan z formularza nadrzędnego (np. formData.species)
  // 'inputValue' to to, co użytkownik widzi w polu <input>
  const [inputValue, setInputValue] = useState(value || '');
  const [filteredSuggestions, setFilteredSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const wrapperRef = useRef(null);

  const debouncedSearchTerm = useDebounce(inputValue, 300); // 300ms opóźnienia

  // Synchronizuj inputValue, jeśli 'value' (z nadrzędnego formularza) się zmieni
  // Np. po wybraniu sugestii
  useEffect(() => {
    if (value !== inputValue) {
        setInputValue(value || '');
    }
  }, [value]); // ✅ POPRAWKA: Usunięto 'inputValue' z zależności

  // Efekt wyszukiwania asynchronicznego
  useEffect(() => {
    // Wyszukaj tylko jeśli:
    // 1. Jest funkcja onSearch
    // 2. Użytkownik przestał pisać (debouncedSearchTerm)
    // 3. Sugestie są widoczne
    // 4. ✅ POPRAWKA: Usunięto 'debouncedSearchTerm !== value', co blokowało wyszukiwanie
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
  }, [debouncedSearchTerm, onSearch, showSuggestions]); // ✅ POPRAWKA: Usunięto 'value'

  // Zamykanie sugestii po kliknięciu poza (bez zmian)
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

  // ✅ POPRAWKA: handleChange MUSI wywołać onChange
  const handleChange = (e) => {
    const newValue = e.target.value;
    setInputValue(newValue);     // Zaktualizuj lokalny input
    onChange(newValue);         // Zaktualizuj stan rodzica (np. formData)
    setShowSuggestions(true);   // Pokaż sugestie
  };

  const handleSelect = (suggestion) => {
    if (clearOnSelect) {
      setInputValue('');
      onChange(''); 
    } else {
      setInputValue(suggestion);
      onChange(suggestion); // Ustawia wartość w nadrzędnym formularzu
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
              onMouseDown={(e) => e.preventDefault()} // Zapobiegaj utracie focusu
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