# Architecture

The current implementation is an isolated Python standard-library ingestion experiment and the original React starter. They are not connected. The intended architecture is a local-first modular FastAPI service, PostgreSQL metadata and protected evidence storage, with deterministic analytics and a React client. Authentication and case isolation must precede any real-data use.
