import io
from email.message import Message
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from budongi.http_helpers import discard_rejected_body


class RejectedBodyTests(unittest.TestCase):
    def handler(self, size, payload=b'fictional-body'):
        headers=Message()
        if size is not None: headers['Content-Length']=size
        connection=Mock(); connection.gettimeout.return_value=5
        return SimpleNamespace(headers=headers,rfile=io.BytesIO(payload),connection=connection)

    def test_discards_only_declared_bytes_and_restores_timeout(self):
        handler=self.handler('3')
        self.assertEqual(discard_rejected_body(handler,16),3)
        self.assertEqual(handler.rfile.read(),b'tional-body')
        self.assertEqual(handler.connection.settimeout.call_args.args,(5,))
        self.assertTrue(all(0<t.args[0]<=.2 for t in handler.connection.settimeout.call_args_list[:-1]))

    def test_ambiguous_and_oversize_framing_is_not_read(self):
        for value in (None,'bad','-1','+1','1,1','١','999999','0'):
            handler=self.handler(value)
            self.assertEqual(discard_rejected_body(handler,16),0)
            self.assertEqual(handler.rfile.tell(),0)
        for name in ('Content-Length','Transfer-Encoding'):
            handler=self.handler('3'); handler.headers[name]='3' if name=='Content-Length' else 'chunked'
            self.assertEqual(discard_rejected_body(handler,16),0)
            self.assertEqual(handler.rfile.tell(),0)

    def test_timeout_and_overall_deadline_are_bounded(self):
        handler=self.handler('8'); handler.rfile=Mock(); handler.rfile.read1.side_effect=TimeoutError
        self.assertEqual(discard_rejected_body(handler,16),0)
        self.assertEqual(handler.connection.settimeout.call_args.args,(5,))
        handler=self.handler('8')
        with patch('budongi.http_helpers.time.monotonic',side_effect=(1,1.21)):
            self.assertEqual(discard_rejected_body(handler,16),0)
        self.assertEqual(handler.rfile.tell(),0)
