/**
 * SessionSidebar Component
 *
 * Displays a sidebar with chat session list.
 * Supports session CRUD operations and search.
 */

import { useState } from 'react'
import {
  Plus,
  MessageSquare,
  Trash2,
  Search,
  X,
  Edit2
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ChatSession } from '@/stores/chatStore'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

interface SessionSidebarProps {
  sessions: ChatSession[]
  currentSessionId: string | null
  isLoading: boolean
  onSelectSession: (sessionId: string) => void
  onCreateSession: (title?: string) => void
  onDeleteSession: (sessionId: string) => void
  onClose?: () => void
}

/**
 * Format date to relative time string
 */
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`

  return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

/**
 * Session item component
 */
interface SessionItemProps {
  session: ChatSession
  isActive: boolean
  onSelect: () => void
  onDelete: (e: React.MouseEvent) => void
}

function SessionItem({ session, isActive, onSelect, onDelete }: SessionItemProps) {
  const [showActions, setShowActions] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(session.title || 'Untitled')

  const handleSaveTitle = () => {
    // TODO: Implement title update when backend supports it
    setIsEditing(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSaveTitle()
    } else if (e.key === 'Escape') {
      setEditTitle(session.title || 'Untitled')
      setIsEditing(false)
    }
  }

  return (
    <div
      className={cn(
        'group relative flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm transition-colors cursor-pointer',
        isActive
          ? 'bg-primary text-primary-foreground'
          : 'hover:bg-muted'
      )}
      onClick={onSelect}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <MessageSquare className={cn(
        'h-4 w-4 flex-shrink-0',
        isActive ? 'text-primary-foreground/80' : 'text-muted-foreground'
      )} />

      <div className="flex-1 min-w-0">
        {isEditing ? (
          <Input
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            onBlur={handleSaveTitle}
            onKeyDown={handleKeyDown}
            onClick={(e) => e.stopPropagation()}
            className="h-6 text-sm"
            autoFocus
          />
        ) : (
          <>
            <p className="truncate font-medium">{session.title || 'Untitled'}</p>
            <p className={cn(
              'text-xs truncate',
              isActive ? 'text-primary-foreground/70' : 'text-muted-foreground'
            )}>
              {formatRelativeTime(session.updated_at)}
            </p>
          </>
        )}
      </div>

      {/* Actions */}
      {showActions && !isEditing && (
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              'h-7 w-7',
              isActive ? 'hover:bg-primary-foreground/20' : 'hover:bg-muted'
            )}
            onClick={(e) => {
              e.stopPropagation()
              setIsEditing(true)
            }}
            title="Rename"
          >
            <Edit2 className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              'h-7 w-7 text-destructive hover:text-destructive',
              isActive ? 'hover:bg-primary-foreground/20' : 'hover:bg-muted'
            )}
            onClick={onDelete}
            title="Delete"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}
    </div>
  )
}

/**
 * Delete confirmation dialog
 */
interface DeleteDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: () => void
  sessionTitle?: string
}

function DeleteDialog({ open, onOpenChange, onConfirm, sessionTitle }: DeleteDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>Delete Conversation</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete "{sessionTitle || 'this conversation'}"?
            This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={onConfirm}>
            Delete
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/**
 * Main SessionSidebar component
 */
export function SessionSidebar({
  sessions,
  currentSessionId,
  isLoading,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  onClose,
}: SessionSidebarProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null)

  // Filter sessions by search query
  const filteredSessions = sessions.filter((session) => {
    const title = (session.title || '').toLowerCase()
    return title.includes(searchQuery.toLowerCase())
  })

  const handleDeleteClick = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setSessionToDelete(sessionId)
    setDeleteDialogOpen(true)
  }

  const handleDeleteConfirm = () => {
    if (sessionToDelete) {
      onDeleteSession(sessionToDelete)
      setDeleteDialogOpen(false)
      setSessionToDelete(null)
    }
  }

  const sessionToDeleteData = sessions.find(s => s.id === sessionToDelete)

  return (
    <>
      <div className="flex flex-col h-full bg-muted/30 border-r">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="font-semibold text-lg">Conversations</h2>
          {onClose && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 lg:hidden"
              onClick={onClose}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* New Chat Button */}
        <div className="p-4 border-b">
          <Button
            className="w-full"
            onClick={() => onCreateSession()}
          >
            <Plus className="h-4 w-4 mr-2" />
            New Chat
          </Button>
        </div>

        {/* Search */}
        <div className="p-3 border-b">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 h-9"
            />
            {searchQuery && (
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-1 top-1 h-7 w-7"
                onClick={() => setSearchQuery('')}
              >
                <X className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
        </div>

        {/* Session List */}
        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <p className="text-muted-foreground">Loading sessions...</p>
              </div>
            ) : filteredSessions.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <MessageSquare className="h-8 w-8 text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">
                  {searchQuery ? 'No matching conversations' : 'No conversations yet'}
                </p>
                {!searchQuery && (
                  <Button
                    variant="link"
                    className="text-sm"
                    onClick={() => onCreateSession()}
                  >
                    Start a new chat
                  </Button>
                )}
              </div>
            ) : (
              filteredSessions.map((session) => (
                <SessionItem
                  key={session.id}
                  session={session}
                  isActive={session.id === currentSessionId}
                  onSelect={() => onSelectSession(session.id)}
                  onDelete={(e) => handleDeleteClick(session.id, e)}
                />
              ))
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Delete Confirmation Dialog */}
      <DeleteDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        onConfirm={handleDeleteConfirm}
        sessionTitle={sessionToDeleteData?.title || undefined}
      />
    </>
  )
}

export default SessionSidebar
