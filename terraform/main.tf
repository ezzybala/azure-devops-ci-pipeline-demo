terraform {
  required_version = ">= 1.4.0"
}

resource "terraform_data" "example" {
  input = "calculator-ci-demo"
}

output "example_name" {
  value = terraform_data.example.output
}
