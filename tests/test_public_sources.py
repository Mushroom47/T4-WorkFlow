"""公开来源缓存合同回归；全部网络响应和 DNS 均在测试中替换。"""

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import Mock, patch
import urllib.request


TOOL = Path(__file__).resolve().parents[1] / "tools/public_sources.py"
SPEC = importlib.util.spec_from_file_location("public_sources", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SourceFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.dataset = self.base / "public"
        self.cache = self.base / "cache"
        self.dataset.mkdir()
        self.cache.mkdir()
        self.body = b"publicly retrievable source bytes\n"
        self.entry = {"path": "sources/example/body.raw.json",
            "sha256": hashlib.sha256(self.body).hexdigest(), "bytes": len(self.body),
            "url": "https://public.example.test/source", "byte_form": "raw",
            "fetch_allowed": True, "redistribution": "local_only"}
        (self.dataset / "README.md").write_text("参与者自写的公开方法\n")
        self.write_catalog()

    def write_catalog(self, entries=None):
        (self.dataset / MODULE.CATALOG).write_text(json.dumps({
            "schema_version": "0.1.0", "sources": [self.entry] if entries is None else entries}))

    def write_cached(self, body=None):
        path = self.cache / self.entry["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.body if body is None else body)
        return path


class MaterializedDatasetTests(SourceFixture):
    def test_overlay_verifies_bytes_and_cleans_without_changing_inputs(self):
        cached = self.write_cached()
        original_catalog = (self.dataset / MODULE.CATALOG).read_bytes()
        with MODULE.materialized_dataset(self.dataset, self.cache) as merged:
            self.assertEqual((merged / self.entry["path"]).read_bytes(), self.body)
            self.assertEqual((merged / "README.md").read_bytes(), (self.dataset / "README.md").read_bytes())
            self.assertNotEqual(merged, self.dataset)
            (merged / "temporary.txt").write_text("仅合并目录内")
        self.assertFalse(merged.exists())
        self.assertFalse((self.dataset / self.entry["path"]).exists())
        self.assertFalse((self.dataset / "temporary.txt").exists())
        self.assertEqual(cached.read_bytes(), self.body)
        self.assertEqual((self.dataset / MODULE.CATALOG).read_bytes(), original_catalog)

    def test_missing_private_source_fails(self):
        with self.assertRaises(MODULE.SourceError):
            with MODULE.materialized_dataset(self.dataset, self.cache):
                self.fail("缺原件不得进入context")

    def test_same_length_wrong_hash_fails(self):
        self.write_cached(b"x" * len(self.body))
        with self.assertRaises(MODULE.SourceError):
            with MODULE.materialized_dataset(self.dataset, self.cache):
                self.fail("错误hash不得通过")

    def test_wrong_declared_bytes_fails_even_when_sha_matches(self):
        self.write_cached()
        self.write_catalog([{**self.entry, "bytes": len(self.body) + 1}])
        with self.assertRaises(MODULE.SourceError):
            with MODULE.materialized_dataset(self.dataset, self.cache):
                self.fail("错误bytes不得通过")

    def test_traversal_absolute_and_noncanonical_paths_fail(self):
        for path in ("../outside", "/tmp/outside", "sources/../outside", "./source", "sources//source", "sources/source/", "C:/outside", "sources\\outside"):
            with self.subTest(path=path):
                self.write_catalog([{**self.entry, "path": path}])
                with self.assertRaises(MODULE.SourceError):
                    MODULE.load_catalog(self.dataset)

    def test_cached_leaf_symlink_is_rejected_even_if_hash_would_match(self):
        outside = self.base / "outside.raw"
        outside.write_bytes(self.body)
        cached = self.cache / self.entry["path"]
        cached.parent.mkdir(parents=True)
        cached.symlink_to(outside)
        with self.assertRaises(MODULE.SourceError):
            with MODULE.materialized_dataset(self.dataset, self.cache):
                self.fail("软链接不得通过")

    def test_cached_parent_symlink_is_rejected(self):
        outside = self.base / "outside"
        (outside / "example").mkdir(parents=True)
        (outside / "example/body.raw.json").write_bytes(self.body)
        (self.cache / "sources").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(MODULE.SourceError):
            with MODULE.materialized_dataset(self.dataset, self.cache):
                self.fail("祖先软链接不得通过")

    def test_public_tree_symlink_is_rejected(self):
        self.write_cached()
        (self.dataset / "unlisted-link").symlink_to(self.cache, target_is_directory=True)
        with self.assertRaises(MODULE.SourceError):
            with MODULE.materialized_dataset(self.dataset, self.cache):
                self.fail("公开目录软链接不得通过")

    def test_cache_root_symlink_is_rejected(self):
        self.write_cached()
        linked = self.base / "linked-cache"
        linked.symlink_to(self.cache, target_is_directory=True)
        with self.assertRaises(MODULE.SourceError):
            with MODULE.materialized_dataset(self.dataset, linked):
                self.fail("cache根软链接不得通过")

    def test_directory_cannot_supply_source_bytes(self):
        (self.cache / self.entry["path"]).mkdir(parents=True)
        with self.assertRaises(MODULE.SourceError):
            with MODULE.materialized_dataset(self.dataset, self.cache):
                self.fail("目录不得作为原件")

    def test_existing_public_bytes_are_verified_without_cache(self):
        path = self.dataset / self.entry["path"]
        path.parent.mkdir(parents=True)
        path.write_bytes(self.body)
        with MODULE.materialized_dataset(self.dataset, None) as merged:
            self.assertEqual((merged / self.entry["path"]).read_bytes(), self.body)
        path.write_bytes(b"bad bytes")
        with self.assertRaises(MODULE.SourceError):
            with MODULE.materialized_dataset(self.dataset, None):
                self.fail("公开目录已存在原件也必须核对")

    def test_derived_fulltext_can_only_be_materialized_from_verified_local_bytes(self):
        self.write_catalog([{**self.entry, "byte_form": "derived_fulltext", "fetch_allowed": False}])
        self.write_cached()
        with MODULE.materialized_dataset(self.dataset, self.cache) as merged:
            self.assertEqual((merged / self.entry["path"]).read_bytes(), self.body)

    def test_duplicate_and_case_colliding_paths_are_rejected(self):
        for second in (self.entry, {**self.entry, "path": self.entry["path"].upper()}):
            with self.subTest(path=second["path"]):
                self.write_catalog([self.entry, second])
                with self.assertRaises(MODULE.SourceError):
                    MODULE.load_catalog(self.dataset)

    def test_malformed_contract_fields_are_rejected(self):
        invalid = [{"sha256": "unknown"}, {"bytes": True}, {"bytes": -1},
            {"byte_form": "html"}, {"fetch_allowed": "true"},
            {"redistribution": "MIT"}, {"url": 42}]
        for change in invalid:
            with self.subTest(change=change):
                self.write_catalog([{**self.entry, **change}])
                with self.assertRaises(MODULE.SourceError):
                    MODULE.load_catalog(self.dataset)

    def test_materialization_never_fetches_missing_source(self):
        with patch.object(MODULE, "_download_opener", side_effect=AssertionError("离线合并不得创建网络opener")):
            with self.assertRaises(MODULE.SourceError):
                with MODULE.materialized_dataset(self.dataset, self.cache):
                    self.fail("缺文件只能失败，不能自动取数")

    def test_context_exception_still_cleans_temporary_directory(self):
        self.write_cached()
        with self.assertRaisesRegex(RuntimeError, "caller failure"):
            with MODULE.materialized_dataset(self.dataset, self.cache) as merged:
                raise RuntimeError("caller failure")
        self.assertFalse(merged.exists())


def public_dns(*args, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))]


