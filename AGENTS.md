# RTCW NextGen

Read [HANDOFF](docs/rtcwnextgen/HANDOFF.md), [STATUS](docs/rtcwnextgen/STATUS.md) and the [acceptance ledger](docs/rtcwnextgen/ACCEPTANCE.md) before choosing a task. Verify the current Git history and resume the recorded task when its dependencies are met.

- Use the current Codex Cloud checkout and the integration branch `rtcwnextgen-prototype`. Use a reviewed PR for `master`. Preserve local work and pinned upstream/submodule commits.
- Keep proprietary game data outside Git, CI artifacts and releases. Use synthetic fixtures in CI and treat licensed installations as read-only inputs.
- Run the build and checks described in [TESTING](docs/rtcwnextgen/TESTING.md). Record actual exit codes, test outcomes, GPU evidence and remaining blockers in STATUS. Advance past a phase when its required checks pass.
- Use [RELEASE-PROCESS](docs/rtcwnextgen/RELEASE-PROCESS.md) for engineering artifacts, game checkpoints and promotion. Record every accepted artifact with its commit and checksum.
