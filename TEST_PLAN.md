# Prototype test plan

## Phase 0 — feasibility (week 1)
- Collect a consented/approved pilot set of 20–30 dogs in varied outdoor lighting.
- Capture repeated short nose clips per dog at different times and distances.
- Measure frame-selection rate, usable-crop rate, recognition accuracy, false match rate, false rejection rate and processing time.
- Use dog-disjoint train/validation/test splits where appropriate; avoid testing against the same capture session only.
- Record conditions and failure cases. Decide GO / REVIEW / STOP before expanding.

## Functional checks
1. `GET /api/health` returns status ok.
2. Register a dog with a valid image/video; confirm a unique LB-xxxxx ID and QR PNG.
3. Register another dog; confirm the ID differs.
4. Upload a malformed file; verify a helpful error rather than a server crash.
5. Submit a clear image/video to the lookup endpoint; confirm a structured response.
6. Test low-quality/blurred media; confirm retry guidance.
7. Check public API output never includes caregiver phone numbers or raw embeddings.
8. Update a record with `PATCH /api/dogs/{dog_id}`.
9. Check QR tag is downloadable.
10. Test mobile layout and keyboard navigation.

## Evaluation and claims
- Similarity score is not accuracy or a probability.
- Do not claim a success percentage until measured against a held-out, labelled field dataset.
- Record false matches separately: wrongly identifying one dog as another can cause harmful downstream decisions.
- Keep QR/manual review available when image quality or score is uncertain.
