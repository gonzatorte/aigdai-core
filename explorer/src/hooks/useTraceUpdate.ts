import { useEffect, useRef } from 'react';

export function useTraceUpdate(props: Record<string, any>) {
  const prev = useRef<Record<string, any>>(props);
  useEffect(() => {
    const changedProps: Record<string, [any, any]> = {};
    Object.entries(props).forEach(([k, v]) => {
      if (prev.current[k] !== v) {
        changedProps[k] = [prev.current[k], v];
      }
    });
    if (Object.keys(changedProps).length > 0) {
      console.log('Changed props:', changedProps);
    }
    prev.current = props;
  });
}
