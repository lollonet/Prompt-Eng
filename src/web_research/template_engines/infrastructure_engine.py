"""
Infrastructure Template Engine for cloud deployments following SOLID principles.

Business Context: Generates cloud infrastructure configurations including
Terraform, CloudFormation, and cloud-specific deployment templates.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .base_engine import ITemplateEngine, TemplateContext, TemplateResult


@dataclass
class CloudConfiguration:
    """Cloud-specific configuration parameters."""

    provider: str = "aws"
    region: str = "us-east-1"
    instance_type: str = "t3.medium"
    availability_zones: int = 2
    auto_scaling: bool = True


class InfrastructureTemplateEngine(ITemplateEngine):
    """
    Specialized template engine for cloud infrastructure deployments.

    Business Context: Handles Infrastructure as Code (IaC) patterns with focus on
    scalability, cost optimization, and multi-cloud deployments.

    Why this approach: Single Responsibility - focuses only on infrastructure
    provisioning patterns while supporting multiple cloud providers.
    """

    @property
    def engine_name(self) -> str:
        return "infrastructure"

    @property
    def supported_technologies(self) -> List[str]:
        return [
            "terraform",
            "cloudformation",
            "aws",
            "azure",
            "gcp",
            "infrastructure",
            "vpc",
            "ec2",
            "rds",
            "elb",
            "iam",
            "s3",
            "cloudwatch",
            "route53",
        ]

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._cloud_providers = self._initialize_cloud_providers()
        self._resource_templates = self._initialize_resource_templates()

    def _initialize_cloud_providers(self) -> Dict[str, Dict]:
        """Initialize cloud provider configurations (≤15 lines)."""
        return {
            "aws": {
                "compute": "ec2",
                "database": "rds",
                "storage": "s3",
                "network": "vpc",
                "monitoring": "cloudwatch",
            },
            "azure": {
                "compute": "virtual-machines",
                "database": "sql-database",
                "storage": "blob-storage",
                "network": "virtual-network",
                "monitoring": "azure-monitor",
            },
            "gcp": {
                "compute": "compute-engine",
                "database": "cloud-sql",
                "storage": "cloud-storage",
                "network": "vpc",
                "monitoring": "cloud-monitoring",
            },
        }

    def _initialize_resource_templates(self) -> Dict[str, Dict]:
        """Initialize infrastructure resource templates (≤15 lines)."""
        return {
            "compute": {"min_instances": 2, "max_instances": 10},
            "database": {"multi_az": True, "backup_retention": 7},
            "network": {"public_subnets": 2, "private_subnets": 2},
            "monitoring": {"retention_days": 30, "alerting": True},
            "security": {"encryption": True, "access_logging": True},
        }

    def can_handle(self, context: TemplateContext) -> bool:
        """
        Determine if this engine can handle the context.

        Business Context: Focuses on infrastructure provisioning and
        cloud deployment scenarios.
        """
        tech_lower = context.technology.lower()
        task_lower = context.task_description.lower()

        # Direct infrastructure technologies
        if any(tech in tech_lower for tech in ["terraform", "cloudformation", "infrastructure"]):
            return True

        # Cloud provider preferences
        cloud_provider = getattr(context.specific_options, "cloud_provider", "")
        if cloud_provider and cloud_provider.lower() in self._cloud_providers:
            return True

        # Infrastructure-related keywords
        infra_keywords = ["provision", "deploy", "infrastructure", "cloud", "scale"]
        if any(keyword in task_lower for keyword in infra_keywords):
            cluster_size = getattr(context.specific_options, "cluster_size", 0)
            if cluster_size and cluster_size > 1:
                return True

        return False

    def estimate_complexity(self, context: TemplateContext) -> str:
        """Estimate infrastructure complexity based on requirements."""
        tech_count = len(context.technology.split())
        cluster_size = getattr(context.specific_options, "cluster_size", 1)
        ha_setup = getattr(context.specific_options, "ha_setup", False)
        monitoring = getattr(context.specific_options, "monitoring_stack", [])

        complexity_score = tech_count + (cluster_size // 2)
        if ha_setup:
            complexity_score += 3
        if monitoring:
            complexity_score += len(monitoring)

        if complexity_score >= 8:
            return "complex"
        elif complexity_score >= 4:
            return "moderate"
        else:
            return "simple"

    async def generate_template(self, context: TemplateContext) -> TemplateResult:
        """
        Generate infrastructure template based on context.

        Business Context: Main entry point that orchestrates infrastructure
        template generation based on cloud provider and deployment requirements.
        """
        self._logger.info(f"Generating Infrastructure template for: {context.technology}")

        # Parse technologies and build configuration
        technologies = self._parse_technologies(context.technology)
        cloud_config = self._build_cloud_config(context)

        # Generate appropriate template based on cloud provider
        if cloud_config.provider == "aws":
            template_content = self._generate_aws_template(technologies, context, cloud_config)
        elif cloud_config.provider == "azure":
            template_content = self._generate_azure_template(technologies, context, cloud_config)
        elif cloud_config.provider == "gcp":
            template_content = self._generate_gcp_template(technologies, context, cloud_config)
        else:
            template_content = self._generate_terraform_template(
                technologies, context, cloud_config
            )

        import hashlib
        from datetime import datetime

        context_hash = hashlib.md5(
            f"{context.technology}_{context.task_description}_{cloud_config.provider}".encode()
        ).hexdigest()[:8]

        return TemplateResult(
            content=template_content,
            template_type="infrastructure",
            confidence_score=0.85,
            estimated_complexity=self.estimate_complexity(context),
            generated_at=datetime.now(),
            context_hash=context_hash,
        )

    def _parse_technologies(self, tech_string: str) -> List[str]:
        """Parse and normalize technology names (≤10 lines)."""
        techs = [tech.strip().lower() for tech in tech_string.split()]

        # Normalize cloud variations
        normalized = []
        for tech in techs:
            if tech in ["aws", "amazon"]:
                normalized.append("aws")
            elif tech in ["azure", "microsoft"]:
                normalized.append("azure")
            elif tech in ["gcp", "google", "gce"]:
                normalized.append("gcp")
            else:
                normalized.append(tech)

        return normalized

    def _build_cloud_config(self, context: TemplateContext) -> CloudConfiguration:
        """Build cloud configuration from context (≤10 lines)."""
        specific_opts = context.specific_options
        provider = getattr(specific_opts, "cloud_provider", "aws")
        cluster_size = getattr(specific_opts, "cluster_size", 2)

        return CloudConfiguration(
            provider=provider.lower(),
            region="us-east-1",
            instance_type="t3.medium",
            availability_zones=min(cluster_size, 3),
            auto_scaling=cluster_size > 2,
        )

    def _generate_aws_template(
        self, technologies: List[str], context: TemplateContext, cloud_config: CloudConfiguration
    ) -> str:
        """
        Generate AWS CloudFormation or Terraform template.

        Business Context: Creates production-ready AWS infrastructure
        with security, scalability, and cost optimization in mind.
        """
        if "terraform" in technologies:
            return self._generate_aws_terraform(technologies, context, cloud_config)
        else:
            return self._generate_aws_cloudformation(technologies, context, cloud_config)

    def _generate_aws_terraform(
        self, technologies: List[str], context: TemplateContext, cloud_config: CloudConfiguration
    ) -> str:
        """Generate AWS Terraform configuration (≤30 lines)."""
        cluster_size = getattr(context.specific_options, "cluster_size", 2)

        return f"""# AWS Infrastructure for {context.technology}
