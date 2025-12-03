"use client";
import { useEffect, useRef } from "react";
import { useAtom, useSetAtom } from "jotai";
import { messagesAtom } from "./atoms";

const WS_URL = "ws://localhost:10090/ws/chat";
export function useChatWebSocket(setStatus) {
  const [messages, setMessages] = useAtom(messagesAtom);
  const wsRef = useRef(null);
  const streamingMsgKeyRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => console.log("WS connected");

    ws.onmessage = (event) => {
      console.log("WS RAW:", event.data);

      let data;
      try {
        data = JSON.parse(event.data);
      } catch (err) {
        console.error("WS parse error", err);
        return;
      }

      // ---------------------------
      // HANDLE DONE EVENT
      // ---------------------------
      if (data.type === "done") {
        console.log("WS DONE:", data);

        streamingMsgKeyRef.current = null;

        // Stop streaming state
        setStatus("ready");

        return;
      }

      // ---------------------------
      // HANDLE STREAMED TOKEN
      // ---------------------------
      if (data.type === "message" && data.role === "chatbot") {
        const token = data.content;

        setMessages((prev) => {
          if (streamingMsgKeyRef.current) {
            return prev.map((msg) =>
              msg.key === streamingMsgKeyRef.current
                ? { ...msg, value: msg.value + token }
                : msg
            );
          }

          const newKey = (prev[0]?.key || 0) + 1;
          streamingMsgKeyRef.current = newKey;

          return [
            { key: newKey, name: "chatbot", value: token },
            ...prev,
          ];
        });

        return;
      }
    };

    ws.onclose = () => {
      streamingMsgKeyRef.current = null;
      setStatus("ready");
      console.log("WS disconnected");
    };

    return () => ws.close();
  }, []);

  const send = (msg) => {
    streamingMsgKeyRef.current = null;

    // Start streaming state
    setStatus("streaming");

    wsRef.current?.send(JSON.stringify({ message: msg }));
  };

  return { send };
}
