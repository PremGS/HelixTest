// EH-002 error response schema
export interface ProcessingError {
  code: string;
  httpStatus: number;
  message: string;
}

export type StageStatus = 'pending' | 'active' | 'complete' | 'failed' | 'blocked';

export interface ProcessingStage {
  id: string;
  label: string;
  status: StageStatus;
  error?: ProcessingError;
}

export interface ProcessingStatusState {
  documentId: string;
  stages: ProcessingStage[];
  isLoading: boolean;
  fetchError: string | null;
}

export const PIPELINE_STAGES: Array<{ id: string; label: string }> = [
  { id: 'uploading', label: 'Uploading' },
  { id: 'extracting', label: 'Extracting Content' },
  { id: 'analysing', label: 'Analysing Claims' },
  { id: 'ready', label: 'Ready for Review' },
];
