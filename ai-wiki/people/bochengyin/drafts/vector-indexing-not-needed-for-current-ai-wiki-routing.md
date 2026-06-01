---
title: "Vector indexing is not needed for current AI wiki routing"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "design"
status: "draft"
created_at: "2026-05-28T20:00:00+10:00"
updated_at: "2026-05-28T20:00:00+10:00"
promotion_candidate: false
promotion_basis: "none"
---
# Review Draft

## Context

While clarifying what "indexing" means for `ai-wiki-toolkit`, the user concluded that the current toolkit does not need vector indexing.

Existing AI wiki routing already has a lighter indexing shape: human-readable `index.md` maps, generated catalog/card metadata, and task-aware route packets that point agents toward the most relevant source docs.

## Design Clarification

Do not add vector indexing just because retrieval systems often use it.

For the current product shape, prefer:

- human-readable index files as repo maps
- generated catalog or card metadata for cheap candidate selection
- sparse route packets that include only high-signal context
- full-document loading only when the referenced card is clearly relevant

Vector embeddings or a vector database should become a candidate only after there is evidence that lightweight routing cannot handle scale, ambiguity, or recall quality.

## Implication

Near-term AI wiki retrieval work should improve the existing sparse index/card/catalog path before introducing vector infrastructure.
