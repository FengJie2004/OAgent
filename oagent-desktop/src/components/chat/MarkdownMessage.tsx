/**
 * MarkdownMessage Component
 *
 * Renders chat messages with markdown support, syntax highlighting,
 * and copy-to-clipboard functionality.
 */

import React, { useState, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { Check, Copy, Bot, User } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ChatMessage } from '@/stores/chatStore'

// Import highlight.js styles
import 'highlight.js/styles/github-dark.css'

interface MarkdownMessageProps {
  message: ChatMessage
}

/**
 * Code block renderer with copy button
 */
function CodeBlock({
  language,
  children,
}: {
  language?: string
  children: string
}) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(children)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy code:', error)
    }
  }, [children])

  return (
    <div className="relative my-4 rounded-lg overflow-hidden border border-border bg-muted">
      {/* Code block header */}
      <div className="flex items-center justify-between px-4 py-2 bg-muted/80 border-b border-border">
        <span className="text-xs text-muted-foreground font-mono">
          {language || 'code'}
        </span>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="h-7 text-xs hover:bg-background"
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5 mr-1" />
              Copied!
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5 mr-1" />
              Copy
            </>
          )}
        </Button>
      </div>
      {/* Code content */}
      <pre className="p-4 overflow-x-auto">
        <code className={`language-${language || 'text'}`}>{children}</code>
      </pre>
    </div>
  )
}

/**
 * Custom renderer for code blocks
 */
function renderCodeBlock(props: {
  className?: string
  children: React.ReactNode
  inline?: boolean
}) {
  const { className, children, inline } = props

  if (inline) {
    return (
      <code className="px-1.5 py-0.5 rounded bg-muted text-sm font-mono">
        {children}
      </code>
    )
  }

  const match = /language-(\w+)/.exec(className || '')
  const language = match ? match[1] : undefined

  return (
    <CodeBlock language={language}>
      {String(children).replace(/\n$/, '')}
    </CodeBlock>
  )
}

/**
 * Format timestamp for display
 */
function formatTime(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

/**
 * Message avatar component
 */
function MessageAvatar({ role }: { role: ChatMessage['role'] }) {
  if (role === 'user') {
    return (
      <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center flex-shrink-0">
        <User className="h-4 w-4" />
      </div>
    )
  }

  if (role === 'tool') {
    return (
      <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0">
        <Bot className="h-4 w-4 text-blue-500" />
      </div>
    )
  }

  return (
    <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
      <Bot className="h-4 w-4 text-primary-foreground" />
    </div>
  )
}

/**
 * Main MarkdownMessage component
 */
export function MarkdownMessage({ message }: MarkdownMessageProps) {
  const { role, content, created_at } = message
  const isUser = role === 'user'

  return (
    <div
      className={cn(
        'flex gap-3 group',
        isUser && 'justify-end'
      )}
    >
      {!isUser && <MessageAvatar role={role} />}

      <div
        className={cn(
          'rounded-lg px-4 py-3 max-w-[80%] relative',
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted'
        )}
      >
        {/* Message content with markdown */}
        <div className={cn(
          'text-sm prose prose-sm dark:prose-invert max-w-none',
          isUser && 'prose-invert'
        )}>
          {isUser ? (
            // User messages - plain text with whitespace preservation
            <p className="whitespace-pre-wrap break-words">{content}</p>
          ) : (
            // Assistant messages - markdown rendering
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
              components={{
                code: renderCodeBlock as never,
                pre: ({ children }) => <>{children}</>, // Don't render pre tags (handled by code)
              }}
            >
              {content}
            </ReactMarkdown>
          )}
        </div>

        {/* Streaming indicator */}
        {message.isStreaming && (
          <span className="inline-block w-2 h-4 ml-1 align-middle bg-current animate-pulse" />
        )}

        {/* Timestamp */}
        <p className={cn(
          'text-xs mt-2 opacity-70',
          isUser && 'text-right'
        )}>
          {formatTime(created_at)}
        </p>

        {/* Copy button for assistant messages */}
        {!isUser && content && (
          <CopyButton text={content} />
        )}
      </div>

      {isUser && <MessageAvatar role={role} />}
    </div>
  )
}

/**
 * Copy button for messages
 */
function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy:', error)
    }
  }, [text])

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={handleCopy}
      className={cn(
        'absolute top-2 right-2 h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity',
        copied && 'opacity-100'
      )}
      title="Copy message"
    >
      {copied ? (
        <Check className="h-3.5 w-3.5 text-green-500" />
      ) : (
        <Copy className="h-3.5 w-3.5" />
      )}
    </Button>
  )
}

export default MarkdownMessage
