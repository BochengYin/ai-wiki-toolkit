# Sanitize Public Release

Use this workflow before sharing the artifact package externally.

1. Search public files for local absolute paths:
   `rg '/[U]sers/|/[h]ome/|C:\\[U]sers\\|/var/folders|/tmp/' evals/impact/aiwiki-memory-report`.
2. Replace raw local paths in public-facing files with logical artifact IDs from
   `manifests/artifacts.public.yaml`.
3. Move local path resolution into ignored `manifests/local-paths.yaml`.
4. Keep only sanitized examples under `artifacts/examples/`.
5. If a large raw artifact is published externally, add its archive URL,
   checksum, and logical artifact ID to `manifests/artifacts.public.yaml`.
6. Re-run the path search and record any intentional local-only files that
   remain excluded from publication.

Current note: public source-of-truth tables should use logical artifact IDs.
Keep workstation path mappings only in ignored local manifests.
