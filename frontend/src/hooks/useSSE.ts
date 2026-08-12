import { useState, useEffect, useRef, useCallback } from 'react';
import type { SSEEvent } from '../types';

export function useSSE(executionId: string | null) {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [done, setDone] = useState(false);
  const sourceRef = useRef<EventSource | null>(null);
  const mountedRef = useRef(false);
  const doneRef = useRef(false);

  const addEvent = useCallback((event: SSEEvent) => {
    if (doneRef.current) return;
    setEvents((prev) => [...prev, event]);
    if (event.type === 'execution_completed') {
      doneRef.current = true;
      setDone(true);
      setConnected(false);
    }
  }, []);

  const reset = useCallback(() => {
    sourceRef.current?.close();
    sourceRef.current = null;
    doneRef.current = false;
    setEvents([]);
    setConnected(false);
    setDone(false);
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  useEffect(() => {
    if (!executionId || doneRef.current) return;

    const token = localStorage.getItem('token');
    if (!token) return;

    const railwayUrl = import.meta.env.VITE_RAILWAY_URL || '';
    const url = railwayUrl
      ? `${railwayUrl}/sse/${executionId}?token=${token}`
      : `/api/v1/executions/${executionId}/stream?token=${token}`;
    const es = new EventSource(url);
    sourceRef.current = es;

    es.onopen = () => {
      if (mountedRef.current && !doneRef.current) setConnected(true);
    };

    es.onmessage = (event) => {
      if (!mountedRef.current || doneRef.current) return;
      try {
        const data = JSON.parse(event.data) as SSEEvent;
        addEvent(data);
      } catch {
        // ignore
      }
    };

    es.onerror = () => {
      if (mountedRef.current) setConnected(false);
      es.close();
    };

    return () => {
      es.close();
      sourceRef.current = null;
    };
  }, [executionId, addEvent]);

  return { events, connected, done, reset, addEvent };
}
