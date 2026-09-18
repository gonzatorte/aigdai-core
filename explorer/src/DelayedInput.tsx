import React, { useState, useCallback, useRef, useEffect } from 'react';

export default function DelayedInput({
  value,
  onChange,
  delay = 300,
  ...inputProps
}: {
  value: string;
  onChange: (value: string) => void;
  delay?: number;
} & Omit<React.InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange'>) {
  const [internalValue, setInternalValue] = useState(value);
  const timeoutRef = useRef<number | null>(null);

  // Update internal value when external value changes
  useEffect(() => {
    setInternalValue(value);
  }, [value]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      setInternalValue(newValue);

      // Clear existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Set new timeout
      timeoutRef.current = setTimeout(() => {
        onChange(newValue);
      }, delay);
    },
    [onChange, delay]
  );

  const isOutOfSync = internalValue !== value;

  return (
    <input
      {...inputProps}
      value={internalValue}
      onChange={handleInputChange}
      style={{
        ...inputProps.style,
        color: isOutOfSync ? '#666' : '#000',
      }}
    />
  );
}
