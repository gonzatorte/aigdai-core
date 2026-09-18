import React, { useState, useEffect, useCallback } from 'react';
import SelectableListStateless from './SelectableListStateless';

export type Item = {
  id: string;
  title: string;
  description?: string;
};

export default function SelectableList({
  selectedItems,
  onSelectionChange,
  onLoadMore,
  searchPlaceholder = 'Search items...',
  loadingMessage = 'Loading...',
  maxHeight = 400,
}: {
  selectedItems: string[];
  onSelectionChange: (selected: Item) => void;
  onLoadMore: (term: string, nextTo?: string) => Promise<Item[]>;
  searchPlaceholder?: string;
  loadingMessage?: string;
  maxHeight?: number;
}) {
  const [pinnedItems, setPinnedItems] = useState<string[]>([]);
  const [availableItems, setAvailableItems] = useState<Item[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  // Handle item selection
  const handleItemSelect = useCallback(
    (itemId: string) => {
      const item = availableItems.find(({ id }) => id === itemId);
      if (item) {
        onSelectionChange(item);
      }
    },
    [onSelectionChange, availableItems]
  );

  const handleItemPin = useCallback(
    (itemId: string) => {
      setPinnedItems((oldPinned) => {
        const newPinned = [...oldPinned];
        const foundIdx = newPinned.indexOf(itemId);
        if (foundIdx !== -1) {
          newPinned.splice(foundIdx, 1);
        } else {
          newPinned.push(itemId);
        }
        return newPinned;
      });
    },
    [setPinnedItems]
  );

  const setAvailableItemsKeepingSelected = useCallback(
    (newItems: Item[], replace: boolean) => {
      setAvailableItems((oldItems) => {
        if (replace) {
          const keeptItems = oldItems.filter(
            ({ id }) => pinnedItems.includes(id) || selectedItems.includes(id)
          );
          const newIds = new Set(newItems.map((item) => item.id));
          const filteredKeeptItems = keeptItems.filter(
            (item) => !newIds.has(item.id)
          );
          return [...filteredKeeptItems, ...newItems];
        }
        return [...oldItems, ...newItems];
      });
    },
    [setAvailableItems, pinnedItems, selectedItems]
  );

  useEffect(() => {
    onLoadMore(searchQuery).then((newItems) =>
      setAvailableItemsKeepingSelected(newItems, true)
    );
  }, [onLoadMore, searchQuery, setAvailableItemsKeepingSelected]);

  // Handle load more button click
  const handleLoadMore = useCallback(
    async (nextTo?: string) => {
      if (isLoadingMore) return;
      setIsLoadingMore(true);
      try {
        await onLoadMore(searchQuery, nextTo).then((newItems) =>
          setAvailableItemsKeepingSelected(newItems, false)
        );
      } catch (error) {
        console.error('Error loading more items:', error);
      } finally {
        setIsLoadingMore(false);
      }
    },
    [onLoadMore, searchQuery, isLoadingMore, setAvailableItemsKeepingSelected]
  );

  return (
    <SelectableListStateless
      availableItems={availableItems}
      selectedItems={selectedItems}
      pinnedItems={pinnedItems}
      term={searchQuery}
      onSelectionChange={handleItemSelect}
      onPinnedChange={handleItemPin}
      onLoadMore={handleLoadMore}
      onTermChange={setSearchQuery}
      loading={isLoadingMore}
      loadingMessage={loadingMessage}
      searchPlaceholder={searchPlaceholder}
      maxHeight={maxHeight}
    />
  );
}
