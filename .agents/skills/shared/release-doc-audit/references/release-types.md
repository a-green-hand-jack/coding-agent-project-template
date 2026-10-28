# Choose what the release needs to explain

Use these differences to select evidence and reader actions, not as a form
every release must fill. All types need background, a comparison scope, an
understandable claim, evidence with limits, an action and traceable references.

| Release object | Emphasis in the narrative | Useful demonstration and evidence | Reader action and boundary |
| --- | --- | --- | --- |
| Product upgrade | What a user can now do and what changes for existing users | Before/after workflow, real usage example; applicable build, regression and real-run evidence for the exact candidate | Installation/upgrade, compatibility, migration and rollback conditions where relevant; distinguish available behavior from plans |
| Results | The question, baseline and measured finding, including its interpretation | Plot/table with units, data/split, method, conditions and uncertainty; artifact and run identities; model/provider only when material | Obtain/reproduce the result; explain generalization limits and what the measurements do not establish |
| Milestone report | What is finished, what remains and why this is a useful checkpoint | A demonstrated path or deliverable plus acceptance status; distinguish working parts from integrated acceptance | Try the completed scope or follow the next milestone; give owners/events for remaining work when known |
| Code archive | What is being preserved, why and what it can still be used for | Fixed source snapshot, provenance, build/reproduction evidence if available, dependency/license context | Retrieve the snapshot; state support, environment and reproducibility limits without implying active maintenance |

Mixed releases can combine these emphases without repeating background or
forcing unrelated fields into a single table. For example, measured results in
a product release still need measurement conditions; a documentation upgrade
does not need an invented benchmark or model inventory.

## A small release

A small fix can be complete in a short opening that names the project, baseline
and user-visible change, one concrete before/after example or compact table,
and a closing paragraph with candidate checks, limitations and the reader's
next action. Finish with the applicable references. Keep the visual useful and
the prose proportional; brevity does not remove evidence or traceability.

## Template upgrade protocol

Keep narrative prose and visuals outside the machine-consumed upgrade
instructions. A template release still needs `### Upgrading ...` followed by
`**Command only.**` when the upgrade command suffices, or numbered manual steps
when it does not. Those steps must describe the candidate's actual migration,
not a hypothetical future tag. A non-template project need not use these
markers. The entrypoint's consistency audit retains the protocol check.
