# Updating resync on pypi

Notes to remind @zimeon...

resync is at <https://pypi.python.org/pypi/resync> on pypi

## Putting up a new version

0. In `develop` branch: bump version number in `resync/_version.py` and check `CHANGES.md` is up to date
1. Check all tests good with appropriate Python 3.x (`python setup.py test` and CI)
2. Check code is up-to-date with github version
3. Check out `master` and merge in `develop`
4. Check all tests still good (`python setup.py test` and CI)
5. Make sure master `README.md` has correct travis-ci icon link
6. Check branches as expected (`git branch -a`)
7. Check local build and version reported OK (`python setup.py build; python setup.py install; resync.py --version`)
8. Check client works with simulator:

   ```
   simeon@RottenApple resync>resync.py --delete --capabilitylist=http://resync.library.cornell.edu/sim100/capabilitylist.xml http://resync.library.cornell.edu/sim100
   Status: NOT IN SYNC (same=92, to create=0, to update=1, to delete=0)
   Will GET 1 resources, and delete 0 resources
   Status:      SYNCED (same=92, created=0, updated=1, deleted=0)
   simeon@RottenApple resync>resync.py -i --delete --capabilitylist=http://resync.library.cornell.edu/sim100/capabilitylist.xml http://resync.library.cornell.edu/sim100
   Status:  NO CHANGES (created=0, updated=0, deleted=0)
   simeon@RottenApple resync>resync -i --delete --capabilitylist=http://resync.library.cornell.edu/sim100/capabilitylist.xml http://resync.library.cornell.edu/sim100
   Status:     CHANGES (created=1, updated=0, deleted=0)
   simeon@RottenApple resync>resync.py -i --delete --capabilitylist=http://resync.library.cornell.edu/sim100/capabilitylist.xml http://resync.library.cornell.edu/sim100
   Status:  NO CHANGES (created=0, updated=0, deleted=0)
   simeon@RottenApple resync>resync.py -a --capabilitylist=http://resync.library.cornell.edu/sim100/capabilitylist.xml http://resync.library.cornell.edu/sim100
   Status:     IN SYNC (same=94, to create=0, to update=0, to delete=0)
   simeon@RottenApple resync>resync.py -a --capabilitylist=http://resync.library.cornell.edu/sim100/capabilitylist.xml http://resync.library.cornell.edu/sim100
   Status: NOT IN SYNC (same=94, to create=1, to update=0, to delete=0)
   simeon@RottenApple resync>resync.py -i --delete --capabilitylist=http://resync.library.cornell.edu/sim100/capabilitylist.xml http://resync.library.cornell.edu/sim100
   Status:     CHANGES (created=1, updated=0, deleted=0)
   simeon@RottenApple resync>resync.py -a --capabilitylist=http://resync.library.cornell.edu/sim100/capabilitylist.xml http://resync.library.cornell.edu/sim100
   Status:     IN SYNC (same=95, to create=0, to update=0, to delete=0)
   ```

9. If all checks out OK, tag and push the new version to github:

    ```
    git tag -n1
    #...current tags
    git tag -a -m "ResourceSync v1.0 specification, add --delay" v2.0.0
    git push --tags

    python setup.py sdist upload
    ```

10. Then check on PyPI at <https://pypi.python.org/pypi/resync>
11. Finally, back on `develop` branch start new version number by editing `resync/_version.py` and `CHANGES.md`
