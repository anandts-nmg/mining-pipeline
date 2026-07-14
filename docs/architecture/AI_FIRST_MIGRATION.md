# AI-First Migration Architecture

## Operating principle

AI interprets and proposes. Deterministic geospatial code transforms, measures,
validates, and publishes. Qualified humans approve high-impact outputs.

The migration is additive, not a rewrite. The existing deterministic pipeline
and CLI remain the legacy baseline. Small, reversible changes will introduce a
hybrid profile before an AI-first profile becomes eligible for operational use.
Changing profiles must never weaken raw-data integrity, EPSG:32647 publication,
provenance, evidence classification, review gates, or approved-artifact write
protection.

## Staged migration

1. **Offline contracts and provenance foundation (this PR).** Define deeply
   immutable Pydantic contracts, strict canonical hashes, locked and packaged
   prompt registrations, append-only review events, typed resolver interfaces,
   and deterministic fake/replay providers. This stage does not change any
   phase or pipeline lifecycle.
2. **Phase 00 metadata enrichment.** Add an opt-in AI job that may propose
   document metadata, file roles, sensor or product types, relationships,
   duplicate candidates, and evidence-group classifications. Raw identity,
   checksum, filename, bundle membership, and immutability remain exclusively
   deterministic and authoritative. AI metadata stays `AI_DRAFT` until its
   required validation and review are complete.
3. **Hybrid phase adapters.** Introduce opt-in phase services one bounded task at
   a time, retaining deterministic results as regression comparators. Phase
   execution and CLI defaults remain backward compatible.
4. **Geospatial interpretation and review.** Add tiled image interpretation,
   deterministic pixel-to-world conversion, validation, stitching, and a QGIS
   review workflow. High-risk geometry cannot feed production scoring or
   publication before `GEOLOGIST_APPROVED`.
5. **AI-first profile.** Enable AI-suitable work by default only after evaluation
   datasets, cost controls, replay coverage, deterministic QA/QC, and risk-based
   review gates meet accepted criteria. Legacy and hybrid profiles remain
   available during the migration window.

## Offline foundation boundaries

The first stage contains no live provider adapter, provider construction,
scheduler, QGIS plugin, raster tiling, coordinate conversion, or phase lifecycle
change. Tests use deterministic fake and replay providers and require no network
access. Prompt fixtures are harmless mechanism tests rather than production
geological instructions.

The PR 1 artifact builder requires complete source, prompt, schema, request,
model, response, generator, critic, content, confidence, limitation, risk,
timestamp, lineage, and review provenance. It hashes the actual typed payload
and cross-checks linked records through typed resolver protocols. Geological
evidence status remains distinct from AI review status, and missing or
inconsistent contract data fails validation.

The second PR 1 hardening pass makes those resolver protocols the explicit
authority boundary. Caller-created Pydantic records are portable data, not
authority: source, parent, request, job, response, prompt, schema, validation,
critique, waiver, reviewer authorization, replacement, and supersession records
must resolve exactly before artifact construction, catalog insertion, lifecycle
transition, or effective-status derivation. The in-memory implementation is the
offline reference enforcement point; a later durable implementation must apply
the same checks transactionally rather than weakening them.

Artifact content and lifecycle events are separate frozen records. Effective
review status is derived from the validated event sequence. Validation requires
deterministic and independent-critique attestations; approval requires a named,
authorized reviewer, an aware timestamp, and a note. Supersession is a separate
immutable link to a distinct approved replacement, so the original approved
record is unchanged and remains addressable. These guarantees are exercised by
an in-memory catalog and authorizer only; this PR does not claim a durable
supersession transaction or a production reviewer identity service.

Source authority is recursive rather than limited to request headers. Source
references embedded in schema-bound generator or critic output must exactly
match both the authoritative source registration and the corresponding request,
including hashes and typed locators. Validation and critique attestations resolve
their complete request, job, response, schema, subject, and timestamp chains.
Terminal rejection has one typed basis: a resolved rejecting critique, a resolved
failed required validation, or a resolved authorization for a named human
reviewer. Caller-created records do not acquire authority through serialization,
copying, or internal hash consistency.

Prompt content is loaded once into immutable resolved records, bound to the
current registered Pydantic schema, and checked against a mandatory source-
controlled lock/history file. Prompt assets are package resources and work from
a non-editable wheel outside a source checkout. The lock prevents accidental
same-version drift during loading; deliberate changes to both the registry and
lock remain a source-review and branch-protection responsibility. New work does
not select deprecated prompts. Historical validation may resolve a deprecated
prompt only by its exact locked identity, text, schema binding, and hash.

A successful offline provider response uses the exact model registered for the
request schema. Its semantic state must be represented by declared Pydantic
fields and round-trip through standard Pydantic JSON without changing exact
persisted bytes. Custom model or field serializers, computed fields, excluded
semantic fields, structural look-alike models, and unsupported containers are
outside this contract and fail closed. Fake and replay providers inspect live
nested values independently of ordinary ``model_dump`` output and cannot emit
human approval, rejection, or supersession authority.

## Enforcement deferred beyond PR 1

The following enforcement points are interfaces in PR 1, not production
services:

- durable, transactional artifact, source, request, response, job, attestation,
  and supersession storage;
- authorization backed by production identity, qualification, revocation, and
  audit systems;
- transactional uniqueness and concurrency control across processes;
- operational egress approval, provider construction, cost controls, retries,
  scheduling, and worker coordination.

The in-memory resolvers and reviewer authorizer are deterministic offline test
implementations. A later persistence/review-policy PR must implement these
interfaces and enforce their checks at every durable write boundary. No live
provider, Phase 00 enrichment, QGIS integration, job database, scheduler, or
Phase 05 automation exists in PR 1.

Repository tests also enforce a reusable tracked-artifact and streamed secret
policy. Pytest denies DNS, sockets, connection helpers, and HTTP entry points in
process; Linux CI adds a network namespace so child processes are offline as
well. These controls protect tests and packaging checks only and do not imply a
production provider egress implementation.

## Controlled operational thresholds

Phase 05 will be implemented incrementally. Survey, flight, GCP, checkpoint,
point-cloud, and accuracy calculations remain deterministic and subject to pilot,
HSE, and qualified-reviewer approval. Any production numeric threshold must be a
controlled, source-traceable configuration value with its source, version, and
approval recorded. An undocumented constant, including one inferred from a
workflow filename or modification time, cannot become production policy.

External methodology may be consulted read-only through
`BUDUUNKHAD_WORKFLOW_DOCS_ROOT`. Conflicts are recorded as discrepancies rather
than silently resolved, and no machine-specific path or external source content
is copied into Git.
