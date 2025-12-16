"use client";

import { useEffect, useRef } from "react";
import { useSetAtom } from "jotai";
import { messagesAtom } from "./atoms";
import { io } from "socket.io-client";

const SOCKET_URL = import.meta.env.VITE_BACKEND_BASE_URL;

export function useChatWebSocket(setStatus) {
  const setMessages = useSetAtom(messagesAtom);
  const socketRef = useRef(null);

  const streamingKeyRef = useRef(null);

  useEffect(() => {
    const socket = io(SOCKET_URL, {
      path: "/socket.io",
      withCredentials: true,
      transports: ["polling", "websocket"],
    });

    socketRef.current = socket;

    socket.on("connect", () => {
      console.log("Socket.IO connected:", socket.id);
    });

    socket.on("disconnect", () => {
      console.log("Socket.IO disconnected");
      streamingKeyRef.current = null;
      setStatus("ready");
    });

    socket.on("message", (data) => {
      console.log("SOCKET MESSAGE:", data);

      if (data.role !== "chatbot") return;

      const token = data.content || "";

      setMessages((prev) => {
        if (streamingKeyRef.current !== null) {
          return prev.map((m) =>
            m.key === streamingKeyRef.current
              ? { ...m, value: m.value + token }
              : m
          );
        }

        const newKey = (prev[0]?.key || 0) + 1;
        streamingKeyRef.current = newKey;

        return [
          { key: newKey, name: "chatbot", value: token },
          ...prev,
        ];
      });
    });

    socket.on("done", () => {
      streamingKeyRef.current = null;
      setStatus("ready");
    });

    return () => socket.disconnect();
  }, []);

  const send = (msg) => {
    streamingKeyRef.current = null;
    setStatus("streaming");
    socketRef.current?.emit("send_message", { message: msg });
  };

  return { send };
}
