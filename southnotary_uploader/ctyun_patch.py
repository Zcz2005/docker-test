from __future__ import annotations

import re


def patch_ctyun_zos_region_parser() -> None:
    """Patch CTYun OOS SDK region parsing to accept huanan2.zos.ctyun.cn endpoints."""
    try:
        import ooscore.args
        from ooscore.compat import urlsplit
    except ImportError as exc:
        raise RuntimeError(
            "CTYun OOS SDK is not installed. Install the SDK that provides "
            "`oos` and `ooscore` before starting this service."
        ) from exc

    current_method = ooscore.args.ClientArgsCreator._get_ctyun_region_re
    if getattr(current_method, "_southnotary_zos_patch", False):
        return

    ooscore.args.REGION_PATTERN = r".*(oos|zos)-(?P<region>[a-zA-Z0-9\-]+?)(-sts)?\."
    ooscore.args.REGION_RE = re.compile(ooscore.args.REGION_PATTERN)

    def _patched_get_ctyun_region_re(self, endpoint_url):
        hostname = urlsplit(endpoint_url).hostname
        match = ooscore.args.REGION_RE.match(hostname or "")
        if match and match.group("region"):
            return match.group("region"), match.group("region")

        if hostname and ".zos." in hostname:
            parts = hostname.split(".")
            if len(parts) >= 3 and parts[1] == "zos":
                return parts[0], parts[0]

        raise Exception("Invalid Endpoint!")

    _patched_get_ctyun_region_re._southnotary_zos_patch = True
    ooscore.args.ClientArgsCreator._get_ctyun_region_re = _patched_get_ctyun_region_re
