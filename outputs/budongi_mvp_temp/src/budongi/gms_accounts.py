"""Local personal-key attribution; never store keys, prompts or provider bodies."""
import json
import uuid
from datetime import datetime, timezone


class GMSAccounts:
    def __init__(self, connect, defaults):
        self.connect = connect
        self.defaults = defaults
        with connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS accounts(
                    id TEXT PRIMARY KEY,key_hash TEXT UNIQUE NOT NULL,policy TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS account_selection(
                    id INTEGER PRIMARY KEY CHECK(id=1),account_id TEXT REFERENCES accounts(id));
                INSERT OR IGNORE INTO account_selection VALUES(1,NULL);
                CREATE TABLE IF NOT EXISTS call_accounts(
                    id TEXT PRIMARY KEY REFERENCES calls(id),account_id TEXT NOT NULL REFERENCES accounts(id),
                    credential_id TEXT NOT NULL,owner_label TEXT NOT NULL,operation TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS account_call_idx ON call_accounts(account_id,id);
                CREATE TABLE IF NOT EXISTS call_details(
                    id TEXT PRIMARY KEY REFERENCES calls(id),completed_at TEXT,result_status TEXT,
                    usage_known INTEGER NOT NULL DEFAULT 0,rate_cost_cents INTEGER,account_delta_cents INTEGER,
                    balance_before TEXT,balance_after TEXT,counted_input_tokens INTEGER);
                CREATE TABLE IF NOT EXISTS account_balances(
                    account_id TEXT PRIMARY KEY REFERENCES accounts(id),body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS balance_events(
                    id INTEGER PRIMARY KEY,account_id TEXT NOT NULL REFERENCES accounts(id),body TEXT NOT NULL);
            ''')

    def ensure(self, db, key_hash, credential_id):
        row = db.execute('SELECT * FROM accounts WHERE key_hash=?', (key_hash,)).fetchone()
        if row is None:
            identifier = str(uuid.uuid4())
            policy = {**self.defaults, 'credential_id': credential_id}
            db.execute('INSERT OR IGNORE INTO accounts VALUES(?,?,?)', (identifier, key_hash, json.dumps(policy)))
            row = db.execute('SELECT * FROM accounts WHERE key_hash=?', (key_hash,)).fetchone()
        return row['id'], {**self.defaults, **json.loads(row['policy']), 'credential_id': credential_id}

    def activate(self, db, identifier, policy):
        body = json.dumps(policy)
        db.execute('UPDATE accounts SET policy=? WHERE id=?', (body, identifier))
        db.execute('UPDATE account_selection SET account_id=? WHERE id=1', (identifier,))
        db.execute('UPDATE policy SET revision=revision+1,body=? WHERE id=1', (body,))

    def matches(self, identifier, key_hash):
        with self.connect() as db:
            return db.execute('SELECT 1 FROM accounts WHERE id=? AND key_hash=?',
                              (identifier, key_hash)).fetchone() is not None

    @staticmethod
    def totals(db, account_id):
        where = ('id IN (SELECT id FROM call_accounts WHERE account_id=?)' if account_id is not None
                 else 'id NOT IN (SELECT id FROM call_accounts)')
        args = (account_id,) if account_id is not None else ()
        sums = db.execute("SELECT COALESCE(SUM(cost_cents),0),COALESCE(SUM(tokens),0),"
                          "COALESCE(SUM(CASE WHEN state IN ('reserved','uncertain') THEN cost_cents ELSE 0 END),0),"
                          "COUNT(*),COALESCE(SUM(CASE WHEN state='reserved' THEN 1 ELSE 0 END),0) FROM calls WHERE "
                          + where, args).fetchone()
        return dict(accounted_credits=sums[0]/100, accounted_tokens=sums[1], held_credits=sums[2]/100,
                    call_count=sums[3], active_calls=sums[4])

    def history(self, db, account_id, limit=30, offset=0):
        return [dict(row) for row in db.execute('''
            SELECT c.*,m.model,m.difficulty,m.input_rate,m.output_rate,
                   a.account_id,a.credential_id,a.owner_label,a.operation,
                   d.completed_at,d.result_status,d.usage_known,d.rate_cost_cents,d.account_delta_cents,d.counted_input_tokens
            FROM calls c JOIN call_accounts a ON a.id=c.id
            LEFT JOIN call_models m ON m.id=c.id LEFT JOIN call_details d ON d.id=c.id
            WHERE a.account_id=? ORDER BY c.created_at DESC,c.id DESC LIMIT ? OFFSET ?
        ''', (account_id, limit, offset))]

    def state(self):
        with self.connect() as db:
            db.execute('BEGIN')  # One snapshot for selected policy, account and totals.
            row = db.execute('SELECT * FROM policy WHERE id=1').fetchone()
            identifier = db.execute('SELECT account_id FROM account_selection WHERE id=1').fetchone()[0]
            legacy = self.totals(db, None)
            totals = self.totals(db, identifier) if identifier else dict.fromkeys(
                ('accounted_credits','accounted_tokens','held_credits','call_count','active_calls'), 0)
            balance = db.execute('SELECT body FROM account_balances WHERE account_id=?', (identifier,)).fetchone()
            return {'policy': {**self.defaults, **json.loads(row['body'])}, 'revision': row['revision'],
                    'account_id': identifier, **totals, 'calls': self.history(db, identifier),
                    'balance': json.loads(balance[0]) if balance else None, 'legacy_unattributed': legacy}

    def record(self, db, call_id, account_id, policy, operation, balance):
        db.execute('INSERT INTO call_accounts VALUES(?,?,?,?,?)',
                   (call_id, account_id, policy['credential_id'], policy['owner_label'], operation))
        db.execute('INSERT INTO call_details(id,balance_before) VALUES(?,?)', (call_id, json.dumps(balance)))

    def balance(self, account_id, balance):
        # Only the already-sanitized GMSClient.balance result is persisted.
        body = json.dumps(balance)
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO account_balances VALUES(?,?)', (account_id, body))
            db.execute('INSERT INTO balance_events(account_id,body) VALUES(?,?)', (account_id, body))

    def finish(self, call_id, status, *, rate_cost=None, observed=None, balance=None, usage_known=False, counted_inputs=None):
        with self.connect() as db:
            db.execute('''UPDATE call_details SET completed_at=?,result_status=?,usage_known=?,
                          rate_cost_cents=?,account_delta_cents=?,balance_after=?,counted_input_tokens=? WHERE id=?''',
                       (datetime.now(timezone.utc).isoformat(), status, int(usage_known), rate_cost, observed,
                        json.dumps(balance) if balance else None, counted_inputs, call_id))

    def disable(self, db, account_id, policy):
        policy = {**policy, 'enabled': False}
        db.execute('UPDATE accounts SET policy=? WHERE id=?', (json.dumps(policy), account_id))
        if db.execute('SELECT account_id FROM account_selection WHERE id=1').fetchone()[0] == account_id:
            db.execute('UPDATE policy SET revision=revision+1,body=? WHERE id=1', (json.dumps(policy),))
