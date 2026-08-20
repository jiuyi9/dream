"""
Jenkins 构建工具 — resolve / build / result

resolve: 将用户意图（slug + 可选参数）解析为确定的构建参数，输出 JSON
build:   提交构建任务 + 轮询队列获取 buildNumber，立即返回控制台地址
result:  轮询构建状态直到结束，输出最终结果 JSON

使用方式：
    python jenkins_build.py resolve [<slug>] [--branch <b>] [--components <c>] [--jdk <v>]
    python jenkins_build.py build --job <job> --components <c> --branch <b> --jdk <v>
    python jenkins_build.py result --job <job> --build-number <n>

输出契约（所有命令统一）：
    成功 → stdout 输出数据 JSON，退出码 0
    失败 → stderr 输出 {"error": "<TypeName>", "message": "..."}，退出码 1
"""

import argparse
import json
import os
import sys
import time
import base64
import logging
import urllib.parse
import subprocess
from html.parser import HTMLParser
from typing import Dict, Optional, List, Any, Tuple

import requests
import urllib3

# 凭据模块位于 shared/scripts（.claude/shared/scripts），按相对路径引入
_SHARED_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "shared", "scripts")
)
if _SHARED_DIR not in sys.path:
    sys.path.insert(0, _SHARED_DIR)
import credentials as creds  # noqa: E402

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


# ============================================================
# 异常
# ============================================================

class JenkinsError(Exception):
    """构建相关异常基类"""
    pass


class ConfigLoadError(JenkinsError):
    """配置文件加载失败"""
    pass


class JobNotFoundError(JenkinsError):
    """任务未找到（slug 在 Jenkins 上零命中或多命中）"""
    pass


class JenkinsAuthError(JenkinsError):
    """认证失败（401）"""
    pass


class JenkinsNotFoundError(JenkinsError):
    """资源不存在（404）：任务/队列项/构建。语义随上下文，由调用方接"""
    def __init__(self, resource: str = ""):
        self.resource = resource
        super().__init__(f"资源不存在：{resource}" if resource else "资源不存在")


class JenkinsFatalError(JenkinsError):
    """致命错误：连接失败/请求超时/其他 HTTP 错误（403/500 等）"""
    def __init__(self, status_code: int, body: str = ""):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {body}"[:200] if body else f"HTTP {status_code}")


class JenkinsConnectionError(JenkinsFatalError):
    """连接失败：host 错误或网络不通"""
    def __init__(self, detail: str = ""):
        super().__init__(0, f"连接失败：{detail}" if detail else "连接失败")


class JenkinsTimeoutError(JenkinsFatalError):
    """请求超时"""
    def __init__(self, detail: str = ""):
        super().__init__(0, f"请求超时：{detail}" if detail else "请求超时")


# ============================================================
# JenkinsClient
# ============================================================

