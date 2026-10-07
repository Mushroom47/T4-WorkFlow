#!/usr/bin/env python3
"""公开数据目录与本地原件缓存的离线合并、校验及受限取数工具。"""

from contextlib import contextmanager
import argparse
import hashlib
import http.client
import ipaddress
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import socket
import ssl
import stat
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request


CATALOG = "public-source-catalog.json"


class SourceError(ValueError):
    """来源路径、保存字节或下载许可不符合公开来源合同。"""


def _relative_path(value):
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise SourceError("source path must be a nonempty relative POSIX path")
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts) or re.match(r"^[A-Za-z]:", value):
        raise SourceError("source path traversal or noncanonical path")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value:
        raise SourceError("source path must be relative and canonical")
    return value


def _root_directory(value, label):
    root = Path(value).absolute()
    try:
        mode = root.lstat().st_mode
    except OSError as exc:
        raise SourceError(f"{label} directory is unavailable: {root}") from exc
    if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
        raise SourceError(f"{label} must be a directory, without a root symlink")
    return root


def _safe_path(root, relative, *, must_exist=True):
    """逐段检查，拒绝相对路径内部的软链接及非普通文件。"""
    relative = _relative_path(relative)
    path = root
    parts = relative.split("/")
    for index, part in enumerate(parts):
        path = path / part
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError as exc:
            if must_exist:
                raise SourceError(f"source is missing: {relative}") from exc
            return root / relative
        except OSError as exc:
            raise SourceError(f"source path cannot be read: {relative}") from exc
        if stat.S_ISLNK(mode):
            raise SourceError(f"source symlink is forbidden: {relative}")
        if index < len(parts) - 1:
            if not stat.S_ISDIR(mode):
                raise SourceError(f"source parent is not a directory: {relative}")
        elif not stat.S_ISREG(mode):
            raise SourceError(f"source is not a regular file: {relative}")
    return path


@contextmanager
def _open_original(root, relative):
    """POSIX 使用目录 fd 和 O_NOFOLLOW；其他平台仍逐段拒绝软链接。"""
    path = _safe_path(root, relative)
    directory_fds = []
    handle = None
    try:
        if os.open in os.supports_dir_fd and hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY"):
            directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            current = os.open(root, directory_flags)
            directory_fds.append(current)
            parts = relative.split("/")
            for part in parts[:-1]:
                current = os.open(part, directory_flags, dir_fd=current)
                directory_fds.append(current)
            fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=current)
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                os.close(fd)
                raise SourceError(f"source is not a regular file: {relative}")
            handle = os.fdopen(fd, "rb")
        else:
            handle = path.open("rb")
        yield handle
    except OSError as exc:
        raise SourceError(f"cannot open source without symlinks: {relative}") from exc
    finally:
        if handle is not None:
            handle.close()
        for fd in reversed(directory_fds):
            os.close(fd)


def _reject_tree_links(root):
    for directory, subdirectories, files in os.walk(root, followlinks=False):
        for name in subdirectories + files:
            path = Path(directory) / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode) or not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise SourceError(f"dataset contains a symlink or special file: {path.relative_to(root)}")


