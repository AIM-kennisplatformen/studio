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
  chatIdAtom,
  messagesAtom,
  textAtom,
  textStatusAtom,
  timerAtom,
} from "./data/atoms";
import { sendChatMessage } from "./data/api";

export default function Chat() {
  return (
    <div className="flex flex-col min-h-screen bg-white">
      {/* messages area grows and scrolls; add bottom padding to avoid being hidden by the sticky input */}
      <div className="flex flex-col overflow-y-auto justify-end p-4 flex-1 pb-5">
        <Messages />
      </div>
      {/* sticky input bar pinned to bottom of the viewport */}
      <div className="w-full bg-white border-t sticky bottom-0 z-10">
        <InputArea />
      </div>
    </div>
  );
}

function InputArea() {
  const chatId = useAtomValue(chatIdAtom);
  const [text, setText] = useAtom(textAtom);
  const [status, setStatus] = useAtom(textStatusAtom);
  const setMessages = useSetAtom(messagesAtom);
  const [responseTimeoutId, setResponseTimeoutId] = useAtom(timerAtom);

  const handleCancel = () => {
    // Clear the pending response timeout, preventing the chatbot message from appearing
    if (responseTimeoutId) clearTimeout(responseTimeoutId);

    // Remove the user's message
    setMessages((prev) => prev.filter((m) => m.key !== prev.length));

    // Reset status and timeout ID
    setStatus("ready");
    setResponseTimeoutId(null);
  };

  const handleSubmission = async () => {
    // Send user's message
    setMessages((prev) => [
      
      { key: prev.length + 1, value: text, name: "user" }, ...prev,
    ]);
    setStatus("submitted");
    setTimeout(() => setStatus("streaming"), 200);

    // Simulate chatbot response after a delay
    const newTimeoutId = setTimeout(async () => {
      const singleMessage = await sendChatMessage(chatId, text);
      setMessages((prev) => [
        
        { key: prev.length + 1, ...singleMessage },...prev,
      ]);

      // Reset states
      setText("");
      setStatus("ready");
      setResponseTimeoutId(null);
      // Clear the ID variable after completion
    }, 2000);
    setResponseTimeoutId(newTimeoutId);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    // If no input → ignore
    if (!text) return;

    // If currently streaming and user presses stop button
    if (status === "streaming") {
      handleCancel();
    } else {
      handleSubmission();
    }
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
  return (
        <div className="flex flex-cole">
    <Conversation >
      <ConversationContent className="flex flex-col-reverse">
        {messages.map(({ key, value, name }) =>
          name === "chatbot" ? (
            <div key={key} className="flex items-start gap-2 justify-start pr-20">
              <Response className="max-w-prose text-sm border border-gray-200 rounded-lg p-2 bg-gray-50  w-fit break-words">
                {value}
              </Response>
            </div>
          ) : (
            <Message from="user" key={key} className="flex justify-end pl-20">
              <MessageContent
                className="max-w-prose break-words"
                style={{ backgroundColor: "#038061", color: "#ffffff" }}
              >
                {value}
              </MessageContent>
            </Message>
          )
        )}
      </ConversationContent>
      <ConversationScrollButton className=" text-white hover:text-white" />
    </Conversation>
    </div>
  );
}