# Provider configuration
terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = "{cloud_config.region}"
}}

# VPC and Networking
resource "aws_vpc" "main" {{
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {{
    Name = "{context.technology}-vpc"
  }}
}}

resource "aws_internet_gateway" "main" {{
  vpc_id = aws_vpc.main.id
  
  tags = {{
    Name = "{context.technology}-igw"
  }}
}}

# Public Subnets
resource "aws_subnet" "public" {{
  count             = {cloud_config.availability_zones}
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${{count.index + 1}}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  
  tags = {{
    Name = "{context.technology}-public-subnet-${{count.index + 1}}"
  }}
}}

# Security Group
resource "aws_security_group" "app" {{
  name_prefix = "{context.technology}-sg"
  vpc_id      = aws_vpc.main.id
  
  ingress {{
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}
  
  ingress {{
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}
  
  ingress {{
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}
  
  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}
}}

# Launch Template
resource "aws_launch_template" "app" {{
  name_prefix   = "{context.technology}-lt"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = "{cloud_config.instance_type}"
  vpc_security_group_ids = [aws_security_group.app.id]
  
  user_data = base64encode(<<-EOF
    #!/bin/bash
    yum update -y
    # Install {context.technology} here
  EOF
  )
  
  tags = {{
    Name = "{context.technology}-launch-template"
  }}
}}

# Auto Scaling Group
resource "aws_autoscaling_group" "app" {{
  name                = "{context.technology}-asg"
  vpc_zone_identifier = aws_subnet.public[*].id
  target_group_arns   = [aws_lb_target_group.app.arn]
  health_check_type   = "ELB"
  
  min_size         = 2
  max_size         = {min(cluster_size * 2, 10)}
  desired_capacity = {cluster_size}
  
  launch_template {{
    id      = aws_launch_template.app.id
    version = "$Latest"
  }}
  
  tag {{
    key                 = "Name"
    value               = "{context.technology}-instance"
    propagate_at_launch = true
  }}
}}

# Load Balancer
resource "aws_lb" "app" {{
  name               = "{context.technology}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.app.id]
  subnets           = aws_subnet.public[*].id
  
  enable_deletion_protection = false
}}

resource "aws_lb_target_group" "app" {{
  name     = "{context.technology}-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  
  health_check {{
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }}
}}

resource "aws_lb_listener" "app" {{
  load_balancer_arn = aws_lb.app.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {{
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }}
}}

# Data sources
data "aws_availability_zones" "available" {{
  state = "available"
}}

data "aws_ami" "amazon_linux" {{
  most_recent = true
  owners      = ["amazon"]
  
  filter {{
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }}
}}

# Outputs
output "load_balancer_dns" {{
  value = aws_lb.app.dns_name
}}

output "vpc_id" {{
  value = aws_vpc.main.id
}}

{self._generate_terraform_deployment_instructions(context)}"""

    def _generate_aws_cloudformation(
        self, technologies: List[str], context: TemplateContext, cloud_config: CloudConfiguration
    ) -> str:
        """Generate AWS CloudFormation template (≤20 lines)."""
        cluster_size = getattr(context.specific_options, "cluster_size", 2)

        return f"""# AWS CloudFormation Template for {context.technology}
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Infrastructure for {context.technology} deployment'

Parameters:
  InstanceType:
    Type: String
    Default: {cloud_config.instance_type}
    Description: EC2 instance type
  
  ClusterSize:
    Type: Number
    Default: {cluster_size}
    Description: Number of instances in the cluster

Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub '${{AWS::StackName}}-vpc'

  InternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: Name
          Value: !Sub '${{AWS::StackName}}-igw'

  PublicSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub '${{AWS::StackName}}-public-subnet'

Outputs:
  VPCId:
    Description: VPC ID
    Value: !Ref VPC
    Export:
      Name: !Sub '${{AWS::StackName}}-VPC-ID'

{self._generate_cloudformation_deployment_instructions(context)}"""

    def _generate_azure_template(
        self, technologies: List[str], context: TemplateContext, cloud_config: CloudConfiguration
    ) -> str:
        """Generate Azure ARM template (≤20 lines)."""
        return f"""# Azure ARM Template for {context.technology}
{{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {{
    "vmSize": {{
      "type": "string",
      "defaultValue": "Standard_B2s",
      "metadata": {{
        "description": "Size of the virtual machine"
      }}
    }},
    "clusterSize": {{
      "type": "int",
      "defaultValue": {getattr(context.specific_options, 'cluster_size', 2)},
      "metadata": {{
        "description": "Number of VMs in the cluster"
      }}
    }}
  }},
  "variables": {{
    "vnetName": "{context.technology}-vnet",
    "subnetName": "{context.technology}-subnet",
    "nsgName": "{context.technology}-nsg"
  }},
  "resources": [
    {{
      "type": "Microsoft.Network/virtualNetworks",
      "apiVersion": "2021-02-01",
      "name": "[variables('vnetName')]",
      "location": "[resourceGroup().location]",
      "properties": {{
        "addressSpace": {{
          "addressPrefixes": ["10.0.0.0/16"]
        }},
        "subnets": [
          {{
            "name": "[variables('subnetName')]",
            "properties": {{
              "addressPrefix": "10.0.1.0/24"
            }}
          }}
        ]
      }}
    }}
  ]
}}

{self._generate_azure_deployment_instructions(context)}"""

    def _generate_gcp_template(
        self, technologies: List[str], context: TemplateContext, cloud_config: CloudConfiguration
    ) -> str:
        """Generate GCP Deployment Manager template (≤20 lines)."""
        return f"""# GCP Deployment Manager Template for {context.technology}
resources:
- name: {context.technology}-network
  type: compute.v1.network
  properties:
    autoCreateSubnetworks: false
    
- name: {context.technology}-subnet
  type: compute.v1.subnetwork
  properties:
    network: $(ref.{context.technology}-network.selfLink)
    ipCidrRange: 10.0.1.0/24
    region: {cloud_config.region}

- name: {context.technology}-firewall
  type: compute.v1.firewall
  properties:
    network: $(ref.{context.technology}-network.selfLink)
    allowed:
    - IPProtocol: TCP
      ports: ["22", "80", "443"]
    sourceRanges: ["0.0.0.0/0"]

- name: {context.technology}-template
  type: compute.v1.instanceTemplate
  properties:
    properties:
      machineType: {cloud_config.instance_type}
      disks:
      - boot: true
        initializeParams:
          sourceImage: projects/debian-cloud/global/images/family/debian-11
      networkInterfaces:
      - network: $(ref.{context.technology}-network.selfLink)
        subnetwork: $(ref.{context.technology}-subnet.selfLink)
        accessConfigs:
        - type: ONE_TO_ONE_NAT

{self._generate_gcp_deployment_instructions(context)}"""

    def _generate_terraform_template(
        self, technologies: List[str], context: TemplateContext, cloud_config: CloudConfiguration
    ) -> str:
        """Generate generic Terraform template (≤15 lines)."""
        return f"""# Generic Terraform Template for {context.technology}
terraform {{
  required_version = ">= 1.0"
  required_providers {{
    {cloud_config.provider} = {{
      source  = "hashicorp/{cloud_config.provider}"
      version = "~> 5.0"
    }}
  }}
}}

provider "{cloud_config.provider}" {{
  region = "{cloud_config.region}"
}}

# Infrastructure resources for {context.technology}
# Add specific resources based on requirements

{self._generate_terraform_deployment_instructions(context)}"""

    def _generate_terraform_deployment_instructions(self, context: TemplateContext) -> str:
        """Generate Terraform deployment instructions (≤15 lines)."""
        return """## TERRAFORM DEPLOYMENT INSTRUCTIONS

```bash
# Initialize Terraform
terraform init

# Plan the deployment
terraform plan

# Apply the infrastructure
terraform apply

# Verify resources
terraform show
terraform output

# Cleanup (when needed)
terraform destroy
```"""

    def _generate_cloudformation_deployment_instructions(self, context: TemplateContext) -> str:
        """Generate CloudFormation deployment instructions (≤10 lines)."""
        return """## CLOUDFORMATION DEPLOYMENT INSTRUCTIONS

```bash
# Deploy the stack
aws cloudformation create-stack \\
  --stack-name monitoring-infrastructure \\
  --template-body file://template.yaml

# Check stack status
aws cloudformation describe-stacks --stack-name monitoring-infrastructure
```"""

    def _generate_azure_deployment_instructions(self, context: TemplateContext) -> str:
        """Generate Azure deployment instructions (≤10 lines)."""
        return """## AZURE DEPLOYMENT INSTRUCTIONS

```bash
# Create resource group
az group create --name monitoring-rg --location eastus

# Deploy ARM template
az deployment group create \\
  --resource-group monitoring-rg \\
  --template-file template.json
```"""

    def _generate_gcp_deployment_instructions(self, context: TemplateContext) -> str:
        """Generate GCP deployment instructions (≤10 lines)."""
        return """## GCP DEPLOYMENT INSTRUCTIONS

```bash
# Deploy with Deployment Manager
gcloud deployment-manager deployments create monitoring-deployment \\
  --config config.yaml

# Check deployment status
gcloud deployment-manager deployments describe monitoring-deployment
```"""
