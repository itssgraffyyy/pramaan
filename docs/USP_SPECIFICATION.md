# USP specification

The initial ingestion core records a SHA-256 digest and per-row references, retains rejected rows and checks field reconciliation separately. It does not yet provide immutable storage, sufficiency analysis, versioned revalidation or signed replay. These must be implemented and tested before claiming the three USPs.
