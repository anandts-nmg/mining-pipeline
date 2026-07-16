# Keyless AI-to-QGIS vertical slice

This migration slice prepares geological interpretation work without requiring an API key.
Preparation, saved-response ingestion, deterministic coordinate transformation, validation,
AI_DRAFT GeoPackage/QGIS generation, and evaluation are local operations. Only `ai execute`
crosses the optional provider boundary and therefore requires explicit AI enablement, a hybrid or
AI-first profile, approved egress, an optional provider SDK, and its environment variable key.

No command edits protected source material. Sources used for AI work must be registered from the
immutable snapshot root. Generated material is confined to a run directory below
`BUDUUNKHAD_WORK_ROOT`; evaluation references remain below `BUDUUNKHAD_EVAL_ROOT`. The central
path policy also protects the raw root and `BUDUUNKHAD_WORKFLOW_DOCS_ROOT`, rejects overlapping
roles, traversal, and symlink escapes. Publication, when deliberately requested by a later
workflow, is confined to `BUDUUNKHAD_PUBLISH_ROOT`.

## Storage configuration

Set local paths outside the repository. These examples are symbolic and not machine-specific:

```text
BUDUUNKHAD_WORKFLOW_DOCS_ROOT=/protected/methodology
BUDUUNKHAD_SNAPSHOT_ROOT=/protected/snapshot
BUDUUNKHAD_WORK_ROOT=/work/buduunkhad-ai
BUDUUNKHAD_EVAL_ROOT=/protected/evaluation
BUDUUNKHAD_PUBLISH_ROOT=/published/buduunkhad
```

Create and verify a write-once inventory before processing:

```bash
buduunkhad ai snapshot-create --run-id run-001 \
  --source-root /protected/snapshot --source-root-id snapshot
buduunkhad ai snapshot-verify --source-root /protected/snapshot \
  --source-root-id snapshot \
  --manifest /work/buduunkhad-ai/runs/run-001/snapshot-manifest.json
```

The manifest records relative paths, sizes, SHA-256 values, sidecar relationships, the source-root
identity, and creation time. It does not copy, resample, or modify source files.

## Prepare and inspect

Select a provider/model during preparation when a response will later come from that provider.
No SDK is imported and no key is read by this command:

```bash
buduunkhad ai prepare --run-id run-001 \
  --source /protected/snapshot/synthetic-map.tif \
  --task geological-feature-proposal \
  --provider openai --model chosen-model \
  --tile-size 1024 --overlap 128 --estimated-cost 0.25
```

Inspect `request-package.json`, `tile-manifest.json`, the rendered `tiles/`, and
`execution-instructions.txt` under the printed package directory. The package binds the source,
tiles, prompt, schema, task, provider/model choice, egress decision, request size, estimated cost,
and stable request fingerprint.

After inspecting those exact files, record the source-egress decision separately:

```bash
buduunkhad ai approve-egress --package /work/.../requests/... \
  --approved-by named-egress-reviewer \
  --note "Approved only the inspected previews in this package"
```

The approval file is write-once and does not create geological approval, publication approval, or
reviewer qualification authority.

## Execute later, or ingest an external response now

Live execution is intentionally separate:

```bash
buduunkhad ai execute --package /work/buduunkhad-ai/runs/run-001/requests/...
```

The OpenAI and Anthropic SDKs are optional extras (`.[openai]` and `.[anthropic]`). Their keys are
read only when this command executes, from `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`. Keys are never
stored in configuration, request packages, logs, the job ledger, errors, or response files. A
provider-enabled AI configuration must be supplied separately; the committed project configuration
remains legacy, disabled, and offline.

An externally obtained response can instead be imported without claiming this process executed the
provider:

```bash
buduunkhad ai ingest-response --package /work/.../requests/... \
  --response /work/.../externally-supplied-response.json
buduunkhad ai process-response --package /work/.../requests/... \
  --response /work/.../validated-responses/job-....json
```

Ingestion revalidates provider/model, response ID, request fingerprint, prompt/schema identities,
structured output, and every source/tile reference. Processing rechecks the source and ingested
response digests, retains original tile-pixel and transformed-map geometry alongside any repaired
output, applies tile offsets and the recorded affine transform, reprojects when needed to
EPSG:32647, and rejects unsafe geometry rather than clamping it.

The processing command writes an AI_DRAFT GeoPackage and a portable `.qgz` project. Open the QGZ in
QGIS to see source imagery, the seven ordered AI Draft vector layers, and validation findings. The
project uses relative paths and the existing no-PyQGIS writer, so PyQGIS is not a base dependency.

## Phase 03 hybrid review handoff

The Phase 03 bridge is opt-in and remains keyless. It accepts only the exact processed draft bound
to the run's request package, source registration, validated response, locked prompt/schema, and
append-only job ledger:

