import { useState, useEffect, useCallback } from 'react';
import {
  ProcessingStatusState,
  ProcessingStage,
  PIPELINE_STAGES,
  StageStatus,
} from '../types/processingStatus.types';

const API_BASE = '/api/v1';

interface ApiStageResponse {
  stage_id: string;
  status: string;
  error?: { code: string; httpStatus: number; message: string };
}

interface ApiStatusResponse {
  document_id: string;
  stages: ApiStageResponse[];
}

function mapApiStagesToStages(apiStages: ApiStageResponse[]): ProcessingStage[] {
  const stageMap = new Map(apiStages.map((s) => [s.stage_id, s]));
  let failedIndex = -1;

  const stages = PIPELINE_STAGES.map((def, idx) => {
    const api = stageMap.get(def.id);
    const rawStatus = api?.status ?? 'pending';
    let status: StageStatus = 'pending';
    if (rawStatus === 'active' || rawStatus === 'in_progress') status = 'active';
    else if (rawStatus === 'complete' || rawStatus === 'completed') status = 'complete';
    else if (rawStatus === 'failed') {
      status = 'failed';
      if (failedIndex === -1) failedIndex = idx;
    } else if (rawStatus !== 'pending') {
      console.warn(`[useProcessingStatus] Unrecognised stage status: "${rawStatus}" for stage "${def.id}". Treating as pending.`);
    }
    return { id: def.id, label: def.label, status, error: api?.error };
  });

  // Mark all stages after the failed one as blocked
  if (failedIndex !== -1) {
    for (let i = failedIndex + 1; i < stages.length; i++) {
      stages[i] = { ...stages[i], status: 'blocked' };
    }
  }

  return stages;
}

export function useProcessingStatus(documentId: string): ProcessingStatusState & {
  refresh: () => void;
} {
  const [state, setState] = useState<ProcessingStatusState>({
    documentId,
    stages: PIPELINE_STAGES.map((def) => ({ id: def.id, label: def.label, status: 'pending' })),
    isLoading: true,
    fetchError: null,
  });

  const fetchStatus = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, fetchError: null }));
    try {
      const response = await fetch(`${API_BASE}/documents/${documentId}/processing-status`);
      if (!response.ok) {
        throw new Error(`Failed to fetch processing status (HTTP ${response.status})`);
      }
      const data: ApiStatusResponse = await response.json();
      setState({
        documentId,
        stages: mapApiStagesToStages(data.stages),
        isLoading: false,
        fetchError: null,
      });
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        fetchError: err instanceof Error ? err.message : 'Failed to load processing status',
      }));
    }
  }, [documentId]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  return { ...state, refresh: fetchStatus };
}
