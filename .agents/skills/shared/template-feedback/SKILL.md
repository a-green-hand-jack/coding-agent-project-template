---
name: template-feedback
description: Turn a downstream template discovery into a reusable upstream Issue.
---

# Template feedback

Use this skill when a project created from this template discovers a defect,
missing capability or cross-project improvement in the template itself.

1. Confirm the behavior is template-level rather than a product-specific bug.
   Check the downstream template version, commit or release tag first.
2. Search the template repository's open and closed Issues for an existing report.
   Reuse the existing Issue when it describes the same underlying problem.
3. Open an Issue in the template repository with:
   - template version and downstream repository;
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
