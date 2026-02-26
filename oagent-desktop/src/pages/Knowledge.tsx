import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Database, Upload, File, Trash2, Search } from 'lucide-react'

interface Document {
  id: string
  name: string
  size: string
  uploadedAt: string
}

export default function Knowledge() {
  const [documents, setDocuments] = useState<Document[]>([
    { id: '1', name: 'product-manual.pdf', size: '2.4 MB', uploadedAt: '2024-01-15' },
    { id: '2', name: 'company-policies.docx', size: '156 KB', uploadedAt: '2024-01-14' },
  ])

  const [knowledgeBases] = useState([
    { id: '1', name: 'Documentation', documents: 5, embeddings: 234 },
    { id: '2', name: 'Support FAQs', documents: 12, embeddings: 567 },
  ])

  return (
    <div className="h-full overflow-auto">
      <div className="container mx-auto p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">Knowledge Base</h1>
          <p className="text-muted-foreground mt-2">
            Manage your documents and embeddings for RAG
          </p>
        </div>

        {/* Knowledge Bases */}
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Knowledge Bases</h2>
            <Button>
              <Database className="h-4 w-4 mr-2" />
              New Knowledge Base
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {knowledgeBases.map((kb) => (
              <Card key={kb.id} className="hover:border-primary/50 transition-colors cursor-pointer">
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Database className="h-5 w-5 text-primary" />
                    <CardTitle className="text-lg">{kb.name}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-4 text-sm text-muted-foreground">
                    <span>{kb.documents} documents</span>
                    <span>{kb.embeddings} embeddings</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Upload Section */}
        <Card>
          <CardHeader>
            <CardTitle>Upload Documents</CardTitle>
            <CardDescription>
              Add documents to your knowledge base for RAG
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="border-2 border-dashed rounded-lg p-8 text-center">
              <Upload className="h-10 w-10 text-muted-foreground mx-auto mb-4" />
              <p className="text-sm text-muted-foreground mb-4">
                Drag and drop files here, or click to browse
              </p>
              <Input type="file" className="hidden" id="file-upload" multiple />
              <label htmlFor="file-upload">
                <Button variant="outline" className="cursor-pointer" asChild>
                  <span>Browse Files</span>
                </Button>
              </label>
              <p className="text-xs text-muted-foreground mt-2">
                Supported: PDF, DOCX, TXT, MD, HTML
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Documents List */}
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Documents</h2>
            <div className="flex gap-2">
              <Input placeholder="Search documents..." className="w-64" />
              <Button variant="outline" size="icon">
                <Search className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <Card>
            <CardContent className="p-0">
              <div className="divide-y">
                {documents.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-3">
                      <File className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium">{doc.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {doc.size} • Uploaded {doc.uploadedAt}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm">
                        Process
                      </Button>
                      <Button variant="ghost" size="icon" className="text-destructive">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}