# Ambiguity Categories

Use these categories to decide whether a coding task needs clarification.

## Behavior

What should the feature actually do? What are edge cases?

## Data Model

Are new fields, tables, states, enums, or migrations required?

## API Contract

What are inputs, outputs, error codes, compatibility rules?

## Permissions

Who can do this? Who cannot? What data can they see?

## Failure Modes

What happens on failure, retry, partial success, invalid input, external dependency failure?

## Existing Conventions

Does the repo already have a pattern, convention, or decision that should be reused?

## UX / User-Facing Text

Does exact copy or user-visible behavior matter?

## Performance / Scale

Does data volume, latency, async processing, pagination, batching, or streaming change implementation?

## Testing Expectation

Which behavior must be tested? Are there known flaky patterns to avoid?

## Rollout / Migration

Does this affect existing data, old users, old APIs, or migration behavior?

## Important

Do not ask all categories every time. Ask only the questions that block safe implementation.