def load_catalog(dataset):
    """读取严格的 0.1.0 catalog；不访问网络。"""
    root = _root_directory(dataset, "dataset")
    with _open_original(root, CATALOG) as stream:
        try:
            catalog = json.load(stream)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise SourceError("invalid public source catalog JSON") from exc
    if not isinstance(catalog, dict) or catalog.get("schema_version") != "0.1.0":
        raise SourceError("public source catalog schema_version must be 0.1.0")
    sources = catalog.get("sources")
    if not isinstance(sources, list):
        raise SourceError("public source catalog sources must be an array")
    seen = set()
    for entry in sources:
        if not isinstance(entry, dict):
            raise SourceError("catalog source must be an object")
        relative = _relative_path(entry.get("path"))
        if relative.casefold() in seen:
            raise SourceError(f"duplicate or case-colliding source path: {relative}")
        seen.add(relative.casefold())
        if not isinstance(entry.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
            raise SourceError(f"invalid source sha256: {relative}")
        if type(entry.get("bytes")) is not int or entry["bytes"] < 0:
            raise SourceError(f"invalid source bytes: {relative}")
        if entry.get("byte_form") not in ("raw", "sanitized_wrapper", "derived_fulltext"):
            raise SourceError(f"invalid source byte_form: {relative}")
        if type(entry.get("fetch_allowed")) is not bool:
            raise SourceError(f"invalid source fetch_allowed: {relative}")
        if entry.get("redistribution") != "local_only":
            raise SourceError(f"unsupported source redistribution: {relative}")
        if "url" not in entry or entry["url"] is not None and not isinstance(entry["url"], str):
            raise SourceError(f"source url must be a string or null: {relative}")
    return catalog


def _checked_copy(root, entry, destination=None):
    digest = hashlib.sha256()
    length = 0
    with _open_original(root, entry["path"]) as source:
        target = destination.open("wb") if destination is not None else None
        try:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                length += len(block)
                digest.update(block)
                if target is not None:
                    target.write(block)
        finally:
            if target is not None:
                target.close()
    if length != entry["bytes"] or digest.hexdigest() != entry["sha256"]:
        raise SourceError(f"source bytes/hash mismatch: {entry['path']}")


@contextmanager
def materialized_dataset(dataset, private_sources):
    """临时复制公开 dataset 并补入已核验的缓存；退出时清理，原目录不变。

    private_sources 自身采用 dataset 相对布局，例如 cache/sources/...
    所有 catalog 项均检查 bytes 与 SHA-256；目录、叶节点软链接均拒绝。
    该函数仅做本地读取，绝不自动下载许可不明的材料。
    """
    root = _root_directory(dataset, "dataset")
    catalog = load_catalog(root)
    _reject_tree_links(root)
    cache = None if private_sources is None else _root_directory(private_sources, "private sources")
    with tempfile.TemporaryDirectory(prefix="t4-public-sources-") as directory:
        merged = Path(directory) / "dataset"
        shutil.copytree(root, merged)
        _reject_tree_links(merged)
        for entry in catalog["sources"]:
            target = _safe_path(merged, entry["path"], must_exist=False)
            if target.exists():
                _checked_copy(merged, entry)
            else:
                if cache is None:
                    raise SourceError(f"private source cache required: {entry['path']}")
                _safe_path(cache, entry["path"])
                target.parent.mkdir(parents=True, exist_ok=True)
                _checked_copy(cache, entry, target)
        yield merged


def _public_addresses(host, port):
    try:
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise SourceError("download hostname cannot be resolved") from exc
    public = []
    for _, _, _, _, address in addresses:
        try:
            ip = ipaddress.ip_address(address[0])
        except ValueError as exc:
            raise SourceError("invalid download network address") from exc
        actual = ip.ipv4_mapped if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped else ip
        if not actual.is_global:
            raise SourceError("download to a private, loopback or reserved address is forbidden")
        if str(ip) not in public:
            public.append(str(ip))
    if not public:
        raise SourceError("download hostname has no public address")
    return public


def validate_fetch_url(url):
    """只接受无凭证的公开 HTTPS URL；每个重定向和实际连接均重新检查。"""
    if not isinstance(url, str) or not url or any(ord(character) < 33 for character in url):
        raise SourceError("download URL is missing or contains whitespace/control characters")
    try:
        parsed = urllib.parse.urlsplit(url)
        host, port = parsed.hostname, parsed.port or 443
    except ValueError as exc:
        raise SourceError("invalid download URL") from exc
    if parsed.scheme != "https" or not host:
        raise SourceError("only HTTPS downloads are permitted")
    if parsed.username is not None or parsed.password is not None or "%" in parsed.netloc:
        raise SourceError("credentials or encoded authority in a download URL are forbidden")
    if parsed.fragment:
        raise SourceError("download URL fragments are not supported")
    for key, _ in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True):
        normalized = key.casefold().replace("-", "_")
        if any(word in normalized for word in ("token", "password", "secret", "credential", "signature", "authorization")) or normalized in ("apikey", "api_key", "key", "sig", "auth"):
            raise SourceError("credential-bearing download query is forbidden")
    host = host.rstrip(".")
    if host.casefold() == "localhost" or host.casefold().endswith((".localhost", ".local", ".internal")):
        raise SourceError("local download host is forbidden")
    _public_addresses(host, port)
    return url


class _PublicHTTPSConnection(http.client.HTTPSConnection):
    def connect(self):
        if self._tunnel_host:
            raise SourceError("proxy tunnels are not permitted for source downloads")
        addresses = _public_addresses(self.host.rstrip("."), self.port)
        # 用已验证 IP 建立连接，TLS 仍以原 hostname 做 SNI/证书核验，避免 DNS 再绑定。
        self.sock = socket.create_connection((addresses[0], self.port), self.timeout, self.source_address)
        self.sock = self._context.wrap_socket(self.sock, server_hostname=self.host)


