# Automated ML Retraining Pipeline - SP23-BAI-057

This repository implements the CSC418 lab-midterm deployment pipeline for
`SP23-BAI-057`. The committed `config.json` and `dataset/train.csv` are the
student-specific inputs. A GitHub data push triggers Jenkins to retrain the
model, run API tests, build and publish a Docker image, and redeploy FastAPI
on EC2.

## API

After deployment, the service listens on port 8000.

```text
GET  /health
GET  /metrics
POST /predict
```

`GET /metrics` returns `student_id`, `accuracy`, `training_rows`,
`model_version`, and `git_sha`.

Example prediction request:

```json
{
  "records": [{
    "soil_deficit": 0.2,
    "heat_stress": 0.4,
    "flow_variance": -0.1,
    "pump_age": 1.1
  }]
}
```

## Local verification

```bash
python generate_dataset.py --config config.json --output dataset/train.csv --rows 300
python train.py
uvicorn app:app --host 0.0.0.0 --port 8000
```

The Dockerfile trains the model during every image build. Jenkins passes the
current Git commit SHA into the image so `/metrics` identifies the deployed
revision.
