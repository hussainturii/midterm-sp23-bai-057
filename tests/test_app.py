import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import joblib
import pandas as pd
from fastapi.testclient import TestClient
from sklearn.dummy import DummyClassifier

import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        artifacts = self.root / 'artifacts'
        artifacts.mkdir()
        model = DummyClassifier(strategy='constant', constant=1).fit([[0, 0, 0, 0]], [1])
        joblib.dump({'model': model, 'features': ['soil_deficit', 'heat_stress', 'flow_variance', 'pump_age']}, artifacts / 'model.joblib')
        (artifacts / 'metrics.json').write_text(json.dumps({
            'student_id': 'SP23-BAI-057', 'accuracy': 0.9, 'training_rows': 300,
            'model_version': 'abc123', 'dataset_sha256': 'abc123', 'git_sha': 'deadbeef'
        }))
        self.path_patch = patch.object(app, 'Path', side_effect=lambda value: self.root / value)
        self.path_patch.start()
        self.client = TestClient(app.app)

    def tearDown(self):
        self.path_patch.stop()
        self.temp.cleanup()

    def test_metrics_has_required_contract(self):
        response = self.client.get('/metrics')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), {'student_id', 'accuracy', 'training_rows', 'model_version', 'dataset_sha256', 'git_sha'})
        self.assertEqual(response.json()['student_id'], 'SP23-BAI-057')

    def test_predict_accepts_records(self):
        response = self.client.post('/predict', json={'records': [{
            'soil_deficit': 0.2, 'heat_stress': 0.4,
            'flow_variance': -0.1, 'pump_age': 1.1
        }]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['predictions'], [1])

    def test_predict_rejects_empty_records(self):
        self.assertEqual(self.client.post('/predict', json={'records': []}).status_code, 422)


if __name__ == '__main__':
    unittest.main()
