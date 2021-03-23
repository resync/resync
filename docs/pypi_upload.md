# Updating resync on pypi

Notes to remind @zimeon...

resync is at <https://pypi.python.org/pypi/resync> on pypi

## Putting up a new version

0. In `develop` branch: bump version number in `resync/__init__.py` and check `CHANGES.md` is up to date
1. Check all tests good with appropriate Python 3.x (`python setup.py test` and CI)
2. Check code is up-to-date with github version
3. Check out `master` and merge in `develop`
4. Check all tests still good (`python setup.py test` and CI)
5. Make sure master `README.md` has correct travis-ci icon link
6. Check branches as expected (`git branch -a`)
7. Check local build and version reported OK (`python setup.py build; python setup.py install; resync-sync -h`)
8. Check client works with simulator:

   ```
   # Run simulator in one window
   resync-simulator> ./resync-simulator

   # Run client in another
   resync> rm -rf localhost_8888

   resync> ./resync-sync --baseline --delete http://localhost:8888/
   Using URI mapping: http://localhost:8888/ -> localhost_8888
   Status:     NOT IN SYNC (same=0, to create=1003, to update=0, to delete=0)
   Will GET 1003 resources, and delete 0 resources
   Status:          SYNCED (same=0, created=1003, updated=0, deleted=0)

   resync> ./resync-sync --baseline --delete http://localhost:8888/
   Using URI mapping: http://localhost:8888/ -> localhost_8888
   Status:     NOT IN SYNC (same=1000, to create=2, to update=1, to delete=2)
   Will GET 3 resources, and delete 2 resources
   Status:          SYNCED (same=1000, created=2, updated=1, deleted=2)

   resync> ./resync-sync --incremental --delete http://localhost:8888/
   Using URI mapping: http://localhost:8888/ -> localhost_8888
   Status: CHANGES APPLIED (created=4, updated=5, deleted=4)
   Will apply 13 changes, and delete 4 resources
   Status:      NO CHANGES (created=4, updated=5, deleted=4)

   esync> ./resync-sync --incremental --delete http://localhost:8888/
   Using URI mapping: http://localhost:8888/ -> localhost_8888
   Status: CHANGES APPLIED (created=0, updated=3, deleted=0)
   Will apply 3 changes, and delete 0 resources
   Status:      NO CHANGES (created=0, updated=3, deleted=0)

   resync> ./resync-sync --incremental --delete http://localhost:8888/; ./resync-sync --audit http://localhost:8888/
   Using URI mapping: http://localhost:8888/ -> localhost_8888
   Status: CHANGES APPLIED (created=1, updated=2, deleted=0)
   Will apply 3 changes, and delete 0 resources
   Status:      NO CHANGES (created=1, updated=2, deleted=0)
   Using URI mapping: http://localhost:8888/ -> localhost_8888
   Status:         IN SYNC (same=1001, to create=0, to update=0, to delete=0)
   ```

9. If all checks out OK, tag and push the new version to github:

```
git tag -n1
#...current tags
git tag -a -m "ResourceSync library and client" v2.0.0
git push --tags
```

10. Upload to PyPI


```
rm -r dist
python setup.py sdist bdist_wheel; ls dist
# Should be source and wheel files for just this version
twine upload dist/*
```

10. Check on PyPI at <https://pypi.python.org/pypi/resync>
11. Finally, back on `develop` branch start new version number by editing `resync/__init__.py` and `CHANGES.md`
