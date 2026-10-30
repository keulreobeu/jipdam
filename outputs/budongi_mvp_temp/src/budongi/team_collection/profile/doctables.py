from __future__ import annotations

from html.parser import HTMLParser

from budongi.team_collection import contract as C


class _Table:
    """Internal representation of a single extracted table."""

    def __init__(self) -> None:
        self.rows: list[list[str]] = []
        self.current_row: list[str] | None = None
        self.current_cell_chunks: list[str] | None = None

    def close_cell(self) -> None:
        if self.current_cell_chunks is not None:
            text = " ".join("".join(self.current_cell_chunks).split())
            if self.current_row is None:
                self.current_row = []
            self.current_row.append(text)
            self.current_cell_chunks = None

    def close_row(self) -> None:
        self.close_cell()
        if self.current_row is not None:
            if len(self.current_row) > 0:
                self.rows.append(self.current_row)
            self.current_row = None

    def start_row(self) -> None:
        self.close_row()
        self.current_row = []

    def start_cell(self) -> None:
        self.close_cell()
        if self.current_row is None:
            self.current_row = []
        self.current_cell_chunks = []


class _DocTableParser(HTMLParser):
    """Parser to extract tables from HTML documents."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.all_tables: list[_Table] = []
        self._table_stack: list[_Table] = []
        self._ignored_depth: int = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_name = tag.lower()
        if tag_name in ("script", "style"):
            self._ignored_depth += 1
            return
        if self._ignored_depth > 0:
            return

        if tag_name == "table":
            table = _Table()
            self.all_tables.append(table)
            self._table_stack.append(table)
        elif tag_name == "tr":
            if self._table_stack:
                self._table_stack[-1].start_row()
        elif tag_name in ("td", "th"):
            if self._table_stack:
                self._table_stack[-1].start_cell()
        elif tag_name == "br":
            if self._table_stack:
                active_table = self._table_stack[-1]
                if active_table.current_cell_chunks is not None:
                    active_table.current_cell_chunks.append(" ")

    def handle_endtag(self, tag: str) -> None:
        tag_name = tag.lower()
        if tag_name in ("script", "style"):
            if self._ignored_depth > 0:
                self._ignored_depth -= 1
            return
        if self._ignored_depth > 0:
            return

        if tag_name == "table":
            if self._table_stack:
                table = self._table_stack.pop()
                table.close_row()
        elif tag_name == "tr":
            if self._table_stack:
                self._table_stack[-1].close_row()
        elif tag_name in ("td", "th"):
            if self._table_stack:
                self._table_stack[-1].close_cell()

    def handle_data(self, data: str) -> None:
        if self._ignored_depth > 0:
            return
        if self._table_stack:
            active_table = self._table_stack[-1]
            if active_table.current_cell_chunks is not None:
                active_table.current_cell_chunks.append(data)

    def close(self) -> None:
        super().close()
        while self._table_stack:
            table = self._table_stack.pop()
            table.close_row()


def extract_tables(html: str) -> list[list[list[str]]]:
    """Extract every table in HTML as a list of rows with whitespace-collapsed cells."""
    if not isinstance(html, str):
        raise C.ContractError("invalid_html")
    parser = _DocTableParser()
    parser.feed(html)
    parser.close()
    return [table.rows for table in parser.all_tables]


def _validate_tables(tables: object) -> None:
    if not isinstance(tables, (list, tuple)):
        raise C.ContractError("invalid_tables")
    for table in tables:
        if not isinstance(table, (list, tuple)):
            raise C.ContractError("invalid_tables")
        for row in table:
            if not isinstance(row, (list, tuple)):
                raise C.ContractError("invalid_tables")
            for cell in row:
                if not isinstance(cell, str):
                    raise C.ContractError("invalid_tables")


def _validate_headers(headers: object) -> None:
    if not isinstance(headers, (list, tuple)):
        raise C.ContractError("invalid_headers")
    if len(headers) == 0:
        raise C.ContractError("invalid_headers")
    for item in headers:
        if not isinstance(item, str):
            raise C.ContractError("invalid_headers")


def _find_column(
    header_row: list[str] | tuple[str, ...],
    candidates: tuple[str, ...] | list[str],
    *,
    ignore_idx: int | None = None,
) -> int | None:
    stripped_header = [cell.strip() for cell in header_row]
    for candidate in candidates:
        cand_clean = candidate.strip()
        for idx, cell_text in enumerate(stripped_header):
            if ignore_idx is not None and idx == ignore_idx:
                continue
            if cell_text == cand_clean or cell_text == candidate:
                return idx
    return None


def column_definitions(
    tables: list,
    *,
    name_headers: tuple = ("출력명", "항목명", "컬럼명", "필드명", "출력값"),
    label_headers: tuple = ("출력설명", "항목설명", "설명", "한글명", "항목명(국문)"),
) -> dict[str, str]:
    """Return a name to label mapping from the first matching output-definition table."""
    _validate_tables(tables)
    _validate_headers(name_headers)
    _validate_headers(label_headers)

    name_headers_set = set(name_headers) | {h.strip() for h in name_headers}

    for table in tables:
        if len(table) == 0:
            continue
        header_row = table[0]
        name_idx = _find_column(header_row, name_headers)
        if name_idx is None:
            continue
        label_idx = _find_column(header_row, label_headers, ignore_idx=name_idx)
        if label_idx is None:
            continue

        min_len = max(name_idx, label_idx) + 1
        result: dict[str, str] = {}
        for row in table[1:]:
            if len(row) < min_len:
                continue
            name_val = row[name_idx].strip()
            if not name_val or name_val in name_headers_set:
                continue
            label_val = row[label_idx].strip()
            if name_val not in result:
                result[name_val] = label_val
        return result

    return {}
