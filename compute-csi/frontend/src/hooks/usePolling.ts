import { useEffect, useRef } from 'react';

export function usePolling(fn: () => void, interval: number, enabled: boolean) {
  const fnRef = useRef(fn);
  fnRef.current = fn;
  useEffect(() => {
    if (!enabled) return;
    const id = setInterval(() => fnRef.current(), interval);
    return () => clearInterval(id);
  }, [interval, enabled]);
}
