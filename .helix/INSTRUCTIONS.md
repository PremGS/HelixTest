# HELIX Instructions

<!-- @helix generated -->

## Important: Read All Context Files First

Before writing any code, read **every file** inside the `.helix/` directory in this repository (not just the three named files INSTRUCTIONS.md, ARCHITECTURE.md, and DECISIONS.md — any additional files placed there are equally relevant).  Understanding the full project context will produce a more accurate implementation.

## User Stories

## EPIC 1: Document Upload & Processing

---

### STORY-001: Document Upload Interface for Pharmaceutical Documents

As a **Legal Reviewer** I want to upload pharmaceutical/scientific documents through a dedicated web interface So that I can submit documents for AI-powered compliance analysis without relying on manual handoff processes.

Acceptance Criteria:
- AC1 - Given a Legal Reviewer is authenticated and on the upload page, When they select a pharmaceutical document file (PDF or supported format) and submit, Then the file is accepted, assigned a unique document ID, and a confirmation message is displayed to the user within 3 seconds.
- AC2 - Given a Legal Reviewer has selected a valid document, When the upload is initiated, Then the system stores the document in Azure Blob Storage with ephemeral retention policy and the upload progress is visually indicated in the UI in real time.
- AC3 - Given a Legal Reviewer submits a document, When the file is received by the FastAPI backend, Then the document metadata (uploader identity, upload timestamp, document name, unique document ID) is persisted in Azure Cosmos DB to support downstream processing and audit trail.
- AC4 - Given a Legal Reviewer attempts to upload a file that exceeds the maximum allowed file size or is of an unsupported file type, When the upload is triggered, Then the system rejects the file, displays a descriptive inline error message specifying the constraint violated (e.g., "File type not supported" or "File exceeds maximum size limit"), and no data is written to storage.
- AC5 - Given a network interruption occurs mid-upload, When the connection is lost before upload completion, Then the system displays an upload failure notification, the incomplete file is not persisted in Azure Blob Storage, and the Legal Reviewer is prompted to retry.

Priority: Must Have | Story Points: 3 | Traces to: FR-UPLOAD-001, NFR-PERF-001
Depends on: None
SRS Sections: business_rules, data_requirements, error_handling_matrix

---

### STORY-002: Azure Document Intelligence Extraction & Markdown Structuring

As a **Legal Reviewer** I want uploaded pharmaceutical documents to be automatically processed by Azure Document Intelligence So that the raw document content is extracted and structured into markdown format ready for downstream compliance analysis.

Acceptance Criteria:
- AC1 - Given a document has been successfully uploaded and stored in Azure Blob Storage, When the FastAPI backend triggers the extraction pipeline, Then Azure Document Intelligence processes the document and returns extracted content structured in markdown format, preserving headings, tables, and paragraph structure.
- AC2 - Given the extraction pipeline completes successfully, When the markdown-structured content is returned by Azure Document Intelligence, Then the structured content is persisted in Azure Cosmos DB against the document's unique ID, with an extraction status of "completed" and a timestamp recorded.
- AC3 - Given
