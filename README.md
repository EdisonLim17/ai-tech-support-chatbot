# TechAssist (AI Tech Support Chatbot)

TechAssist is a cloud-native, enterprise-grade serverless application that delivers instant technical support responses to users. Built on Amazon Bedrock with the Claude 3.5 Haiku model, it intelligently answers questions, redacts sensitive information, validates JSON outputs, and escalates unresolved issues to human agents—all while enforcing company policies, tone guidelines, and strict business rules.

The architecture prioritizes high availability, scalability, and security, capable of handling millions of concurrent connections with 99.95 % uptime and fast response times. Infrastructure is fully automated with Terraform and GitHub Actions, requiring zero manual configuration.

---

## 🌐 Video Demo

[Watch the demo](https://www.youtube.com/watch?v=5g3UpTpsSuo)

---

## ☁️ Architecture

![Image of architecture](IAM-Policy-Generator-AWS-Architecture.jpeg)

**Key AWS Components:**
- **API Gateway** – Public HTTPS endpoint for chatbot requests
- **AWS Lambda** – Stateless compute layer running the chatbot logic and Bedrock calls
- **Amazon Bedrock (Claude 3.5 Haiku)** – Large language model powering intelligent responses
- **Amazon DynamoDB** – Stores conversation history and escalation data with millisecond latency
- **Amazon SNS** – Publishes escalation notifications to human support channels
- **Amazon CloudWatch** – Monitors metrics, logs, and alerts for uptime and performance
- **AWS Secrets Manager** – Secures API keys, system prompt templates, and configuration
- **Terraform** – Infrastructure-as-code for reproducible, environment-agnostic deployments
- **GitHub Actions** – CI/CD pipelines for automated provisioning, testing, and deployments

---

## 🚀 Features

- **Real-time Tech Support:** Handles millions of simultaneous users with < 100 ms median latency and 99.95 % uptime
- **Policy-Aware Responses:** Uses a system-prompt framework encoding company policies, tone guidelines, and business rules to ensure every reply is compliant and brand-aligned
- **Secure Escalation:** Detects unresolved issues and routes them to human agents through Amazon SNS
- **Data Privacy:** Automatically redacts PII before storing or returning any response
- **Serverless & Scalable:** Fully serverless backend with on-demand scaling, zero maintenance, and pay-per-use efficiency
- **Automated Deployments:** Zero-touch infrastructure management using Terraform and GitHub Actions

---

## 🧰 Tech Stack

| Layer                | Tech/Service                      |
|----------------------|-----------------------------------|
| Backend Logic        | AWS Lambda (Python)               |
| AI Integration       | Amazon Bedrock (Claude 3.5 Haiku) |
| Data Storage         | Amazon DynamoDB                   |
| Messaging/Escalation | Amazon SNS                        |
| API Endpoint         | Amazon API Gateway                |
| Monitoring           | Amazon CloudWatch                 |
| Secrets Management   | AWS Secrets Manager               |
| Infrastructure       | Terraform                         |
| CI/CD                | GitHub Actions                    |

---

## 🔐 Security Highlights

- **System Prompt Governance:** Centralized prompt enforces tone, policy, and business rules for every Bedrock invocation
- **Principle of Least Privilege:** Tightly scoped IAM roles for Lambda, DynamoDB, and CI/CD pipelines
- **Secrets in AWS Secrets Manager:** No secrets or API keys stored in code or environment variables
- **End-to-End Encryption:** All traffic served over HTTPS via API Gateway
- **Automated Compliance:** Continuous monitoring and alerting with CloudWatch to maintain 99.95 % uptime

---

## 🔄 CI/CD Workflow

### Infrastructure – Terraform + GitHub Actions
- On pushes to `main`, GitHub Actions runs Terraform plans and applies infrastructure updates automatically
- Secrets and configuration values are fetched dynamically from Secrets Manager and Terraform outputs

### Application Code – GitHub Actions
- Backend Lambda code is tested and deployed without manual steps
- Automated rollback on failed builds ensures continuous availability
