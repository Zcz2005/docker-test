"""Patch ooscore to support zos-format endpoints."""

import re

import ooscore.args

ooscore.args.REGION_PATTERN = r".*(oos|zos)-(?P<region>[a-zA-Z0-9\-]+?)(-sts)?\."
ooscore.args.REGION_RE = re.compile(ooscore.args.REGION_PATTERN)


def _patched_get_ctyun_region_re(self, endpoint_url):
    from ooscore.compat import urlsplit

    hostname = urlsplit(endpoint_url).hostname
    match = ooscore.args.REGION_RE.match(hostname)
    if match and match.group("region"):
        return match.group("region"), match.group("region")
    if hostname and ".zos." in hostname:
        parts = hostname.split(".")
        if len(parts) >= 3 and parts[1] == "zos":
            return parts[0], parts[0]
    raise Exception("Invalid Endpoint!")


ooscore.args.ClientArgsCreator._get_ctyun_region_re = _patched_get_ctyun_region_re
