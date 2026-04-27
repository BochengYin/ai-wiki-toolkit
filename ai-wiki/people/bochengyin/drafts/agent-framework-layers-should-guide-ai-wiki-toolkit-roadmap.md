---
title: "Agent framework layers should guide AI wiki toolkit roadmap"
author_handle: "bochengyin"
model: "gpt-5"
source_kind: "external_reference"
status: "draft"
created_at: "2026-04-27T00:00:00+1000"
updated_at: "2026-04-27T14:03:08+1000"
promotion_candidate: true
promotion_basis: "Second confirming signal: a separate agent independently framed ai-wiki-toolkit as a memory and workflow framework rather than an AI wiki folder."
---
# Review Draft

## Context

The user pointed to an April 2026 X Article summarizing Luo Fuli's view that the AI agent paradigm is shifting from raw model strength toward framework quality.

The useful framing for `ai-wiki-toolkit` is not "copy OpenClaw" or build a full runtime orchestrator. It is that an agent framework has at least three layers:

- human interaction: how people hand work to the agent and build trust over repeated use
- model communication: how the framework packages context, instructions, skills, and private knowledge for the model
- scheduling and orchestration: how the framework chooses models, workflows, tools, and quality gates based on task shape

## Second Signal

A separate agent independently suggested the same reframing: `ai-wiki-toolkit` should be described less as an AI wiki folder and more as a repo-native framework where coding agents follow a loop:

1. read memory
2. act in the repository
3. cite and reuse relevant memory
4. write back durable lessons
5. evaluate whether memory changed behavior

That confirms the product gap is largely narrative and framework-shape clarity, not a need to become a larger agent runtime.

## Current Fit

`ai-wiki-toolkit` already has a strong memory-harness base:

- repo-visible memory files
- managed prompt routing
- repo-local skills
- end-of-task reuse and write-back checks
- pilot eval evidence that ambient repo memory can change agent behavior

The gap is that much of the memory is still passive Markdown. The next product step should make AI wiki content more usable as framework assets: skills, workflow contracts, context packets, evaluation gates, and routing hints.

## Positioning Takeaway

The strongest positioning direction is:

> `ai-wiki-toolkit` is a repo-native memory and workflow framework for coding agents, designed to make project knowledge reusable, reviewable, and continuously updated inside the repo.

This keeps "memory" central but makes the framework loop explicit.

## Gap Assessment

The toolkit already has the memory harness base. The remaining gap is turning repo memory from passive files plus prompt instructions into operational framework assets.

The biggest missing pieces are:

1. context selection: agents still rely on broad read-order instructions instead of a task-aware selector that says which memory matters now
2. memory compilation: stable notes are not yet compiled into focused context packets, skill templates, or workflow contracts
3. workflow state: the read -> act -> cite/reuse -> write back -> evaluate loop is expressed in prompts and skills, but not tracked as a first-class task state machine
4. feedback quality: reuse telemetry records events, but there is not yet a product-facing diagnosis of missed memory, stale memory, noisy memory, or high-value memory
5. consolidation: draft consolidation exists as a skill, but there is no command or report that helps humans turn draft clusters into governed shared memory
6. evaluation packaging: the pilot eval is strong evidence, but the eval workflow is not yet a repeatable product surface that users can run on their own repos
7. agent integration: Codex-style repo skills are supported, but cross-agent behavior remains mostly prompt-file based rather than adapter-backed

The highest-leverage next step is not multi-model orchestration. It is task-aware context routing: make the toolkit better at deciding which memory should be loaded, cited, ignored, or updated for the current task.

## User Priority Signals

The user confirmed the following roadmap priorities:

- context routing should be built next
- feedback diagnosis is needed, especially missed, stale, noisy, conflicting, and high-ROI memory
- consolidation should become an agent proposal surface where humans review merge, promotion, conflict, or deletion recommendations
- eval should become a product surface that users can run against their own repositories

The user asked for deeper explanation of:

- memory compilation: what stable Markdown should compile into and how that differs from simply reading notes
- cross-agent adapters: what an adapter layer would do beyond generic prompt-file support

Workflow state looks promising as a user experience improvement, but implementation complexity needs to be scoped carefully.

## Route And Context Packet Design

The route step should answer: "What kind of task is this, and which memory is worth loading now?"

The context packet step should answer: "Given that route, what compact, cited, task-specific guidance should the agent receive before acting?"

