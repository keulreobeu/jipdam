import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import download_shared_data as download


class DownloadSharedDataTests(unittest.TestCase):
    def test_drive_form_keeps_uuid_and_rejects_wrong_file_or_host(self):
        page = '<form id="download-form" method="get" action="https://drive.usercontent.google.com/download">' + ''.join(
            f'<input type="hidden" name="{key}" value="{value}">' for key,value in
            [('id','approved-id'),('export','download'),('confirm','t'),('uuid','provider-uuid')]) + '</form>'
        url = download._confirmation_url(page, 'approved-id')
        self.assertIn('uuid=provider-uuid', url)
        self.assertTrue(url.startswith('https://drive.usercontent.google.com/download?'))
        for changed in (page.replace('approved-id','other-id'), page.replace('drive.usercontent.google.com','attacker.example')):
            with self.assertRaises(ValueError): download._confirmation_url(changed,'approved-id')

    def test_verified_parts_publish_once_and_existing_output_is_preserved(self):
        chunks = [b'first part', b'second part']
        digest = lambda content: hashlib.sha256(content).hexdigest()
        package = {'archive_name':'test.zip','bytes':sum(map(len,chunks)),'sha256':digest(b''.join(chunks)),
                   'files':[{'id':str(i),'name':f'test.zip.part{i}','bytes':len(chunk),'sha256':digest(chunk)} for i,chunk in enumerate(chunks)]}
        def fetch(file, target, opener): target.write_bytes(chunks[int(file['id'])])
        with tempfile.TemporaryDirectory() as temporary, patch.dict(download.PACKAGES, {'molit':package}), patch.object(download,'download_file',side_effect=fetch) as mocked:
            target = Path(temporary)/'new'
            paths = download.download_package('molit',target)
            self.assertEqual((target/'test.zip').read_bytes(),b''.join(chunks))
            self.assertEqual(len(paths),3)
            with self.assertRaises(ValueError): download.download_package('molit',target)
            self.assertEqual(mocked.call_count,2)
            self.assertEqual((target/'test.zip').read_bytes(),b''.join(chunks))

    def test_bad_assembled_hash_never_publishes_output(self):
        content=b'changed'
        package={'archive_name':'test.zip','bytes':len(content),'sha256':'0'*64,
                 'files':[{'id':'id','name':'test.zip.part001','bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()}]}
        with tempfile.TemporaryDirectory() as temporary, patch.dict(download.PACKAGES, {'molit':package}), patch.object(download,'download_file',side_effect=lambda _,target,opener:target.write_bytes(content)):
            target=Path(temporary)/'new'
            with self.assertRaises(ValueError): download.download_package('molit',target)
            self.assertFalse(target.exists())

    def test_downloaded_file_size_and_hash_are_checked(self):
        from email.message import Message
        import io
        headers=Message(); headers['Content-Type']='application/zip'
        class Response(io.BytesIO):
            pass
        response=Response(b'changed'); response.headers=headers
        class Opener:
            def open(self,*args,**kwargs): return response
        with tempfile.TemporaryDirectory() as temporary, self.assertRaises(ValueError):
            download.download_file({'id':'id','name':'archive.zip','bytes':7,'sha256':'0'*64},Path(temporary)/'file.zip',Opener())
