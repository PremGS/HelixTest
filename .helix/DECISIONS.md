# HELIX Decisions

<!-- @helix generated — edit freely; not overwritten on re-runs -->

## Log

Record architectural decisions, trade-offs, and notable implementation choices here as they are made.

| Date | Decision | Rationale |
| ---- | -------- | --------- |
| 2026-08-31 | Built ProcessingStatusPanel with StageIndicator and ErrorBanner sub-components using CSS Modules; useProcessingStatus hook hydrates from REST on mount and derives blocked states from first failed stage | Keeps all logic co-located, avoids external state libraries, and ensures browser-refresh persistence (AC3) via initial REST fetch before any SignalR events |
<!-- ticket:SUBTASK-9 -->

## UI Screen Inventory

These screens exist in the repository and must **not** be restructured, renamed, or removed without explicit approval.

| Path | Name | Route |
| ---- | ---- | ----- |
| frontend/src/pages/SignIn.jsx | Sign In | /auth |
| frontend/src/pages/UserProfile.jsx | User Profile | /dashboard |
| frontend/src/pages/ReviewDashboard.jsx | Review Dashboard | /dashboard |
| frontend/src/pages/UploadErrorDetails.jsx | Upload Error Details | /documents/upload |
| frontend/src/pages/DocumentUpload.jsx | Document Upload | /documents/upload |
| frontend/src/pages/DocumentQueue.jsx | Document Queue | /documents |
| frontend/src/pages/DocumentProcessingStatus.jsx | Document Processing Status | /documents/:documentId/processing |
| frontend/src/pages/ClaimDetail.jsx | Claim Detail | /documents/:documentId/review |
| frontend/src/pages/DocumentReview.jsx | Document Review | /documents/:documentId/review |
| frontend/src/pages/AiQueryAssistant.jsx | AI Query Assistant | /documents/:documentId/review |
| frontend/src/pages/SubmitReviewDecision.jsx | Submit Review Decision | /documents/:documentId/review |
| frontend/src/pages/KnowledgeBaseDocumentDetail.jsx | Knowledge Base Document Detail | /knowledge-base/:kbDocumentId |
| frontend/src/pages/KnowledgeBase.jsx | Knowledge Base | /knowledge-base |
| frontend/src/pages/AddKnowledgeBaseDocument.jsx | Add Knowledge Base Document | /knowledge-base |
| frontend/src/pages/AuditEventDetail.jsx | Audit Event Detail | /audit |
| frontend/src/pages/AuditTrail.jsx | Audit Trail | /audit |
| frontend/src/pages/ComplianceReports.jsx | Compliance Reports | /reports |
| frontend/src/pages/AdminPanel.jsx | Admin Panel | /admin |
| frontend/src/pages/ComplianceReportPreview.jsx | Compliance Report Preview | /reports/:reportId |
| frontend/src/pages/UserManagement.jsx | User Management | /admin/users |
| frontend/src/pages/EditUserRole.jsx | Edit User Role | /admin/users |
| frontend/src/pages/PipelineHealthMonitor.jsx | Pipeline Health Monitor | /admin/pipeline-health |
