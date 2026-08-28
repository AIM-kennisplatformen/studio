"use client";

import { useState, useRef, useEffect } from "react";
import { useAtom, useSetAtom } from "jotai";
import {
  initialMessages,
  messagesAtom,
  textAtom,
  textStatusAtom,
  lastDoneMessageKeyAtom,
  selectedNodeAtom,
} from "../../../lib/atoms";
import { getChatSessionDetails, setActiveChatSession } from "../../../data/api";
import Messages from "./Messages";
import InputArea from "./ChatInput";

function mapRestoredMessages(sessionMessages) {
  const restoredMessages = sessionMessages.map((message, index) => ({
    key: index + 1,
    value: message.content,
    name: message.role,
  }));

  return restoredMessages.length > 0
    ? restoredMessages.reverse()
    : [...initialMessages];
}

export default function Chat({
  currentChat,
  setCurrentChat,
  pendingMessage,
  setPendingMessage,
  onTitleUpdate,
}) {
  const [feedbackText, setFeedbackText] = useState("");
  const [showFeedback, setShowFeedback] = useState(true);
  const [sessionReady, setSessionReady] = useState(false);
  const shouldLog = useRef(false);
  const isNewSessionRef = useRef(false);
  const setMessages = useSetAtom(messagesAtom);
  const setText = useSetAtom(textAtom);
  const setStatus = useSetAtom(textStatusAtom);
  const setLastDoneMessageKey = useSetAtom(lastDoneMessageKeyAtom);
  const [selectedNode] = useAtom(selectedNodeAtom);
  const focusNodeLabel = selectedNode?.data
    ? selectedNode?.data.label
    : "No nodes available";

  useEffect(() => {
    let isCurrent = true;

    async function restoreChat() {
      if (isNewSessionRef.current) {
        isNewSessionRef.current = false;
        return;
      }

      setText("");
      setStatus("ready");
      setLastDoneMessageKey(null);
      setFeedbackText("");
      setShowFeedback(true);
      setSessionReady(false);
      shouldLog.current = false;

      const sessionId = currentChat?.session_id;
      if (!sessionId) {
        setMessages([...initialMessages]);

        if (isCurrent) setSessionReady(true);
        return;
      }

      setMessages([]);

      try {
        await setActiveChatSession(sessionId);
        const details = await getChatSessionDetails(sessionId);
        if (!isCurrent) return;

        setMessages(
          details?.messages ? mapRestoredMessages(details.messages) : []
        );
        setSessionReady(true);
      } catch (err) {
        console.error("Error restoring chat session:", err);
      }
    }

    restoreChat();

    return () => {
      isCurrent = false;
    };
  }, [
    currentChat?.session_id,
    setLastDoneMessageKey,
    setMessages,
    setStatus,
    setText,
  ]);

  return (
    <div className="relative z-10 flex h-full flex-col bg-white">
      <div className="min-h-0 flex-1 overflow-hidden">
        <Messages
          feedbackText={feedbackText}
          showFeedback={showFeedback}
          setFeedbackText={setFeedbackText}
          setShowFeedback={setShowFeedback}
          shouldLog={shouldLog}
          showSystemMessages={false} //TODO: controlled by settings menu
        />
      </div>

      <div className="shrink-0 border-t border-gray-200 bg-white">
        <div className="text-primary ms-5 w-min truncate pt-1 text-xs hover:cursor-default">
          <p className="italic">Focus: {focusNodeLabel}</p>
        </div>
        <InputArea
          setShowFeedback={setShowFeedback}
          shouldLog={shouldLog}
          initialText={pendingMessage}
          setPendingMessage={setPendingMessage}
          sessionReady={sessionReady}
          isNewSessionRef={isNewSessionRef}
          setCurrentChat={setCurrentChat}
          currentChat={currentChat}
          onTitleUpdate={onTitleUpdate}
        />
      </div>
    </div>
  );
}
