#!/usr/bin/env python3
"""
云眸发布平台操作脚本 - 发布模块

支持的操作：
  resolve  - 解析发布参数（含默认版本）
  versions - 查看单个组件的版本列表
  publish  - 发布单个组件

用法：
  python scripts/publish/publish.py resolve --components <componentNames> --image-tag <imageTag> [--env <env>]
  python scripts/publish/publish.py versions <component>
  python scripts/publish/publish.py publish --component-id <componentId> --version-id <versionId> --image-name <imageName> --image-tag <imageTag> [--env <env>]
"""

import json
import os
import sys
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

# 配置文件路径
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_SCRIPT_DIR, "publish.json")

# 最大并发数
_MAX_WORKERS = 5


def _load_config():
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_config():
    return _load_config()["systemConfig"]


def _get_base_url():
    """返回 API 基地址：baseUrl + publishPath"""
    config = _get_config()
    return config["baseUrl"] + config["publishPath"]


def _get_runtime_url(env):
    """返回运行情况查看地址：baseUrl + envRuntimePath（替换 {env} 占位符）"""
    config = _get_config()
    return config["baseUrl"] + config["envRuntimePath"].format(env=env)


def _get_default_env():
    return _get_config()["defaultEnv"]


def _get_allowed_envs():
    return _get_config()["allowedEnvs"]


def _get_timeout():
    return _get_config()["requestTimeoutSeconds"]


def _build_headers():
    base_url = _get_config()["baseUrl"]
    return {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": base_url,
        "Referer": base_url + "/",
    }


def get_token():
    """获取 accessToken（直接调用 login 模块）"""
    from login import login
    return login()


def api_get(path, token, params=None):
    headers = {**_build_headers(), "Authorization": f"Bearer {token}"}
    resp = requests.get(f"{_get_base_url()}{path}", headers=headers, params=params, timeout=_get_timeout())
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(data.get("message", "unknown error"))
    return data["data"]


def api_post(path, token, payload):
    headers = {**_build_headers(), "Authorization": f"Bearer {token}"}
    resp = requests.post(f"{_get_base_url()}{path}", json=payload, headers=headers, timeout=_get_timeout())
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(data.get("message", "unknown error"))
    return data["data"]


# ---------------------------------------------------------------------------
# 核心业务函数
# ---------------------------------------------------------------------------

def search_components(token, keyword):
    """搜索组件，返回匹配的组件列表（不含版本信息）"""
    data = api_get("/components", token)
    rows = data.get("rows", [])
    if not keyword:
        return rows
    kw = keyword.lower()
    return [r for r in rows if kw in r.get("name", "").lower() or kw in r.get("code", "").lower()]


def get_default_version(token, componentId):
    """获取组件默认版本（lastStatusTime 倒序第一个）"""
    data = api_get(f"/components/{componentId}/versions", token)
    rows = data.get("rows", [])
    if not rows:
        raise RuntimeError(f"component {componentId} has no versions")
    sorted_rows = sorted(rows, key=lambda v: v.get("lastStatusTime", ""), reverse=True)
    return sorted_rows[0]


def get_version_list(token, componentId):
    """获取组件完整版本列表（lastStatusTime 倒序）"""
    data = api_get(f"/components/{componentId}/versions", token)
    rows = data.get("rows", [])
    return sorted(rows, key=lambda v: v.get("lastStatusTime", ""), reverse=True)


def get_environment_id(token, env):
    """根据环境名称获取环境 ID"""
    data = api_get("/environments", token)
    for e in data.get("rows", []):
        if e["name"] == env:
            return e["id"]
    raise RuntimeError(f"environment '{env}' not found")


def resolve_component(token, comp):
    """为单个组件获取默认版本，返回 resolve 所需字段"""
    default_ver = get_default_version(token, comp["id"])
    imageName = comp["imageNames"][0] if comp.get("imageNames") else comp["code"]
    return {
        "name": comp["name"],
        "componentId": comp["id"],
        "imageName": imageName,
        "version": default_ver["name"],
        "versionId": default_ver["id"],
    }


# ---------------------------------------------------------------------------
# 命令处理
# ---------------------------------------------------------------------------

