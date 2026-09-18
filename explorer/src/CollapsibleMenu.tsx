import React, { useState } from 'react';

export default function CollapsibleMenu({
  children,
  title = 'Menu',
  defaultOpen = false,
  width = 250,
  position,
}: {
  children: React.ReactNode;
  title?: string;
  defaultOpen?: boolean;
  width?: number;
  position?: 'left' | 'right';
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  const isLeft = position === 'left';

  return (
    <div
      style={{
        position: 'fixed',
        [isLeft ? 'left' : 'right']: isOpen ? 0 : -width,
        top: 0,
        width: width,
        height: '100vh',
        backgroundColor: '#2c3e50',
        color: 'white',
        transition: `${isLeft ? 'left' : 'right'} 0.3s ease-in-out`,
        zIndex: 1000,
        boxShadow: isOpen
          ? isLeft
            ? '2px 0 10px rgba(0,0,0,0.3)'
            : '-2px 0 10px rgba(0,0,0,0.3)'
          : 'none',
      }}
    >
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          position: 'absolute',
          [isLeft ? 'right' : 'left']: -40,
          top: '50%',
          transform: 'translateY(-50%)',
          width: 40,
          height: 40,
          backgroundColor: '#2c3e50',
          border: 'none',
          color: 'white',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '18px',
          borderRadius: isLeft ? '0 4px 4px 0' : '4px 0 0 4px',
          boxShadow: isLeft
            ? '2px 0 5px rgba(0,0,0,0.2)'
            : '-2px 0 5px rgba(0,0,0,0.2)',
          zIndex: 1001,
        }}
        title={isOpen ? 'Close Menu' : 'Open Menu'}
      >
        {isOpen ? '×' : '☰'}
      </button>

      {/* Menu Header */}
      <div
        style={{
          padding: '20px',
          borderBottom: '1px solid #34495e',
          backgroundColor: '#34495e',
        }}
      >
        <h2
          style={{
            margin: 0,
            fontSize: '18px',
            fontWeight: 'bold',
          }}
        >
          {title}
        </h2>
      </div>

      {/* Menu Content */}
      <div
        style={{
          padding: '20px',
          height: 'calc(100vh - 80px)',
          overflowY: 'auto',
        }}
      >
        {children}
      </div>
    </div>
  );
}
