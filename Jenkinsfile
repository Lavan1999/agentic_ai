pipeline {
    agent any

    environment {
        PROJECT_DIR = "/var/www/html/ai-agent"
        SONARQUBE_TOKEN = credentials('sonarqube')
    }

    stages {
        stage('Fix Initial Permissions') {
            steps {
                script {
                    sh '''
                    sudo chmod -R 777 ${PROJECT_DIR} || true
                    sudo chown -R ubuntu:www-data ${PROJECT_DIR} || true
                    '''
                }
            }
        }
        stage('Fetch Latest Changes') {
            steps {
                script {
                    echo "Fetching latest changes from GitHub..."
                    withCredentials([usernamePassword(credentialsId: 'git_credentials', 
                        usernameVariable: 'GIT_USERNAME', passwordVariable: 'GIT_PASSWORD')]) {
                        
                        sh """
                            cd ${PROJECT_DIR}
                            git config --global --add safe.directory ${PROJECT_DIR}
                            git remote add origin https://\${GIT_USERNAME}:\${GIT_PASSWORD}@github.com/finloge/AI-agents.git || true
                            git remote set-url origin https://\${GIT_USERNAME}:\${GIT_PASSWORD}@github.com/finloge/AI-agents.git
                            git fetch origin
                            git reset --hard origin/dev-main
                        """
                    }
                }
            }
        }

        stage('Run Deployment Scripts') {
            steps {
                script {
                    echo "Running deployment scripts..."
                    sh """
                        cd ${PROJECT_DIR}
                        for script in env.sh nginx.sh; do 
                          if [ -f "./\$script" ]; then 
                            echo "Running \$script..."
                            bash ./\$script || { echo "\$script execution failed! Exiting."; exit 1; }
                          else 
                            echo "\$script not found! Exiting."
                            exit 1
                          fi
                        done
                    """
                }
            }
        }

        stage('Restart Services') {
            steps {
                script {
                    echo "Restarting Nginx and Supervisor..."
                    sh "sudo systemctl restart nginx || echo 'Failed to restart Nginx'"
                    sh "sudo systemctl restart supervisor || echo 'Failed to restart Supervisor'"
                }
            }
        }
        stage('SonarQube Analysis') {
            steps {
                script {
                    def scannerHome = tool 'SonarQube Scanner'
                    withSonarQubeEnv('SonarQube Server') {
                        sh(script: """
                        ${scannerHome}/bin/sonar-scanner -Dsonar.projectKey=ai-agent \
                        -Dsonar.sources=. -Dsonar.host.url=http://209.38.123.111:9000 -Dsonar.login=${SONARQUBE_TOKEN} 2>&1
                        """)
                        // SonarQube logs are not appended to currentBuild.description
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                sh '''
                sudo chmod -R 777 ${PROJECT_DIR} || true
                sudo chown -R ubuntu:www-data ${PROJECT_DIR} || true
                '''
            }
            script {
                def jobName = env.JOB_NAME
                def buildNumber = env.BUILD_NUMBER
                def pipelineStatus = currentBuild.result ?: 'SUCCESS'
                def bannerColor = pipelineStatus.toUpperCase() == 'SUCCESS' ? 'green' : 'red'

                // Capture the final log output from currentBuild.description excluding SonarQube logs
                def finalLog = currentBuild.description ?: "No logs available."

                // Email body with styled log
                def body = """
                    <html>
                        <body>
                            <div style="border: 4px solid ${bannerColor}; padding: 10px;">
                                <h2>${jobName} - Build ${buildNumber}</h2>
                                <div style="background-color: ${bannerColor}; padding: 10px;">
                                    <h3 style="color: white;">Pipeline Status: ${pipelineStatus.toUpperCase()}</h3>
                                </div>
                                <p>Please find the build log details below:</p>
                                <pre style="background-color: black; color: white; padding: 10px; border-radius: 5px; font-family: 'Courier New', Courier, monospace; font-size: 14px;">${finalLog}</pre>
                            </div>
                        </body>
                    </html>
                """

                emailext(
                    subject: "${jobName} - Build ${buildNumber} - ${pipelineStatus.toUpperCase()}",
                    body: body,
                    to: 'soumyarout567@gmail.com',
                    from: 'soumyajit.rout@finloge.com',
                    replyTo: 'soumyajit.rout@finloge.com',
                    mimeType: 'text/html'
                )
            }
        }
        failure {
            echo "Pipeline execution failed!"
        }
    }
}