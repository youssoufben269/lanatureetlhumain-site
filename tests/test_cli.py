import os
import unittest
from unittest.mock import patch

from waitress.adjustments import Adjustments
from membership.__main__ import main
from membership.config import Settings


class ServeCommandTest(unittest.TestCase):
    def test_waitress_configuration_with_and_without_proxy(self):
        for proxy in ('', '127.0.0.1'):
            with self.subTest(proxy=proxy), \
                 patch.dict(os.environ, {'LNH_TRUSTED_PROXY': proxy}), \
                 patch('sys.argv', ['membership', 'serve']), \
                 patch('membership.__main__.Settings.from_env', return_value=Settings()), \
                 patch('membership.__main__.Service'), \
                 patch('membership.__main__.Application'), \
                 patch('waitress.serve') as serve:
                main()
                options = serve.call_args.kwargs
                adjustments = Adjustments(**options)
                self.assertEqual(adjustments.trusted_proxy, proxy or None)
                self.assertEqual(adjustments.clear_untrusted_proxy_headers, True)
