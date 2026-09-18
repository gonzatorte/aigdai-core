import React, { useState, useCallback } from 'react';
import { COMMON_PREFIXES, BASE_ONTO_PREFIX_RE } from './api/sparqlQueries';
import { encodeEntities } from './lib/util';
// import { useMask } from '@react-input/mask';

const PREFIX = `${COMMON_PREFIXES}
SELECT ?s ?p ?o WHERE {
`;
const POSTFIX = `
FILTER regex(STR(?s), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
FILTER regex(STR(?p), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
FILTER regex(STR(?o), "^${BASE_ONTO_PREFIX_RE}.+", "i") .
}`;
const PREFIX_HTML = encodeEntities(PREFIX).replace(/\n/g, '<br/>');
const POSTFIX_HTML = encodeEntities(POSTFIX).replace(/\n/g, '<br/>');

export default function SparqlQueryModal({
  isOpen,
  onClose,
  onExecuteQuery,
}: {
  isOpen: boolean;
  onClose: () => void;
  onExecuteQuery: (query: string) => Promise<Record<string, any>[]>;
}) {
  // const inputRef = useMask({
  //   mask: '+0',
  //   replacement: { _: /\d/ },
  // });
  const [query, setQuery] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [results, setResults] = useState<Record<string, any>[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleClose = useCallback(() => {
    setQuery('');
    setResults(null);
    setError(null);
    setIsExecuting(false);
    onClose();
  }, [onClose]);

  const handleExecute = useCallback(async () => {
    if (!query.trim()) return;

    setIsExecuting(true);
    setError(null);
    setResults(null);

    try {
      const queryResults = await onExecuteQuery(query.trim());
      setResults(queryResults);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsExecuting(false);
    }
  }, [query, onExecuteQuery]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        handleExecute();
      }
    },
    [handleExecute]
  );

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
          width: '80vw',
          maxWidth: '1000px',
          height: '80vh',
          maxHeight: '800px',
          display: 'flex',
          flexDirection: 'column',
          color: '#ecf0f1',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '20px',
          }}
        >
          <h2 style={{ margin: 0, color: '#ecf0f1' }}>SPARQL Query</h2>
          <button
            onClick={handleClose}
            style={{
              background: 'none',
              border: 'none',
              color: '#ecf0f1',
              fontSize: '24px',
              cursor: 'pointer',
              padding: '4px',
            }}
          >
            ×
          </button>
        </div>

        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          <div style={{ flex: '0 0 auto' }}>
            <label
              style={{
                display: 'block',
                marginBottom: '8px',
                fontWeight: 'bold',
              }}
            >
              Query
            </label>
            <span dangerouslySetInnerHTML={{ __html: PREFIX_HTML }} />
            {/* <textarea value={PREFIX} disabled/> */}
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter your SPARQL query here... (Ctrl+Enter to execute)"
              style={{
                width: '100%',
                height: '200px',
                padding: '12px',
                borderRadius: '4px',
                border: '1px solid #34495e',
                backgroundColor: '#34495e',
                color: '#ecf0f1',
                fontSize: '14px',
                fontFamily: 'monospace',
                resize: 'vertical',
              }}
            />
            {/* <textarea value={POSTFIX} disabled/> */}
            <span dangerouslySetInnerHTML={{ __html: POSTFIX_HTML }} />
          </div>

          <div
            style={{
              flex: '1 1 auto',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <div
              style={{
                display: 'flex',
                gap: '12px',
                marginBottom: '16px',
                flex: '0 0 auto',
              }}
            >
              <button
                onClick={handleExecute}
                disabled={!query.trim() || isExecuting}
                style={{
                  padding: '10px 20px',
                  backgroundColor:
                    !query.trim() || isExecuting ? '#7f8c8d' : '#3498db',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor:
                    !query.trim() || isExecuting ? 'not-allowed' : 'pointer',
                  fontSize: '14px',
                }}
              >
                {isExecuting ? 'Executing...' : 'Execute Query'}
              </button>
              <button
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
                Close
              </button>
            </div>

            <div
              style={{
                flex: '1 1 auto',
                border: '1px solid #34495e',
                borderRadius: '4px',
                padding: '12px',
                backgroundColor: '#34495e',
                overflow: 'auto',
              }}
            >
              {error && (
                <div
                  style={{
                    color: '#e74c3c',
                    marginBottom: '12px',
                    padding: '8px',
                    backgroundColor: '#2c3e50',
                    borderRadius: '4px',
                    border: '1px solid #e74c3c',
                  }}
                >
                  <strong>Error:</strong> {error}
                </div>
              )}

              {results && (
                <div>
                  <div
                    style={{
                      marginBottom: '12px',
                      fontWeight: 'bold',
                      color: '#27ae60',
                    }}
                  >
                    Results ({Array.isArray(results) ? results.length : 'N/A'}{' '}
                    rows)
                  </div>
                  <pre
                    style={{
                      color: '#ecf0f1',
                      fontSize: '12px',
                      fontFamily: 'monospace',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                    }}
                  >
                    {JSON.stringify(results, null, 2)}
                  </pre>
                </div>
              )}

              {!results && !error && !isExecuting && (
                <div
                  style={{
                    color: '#95a5a6',
                    fontStyle: 'italic',
                    textAlign: 'center',
                    padding: '20px',
                  }}
                >
                  Enter a SPARQL query and click Execute Query button to see
                  results
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
