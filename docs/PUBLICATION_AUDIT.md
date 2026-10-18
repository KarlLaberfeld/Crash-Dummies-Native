# Publication audit - October 18, 2026

This technical review prepares Crash Dummies Native's description and distribution
for a possible visibility change. **It does not authorize publication of protected
game expression, clear trademark rights, or certify the port's fidelity.**
Repository visibility was not changed by this work.

## Inspected baseline

GitHub repository: `KarlLaberfeld/Crash-Dummies-Native`.
All advertised branches and tags were fetched into an isolated local bare audit
repository, independently of the development checkout:

- `main`: `70f446a1a566c7fe99433747816035f930cfb2c9`
- `v0.1.0-alpha.1`: the same commit
- 76 reachable commits and 925 distinct historical file blobs.

All historical file contents, filenames, commit messages, author/committer
metadata and available tag objects were scanned. The GitHub API was paginated
for releases, issues, pull requests, issue/review comments and Actions data.
The API reported one release with four assets and no issues, pull requests,
comments, workflow definitions, workflow runs or Actions artifacts. No issue or
release-body attachment URLs were present. Wiki, Discussions and Pages were
disabled, so there were no enabled additional publishing surfaces to inspect.

## Findings

- No binary Git blobs or historical ROM, extracted-data, image/audio/video,
  archive, emulator-DLL or executable paths were found in the published history.
- No embedded base64 media candidate was found.
- No credential candidate matched the checks for GitHub/OpenAI/Slack/AWS/Google
  keys, private-key headers, JWTs, bearer literals, credential-bearing URLs,
  connection secrets, Azure signatures or quoted credential assignments.
- Commit metadata uses a GitHub noreply identity. The other email match is a
  GitHub signing-system identity. No personal mailbox was identified.
- The apparent `/users/` path matches were GitHub API profile URLs, not personal
  filesystem paths. No personal Windows user-directory path was identified.
- There was no finding requiring credential rotation or Git-history rewriting.

The patterns are a bounded automated check followed by classification of the
matches, not a guarantee that every possible secret or protected expression is
detectable. Source code reconstructed from the original is present; its legal
status is a separate question documented in [PROVENANCE.md](PROVENANCE.md).

## Release verification

All four actual GitHub release assets were downloaded and their SHA-256 digests
checked against GitHub's asset metadata. Downloads followed signed redirects
without forwarding GitHub credentials to another host.

The downloaded Windows ZIP passed the same strict 16-file allowlist and complete
manifest/hash checks used during packaging. It contains the EXE, extraction
tools, MIT license, notices and build metadata. No ROM, extracted `.dat` files,
reference emulator or original recordings are packaged. Text and printable
binary strings were included in the credential/path inspection; arbitrary
binary semantics and copyright ownership cannot be established by this scan.

- ZIP SHA-256: `b7383693aae45e412f22a7e70a8c64b7987daa352877274aa15f38d668b455b0`
- EXE SHA-256: `9a0013df578f7b5b024d8486f6546574df69bc4860025fdadb3e952041d67bf4`

## Description changes and remaining decisions

The current README, release description and future package template use
visibility-neutral wording. They retain the unofficial-project statement, alpha
status, original-ROM requirement, MIT scope and explicit limits on timing,
audio/images, physical controller testing and missing save/configuration features.
The issue template asks reporters to remove credentials and private details.

The already versioned alpha ZIP and its validation attachment retain their
original creation-time wording, including references to the private evaluation
environment. Those artifacts, their tag and checksums were not silently replaced.
Their wording records the release's original context rather than a promise about
future repository visibility.

Remaining before a visibility change: assess rights in reconstructed code and
the project name separately; recheck any subsequently added files, refs, releases,
issues or Actions output. A public GitHub repository can be copied and forked;
later making it private cannot withdraw those copies. No public switch, history
rewrite, additional license grant or final-release claim is part of this audit.

Detailed machine-readable findings and downloaded inspection copies remain in
the ignored local workspace. This report intentionally contains no credentials,
personal local paths or raw private diagnostic logs.
