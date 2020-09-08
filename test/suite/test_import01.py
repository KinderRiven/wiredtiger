#!/usr/bin/env python
#
# Public Domain 2014-2020 MongoDB, Inc.
# Public Domain 2008-2014 WiredTiger, Inc.
#
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# test_import01.py
# Import a file into a running database.

import os, shutil
import wiredtiger, wttest

def timestamp_str(t):
    return '%x' % t

class test_import01(wttest.WiredTigerTestCase):
    conn_config = ('cache_size=50MB,log=(enabled),statistics=(all)')
    session_config = 'isolation=snapshot'

    def update(self, uri, key, value, commit_ts):
        cursor = self.session.open_cursor(uri)
        self.session.begin_transaction()
        cursor[key] = value
        self.session.commit_transaction('commit_timestamp=' + timestamp_str(commit_ts))
        cursor.close()

    def copy_file(self, file_name, old_dir, new_dir):
        if os.path.isfile(file_name) and "WiredTiger.lock" not in file_name and \
            "Tmplog" not in file_name and "Preplog" not in file_name:
            shutil.copy(os.path.join(old_dir, file_name), new_dir)

    def test_file_import(self):
        original_db_file = 'original_db_file'
        uri = 'file:' + original_db_file

        # mongodb create config
        create_config_mdb_4k = ('access_pattern_hint=none,allocation_size=4K,app_metadata=,assert=(commit_timestamp=none,durable_timestamp=none,read_timestamp=none),block_allocation=best,block_compressor="zlib",cache_resident=false,checksum="uncompressed",colgroups=,collator=,columns=,dictionary=0,encryption=(keyid=,name=),exclusive=false,extractor=,format=btree,huffman_key=,huffman_value=,ignore_in_memory_cache_size=false,immutable=false,internal_item_max=0,internal_key_max=1607,internal_key_truncate=true,internal_page_max=65536,key_format=u,key_gap=14,leaf_item_max=0,leaf_key_max=98,leaf_page_max=4096,leaf_value_max=40960,log=(enabled=true),memory_page_image_max=0,memory_page_max=4194304,os_cache_dirty_max=0,os_cache_max=0,prefix_compression=false,prefix_compression_min=4,source=,split_deepen_min_child=0,split_deepen_per_child=0,split_pct=86,type=file,value_format=u')
        # mongodb create config with allocation_size=512B
        create_config_mdb_512 = ('access_pattern_hint=none,allocation_size=512B,app_metadata=,assert=(commit_timestamp=none,durable_timestamp=none,read_timestamp=none),block_allocation=best,block_compressor="zlib",cache_resident=false,checksum="uncompressed",colgroups=,collator=,columns=,dictionary=0,encryption=(keyid=,name=),exclusive=false,extractor=,format=btree,huffman_key=,huffman_value=,ignore_in_memory_cache_size=false,immutable=false,internal_item_max=0,internal_key_max=1607,internal_key_truncate=true,internal_page_max=65536,key_format=u,key_gap=14,leaf_item_max=0,leaf_key_max=98,leaf_page_max=4096,leaf_value_max=40960,log=(enabled=true),memory_page_image_max=0,memory_page_max=4194304,os_cache_dirty_max=0,os_cache_max=0,prefix_compression=false,prefix_compression_min=4,source=,split_deepen_min_child=0,split_deepen_per_child=0,split_pct=86,type=file,value_format=u')

        create_config = create_config_mdb_512
        self.session.create(uri, create_config)

        # Add some data.
        self.update(uri, b'1', b'\x01\x02aaa\x03\x04', 10)
        self.update(uri, b'2', b'\x01\x02bbb\x03\x04', 20)

        # Perform a checkpoint.
        self.session.checkpoint()

        # Add more data.
        self.update(uri, b'3', b'\x01\x02ccc\x03\x04', 30)
        self.update(uri, b'4', b'\x01\x02ddd\x03\x04', 40)

        # Perform a checkpoint.
        self.session.checkpoint()

        # Close the connection.
        self.close_conn()

        # Create a new database and connect to it.
        newdir = 'IMPORT_DB'
        shutil.rmtree(newdir, ignore_errors=True)
        os.mkdir(newdir)
        self.conn = self.setUpConnectionOpen(newdir)
        self.session = self.setUpSessionOpen(self.conn)
        self.session.create('table:db_table', create_config)

        # Copy over the datafiles for the object we want to import.
        self.copy_file(original_db_file, '.', newdir)

        # Import the file.
        self.session.live_import(uri)

        # Verify object.
        self.session.verify(uri)

        # Add some data.
        self.update(uri, b'5', b'\x01\x02eee\x03\x04', 50)
        self.update(uri, b'6', b'\x01\x02fff\x03\x04', 60)

        # Perform a checkpoint.
        self.session.checkpoint()


if __name__ == '__main__':
    wttest.run()
