# Architecture

The current React dashboard calls a synthetic-only FastAPI service through the Vite development proxy. The service reprocesses bundled CSV fixtures in memory; it does not accept uploads or persist cases. The intended architecture includes PostgreSQL metadata and protected evidence storage. Authentication and case isolation must precede any real-data use.
