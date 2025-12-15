"use client";

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
  ConversationScrollButton,
} from "@/components/shadcn-io/ai/conversation";

import { useAtom, useAtomValue, useSetAtom } from "jotai";
import {
  messagesAtom,
  textAtom,
  textStatusAtom,
} from "./data/atoms";

import { useChatWebSocket } from "./data/chatWebsocket";
import { useRef, useEffect } from "react";

export default function Chat() {
  return (
    <div className="flex flex-col min-h-screen bg-white">
      {/* Messages container */}
      <div className="flex flex-col overflow-y-auto p-4 flex-1 pb-5">
        <Messages />
      </div>

      {/* Sticky bottom input bar */}
      <div className="w-full bg-white border-t sticky bottom-0 z-10">
        <InputArea />
      </div>
    </div>
  );
}

function InputArea() {
  const [text, setText] = useAtom(textAtom);
  const [status, setStatus] = useAtom(textStatusAtom);
  const setMessages = useSetAtom(messagesAtom);

  // WebSocket connection
  const { send } = useChatWebSocket(setStatus);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text) return;

    // Add user message instantly
    setMessages((prev) => [
      { key: prev.length + 1, value: text, name: "user" },
      ...prev,
    ]);

    // Update UI state
    setStatus("streaming");

    // Send to WebSocket server
    send(text);

    // Clear input
    setText("");
  };

  return (
    <div className="p-4 w-full">
      <PromptInput onSubmit={handleSubmit} className="flex items-center">
        <PromptInputTextarea
          onChange={(e) => setText(e.target.value)}
          value={text}
          placeholder="Type your message..."
          className="flex-1"
        />

        <PromptInputToolbar className="ml-2">
          <PromptInputSubmit
            disabled={!text}
            status={status}
            style={{ backgroundColor: "#038061", color: "white" }}
          />
        </PromptInputToolbar>
      </PromptInput>
    </div>
  );
}

function Messages() {
  const messages = useAtomValue(messagesAtom);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <Conversation>
      <ConversationContent className="flex flex-col justify-end overflow-y-auto h-full">
        {[...messages].reverse().map(({ key, value, name }) =>
          name === "chatbot" ? (
            <div key={key} className="flex items-start gap-2 justify-start pr-20">
              <Response className="max-w-prose text-sm border border-gray-200 rounded-lg p-2 bg-gray-50 w-fit break-words">
                {value}
              </Response>
            </div>
          ) : (
            <Message
              from="user"
              key={key}
              className="flex justify-end pl-20"
            >
              <MessageContent
                className="max-w-prose break-words"
                style={{ backgroundColor: "#038061", color: "#ffffff" }}
              >
                {value}
              </MessageContent>
            </Message>
          )
        )}

        <div ref={bottomRef} />
      </ConversationContent>

      <ConversationScrollButton className="text-white hover:text-white" />
    </Conversation>
  );
}
