import sqlite3
conn = sqlite3.connect('instance/contracts.db')
conn.execute('ALTER TABLE tenant_customer ADD COLUMN trial_expires_at DATETIME')
conn.commit()
conn.close()
print('done')
