"use client"

import { useState } from "react"

import { Conversation } from "@/components/shadcn-io/ai/conversation";
import { Message } from "@/components/shadcn-io/ai/message";
import { PromptInput } from "@/components/shadcn-io/ai/prompt-input";
import {Response} from "@/components/shadcn-io/ai/response";
export  function ChatAI() {
  const [messages, setMessages] = useState([])

  const handleSend = (prompt) => {
    if (!prompt.trim()) return

    const userMessage = {
      id: Date.now() + "-u",
      role: "user",
      content: prompt,
    }

    const botMessage = {
      id: Date.now() + "-b",
      role: "assistant",
      content: "🤖 This is a fake bot response — no AI used!",
    }

    setMessages((prev) => [...prev, userMessage, botMessage])
  }
  console.log({ Conversation, Message, Response, PromptInput })

  return (
    <>
    <div className="text-red-500 text-2xl">Hello Tailwind!</div>
      <div className="flex-1 overflow-hidden">
        <Conversation>
          {messages.map((msg) =>
            msg.role === "user" ? (
              <Message key={msg.id} from="user">
                {msg.content}
              </Message>
            ) : (
              <Message key={msg.id} from="assistant">
                <Response>{msg.content}</Response>
              </Message>
            )
          )}
        </Conversation>
      </div>

      <PromptInput
        placeholder="Type your message..."
        onSubmit={(value) => handleSend(value)}
      />
    </>
  )
}
