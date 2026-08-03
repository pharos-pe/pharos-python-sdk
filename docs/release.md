# Release Process

The SDK follows Semantic Versioning independently from the `/api/v1` API version.

1. Update `CHANGELOG.md` — replace `Unreleased` with the date.
2. Run `ruff check .`, `mypy --no-site-packages pharos_sdk`, and `pytest`.
3. Create a signed tag such as `v0.1.0`, and push it. GitHub Actions runs the tests on every
   supported Python and then publishes to PyPI through Trusted Publishing.

```bash
git tag -s v0.1.0 -m "Pharos Python SDK 0.1.0"
git push origin main v0.1.0
```

## One-time setup

**The PyPI publisher.** Trusted Publishing has to know the workflow before the project exists on
PyPI, or the publish step fails after a green test run. On pypi.org → *Your account* → *Publishing* →
**Add a pending publisher**: project `pharos-sdk`, owner `pharos-pe`, repository
`pharos-python-sdk`, workflow **`ci.yml`** (the file name, not the workflow's display name), and an
**empty** environment — the job declares none, and a value here is compared literally.

**Signing.** `git tag -s` needs a signing key. SSH is enough and needs no GPG:

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_rsa.pub
git config --global gpg.ssh.allowedSignersFile ~/.config/git/allowed_signers
printf 'you@example.com %s\n' "$(cat ~/.ssh/id_rsa.pub)" >> ~/.config/git/allowed_signers
```

The same key must also be registered on GitHub a **second** time, as a *Signing Key*: an
authentication key does not verify signatures, and a tag signed with one reports
`verified: false, reason: unknown_key` until it is. `git tag -v v0.1.0` prints `Good "git" signature`
when the local side is right; GitHub re-checks its own list and marks past tags Verified
retroactively, so there is nothing to re-tag.

## What can go wrong

**Nothing is published until the tests pass and the tag matches `version.py`.** That guard reads the
`__version__` assignment — it once matched the module docstring instead and refused every tag. If you
change it, run the step's own script against a matching and a mismatching tag before tagging again.

**A version is final.** PyPI never accepts the same version twice, and deleting a release does not
free the number. If a release is wrong, the only way forward is the next version.

**Re-tagging is safe only before publication.** `v0.1.0` was moved after a fix because nothing had
been uploaded yet. Once a version is on PyPI its tag is a fixed point others depend on.

## After publishing

- `gh release create vX.Y.Z --title "X.Y.Z" --notes-file <the changelog section> --verify-tag`.
  `--verify-tag` refuses to create a release for a tag that is not on the remote.
- Confirm the package page renders: https://pypi.org/project/pharos-sdk/
