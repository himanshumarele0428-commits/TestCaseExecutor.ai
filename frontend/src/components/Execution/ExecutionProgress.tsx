import type { SSEEvent } from '../../types';
import StatusBadge from '../Common/StatusBadge';
import { Play, CheckCircle, XCircle } from 'lucide-react';

interface Props {
  events: SSEEvent[];
  connected: boolean;
  done: boolean;
  finalStatus: string | null;
  totalTestCases: number;
}

export default function ExecutionProgress({ events, connected, done, finalStatus, totalTestCases }: Props) {
  const completedTCs = events.filter((e) => e.type === 'test_case_completed').length;
  const progressPct = totalTestCases > 0 ? Math.round((completedTCs / totalTestCases) * 100) : 0;
  const isRunning = connected && !done;
  const lastStepStarted = events.filter((e) => e.type === 'step_started').pop();
  const currentStep = done ? null : lastStepStarted;
  const lastCompleted = events.filter((e) => e.type === 'step_completed').pop();
  const isFailed = done && finalStatus === 'FAILED';

  const status = done ? (isFailed ? 'FAILED' : 'COMPLETED') : isRunning ? 'RUNNING' : 'QUEUED';
  const statusLabel = done ? (isFailed ? 'Failed' : 'Completed') : isRunning ? 'Running' : 'Starting...';

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white font-semibold flex items-center gap-2">
          <Play className={`w-4 h-4 ${done ? 'text-green-400' : 'text-blue-400'}`} />
          Execution {statusLabel}
        </h3>
        <StatusBadge status={status} />
      </div>

      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-400 mb-1">
          <span>Progress</span>
          <span>{completedTCs} / {totalTestCases} test cases</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2.5">
          <div
            className={`h-2.5 rounded-full transition-all duration-500 ${isFailed ? 'bg-red-500' : done ? 'bg-green-500' : 'bg-indigo-500'}`}
            style={{ width: `${done ? 100 : progressPct}%` }}
          />
        </div>
      </div>

      {currentStep && (
        <div className="bg-gray-800/50 rounded-lg p-3 mb-3">
          <p className="text-xs text-gray-500 mb-1">Current Step</p>
          <p className="text-white text-sm">{currentStep.step_description}</p>
          <p className="text-gray-400 text-xs mt-1">Intent: {currentStep.intent}</p>
        </div>
      )}

      {lastCompleted && (
        <div className="flex items-center gap-2 text-sm">
          {lastCompleted.status === 'PASSED' ? (
            <CheckCircle className="w-4 h-4 text-green-400" />
          ) : (
            <XCircle className="w-4 h-4 text-red-400" />
          )}
          <span className={lastCompleted.status === 'PASSED' ? 'text-green-400' : 'text-red-400'}>
            Last step: {lastCompleted.status}
          </span>
          {lastCompleted.duration_ms && (
            <span className="text-gray-500">({(lastCompleted.duration_ms / 1000).toFixed(1)}s)</span>
          )}
        </div>
      )}

      {done && (
        <div className={`mt-4 p-3 rounded-lg ${isFailed ? 'bg-red-900/20 border border-red-800' : 'bg-green-900/20 border border-green-800'}`}>
          <div className="flex items-center gap-2">
            {isFailed ? (
              <XCircle className="w-5 h-5 text-red-400" />
            ) : (
              <CheckCircle className="w-5 h-5 text-green-400" />
            )}
            <span className={`font-medium ${isFailed ? 'text-red-300' : 'text-green-300'}`}>
              {isFailed ? 'Execution failed' : 'Execution completed successfully'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
