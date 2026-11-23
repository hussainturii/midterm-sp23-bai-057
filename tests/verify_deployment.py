"""Compare the deployed metrics with this checkout and an independent refit."""
import hashlib
import json
import os
import time
import urllib.request
from pathlib import Path

import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

config = json.loads(Path('config.json').read_text())
data = pd.read_csv('dataset/train.csv')
digest = hashlib.sha256(Path('dataset/train.csv').read_bytes()).hexdigest()
x = data[config['features']].apply(pd.to_numeric, errors='coerce')
y = data['label'].astype(int)
xt, xv, yt, yv = train_test_split(x, y, test_size=.25,
    random_state=int(config['seed']), stratify=y)
model = make_pipeline(SimpleImputer(strategy='median'), StandardScaler(),
    LogisticRegression(max_iter=700, random_state=int(config['seed'])))
model.fit(xt, yt)
expected = dict(student_id=config['student_id'], training_rows=len(data),
    dataset_sha256=digest, model_version=digest[:12],
    git_sha=os.environ['EXPECTED_SHA'],
    accuracy=round(float(accuracy_score(yv, model.predict(xv))), 6))
url = os.environ.get('METRICS_URL', 'http://127.0.0.1:8000/metrics')
for attempt in range(30):
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            actual = json.load(response)
        assert actual == expected, (actual, expected)
        print(json.dumps({'verified': True, 'metrics': actual}, indent=2))
        break
    except Exception:
        if attempt == 29:
            raise
        time.sleep(2)
