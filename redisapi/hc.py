# Copyright 2015 redisapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os

from utils import get_value
from redisapi import mongodb_database


class FakeHealthCheck(object):
    added = False
    removed = False

    def add(self, host, port):
        self.added = True

    def remove(self, host, port):
        self.removed = True


class ZabbixHealthCheck(object):
    def __init__(self):
        url = get_value("ZABBIX_URL")
        user = get_value("ZABBIX_USER")
        password = get_value("ZABBIX_PASSWORD")
        self.host_id = get_value("ZABBIX_HOST")
        self.host_name = os.environ.get("ZABBIX_HOST_NAME", "Zabbix Server")
        self.interface_id = get_value("ZABBIX_INTERFACE")
        from pyzabbix import ZabbixAPI
        self.zapi = ZabbixAPI(url)
        self.zapi.login(user, password)

        self.items = self.mongo()['zabbix']

    def mongo(self):
        return mongodb_database()

    def add(self, host, port):
        item_key = "net.tcp.service[tcp,{},{}]".format(host, port)
        item_result = self.zapi.item.create(
            name="redis healthcheck for {}:{}".format(host, port),
            key_=item_key,
            delay=60,
            hostid=self.host_id,
            interfaceid=self.interface_id,
            type=3,
            value_type=3,
        )
        trigger_result = self.zapi.trigger.create(
            description="trigger hc for redis {}:{}".format(host, port),
            expression="{{{}:{}.last()}}=0".format(self.host_name, item_key),
            priority=5,
        )
        item = {
            'host': host,
            'port': port,
            'item': item_result['itemids'][0],
            'trigger': trigger_result['triggerids'][0],
        }
        self.items.insert(item)

    def remove(self, host, port):
        item = self.items.find_one({"host": host, "port": port})
        self.zapi.trigger.delete(item["trigger"])
        self.zapi.item.delete(item["item"])
        self.items.remove({"host": host, "port": port})


health_checkers = {
    'fake': FakeHealthCheck,
    'zabbix': ZabbixHealthCheck,
}
