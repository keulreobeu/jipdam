"""Read-only input gates for real rental verification; never invent approval."""
from contextlib import closing
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit
from .canonical_rental import (DEFAULT_CANONICAL_DB, DEFAULT_RENTAL_SERVING_DB,
    open_canonical_reader, open_rental_serving_reader, canonical_rental_status)
from .rental_review import file_sha256, load_review_package
from .rental_recommendation import RentalDataUnavailable


def rental_readiness(*, canonical_db=DEFAULT_CANONICAL_DB, database=DEFAULT_RENTAL_SERVING_DB,
                     review_package=None, model=None, endpoint='http://127.0.0.1:11434/v1/chat/completions'):
    gates = []
    def gate(part, purpose, status, reason):
        gates.append({'part': part, 'purpose': purpose, 'status': status, 'reason': reason})
    source_hash = None
    try:
        with closing(open_canonical_reader(canonical_db)) as source:
            version = source.execute('PRAGMA user_version').fetchone()[0]
        source_hash = file_sha256(Path(canonical_db))
        gate(1, '첫 실행과 원본 불변 조회', 'ready', f'canonical v{version} 읽기 가능')
    except (OSError, RentalDataUnavailable):
        gate(1, '첫 실행과 원본 불변 조회', 'blocked', 'canonical 파일·스키마를 확인하세요.')
    if review_package is None:
        gate(2, '승인된 검수 자료 반영', 'needs_input', '이미 승인된 검수 패키지 경로가 필요합니다.')
    elif source_hash is None:
        gate(2, '승인된 검수 자료 반영', 'blocked', '패키지 대사에 필요한 원본 DB가 없습니다.')
    else:
        try:
            load_review_package(Path(review_package), source_hash)
            gate(2, '승인된 검수 자료 반영', 'validated', '패키지 검증 통과; prepare-rentals에 명시해 반영하세요.')
        except (OSError, RentalDataUnavailable, ValueError):
            gate(2, '승인된 검수 자료 반영', 'blocked', '패키지 승인·원본 해시·계보를 확인하세요.')
    state = None
    reviewed_status_counts = {}
    try:
        with closing(open_rental_serving_reader(database)) as serving:
            state = canonical_rental_status(serving)
            metadata = dict(serving.execute('SELECT key,value FROM metadata'))
            reviewed_status_counts = {row['source_status']: row['count'] for row in serving.execute(
                'SELECT o.source_status,COUNT(*) AS count FROM rental_observations o '
                'JOIN reviewed_relations r ON r.observation_id=o.observation_id GROUP BY o.source_status')}
        if source_hash is None or metadata['source_db_sha256'] != source_hash:
            gate(3, '실제 추천·상세 성능 검증', 'blocked', '현재 canonical로 prepare-rentals를 다시 실행하세요.')
        elif (state['status'] != 'ready' or not all(state[field] for field in
              ('coordinates_available', 'facility_data_available', 'coverage_available'))):
            gate(3, '실제 추천·상세 성능 검증', 'needs_input', '확정 관계·좌표·시설·커버리지 반영 후 실제 후보 ID로 계측하세요.')
        else:
            gate(3, '실제 추천·상세 성능 검증', 'ready', '실제 후보를 선택해 추천/상세 benchmark와 내용을 검증하세요.')
    except (OSError, RentalDataUnavailable, sqlite3.Error, ValueError, KeyError, TypeError):
        state = None
        reviewed_status_counts = {}
        gate(3, '실제 추천·상세 성능 검증', 'blocked', 'serving 파일·스키마를 확인하세요.')
    unresolved_status_count = sum(count for status, count in reviewed_status_counts.items()
                                  if status not in ('valid', 'cancelled'))
    if state is not None and sum(reviewed_status_counts.values()) != state['confirmed_complex_observations']:
        gate(3, '확정 연결 거래의 취소·정정 상태', 'blocked', '확정 관계와 상태 집계 건수가 다릅니다. serving을 검증하세요.')
    elif unresolved_status_count:
        gate(3, '확정 연결 거래의 취소·정정 상태', 'needs_input',
             f'확정 연결 관측 {unresolved_status_count:,}건의 상태가 valid로 확인되지 않았습니다.')
    elif state is not None and state['status'] == 'ready':
        gate(3, '확정 연결 거래의 취소·정정 상태', 'ready', '확정 연결 관측의 상태가 valid 또는 cancelled로 검수됐습니다.')
    else:
        gate(3, '확정 연결 거래의 취소·정정 상태', 'blocked', '읽을 수 있는 확정 연결 serving이 필요합니다.')
    try:
        parsed = urlsplit(endpoint)
        valid_endpoint = (parsed.scheme == 'http' and parsed.hostname in ('127.0.0.1','localhost','::1')
                          and not (parsed.username or parsed.password or parsed.query or parsed.fragment)
                          and parsed.path == '/v1/chat/completions' and (parsed.port is None or 1 <= parsed.port <= 65535))
    except (ValueError, TypeError):
        valid_endpoint = False
    if not valid_endpoint:
        gate(3, '지정 로컬 모델 질문 검증', 'blocked', '인증정보 없는 loopback chat/completions HTTP 주소가 필요합니다.')
    elif not isinstance(model, str) or not model.strip():
        gate(3, '지정 로컬 모델 질문 검증', 'needs_input', '사용자가 지정한 설치 모델명이 필요합니다. 모델을 자동 설치하지 않습니다.')
    else:
        gate(3, '지정 로컬 모델 질문 검증', 'configured', '설정만 확인됨; rental-mvp에서 누락·단위·수정·복구를 실제 검증하세요.')
    status = 'blocked' if any(g['status'] == 'blocked' for g in gates) else 'needs_input' if any(
        g['status'] == 'needs_input' for g in gates) else 'configured'
    return {'status': status, 'gates': gates, 'serving': state, 'real_validation_complete': False}
