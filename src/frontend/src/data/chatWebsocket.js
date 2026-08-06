"use client";
import { useEffect, useRef } from "react";
import { useSetAtom } from "jotai";
import {
  messagesAtom,
  lastDoneMessageKeyAtom,
  graphRefetchTriggerAtom,
  selectNodeEmitAtom,
  revertTitleEmitAtom,
} from "../lib/atoms";
import { io } from "socket.io-client";
import { BACKEND_BASE_URL } from "./api.js";

export function useChatWebSocket(setStatus, onTitleUpdate) {
  const SOCKET_PATH = "/socket.io";

  const setMessages = useSetAtom(messagesAtom);
  const setLastDoneMessageKey = useSetAtom(lastDoneMessageKeyAtom);
  const triggerRefetch = useSetAtom(graphRefetchTriggerAtom);
  const setSelectedNodeEmit = useSetAtom(selectNodeEmitAtom);
  const setRevertTitleEmit = useSetAtom(revertTitleEmitAtom);
  const socketRef = useRef(null);
  const streamingKeyRef = useRef(null);
  const chatModelStartCountRef = useRef(0);
  const pendingRevertRef = useRef(null);

  useEffect(() => {
    const socket = io(BACKEND_BASE_URL, {
      path: SOCKET_PATH,
      withCredentials: true,
      transports: ["polling", "websocket"],
    });

    socketRef.current = socket;
    setSelectedNodeEmit(
      () => (nodeId) => socket.emit("select_node", { node_id: nodeId })
    );
    setRevertTitleEmit(
      () => (sessionId, name) => {
        pendingRevertRef.current = { sessionId, name };
        socket.emit("session_title_revert", { session_id: sessionId, name });
      }
    );

    socket.on("connect", () => {
      console.log("Socket.IO connected:", socket.id);
    });

    socket.on("disconnect", () => {
      console.log("Socket.IO disconnected");
      streamingKeyRef.current = null;
      setStatus("ready");
    });

    socket.on("message", (data) => {
      if (data.role !== "ai") return;

      if (data.subnode === "system_prompt") {
        const content = data.content || "";
        setLastDoneMessageKey(null);
        setMessages((prev) => {
          const newKey = (prev[0]?.key || 0) + 1;
          return [
            {
              key: newKey,
              name: "system_prompt",
              value: content,
              reasoning: null,
            },
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
          { key: newKey, name: "ai", value: token, reasoning: null },
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

    socket.on("session_title_updated", (data) => {
      onTitleUpdate?.(data.session_id, data.name);

      const pending = pendingRevertRef.current;
      const isRevertEcho =
        data.previous_name == null &&
        pending?.sessionId === data.session_id &&
        pending?.name === data.name;
      pendingRevertRef.current = null;
      if (isRevertEcho) return;

      const content = data.name || "";

      setMessages((prev) => {
        const newKey = (prev[0]?.key || 0) + 1;
        return [
          {
            key: newKey,
            name: "session_title_updated",
            value: content,
            previousName: data.previous_name ?? null,
            sessionId: data.session_id,
            reasoning: null,
          },
          ...prev,
        ];
      });
    });

    return () => {
      socket.disconnect();
      setSelectedNodeEmit(null);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const send = (msg) => {
    streamingKeyRef.current = null;
    chatModelStartCountRef.current = 0;
    setStatus("thinking");
    socketRef.current?.emit("send_message", { message: msg });
  };

  return { send };
}