def cmd_resolve(args):
    token = get_token()

    # 解析组件：逗号分隔
    comp_names = [c.strip() for c in args.components.split(",") if c.strip()]
    if not comp_names:
        print(json.dumps({"error": "no components specified"}, ensure_ascii=False))
        sys.exit(1)

    # 逐个搜索组件
    components = []
    for name in comp_names:
        matched = search_components(token, name)
        exact = [c for c in matched if c["name"] == name or c["code"] == name]
        if not exact:
            print(json.dumps({"error": f"component '{name}' not found"}, ensure_ascii=False))
            sys.exit(1)
        components.append(exact[0])

    # 验证环境
    env = args.env or _get_default_env()
    allowed = _get_allowed_envs()
    if env not in allowed:
        print(json.dumps({"error": f"unsupported env: {env} (allowed: {', '.join(allowed)})"}, ensure_ascii=False))
        sys.exit(1)

    # 并发获取默认版本和 envId
    envId = get_environment_id(token, env)

    results = []
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
        future_map = {executor.submit(resolve_component, token, c): c for c in components}
        for future in as_completed(future_map):
            try:
                results.append(future.result())
            except RuntimeError as e:
                comp = future_map[future]
                print(json.dumps({"error": f"resolve component '{comp['name']}' failed: {e}"}, ensure_ascii=False))
                sys.exit(1)

    # 保持输入顺序
    result_by_name = {r["name"]: r for r in results}
    ordered = [result_by_name[c["name"]] for c in components if c["name"] in result_by_name]

    print(json.dumps({
        "imageTag": args.image_tag,
        "env": env,
        "envId": envId,
        "envRuntimeUrl": _get_runtime_url(env),
        "components": ordered,
    }, ensure_ascii=False, indent=2))


def cmd_versions(args):
    token = get_token()

    # 查找组件
    components = search_components(token, args.component)
    matched = [c for c in components if c["name"] == args.component or c["code"] == args.component]
    if not matched:
        print(json.dumps({"error": f"component '{args.component}' not found"}, ensure_ascii=False))
        sys.exit(1)

    comp = matched[0]
    versions = get_version_list(token, comp["id"])

    print(json.dumps({
        "component": comp["name"],
        "versions": [
            {"name": v["name"], "versionId": v["id"]}
            for v in versions
        ],
    }, ensure_ascii=False, indent=2))


def cmd_publish(args):
    env = args.env or _get_default_env()

    # 环境校验
    allowed = _get_allowed_envs()
    if env not in allowed:
        print(json.dumps({"success": False}, ensure_ascii=False))
        sys.exit(1)

    try:
        token = get_token()
        envId = get_environment_id(token, env)
        dockerImage = f"{args.image_name}:{args.image_tag}"

        payload = {
            "componentId": args.component_id,
            "dockerImages": [dockerImage],
            "envId": envId,
            "isFileSave": False,
            "fileName": "",
            "versionId": args.version_id,
            "environmentCheck": False,
        }

        api_post("/publishes", token, payload)
        print(json.dumps({"success": True}, ensure_ascii=False))
    except Exception:
        print(json.dumps({"success": False}, ensure_ascii=False))
        sys.exit(1)


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="云眸发布平台 - 发布操作")
    subparsers = parser.add_subparsers(dest="command", help="操作类型")

    # resolve
    p_resolve = subparsers.add_parser("resolve", help="解析发布参数")
    p_resolve.add_argument("--components", "-c", required=True, help="组件名称，多个用逗号分隔")
    p_resolve.add_argument("--image-tag", "-t", required=True, help="镜像标签")
    p_resolve.add_argument("--env", "-e", help="发布环境")

    # versions
    p_versions = subparsers.add_parser("versions", help="查看单个组件的版本列表")
    p_versions.add_argument("component", help="组件名称")

    # publish
    p_pub = subparsers.add_parser("publish", help="发布单个组件")
    p_pub.add_argument("--component-id", required=True, help="组件 ID")
    p_pub.add_argument("--version-id", required=True, help="版本 ID")
    p_pub.add_argument("--image-name", required=True, help="镜像名")
    p_pub.add_argument("--image-tag", "-t", required=True, help="镜像标签")
    p_pub.add_argument("--env", "-e", help="发布环境")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "resolve":
            cmd_resolve(args)
        elif args.command == "versions":
            cmd_versions(args)
        elif args.command == "publish":
            cmd_publish(args)
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()