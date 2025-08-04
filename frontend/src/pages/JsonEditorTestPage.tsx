import { JsonEditor, JsonViewer } from '@/components/JsonEditor';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog } from '@/components/ui/dialog';
import React, { useState } from 'react';

const JsonEditorTestPage: React.FC = () => {
  const [sampleData, setSampleData] = useState({
    user: {
      id: 1,
      name: "John Doe",
      email: "john.doe@example.com",
      active: true
    },
    preferences: {
      theme: "dark",
      notifications: {
        email: true,
        push: false,
        sms: false
      },
      language: "en-US"
    },
    skills: [
      "JavaScript",
      "TypeScript", 
      "React",
      "Node.js",
      "Python"
    ],
    metadata: {
      createdAt: "2024-01-01T00:00:00Z",
      lastLogin: "2024-12-01T10:30:00Z",
      loginCount: 42
    }
  });

  const [isControlledOpen, setIsControlledOpen] = useState(false);

  const handleSave = (newData: unknown) => {
    setSampleData(newData as typeof sampleData);
    console.log('Data updated:', newData);
    // You could also send this to an API endpoint
    alert('Data saved successfully! Check console for details.');
  };

  return (
    <div className="container mx-auto p-6 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          JSON Editor Components Demo
        </h1>
        <p className="text-gray-600">
          Test the dialog and JSON editor components with interactive examples
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trigger-based JSON Editor */}
        <Card>
          <CardHeader>
            <CardTitle>1. JSON Editor with Trigger</CardTitle>
            <CardDescription>
              Click the button to open a modal JSON editor
            </CardDescription>
          </CardHeader>
          <CardContent>
            <JsonEditor
              data={sampleData}
              onSave={handleSave}
              title="Edit User Data"
              trigger={
                <Button className="w-full">
                  Edit JSON Data
                </Button>
              }
            />
          </CardContent>
        </Card>

        {/* Controlled Dialog */}
        <Card>
          <CardHeader>
            <CardTitle>2. Controlled Dialog</CardTitle>
            <CardDescription>
              Manually control the dialog open/close state
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              className="w-full" 
              variant="outline"
              onClick={() => setIsControlledOpen(true)}
            >
              Open Controlled Editor
            </Button>
            
            <Dialog open={isControlledOpen} onOpenChange={setIsControlledOpen}>
              <JsonEditor
                data={sampleData}
                onSave={handleSave}
                title="Controlled JSON Editor"
                isOpen={isControlledOpen}
                onOpenChange={setIsControlledOpen}
              />
            </Dialog>
          </CardContent>
        </Card>

        {/* Read-only Viewer */}
        <Card>
          <CardHeader>
            <CardTitle>3. Read-only JSON Viewer</CardTitle>
            <CardDescription>
              View JSON data without editing capabilities
            </CardDescription>
          </CardHeader>
          <CardContent>
            <JsonEditor
              data={sampleData}
              readOnly={true}
              title="View User Data (Read-only)"
              trigger={
                <Button variant="secondary" className="w-full">
                  View JSON (Read-only)
                </Button>
              }
            />
          </CardContent>
        </Card>

        {/* Format Test */}
        <Card>
          <CardHeader>
            <CardTitle>4. JSON with Formatting Test</CardTitle>
            <CardDescription>
              Test with unformatted JSON to see the format feature
            </CardDescription>
          </CardHeader>
          <CardContent>
            <JsonEditor
              data={{compressed:true,data:{nested:{value:123}},array:[1,2,3]}}
              onSave={(data) => console.log('Formatted data saved:', data)}
              title="Format JSON Test"
              trigger={
                <Button variant="outline" className="w-full">
                  Edit Unformatted JSON
                </Button>
              }
            />
          </CardContent>
        </Card>
      </div>

      {/* Inline Viewers */}
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>5. Inline JSON Viewer (Read-only)</CardTitle>
            <CardDescription>
              Embedded JSON viewer without modal dialog
            </CardDescription>
          </CardHeader>
          <CardContent>
            <JsonViewer data={sampleData} height="250px" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>6. Inline JSON Viewer (Editable)</CardTitle>
            <CardDescription>
              Embedded JSON editor - changes are not saved automatically
            </CardDescription>
          </CardHeader>
          <CardContent>
            <JsonViewer data={sampleData} height="300px" readOnly={false} />
          </CardContent>
        </Card>
      </div>

      {/* Current Data Display */}
      <Card>
        <CardHeader>
          <CardTitle>Current Data State</CardTitle>
          <CardDescription>
            This shows the current state of the sample data (updates when saved)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="bg-gray-100 p-4 rounded-lg text-sm overflow-auto max-h-64">
            {JSON.stringify(sampleData, null, 2)}
          </pre>
        </CardContent>
      </Card>

      {/* Usage Instructions */}
      <Card>
        <CardHeader>
          <CardTitle>Usage Instructions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-semibold">Features to test:</h4>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 mt-2">
              <li>Edit JSON data in the modal editors and click "Save Changes"</li>
              <li>Use the "Format JSON" button to format messy JSON</li>
              <li>Try entering invalid JSON to see error handling</li>
              <li>Use the read-only viewer to inspect data without editing</li>
              <li>Test the inline editors for embedded use cases</li>
              <li>Observe how the "Current Data State" updates when you save changes</li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-semibold">Key Features:</h4>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 mt-2">
              <li>Monaco Editor with JSON syntax highlighting</li>
              <li>Real-time JSON validation with error messages</li>
              <li>Auto-formatting capabilities</li>
              <li>Both modal and inline display options</li>
              <li>Read-only and editable modes</li>
              <li>Responsive design with dark theme</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default JsonEditorTestPage;
