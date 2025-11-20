// frontend/src/hooks/useDebounce.js
import { useState, useEffect } from 'react';

// Ten hook opóźnia wykonanie akcji (np. wyszukiwania)
function useDebounce(value, delay) {
    const [debouncedValue, setDebouncedValue] = useState(value);

    useEffect(() => {
        // Ustaw timer, który zaktualizuje wartość po 'delay' ms
        const handler = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);

        // Anuluj timer, jeśli wartość się zmieniła (użytkownik dalej pisze)
        return () => {
            clearTimeout(handler);
        };
    }, [value, delay]); // Uruchom ponownie tylko, gdy zmieni się wartość lub opóźnienie

    return debouncedValue;
}

export default useDebounce;