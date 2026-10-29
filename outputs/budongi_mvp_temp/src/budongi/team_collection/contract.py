"""Contract constants for role-2 team_collection_v1 packages (ROLE2-COLLECT-001).

Values mirror docs/team-data-contract.md sections 2-7. Every unit and shell
imports names from here instead of repeating literals.
"""
from __future__ import annotations

import re

DELIVERY_SCHEMA_VERSION = "team_collection_v1"
QUALITY_STATUS = "source_unverified"
JOURNAL_SCHEMA = "role2_journal_v1"
PLAN_SCHEMA = "role2_plan_v1"
REGISTRY_SCHEMA = "role2_sources_v1"
DATASET_PREFIX = "T"
ISSUE_PREFIX = "T-I"
OWNER = "cannedJean"

RECORD_TYPES = ("facility", "transit_route", "transit_stop_link", "time_observation",
                "spatial_layer", "regional_statistic")
RAW_ONLY = "raw_only"
LANES = ("A1", "A2", "B", "C", "D", "E")
FILE_LANES = frozenset({"A1", "A2", "E"})

ENVELOPE_FIELDS = (
    "delivery_schema_version", "source_id", "batch_id", "mapping_version", "record_type",
    "source_file_ref", "source_content_sha256", "source_section", "source_row_number",
    "source_column_number", "source_feature_id", "source_record_id",
    "source_retrieved_at_utc", "provided_at_utc", "staged_at_utc", "loaded_at_utc",
    "source_published_at_utc", "source_date", "source_effective_from", "source_effective_to",
    "quality_status", "validation_status", "validation_reason",
)
LOCATION_FIELDS = (
    "entity_level", "identifier_namespace", "source_entity_id", "sgg_cd", "bjd_cd", "adm_cd",
    "region_name_raw", "region_path_raw", "road_address_raw", "jibun_address_raw",
    "complex_id", "building_id", "address_id",
    "latitude", "longitude", "source_x", "source_y", "source_crs", "source_axis_order",
    "coordinate_method", "coordinate_evidence_ref", "coordinate_review_status",
)
REQUIRED_FIELDS = {
    "facility": ("name", "facility_type_code", "entity_level"),
    "transit_route": ("identifier_namespace", "source_entity_id", "name"),
    "transit_stop_link": ("route_namespace", "source_route_id", "stop_namespace", "source_stop_id",
                          "stop_sequence"),
    "time_observation": ("metric_code", "subject_namespace", "source_subject_id", "observed_at_utc",
                         "unit_code", "value_status"),
    "spatial_layer": ("layer_id", "representation", "geometry_ref", "source_crs"),
    "regional_statistic": ("metric_code", "region_path_raw", "frequency", "period_key", "unit_code",
                           "value_status", "dimensions_json"),
}
VALUE_TYPES = frozenset({"time_observation", "regional_statistic"})  # value_decimal when numeric
VALUE_STATUSES = ("numeric", "missing")
REPRESENTATIONS = ("image", "vector", "raster")

VALIDATION_STATUSES = ("accepted", "excluded", "rejected")
JSONL_STATUSES = ("accepted", "rejected")  # excluded rows are counted, never written to JSONL
REQUEST_STATUSES = ("complete", "complete_zero", "partial", "failed", "not_collected", "inconsistent")
BATCH_COMPLETE = frozenset({"complete", "complete_zero"})
ATTEMPT_STATUSES = ("received", "success", "error", "interrupted_write")
LICENSE_CLASSES = ("kogl1", "kogl2", "kogl3", "kogl4", "unrestricted", "noncommercial", "unknown")
LICENSE_REVIEW = ("pending", "verified", "rejected")
RESTRICTED_LICENSES = frozenset({"kogl3", "kogl4", "noncommercial"})  # share raw + metadata only
SOURCE_STATUSES = ("approved", "pending", "excluded")

# reason code -> validation status it implies
REASONS = {
    "blank_row": "excluded", "out_of_scope_region": "excluded", "scope_undetermined": "excluded",
    "duplicate_delivery": "excluded",
    "ragged_row": "rejected", "missing_required": "rejected", "invalid_number": "rejected",
    "invalid_date": "rejected", "invalid_code": "rejected", "invalid_sequence": "rejected",
    "invalid_geometry": "rejected",
}
COORDINATE_NULL_REASONS = ("missing", "crs_unknown", "crs_not_wgs84", "axis_unknown", "not_finite",
                           "out_of_range")

WGS84 = "EPSG:4326"
KOREA_LAT, KOREA_LON = (33.0, 39.0), (124.0, 132.0)
SEOUL_LAT, SEOUL_LON = (37.0, 38.0), (126.0, 128.0)

BATCH_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-\d{8}-v\d+$")
BATCH_ID_MAX = 80
SOURCE_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
T_ID_RE = re.compile(r"^[TRL]\d{1,3}[a-z]?$")
REQUEST_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
RECORD_URL_RE = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+/issues/[1-9]\d*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

MAX_FILE_BYTES = 2 * 1024 ** 3
MAX_RESPONSE_BYTES = 32 * 1024 * 1024
PART_BYTES = 95 * 1024 * 1024
QUOTA_STOP_RATIO = 0.95
USER_AGENT = "jipdam-role2-collection/1"


class ContractError(ValueError):
    """Carries a stable error code only; never echoes URLs, keys or response bodies."""
