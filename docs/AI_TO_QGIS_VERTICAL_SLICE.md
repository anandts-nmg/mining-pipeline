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

This slice does not add a QGIS plugin UI, human approval authority, production publication
approval, scheduling/retries, Phase 00 enrichment, Phase 01–05 AI behavior, or a replacement for
the Phase 04 deterministic workflow. The isolated `qgis_process` adapter is only a future-ready
boundary for validity, repair, reprojection, clipping, spatial indexing, and packaging algorithms.
Later phase integration must remain additive and retain the legacy regression baseline.
