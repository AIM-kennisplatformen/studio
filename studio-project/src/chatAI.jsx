"use client"

import {
  PromptInput,

  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
} from '@/components/shadcn-io/ai/prompt-input';

import { Message, MessageContent, MessageAvatar } from "@/components/shadcn-io/ai/message";
import { Conversation, ConversationContent, ConversationScrollButton } from "@/components/shadcn-io/ai/conversation";
import { avatars } from "./data/avatars";
import { useAtom, useAtomValue } from "jotai";
import { useEffect, useRef } from 'react';
import { messagesAtom, textAtom, textStatusAtom, timerAtom } from "./data/atoms";

  
export default function Chat(){
  
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
  const [messages, setMessages] = useAtom(messagesAtom);
  const [timers, setTimers] = useAtom(timerAtom);
  const containerRef = useRef(null);

  const standardChatbotResponse = {
    value: 'I\'ll look it up!',
    name: 'chatbot'
  }
  const clearTimers = () => {
    if (timers.stream) clearTimeout(timers.stream);
    if (timers.response) clearTimeout(timers.response);
    setTimers({ stream: null, response: null });
  }

  const handleSubmit = (e) => {
    e.preventDefault();
    // If no input → ignore
    if (!text) return;

    // If currently streaming → stop
    if (status === "streaming") {
      clearTimers();
      setMessages((prev) => prev.filter((m) => m.key !== prev.length));
      setStatus("ready");
      return;
    }



    // Send new message
    clearTimers();
    setMessages((prev) => [...prev, { key: prev.length+1, value: text, name: "user" }]);
    setStatus("submitted");
    const streamTimer = setTimeout(() => setStatus("streaming"), 200);
    const responseTimer = setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { key: prev.length+1, ...standardChatbotResponse },
      ]);
      setText("");
      setStatus("ready");
      clearTimers();
    }, 2000);

    setTimers({ stream: streamTimer, response: responseTimer });
  };

  useEffect(() => clearTimers, []);

   useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className='p-4 w-full'>
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
  const data = messages.map(msg => {
    const avatar = avatars.find(a => a.name == msg.name);
    return {
        ...msg,
        avatar: avatar ? avatar.link: null
    };
  })
  return (
<Conversation >
      <ConversationContent>
        {data.map(({key, value, name, avatar}) => (
          <Message from={name === 'chatbot' ? 'chatbot' : 'user'} key={key}>
            <MessageContent>{value}</MessageContent>
            <MessageAvatar name={name} src={avatar} />
          </Message>
        ))}
      </ConversationContent>
      <ConversationScrollButton className=" text-white hover:text-white" />
    </Conversation>)
  ;
}
