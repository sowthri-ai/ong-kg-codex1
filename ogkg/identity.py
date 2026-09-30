"""
Identity and cross-system identifiers for OGKG reference models (contract module, v0.5).

- Node IRIs are site-scoped:        https://example.org/ogkg/data/<site>#<node id>
- Fact IDs are content-derived:     F-<12 hex of sha1(site|subject|predicate|valid_from|source_system)>
  so a rebuild never renumbers a fact, and two sites can never collide.
- External identifiers follow the conventions a real site's systems use, so connectors and
  entity resolution can map messy source records onto graph nodes:
      PI      historian tag            11FI1001.PV   (unit code + ISA letters + loop number + attribute)
      SAP_FL  functional location      GAM-CDU-A-CHG-P-101A
      SAP_EQ  equipment number         8 digits, stable hash of the site-scoped node id
      LIMS    sample point             SP-GAM-V-102-BOOT
      RBI     inspection record id     RBI-GAM-PC-102
See docs/dev/data-contract.md.
"""
import hashlib
import re

BASE = "https://example.org/ogkg/data/"
SITE_CODES = {"gamma": "GAM"}

# two-character plant-unit codes used as the prefix of historian tags
UNIT_CODES = {
    "CDU-COM": "10", "CDU-A": "11", "CDU-B": "12", "TF-1": "19", "VDU-1": "21", "DCU-1": "22",
    "VGOHT-1": "30", "FCC-1": "31", "GHT-1": "32", "HCU-1": "41", "DHT-1": "42", "KHT-1": "43",
    "NHT-1": "51", "CCR-1": "52", "ISOM-1": "53", "ARO-1": "54", "ALKY-1": "61", "MTBE-1": "62", "LPG-1": "63",
    "LUBE-1": "71", "ASPH-1": "72", "HMU-1": "81", "ARU-1": "82", "SWS-1": "83", "SRU-1": "84",
    "GBL-1": "91", "DBL-1": "92", "TF-2": "93", "TF-3": "94", "MT-1": "95",
    "UTL-STM": "U1", "UTL-CW": "U2", "UTL-FG": "U3", "UTL-FLR": "U4", "UTL-N2": "U5", "UTL-WTR": "U6", "UTL-H2": "U7",
    "UTL-PWR": "U8",
}

EXTERNAL_SYSTEMS = ("PI", "SAP_FL", "SAP_EQ", "LIMS", "RBI", "CMS")


def iri(node_id, site="gamma"):
    return f"{BASE}{site}#{node_id}"


def fact_id(site, subject, predicate, valid_from, source_system, salt=""):
    key = "|".join(str(x) for x in (site, subject, predicate, valid_from, source_system, salt))
    return "F-" + hashlib.sha1(key.encode()).hexdigest()[:12]


def pi_tag(unit_id, tag_id, attribute="PV"):
    """'FI-1001' at CDU-A -> '11FI1001.PV'. Tag ids are <letters>-<number>."""
    letters, number = tag_id.split("-", 1)
    return f"{UNIT_CODES[unit_id]}{letters}{number}.{attribute}"


def sap_fl(site, unit_id, section_code, eq_id):
    return f"{SITE_CODES[site]}-{unit_id}-{section_code}-{eq_id}"


def sap_eq(site, eq_id):
    return str(10_000_000 + int(hashlib.sha1(f"{site}|{eq_id}".encode()).hexdigest()[:8], 16) % 89_999_999)


def lims_point(site, eq_id, item="SAMPLE"):
    return f"SP-{SITE_CODES[site]}-{eq_id}-{item}"


def rbi_id(site, eq_id):
    return f"RBI-{SITE_CODES[site]}-{eq_id}"


_TAG = re.compile(r"^(?:[0-9U][0-9])?-?([A-Z]{1,5})-?(\d{3,5}[A-Z]?)(?:\.(?:PV|SP|OP|MODE))?$")


def normalise_tag(raw):
    """Best-effort normalisation of an equipment or instrument tag as typed in a source system.
    'p101a' -> 'P-101A'; '11-FI-1001.PV' -> 'FI-1001'; ' e 120 a ' -> 'E-120A'. Returns None if no pattern fits."""
    s = re.sub(r"\s+", "", str(raw).upper()).replace("_", "-")
    m = _TAG.match(s)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}"
