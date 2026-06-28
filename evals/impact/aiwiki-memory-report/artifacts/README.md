# Artifacts

This directory is for small sanitized examples only.

Large raw artifacts stay out of git:

- full `chain.json`
- full `record.jsonl`
- full `live_log.jsonl`
- full `live_results.jsonl`
- replay result JSONL files

Use `../manifests/artifacts.public.yaml` to refer to raw artifacts by logical
ID. If raw artifacts are later published, add archive URLs and checksums to the
manifest rather than committing large files here.
