# Copyright 2015 redisapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os

from aclapiclient import aclapiclient, l4_options


class GloboACLAPIManager(object):

    def __init__(self):
        endpoint = os.environ.get("ACL_API_ENDPOINT")
        username = os.environ.get("ACL_API_USERNAME")
        password = os.environ.get("ACL_API_PASSWORD")
        self.client = aclapiclient.Client(username, password, endpoint)

    def grant_access(self, instance, unit_host):
        source = unit_host + "/32"
        for endpoint in instance.endpoints:
            desc = 'redis-api instance "{}" access from {}/32 to {}/32'.format(instance.name,
                                                                               unit_host,
                                                                               endpoint["host"])
            dest = endpoint["host"] + "/32"
            l4_opts = l4_options.L4Opts(operator="eq", port=endpoint["port"], target="dest")
            self.client.add_tcp_permit_access(desc=desc, source=source,
                                              dest=dest, l4_opts=l4_opts)
        self.client.commit()

    def revoke_access(self, instance, unit_host):
        source = unit_host + "/32"
        for endpoint in instance.endpoints:
            desc = 'redis-api instance "{}" access from {}/32 to {}/32'.format(instance.name,
                                                                               unit_host,
                                                                               endpoint["host"])
            dest = endpoint["host"] + "/32"
            l4_opts = l4_options.L4Opts(operator="eq", port=endpoint["port"], target="dest")
            self.client.remove_tcp_permit_access(desc=desc, source=source,
                                                 dest=dest, l4_opts=l4_opts)
        self.client.commit()


class DumbAccessManager(object):

    def grant_access(self, instance, unit_host):
        pass

    def revoke_access(self, instance, unit_host):
        pass

access_managers = {"globo-acl-api": GloboACLAPIManager,
                   "default": DumbAccessManager}