"use client";

import { useState, useRef, useEffect } from "react";

import {
  PromptInput,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
} from "@/components/shadcn-io/ai/prompt-input";

import { Response } from "@/components/shadcn-io/ai/response";
import { Message, MessageContent } from "@/components/shadcn-io/ai/message";

import {
  Conversation,
  ConversationContent,
} from "@/components/shadcn-io/ai/conversation";

import { useAtom, useAtomValue, useSetAtom } from "jotai";
import {
  messagesAtom,
  textAtom,
  textStatusAtom,
  lastDoneMessageKeyAtom,
  selectedNodeAtom,
} from "./data/atoms";

import { useChatWebSocket } from "./data/chatWebsocket";
import {
  Reasoning,
  ReasoningTrigger,
} from "@/components/shadcn-io/ai/reasoning";
import { Action, Actions } from "@/components/shadcn-io/ai/actions";
import { ThumbsUpIcon, ThumbsDownIcon } from "lucide-react";
import { logResponseFeedback, logEvent } from "./data/api";
import LogOutButton from "@/components/LogOutButton.jsx";

async function handleFeedback(
  messageKey,
  feedback,
  setShowFeedback,
  setFeedbackText
) {
  setShowFeedback(false);
  const response = await logResponseFeedback(messageKey, feedback);
  if (response === null) {
    setFeedbackText(
      "An error occurred while sending your feedback. Please try again."
    );
    return;
  }
  setFeedbackText(response);
}

export default function Chat() {
  const [feedbackText, setFeedbackText] = useState("");
  const [showFeedback, setShowFeedback] = useState(true);
  const shouldLog = useRef(false);
  const [selectedNode] = useAtom(selectedNodeAtom);
  const focusNodeLabel = selectedNode?.data
    ? selectedNode?.data.label
    : "No nodes available";
  return (
    <div className="relative z-10 flex h-full flex-col bg-white">
      {/* Header with logout */}
      <div className="flex shrink-0 justify-end border-b border-gray-200 bg-white px-4 py-2">
        <LogOutButton />
      </div>

      {/* Messages - scrollable */}
      <div className="min-h-0 flex-1 overflow-hidden">
        <Messages
          feedbackText={feedbackText}
          showFeedback={showFeedback}
          setFeedbackText={setFeedbackText}
          setShowFeedback={setShowFeedback}
          shouldLog={shouldLog}
          showSystemMessages={false}
        />
      </div>

      {/* Input - sticky at bottom */}
      <div className="shrink-0 border-t border-gray-200 bg-white">
        <div className="ms-5 w-min truncate pt-1 text-xs text-[#038061] hover:cursor-default">
          <p className="italic">Focus: {focusNodeLabel}</p>
        </div>
        <InputArea setShowFeedback={setShowFeedback} shouldLog={shouldLog} />
      </div>
    </div>
  );
}

function InputArea({ setShowFeedback, shouldLog }) {
  const [text, setText] = useAtom(textAtom);
  const [status, setStatus] = useAtom(textStatusAtom);
  const setMessages = useSetAtom(messagesAtom);

  const { send } = useChatWebSocket(setStatus);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text || status !== "ready") return;

    shouldLog.current = true;

    setMessages((prev) => [
      { key: prev.length + 1, value: text, name: "user" },
      ...prev,
    ]);

    setStatus("thinking");
    send(text);
    setText("");
    setShowFeedback(true);
  };

  return (
    <div className="w-full p-4">
      <PromptInput onSubmit={handleSubmit} className="flex items-center">
        <PromptInputTextarea
          onChange={(e) => setText(e.target.value)}
          value={text}
          placeholder="Type your message..."
          className="flex-1"
        />
        <PromptInputToolbar className="ml-2">
          <PromptInputSubmit
            disabled={!text || status !== "ready"}
            status={status === "thinking" ? "submitted" : status}
            style={{ backgroundColor: "#038061", color: "white" }}
          />
        </PromptInputToolbar>
      </PromptInput>
    </div>
  );
}

