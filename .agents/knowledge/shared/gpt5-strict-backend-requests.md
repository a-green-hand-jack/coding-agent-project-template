---
name: gpt5-strict-backend-requests
date: 2026-10-15
source: dated observation of backend error responses during a benchmark evaluation that sent GPT-5.x requests through an OpenAI-compatible relay (Issue #44)
scope: shared
applies_to: repositories whose code, agent CLIs or third-party tools (agent SDKs, LiteLLM, benchmark harnesses) send GPT-5.x requests to a Responses API backend, directly or through a relay
status: active
refresh_after: when a provider changes its request validation, or when a named client changes its default parameters or its routing of GPT-5.x models; otherwise recheck before the next batch against a backend not checked in the last 90 days
supersedes: null
superseded_by: null
---

# GPT-5.x requests that strict Responses backends reject

## Fact

As observed on 2026-10-15, a strict GPT-5.x Responses backend answered HTTP 400
to each of three request shapes. Each has a replacement.

| Rejected shape | Error text | Send instead |
| --- | --- | --- |
| `temperature` (for example `1.0`) on a Responses request; `top_p` is the same kind of sampling parameter | `Unsupported parameter: temperature` | Omit `temperature` and `top_p`. Control reasoning with `reasoning.effort`. |
| A `{"role": "system"}` item in `input` | `System messages are not allowed` | Put the system prompt in the top-level `instructions`, or fold it into the first user message. |
| An output-only field on a replayed `input` item, for example `status` | `Unknown parameter: 'input[N].status'` | Drop output-only fields from every item replayed from an earlier response before sending it back as input. |

A relay can hide these rejections. If the relay's first-choice upstream is
strict and it retries on a more lenient upstream, the client sees success while
the strict upstream has already counted a failed request. Local success is
therefore no evidence that the upstream accepted the request. In the observed
run the relay's operator counted over an order of magnitude more failed
requests than the project's own records showed dead conversations.

Common clients produce these shapes without the project writing them:

- **Agent SDKs routed through LiteLLM.** An SDK whose model configuration holds
  `temperature` sends it to every model. It sends GPT-5-family models to the
  Responses API and replays earlier output items, with their output-only
  fields, as `input`.
- **LiteLLM with a model id it does not know.** With an `openai/` prefix and an
  unrecognized id, LiteLLM does not know which parameters the model rejects, so
  `drop_params: true` did not stop `temperature` reaching the backend.
- **Harnesses that default `temperature`.** A benchmark judge that defaults to
  `--temperature 1.0` and sends a system message produces two of the shapes
  above on its own.

## Evidence

Each error text above is the backend's response as relayed to the client, seen
in one evaluation. The three shapes were then traced to the clients listed. The
facts are the observed responses, not a reading of the provider's documentation,
so a provider changing its validation is what would make them wrong.

## Refresh

Recheck when the condition in `refresh_after` holds. To check a backend, send
one credential-free request body of each shape directly to it and compare the
response with the table; do not infer the answer from a relay's success. Update
the table, the date and `source`, and mark the record superseded if a shape is
now accepted. The decisions that use these facts are in
[`../../memory/shared/third-party-llm-compat-patches.md`](../../memory/shared/third-party-llm-compat-patches.md).