class JenkinsClient:
    """Jenkins REST API 客户端，使用用户名+密码 Basic Auth 认证"""

    def __init__(self, url: str, username: str, password: str):
        self.jenkins_url = url.rstrip("/")
        self.username = username
        self.password = password

        auth_string = f"{username}:{password}".encode("utf-8")
        self.auth_header = f"Basic {base64.b64encode(auth_string).decode('utf-8')}"

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": self.auth_header,
            "User-Agent": "JenkinsClient/1.0",
            "Accept": "application/json",
        })
        self.session.verify = False

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        return_response: bool = False,
    ) -> Any:
        """发送 HTTP 请求。唯一的 HTTP 错误判定点。

        成功返回 response 数据（json dict 或 text str）；return_response=True 时
        返回原始 response 对象（含 headers/status，供解析 Location 头或 HTML body）。
        失败按状态码/异常类型抛对应异常。
        """
        url = f"{self.jenkins_url}{endpoint}"
        try:
            response = self.session.request(
                method=method, url=url, headers=self._headers(),
                params=params, timeout=30,
            )
        except requests.exceptions.ConnectionError as e:
            raise JenkinsConnectionError(str(e)) from e
        except requests.exceptions.Timeout as e:
            raise JenkinsTimeoutError(str(e)) from e
        except Exception as e:
            raise JenkinsFatalError(0, f"请求异常：{e}") from e

        status = response.status_code
        if status == 401:
            raise JenkinsAuthError("账号或密码错误")
        if status == 404:
            raise JenkinsNotFoundError(endpoint)
        if status not in (200, 201):
            raise JenkinsFatalError(status, response.text[:200])

        if return_response:
            return response
        if status == 200:
            try:
                return response.json()
            except json.JSONDecodeError:
                return response.text
        return None

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.auth_header,
            "Content-Type": "application/json",
            "User-Agent": "JenkinsClient/1.0",
        }

    def _encode_job(self, job_name: str) -> str:
        return urllib.parse.quote(job_name, safe="")

    # ---- 任务 ----

    def get_jobs(self) -> Dict[str, Any]:
        tree = "jobs[name,url,color,builds[number,result,timestamp,duration]]"
        return self._request("GET", f"/api/json?tree={tree}")

    def get_job_details(self, job_name: str) -> Dict[str, Any]:
        try:
            return self._request("GET", f"/job/{self._encode_job(job_name)}/api/json")
        except JenkinsNotFoundError:
            raise JenkinsNotFoundError(f"任务不存在：{job_name}")

    # ---- 组件列表 ----

    def fetch_component_sections(self, job_name: str) -> List[str]:
        """从 Jenkins 构建页面 HTML 解析 component_sections 可选值。

        Extended Choice Parameter 插件不通过 JSON API 暴露 choices，
        直接请求 /build?delay=0sec 从 HTML 中解析。支持两种表单形式：
        - <select name="component_sections"> 下的 <option>（下拉多选）
        - <input name="component_sections.value" type="checkbox">（复选框）
        """
        endpoint = f"/job/{self._encode_job(job_name)}/build?delay=0sec"
        url = f"{self.jenkins_url}{endpoint}"
        response = self.session.get(url, headers=self._headers(), timeout=30, verify=False)
        html_text = response.text

        parser = _ComponentSelectParser()
        parser.feed(html_text)
        return parser.components

    # ---- 构建触发 ----

    def trigger_build(self, job_name: str, params: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """触发构建，从响应头 Location 解析队列 ID。

        成功返回 queue_id；404 抛 JenkinsNotFoundError；401/连接/超时/其他由 _request 抛。

        Jenkins Extended Choice Parameter（PT_CHECKBOX）要求多个选中值以同名参数
        重复出现的方式传递（a=1&a=2），而非逗号拼接。此处将逗号分隔的字符串值展开为列表。
        """
        if params:
            params = {
                k: ([x.strip() for x in v.split(",") if x.strip()] if isinstance(v, str) and "," in v else v)
                for k, v in params.items()
            }
        encoded = self._encode_job(job_name)
        endpoint = f"/job/{encoded}/buildWithParameters" if params else f"/job/{encoded}/build"
        response = self._request("POST", endpoint, params=params, return_response=True)
        location = response.headers.get("Location", "")
        if not location:
            return None
        parts = location.rstrip("/").split("/")
        for i, part in enumerate(parts):
            if part == "item" and i + 1 < len(parts):
                try:
                    return int(parts[i + 1])
                except ValueError:
                    pass
        return None

    # ---- 队列与构建查询 ----

    def get_queue_item(self, queue_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/queue/item/{queue_id}/api/json")

    def get_build_info(self, job_name: str, build_number: int) -> Dict[str, Any]:
        return self._request("GET", f"/job/{self._encode_job(job_name)}/{build_number}/api/json")

    def get_console_output(self, job_name: str, build_number: int) -> Dict[str, Any]:
        encoded = self._encode_job(job_name)
        text = self._request("GET", f"/job/{encoded}/{build_number}/consoleText")
        return {"text": text, **self._parse_console_result(text)}

    def _parse_console_result(self, console_output: str) -> Dict[str, Any]:
        image_tag = ""
        success_components: List[str] = []
        failed_components: List[str] = []
        if not console_output:
            return {"imageTag": "", "successComponents": "", "failedComponents": ""}
        for line in console_output.splitlines():
            if line.startswith("#### "):
                content = line[5:]
                if ":" in content:
                    key, _, value = content.partition(":")
                    key = key.strip()
                    value = value.strip()
                    if key == "镜像标签":
                        image_tag = value
                    elif key == "构建成功":
                        success_components = [c.strip() for c in value.split()] if value else []
                    elif key == "构建失败":
                        failed_components = [c.strip() for c in value.split()] if value else []
        return {
            "imageTag": image_tag,
            "successComponents": ",".join(success_components),
            "failedComponents": ",".join(failed_components),
        }

    def console_url(self, job_name: str, build_number: int) -> str:
        return f"{self.jenkins_url}/job/{job_name}/{build_number}/console"


# ============================================================
# Component HTML 解析
# ============================================================

class _ComponentSelectParser(HTMLParser):
    """解析 HTML 中 component_sections 的可选值。

    支持两种表单形式：
    - <select name="component_sections"> 下的 <option> 值
    - <input name="component_sections.value" type="checkbox"> 的 value 属性
    """

    def __init__(self):
        super().__init__()
        self.components: List[str] = []
        self._in_select = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "select" and attrs_dict.get("name") == "component_sections":
            self._in_select = True
        elif tag == "option" and self._in_select:
            value = attrs_dict.get("value", "")
            if value:
                self.components.append(value)
        elif tag == "input" and attrs_dict.get("name") == "component_sections.value":
            value = attrs_dict.get("value", "")
            if value:
                self.components.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag == "select" and self._in_select:
            self._in_select = False


# ============================================================
# 配置
# ============================================================

def _get_script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """加载 jenkins.json 配置文件"""
    if config_path is None:
        config_path = os.path.join(_get_script_dir(), "jenkins.json")

    if not os.path.exists(config_path):
        raise ConfigLoadError(f"配置文件不存在: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigLoadError(f"配置文件 JSON 格式错误: {e}")

    sc = config.get("systemConfig", {})
    if not sc.get("url"):
        raise ConfigLoadError("配置文件中缺少 systemConfig.url")
    if not sc.get("jobPrefix"):
        raise ConfigLoadError("配置文件中缺少 systemConfig.jobPrefix")

    return config


def _save_config(config: Dict[str, Any]) -> None:
    """回写配置文件（仅用于 jobCache 自动维护）"""
    config_path = os.path.join(_get_script_dir(), "jenkins.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# ============================================================
# 任务名解析
# ============================================================

def _get_cache_key(config: Dict[str, Any], slug: str) -> str:
    prefix = config["systemConfig"]["jobPrefix"]
    lookup = slug[len(prefix):] if slug.startswith(prefix) else slug
    return lookup.casefold()


def resolve_job_name(client: JenkinsClient, config: Dict[str, Any], slug: str) -> str:
    """解析真实 job 名。

    支持短标识（如 "siot"）→ 查缓存/匹配 Jenkins 任务列表，
    也支持完整 job 名（如 "iBuilding-87A0-UNIT-CLOUD-siot"）→ 自动剥离前缀后匹配。

    缓存命中即视为有效——不额外发请求校验。若任务在 Jenkins 上被改名/删除导致
    触发构建时 404，由 build 命令 catch 404 清缓存重新解析。
    """
    prefix = config["systemConfig"]["jobPrefix"]
    cache_key = _get_cache_key(config, slug)
    cache = config.setdefault("jobCache", {})

    if cache_key in cache:
        entry = cache[cache_key]
        if isinstance(entry, str):
            cache[cache_key] = {"jobSuffix": entry, "component_sections": None}
            _save_config(config)
        return prefix + cache[cache_key]["jobSuffix"]

    # 慢路径：从 Jenkins 匹配
    lookup = slug[len(prefix):] if slug.startswith(prefix) else slug
    suffix = _match_job_suffix_from_jenkins(client, prefix, lookup)
    cache[cache_key] = {"jobSuffix": suffix, "component_sections": None}
    _save_config(config)
    return prefix + suffix


def _match_job_suffix_from_jenkins(client: JenkinsClient, prefix: str, slug: str) -> str:
    """拉 Jenkins 全部 job 名，按前缀取尾部与 slug 大小写不敏感匹配"""
    try:
        data = client.get_jobs()
    except JenkinsError as e:
        raise JenkinsError(f"获取任务列表失败：{e}") from e

    names = [j.get("name", "") for j in data.get("jobs", [])]
    suffixes = [n[len(prefix):] for n in names if n.startswith(prefix)]

    slug_cf = slug.casefold()
    matched = [s for s in suffixes if s.casefold() == slug_cf]

    if len(matched) == 1:
        return matched[0]
    if not matched:
        raise JobNotFoundError(
            f"未找到任务 '{slug}'，相近后缀: {', '.join(suffixes) if suffixes else '(无)'}"
        )
    raise JobNotFoundError(
        f"任务 '{slug}' 匹配到多个后缀，请明确指定其一: {', '.join(matched)}"
    )


# ============================================================
# 组件列表
# ============================================================

def _get_component_sections(
    client: JenkinsClient, config: Dict[str, Any], job_name: str, cache_key: str,
) -> List[str]:
    """获取组件列表：优先缓存，缓存未命中从 Jenkins HTML 解析并回写"""
    cache = config.setdefault("jobCache", {})
    entry = cache.get(cache_key)

    if isinstance(entry, dict) and entry.get("component_sections"):
        return entry["component_sections"]

    components = client.fetch_component_sections(job_name)

    if cache_key in cache and isinstance(cache[cache_key], dict):
        cache[cache_key]["component_sections"] = components
    elif cache_key in cache:
        cache[cache_key] = {"jobSuffix": cache[cache_key], "component_sections": components}
    else:
        suffix = job_name[len(config["systemConfig"]["jobPrefix"]):]
        cache[cache_key] = {"jobSuffix": suffix, "component_sections": components}
    _save_config(config)

    return components


# ============================================================
# Git 信息采集
# ============================================================

def _collect_git_info() -> Dict[str, str]:
    """收集本地 git 信息：仓库名、当前分支、当前目录名。失败时对应字段为空字符串。"""

    def _git(args: List[str]) -> str:
        try:
            result = subprocess.run(
                ["git"] + args, capture_output=True, text=True, timeout=10,
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except Exception:
            return ""

    repo_path = _git(["rev-parse", "--show-toplevel"])
    repo_name = os.path.basename(repo_path) if repo_path else ""
    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"])
    cwd_name = os.path.basename(os.getcwd())

    return {"repo_name": repo_name, "branch": branch, "cwd_name": cwd_name}


# ============================================================
# 凭据与 client 创建
# ============================================================

def create_jenkins_client(config: Dict[str, Any]) -> JenkinsClient:
    """创建 Jenkins client。凭据经 get_valid_credentials 统一获取：
    有已存凭据先验证（发一次请求），通过直接用；无凭据或已存失效则弹窗重输。
    """
    url = config["systemConfig"]["url"]

    def verify(username: str, password: str) -> Optional[str]:
        try:
            tmp = JenkinsClient(url, username, password)
            tmp._request("GET", "/api/json")
            return None
        except JenkinsAuthError:
            return "账号或密码错误，请重新输入"
        except JenkinsFatalError as e:
            raise RuntimeError(str(e)) from e

    username, password = creds.get_valid_credentials(verify)
    return JenkinsClient(url, username, password)


# ============================================================
# resolve — 构建参数解析
# ============================================================

def resolve_build_params(
    config: Dict[str, Any],
    slug: Optional[str] = None,
    user_branch: Optional[str] = None,
    user_components: Optional[str] = None,
    user_jdk: Optional[str] = None,
) -> Dict[str, Any]:
    """将用户意图解析为确定的构建参数，返回结构化 dict。

    输出字段：
      job:                 完整 job 名
      branch:              分支名
      componentSections:   可构建组件列表
      selectedComponents:  待构建组件
      jdkVersion:          JDK 版本

    组件匹配规则：
    - 用户指定了 --components → 逗号分割后逐一校验，不在 componentSections 中的忽略并告警
    - 用户未指定 → 当前目录名若在 componentSections 中则自动选中，否则为空数组
    """
    git_info = _collect_git_info()

    # slug 推导：用户指定 > 仓库目录名
    if not slug:
        slug = git_info["repo_name"]

    # branch 推导：用户指定 > 当前分支
    branch = user_branch or git_info["branch"]

    # jdk 推导：用户指定 > 配置默认值
    jdk = user_jdk or config["systemConfig"].get("defaultJDK", "")

    # job 名解析（缓存优先）
    cache_key = _get_cache_key(config, slug)
    cache = config.setdefault("jobCache", {})
    entry = cache.get(cache_key)

    if isinstance(entry, dict) and entry.get("jobSuffix"):
        job_name = config["systemConfig"]["jobPrefix"] + entry["jobSuffix"]
        client = None
    elif isinstance(entry, str):
        job_name = config["systemConfig"]["jobPrefix"] + entry
        client = None
    else:
        client = create_jenkins_client(config)
        job_name = resolve_job_name(client, config, slug)

    # 组件列表（缓存优先）
    if isinstance(entry, dict) and entry.get("component_sections"):
        component_sections = entry["component_sections"]
    else:
        if client is None:
            client = create_jenkins_client(config)
        component_sections = _get_component_sections(client, config, job_name, cache_key)

    # 待构建组件：用户指定 > 当前目录名匹配
    if user_components is not None:
        user_list = [c.strip() for c in user_components.split(",") if c.strip()]
        valid = [c for c in user_list if c in component_sections]
        invalid = [c for c in user_list if c not in component_sections]
        if invalid:
            print(
                f"警告：以下组件不在可构建列表中，已忽略：{', '.join(invalid)}",
                file=sys.stderr,
            )
        selected_components = valid
    else:
        cwd = git_info["cwd_name"]
        matched = [c for c in component_sections if cwd in c]
        selected_components = [matched[0]] if len(matched) == 1 else []

    return {
        "job": job_name,
        "branch": branch,
        "componentSections": component_sections,
        "selectedComponents": selected_components,
        "jdkVersion": jdk,
    }


# ============================================================
# build — 触发构建
# ============================================================

def trigger_and_get_build_number(
    client: JenkinsClient,
    job_name: str,
    build_params: Dict[str, str],
    queue_poll_interval: float = 2.0,
    queue_poll_max_retries: int = 60,
) -> Tuple[int, int]:
    """触发构建并轮询队列获取构建编号。

    返回 (queue_id, build_number)。
    队列等待超时抛 JenkinsError。
    """
    queue_id = client.trigger_build(job_name, build_params)
    if queue_id is None:
        raise JenkinsError("触发构建失败：未能获取队列 ID")

    build_number = _poll_queue_for_build_number(
        client, job_name, queue_id,
        poll_interval=queue_poll_interval,
        max_retries=queue_poll_max_retries,
    )
    if build_number is None:
        timeout_sec = queue_poll_max_retries * queue_poll_interval
        raise JenkinsError(
            f"队列等待超时：{timeout_sec} 秒内未获取到构建编号 (queueId={queue_id})"
        )

    return queue_id, build_number


def _poll_queue_for_build_number(
    client: JenkinsClient, job_name: str, queue_id: int,
    poll_interval: float = 2.0, max_retries: int = 60,
) -> Optional[int]:
    """轮询 Jenkins 队列，获取构建编号。

    404 特殊处理：队列项还没出现/已消失→从最近构建中按 queueId 匹配。
    """
    for i in range(max_retries):
        try:
            queue_info = client.get_queue_item(queue_id)
            logger.debug(f"轮询队列 [{i + 1}/{max_retries}]")

            executable = queue_info.get("executable")
            if executable and "number" in executable:
                return executable["number"]

            if queue_info.get("cancelled"):
                return None

        except JenkinsNotFoundError:
            build_number = _find_build_from_queue_id(client, job_name, queue_id)
            if build_number is not None:
                return build_number
        except Exception as e:
            logger.warning(f"轮询队列异常: {e}")

        if i < max_retries - 1:
            time.sleep(poll_interval)

    return None


def _find_build_from_queue_id(
    client: JenkinsClient, job_name: str, queue_id: int,
) -> Optional[int]:
    """当队列项已消失时，从最近构建中匹配 queueId"""
    try:
        job_info = client.get_job_details(job_name)
        for build in job_info.get("builds", []):
            build_number = build["number"]
            try:
                build_info = client.get_build_info(job_name, build_number)
                if build_info.get("queueId") == queue_id:
                    return build_number
            except JenkinsNotFoundError:
                continue
    except JenkinsNotFoundError:
        return None
    except Exception as e:
        logger.warning(f"查找构建时发生异常：{e}")
    return None


# ============================================================
# result — 轮询构建结果
# ============================================================

def query_build_result(
    client: JenkinsClient,
    job: str,
    build_number: int,
    timeout: float = 600,
    interval: float = 5,
) -> Dict[str, Any]:
    """轮询构建状态直到结束，返回最终结果。

    输出字段：
      job:               任务名
      buildNumber:       构建编号
      result:            Jenkins 构建结果，SUCCESS 表示成功
      imageTag:          镜像标签
      successComponents: 构建成功的组件列表
      failedComponents:  构建失败的组件列表
      consoleUrl:        Jenkins 控制台地址
    """
    console_url = client.console_url(job, build_number)
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            build_info = client.get_build_info(job, build_number)
        except JenkinsNotFoundError:
            # 构建号还没出现，等 interval 后重试
            print(f"构建中... 构建号尚未分配", file=sys.stderr)
            time.sleep(interval)
            continue

        result = build_info.get("result")
        if result is not None:
            image_tag = ""
            success_components = ""
            failed_components = ""
            try:
                co = client.get_console_output(job, build_number)
                image_tag = co.get("imageTag", "")
                success_components = co.get("successComponents", "")
                failed_components = co.get("failedComponents", "")
            except Exception:
                pass

            return {
                "job": job,
                "buildNumber": build_number,
                "result": result,
                "imageTag": image_tag,
                "successComponents": success_components,
                "failedComponents": failed_components,
                "consoleUrl": console_url,
            }

        # 构建中，输出进度
        elapsed = build_info.get("duration", 0)
        print(f"构建中... 已耗时 {elapsed // 1000}s", file=sys.stderr)
        time.sleep(interval)

    raise JenkinsError(
        f"构建结果等待超时：{timeout} 秒内未获取到最终结果 (job={job}, buildNumber={build_number})"
    )


# ============================================================
# CLI
# ============================================================

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Jenkins 构建工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  python jenkins_build.py resolve siot
  python jenkins_build.py resolve siot --branch master --components siot-a
  python jenkins_build.py build --job iBuilding-87A0-UNIT-CLOUD-siot --components siot-a --branch master --jdk 11.0.15.1
  python jenkins_build.py result --job iBuilding-87A0-UNIT-CLOUD-siot --build-number 1234
""",
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # resolve
    p_resolve = subparsers.add_parser("resolve", help="采集并解析构建参数")
    p_resolve.add_argument("slug", nargs="?", default=None, help="Jenkins 任务短标识")
    p_resolve.add_argument("--branch", "-b", default=None, help="分支名称")
    p_resolve.add_argument("--components", "-c", default=None, help="要构建的组件（逗号分割）")
    p_resolve.add_argument("--jdk", default=None, help="JDK 版本")

    # build
    p_build = subparsers.add_parser("build", help="触发构建")
    p_build.add_argument("--job", required=True, help="完整 Jenkins job 名")
    p_build.add_argument("--components", required=True, help="要构建的组件（逗号分割）")
    p_build.add_argument("--branch", required=True, help="分支名称")
    p_build.add_argument("--jdk", required=True, help="JDK 版本")
    p_build.add_argument("--param", "-p", action="append", default=[], dest="extra_params",
                         help="额外 Jenkins 参数，格式 key=value（可多次指定）")

    # result
    p_result = subparsers.add_parser("result", help="轮询构建状态直到结束")
    p_result.add_argument("--job", required=True, help="完整 Jenkins job 名")
    p_result.add_argument("--build-number", "-n", type=int, required=True, help="构建编号")

    return parser


def main():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")

    parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        config = load_config()

        if args.command == "resolve":
            result = resolve_build_params(
                config, args.slug, args.branch, args.components, args.jdk,
            )
            print(json.dumps(result, ensure_ascii=False))

        elif args.command == "build":
            client = create_jenkins_client(config)

            build_params: Dict[str, str] = {
                "component_sections": args.components,
                "Branch": args.branch,
                "JDK_version": args.jdk,
            }
            for kv in (args.extra_params or []):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    build_params[k] = v
                else:
                    build_params[kv] = ""

            queue_id, build_number = trigger_and_get_build_number(
                client, args.job, build_params,
            )
            console_url = client.console_url(args.job, build_number)

            print(json.dumps({
                "job": args.job,
                "buildNumber": build_number,
                "consoleUrl": console_url,
            }, ensure_ascii=False))

        elif args.command == "result":
            client = create_jenkins_client(config)
            sc = config["systemConfig"]
            result = query_build_result(client, args.job, args.build_number,
                                        timeout=sc.get("pollTimeoutSeconds", 600),
                                        interval=sc.get("pollIntervalSeconds", 5))
            print(json.dumps(result, ensure_ascii=False))

        else:
            print(json.dumps({"error": "UnknownCommand", "message": f"未知命令: {args.command}"}), file=sys.stderr)
            sys.exit(1)

    except creds.CredentialInputCancelled:
        print(json.dumps({"error": "CredentialInputCancelled", "message": "用户取消输入凭据"}), file=sys.stderr)
        sys.exit(1)
    except JenkinsError as e:
        print(json.dumps({"error": type(e).__name__, "message": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": type(e).__name__, "message": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()