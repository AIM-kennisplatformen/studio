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
import { useAtom, useAtomValue, useSetAtom } from "jotai";
import { useRef, useEffect } from 'react';
import { messagesAtom, textAtom, textStatusAtom } from "./data/atoms";

  
export default function Chat(){
  
  return (
    <div className="flex flex-col min-h-screen bg-white">
      {/* messages area grows and scrolls; add bottom padding to avoid being hidden by the sticky input */}
      <div className="flex-1 overflow-auto pb-24">
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
  const streamTimerRef = useRef(null);
  const responseTimerRef = useRef(null);
  const userMessageKeyRef = useRef(null);

  const standardChatbotResponse = {
    value: 'I\'ll look it up!',
    name: 'chatbot'
  }
  const handleSubmit = (event) => {
    event.preventDefault();

    if (!text) {
      return;
    }
    const newMessage = {
        value: text,
        name: 'user'
      };

    // clear any existing timers
    if (streamTimerRef.current) {
      clearTimeout(streamTimerRef.current);
      streamTimerRef.current = null;
    }
    if (responseTimerRef.current) {
      clearTimeout(responseTimerRef.current);
      responseTimerRef.current = null;
    }

    // create a stable key for this user message and append immediately
    const userKey = Date.now();
    userMessageKeyRef.current = userKey;
    setMessages(msg => [...msg, { key: userKey, ...newMessage }]);
    setStatus('submitted');

    // schedule streaming state
    streamTimerRef.current = setTimeout(() => {
      setStatus('streaming');
    }, 200);

    // schedule bot response (can be cancelled by stop)
    responseTimerRef.current = setTimeout(() => {
      setStatus('ready');
      setText('');
      setMessages(msg => [...msg, { key: Date.now(), ...standardChatbotResponse }]);
      // clear the stored user message key since response completed
      userMessageKeyRef.current = null;
      responseTimerRef.current = null;
      streamTimerRef.current = null;
    }, 2000);
  };

  // Handler for clicks on submit button; if streaming, treat as Stop
  const handleSubmitClick = (e) => {
    if (status === 'streaming') {
      // prevent the form submission and cancel streaming
      e.preventDefault();
      e.stopPropagation();
      if (streamTimerRef.current) {
        clearTimeout(streamTimerRef.current);
        streamTimerRef.current = null;
      }
      if (responseTimerRef.current) {
        clearTimeout(responseTimerRef.current);
        responseTimerRef.current = null;
      }
      // remove the user's message that was just appended
      if (userMessageKeyRef.current) {
        const keyToRemove = userMessageKeyRef.current;
        setMessages(msg => msg.filter(m => m.key !== keyToRemove));
        userMessageKeyRef.current = null;
      }
      setStatus('ready');
      return;
    }
    // otherwise allow the click to submit the form normally (onSubmit will run)
  };

  // cleanup timers when component unmounts
  useEffect(() => {
    return () => {
      if (streamTimerRef.current) {
        clearTimeout(streamTimerRef.current);
        streamTimerRef.current = null;
      }
      if (responseTimerRef.current) {
        clearTimeout(responseTimerRef.current);
        responseTimerRef.current = null;
      }
    };
  }, []);

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
          <PromptInputSubmit disabled={!text} status={status} onClick={handleSubmitClick} />
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
      <ConversationScrollButton />
    </Conversation>)
  ;
}
