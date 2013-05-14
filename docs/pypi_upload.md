=======================
Updating resync on pypi
=======================

Notes to remind zimeon...

resync is at https://pypi.python.org/pypi/resync

Putting up a new version
------------------------

1. Check code is up-to-date with github version
2. Check all tests good (py.test)
3. Check branches as expected (git branch -a)
4. Check version number if set correctly (more resync/_version.py)
5. Check local build and version reported OK (python setup.py install; resync --version)
6. Check client works with simulator:

   ```
   simeon@RottenApple resync>resync --delete http://resync.library.cornell.edu/sim100
   Status: NOT IN SYNC (same=92, to create=0, to update=1, to delete=0)
   Will GET 1 resources, and delete 0 resources
   Status:      SYNCED (same=92, created=0, updated=1, deleted=0)
   simeon@RottenApple resync>resync -i --delete http://resync.library.cornell.edu/sim100
   Status:  NO CHANGES (created=0, updated=0, deleted=0)
   simeon@RottenApple resync>resync -i --delete http://resync.library.cornell.edu/sim100
   Status:     CHANGES (created=1, updated=0, deleted=0)
   simeon@RottenApple resync>resync -i --delete http://resync.library.cornell.edu/sim100
   Status:  NO CHANGES (created=0, updated=0, deleted=0)
   simeon@RottenApple resync>resync -a http://resync.library.cornell.edu/sim100
   Status:     IN SYNC (same=94, to create=0, to update=0, to delete=0)
   simeon@RottenApple resync>resync -a http://resync.library.cornell.edu/sim100
   Status: NOT IN SYNC (same=94, to create=1, to update=0, to delete=0)
   simeon@RottenApple resync>resync -i --delete http://resync.library.cornell.edu/sim100
   Status:     CHANGES (created=1, updated=0, deleted=0)
   simeon@RottenApple resync>resync -a http://resync.library.cornell.edu/sim100
   Status:     IN SYNC (same=95, to create=0, to update=0, to delete=0)
    ```

If all checks out OK, tag and push the new version:

    ```
    git tag -n1
    #...current tags
    git tag -a -m "ResourceSync v0.6 specification, add --paths" v0.6.2
    git push --tags

    python setup.py sdist upload
    ```

Then check on PyPI at https://pypi.python.org/pypi/resync

Finally, start new version number by editing resync/_version.py and CHANGES.md

