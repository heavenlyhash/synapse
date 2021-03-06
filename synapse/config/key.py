# -*- coding: utf-8 -*-
# Copyright 2015 OpenMarket Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from ._base import Config, ConfigError
import syutil.crypto.signing_key
from syutil.crypto.signing_key import (
    is_signing_algorithm_supported, decode_verify_key_bytes
)
from syutil.base64util import decode_base64
from synapse.util.stringutils import random_string


class KeyConfig(Config):

    def read_config(self, config):
        self.signing_key = self.read_signing_key(config["signing_key_path"])
        self.old_signing_keys = self.read_old_signing_keys(
            config["old_signing_keys"]
        )
        self.key_refresh_interval = self.parse_duration(
            config["key_refresh_interval"]
        )
        self.perspectives = self.read_perspectives(
            config["perspectives"]
        )

    def default_config(self, config_dir_path, server_name):
        base_key_name = os.path.join(config_dir_path, server_name)
        return """\
        ## Signing Keys ##

        # Path to the signing key to sign messages with
        signing_key_path: "%(base_key_name)s.signing.key"

        # The keys that the server used to sign messages with but won't use
        # to sign new messages. E.g. it has lost its private key
        old_signing_keys: {}
        #  "ed25519:auto":
        #    # Base64 encoded public key
        #    key: "The public part of your old signing key."
        #    # Millisecond POSIX timestamp when the key expired.
        #    expired_ts: 123456789123

        # How long key response published by this server is valid for.
        # Used to set the valid_until_ts in /key/v2 APIs.
        # Determines how quickly servers will query to check which keys
        # are still valid.
        key_refresh_interval: "1d" # 1 Day.

        # The trusted servers to download signing keys from.
        perspectives:
          servers:
            "matrix.org":
              verify_keys:
                "ed25519:auto":
                  key: "Noi6WqcDj0QmPxCNQqgezwTlBKrfqehY1u2FyWP9uYw"
        """ % locals()

    def read_perspectives(self, perspectives_config):
        servers = {}
        for server_name, server_config in perspectives_config["servers"].items():
            for key_id, key_data in server_config["verify_keys"].items():
                if is_signing_algorithm_supported(key_id):
                    key_base64 = key_data["key"]
                    key_bytes = decode_base64(key_base64)
                    verify_key = decode_verify_key_bytes(key_id, key_bytes)
                    servers.setdefault(server_name, {})[key_id] = verify_key
        return servers

    def read_signing_key(self, signing_key_path):
        signing_keys = self.read_file(signing_key_path, "signing_key")
        try:
            return syutil.crypto.signing_key.read_signing_keys(
                signing_keys.splitlines(True)
            )
        except Exception:
            raise ConfigError(
                "Error reading signing_key."
                " Try running again with --generate-config"
            )

    def read_old_signing_keys(self, old_signing_keys):
        keys = {}
        for key_id, key_data in old_signing_keys.items():
            if is_signing_algorithm_supported(key_id):
                key_base64 = key_data["key"]
                key_bytes = decode_base64(key_base64)
                verify_key = decode_verify_key_bytes(key_id, key_bytes)
                verify_key.expired_ts = key_data["expired_ts"]
                keys[key_id] = verify_key
            else:
                raise ConfigError(
                    "Unsupported signing algorithm for old key: %r" % (key_id,)
                )
        return keys

    def generate_files(self, config):
        signing_key_path = config["signing_key_path"]
        if not os.path.exists(signing_key_path):
            with open(signing_key_path, "w") as signing_key_file:
                key_id = "a_" + random_string(4)
                syutil.crypto.signing_key.write_signing_keys(
                    signing_key_file,
                    (syutil.crypto.signing_key.generate_signing_key(key_id),),
                )
        else:
            signing_keys = self.read_file(signing_key_path, "signing_key")
            if len(signing_keys.split("\n")[0].split()) == 1:
                # handle keys in the old format.
                key_id = "a_" + random_string(4)
                key = syutil.crypto.signing_key.decode_signing_key_base64(
                    syutil.crypto.signing_key.NACL_ED25519,
                    key_id,
                    signing_keys.split("\n")[0]
                )
                with open(signing_key_path, "w") as signing_key_file:
                    syutil.crypto.signing_key.write_signing_keys(
                        signing_key_file,
                        (key,),
                    )
