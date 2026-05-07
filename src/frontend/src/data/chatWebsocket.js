"use client";
import { useEffect, useRef } from "react";
import { useSetAtom } from "jotai";
import { messagesAtom, lastDoneMessageKeyAtom, graphRefetchTriggerAtom, selectNodeEmitAtom } from "./atoms";
import { io } from "socket.io-client";

const SOCKET_URL = import.meta.env.VITE_BACKEND_BASE_URL;

export function useChatWebSocket(setStatus) {
  const setMessages = useSetAtom(messagesAtom);
  const setLastDoneMessageKey = useSetAtom(lastDoneMessageKeyAtom);
  const triggerRefetch = useSetAtom(graphRefetchTriggerAtom);
  const setSelectedNodeEmit = useSetAtom(selectNodeEmitAtom);
  const socketRef = useRef(null);
  const streamingKeyRef = useRef(null);
  const chatModelStartCountRef = useRef(0);

  useEffect(() => {
    const socket = io(SOCKET_URL, {
      path: "/socket.io",
      withCredentials: true,
      transports: ["polling", "websocket"],
    });

    socketRef.current = socket;
    setSelectedNodeEmit(() => (nodeId) => socket.emit("select_node", { node_id: nodeId }));

    socket.on("connect", () => {
      console.log("Socket.IO connected:", socket.id);
    });

    socket.on("disconnect", () => {
      console.log("Socket.IO disconnected");
      streamingKeyRef.current = null;
      setStatus("ready");
    });

    socket.on("message", (data) => {
      if (data.role !== "chatbot") return;

      if (data.subnode === "system_prompt") {
        const content = data.content || "";
        setLastDoneMessageKey(null);
        setMessages((prev) => {
          const newKey = (prev[0]?.key || 0) + 1;
          return [
            { key: newKey, name: "system_prompt", value: content, reasoning: null },
            ...prev,
          ];
        });
        return;
      }

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
          { key: newKey, name: "chatbot", value: token, reasoning: null },
          ...prev,
        ];
      });
    });

    socket.on("event", (payload) => {
      if (payload.type === "on_chat_model_start") {
        chatModelStartCountRef.current += 1;
        if (chatModelStartCountRef.current >= 2) {
          setStatus("streaming");
        }
      }
    });

    socket.on("done", () => {
      if (streamingKeyRef.current !== null) {
        setLastDoneMessageKey(streamingKeyRef.current);
      }
      streamingKeyRef.current = null;
      setStatus("ready");
      triggerRefetch((n) => n + 1);
    });

    return () => {
      socket.disconnect();
      setSelectedNodeEmit(null);
    };
  }, []);

  const send = (msg) => {
    streamingKeyRef.current = null;
    chatModelStartCountRef.current = 0;
    setStatus("thinking");
    socketRef.current?.emit("send_message", { message: msg });
  };

  return { send };
}