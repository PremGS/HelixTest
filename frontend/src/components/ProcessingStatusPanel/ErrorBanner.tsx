import React from 'react';
import { ProcessingError } from '../../types/processingStatus.types';
import styles from './ProcessingStatusPanel.module.css';

interface ErrorBannerProps {
  error: ProcessingError;
}

const ErrorBanner: React.FC<ErrorBannerProps> = ({ error }) => {
  return (
    <div className={styles.errorBanner} role="alert">
      <span className={styles.errorBannerIcon} aria-hidden="true">&#9888;</span>
      <div className={styles.errorBannerContent}>
        <span className={styles.errorBannerMessage}>{error.message}</span>
        {error.code && (
          <span className={styles.errorBannerCode}>Error code: {error.code}</span>
        )}
      </div>
    </div>
  );
};

export default ErrorBanner;
