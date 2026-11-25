# Current experimental schema

CDR A: caller, callee, timestamp, duration. CDR B: a_number, b_number, start_time, seconds. IPDR: start_time, source_ip, source_port. Timestamps require ISO 8601 offsets. Identifiers and duration remain strings. Each source reference is the original file SHA-256 plus the logical CSV record number (header is record 1, including when a record spans physical lines). These are synthetic formats, not official operator specifications.
