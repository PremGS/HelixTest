import React from 'react';
import { useProcessingStatus } from '../../hooks/useProcessingStatus';
import StageIndicator from './StageIndicator';
import ErrorBanner from './ErrorBanner';
import styles from './ProcessingStatusPanel.module.css';
import { ProcessingError } from '../../types/processingStatus.types';

interface ProcessingStatusPanelProps {
  documentId: string;
}

const ProcessingStatusPanel: React.FC<ProcessingStatusPanelProps> = ({ documentId }) => {
  const { stages, isLoading, fetchError, refresh } = useProcessingStatus(documentId);

  const failedStage = stages.find((s) => s.status === 'failed');
  const failedError: ProcessingError | undefined = failedStage?.error;

  if (isLoading) {
    return (
      <div className={styles.panel}>
        <p className={styles.loadingText}>Loading processing status&hellip;</p>
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className={styles.panel}>
        <p className={styles.fetchError}>
          Unable to load processing status: {fetchError}.{' '}
          <button className={styles.retryButton} onClick={refresh} type="button">
            Retry
          </button>
        </p>
      </div>
    );
  }

  return (
    <div className={styles.panel}>
      <h2 className={styles.panelTitle}>Processing Status</h2>
      <ol className={styles.stageList} aria-label="Processing pipeline stages">
        {stages.map((stage, idx) => (
          <StageIndicator key={stage.id} stage={stage} stepNumber={idx + 1} />
        ))}
      </ol>
      {failedError && <ErrorBanner error={failedError} />}
    </div>
  );
};

export default ProcessingStatusPanel;
