# Acceptance and message cadence scenarios

These are provider-free review cases for
[write responsibility](../../issue-workflow/SKILL.md#acceptance-write-responsibility)
and [message cadence](../SKILL.md#message-cadence). Walk each case against the
rules and record the outcome locally. They do not implement a lock, execute
Herdr, prove a live exchange or justify injecting conflicts into a real run.

| Case | Situation | Required decision and evidence |
| --- | --- | --- |
| Normal handoff | Worker finishes a base plus saved diff; coordinator will test it. | Worker combines ready-for-review with explicit pause, protected inputs and allowed outputs. Owner ACKs; after every writer ACK and version check, acceptance starts. Record identities, version, commands and run. |
| Missing writer ACK | One writer is idle or its queue accepted the pause request, without explicit confirmation. | Do not start acceptance on that checkout. Keep the pending writer/owner and recovery condition; independent read-only work continues. |
| New authorized edit | A new user request arrives during acceptance. | Authorization to change scope does not release the pause. End/invalidate old acceptance, establish stopped/isolated run evidence, explicitly return/ACK responsibility, edit and verify the new version. |
| Mid-run drift | An input changed and was restored; HEAD and final status match. | Invalidate affected evidence, preserve the observed interference and notify promptly. Reconcile/stop/isolate and hand back before edits, then recheck; endpoint equality is insufficient. |
| Crash or lost contact | Owner disappears or a writer restarts while the run may survive. | Read saved run/boundary/receipts. Keep protected writes paused until run state is known and authorized transfer is ACKed; timeout never transfers ownership. |
| Completed return | Checks have finished and no process still reads protected inputs. | Owner combines exact-version result and explicit return. Writer ACKs receipt of responsibility, possibly in its combined result; no ACK-of-ACK. Pending review/delivery duties remain named. |
| Immutable snapshot | Acceptance reads an independently immutable copy. | Preserve source HEAD/diff and input digests, enforce/verify isolation and route outputs elsewhere. Development checkout can change; a plain copy or checksum alone does not qualify. |
| Allowed output | Tests write logs under the agreed state root. | Permit declared output writes while inputs stay protected. Do not classify a consumed configuration or fixture as unrestricted output. |
| Critical events | A blocker, failure, transfer or head update changes the receiver's next action. | Notify promptly with evidence and owner. Require transfer ACK before dependent action; do not hold the event for routine batching. |
| Combined milestone | Implementation, checks and an authorized PR creation finish at one checkpoint/version. | One message retains all event IDs, PR URL/version, outcomes and duties; routine progress stays local. No critical event is dropped. |
| Duplicate event | The same task/attempt/event arrives again. | Record disposition without repeating actions. Return the existing receipt only if the sender still needs confirmation; conflicting same-ID content needs reconciliation. |
| ACK loop | Receiver gets a pure ACK, or an ACK carrying a new transfer. | Pure ACK updates receipt without a reply. Only a new transfer needs its own explicit confirmation, identifying that obligation. |
| Bounded retry | Initial queue fails or receipt is absent. | Preserve exact failure and state; at most one retry after a changed precondition or active checkpoint with fresh preflight. Fallback counts as retry. Exhaustion retains owner/escalation; no timer loop. |
| Independent work | A result receipt is pending during useful work. | Continue independent tasks/read-only review. Do not continuously wait or inspect unchanged state; recover from durable receipts at the next active checkpoint. |

For real acceptance, use only the authorized participants and checkout. Record
their agent/provider/model/effort and why this exchange is needed. Save the
version, boundary, pause/owner ACKs, actual check commands and outputs, stopped
run evidence, explicit return and the recipient's combined result/return ACK.
Keep submission separate from receipt and completed acceptance. Scenario review
covers adverse branches; it does not claim those failures happened live. A pure
receipt ends the acknowledgement chain, and no unrelated session is contacted.
