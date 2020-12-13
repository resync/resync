"""Extension of unittest.TestCase with fuzzy XML comparison via strings."""

import re
import unittest


class TestCase(unittest.TestCase):

    def _open_ex(self, ex):
        raise Exception("Must override _open_ex(..)!")

    def _assert_xml_equal_ex(self, xml, ex):
        """Compare XML supplied with XML from example file ex"""
        ex_xml = self._open_ex(ex).read()
        self._assert_xml_equal(xml, ex_xml)

    def _assert_xml_equal(self, a, b):
        context = "Element mismatch in\n%s\nvs\n%s\n" % (a, b)
        aa = self._xml_massage_split(a)
        bb = self._xml_massage_split(b)
        ia = iter(aa)
        ib = iter(bb)
        try:
            while (1):
                self._assert_xml_elements_equal(self._xml_reorder_attributes(next(ia)),
                                                self._xml_reorder_attributes(
                                                    next(ib)),
                                                context)
        except StopIteration:
            # all is good provided there were the same number of elements
            pass
        self.assertEqual(len(aa), len(bb), "Same length check\n%s" % (context))

    def _assert_xml_elements_equal(self, a, b, context):
        context = "Elements %s != %s\n%s" % (a, b, context)
        self.assertEqual(a, b, context)

    def _xml_reorder_attributes(self, xml):
        """Manipulate string for single element with atts in alpha order

        This is a bit of a fudge because of pattern matching. Should give
        correct match for all matches, but might give matches in rare cases
        that should not.
        """
        return(' '.join(sorted(xml.split(' '))))

    def _xml_massage_split(self, xml):
        """Massage XML for comparison and split by elements (on >)"""
        xml = re.sub(r'\s+$', '', xml)
        xml = re.sub(r'^\s+', '', xml)
        xml = re.sub(r'\s+', ' ', xml)
        # always one space before end of self-closing element
        xml = re.sub(r'\s*/>', ' />', xml)
        xml = re.sub(r'>\s+<', '><', xml)  # remove space between elements
        # FUDGES, need to check these are OK
        xml = re.sub(r"version='1.0'", 'version="1.0"', xml)
        xml = re.sub(r"encoding='UTF-8'", 'encoding="UTF-8"', xml)
        # return self.assertEqual( x, 'xx' )
        return(xml.split('>'))
