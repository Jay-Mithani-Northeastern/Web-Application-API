
variable "aws_region" {
  type    = string
  default = "us-east-1"
}
variable "ami_regions" {
  default = [
    "us-east-1",
  ]
}
variable "ami_users" {
  default = [
    "712116592721",
  ]
}
variable "profile" {
  type    = string
  default = "packer"
}

variable "source_ami" {
  type    = string
  default = "ami-0dfcb1ef8550277af" # Amzon Linux 2
}

variable "instance_type" {
  type    = string
  default = "t2.micro"
}

variable "ssh_username" {
  type    = string
  default = "ec2-user"
}

variable "artifacts_source" {
  type    = string
  default = "../app.zip"
}

variable "artifacts_destination" {
  type    = string
  default = "/tmp/"
}

variable "service_source" {
  type    = string
  default = "webapp.service"
}

variable "service_destination" {
  type    = string
  default = "/lib/systemd/system/webapp.service"
}

variable "packer_script_file" {
  type    = string
  default = "packer.sh"
}

source "amazon-ebs" "my-ami" {
  profile         = "${var.profile}"
  region          = "${var.aws_region}"
  ami_name        = "csye6225_${formatdate("YYYY_MM_DD_hh_mm_ss", timestamp())}"
  ami_description = "AMI for CSYE 6225"
  ami_regions     = var.ami_regions
  ami_users       = var.ami_users
  instance_type   = "${var.instance_type}"
  source_ami      = "${var.source_ami}"
  ssh_username    = "${var.ssh_username}"

}

build {
  sources = ["source.amazon-ebs.my-ami"]

  provisioner "file" {
    source      = "${var.artifacts_source}"
    destination = "${var.artifacts_destination}"
  }

  provisioner "shell" {
    script = "${var.packer_script_file}"
  }
}

