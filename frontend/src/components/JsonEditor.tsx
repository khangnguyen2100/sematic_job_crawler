import Editor from '@monaco-editor/react';
import React, { useEffect, useRef, useState } from 'react';
import { Button } from './ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from './ui/dialog';

interface JsonEditorProps {
  data: unknown;
  onSave?: (data: unknown) => void;
  readOnly?: boolean;
  title?: string;
  trigger?: React.ReactNode;
  isOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export const JsonEditor: React.FC<JsonEditorProps> = ({
  data,
  onSave,
  readOnly = false,
  title = "JSON Editor",
  trigger,
  isOpen: controlledIsOpen,
  onOpenChange: controlledOnOpenChange
}) => {
  const [internalIsOpen, setInternalIsOpen] = useState(false);
  const [jsonValue, setJsonValue] = useState('');
  const [error, setError] = useState<string | null>(null);
  const editorRef = useRef<unknown>(null);

  // Use controlled state if provided, otherwise use internal state
  const isOpen = controlledIsOpen !== undefined ? controlledIsOpen : internalIsOpen;
  const onOpenChange = controlledOnOpenChange || setInternalIsOpen;

  useEffect(() => {
    try {
      setJsonValue(JSON.stringify(data, null, 2));
      setError(null);
    } catch (_err) {
      setError('Invalid JSON data provided');
      setJsonValue('{}');
    }
  }, [data, isOpen]);

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      setJsonValue(value);
      
      // Validate JSON
      try {
        JSON.parse(value);
        setError(null);
      } catch (_err) {
        setError('Invalid JSON syntax');
      }
    }
  };

  const handleSave = () => {
    try {
      const parsedData = JSON.parse(jsonValue);
      onSave?.(parsedData);
      onOpenChange(false);
    } catch (_err) {
      setError('Cannot save: Invalid JSON syntax');
    }
  };

  const handleEditorMount = (editor: unknown) => {
    editorRef.current = editor;
  };

  const formatJson = () => {
    try {
      const parsed = JSON.parse(jsonValue);
      const formatted = JSON.stringify(parsed, null, 2);
      setJsonValue(formatted);
      setError(null);
    } catch (_err) {
      setError('Cannot format: Invalid JSON syntax');
    }
  };

  const DialogComponent = (
    <DialogContent className="max-w-4xl max-h-[80vh]">
      <DialogHeader>
        <DialogTitle>{title}</DialogTitle>
        <DialogDescription>
          {readOnly ? "View JSON data" : "Edit JSON data and click save when finished"}
        </DialogDescription>
      </DialogHeader>
      
      <div className="flex flex-col gap-4">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
            {error}
          </div>
        )}
        
        <div className="border rounded-lg overflow-hidden" style={{ height: '400px' }}>
          <Editor
            height="400px"
            defaultLanguage="json"
            value={jsonValue}
            onChange={handleEditorChange}
            onMount={handleEditorMount}
            options={{
              readOnly,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              fontSize: 14,
              lineNumbers: 'on',
              renderWhitespace: 'selection',
              automaticLayout: true,
              formatOnPaste: true,
              formatOnType: true,
            }}
            theme="vs-dark"
          />
        </div>
      </div>

      <DialogFooter className="flex justify-between">
        <div className="flex gap-2">
          {!readOnly && (
            <Button
              type="button"
              variant="outline"
              onClick={formatJson}
              disabled={!!error}
            >
              Format JSON
            </Button>
          )}
        </div>
        
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            {readOnly ? 'Close' : 'Cancel'}
          </Button>
          {!readOnly && onSave && (
            <Button
              type="button"
              onClick={handleSave}
              disabled={!!error}
            >
              Save Changes
            </Button>
          )}
        </div>
      </DialogFooter>
    </DialogContent>
  );

  // If trigger is provided, wrap in Dialog root
  if (trigger) {
    return (
      <Dialog open={isOpen} onOpenChange={onOpenChange}>
        <DialogTrigger asChild>
          {trigger}
        </DialogTrigger>
        {DialogComponent}
      </Dialog>
    );
  }

  // If no trigger, assume parent is handling Dialog root
  return DialogComponent;
};

// Standalone JSON viewer component (non-modal)
interface JsonViewerProps {
  data: unknown;
  height?: string;
  readOnly?: boolean;
}

export const JsonViewer: React.FC<JsonViewerProps> = ({
  data,
  height = '300px',
  readOnly = true
}) => {
  const [jsonValue, setJsonValue] = useState('');

  useEffect(() => {
    try {
      setJsonValue(JSON.stringify(data, null, 2));
    } catch (_err) {
      setJsonValue('{}');
    }
  }, [data]);

  return (
    <div className="border rounded-lg overflow-hidden" style={{ height }}>
      <Editor
        height={height}
        defaultLanguage="json"
        value={jsonValue}
        options={{
          readOnly,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          fontSize: 14,
          lineNumbers: 'on',
          renderWhitespace: 'selection',
          automaticLayout: true,
        }}
        theme="vs-dark"
      />
    </div>
  );
};