class _PublicHTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, request):
        validate_fetch_url(request.full_url)
        return self.do_open(_PublicHTTPSConnection, request, context=self._context)


class _PublicRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        validate_fetch_url(newurl)
        return super().redirect_request(request, response, code, message, headers, newurl)


def _download_opener():
    # 不读取环境代理，避免经代理改变已核验的目标/凭证传播范围。
    return urllib.request.build_opener(urllib.request.ProxyHandler({}),
        _PublicHTTPSHandler(context=ssl.create_default_context()), _PublicRedirectHandler())


def _cache_parent(cache, relative):
    path = cache
    for part in _relative_path(relative).split("/")[:-1]:
        path = path / part
        try:
            path.mkdir()
        except FileExistsError:
            pass
        if stat.S_ISLNK(path.lstat().st_mode) or not path.is_dir():
            raise SourceError("cache parent must be a directory without symlinks")
    return cache / relative


def fetch_sources(dataset, private_sources, *, timeout=30):
    """下载 catalog 明确允许的 raw，wrapper/全文派生/禁取资料只报告本地导入需要。

    哈希不同或超过声明长度时保留 *.not-matching，抛 SourceError；
    不把它放到期望路径，也不修改 catalog 或期望哈希。
    """
    catalog = load_catalog(dataset)
    cache_path = Path(private_sources).absolute()
    cache_path.mkdir(parents=True, exist_ok=True)
    cache = _root_directory(cache_path, "private sources")
    results = []
    opener = _download_opener()
    for entry in catalog["sources"]:
        destination = _safe_path(cache, entry["path"], must_exist=False)
        if destination.exists():
            _checked_copy(cache, entry)
            results.append({"path": entry["path"], "status": "already_verified"})
            continue
        if not entry["fetch_allowed"] or entry["byte_form"] != "raw":
            results.append({"path": entry["path"], "status": "local_import_required"})
            continue
        validate_fetch_url(entry["url"])
        destination = _cache_parent(cache, entry["path"])
        request = urllib.request.Request(entry["url"], headers={
            "User-Agent": "T4-WorkFlow public source reproducibility",
            "Accept-Encoding": "identity"})
        temporary = None
        digest, length, complete = hashlib.sha256(), 0, True
        try:
            with opener.open(request, timeout=timeout) as response:
                validate_fetch_url(response.geturl())
                with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=destination.name + ".download-", delete=False) as output:
                    temporary = Path(output.name)
                    while True:
                        # 至多保存声明长度+1；避免恶意响应无限消耗磁盘。
                        block = response.read(min(1024 * 1024, entry["bytes"] + 1 - length))
                        if not block:
                            break
                        output.write(block)
                        digest.update(block)
                        length += len(block)
                        if length > entry["bytes"]:
                            complete = False
                            break
            if length != entry["bytes"] or digest.hexdigest() != entry["sha256"]:
                mismatch = destination.with_name(destination.name + "." + digest.hexdigest() + ".not-matching")
                if mismatch.exists() or mismatch.is_symlink():
                    raise SourceError("mismatch diagnostic path already exists; original left unchanged")
                temporary.rename(mismatch)
                temporary = None
                detail = "complete response" if complete else "response prefix: exceeded declared bytes"
                raise SourceError(f"download bytes/hash mismatch ({detail}); retained {mismatch}")
            if destination.exists() or destination.is_symlink():
                raise SourceError("source destination appeared during download; refusing overwrite")
            temporary.rename(destination)
            temporary = None
            results.append({"path": entry["path"], "status": "downloaded_verified",
                "sha256": digest.hexdigest(), "bytes": length})
        except (OSError, urllib.error.URLError, http.client.HTTPException) as exc:
            raise SourceError(f"source download failed: {entry['path']}: {exc}") from exc
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("verify", "fetch"):
        command = commands.add_parser(name)
        command.add_argument("--dataset", required=True, type=Path)
        command.add_argument("--private-sources", required=True, type=Path)
        if name == "fetch":
            command.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args(argv)
    try:
        if args.command == "fetch":
            results = fetch_sources(args.dataset, args.private_sources, timeout=args.timeout)
        else:
            with materialized_dataset(args.dataset, args.private_sources):
                results = {"status": "verified", "sources": len(load_catalog(args.dataset)["sources"])}
    except SourceError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
