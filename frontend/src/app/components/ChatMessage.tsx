"use client"

import type React from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { motion } from "framer-motion"
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter"
import { atomDark } from "react-syntax-highlighter/dist/esm/styles/prism"

interface ChatMessageProps {
  message: string
  isAI: boolean
  status?: string
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, isAI, status }) => {
  if (status) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-center py-4 text-gray-500"
      >
        <div className="flex items-center space-x-2">
          <div className="animate-pulse h-2 w-2 rounded-full bg-blue-500"></div>
          <div className="animate-pulse h-2 w-2 rounded-full bg-blue-500" style={{ animationDelay: "0.2s" }}></div>
          <div className="animate-pulse h-2 w-2 rounded-full bg-blue-500" style={{ animationDelay: "0.4s" }}></div>
          <span className="ml-2 text-sm font-medium">{status}</span>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex mb-4 ${isAI ? "justify-start" : "justify-end"}`}
    >
      <div
        className={`rounded-xl px-6 py-3 max-w-[85%] ${
          isAI
            ? 'bg-white border border-gray-200'
            : 'bg-blue-600 text-white'
        }`}
      >
        {isAI ? (
          <div className="prose prose-sm max-w-none dark:prose-invert leading-relaxed">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code(props) {
                  const {className, children, ...rest} = props;
                  const match = /language-(\w+)/.exec(className || '');
                  return match ? (
                    <div className="rounded-md overflow-hidden my-2">
                      <SyntaxHighlighter
                        style={atomDark}
                        language={match[1]}
                        PreTag="div"
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    </div>
                  ) : (
                    <code className={`${className} bg-gray-100 rounded px-1 py-0.5`} {...rest}>
                      {children}
                    </code>
                  );
                },
                a(props) {
                  const {href, children} = props;
                  return (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 underline decoration-blue-400 hover:decoration-blue-600"
                    >
                      {children}
                    </a>
                  );
                },
                p(props) {
                  return (
                    <p className="mb-3 last:mb-0" {...props} />
                  );
                }
              }}
            >
              {message}
            </ReactMarkdown>
          </div>
        ) : (
          <p className="text-sm whitespace-pre-wrap leading-relaxed">{message}</p>
        )}
      </div>
    </motion.div>
  )
}

export default ChatMessage
