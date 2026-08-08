import { useEffect, useRef } from 'react';
import type { SSEEvent } from '../../types';
import { Terminal } from 'lucide-react';

interface Props {
  events: SSEEvent[];
}

export default function ExecutionConsole({ events }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const formatTime = () => {
    const now = new Date();
    return now.toLocaleTimeString('en-US', { hour12: false });
  };

  const getLogStyle = (event: SSEEvent) => {
    switch (event.type) {
      case 'step_completed':
        return event.status === 'PASSED' ? 'text-green-400' : 'text-red-400';
      case 'execution_completed':
        return 'text-indigo-400';
      default:
        return 'text-gray-400';
    }
  };

  const getLogMessage = (event: SSEEvent) => {
    switch (event.type) {
      case 'execution_started':
        return `Execution started — ${event.total_test_cases} test case(s)`;
      case 'test_case_started':
        return `Test case started: ${event.test_case_name}`;
      case 'step_started':
        return `Step ${event.step_order} started: ${event.step_description}`;
      case 'step_completed':
        return `Step ${event.step_order}: ${event.status}${event.error ? ` — ${event.error}` : ''}`;
      case 'test_case_completed':
        return `Test case completed: ${event.test_case_name} — ${event.status}`;
      case 'execution_completed':
        return `Execution completed — ${event.passed} passed, ${event.failed} failed`;
      default:
        return JSON.stringify(event);
    }
  };

  return (
    <div className="bg-gray-950 border border-gray-800 rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2 bg-gray-900 border-b border-gray-800">
        <Terminal className="w-4 h-4 text-gray-400" />
        <span className="text-sm text-gray-400 font-medium">Execution Console</span>
      </div>
      <div className="p-4 h-48 overflow-auto font-mono text-xs space-y-1">
        {events.length === 0 && <p className="text-gray-600">Waiting for execution to start...</p>}
        {events.map((event, i) => (
          <div key={i} className={getLogStyle(event)}>
            <span className="text-gray-600">[{formatTime()}]</span> {getLogMessage(event)}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
