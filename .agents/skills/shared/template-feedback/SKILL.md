---
name: template-feedback
description: Turn a downstream template discovery into a reusable upstream Issue.
---

# Template feedback

Use this skill when a repository built from a template (a project, or a derived
template that other projects are made from) discovers a defect, missing
capability or cross-project improvement in the template itself.

1. Confirm the behavior is template-level rather than a product-specific bug.
   Check the downstream template version, commit or release tag first.
   Choose the template repository that owns the defective content from the
   registry (`sed -n '/^template:/,/^[^[:space:]]/p' .agents/content-registry.yaml`):
   - In a project, it is `template.repository` at `template.version`. A project
     made from a derived template reports there too, even for content the
     derived template inherited, and never past it.
   - In a derived template (the block has `template.upstream`), content it
     inherited goes to `template.upstream.repository` at
     `template.upstream.version`: a path that exists at that tag, whose text
     above any `## In this repository` section (a script: the whole file) is
     unchanged. A defect in its own content is a local Issue, not feedback.
     When a project's feedback Issue turns out to concern inherited content,
     open the upstream Issue with this skill and link the two Issues.
2. Search the template repository's open and closed Issues for an existing report.
   Reuse the existing Issue when it describes the same underlying problem.
3. Open an Issue in the template repository with:
   - template version and the kind of downstream repository ("a private
     downstream repository" or "a public downstream repository"); name the
     repository only when it is public and its maintainer agrees;
   - concrete reproduction steps and expected behavior;
   - observed behavior and evidence;
   - why the change is cross-project rather than local;
   - a proposed general rule or interface, if known;
   - compatibility, migration and cleanup impact.
4. Keep downstream work moving with a local workaround only when it is clearly
   marked as temporary and linked to the upstream Issue.
   The template repository is public: never include downstream private content,
   credentials, local paths or raw logs in the feedback Issue. Describe only the
   smallest redacted reproduction needed to make the report reusable.
5. When the template change lands, update the downstream project through the
   normal Issue, branch and PR process. Do not copy the template repository's
   history or private development state into the downstream project.

The upstream Issue is the shared improvement channel. Do not send credentials,
private logs or large artifacts; attach redacted evidence or a reproducible
fixture instead.
