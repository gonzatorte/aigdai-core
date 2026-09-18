import React, { useCallback, useMemo } from 'react';
import DelayedInput from './DelayedInput';

export interface Item {
  id: string;
  title: string;
  description?: string;
}

export default function SelectableListStateless({
  availableItems,
  selectedItems,
  pinnedItems,
  term,
  onSelectionChange,
  onPinnedChange,
  onLoadMore,
  onTermChange,
  loading = false,
  searchPlaceholder = 'Search items...',
  loadingMessage = 'Loading...',
  maxHeight = 400,
}: {
  availableItems: Item[];
  selectedItems: string[];
  pinnedItems: string[];
  term: string;
  onSelectionChange: (selectedId: string) => void;
  onPinnedChange: (selectedId: string) => void;
  onLoadMore: (nextTo?: string) => void;
  onTermChange: (term: string) => void;
  loading?: boolean;
  searchPlaceholder?: string;
  loadingMessage?: string;
  maxHeight?: number;
}) {
  const { sortedItems, lastItem } = useMemo(() => {
    const sortedItems = [...availableItems].sort((a, b) => {
      const aPinned = pinnedItems.includes(a.id);
      const bPinned = pinnedItems.includes(b.id);

      if (aPinned && !bPinned) return -1;
      if (!aPinned && bPinned) return 1;

      return a.id.localeCompare(b.id);
    });
    return { sortedItems, lastItem: sortedItems[sortedItems.length - 1] };
  }, [availableItems, pinnedItems]);

  const handleItemSelect = useCallback(
    (itemId: string) => {
      onSelectionChange(itemId);
    },
    [onSelectionChange]
  );

  const handleItemPin = useCallback(
    (itemId: string, event: React.MouseEvent) => {
      event.stopPropagation();
      onPinnedChange(itemId);
    },
    [onPinnedChange]
  );

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: '#34495e',
        borderRadius: '8px',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          padding: '16px',
          borderBottom: '1px solid #2c3e50',
        }}
      >
        <DelayedInput
          type="text"
          delay={2000}
          placeholder={searchPlaceholder}
          value={term}
          onChange={onTermChange}
          style={{
            width: '100%',
            padding: '8px 12px',
            border: '1px solid #2c3e50',
            borderRadius: '4px',
            backgroundColor: '#2c3e50',
            color: '#ecf0f1',
            fontSize: '14px',
            outline: 'none',
          }}
        />
      </div>

      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          maxHeight: maxHeight,
        }}
      >
        {sortedItems.length === 0 ? (
          <div
            style={{
              padding: '20px',
              textAlign: 'center',
              color: '#bdc3c7',
              fontSize: '14px',
            }}
          >
            No items available
          </div>
        ) : (
          sortedItems.map((item) => {
            const isSelected = Boolean(
              selectedItems.find((id) => id === item.id)
            );
            const isPinned = pinnedItems.includes(item.id);

            return (
              <div
                key={item.id}
                onClick={() => handleItemSelect(item.id)}
                style={{
                  padding: '12px 16px',
                  borderBottom: '1px solid #2c3e50',
                  backgroundColor: isSelected ? '#3498db' : 'transparent',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  transition: 'background-color 0.2s ease',
                  position: 'relative',
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.backgroundColor = '#2c3e50';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }
                }}
              >
                <button
                  onClick={(e) => handleItemPin(item.id, e)}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    padding: '4px',
                    color: isPinned ? '#f39c12' : '#bdc3c7',
                    fontSize: '14px',
                    transition: 'color 0.2s ease',
                  }}
                  title={isPinned ? 'Unpin item' : 'Pin item'}
                >
                  📌
                </button>
                <div style={{ flex: 1 }}>
                  <div
                    style={{
                      fontSize: '14px',
                      fontWeight: 'bold',
                      color: isSelected ? '#fff' : '#ecf0f1',
                      marginBottom: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                    }}
                  >
                    {item.title}
                  </div>
                  {item.description && (
                    <div
                      style={{
                        fontSize: '12px',
                        color: isSelected ? '#bdc3c7' : '#95a5a6',
                        marginLeft: '20px',
                      }}
                    >
                      {item.description}
                    </div>
                  )}
                </div>
                {isPinned && (
                  <div
                    style={{
                      position: 'absolute',
                      top: '4px',
                      right: '8px',
                      fontSize: '10px',
                      color: '#f39c12',
                      fontWeight: 'bold',
                    }}
                  >
                    PINNED
                  </div>
                )}
              </div>
            );
          })
        )}

        {/* Load More Button */}
        {onLoadMore && (
          <div
            style={{
              padding: '16px',
              textAlign: 'center',
              borderTop: '1px solid #2c3e50',
            }}
          >
            <button
              onClick={() => onLoadMore(lastItem?.id)}
              disabled={loading}
              style={{
                padding: '8px 16px',
                backgroundColor: loading ? '#2c3e50' : '#3498db',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                cursor: loading ? 'not-allowed' : 'pointer',
                fontSize: '14px',
                transition: 'background-color 0.2s ease',
              }}
            >
              {loading ? 'Loading...' : 'Load More'}
            </button>
          </div>
        )}

        {loading && (
          <div
            style={{
              padding: '16px',
              textAlign: 'center',
              color: '#bdc3c7',
              fontSize: '14px',
            }}
          >
            {loadingMessage}
          </div>
        )}
      </div>
    </div>
  );
}
