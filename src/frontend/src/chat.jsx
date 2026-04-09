"use client";

import {
  PromptInput,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
} from "@/components/shadcn-io/ai/prompt-input";
import { FeedbackButton } from "@/components/FeedbackButton";

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
} from "./data/atoms";

import { useChatWebSocket } from "./data/chatWebsocket";
import { Reasoning, ReasoningTrigger } from "@/components/shadcn-io/ai/reasoning";
import {Action, Actions} from "@/components/shadcn-io/ai/actions";
import { ThumbsUpIcon, ThumbsDownIcon } from "lucide-react";

export default function Chat() {
  return (
    <div className="flex flex-col h-full bg-white">
      {/* Messages container - scrollable */}
      <div className="flex-1 min-h-0 h-full overflow-hidden">
        <Messages />
      </div>

      {/* Bottom row: Feedback button + InputArea - sticky at bottom */}
      <div className="flex border-t border-gray-200 bg-white">
        {/* Left-side Feedback Button */}
        <div className="flex flex-col justify-end -ml-22 pb-18">
          <FeedbackButton />
        </div>

        {/* Input area takes full remaining width */}
        <div className="flex-1 -ml-9">
          <InputArea />
        </div>
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
    if (!text || status !== "ready") return;

    // Add user message instantly
    setMessages((prev) => [
      { key: prev.length + 1, value: text, name: "user" },
        ...prev,

    ]);

    // Update UI state
    setStatus("thinking");

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
            disabled={!text || status !== "ready"}
            status={status === "thinking" ? "submitted" : status}
            style={{ backgroundColor: "#038061", color: "white" }}
          />
        </PromptInputToolbar>
      </PromptInput>
    </div>
  );
}

function Messages() {
  const messages = useAtomValue(messagesAtom);
  const status = useAtomValue(textStatusAtom);
  const lastDoneKey = useAtomValue(lastDoneMessageKeyAtom);

  return (
    <Conversation className="h-full">
      <ConversationContent className="flex flex-col gap-4 p-4 min-h-full">
        <div className="flex-1" />
        {[...messages].reverse().map(({ key, value, name }) =>
          name === "chatbot" ? (
            <div key={key} className="flex items-start gap-2 justify-start pr-20">
              <div className="flex flex-col items-start">
              <Response className="max-w-prose text-sm border border-gray-200 rounded-lg p-2 bg-gray-50 break-words">
                {value}
              </Response>
              {key === lastDoneKey && status === "ready" && (
              <Actions>
                <Action             
                  style={{ backgroundColor: "#038061", color: "white" }}
                  onClick={() => console.log("Thumbs up!")} 
                  tooltip="Good response">
                  <ThumbsUpIcon className="size-4" />
                </Action>
                <Action             
                  style={{ backgroundColor: "#038061", color: "white" }}
                  onClick={() => console.log("Thumbs down!")} tooltip="Bad response">
                    <ThumbsDownIcon className="size-4" />
                </Action>
              </Actions>
              )}
            </div>
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
          {status === "thinking" && (
            <div>
              <Reasoning isStreaming={status === "thinking"}>
                <ReasoningTrigger style={{ backgroundColor: "transparent", color: "black", border: "none", padding: "0", outline: "none", cursor: "text" }}>
                  🧠 Thinking...
                </ReasoningTrigger>
              </Reasoning>
            </div>
          )}
      </ConversationContent>
    </Conversation>
  );
}
