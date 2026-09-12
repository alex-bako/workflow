# Releases and marketplace installation

Both clients install the same plugin from a Git-hosted marketplace. `stable`
points to the last successfully released commit; `main` is for development.
The clients manage their own checkout/cache. No manual clone, npm package,
additional registry, model API call or release secret is needed to install it.
This is a public repository marketplace, not a listing in either vendor's
curated plugin directory.

## Installations and updates

Use the commands in the [README](../README.md). To pin a release, replace Claude's
`#stable` with `#v0.6.0`, or Codex's `--ref stable` with `--ref v0.6.0`.
Pinned installations stay on that tag until you change the registered source.
Do not register a raw `marketplace.json` URL: the plugin entry uses a path inside
the repository, so the client needs a Git source.

For an existing **Claude local installation**, inspect
`claude plugin marketplace list` first. If `agentic-workflow` points to your local
clone, uninstall only `agentic-workflow@agentic-workflow`, remove that marketplace
with `claude plugin marketplace remove agentic-workflow`, then follow the README.

For the old **Codex `personal` installation**, inspect
`codex plugin marketplace list` and `codex plugin list` first. Remove only the old
plugin using `codex plugin remove agentic-workflow@personal`, then install the new
`agentic-workflow` marketplace. Keep `personal` if it supplies any other plugins.
If the target marketplace name already exists, check its source and remove that
registration only if it belongs to this repository before adding the remote one.

Existing project plans and checkpoints stay in your project. Existing agent
profiles and Claude settings stay in your client configuration. `aw-setup` refuses
to replace conflicting profiles; inspect and reconcile such differences explicitly
before rerunning setup. It does not guess whether an edited profile is disposable.

## Publish a release

1. Update `version` in both `plugins/agentic-workflow/.codex-plugin/plugin.json`
   and `.claude-plugin/plugin.json` to the same new **X.Y.Z**. Do not reuse a
   published version or put versions in marketplace entries. Client caches rely
   on version changes to detect plugin updates.
2. Run `python3 scripts/check_release.py` and
   `python3 -m unittest discover -s tests -v`. Commit and push to `main`; wait for CI.
3. Tag that commit and push the tag (substitute the new version):

   ```sh
   git tag -a v0.6.0 -m 'Release 0.6.0'
   git push origin v0.6.0
   ```

The Release action independently checks both marketplace entry points, matching
manifest/tag versions, main-branch ancestry and all tests. It creates a GitHub
release with generated notes and GitHub's automatic source ZIP/tar downloads,
then fast-forwards `stable` to the tested commit. Release runs are serialized;
an older or divergent commit cannot move `stable` backward, and a new release
must have a higher SemVer than the current stable release. CI has read-only
permissions; only the release job receives `contents: write`.

Check the [Actions runs](https://github.com/alex-bako/workflow/actions) and
[releases](https://github.com/alex-bako/workflow/releases). A published release is
not available through `stable` until the promotion step succeeds. Rerun a failed
job after fixing an external failure; an existing published release is reused.
Resolve an existing draft explicitly. If code needs fixing, publish a new version
and tag. Never move a published tag or force-push `stable`.

## Research and compatibility

Verified with Claude Code 2.1.269 and Codex CLI 0.154.0. The existing vendor
manifests remain supported; no portable-manifest migration is needed for this
release. Sources checked September 12, 2026:

- [OpenAI plugin packaging and Git marketplaces](https://developers.openai.com/plugins/build/plugins)
- [Claude marketplace sources and versioning](https://code.claude.com/docs/en/plugin-marketplaces)
- [Claude installation, ref selection and updates](https://code.claude.com/docs/en/discover-plugins)
- [GitHub tag-triggered workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- [GitHub workflow permissions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)

The marketplace JSON is checked locally and in CI, alongside the workflow tests.
For changes to marketplace schema, also validate with the installed clients and
smoke-test registration and installation using isolated client configuration
folders before telling users the release is ready.
