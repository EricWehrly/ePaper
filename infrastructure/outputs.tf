output "chisel_server_public_ip" {
  description = "Public IP address of the Chisel server"
  value       = aws_eip.chisel_server.public_ip
}

output "chisel_server_domain" {
  description = "Domain name for the Chisel tunnel"
  value       = var.domain_name
}

output "chisel_tunnel_url" {
  description = "Full HTTPS URL for the Chisel tunnel"
  value       = "https://${var.domain_name}"
}

output "chisel_server_endpoint" {
  description = "Chisel server endpoint for client connection"
  value       = "https://${var.domain_name}:8080"
}

output "ssh_connection" {
  description = "SSH connection command for the Chisel server (if key_name provided)"
  value       = var.key_name != null ? "ssh -i /path/to/your/${var.key_name}.pem ec2-user@${aws_eip.chisel_server.public_ip}" : "No SSH key configured - use SSM Session Manager instead"
}

output "ssm_connection" {
  description = "AWS SSM Session Manager connection command"
  value       = "aws ssm start-session --target ${aws_instance.chisel_server.id} --region ${var.aws_region}"
}

output "ssl_certificate_info" {
  description = "SSL certificate is managed by certbot on the instance (Let's Encrypt)"
  value       = "Certificate auto-renewed by certbot for ${var.domain_name}"
}

output "hosted_zone_name" {
  description = "Name of the hosted zone"
  value       = local.actual_zone.name
}

output "hosted_zone_id" {
  description = "ID of the hosted zone used"
  value       = local.actual_zone.zone_id
}

output "chisel_auth" {
  description = "The Chisel authentication credential (auto-generated if not provided)"
  value       = local.actual_chisel_auth
  sensitive   = true
}

output "client_config_generated" {
  description = "Whether client configuration was generated"
  value       = var.generate_client_config
}

output "client_setup_instructions" {
  description = "Instructions for setting up the Chisel client"
  value = var.generate_client_config ? [
    "1. Copy these files to your target system:",
    "   - infrastructure/docker-compose.chisel.yml",
    "   - infrastructure/.env.chisel (generated)",
    "2. Run: docker compose -f docker-compose.chisel.yml up -d",
    "3. Check status: docker compose -f docker-compose.chisel.yml logs -f"
  ] : [
    "Client config not generated. Set generate_client_config = true to enable."
  ]
}