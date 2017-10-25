#!groovy

pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                echo 'Checkout...'
                checkout scm
            }
        }
        stage('Build') {
            steps {
                echo 'Building...'
                // add jenkins user and home to be compatible with Jenkins Docker plugin
                sh '''
                   echo RUN groupadd -o -g $(id -g) -r jenkins >> Dockerfile
                   echo RUN useradd -o -u $(id -u) --create-home -r -g  jenkins jenkins >> Dockerfile
                   '''
                sh "docker build --no-cache -t sonatanfv/son-emu:dev ."
            }
        }
        stage('Test') {
            steps {
                echo 'Testing inside Docker container ...'
                // we need to use privileged mode and host pids for the emulator
                // also need -u 0:0 (root user of container) and we need to do a manual /son-emu/utils/docker/entrypoint.sh
                // because the Jenkins Docker plugins overwrites the entrypoint specified in the Dockerfile
                withDockerContainer(image: "sonatanfv/son-emu:dev", args: "--privileged --pid='host' -v /var/run/docker.sock:/var/run/docker.sock -u 0:0 --entrypoint /son-emu/utils/docker/entrypoint.sh") {
                    sh 'echo "Tests executed inside: $(hostname)"'
                    sh 'pwd'
                    sh 'whoami'
                    sh 'cd /son-emu/; ls'
                    sh '/son-emu/utils/docker/entrypoint.sh'
                    sh 'cd /son-emu/; py.test -v src/emuvim/test/unittests'
                }
            }
        }
        stage('Package') {
            steps {
                echo 'Packaging (Docker-image)...'
                // push to public Docker registry
                sh "docker push sonatanfv/son-emu:dev"
                // might be moved to another job (:dev and :latest are the same for now)
                sh "docker tag sonatanfv/son-emu:dev sonatanfv/son-emu:latest"
                sh "docker push sonatanfv/son-emu:latest"
                // push to internal Docker registry
                sh "docker tag sonatanfv/son-emu:dev registry.sonata-nfv.eu:5000/son-emu:latest"
                sh "docker push registry.sonata-nfv.eu:5000/son-emu"        
            }
        }
    }
    post {
         success {
                 mail(from: "jenkins@sonata-nfv.eu", 
                 to: "manuel.peuster@upb.de", 
                 subject: "SUCCESS: ${env.JOB_NAME}/${env.BUILD_ID} (${env.BRANCH_NAME})",
                 body: "${env.JOB_URL}")
         }
         failure {
                  mail(from: "jenkins@sonata-nfv.eu", 
                 to: "manuel.peuster@upb.de", 
                 subject: "FAILURE: ${env.JOB_NAME}/${env.BUILD_ID} (${env.BRANCH_NAME})",
                 body: "${env.JOB_URL}")
         }
    }
}
