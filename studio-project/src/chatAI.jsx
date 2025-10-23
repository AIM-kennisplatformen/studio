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
import { messagesAtom, textAtom, textStatusAtom } from "./data/atoms";

  
export default function Chat(){
  
  return (
    <div className="flex flex-col min-h-screen bg-white">
      <div className="flex-1 overflow-auto">
        <Messages  />
      </div>
      <div className="w-full bg-white border-t">
        <InputArea />
      </div>
    </div>
  );

}

function InputArea() {
  const [text, setText] = useAtom(textAtom);
  const [status, setStatus] = useAtom(textStatusAtom);
  const setMessages = useSetAtom(messagesAtom);

  const standardChatbotResponse = {
    value: 'I\'ll look it up!',
    name: 'chatbot'
  }
  const handleSubmit = (event) => {
    event.preventDefault();

    if (!text) {
      return;
    }

    setStatus('submitted');

    setTimeout(() => {
      setStatus('streaming');
      const newMessage = {
        value: text,
        name: 'user'
      };
      setMessages(msg => [...msg, {key: msg.length+1, ...newMessage}] );
    }, 200);

    setTimeout(() => {
      setStatus('ready');
      setText('');
      setMessages(msg => [...msg, {key: msg.length+1, ...standardChatbotResponse}]);

    }, 2000);
  };

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
        {data.map(({key, value, name, avatar}, index) => (
            
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
