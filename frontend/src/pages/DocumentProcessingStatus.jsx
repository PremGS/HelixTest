import React from 'react';
import { useParams } from 'react-router-dom';
import ProcessingStatusPanel from '../components/ProcessingStatusPanel/ProcessingStatusPanel';

const DocumentProcessingStatus = () => {
  const { documentId } = useParams();

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-12 px-4">
      <div className="w-full max-w-xl">
        <h1 className="text-2xl font-semibold text-gray-900 mb-6">
          Document Processing Status
        </h1>
        {documentId ? (
          <ProcessingStatusPanel documentId={documentId} />
        ) : (
          <p className="text-gray-500">No document ID provided.</p>
        )}
      </div>
    </div>
  );
};

export default DocumentProcessingStatus;
