## Release checklist

### Preparing a release candidate:
- [ ] tests pass on `main` branch
- [ ] `dgbowl-schemas` released and updated in `pyproject.toml`
- [ ] `__latest_recipe__` in `src/dgpost/utils/parse.py` updated
- [ ] `docs/version.rst` updated to include new version file
- [ ] `docs/version.vX.Y.rst` created

### Preparing a full release
- [ ] `docs/version.vX.Y.rst` release date updated
- [ ] a tagged release candidate passes `integration-test`

### After release
- [ ] pypi packages built and uploaded
- [ ] docs built and deployed