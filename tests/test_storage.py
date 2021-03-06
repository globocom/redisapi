# Copyright 2015 redisapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest
import mock
import os

from redisapi.storage import Instance


class InstanceTest(unittest.TestCase):

    def test_instance(self):
        host = "host"
        id = "id"
        name = "name"
        port = "port"
        plan = "plan"
        endpoints = [{"port": port, "host": host, "container_id": id}]
        instance = Instance(
            name=name,
            plan=plan,
            endpoints=endpoints,
        )
        self.assertEqual(instance.name, name)
        self.assertEqual(instance.plan, plan)
        self.assertListEqual(instance.endpoints, endpoints)

    def test_to_json(self):
        host = "host"
        id = "id"
        name = "name"
        port = "port"
        plan = "plan"
        endpoints = [{"port": port, "host": host, "container_id": id}]
        instance = Instance(
            name=name,
            plan=plan,
            endpoints=endpoints,
        )
        expected = {
            'name': name,
            'plan': plan,
            'endpoints': endpoints,
        }
        self.assertDictEqual(instance.to_json(), expected)


class MongoStorageTest(unittest.TestCase):

    def remove_env(self, env):
        if env in os.environ:
            del os.environ[env]

    @mock.patch("pymongo.MongoClient")
    def test_mongodb_uri_environ(self, mongo_mock):
        from redisapi.storage import MongoStorage
        storage = MongoStorage()
        storage.db()
        mongo_mock.assert_called_with("mongodb://localhost:27017/")

        os.environ["MONGODB_URI"] = "0.0.0.0"
        self.addCleanup(self.remove_env, "MONGODB_URI")
        storage = MongoStorage()
        storage.db()
        mongo_mock.assert_called_with("0.0.0.0")

    @mock.patch("pymongo.MongoClient")
    def test_mongodb_dbaas_uri_environ(self, mongo_mock):
        from redisapi.storage import MongoStorage
        os.environ["DBAAS_MONGODB_ENDPOINT"] = "0.0.0.1"
        self.addCleanup(self.remove_env, "DBAAS_MONGODB_ENDPOINT")
        storage = MongoStorage()
        storage.db()
        mongo_mock.assert_called_with("0.0.0.1")

    @mock.patch("pymongo.MongoClient")
    def test_mongodb_dbaas_database_name_environ(self, mongo_mock):
        from redisapi.storage import MongoStorage
        os.environ["DBAAS_MONGODB_ENDPOINT"] = "0.0.0.1"
        os.environ["DATABASE_NAME"] = "xxxx"
        self.addCleanup(self.remove_env, "DBAAS_MONGODB_ENDPOINT")

        def error():
            from pymongo.errors import ConfigurationError
            raise ConfigurationError()
        mongo_mock.return_value.get_default_database.side_effect = error
        storage = MongoStorage()
        storage.db()
        mongo_mock.assert_called_with("0.0.0.1")
        mongo_mock.return_value.__getitem__.assert_called_with("xxxx")

    @mock.patch("pymongo.MongoClient")
    def test_mongodb_dbaas_database_name_from_url(self, mongo_mock):
        from redisapi.storage import MongoStorage
        os.environ["DBAAS_MONGODB_ENDPOINT"] = "0.0.0.1"
        self.addCleanup(self.remove_env, "DBAAS_MONGODB_ENDPOINT")
        storage = MongoStorage()
        storage.db()
        mongo_mock.assert_called_with("0.0.0.1")
        mongo_mock.return_value.get_default_database.assert_called_with()

    def test_add_instance(self):
        from redisapi.storage import MongoStorage
        storage = MongoStorage()
        instance = Instance(
            "xname", "plan", [{"host": "host", "port": "port",
                               "container_id": "id"}])
        storage.add_instance(instance)
        result = storage.find_instance_by_name(instance.name)
        self.assertEqual(instance.endpoints[0]["container_id"],
                         result.endpoints[0]["container_id"])
        storage.remove_instance(instance)

    def test_find_instance_by_name(self):
        from redisapi.storage import MongoStorage
        storage = MongoStorage()
        instance = Instance(
            "xname", "plan", [{"host": "host", "container_id": "id",
                               "port": "port"}])
        storage.add_instance(instance)
        result = storage.find_instance_by_name(instance.name)
        self.assertEqual(instance.endpoints[0]["container_id"],
                         result.endpoints[0]["container_id"])
        storage.remove_instance(instance)

    def test_find_instances_by_host(self):
        from redisapi.storage import MongoStorage
        storage = MongoStorage()
        instance = Instance(
            "xname", "plan", [{"host": "host", "container_id": "id",
                               "port": "port"}])
        storage.add_instance(instance)
        result = storage.find_instances_by_host("host")
        self.assertEqual(instance.endpoints[0]["container_id"],
                         result[0].endpoints[0]["container_id"])
        storage.remove_instance(instance)

    def test_remove_instance(self):
        from redisapi.storage import MongoStorage
        storage = MongoStorage()
        instance = Instance(
            "xname", "plan",
            [{"host": "host", "container_id": "id", "port": "port"}])
        storage.add_instance(instance)
        result = storage.find_instance_by_name(instance.name)
        endpoint = instance.endpoints[0]
        self.assertEqual(endpoint["container_id"],
                         result.endpoints[0]["container_id"])
        storage.remove_instance(instance)
        length = storage.db()['instances'].find(
            {"name": instance.name}).count()
        self.assertEqual(length, 0)
