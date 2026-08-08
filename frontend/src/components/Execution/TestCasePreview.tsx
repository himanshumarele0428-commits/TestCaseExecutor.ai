import { FileText, CheckCircle } from 'lucide-react';
import type { ParsedTestCase } from '../../types';

interface Props {
  filename: string;
  testCasesCount: number;
  totalSteps: number;
  testCases: ParsedTestCase[];
}

export default function TestCasePreview({ filename, testCasesCount, totalSteps, testCases }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <div className="flex items-center gap-3 mb-4">
        <FileText className="w-6 h-6 text-indigo-400" />
        <div>
          <h3 className="text-white font-semibold">{filename}</h3>
          <p className="text-gray-400 text-sm">
            {testCasesCount} test case{testCasesCount !== 1 ? 's' : ''} &bull; {totalSteps} total step{totalSteps !== 1 ? 's' : ''}
          </p>
        </div>
      </div>
      <div className="space-y-3 max-h-64 overflow-auto">
        {testCases.map((tc, i) => (
          <div key={i} className="bg-gray-800/50 rounded-lg p-3">
            <p className="text-white font-medium text-sm mb-2">{tc.name}</p>
            {tc.module && <span className="text-xs text-indigo-400 bg-indigo-900/30 px-2 py-0.5 rounded">{tc.module}</span>}
            <div className="mt-2 space-y-1">
              {tc.steps.map((step) => (
                <div key={step.order} className="flex items-start gap-2 text-gray-400 text-xs">
                  <CheckCircle className="w-3 h-3 text-gray-600 mt-0.5 flex-shrink-0" />
                  <span>{step.description}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
