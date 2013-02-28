"""ResourceSync ResourceDump object

"""

from list_base import ListBase

class ResourceDump(ListBase):
    """Class representing a Resource Dump"""

    def __init__(self, resources=None, md=None, ln=None):
        if (resources is None):
            resources = list()
        super(ResourceDump, self).__init__(resources=resources, md=md, ln=ln)
        self.capability_name='resourcedump'
        self.capability_md='resourcedump'

