# Veritas Hiring Release — Source Manifest

**Release:** `iem-work-sample-v1`
**Status:** Curated source-only release; corpus excluded pending rights review
**Last reviewed:** 2026-09-01

## Included source policy

The hiring branch includes source code and documentation describing the Veritas workflow. It does not include copied raw documents, generated embeddings, synthesis history, client material, or private 8825 strategy content.

## Intended demo source categories

| Category | Intended role | Hiring release status |
|---|---|---|
| Official public technical documentation | Authoritative specification context | Excluded from branch pending redistribution review |
| Public vendor or implementation guidance | Practical implementation context | Excluded from branch pending source-rights review |
| Public failure/debugging material | Failure and risk context | Excluded from branch pending source-rights review |
| Synthetic demo records | Safe test fixtures for future local reproduction | Not included in this release |

## Live deployment observation

The separately deployed live demo was checked on 2026-09-01:

- URL: `https://veritas.8825.systems`
- Health: `healthy`
- Loaded chunks reported by `/api/health`: `74`
- Canonical query: `How do I implement Claude tool use with error handling?`
- Observed response: structured ideas, three source tiers, full source coverage, approximately 1.7–1.8 citations per paragraph.

The live deployment was not changed by this release. The hiring branch does not claim to contain or reproduce the deployed corpus.

## Explicit exclusions

The following are excluded from the hiring release:

- Client, employer, or private 8825 material.
- RAL, HCSS, Reinsurance Associates, or other client workflow data.
- API keys, credentials, private URLs, local filesystem paths, and environment files.
- `history/synthesis_history.json` and backend history persistence.
- Raw third-party documentation and copied source bodies whose redistribution rights are not confirmed.
- Generated embeddings and large corpus snapshots.
- Placeholder `example.com` source records.
- Failed tests, test result directories, and stale screenshots.
- Internal migration, deployment, setup, phase-planning, and editor workflow notes.

## Future local corpus requirements

Before adding any local demo corpus, each source must be:

1. Publicly accessible or explicitly licensed for redistribution.
2. Short enough to include only what the demo needs.
3. Attributed with a verified canonical URL.
4. Free of client, personal, credential, and private operational data.
5. Marked as official, practice, failure, or synthetic.
6. Reflected consistently in the README, manifest, runtime behavior, and demo recording.

## Current decision

Do not add the corpus to this branch solely to make local execution appear turnkey. The live demo is the executable surface; this branch is the reviewed source and scope surface. A future synthetic corpus may be added only after the source and privacy checks above pass.