class DownloadURLTests(unittest.TestCase):
    def test_public_https_url_passes(self):
        with patch.object(MODULE.socket, "getaddrinfo", side_effect=public_dns):
            self.assertEqual(MODULE.validate_fetch_url("https://public.example.test/source?id=123"),
                "https://public.example.test/source?id=123")

    def test_non_https_and_credential_urls_are_rejected(self):
        urls = ["http://public.example.test/file", "file:///tmp/file", "ftp://public.example.test/file",
            "https://user:password@public.example.test/file", "https://public.example.test/file?api_key=secret",
            "https://public.example.test/file?access_token=secret", "https://localhost/file",
            "https://foo.local/file", "https://public.example.test/file#fragment", "https://public.example.test/a\nheader"]
        with patch.object(MODULE.socket, "getaddrinfo", side_effect=public_dns):
            for url in urls:
                with self.subTest(url=url), self.assertRaises(MODULE.SourceError):
                    MODULE.validate_fetch_url(url)

    def test_one_private_dns_address_rejects_the_entire_host(self):
        addresses = public_dns() + [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]
        with patch.object(MODULE.socket, "getaddrinfo", return_value=addresses), self.assertRaises(MODULE.SourceError):
            MODULE.validate_fetch_url("https://mixed.example.test/file")

    def test_ipv4_mapped_private_ipv6_is_rejected(self):
        addresses = [(socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::ffff:127.0.0.1", 443, 0, 0))]
        with patch.object(MODULE.socket, "getaddrinfo", return_value=addresses), self.assertRaises(MODULE.SourceError):
            MODULE.validate_fetch_url("https://mapped.example.test/file")

    def test_redirect_to_local_or_non_https_url_is_rejected(self):
        handler = MODULE._PublicRedirectHandler()
        request = urllib.request.Request("https://public.example.test/source")
        for target in ("file:///etc/passwd", "http://public.example.test/source", "https://localhost/source"):
            with self.subTest(target=target), self.assertRaises(MODULE.SourceError):
                handler.redirect_request(request, None, 302, "Found", {}, target)
        with patch.object(MODULE.socket, "getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 443))]), self.assertRaises(MODULE.SourceError):
            handler.redirect_request(request, None, 302, "Found", {}, "https://private.example.test/source")

    def test_actual_connection_uses_validated_ip_with_original_tls_hostname(self):
        connection = MODULE._PublicHTTPSConnection("public.example.test")
        connection._context = Mock()
        original_socket = Mock()
        with patch.object(MODULE.socket, "getaddrinfo", side_effect=public_dns), patch.object(MODULE.socket, "create_connection", return_value=original_socket) as create:
            connection.connect()
        self.assertEqual(create.call_args.args[0], ("8.8.8.8", 443))
        connection._context.wrap_socket.assert_called_once_with(original_socket, server_hostname="public.example.test")


class FakeResponse(io.BytesIO):
    def geturl(self):
        return "https://public.example.test/source"


class FetchSourcesTests(SourceFixture):
    def fake_fetch(self, body):
        opener = Mock()
        opener.open.return_value = FakeResponse(body)
        with patch.object(MODULE, "_download_opener", return_value=opener), patch.object(MODULE.socket, "getaddrinfo", side_effect=public_dns):
            result = MODULE.fetch_sources(self.dataset, self.cache)
        return result, opener

    def test_allowed_raw_download_must_match_hash_and_bytes(self):
        result, opener = self.fake_fetch(self.body)
        self.assertEqual(result[0]["status"], "downloaded_verified")
        self.assertEqual((self.cache / self.entry["path"]).read_bytes(), self.body)
        self.assertEqual(opener.open.call_count, 1)
        self.assertFalse((self.dataset / self.entry["path"]).exists())

    def test_forbidden_source_and_sanitized_wrapper_are_never_downloaded(self):
        entries = [{**self.entry, "fetch_allowed": False, "url": "https://www.amgen.com/restricted"},
            {**self.entry, "path": "sources/wrapper.json", "byte_form": "sanitized_wrapper"},
            {**self.entry, "path": "sources/fulltext.txt", "byte_form": "derived_fulltext"}]
        self.write_catalog(entries)
        result, opener = self.fake_fetch(b"must not be read")
        self.assertEqual([row["status"] for row in result], ["local_import_required"] * 3)
        opener.open.assert_not_called()

    def test_changed_hash_is_retained_only_as_not_matching(self):
        changed = b"x" * len(self.body)
        with self.assertRaises(MODULE.SourceError):
            self.fake_fetch(changed)
        self.assertFalse((self.cache / self.entry["path"]).exists())
        diagnostics = list(self.cache.rglob("*.not-matching"))
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].read_bytes(), changed)
        catalog = json.loads((self.dataset / MODULE.CATALOG).read_text())
        self.assertEqual(catalog["sources"][0]["sha256"], self.entry["sha256"])

    def test_oversized_response_is_bounded_and_cannot_fill_expected_path(self):
        with self.assertRaises(MODULE.SourceError):
            self.fake_fetch(self.body + b"unbounded extra response")
        self.assertFalse((self.cache / self.entry["path"]).exists())
        diagnostic = next(self.cache.rglob("*.not-matching"))
        self.assertEqual(diagnostic.stat().st_size, len(self.body) + 1)

    def test_existing_valid_cache_is_not_downloaded_again(self):
        cached = self.write_cached()
        result, opener = self.fake_fetch(b"different response")
        self.assertEqual(result[0]["status"], "already_verified")
        opener.open.assert_not_called()
        self.assertEqual(cached.read_bytes(), self.body)

    def test_existing_bad_cache_is_not_overwritten(self):
        cached = self.write_cached(b"corrupt old cache")
        with self.assertRaises(MODULE.SourceError):
            self.fake_fetch(self.body)
        self.assertEqual(cached.read_bytes(), b"corrupt old cache")

    def test_missing_url_cannot_trigger_a_download(self):
        self.write_catalog([{**self.entry, "url": None}])
        with self.assertRaises(MODULE.SourceError):
            self.fake_fetch(self.body)
        self.assertFalse((self.cache / self.entry["path"]).exists())


if __name__ == "__main__":
    unittest.main()
