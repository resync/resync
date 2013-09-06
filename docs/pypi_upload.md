=======================
Updating resync on pypi
=======================

Notes to remind zimeon...

resync is at https://pypi.python.org/pypi/resync

Putting up a new version
------------------------

0. In dev branch: bump version number in resync/_version.py and check CHANGES.md is up to date
1. Check all tests good (python setup.py test; py.test)
2. Check code is up-to-date with github version
3. Check out master and merge in dev
4. Check all tests good (python setup.py test; py.test)
5. Check branches as expected (git branch -a)
6. Check local build and version reported OK (python setup.py build; sudo python setup.py install; resync --version)
7. Check client works with simulator:

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

8. If all checks out OK, tag and push the new version to github:

    ```
    git tag -n1
    #...current tags
    git tag -a -m "ResourceSync v0.9 specification, add --paths" v0.9.3
    git push --tags

    python setup.py sdist upload
    ```

9. Then check on PyPI at https://pypi.python.org/pypi/resync
10. Finally, back on dev branch start new version number by editing resync/_version.py and CHANGES.md

