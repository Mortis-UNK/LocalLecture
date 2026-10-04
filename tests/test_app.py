import os
import unittest
from unittest.mock import patch

from app.gradio_app import configure_local_proxy_bypass


class ProxyTests(unittest.TestCase):
    def test_preserves_external_proxy_and_existing_exclusions(self):
        with patch.dict(os.environ, {"HTTPS_PROXY": "http://proxy.example:8080",
                                     "NO_PROXY": "example.org", "no_proxy": "example.org"}, clear=True):
            configure_local_proxy_bypass()
            configure_local_proxy_bypass()
            self.assertEqual(os.environ["HTTPS_PROXY"], "http://proxy.example:8080")
            self.assertEqual(set(os.environ["NO_PROXY"].split(",")),
                             {"example.org", "localhost", "127.0.0.1", "::1"})
            self.assertEqual(os.environ["NO_PROXY"], os.environ["no_proxy"])
