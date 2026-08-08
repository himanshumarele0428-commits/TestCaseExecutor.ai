import { useCallback, useState } from 'react';
import { Upload, FileText, X, Loader2 } from 'lucide-react';

interface Props {
  onFileSelect: (file: File) => void;
  onUpload: () => void;
  selectedFile: File | null;
  uploading: boolean;
  disabled?: boolean;
}

export default function FileUpload({ onFileSelect, onUpload, selectedFile, uploading, disabled }: Props) {
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) validateAndSelect(file);
    },
    [onFileSelect]
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) validateAndSelect(file);
  };

  const validateAndSelect = (file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!['.txt', '.md'].includes(ext)) {
      alert('Only .txt and .md files are accepted');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      alert('File size must be under 5MB');
      return;
    }
    onFileSelect(file);
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onFileSelect(null as any);
  };

  if (selectedFile) {
    return (
      <div className="border border-indigo-700/50 rounded-xl p-6 bg-gray-800/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-900/30 flex items-center justify-center">
              <FileText className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <p className="text-white font-medium">{selectedFile.name}</p>
              <p className="text-gray-500 text-sm">{(selectedFile.size / 1024).toFixed(1)} KB</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleClear}
              className="p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded-lg transition-colors"
              title="Remove file"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
        <button
          onClick={onUpload}
          disabled={uploading || disabled}
          className="mt-4 w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
        >
          {uploading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" /> Parsing file...
            </>
          ) : (
            <>
              <Upload className="w-5 h-5" /> Upload & Parse
            </>
          )}
        </button>
      </div>
    );
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
        dragOver
          ? 'border-indigo-500 bg-indigo-900/20'
          : disabled
          ? 'border-gray-700 bg-gray-800/50'
          : 'border-gray-600 bg-gray-800/30 hover:border-indigo-500 hover:bg-gray-800/50 cursor-pointer'
      }`}
    >
      <input type="file" accept=".txt,.md" onChange={handleFileChange} className="hidden" id="file-upload" disabled={disabled} />
      <label htmlFor="file-upload" className={disabled ? 'cursor-not-allowed' : 'cursor-pointer'}>
        <Upload className="w-10 h-10 text-gray-400 mx-auto mb-3" />
        <p className="text-gray-300 font-medium mb-1">Drop your test file here or click to browse</p>
        <p className="text-gray-500 text-sm">Supports .txt and .md files (max 5MB)</p>
        <p className="text-gray-600 text-xs mt-2">Write test steps in plain English — the AI handles the rest</p>
      </label>
    </div>
  );
}
