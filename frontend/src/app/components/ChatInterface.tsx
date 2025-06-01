"use client"

import type React from "react"
import { useState, useRef, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import ChatMessage from "./ChatMessage"
import { streamQuery } from "../services/api"

interface Message {
  text: string
  isAI: boolean
  status?: string
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Load messages from localStorage on component mount
  useEffect(() => {
    const storedMessages = localStorage.getItem("chatMessages")
    if (storedMessages) {
      try {
        const parsedMessages = JSON.parse(storedMessages)
        const formattedMessages = parsedMessages.map((msg: any) => ({
          text: msg.content,
          isAI: msg.role === "assistant",
        }))
        setMessages(formattedMessages)
      } catch (error) {
        console.error("Error parsing stored messages:", error)
      }
    }
  }, [])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto"
      inputRef.current.style.height = `${inputRef.current.scrollHeight}px`
    }
  }, [input])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = { text: input, isAI: false }
    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    if (inputRef.current) {
      inputRef.current.style.height = "auto"
    }

    try {
      for await (const message of streamQuery(input)) {
        if (message.type === "status") {
          setMessages((prev) => [
            ...prev.filter((msg) => !msg.status),
            { text: "", isAI: true, status: message.content },
          ])
        } else if (message.type === "content") {
          setMessages((prev) => [...prev.filter((msg) => !msg.status), { text: message.content, isAI: true }])
        } else if (message.type === "error") {
          setMessages((prev) => [
            ...prev.filter((msg) => !msg.status),
            { text: `Error: ${message.content}`, isAI: true },
          ])
        }
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev.filter((msg) => !msg.status),
        { text: "An error occurred while processing your request.", isAI: true },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="mx-auto w-full">
          <h1 className="text-lg font-semibold text-gray-800">Repello AI</h1>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 relative">
        <div className="max-w-3xl mx-auto w-full space-y-6">
          <AnimatePresence>
            {messages.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="absolute inset-0 flex flex-col items-center justify-center text-center text-gray-500 space-y-4"
              >
                <div className="w-16 h-16 bg-blue-100 flex items-center justify-center rounded-full">
                  <svg
                    className="w-8 h-8 text-blue-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                    />
                  </svg>
                </div>
                <div>
                  <h2 className="text-xl font-semibold mb-2">Welcome to Research Assistant</h2>
                  <p className="text-sm max-w-md mx-auto">
                    I can help you research any topic by searching the web and synthesizing information from multiple sources.
                  </p>
                </div>
              </motion.div>
            ) : (
              messages.map((message, index) => (
                <ChatMessage
                  key={index}
                  message={message.text}
                  isAI={message.isAI}
                  status={message.status}
                />
              ))
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Form */}
      <div className="px-4 py-4">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto w-full">
          <div className="flex gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask your research question..."
              className="flex-1 pl-4 pr-4 py-3 text-sm border rounded-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 resize-none overflow-y-auto"
              style={{ 
                height: '44px',
                maxHeight: '44px'
              }}
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
            >
              {isLoading ? (
                <div className="flex items-center space-x-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-white animate-bounce" />
                  <div className="w-1.5 h-1.5 rounded-full bg-white animate-bounce" style={{ animationDelay: '0.2s' }} />
                  <div className="w-1.5 h-1.5 rounded-full bg-white animate-bounce" style={{ animationDelay: '0.4s' }} />
                </div>
              ) : (
                'Send'
              )}
            </button>
          </div>
          <p className="mt-2 text-xs text-gray-500 text-center">
            Press Enter to send, Shift + Enter for new line
          </p>
        </form>
      </div>
    </div>
  )
}

export default ChatInterface
