import { useEffect, useRef, useState } from "react";
import { WS_URL } from "../services/api";
import type { WSEvent } from "../types";

type EventHandler = (event: WSEvent) => void;

/**
 * Maintains a single WebSocket connection to the backend event bus
 * (Section 44a) and re-connects automatically on disconnect. Components
 * subscribe via `onEvent` for specific event types, or read `connected`
 * to show a live/offline indicator.
 */
export function useLiveEvents(onEvent?: EventHandler) {
  const [connected, setConnected] = useState(false);
  const handlerRef = useRef(onEvent);
  handlerRef.current = onEvent;

  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let closedByCleanup = false;

    function connect() {
      socket = new WebSocket(WS_URL);

      socket.onopen = () => setConnected(true);
      socket.onclose = () => {
        setConnected(false);
        if (!closedByCleanup) {
          reconnectTimer = setTimeout(connect, 2000);
        }
      };
      socket.onerror = () => {
        socket?.close();
      };
      socket.onmessage = (event) => {
        try {
          const parsed: WSEvent = JSON.parse(event.data);
          handlerRef.current?.(parsed);
        } catch {
          // ignore malformed frames
        }
      };
    }

    connect();

    return () => {
      closedByCleanup = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, []);

  return { connected };
}
