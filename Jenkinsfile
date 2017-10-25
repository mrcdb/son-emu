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
                script {
                    echo 'Testing inside Docker container ...'
                    mdg = "vim-emu1"
                    docker_args = ""
                    if(mdg == "vim-emu") {
                        // we need to use privileged mode and host pids for the emulator
                        // also need -u 0:0 (root user inside container)
                        docker_args = "--privileged --pid='host' -v /var/run/docker.sock:/var/run/docker.sock -u 0:0"
                    }
                    withDockerContainer(image: "sonatanfv/son-emu:dev", args: docker_args) {
                        sh 'devops-stages/stage-test.sh'
                    }
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
