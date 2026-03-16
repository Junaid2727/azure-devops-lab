# ☁️ Azure Cloud Engineering — Hands-On Lab Guide

> **Real-world Azure scenarios for DevOps / Cloud Engineer interviews (2+ years level)**

---

## 👨‍💻 About This Repository

This repository contains hands-on Azure labs I built while preparing for a **DevOps / Cloud Engineer interview**. Each scenario solves a real-world problem using Azure services — exactly the type of questions asked in interviews at the 2+ years experience level.

All labs were tested on an **Azure free trial account ($100 credits)**. Total cost for all 8 scenarios is approximately **$10-15** if resources are deleted after each lab.

---

## 🗺️ Scenarios Overview

| # | Scenario | Azure Services | Key Concept |
|---|----------|---------------|-------------|
| 1 | [HA Web App with App Service](#scenario-1) | App Service, Deployment Slots | Zero Downtime Deploy |
| 2 | [Secure Network Architecture](#scenario-2) | VNet, NSG, Subnets, Bastion | Defense in Depth |
| 3 | [Secrets Management](#scenario-3) | Key Vault, Managed Identity, RBAC | Zero Credential Exposure |
| 4 | [Secure Storage Access](#scenario-4) | Blob Storage, SAS Tokens, Tiers | Private vs Public Access |
| 5 | [Database HA & Failover](#scenario-5) | Azure SQL, Geo-replication | RPO & RTO |
| 6 | [Monitoring & Alerting](#scenario-6) | Azure Monitor, Log Analytics, App Insights | Proactive Monitoring |
| 7 | [Cost Management & Governance](#scenario-7) | Azure Policy, Budgets, Tags | Governance at Scale |
| 8 | [VM Backup & Recovery](#scenario-8) | Recovery Services Vault, Backup Policy | BCDR Strategy |

---

## 📋 Prerequisites

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login

# Set your subscription
az account set --subscription "Your Subscription Name"

# Verify
az account show
```

---

## 🚀 Scenario 1 — HA Web App with Azure App Service {#scenario-1}

**Interview Question:** *"How would you host a highly available web application on Azure without managing VMs?"*

### What We Build
A Python Flask app on App Service with deployment slots for zero-downtime deployments.

### Key Commands
```bash
# Create App Service Plan (Free tier)
az appservice plan create \
  --name ha-app-plan \
  --resource-group appservice-rg \
  --location westeurope \
  --sku F1 \
  --is-linux

# Create Web App
az webapp create \
  --name $APP_NAME \
  --resource-group appservice-rg \
  --plan ha-app-plan \
  --runtime "PYTHON:3.11"

# Deploy application
az webapp deploy \
  --resource-group appservice-rg \
  --name $APP_NAME \
  --src-path myapp.zip \
  --type zip

# Create staging slot (requires S1 plan)
az webapp deployment slot create \
  --name $APP_NAME \
  --resource-group appservice-rg \
  --slot staging

# Swap to production — ZERO DOWNTIME!
az webapp deployment slot swap \
  --resource-group appservice-rg \
  --name $APP_NAME \
  --slot staging \
  --target-slot production
```

### What We Achieved
- ✅ Live website accessible from anywhere in the world
- ✅ Zero downtime deployment using slot swap
- ✅ Instant rollback — swap back in 15 seconds
- ✅ 99.95% SLA with no VM management

📁 See [`scenario-1-appservice/`](./scenario-1-appservice/) for full code

---

## 🌐 Scenario 2 — Secure Network Architecture {#scenario-2}

**Interview Question:** *"Web app should be public, database should NEVER be directly accessible from internet. How?"*

### Architecture
```
Internet → Public Subnet (10.0.1.0/24) → Web App
Internet → Private Subnet (10.0.2.0/24) → BLOCKED ❌
Web App  → Private Subnet               → Database ✅
Admin    → AzureBastionSubnet           → VMs (no public IP)
```

### Key Commands
```bash
# Create VNet
az network vnet create \
  --name secure-vnet \
  --address-prefix 10.0.0.0/16 \
  --subnet-name public-subnet \
  --subnet-prefix 10.0.1.0/24

# Create private subnet
az network vnet subnet create \
  --name private-subnet \
  --address-prefix 10.0.2.0/24

# NSG: Allow DB only from public subnet
az network nsg rule create \
  --nsg-name private-nsg \
  --name Allow-DB-From-Public \
  --priority 100 \
  --source-address-prefix 10.0.1.0/24 \
  --destination-port-range 5432 \
  --access Allow

# NSG: Block internet from private subnet
az network nsg rule create \
  --nsg-name private-nsg \
  --name Deny-Internet \
  --priority 200 \
  --source-address-prefix Internet \
  --access Deny
```

📁 See [`scenario-2-networking/`](./scenario-2-networking/) for full scripts

---

## 🔐 Scenario 3 — Secrets Management {#scenario-3}

**Interview Question:** *"How do you store passwords securely without hardcoding them anywhere?"*

### The Flow
```
App → Managed Identity token → Azure AD → Access Token
    → Present token to Key Vault
    → Key Vault checks RBAC
    → Returns secret value
    → ZERO credentials in code!
```

### Key Commands
```bash
# Create Key Vault
az keyvault create \
  --name $KEYVAULT_NAME \
  --resource-group keyvault-rg \
  --enable-rbac-authorization true

# Store a secret
az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name "db-password" \
  --value "SuperSecurePass123!"

# Assign Managed Identity to App Service
az webapp identity assign \
  --name $APP_NAME \
  --resource-group keyvault-rg

# Grant App Service permission to read secrets
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee $IDENTITY \
  --scope $KV_ID
```

### Python Code
```python
from azure.identity import ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient

credential = ManagedIdentityCredential()
client = SecretClient(vault_url=KV_URL, credential=credential)
secret = client.get_secret("db-password")
# No credentials in code!
```

📁 See [`scenario-3-keyvault/`](./scenario-3-keyvault/) for full app code

---

## 📦 Scenario 4 — Secure Storage Access {#scenario-4}

**Interview Question:** *"How do you give a user temporary access to a private file?"*

### SAS Token — Temporary Access
```bash
# Generate SAS token valid for 1 hour, read-only
az storage blob generate-sas \
  --account-name $STORAGE_ACCOUNT \
  --container-name invoices \
  --name invoice-001.pdf \
  --permissions r \
  --expiry $(date -u -d "1 hour" '+%Y-%m-%dT%H:%MZ') \
  --output tsv
```

### Storage Tiers (Cost Optimization)
```
Hot     → $0.018/GB  → Frequently accessed files
Cool    → $0.010/GB  → Monthly access
Cold    → $0.004/GB  → Rare access
Archive → $0.001/GB  → Long-term backup
```

### Lifecycle Policy
```json
{
  "rules": [{
    "name": "move-old-invoices",
    "definition": {
      "actions": {
        "baseBlob": {
          "tierToCool": { "daysAfterModificationGreaterThan": 30 },
          "tierToArchive": { "daysAfterModificationGreaterThan": 90 },
          "delete": { "daysAfterModificationGreaterThan": 365 }
        }
      }
    }
  }]
}
```

📁 See [`scenario-4-storage/`](./scenario-4-storage/) for full scripts

---

## 🗄️ Scenario 5 — Database HA & Failover {#scenario-5}

**Interview Question:** *"If your database region goes down, how do you keep the app running?"*

### Critical Terms
| Term | Definition | Our Target |
|------|-----------|------------|
| RPO | Max acceptable data loss | Near zero |
| RTO | Max acceptable downtime | < 30 seconds |
| Geo-replication | Real-time cross-region copy | West Europe → North Europe |
| Failover Group | Auto-failover + single endpoint | Automatic |

### Key Commands
```bash
# Create failover group
az sql failover-group create \
  --name $FAILOVER_GROUP \
  --server $PRIMARY_SERVER \
  --partner-server $SECONDARY_SERVER \
  --databases $DB_NAME \
  --failover-policy Automatic \
  --grace-period 1

# Test failover
az sql failover-group set-primary \
  --name $FAILOVER_GROUP \
  --server $SECONDARY_SERVER

# Your app always uses ONE endpoint:
# mygroup.database.windows.net → auto-routes to primary!
```

📁 See [`scenario-5-sql-ha/`](./scenario-5-sql-ha/) for full scripts

---

## 📊 Scenario 6 — Monitoring & Alerting {#scenario-6}

**Interview Question:** *"How do you know about problems BEFORE customers complain?"*

### Setup
```bash
# Create Log Analytics Workspace
az monitor log-analytics workspace create \
  --workspace-name $WORKSPACE_NAME \
  --sku PerGB2018 \
  --retention-time 30

# Create Application Insights
az monitor app-insights component create \
  --app $APP_INSIGHTS_NAME \
  --kind web \
  --workspace $WORKSPACE_ID

# Create alert for high error rate
az monitor metrics alert create \
  --name "High-Error-Rate" \
  --condition "count requests/failed > 5" \
  --window-size 5m \
  --severity 2
```

### KQL Queries
```kql
// Count errors by status code
AppServiceHTTPLogs
| summarize count() by ScStatus
| order by count_ desc

// Find slow requests
AppServiceHTTPLogs
| where TimeTaken > 2000
| project TimeGenerated, CsUriStem, TimeTaken
```

📁 See [`scenario-6-monitoring/`](./scenario-6-monitoring/) for full scripts

---

## 💰 Scenario 7 — Cost Management & Governance {#scenario-7}

**Interview Question:** *"50 developers, $50,000 bill, nobody knows what's costing what. How do you fix this?"*

### Mandatory Tags
```bash
az group update \
  --name $RESOURCE_GROUP \
  --tags \
    Environment="production" \
    Owner="junaid" \
    Project="webapp" \
    Team="devops" \
    CostCenter="CC-101"
```

### Azure Policy — Enforce Tagging
```json
{
  "if": {
    "field": "tags[Owner]",
    "exists": "false"
  },
  "then": {
    "effect": "Deny"
  }
}
```

### Budget with Alerts
```bash
az consumption budget create \
  --budget-name "monthly-budget" \
  --amount 1000 \
  --time-grain Monthly \
  --notifications '[
    {"threshold": 80, "thresholdType": "Actual"},
    {"threshold": 100, "thresholdType": "Actual"},
    {"threshold": 110, "thresholdType": "Forecasted"}
  ]'
```

📁 See [`scenario-7-governance/`](./scenario-7-governance/) for full scripts

---

## 💾 Scenario 8 — VM Backup & Recovery {#scenario-8}

**Interview Question:** *"Developer deleted critical production data. How do you recover it?"*

### Backup Policy
```
Daily backups   → 2AM UTC → Keep 7 days
Weekly backups  → Sunday  → Keep 4 weeks  
Monthly backups → 1st Sun → Keep 12 months
Yearly backups  → January → Keep 3 years
```

### Done via Azure Portal
1. Create Recovery Services Vault
2. Set Geo-redundant storage
3. Create DailyBackupPolicy
4. Enable backup on VM
5. Trigger manual backup
6. Verify recovery points exist
7. Test restore process

### Key Concepts
- **Soft Delete** → Deleted backups recoverable for 14 days
- **Instant Recovery** → Snapshots for fast 2-day restores
- **Geo-redundant** → Backups survive regional failures

📁 See [`scenario-8-backup/`](./scenario-8-backup/) for portal walkthrough

---

## 🎤 Interview Cheat Sheet

### Services Quick Reference
| Interviewer says... | You mention... |
|---------------------|----------------|
| Host web app without VMs | App Service — PaaS, slots, auto-scale |
| Zero downtime deployment | Deployment slots + slot swap |
| Secure network design | VNet + subnets + NSG + Bastion |
| Store passwords securely | Key Vault + Managed Identity |
| Temporary file access | SAS tokens with expiry |
| Cheap storage for old files | Blob tiers + lifecycle policies |
| DB survives region failure | Azure SQL + geo-replication + failover groups |
| Know about issues proactively | Azure Monitor + Log Analytics + App Insights |
| Control Azure spending | Budgets + Tags + Azure Policy |
| Recover deleted data | Recovery Services Vault + backup policy |

### Key SLAs to Remember
| Service | SLA |
|---------|-----|
| Single VM | 99.9% |
| VMs in Availability Set | 99.95% |
| App Service (Standard+) | 99.95% |
| Azure SQL | 99.99% |

---

## 🧹 Cost Management Tips

```bash
# Stop AKS cluster when not using
az aks stop --resource-group $RG --name $CLUSTER

# Deallocate VM (no compute charges)
az vm deallocate --resource-group $RG --name $VM

# Delete entire lab when done
az group delete --name $RG --yes --no-wait
```

---

## 📚 Additional Resources

- [Azure Documentation](https://docs.microsoft.com/azure)
- [Azure CLI Reference](https://docs.microsoft.com/cli/azure)
- [KQL Reference](https://docs.microsoft.com/azure/data-explorer/kql-quick-reference)
- [Azure Architecture Center](https://docs.microsoft.com/azure/architecture)
- [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator)

---

## 📄 Full Documentation

Download the complete Word document with all scenarios, diagrams, and interview answers:
👉 [`docs/azure-cloud-lab-guide.docx`](./docs/azure-cloud-lab-guide.docx)

---

*Built with ❤️ for Azure DevOps interview preparation*
