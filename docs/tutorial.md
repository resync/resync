============================================
ResourceSync tutorial exercises using resync
============================================


Writing a Resource Dump
-----------------------

Relative to the base directory of the github distribution there is a directory
'resync/test/testdata/dir1' with two files, 'file_a' and 'file_b'. We can create 
a Resource Dump of this directory, as if it were mapped to 'http://example.com/dir1',
with the following:

'''
simeon@RottenApple resync>resync --resourcedump --outfile /tmp/rd.zip http://example.com/dir1 resync/test/testdata/dir1
Total size of files to include in dump 65 bytes
Wrote ZIP file dump /tmp/rd.zip with size 595 bytes

simeon@RottenApple resync>zipinfo /tmp/rd.zip 
Archive:  /tmp/rd.zip
Zip file size: 595 bytes, number of entries: 3
?rw-------  2.0 unx      409 b- defN 13-May-28 18:40 manifest.xml
-rw-r--r--  2.0 unx       20 b- defN 12-Jul-25 13:13 file_a
-rw-r--r--  2.0 unx       45 b- defN 01-Sep-08 21:46 file_b
3 files, 474 bytes uncompressed, 297 bytes compressed:  37.3%
'''

This can then be unpacked and the files checked:

'''
simeon@RottenApple resync>mkdir /tmp/rd
simeon@RottenApple resync>cd /tmp/rd
simeon@RottenApple rd>unzip ../rd.zip 
Archive:  ../rd.zip
  inflating: manifest.xml            
  inflating: file_a                  
  inflating: file_b                  
simeon@RottenApple rd>more manifest.xml 
<?xml version='1.0' encoding='UTF-8'?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:rs="http://www.openarchives.org/rs/terms/"><url><loc>http://example.com/dir1/file_a</loc><lastmod>2012-07-25T17:13:46Z</lastmod><rs:md length="20" path="file_a" /></url><url><loc>http://example.com/dir1/file_b</loc><lastmod>2001-09-09T01:46:40Z</lastmod><rs:md length="45" path="file_b" /></url></urlset>
simeon@RottenApple rd>more file_a 
I am file a in dir1
simeon@RottenApple rd>more file_b 
I am file b in dir1, I am bigger than file_a
'''
