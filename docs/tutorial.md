
# ResourceSync tutorial exercises using resync

## Writing a Resource Dump

Relative to the base directory of the github distribution there is a directory
`tests/testdata/dir1` with two files, `file_a` and `file_b`. We can create
a Resource Dump of this directory, as if it were mapped to `http://example.com/dir1`,
with the following:

```
resync> ./resync-build -v --write-resourcedump --outfile /tmp/rd http://example.com/dir1 tests/testdata/dir1
Scanning disk from tests/testdata/dir1
Writing resource dump to True...
Total size of files to include in dump 65 bytes
Writing sitemap /tmp/rd00000.xml...
Wrote sitemap /tmp/rd00000.xml
Wrote ZIP file dump /tmp/rd00000.zip with size 623 bytes
Wrote 1 dump files
resync> zipinfo /tmp/rd00000.zip
Archive:  /tmp/rd00000.zip
Zip file size: 623 bytes, number of entries: 3
?rw-------  2.0 unx      453 b- defN 20-Dec-16 10:58 manifest.xml
-rw-r--r--  2.0 unx       20 b- defN 12-Jul-25 13:13 file_a
-rw-r--r--  2.0 unx       45 b- defN 01-Sep-08 21:46 file_b
3 files, 518 bytes uncompressed, 325 bytes compressed:  37.3%
```

This can then be unpacked and the files checked:

```
resync> mkdir /tmp/rd
mkdir: /tmp/rd: File exists
resync> cd /tmp/rd
rd> unzip ../rd00000.zip
Archive:  ../rd00000.zip
  inflating: manifest.xml            
  inflating: file_a                  
  inflating: file_b                  
rd> more manifest.xml
<?xml version='1.0' encoding='UTF-8'?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/"><rs:md capability="resourcedump-manifest" /><url><loc>http://example.com/dir1/file_a</loc><lastmod>2012-07-25T17:13:46Z</lastmod><rs:md length="20" path="file_a" /></url><url><loc>http://example.com/dir1/file_b</loc><lastmod>2001-09-09T01:46:40Z</lastmod><rs:md length="45" path="file_b" /></url></urlset>
rd> more file_a
I am file a in dir1
rd> more file_b
I am file b in dir1, I am bigger than file_a
```
