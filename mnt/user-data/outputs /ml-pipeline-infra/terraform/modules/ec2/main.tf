data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-22.04-amd64-server-*"]
  }
}

resource "aws_iam_role" "compute_role" {
  name = "ml-pipeline-compute-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "s3_read" {
  name = "model-store-read"
  role = aws_iam_role.compute_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:ListBucket"]
      Resource = [var.model_bucket_arn, "${var.model_bucket_arn}/*"]
    }]
  })
}

resource "aws_iam_instance_profile" "compute_profile" {
  name = "ml-pipeline-compute-profile-${var.environment}"
  role = aws_iam_role.compute_role.name
}

resource "aws_security_group" "compute_sg" {
  name        = "ml-pipeline-compute-sg-${var.environment}"
  description = "Inference service security group"

  ingress {
    description = "Inference API"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  ingress {
    description = "SSH (restricted)"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "compute" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  iam_instance_profile   = aws_iam_instance_profile.compute_profile.name
  vpc_security_group_ids = [aws_security_group.compute_sg.id]

  root_block_device {
    volume_size = 50
    encrypted   = true
  }

  user_data = <<-EOF
    #!/bin/bash
    apt-get update -y
    apt-get install -y docker.io
    systemctl enable docker
    systemctl start docker
  EOF

  tags = {
    Name = "ml-pipeline-compute-${var.environment}"
  }
}