```bash
buduunkhad ai phase03 import-ai-draft --run-id run-001 \
  --draft /work/buduunkhad-ai/runs/run-001/gis/job_AI_DRAFT.gpkg \
  --review-package /work/buduunkhad-ai/runs/run-001/phase03-review/geology
```

The review directory contains a portable QGIS project, georeferenced copies of the source tiles,
an optional copy of existing Phase 03 evidence, validation findings, read-only `Original AI_DRAFT`
layers, and separate editable `Pending Review` layers. Promotion does not rely on the QGIS flag: it
re-derives and hashes those originals against the ledger-bound draft before accepting them. Saved
or manually obtained responses retain
their actual provider/model identity while `response_origin = saved_response` records that this
workflow did not execute the provider locally.

In QGIS, edit only the pending review layers. Set `review_state = HUMAN_REVIEWED` and
`review_decision` to `accepted`, `accepted_with_edits`, or `rejected`, then record `reviewer`, an
aware ISO-8601 `reviewed_at`, and a non-empty `review_note`. Geometry edits belong only in the
review layer; the original proposal and its pre/post-repair geometry remain separately traceable.
Use `accepted_with_edits` whenever the exact geometry changed.

Promotion is a separate deterministic operation:

```bash
buduunkhad ai phase03 promote-reviewed \
  --review-package /work/buduunkhad-ai/runs/run-001/phase03-review/geology \
  --output /work/buduunkhad-ai/runs/run-001/promotions/accepted-phase03.gpkg
```

`AI_DRAFT`, `HUMAN_REVIEWED`, and `ACCEPTED_EVIDENCE` are separate fields and stages. Promotion
requires complete reviewer metadata, includes only accepted decisions, mints hash-derived stable
feature IDs, preserves original and reviewed geometry provenance, and writes a one-shot audit
sidecar that normal application paths never update or delete. The feature ID represents the
original proposal identity and provenance; the reviewed geometry, decision, reviewer, and note have
separate content digests in the output and audit. IDs therefore remain stable across row order,
package relocation, and accepted geometry edits without conflating those edits with identical
content.
It is idempotent and never modifies the draft, review package, legacy Phase 03 evidence, or an
external publication destination. `ACCEPTED_EVIDENCE` here is a Phase 03 handoff state; it does not
claim production reviewer qualification, `GEOLOGIST_APPROVED`, or publication approval.
Once an output path has been promoted, application code treats its evidence and audit as immutable;
changed decisions require a new versioned output path rather than rewriting the prior record. This
is application-controlled append-only behavior, not cryptographic protection against a filesystem
administrator who can replace both files.
Promotion stages both files, holds an exclusive output lock, and removes a newly created output if
the audit commit fails. Because two filesystem entries cannot be committed as one transaction, an
abrupt process or operating-system failure between final renames can still leave an incomplete
pair; subsequent promotion refuses that state, and a stale `.promotion.lock` requires inspection
before retrying.

Phase 04 continues to use its deterministic fixed-grid comparator. Untagged legacy human evidence
remains compatible, but every AI-lifecycle-labelled layer—including standalone
`ACCEPTED_EVIDENCE`—is ignored until a future authoritative Phase 03-to-04 adapter is adopted.
Copying a draft, review package, or promotion near Phase 04 inputs therefore cannot affect scoring.

The accepted-evidence GeoPackage preserves feature classification, legend code, arbitrary
schema-bound interpretation attributes, confidence components, source references, validation and
repair records, prompt/schema identities, original pixel geometry, deterministic draft geometry,
and reviewed geometry provenance. It remains standalone: this PR does not normalize it into the
legacy 14-column evidence schema or satisfy scientific/geologist approval gates.

## Evaluate

Reference data stays outside Git beneath `BUDUUNKHAD_EVAL_ROOT`. Matching parameters are required
explicitly so this infrastructure introduces no geological or QA/QC threshold:

```bash
buduunkhad ai evaluate --run-id run-001 --candidate /work/.../draft.gpkg \
  --reference /protected/evaluation/reference.gpkg \
  --layers geology_units,faults_structures,mineral_occurrences \
  --match-distance 25 --line-buffer 10 --minimum-iou 0.25
```

The command writes JSON and CSV with counts, validity rate, precision/recall, line overlap,
Hausdorff distance, polygon IoU, position error, and unmatched summaries where applicable.

## Deliberately not included

This slice does not add a QGIS plugin UI, production reviewer-qualification authority, production
publication approval, scheduling/retries, Phase 00 enrichment, broad Phase 01–05 AI behavior, or a
replacement for the Phase 04 deterministic workflow. The Phase 03 handoff supplies a controlled
review and promotion path but does not solve the interpretation bottleneck or mark Phase 03
scientifically complete. The isolated `qgis_process` adapter remains a future-ready boundary for
validity, repair, reprojection, clipping, spatial indexing, and packaging algorithms.
