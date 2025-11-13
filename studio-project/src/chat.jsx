"use client";

import {
  PromptInput,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
} from "@/components/shadcn-io/ai/prompt-input";

import { Response } from "@/components/shadcn-io/ai/response";

import {
  Message,
  MessageContent,
  MessageAvatar,
} from "@/components/shadcn-io/ai/message";
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/shadcn-io/ai/conversation";
import { avatars } from "./data/avatars";
import { useAtom, useAtomValue, useSetAtom } from "jotai";
import {
  messagesAtom,
  textAtom,
  textStatusAtom,
  timerAtom,
} from "./data/atoms";
import { fetchAnswer } from "./data/chatResponse";

export default function Chat() {
  return (
    <div className="flex flex-col min-h-screen bg-white">
      {/* messages area grows and scrolls; add bottom padding to avoid being hidden by the sticky input */}
      <div className="flex-1 flex flex-col overflow-y-auto">
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

  const handleSubmission = () => {
    // Send user's message
    setMessages((prev) => [
      ...prev,
      { key: prev.length + 1, value: text, name: "user" },
    ]);
    setStatus("submitted");
    setTimeout(() => setStatus("streaming"), 200);

    // Simulate chatbot response after a delay
    const newTimeoutId = setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { key: prev.length + 1, ...fetchAnswer("1", text) },
      ]);

      // Reset states
      setText("");
      setStatus("ready");
      setResponseTimeoutId(null);
      // Clear the ID variable after completion
    }, 2000);
    setResponseTimeoutId(newTimeoutId);
  };

  const handleSubmit = (e) => {
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
          <PromptInputSubmit disabled={!text} status={status} />
        </PromptInputToolbar>
      </PromptInput>
    </div>
  );
}

function Messages() {
  const messages = useAtomValue(messagesAtom);
  const data = messages.map((msg) => {
    const avatar = avatars.find((a) => a.name == msg.name);
    return {
      ...msg,
      avatar: avatar ? avatar.link : null,
    };
  });
  return (
    <Conversation>
      <ConversationContent>
        {data.map(({ key, value, name, avatar }) =>
          name === "chatbot" ? (
            <div key={key} className="flex items-start gap-2">
              <MessageAvatar name={name} src={avatar} />
              <Response>{value}</Response>
            </div>
          ) : (
            <Message from="user" key={key}>
              <MessageContent>{value}</MessageContent>
              <MessageAvatar name={name} src={avatar} />
            </Message>
          )
        )}
      </ConversationContent>
      <ConversationScrollButton className=" text-white hover:text-white" />
    </Conversation>
  );
}
