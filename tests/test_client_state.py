from .testlib import TestCase

import os.path
from resync.client_state import ClientState


class TestClientState(TestCase):

    def test01_set_and_get(self):
        cs = ClientState()
        self.assertEqual(cs.status_file, '.resync-client-status.cfg')
        cs.status_file = os.path.join(self.tmpdir, cs.status_file)
        # Get state
        site = 'https://this.site/'
        self.assertEqual(cs.get_state(site), None)
        cs.set_state(site, 123)
        self.assertEqual(cs.get_state(site), 123)
        cs.set_state(site, 456)
        self.assertEqual(cs.get_state(site), 456)
        cs.set_state(site)
        self.assertEqual(cs.get_state(site), None)
