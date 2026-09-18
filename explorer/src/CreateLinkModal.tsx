import React, { useCallback, useMemo, useState } from 'react';
import { SemanticGraphNode } from './types';

export default function CreateLinkModal({
  inCreationLink,
  onClose,
  onSubmit,
  subjectToObjectPropsMapping,
}: {
  inCreationLink: {
    source: SemanticGraphNode;
    target: SemanticGraphNode;
  } | null;
  onClose: () => void;
  onSubmit: (
    source: SemanticGraphNode,
    target: SemanticGraphNode,
    kind: string[]
  ) => void;
  subjectToObjectPropsMapping: Map<string, readonly [string, string]>;
}) {
  const [selectedLinkTypes, setSelectedLinkTypes] = useState<string[]>([]);

  const availableLinkTypes = useMemo(() => {
    if (!inCreationLink) return [];

    const { source, target } = inCreationLink;

    const validLinkTypes = new Set(
      source.kind
        .map((sourceKind) => {
          const [prop, range] = subjectToObjectPropsMapping.get(sourceKind) || [
            null,
            null,
          ];
          if (range && target.kind.includes(range)) {
            return prop;
          }
          return null;
        })
        .filter((prop) => prop !== null)
    );

    return Array.from(validLinkTypes);
  }, [inCreationLink, subjectToObjectPropsMapping]);

  const handleClose = useCallback(() => {
    setSelectedLinkTypes([]);
    onClose();
  }, [onClose, setSelectedLinkTypes]);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (!inCreationLink || selectedLinkTypes.length === 0) {
        return;
      }

      onSubmit(inCreationLink.source, inCreationLink.target, selectedLinkTypes);
      handleClose();
    },
    [inCreationLink, selectedLinkTypes, onSubmit, handleClose]
  );

  const toggleLinkType = (linkType: string) => {
    setSelectedLinkTypes((prev) =>
      prev.includes(linkType)
        ? prev.filter((type) => type !== linkType)
        : [...prev, linkType]
    );
  };

  if (!inCreationLink) return null;

  const { source, target } = inCreationLink;

  if (!source || !target) {
    return null;
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 1000,
      }}
    >
      <div
        style={{
          backgroundColor: '#2c3e50',
          borderRadius: '8px',
          padding: '24px',
          width: '500px',
          maxHeight: '80vh',
          overflowY: 'auto',
          color: '#ecf0f1',
        }}
      >
        <h2 style={{ margin: '0 0 20px 0', color: '#ecf0f1' }}>Create Link</h2>

        <div style={{ marginBottom: '16px' }}>
          <div style={{ marginBottom: '8px' }}>
            <strong>Source Node:</strong> {source.id} ({source.kind.join(', ')})
          </div>
          <div style={{ marginBottom: '8px' }}>
            <strong>Target Node:</strong> {target.id} ({target.kind.join(', ')})
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label
              style={{
                display: 'block',
                marginBottom: '8px',
                fontWeight: 'bold',
              }}
            >
              Link Types *
            </label>
            {availableLinkTypes.length === 0 ? (
              <div style={{ color: '#e74c3c', fontStyle: 'italic' }}>
                No valid link types available between these node types.
              </div>
            ) : (
              <div
                style={{
                  maxHeight: '150px',
                  overflowY: 'auto',
                  border: '1px solid #34495e',
                  borderRadius: '4px',
                  padding: '8px',
                }}
              >
                {availableLinkTypes.map((linkType) => (
                  <label
                    key={linkType}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      marginBottom: '4px',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={selectedLinkTypes.includes(linkType)}
                      onChange={() => toggleLinkType(linkType)}
                      style={{ marginRight: '8px' }}
                    />
                    {linkType}
                  </label>
                ))}
              </div>
            )}
          </div>

          <div
            style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}
          >
            <button
              type="button"
              onClick={handleClose}
              style={{
                padding: '10px 20px',
                backgroundColor: '#95a5a6',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px',
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={
                selectedLinkTypes.length === 0 ||
                availableLinkTypes.length === 0
              }
              style={{
                padding: '10px 20px',
                backgroundColor:
                  selectedLinkTypes.length === 0 ||
                  availableLinkTypes.length === 0
                    ? '#7f8c8d'
                    : '#27ae60',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor:
                  selectedLinkTypes.length === 0 ||
                  availableLinkTypes.length === 0
                    ? 'not-allowed'
                    : 'pointer',
                fontSize: '14px',
              }}
            >
              Create Link
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
