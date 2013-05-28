"""ResourceSync explorer"""

import sys
import urllib
import urlparse
import os.path
import datetime
import distutils.dir_util 
import re
import time
import logging
import requests

from resync.resource_list_builder import ResourceListBuilder
from resync.resource_list import ResourceList
from resync.change_list import ChangeList
from resync.capability_list import CapabilityList
from resync.capability_list_index import CapabilityListIndex
from resync.mapper import Mapper
from resync.sitemap import Sitemap
from resync.dump import Dump
from resync.resource import Resource
from resync.url_authority import UrlAuthority
from resync.utils import compute_md5_for_file
from resync.client import Client,ClientFatalError
from resync.client_state import ClientState
from w3c_datetime import str_to_datetime,datetime_to_str

class Explorer(Client):
    """Extension of the client code to explore a ResourceSync source
    """
    def explore(self):
        """Explore capabilities of a server interactvely
        
        Will use sitemap URI taken either from explicit self.sitemap_name
        or derived from the mappings supplied.
        """
        uri = None
        if (self.sitemap_name is not None):
            uri = self.sitemap
            print "Taking location from --sitemap option"
            acceptable_capabilities = None #ie. any
        elif (len(self.mapper)>0):
            pu = urlparse.urlparse(self.mapper.default_src_uri())
            uri = urlparse.urlunparse( [ pu[0], pu[1], '/.well-known/resourcesync', '', '', '' ] )
            print "Will look for discovery information based on mappings"
            acceptable_capabilities = [ 'capabilitylist', 'capabilitylistindex' ]
        else:
            raise ClientFatalError("Neither explicit sitemap nor mapping specified")
        history = []
        inp = None
        checks = None
        while (inp!='q'):
            print
            if (inp=='b'):
                if (len(history)<2):
                    break #can't do this, exit
                history.pop() #throw away current
                uri=history.pop()
                acceptable_capabilities=None
            history.append(uri)
            (uri,checks,acceptable_capabilities,inp) = self.explore_uri(uri,checks,acceptable_capabilities,len(history)>1)
        print "resync-explorer done, bye..."

    def explore_uri(self, uri, checks, caps, show_back=True):
        """Interactive exploration of document at uri

        Will flag warnings if the document is not of type listed in caps
        """
        s=Sitemap()
        print "Reading %s" % (uri)
        options={}
        capability=None
        try:
            if (caps=='resource'):
                self.explore_show_head(uri,check_headers=checks)
            else: 
                list = s.parse_xml(urllib.urlopen(uri))
                (options,capability)=self.explore_show_summary(list,s.parsed_index,caps)
        except IOError as e:
            print "Cannot read %s (%s)\nGoing back" % (uri,str(e))
            return('','','','b')
        except Exception as e:
            print "Cannot parse %s (%s)\nGoing back" % (uri,str(e))
            return('','','','b')
        while (True):
            # don't offer number option for no resources/capabilities
            num_prompt = '' if (len(options)==0) else 'number, '
            up_prompt = 'b(ack), ' if (show_back) else ''
            inp = raw_input( "Follow [%s%sq(uit)]?" % (num_prompt,up_prompt) )
            if (inp in options.keys()):
                break
            if (inp == 'q' or inp == 'b'):
                return('','','',inp)
        checks = {}
        if ( options[inp].capability is None ):
            if (capability == 'capabilitylistindex'):
                # all links should be to capabilitylist documents
                caps = ['capabilitylist']
            elif (capability in ['resourcelist','changelist',
                                 'resourcedump','changedump']):
                caps = 'resource'
        else:
            r = options[inp]
            caps = [r.capability]
            if (r.length is not None):
                checks['content-length']=r.length
            if (r.lastmod is not None):
                checks['last-modified']=r.lastmod
            # FIXME - could do sanity check here and issue warnings if odd
        return( options[inp].uri, checks, caps, inp )

    def explore_show_summary(self,list,parsed_index,caps):
        """Show summary of one capability document

        Used as part of --explore.
        FIXME - should look for <rs:ln rel="up"...> link and show that
        """
        num_entries = len(list.resources)
        capability = '(unknown capability)'
        if ('capability' in list.md):
            capability = list.md['capability']
        if (parsed_index):
            capability += 'index'
        print "Parsed %s document with %d entries:" % (capability,num_entries)
        if (caps is not None and capability not in caps):
            print "WARNING - expected a %s document" % (','.join(caps))
        to_show = num_entries
        if (num_entries>21):
            to_show = 20
        # What entries are allowed? 
        # FIXME - not complete
        entry_caps = []
        if (capability == 'capabilitylistindex'):
            entry_caps = ['capabilitylist']
        elif (capability == 'capabilitylist'):
            entry_caps = ['resourcelist','changelist','resourcedump','changedump','changelistindex']
        elif (capability == 'changelistindex'):
            entry_caps = ['changelist']
        options = {}
        n=0
        if ('up' in list.ln):
            options['up']=list.ln['up']
            print "[%s] %s" % ('up',list.ln['up'].uri)
        for r in list.resources:
            if (n>=to_show):
                print "(not showing remaining %d entries)" % (num_entries-n)
                break
            n+=1
            options[str(n)]=r
            print "[%d] %s" % (n,r.uri)
            if (r.capability is not None):
                warning = ''
                if (r.capability not in entry_caps):
                    warning = " (EXPECTED %s)" % (' or '.join(entry_caps))
                print "  %s%s" % (r.capability,warning)
            elif (len(entry_caps)==1):
                r.capability=entry_caps[0]
                print "  capability not specified, should be %s" % (r.capability)
        return(options,capability)

    def explore_show_head(self,uri,check_headers=None):
        """Do HEAD on uri and show infomation

        Will also check headers against any values specified in 
        check_headers.
        """
        print "HEAD %s" % (uri)
        response = requests.head(uri)
        print "  status: %s" % (response.status_code)
        # generate normalized lastmod
#        if ('last-modified' in response.headers):
#            response.headers.add['lastmod'] = datetime_to_str(str_to_datetime(response.headers['last-modified']))
        # print some of the headers
        for header in ['content-length','last-modified','lastmod','content-type','etag']:
            if header in response.headers:
                check_str=''
                if (check_headers is not None and
                    header in check_headers):
                    if (response.headers[header] == check_headers[header]):
                        check_str=' MATCHES EXPECTED VALUE'
                    else:
                        check_STR=' EXPECTED %s' % (check_headers[header])
                print "  %s: %s%s" % (header, response.headers[header], check_str)