function Messages({
  feedbackText,
  showFeedback,
  setFeedbackText,
  setShowFeedback,
  shouldLog,
  showSystemMessages,
}) {
  const messages = useAtomValue(messagesAtom);
  const status = useAtomValue(textStatusAtom);
  const lastDoneKey = useAtomValue(lastDoneMessageKeyAtom);
  const selectedNode = useAtomValue(selectedNodeAtom);
  const prevStatusRef = useRef(null);

  // Log response_generated event
  useEffect(() => {
    const prevStatus = prevStatusRef.current;
    prevStatusRef.current = status;

    if (status !== "ready" || !["thinking", "streaming"].includes(prevStatus))
      return;
    if (!lastDoneKey) return;
    if (!shouldLog.current) return;
    shouldLog.current = false;

    const chronological = [...messages].reverse();
    const botIndex = chronological.findIndex(({ key }) => key === lastDoneKey);
    const question = botIndex > 0 ? chronological[botIndex - 1]?.value : null;

    logEvent("response_generated", {
      messageKey: lastDoneKey,
      question,
      selectedNodeId: selectedNode?.id ?? null,
      selectedNodeLabel: selectedNode?.data?.label ?? null,
      timestamp: new Date().toISOString(),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, lastDoneKey, messages]);

  const reversedMessages = [...messages].reverse();
  const lastDoneIndex = reversedMessages.findIndex(
    ({ key }) => key === lastDoneKey
  );
  const lastDoneMessage = reversedMessages.find(
    ({ key }) => key === lastDoneKey
  );
  const questionForFeedback =
    lastDoneIndex !== -1 && lastDoneIndex + 1 < reversedMessages.length
      ? reversedMessages[lastDoneIndex + 1]?.value
      : null;

  return (
    <Conversation className="h-full">
      <ConversationContent className="flex min-h-full flex-col gap-4 p-4">
        <div className="flex-1" />
        {reversedMessages
          .filter(({ name }) =>
            showSystemMessages ? true : name !== "system_prompt"
          )
          .map(({ key, value, name }) => {
            if (name === "system_prompt") {
              return (
                <div
                  key={key}
                  className="flex w-full items-start justify-start gap-2 pr-[5%]">
                  <div className="flex w-full flex-col items-start">
                    <Response className="w-full rounded-lg border border-gray-200 bg-gray-50 p-2 text-sm wrap-break-word">
                      {value}
                    </Response>
                  </div>
                </div>
              );
            }

            if (name === "chatbot") {
              return (
                <div
                  key={key}
                  className="flex w-full items-start justify-start gap-2 pr-[5%]">
                  <div className="flex w-full flex-col items-start">
                    <Response className="w-full rounded-lg border border-gray-200 bg-gray-50 p-2 text-sm wrap-break-word">
                      {value}
                    </Response>
                    {key === lastDoneKey &&
                      status === "ready" &&
                      lastDoneMessage?.name === "chatbot" && (
                        <div
                          onClick={(e) => e.stopPropagation()}
                          onSubmit={(e) => e.preventDefault()}
                          className="mt-1 ml-7">
                          {questionForFeedback && (
                            <p className="mb-1 text-xs text-gray-400 italic">
                              Feedback for: "
                              {questionForFeedback.length > 80
                                ? questionForFeedback.slice(0, 80) + "…"
                                : questionForFeedback}
                              "
                            </p>
                          )}
                          <Actions>
                            {showFeedback ? (
                              <>
                                <Action
                                  label="Good response"
                                  style={{
                                    backgroundColor: "#038061",
                                    color: "white",
                                  }}
                                  onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    handleFeedback(
                                      key,
                                      "positive",
                                      setShowFeedback,
                                      setFeedbackText
                                    );
                                  }}>
                                  <ThumbsUpIcon className="size-4" />
                                </Action>
                                <Action
                                  label="Bad response"
                                  style={{
                                    backgroundColor: "#038061",
                                    color: "white",
                                  }}
                                  onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    handleFeedback(
                                      key,
                                      "negative",
                                      setShowFeedback,
                                      setFeedbackText
                                    );
                                  }}>
                                  <ThumbsDownIcon className="size-4" />
                                </Action>
                              </>
                            ) : (
                              <>
                                <p className="text-sm text-gray-600">
                                  {feedbackText}
                                </p>
                                <button
                                  type="button"
                                  onClick={() => setShowFeedback(true)}
                                  className="cursor-pointer border-0 p-0 text-sm hover:underline"
                                  style={{
                                    color: "white",
                                    backgroundColor: "#038061",
                                  }}>
                                  Edit Feedback
                                </button>
                              </>
                            )}
                          </Actions>
                        </div>
                      )}
                  </div>
                </div>
              );
            }

            return (
              <Message
                from="user"
                key={key}
                className="flex justify-end pl-[5%]">
                <MessageContent
                  className="max-w-prose wrap-break-word"
                  style={{ backgroundColor: "#038061", color: "#ffffff" }}>
                  {value}
                </MessageContent>
              </Message>
            );
          })}
        {status === "thinking" && (
          <div>
            <Reasoning isStreaming={status === "thinking"}>
              <ReasoningTrigger
                style={{
                  backgroundColor: "transparent",
                  color: "black",
                  border: "none",
                  padding: "0",
                  outline: "none",
                  cursor: "text",
                }}>
                🧠 Thinking...
              </ReasoningTrigger>
            </Reasoning>
          </div>
        )}
      </ConversationContent>
    </Conversation>
  );
}
