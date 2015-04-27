/* Copyright 2014, 2015 OpenMarket Ltd
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
CREATE TABLE IF NOT EXISTS users(
    name VARCHAR(150),
    password_hash VARCHAR(150),
    creation_ts BIGINT,
    admin SMALLINT DEFAULT 0 NOT NULL,
    UNIQUE(name)
);

CREATE TABLE IF NOT EXISTS access_tokens(
    id BIGINT PRIMARY KEY,
    user_id VARCHAR(150) NOT NULL,
    device_id VARCHAR(150),
    token VARCHAR(150) NOT NULL,
    last_used BIGINT,
    UNIQUE(token)
);

CREATE TABLE IF NOT EXISTS user_ips (
    user_id VARCHAR(150) NOT NULL,
    access_token VARCHAR(150) NOT NULL,
    device_id VARCHAR(150),
    ip VARCHAR(150) NOT NULL,
    user_agent TEXT NOT NULL,
    last_seen BIGINT NOT NULL
);

CREATE INDEX user_ips_user ON user_ips(user_id);
CREATE INDEX user_ips_user_ip ON user_ips(user_id, access_token, ip);