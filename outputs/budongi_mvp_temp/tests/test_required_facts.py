"""Public evaluate() evidence for the EVAL-001 baseline acceptance criteria."""
import csv
import json
from pathlib import Path
import tempfile
import unittest

from budongi.eval import evaluate


class RequiredFactContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def fact(self, value, **extra):
        return {'entity': 'APT_A', 'field': 'fact', 'value': value, **extra}

    def run_cases(self, cases):
        gold, run, report = (self.root / name for name in ('gold.jsonl', 'run.jsonl', 'report.csv'))
        golden, predictions = [], []
        for index, (facts, answer) in enumerate(cases):
            golden.append({'id': f'q{index}', 'task_type': 'FACT', 'required_facts': facts})
            if answer is not None:
                predictions.append({'question_id': f'q{index}', 'answer': answer})
        gold.write_text(''.join(json.dumps(item, ensure_ascii=False) + '\n' for item in golden), encoding='utf-8')
        run.write_text(''.join(json.dumps(item, ensure_ascii=False) + '\n' for item in predictions), encoding='utf-8')
        result = evaluate(gold, run, report)
        with report.open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream))
        return result, rows

    def test_units_money_and_tolerance_boundaries(self):
        cases = [
            ([self.fact(900000000, unit='원')], 'APT_A 가격은 9억원입니다.'),
            ([self.fact(90000, unit='만원')], 'APT_A 가격은 900,000,000원 입니다.'),
            ([self.fact(84, unit='㎡')], 'APT_A 면적은 84제곱미터입니다.'),
            ([self.fact(350, unit='m', tolerance=10)], 'APT_A 거리는 340미터입니다.'),
            ([self.fact(350, unit='m', tolerance=10)], 'APT_A 거리는 360m입니다.'),
            ([self.fact(350, unit='m', tolerance=10)], 'APT_A 거리는 360.1m입니다.'),
            ([self.fact(90000, unit='만원')], 'APT_A 가격은 900,000,000원입니다.'),
        ]
        result, rows = self.run_cases(cases)
        self.assertEqual([row['required_fact_status'] for row in rows], ['passed'] * 5 + ['failed', 'failed'])
        self.assertEqual(result['required_fact_coverage']['matched_facts'], 5)
        self.assertEqual(result['required_fact_coverage']['missing_facts'], 2)

    def test_text_and_date_normalization(self):
        cases = [
            ([self.fact('Green   Park')], 'APT_A 이름은 GREEN park 입니다.'),
            ([self.fact('2023-01-10')], 'APT_A 계약일은 2023년 1월 10일입니다.'),
            ([self.fact('2023-01-10')], 'APT_A 계약일은 2023.1.10 입니다.'),
            ([self.fact('2023-01-10')], 'APT_A 계약일은 2023-01-11입니다.'),
            ([self.fact('2023-02-30')], 'APT_A 계약일은 2023-02-28입니다.'),
        ]
        _, rows = self.run_cases(cases)
        self.assertEqual([row['required_fact_status'] for row in rows],
                         ['passed', 'passed', 'passed', 'failed', 'not_measured'])

    def test_entity_context_and_aliases(self):
        cases = [
            ([self.fact(350, unit='m')], 'APT_A 거리는 350m입니다.'),
            ([self.fact(350, unit='m', entity_aliases=['집담아파트'])], '집담아파트 거리는 350m입니다.'),
            ([self.fact(350, unit='m')], 'APT_B 거리는 350m입니다.'),
            ([self.fact(350, unit='m')], 'APT_AB 거리는 350m입니다.'),
            ([self.fact(350, unit='m')], 'APT_A 정보입니다. APT_B 거리는 350m입니다.'),
        ]
        _, rows = self.run_cases(cases)
        self.assertEqual([row['required_fact_status'] for row in rows], ['passed', 'passed', 'failed', 'failed', 'failed'])

    def test_invalid_and_absent_facts_remain_unmeasured(self):
        invalid = [self.fact(None), self.fact(True), self.fact({'unknown': 1}), self.fact(350),
                   self.fact(350, unit='km'), self.fact(350, unit='m', tolerance=-1),
                   self.fact(350, unit='m', entity_aliases=[]), self.fact(350, unit='m', entity_aliases='APT_A')]
        cases = [(invalid, 'APT_A 거리는 350m입니다.'), ([], 'APT_A 정보입니다.'),
                 (None, 'APT_A 정보입니다.'), ([self.fact(350, unit='m')], None),
                 ([self.fact(350, unit='m'), self.fact(None)], 'APT_A 정보입니다.')]
        result, rows = self.run_cases(cases)
        self.assertEqual([row['required_fact_status'] for row in rows], ['not_measured'] * 4 + ['failed'])
        self.assertEqual(result['required_fact_coverage']['matched_facts'], 0)
        self.assertEqual(result['required_fact_coverage']['not_measured_facts'], len(invalid) + 2)
        self.assertEqual(result['required_fact_coverage']['missing_facts'], 1)

    def test_reports_preserve_status_counts_and_fact_evidence(self):
        fact = self.fact(350, unit='m', tolerance=10, entity_aliases=['집담아파트'])
        cases = [([fact], '집담아파트 거리는 355미터입니다.'),
                 ([fact], '집담아파트 거리는 400미터입니다.'),
                 ([self.fact(350, unit='km')], 'APT_A 거리는 350km입니다.')]
        result, rows = self.run_cases(cases)
        coverage = result['required_fact_coverage']
        self.assertEqual((coverage['matched_facts'], coverage['missing_facts'], coverage['not_measured_facts']), (1, 1, 1))
        self.assertEqual(coverage['coverage_rate'], 0.5)
        details = json.loads(rows[0]['required_fact_details'])[0]
        for key, value in fact.items():
            self.assertEqual(details[key], value)
        self.assertEqual(json.loads(rows[2]['required_fact_details'])[0]['reason'], 'unsupported_unit')
        before = (self.root / 'report.csv').read_bytes()
        again = evaluate(self.root / 'gold.jsonl', self.root / 'run.jsonl', self.root / 'report.csv')
        self.assertEqual(again, result)
        self.assertEqual((self.root / 'report.csv').read_bytes(), before)
        only_unmeasured, _ = self.run_cases([([self.fact(None)], 'APT_A 정보입니다.')])
        self.assertIsNone(only_unmeasured['required_fact_coverage']['coverage_rate'])

    def test_existing_metrics_and_unmeasured_generation_are_preserved(self):
        gold, run, report = (self.root / name for name in ('gold.jsonl', 'run.jsonl', 'report.csv'))
        call = {'tool': 'search_apartments', 'arguments': {'district': '강서구'}}
        gold.write_text(json.dumps({'id': 'q1', 'expected_tool_calls': [call], 'expected_entities': ['APT_A'],
                                    'required_facts': [self.fact(350, unit='m')]}) + '\n', encoding='utf-8')
        run.write_text(json.dumps({'question_id': 'q1', 'tool_calls': [{**call, 'returned_ids': ['APT_A']}],
                                   'answer': 'APT_A 거리는 350m입니다.', 'grounding_check': {'status': 'passed'}})
                       + '\n', encoding='utf-8')
        result = evaluate(gold, run, report)
        for key in ('tool_selection_accuracy', 'argument_exact_accuracy', 'entity_precision_mean', 'entity_recall_mean'):
            self.assertEqual(result[key], 1.0)
        self.assertEqual(result['answer_grounding']['pass_rate'], 1.0)
        self.assertEqual(result['generation'], 'required_fact_coverage_measured_full_claim_precision_pending')
        with report.open(encoding='utf-8-sig', newline='') as stream:
            self.assertEqual(next(csv.DictReader(stream))['generation_check'], 'full_claim_precision_pending')
