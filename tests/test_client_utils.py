from .testlib import TestCase

import argparse
import logging
import os.path
import re
import unittest
from resync.client_utils import init_logging, count_true_args, parse_links, parse_link, parse_capabilities, parse_capability_lists, add_shared_misc_options, process_shared_misc_options
from resync.client import ClientFatalError
from resync.url_or_file_open import CONFIG


class TestClientUtils(TestCase):

    def test01_init_logging(self):
        # to_file=False, logfile=None, default_logfile='/tmp/resync.log',
        #         human=True, verbose=False, eval_mode=False,
        #         default_logger='client', extra_loggers=None):
        tmplog = os.path.join(self.tmpdir, 'tmp.log')
        init_logging(to_file=True, default_logfile=tmplog,
                     extra_loggers=['x1', 'x2'])
        # check x1 and x2 set, not x3 (can tell by level)
        self.assertTrue(logging.getLogger('x1').level, logging.DEBUG)
        self.assertTrue(logging.getLogger('x2').level, logging.DEBUG)
        self.assertEqual(logging.getLogger('x3').level, 0)
        # write something, check goes to file
        log = logging.getLogger('resync')
        log.warning('PIGS MIGHT FLY')
        logtxt = open(tmplog, 'r').read()
        self.assertTrue(re.search(r'WARNING \| PIGS MIGHT FLY', logtxt))

    def test02_count_true_args(self):
        self.assertEqual(count_true_args(), 0)
        self.assertEqual(count_true_args(True), 1)
        self.assertEqual(count_true_args(False), 0)
        self.assertEqual(count_true_args(0, 1, 2, 3), 3)

    def test03_parse_links(self):
        self.assertEqual(parse_links([]), [])
        self.assertEqual(parse_links(['u,h']), [{'href': 'h', 'rel': 'u'}])
        self.assertEqual(parse_links(['u,h', 'v,i']), [
                         {'href': 'h', 'rel': 'u'}, {'href': 'i', 'rel': 'v'}])
        self.assertRaises(ClientFatalError, parse_links, 'xx')
        self.assertRaises(ClientFatalError, parse_links, ['u'])
        self.assertRaises(ClientFatalError, parse_links, ['u,h', 'u'])

    def test04_parse_link(self):
        # Input string of the form: rel,href,att1=val1,att2=val2
        self.assertEqual(parse_link('u,h'), {'href': 'h', 'rel': 'u'})
        self.assertEqual(parse_link('u,h,a=b'), {
                         'a': 'b', 'href': 'h', 'rel': 'u'})
        self.assertEqual(parse_link('u,h,a=b,c=d'), {
                         'a': 'b', 'c': 'd', 'href': 'h', 'rel': 'u'})
        self.assertEqual(parse_link('u,h,a=b,a=d'), {
                         'a': 'd', 'href': 'h', 'rel': 'u'})  # desired??
        self.assertRaises(ClientFatalError, parse_link, '')
        self.assertRaises(ClientFatalError, parse_link, 'u')
        self.assertRaises(ClientFatalError, parse_link, 'u,')
        self.assertRaises(ClientFatalError, parse_link, 'u,h,,')
        self.assertRaises(ClientFatalError, parse_link, 'u,h,a')
        self.assertRaises(ClientFatalError, parse_link, 'u,h,a=')
        self.assertRaises(ClientFatalError, parse_link, 'u,h,a=b,=c')

    def test05_parse_capabilities(self):
        # Input string of the form: cap_name=uri,cap_name=uri
        # good
        c = parse_capabilities('a=')
        self.assertEqual(len(c), 1)
        self.assertEqual(c['a'], '')
        c = parse_capabilities('a=b,c=')
        self.assertEqual(len(c), 2)
        self.assertEqual(c['a'], 'b')
        # bad
        self.assertRaises(ClientFatalError, parse_capabilities, 'a')
        self.assertRaises(ClientFatalError, parse_capabilities, 'a=b,')

    def test06_parse_capability_lists(self):
        # Input string of the form: uri,uri
        self.assertEqual(parse_capability_lists('a,b'), ['a', 'b'])

    def test07_add_shared_misc_options(self):
        """Test add_shared_misc_options method."""
        parser = argparse.ArgumentParser()
        add_shared_misc_options(parser, default_logfile='/tmp/abc.log')
        args = parser.parse_args(['--hash', 'md5', '--hash', 'sha-1',
                                  '--checksum',
                                  '--from', '2020-01-01T01:01:01Z',
                                  '--exclude', 'ex1', '--exclude', 'ex2',
                                  '--multifile',
                                  '--logger', '--logfile', 'log.out',
                                  '--spec-version', '1.0',
                                  '-v'])
        self.assertEqual(args.hash, ['md5', 'sha-1'])
        self.assertTrue(args.checksum)
        self.assertEqual(args.from_datetime, '2020-01-01T01:01:01Z')
        self.assertEqual(args.exclude, ['ex1', 'ex2'])
        self.assertTrue(args.multifile)
        self.assertTrue(args.logger)
        self.assertEqual(args.logfile, 'log.out')
        self.assertEqual(args.spec_version, '1.0')
        self.assertTrue(args.verbose)
        # Remote options
        parser = argparse.ArgumentParser()
        add_shared_misc_options(parser, default_logfile='/tmp/abc.log', include_remote=True)
        args = parser.parse_args(['--noauth',
                                  '--access-token', 'VerySecretToken',
                                  '--delay', '1.23',
                                  '--user-agent', 'rc/2.1.1'])
        self.assertTrue(args.noauth)
        self.assertEqual(args.access_token, 'VerySecretToken')
        self.assertEqual(args.delay, 1.23)
        self.assertEqual(args.user_agent, 'rc/2.1.1')
        # Remote options note selected
        parser = argparse.ArgumentParser()
        add_shared_misc_options(parser, default_logfile='/tmp/abc.log', include_remote=False)
        self.assertRaises(SystemExit, parser.parse_args, ['--access-token', 'VerySecretToken'])

    def test08_process_shared_misc_options(self):
        """Test process_shared_misc_options method."""
        global CONFIG
        config_copy = CONFIG.copy()
        args = argparse.Namespace(hash=['sha-1'], checksum='md5')
        process_shared_misc_options(args)
        self.assertEqual(args.hash, ['sha-1', 'md5'])
        # Remote options
        args = argparse.Namespace(access_token='ExtraSecretToken',
                                  delay=2.5,
                                  user_agent='me',
                                  checksum=None)
        process_shared_misc_options(args, include_remote=True)
        self.assertEqual(CONFIG['bearer_token'], 'ExtraSecretToken')
        self.assertEqual(CONFIG['delay'], 2.5)
        self.assertEqual(CONFIG['user_agent'], 'me')
        # Negative delay is bad...
        args = argparse.Namespace(access_token=None, delay=-1.0, user_agent=None, checksum=None)
        self.assertRaises(argparse.ArgumentTypeError, process_shared_misc_options, args, include_remote=True)
        # Config is a global so reset back to old version
        for (k, v) in config_copy.items():
            CONFIG[k] = v
