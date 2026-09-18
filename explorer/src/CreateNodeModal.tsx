import React, { useMemo, useState } from 'react';
import { SemanticGraphNode, DataProp } from './types';

export default function CreateNodeModal({
  isOpen,
  onClose,
  onSubmit,
  availableNodeKinds,
  entityDataPropsMapping,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (node: SemanticGraphNode) => void;
  availableNodeKinds: string[];
  entityDataPropsMapping: Map<string, string[]>;
}) {
  const [nodeId, setNodeId] = useState('');
  const [selectedKinds, setSelectedKinds] = useState<string[]>([]);
  const [dataProps, setDataProps] = useState<DataProp[]>([]);
  const [newPropKey, setNewPropKey] = useState('');
  const [newPropValue, setNewPropValue] = useState('');
  const availableDataProps = useMemo(() => {
    const aa = Array.from(entityDataPropsMapping.entries())
      .filter(([kind]) => selectedKinds.includes(kind))
      .map(([_kind, dataProps]) => dataProps);
    return Array.from(
      new Set(aa[0] !== undefined ? aa[0].concat(...aa.slice(1)) : []).values()
    );
  }, [entityDataPropsMapping, selectedKinds]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!nodeId.trim() || selectedKinds.length === 0) {
      return;
    }

    const newNode: SemanticGraphNode = {
      id: nodeId.trim(),
      kind: selectedKinds,
      dataProps: dataProps.filter(
        (prop) => prop.key.trim() && prop.value !== ''
      ),
    };

    onSubmit(newNode);
    handleClose();
  };

  const handleClose = () => {
    setNodeId('');
    setSelectedKinds([]);
    setDataProps([]);
    setNewPropKey('');
    setNewPropValue('');
    onClose();
  };

  const addDataProp = () => {
    if (newPropKey.trim() && newPropValue !== '') {
      setDataProps((old) => [
        ...old,
        { key: newPropKey.trim(), value: newPropValue },
      ]);
      setNewPropKey('');
      setNewPropValue('');
    }
  };

  const removeDataProp = (index: number) => {
    setDataProps(dataProps.filter((_, i) => i !== index));
  };

  const toggleKind = (kind: string) => {
    setSelectedKinds((prev) =>
      prev.includes(kind) ? prev.filter((k) => k !== kind) : [...prev, kind]
    );
  };

  if (!isOpen) return null;

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
        <h2 style={{ margin: '0 0 20px 0', color: '#ecf0f1' }}>Add New Node</h2>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label
              style={{
                display: 'block',
                marginBottom: '8px',
                fontWeight: 'bold',
              }}
            >
              Node ID *
            </label>
            <input
              type="text"
              value={nodeId}
              onChange={(e) => setNodeId(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '4px',
                border: '1px solid #34495e',
                backgroundColor: '#34495e',
                color: '#ecf0f1',
                fontSize: '14px',
              }}
              placeholder="Enter node ID"
              required
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label
              style={{
                display: 'block',
                marginBottom: '8px',
                fontWeight: 'bold',
              }}
            >
              Node Kinds *
            </label>
            <div
              style={{
                maxHeight: '150px',
                overflowY: 'auto',
                border: '1px solid #34495e',
                borderRadius: '4px',
                padding: '8px',
              }}
            >
              {availableNodeKinds.map((kind) => (
                <label
                  key={kind}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: '4px',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedKinds.includes(kind)}
                    onChange={() => toggleKind(kind)}
                    style={{ marginRight: '8px' }}
                  />
                  {kind}
                </label>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label
              style={{
                display: 'block',
                marginBottom: '8px',
                fontWeight: 'bold',
              }}
            >
              Data Properties
            </label>
            <div style={{ marginBottom: '8px' }}>
              {availableDataProps.map((dataProp) => (
                <React.Fragment key={dataProp}>
                  <label key={dataProp}>{dataProp}</label>
                  <input
                    type="text"
                    value={newPropKey}
                    onChange={(e) => {
                      setDataProps((old) =>
                        old.map(({ key, value }) =>
                          key === dataProp
                            ? {
                                key: dataProp,
                                value: e.target.value,
                              }
                            : { key, value }
                        )
                      );
                    }}
                    style={{
                      width: '45%',
                      padding: '8px 12px',
                      borderRadius: '4px',
                      border: '1px solid #34495e',
                      backgroundColor: '#34495e',
                      color: '#ecf0f1',
                      fontSize: '14px',
                      marginRight: '8px',
                    }}
                  />
                </React.Fragment>
              ))}
            </div>
            <div style={{ marginBottom: '8px' }}>
              <input
                type="text"
                value={newPropKey}
                onChange={(e) => setNewPropKey(e.target.value)}
                placeholder="Property key"
                style={{
                  width: '45%',
                  padding: '8px 12px',
                  borderRadius: '4px',
                  border: '1px solid #34495e',
                  backgroundColor: '#34495e',
                  color: '#ecf0f1',
                  fontSize: '14px',
                  marginRight: '8px',
                }}
              />
              <input
                type="text"
                value={newPropValue}
                onChange={(e) => setNewPropValue(e.target.value)}
                placeholder="Property value"
                style={{
                  width: '45%',
                  padding: '8px 12px',
                  borderRadius: '4px',
                  border: '1px solid #34495e',
                  backgroundColor: '#34495e',
                  color: '#ecf0f1',
                  fontSize: '14px',
                  marginRight: '8px',
                }}
              />
              <button
                type="button"
                onClick={addDataProp}
                style={{
                  padding: '8px 12px',
                  backgroundColor: '#3498db',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '14px',
                }}
              >
                Add
              </button>
            </div>
            {dataProps.length > 0 && (
              <div style={{ maxHeight: '100px', overflowY: 'auto' }}>
                {dataProps.map((prop, index) => (
                  <div
                    key={index}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '4px 8px',
                      backgroundColor: '#34495e',
                      marginBottom: '4px',
                      borderRadius: '4px',
                    }}
                  >
                    <span>
                      {prop.key}: {prop.value}
                    </span>
                    <button
                      type="button"
                      onClick={() => removeDataProp(index)}
                      style={{
                        backgroundColor: '#e74c3c',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        padding: '2px 6px',
                        cursor: 'pointer',
                        fontSize: '12px',
                      }}
                    >
                      Remove
                    </button>
                  </div>
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
              style={{
                padding: '10px 20px',
                backgroundColor: '#27ae60',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px',
              }}
            >
              Add Node
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
