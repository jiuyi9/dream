#!/usr/bin/env python3
"""
云眸发布平台操作脚本 - 登录模块
凭据经 shared/scripts/credentials.py 从系统凭据管理器（keyring）读取，
调用登录接口获取 accessToken。

配置从同级目录 publish.json 读取。

用法：
  python scripts/publish/login.py

输出：JSON 格式，包含 accessToken 和用户信息
"""

import json
import os
import sys
import base64

import requests
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

# 配置文件路径
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_SCRIPT_DIR, "publish.json")

# shared/scripts 目录（.claude/shared/scripts），凭据模块所在
_SHARED_SCRIPTS_DIR = os.path.normpath(os.path.join(_SCRIPT_DIR, "..", "..", "..", "..", "shared", "scripts"))
sys.path.insert(0, _SHARED_SCRIPTS_DIR)
from credentials import get_valid_credentials, CredentialInputCancelled  # noqa: E402


def _load_config():
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_base_url():
    config = _load_config()["systemConfig"]
    return config["baseUrl"] + config["publishPath"]


def _get_origin():
    return _load_config()["systemConfig"]["baseUrl"]


def _build_headers():
    origin = _get_origin()
    return {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": origin,
        "Referer": origin + "/",
    }


def get_rsa_public_key():
    base_url = _get_base_url()
    headers = _build_headers()
    resp = requests.get(f"{base_url}/secret/publicKey", headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"get publicKey failed: {data.get('message', resp.text)}")
    return data["data"]["publicKey"]


def rsa_encrypt(plaintext, public_key_base64):
    pem_key = "-----BEGIN PUBLIC KEY-----\n" + public_key_base64 + "\n-----END PUBLIC KEY-----"
    key = RSA.import_key(pem_key)
    cipher = PKCS1_v1_5.new(key)
    ciphertext = cipher.encrypt(plaintext.encode("utf-8"))
    return base64.b64encode(ciphertext).decode("utf-8")


class _LoginError(Exception):
    """登录失败（凭据或服务端原因），供 verify 回调捕获后转为窗内提示。"""


def _do_login(username, password, public_key):
    """实际登录请求。成功返回 accessToken，失败抛 _LoginError（原始 message 只进异常，不对外显示）。"""
    base_url = _get_base_url()
    headers = _build_headers()
    encrypted_password = rsa_encrypt(password, public_key)
    payload = {"userName": username, "password": encrypted_password, "loginType": 1}
    resp = requests.post(f"{base_url}/login", json=payload, headers=headers, timeout=10)
    data = resp.json()
    if data.get("code") != 0:
        raise _LoginError(data.get("message", resp.text))
    access_token = data["data"]["accessToken"]
    if not access_token:
        raise _LoginError("no accessToken returned")
    return access_token


def login():
    """登录云眸获取 accessToken。

    凭据经 get_valid_credentials 统一获取：有已存凭据先验证（试登录），
    通过直接用；无凭据或已存失效则弹窗重输（窗内验证闭环，可一直改到对或取消）。
    token 经 verify 闭包带回，不重复登录。
    """
    public_key = get_rsa_public_key()
    token_holder = {}

    def verify(username, password):
        """登录验证回调：成功返回 None 并存 token 到闭包，失败返回固定错误信息。"""
        try:
            token_holder["token"] = _do_login(username, password, public_key)
            return None
        except _LoginError:
            return "账号或密码错误，请重新输入"

    get_valid_credentials(verify=verify)
    return token_holder["token"]


def main():
    try:
        token = login()
        print(json.dumps({"accessToken": token}, ensure_ascii=False))
    except CredentialInputCancelled:
        print(json.dumps({"error": "用户取消输入"}, ensure_ascii=False))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()