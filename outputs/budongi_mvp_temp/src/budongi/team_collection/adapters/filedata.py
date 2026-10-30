from __future__ import annotations

import re

from budongi.team_collection import contract as C

_SEOUL_INF_ID_RE = re.compile(r"^OA-[0-9]{1,6}$")
_DATAGOKR_FILE_ID_RE = re.compile(r"^FILE_[0-9A-Za-z_]+$")
_PUBLIC_DATA_PK_RE = re.compile(r"^[0-9A-Za-z_-]+$")
_DATAGOKR_DETAIL_RE = re.compile(
    r"fn_fileDataDown\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'(FILE_[0-9A-Za-z_]+)'\s*,\s*'([0-9]+)'\s*,\s*'([^']*)'\s*\)"
)


def _sequence_str(value: int | str) -> str:
    """Validate and format a sequence parameter value."""
    if isinstance(value, bool):
        raise C.ContractError("invalid_file_param")
    if isinstance(value, int):
        if value < 0:
            raise C.ContractError("invalid_file_param")
        return str(value)
    if isinstance(value, str):
        if not re.fullmatch(r"[0-9]+", value):
            raise C.ContractError("invalid_file_param")
        return str(int(value))
    raise C.ContractError("invalid_file_param")


def seoul_file_url(inf_id: str, *, inf_seq: int | str, seq: int | str) -> str:
    """Build the verified datafile.seoul.go.kr nio_download GET URL."""
    if not isinstance(inf_id, str) or not _SEOUL_INF_ID_RE.fullmatch(inf_id):
        raise C.ContractError("invalid_dataset_id")
    inf_seq_str = _sequence_str(inf_seq)
    seq_str = _sequence_str(seq)
    return (
        f"https://datafile.seoul.go.kr/bigfile/iot/inf/nio_download.do"
        f"?&useCache=false&infId={inf_id}&seqNo=&seq={seq_str}&infSeq={inf_seq_str}"
    )


def datagokr_detail_downloads(html: str) -> tuple[dict, ...]:
    """Extract attachment download identifiers from a data.go.kr HTML fragment."""
    if not isinstance(html, str):
        raise C.ContractError("invalid_payload")
    seen: set[tuple[str, str]] = set()
    downloads: list[dict] = []
    for match in _DATAGOKR_DETAIL_RE.finditer(html):
        atch_file_id = match.group(3)
        file_detail_sn = match.group(4)
        ext = match.group(5).lower()
        key = (atch_file_id, file_detail_sn)
        if key not in seen:
            seen.add(key)
            downloads.append(
                {
                    "atch_file_id": atch_file_id,
                    "file_detail_sn": file_detail_sn,
                    "ext": ext,
                }
            )
    return tuple(downloads)


def datagokr_file_url(atch_file_id: str, file_detail_sn: int | str) -> str:
    """Build the verified www.data.go.kr fileDownload.do GET URL."""
    if not isinstance(atch_file_id, str) or not _DATAGOKR_FILE_ID_RE.fullmatch(atch_file_id):
        raise C.ContractError("invalid_file_id")
    sn = _sequence_str(file_detail_sn)
    return f"https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId={atch_file_id}&fileDetailSn={sn}&insertDataPrcus=N"


def standard_page_params(
    column_doc: dict,
    *,
    public_data_pk: str,
    per_page: int = 10000,
) -> tuple[tuple[tuple[str, str], ...], ...]:
    """Build per-page parameter tuples for standard-dataset grid download."""
    if not isinstance(column_doc, dict):
        raise C.ContractError("invalid_column_doc")
    if not isinstance(public_data_pk, str) or not _PUBLIC_DATA_PK_RE.fullmatch(public_data_pk):
        raise C.ContractError("invalid_file_param")
    if isinstance(per_page, bool) or not isinstance(per_page, int) or per_page < 1 or per_page > 10000:
        raise C.ContractError("invalid_file_param")

    if "totalCount" not in column_doc:
        raise C.ContractError("invalid_column_doc")
    total_count = column_doc["totalCount"]
    if isinstance(total_count, bool) or not isinstance(total_count, int) or total_count < 0:
        raise C.ContractError("invalid_column_doc")

    if "tableVO" not in column_doc:
        raise C.ContractError("invalid_column_doc")
    table_vo = column_doc["tableVO"]
    if not isinstance(table_vo, dict):
        raise C.ContractError("invalid_column_doc")

    if "svcTableNm" not in table_vo:
        raise C.ContractError("invalid_column_doc")
    svc_table_nm = table_vo["svcTableNm"]
    if not isinstance(svc_table_nm, str) or len(svc_table_nm) == 0:
        raise C.ContractError("invalid_column_doc")

    if "colNmList" not in table_vo:
        raise C.ContractError("invalid_column_doc")
    col_nm_list = table_vo["colNmList"]
    if not isinstance(col_nm_list, list) or len(col_nm_list) == 0:
        raise C.ContractError("invalid_column_doc")
    for col in col_nm_list:
        if not isinstance(col, str) or len(col) == 0:
            raise C.ContractError("invalid_column_doc")

    if "limit" not in table_vo:
        raise C.ContractError("invalid_column_doc")
    limit = table_vo["limit"]
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise C.ContractError("invalid_column_doc")

    if total_count > limit:
        raise C.ContractError("standard_over_grid_limit")

    if total_count == 0:
        return ()

    num_pages = (total_count + per_page - 1) // per_page
    base_prefix = (("publicDataPk", public_data_pk),) + tuple(("colNmList", col) for col in col_nm_list)
    base_suffix = (
        ("totalCount", str(total_count)),
        ("svcTableNm", svc_table_nm),
        ("perPage", str(per_page)),
    )

    pages = []
    for page_num in range(1, num_pages + 1):
        pages.append(base_prefix + base_suffix + (("page", str(page_num)),))
    return tuple(pages)


def kric_file_url(dataset_id: int | str, operation: int | str) -> str:
    """Build the verified data.kric.go.kr download.file GET URL."""
    ds_id = _sequence_str(dataset_id)
    op = _sequence_str(operation)
    return f"https://data.kric.go.kr/rips/dataset/download.file?type=filedata&id={ds_id}&operation={op}"
