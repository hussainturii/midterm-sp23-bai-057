pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        IMAGE = 'hussainturii/midterm-sp23-bai-057:latest'
        CONTAINER = 'midterm-sp23-bai-057'
        STUDENT_ID = 'SP23-BAI-057'
    }

    stages {
        stage('Fetch latest data') {
            steps {
                checkout scm
                sh 'git rev-parse HEAD > .git_sha'
                sh 'test -s config.json && test -s dataset/train.csv'
            }
        }

        stage('Retrain and test') {
            steps {
                sh '''#!/bin/sh
                    docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e PIP_CACHE_DIR=/tmp \\
                      -v "$WORKSPACE:/app" -w /app python:3.12-slim sh -c \\
                      'pip install --no-cache-dir -r requirements.txt && python train.py && python -m unittest discover -s tests -v'
                '''
            }
        }

        stage('Build image') {
            steps {
                script {
                    env.GIT_SHA = readFile('.git_sha').trim()
                }
                sh 'docker build --build-arg GIT_SHA="$GIT_SHA" -t "$IMAGE" .'
            }
        }

        stage('Deploy on EC2') {
            steps {
                sh '''#!/bin/sh
                    docker rm -f "$CONTAINER" 2>/dev/null || true
                    docker run -d --name "$CONTAINER" --restart unless-stopped \\
                      -p 8000:8000 "$IMAGE"
                    for attempt in 1 2 3 4 5 6; do
                      curl -fsS http://127.0.0.1:8000/health && break
                      sleep 3
                    done
                    curl -fsS http://127.0.0.1:8000/metrics
                '''
            }
        }
        stage('Verify deployed model') {
            steps {
                sh '''docker run --rm --network host -e EXPECTED_SHA="$GIT_SHA" \\
                  -v "$WORKSPACE/tests:/tests:ro" "$IMAGE" python /tests/verify_deployment.py'''
            }
        }
        stage('Publish Docker Hub image') {
            steps {
                sh 'docker push "$IMAGE"'
            }
        }
    }

    post {
        always {
            script {
                def authorEmail = sh(script: "git log -1 --format='%ae'", returnStdout: true).trim()
                emailext(
                    to: authorEmail,
                    subject: "${currentBuild.currentResult}: ${env.STUDENT_ID} #${env.BUILD_NUMBER}",
                    from: 'h0essainr@gmail.com',
                    body: "${env.STUDENT_ID} Jenkins build ${env.BUILD_NUMBER}: ${currentBuild.currentResult}. ${env.BUILD_URL}",
                    attachLog: true
                )
            }
        }
    }
}
