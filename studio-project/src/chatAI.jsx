"use client"

import { useState } from "react"
import {
  PromptInput,

  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
} from '@/components/shadcn-io/ai/prompt-input';

import { Message, MessageContent, MessageAvatar } from "@/components/shadcn-io/ai/message";
import { Conversation, ConversationContent, ConversationScrollButton } from "@/components/shadcn-io/ai/conversation";
import { avatars } from "./avatars";

export default function Chat(){

  return (
    <>
      <Messages />
      <InputArea />
    </>
  );

}

function InputArea() {
  const [text, setText] = useState('');
  const [status, setStatus] = useState('ready');

  const handleSubmit = (event) => {
    event.preventDefault();

    if (!text) {
      return;
    }

    setStatus('submitted');

    setTimeout(() => {
      setStatus('streaming');
    }, 200);

    setTimeout(() => {
      setStatus('ready');
      setText('');
    }, 2000);
  };

  return (
    <div className='p-8 w-full'>
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
    </PromptInput></div>);
  
}


function Messages() {
    const messages =
  [
    {
      key: 1,
      value: 'Hello! How can I help you today?',
      name: 'chatbot',
    },
    {
      key: 2,
      value: "I'd like to learn about React hooks.",
      name: 'user',
    },
    {
      key: 3,
      value: 'Great topic! Which hook interests you most?',
      name: 'chatbot',
    },
    {
      key: 4,
      value: 'useState and useEffect are the most common ones.',
      name: 'user',
    },
    {
      key: 5,
      value: 'Perfect! Let me show you some examples.',
      name: 'chatbot',
    },
    {
      key: 6,
      value: 'That would be really helpful, thanks!',
      name: 'user',
    },
  ];

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
        {data.map(({ key, value, name, avatar}, index) => (
            
          <Message from={index % 2 === 0 ? 'chatbot' : 'user'} key={key}>
            <MessageContent>{value}</MessageContent>
            <MessageAvatar name={name} src={avatar} />
          </Message>
        ))}
      </ConversationContent>
      <ConversationScrollButton />
    </Conversation>)
  ;
}
