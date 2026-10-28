---
name: third-party-llm-compat-patches
date: 2026-10-15
source: Issue #44, from one downstream adopter's benchmark evaluation; placement decided by the template maintainer in that Issue
applies_to: repositories that run third-party tools (benchmarks, agent SDKs, agent CLIs) which call an LLM provider or relay
---

# Compatibility changes to third-party LLM tools live in the repository

## Decision

1. **A compatibility change to a third-party tool the project runs lives in the
   repository.** It is a patch or wrapper applied on every run, together with a
   statement that metrics, prompts and reasoning effort are unchanged. It never
   lives only as edits in a temporary clone.
2. **Before a batch against a relay or provider, capture one request body and
   check it against the target backend's rules.** Remove credentials from the
   body first. Do this for each distinct entry point that sends requests, such as
   each judge, agent or client in the harness.
3. **Do not rely on retry-without-the-parameter fallbacks.** Each first attempt
   is still a failed request upstream, and the request volume doubles.

## Why

A project's tools send requests the project never wrote. In one downstream, a
fix for rejected requests existed only as local edits in a temporary clone of
the benchmark. A fresh clone or another entry point would send the rejected
shapes again, and a second judge in the same harness was never patched. This is
the template's existing rule applied to compatibility changes: state and
changes are not hidden outside the repository.

A relay can fall back to a lenient upstream without telling the client, so a
successful run does not show that the first-choice upstream accepted the
requests. The same run looked healthy locally while the relay's operator saw
far more failed requests than the project's own records showed. A fallback that
retries without the offending parameter has the same effect inside the client.
These hold for any relay or provider.

## Apply

Each project fills one parameter:

- `PATCH_DIR`: where the project keeps its patches or wrappers for third-party
  tools, inside the repository.

Then:

1. When a tool must be changed to work with a backend, add the change to
   `PATCH_DIR` and apply it from the project's run entry point, so a fresh clone
   gets it every run. Record in the patch's description that metrics, prompts
   and reasoning effort are unchanged; if the change would alter any of them, it
   is not a compatibility change and needs its own decision.
2. Before a batch, capture one request body from each distinct sender, strip
   credentials, and check it against the target backend's rules. The current
   facts for GPT-5.x are in
   [`../../knowledge/shared/gpt5-strict-backend-requests.md`](../../knowledge/shared/gpt5-strict-backend-requests.md).
   Check the backend directly when a relay sits in front of it, because the
   relay's success does not show what its first-choice upstream accepted.
3. Fix the request shape. Do not add a retry that drops the rejected parameter.
4. Before committing a patch, captured body, log or Issue text, check that it
   holds no credential value, account, relay operator or machine-local path. See
   [`llm-credentials.md`](llm-credentials.md).
