import React, { useState } from 'react';
import { JsonEditor, JsonViewer } from './JsonEditor';
import { Button } from './ui/button';
import { Dialog } from './ui/dialog';

interface SampleDataType {
  id: number;
  name: string;
  email: string;
  preferences: {
    theme: string;
    notifications: boolean;
    language: string;
  };
  skills: string[];
  experience: {
    years: number;
    companies: Array<{
      name: string;
      role: string;
      duration: string;
    }>;
  };
}

// Example component showing how to use the JsonEditor and Dialog components
export const JsonEditorExample: React.FC = () => {
  const [sampleData, setSampleData] = useState<SampleDataType>({
    id: 1,
    name: "John Doe",
    email: "john.doe@example.com",
    preferences: {
      theme: "dark",
      notifications: true,
      language: "en"
    },
    skills: ["JavaScript", "TypeScript", "React", "Node.js"],
    experience: {
      years: 5,
      companies: [
        { name: "TechCorp", role: "Frontend Developer", duration: "2021-2023" },
        { name: "WebSolutions", role: "Full Stack Developer", duration: "2019-2021" }
      ]
    }
  });

  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const handleSave = (newData: unknown) => {
    setSampleData(newData as SampleDataType);
    console.log('Data saved:', newData);
  };

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-bold">JSON Editor Components Demo</h2>
      
      {/* Example 1: JsonEditor with trigger button */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">1. JSON Editor with Trigger Button</h3>
        <JsonEditor
          data={sampleData}
          onSave={handleSave}
          title="Edit User Data"
          trigger={<Button>Edit JSON Data</Button>}
        />
      </div>

      {/* Example 2: JsonEditor with controlled state */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">2. JSON Editor with Controlled State</h3>
        <Button onClick={() => setIsDialogOpen(true)}>
          Open Controlled JSON Editor
        </Button>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <JsonEditor
            data={sampleData}
            onSave={handleSave}
            title="Controlled JSON Editor"
            isOpen={isDialogOpen}
            onOpenChange={setIsDialogOpen}
          />
        </Dialog>
      </div>

      {/* Example 3: Read-only JsonEditor */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">3. Read-only JSON Viewer (Modal)</h3>
        <JsonEditor
          data={sampleData}
          readOnly={true}
          title="View User Data (Read-only)"
          trigger={<Button variant="outline">View JSON Data</Button>}
        />
      </div>

      {/* Example 4: Inline JsonViewer */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">4. Inline JSON Viewer</h3>
        <JsonViewer data={sampleData} height="200px" />
      </div>

      {/* Example 5: Editable inline JsonViewer */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">5. Editable Inline JSON Viewer</h3>
        <JsonViewer data={sampleData} height="300px" readOnly={false} />
      </div>

      {/* Current data display */}
      <div className="mt-8 p-4 bg-gray-50 rounded-lg">
        <h3 className="text-lg font-semibold mb-2">Current Data State:</h3>
        <pre className="text-sm bg-white p-3 rounded border overflow-auto">
          {JSON.stringify(sampleData, null, 2)}
        </pre>
      </div>
    </div>
  );
};
