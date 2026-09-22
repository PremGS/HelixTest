import React from 'react';
import { ProcessingStage } from '../../types/processingStatus.types';
import styles from './ProcessingStatusPanel.module.css';

interface StageIndicatorProps {
  stage: ProcessingStage;
  stepNumber: number;
}

const StageIndicator: React.FC<StageIndicatorProps> = ({ stage, stepNumber }) => {
  const getStatusIcon = () => {
    switch (stage.status) {
      case 'complete':
        return <span className={styles.iconComplete} aria-label="Complete">&#10003;</span>;
      case 'active':
        return <span className={styles.iconActive} aria-label="In progress" />;
      case 'failed':
        return <span className={styles.iconFailed} aria-label="Failed">&#10007;</span>;
      case 'blocked':
        return <span className={styles.iconBlocked} aria-label="Blocked">&#128274;</span>;
      default:
        return <span className={styles.iconPending} aria-label="Pending">{stepNumber}</span>;
    }
  };

  const stageClass = [
    styles.stage,
    styles[`stage--${stage.status}`],
  ].filter(Boolean).join(' ');

  return (
    <li className={stageClass}>
      <div className={styles.stageIconWrapper}>{getStatusIcon()}</div>
      <span className={styles.stageLabel}>{stage.label}</span>
    </li>
  );
};

export default StageIndicator;
