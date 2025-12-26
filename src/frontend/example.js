import React, { useState, useEffect } from 'react';

function WorkflowRunner() {
  const [workflowId, setWorkflowId] = useState(null);
  const [status, setStatus] = useState('idle');
  const [events, setEvents] = useState([]);
  const [interruptData, setInterruptData] = useState(null);
  const [userInput, setUserInput] = useState({});
  const [result, setResult] = useState(null);

  // Start workflow
  const startWorkflow = async (prompt) => {
    setStatus('starting');
    setEvents([]);
    
    const response = await fetch('http://localhost:8000/workflow/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    });
    
    const data = await response.json();
    setWorkflowId(data.workflow_id);
    
    // Start listening to SSE stream
    listenToStream(data.workflow_id);
  };

  // Listen to SSE stream
  const listenToStream = (id) => {
    const eventSource = new EventSource(`http://localhost:8000/workflow/${id}/stream`);
    
    eventSource.onmessage = (event) => {
      if (event.data === '[DONE]') {
        eventSource.close();
        setStatus('completed');
        return;
      }
      
      const data = JSON.parse(event.data);
      setEvents(prev => [...prev, data]);
      
      // Check for result
      if (data.result) {
        setResult(data.result);
      }
    };
    
    // Handle interrupt event
    eventSource.addEventListener('interrupt', (event) => {
      const data = JSON.parse(event.data);
      setStatus('waiting_for_input');
      setInterruptData(data.interrupt_data);
      eventSource.close();
    });
    
    eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
      eventSource.close();
      setStatus('error');
    };
  };

  // Resume workflow with user input
  const resumeWorkflow = async () => {
    setStatus('resuming');
    
    const response = await fetch(`http://localhost:8000/workflow/${workflowId}/resume`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_input: userInput })
    });
    
    const data = await response.json();
    
    if (data.status === 'waiting_for_input') {
      setInterruptData(data.interrupt_data);
    } else {
      setInterruptData(null);
      setUserInput({});
      // Continue listening to stream
      listenToStream(workflowId);
    }
  };

  // Handle input change
  const handleInputChange = (key, value) => {
    setUserInput(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="workflow-runner">
      <h2>Azure Workflow Runner</h2>
      
      {/* Start Workflow */}
      {status === 'idle' && (
        <div>
          <button onClick={() => startWorkflow('Create Azure VM')}>
            Start Workflow
          </button>
        </div>
      )}

      {/* Status */}
      <div>Status: <strong>{status}</strong></div>

      {/* Event Stream */}
      {events.length > 0 && (
        <div className="events">
          <h3>Events:</h3>
          <ul>
            {events.map((event, idx) => (
              <li key={idx}>{JSON.stringify(event)}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Interrupt - Collect User Input */}
      {status === 'waiting_for_input' && interruptData && (
        <div className="user-input">
          <h3>Input Required:</h3>
          {Object.entries(interruptData).map(([key, description]) => (
            <div key={key}>
              <label>{description}:</label>
              <input
                type="text"
                value={userInput[key] || ''}
                onChange={(e) => handleInputChange(key, e.target.value)}
              />
            </div>
          ))}
          <button onClick={resumeWorkflow}>Submit</button>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="result">
          <h3>Result:</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default WorkflowRunner;