The first implementation should be a conservative generated artifact, not a freeform agent summary. A good pipeline is:

1. collect task signals: user request, touched file paths, git status, explicit task type if provided, and optional agent/tool name
2. load the local AI wiki catalog, document metadata, headings, path names, and lightweight metrics
3. score candidate memory using deterministic signals first: path scope, frontmatter tags, heading keywords, doc kind, recency, and prior reuse usefulness
4. ask an agent or LLM only to justify or compress selected candidates, not to invent new rules
5. emit a packet with source paths, quoted-or-paraphrased rule snippets, reasons for inclusion, skip list, context budget, and confidence
6. require the acting agent to cite packet items it actually used in the final reuse footer

The packet should remain a derived local artifact. Markdown stays the source of truth.

Example packet shape:

```yaml
task_id: scaffold-prompt-update-2026-04-27
route:
  task_type: scaffold_prompt_workflow
  risk_tags:
    - user_owned_docs
    - managed_prompt_block
context_budget:
  target_words: 900
must_load:
  - doc_id: conventions/package-managed-vs-user-owned-docs
    path: ai-wiki/conventions/package-managed-vs-user-owned-docs.md
    reason: task touches package-managed versus user-owned AI wiki ownership
    confidence: high
must_follow:
  - rule: keep evolving package guidance under _toolkit/**
    source: ai-wiki/conventions/package-managed-vs-user-owned-docs.md
  - rule: do not rewrite user-owned AI wiki docs during install
    source: ai-wiki/constraints.md
skip:
  - doc_id: release_distribution_integrity
    reason: release packaging is not in scope
packet_status: generated_from_sources
```

The trust model is provenance plus bounded synthesis:

- every actionable rule needs a source path
- generated summaries cannot introduce uncited requirements
- low-confidence matches are labeled as candidates, not rules
- packet output is diffable and can be checked by `doctor`
- if source docs conflict, the packet reports the conflict instead of choosing silently
- packet artifacts should be regenerated, not edited as canonical memory

This differs from the current AI wiki workflow because the current flow tells agents where to look. Routing and context packets would give agents a task-specific working set and make the selection itself auditable.

## Route MVP Implementation

The first route/context packet implementation landed as a conservative package-integrated layer:

- `aiwiki-toolkit route` generates a transient packet from the current task text, optional changed paths, the repo AI wiki catalog, document text, and reuse stats
- managed prompt blocks now ask agents to run `aiwiki-toolkit route --task "<current user request>"` at task start when available
- users do not need to provide separate manual input during normal agent use; the agent supplies the current request text because the CLI cannot see private conversation context on its own
- packets are printed to stdout and are not canonical memory
- packets include `must_load`, `maybe_load`, `must_follow`, `context_notes`, `skip`, risk tags, and trust-model reminders
- authoritative `must_follow` rules require cited user-owned source paths
- drafts and trails can appear as exploratory `context_notes`, not authoritative rules
- managed `_toolkit/**` docs describe routing behavior but are still excluded from user-owned reuse telemetry

This is intentionally not a daemon, runtime, or multi-model scheduler. It is a task-aware selection and packet-generation layer that integrates into the existing AI wiki agent workflow.

## Product Implication

Treat AI wiki as the private-intelligence layer of an agent framework.

Possible roadmap direction:

1. human interaction layer: improve clarify-before-code, task relevance, and user-facing evidence so users know when memory helped
2. model communication layer: turn stable wiki notes into structured context bundles or skill templates instead of relying only on broad read-order instructions
3. orchestration layer: add lightweight task classification, model/tool routing hints, context-budget rules, and eval gates without taking over the agent runtime

This keeps the toolkit aligned with its current scope: repository-native memory and workflow scaffolding, not a closed agent product.

## Guardrails

Do not make this a feature that automatically rewrites shared user-owned AI wiki docs.

Respect the existing ownership boundary:

- capture raw signals in handle-local drafts
- consolidate repeated patterns separately
- promote only after the two-signal gate or explicit human confirmation
- keep package-managed evolution under `_toolkit/**` or generated artifacts

## Reuse Assessment

This should be useful when evaluating roadmap work that tries to move the toolkit from "agents read docs" toward "agents operate through reusable, repo-visible framework assets."

Mark as a promotion candidate because there are now two independent signals for the same framing. Human confirmation is still needed before turning it into shared positioning, a roadmap decision, or README copy.
