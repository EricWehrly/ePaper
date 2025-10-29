# Route 53 DNS record pointing to the inlets server
resource "aws_route53_record" "inlets" {
  zone_id = local.actual_zone.zone_id
  name    = var.domain_name
  type    = "A"
  ttl     = 300
  records = [aws_eip.inlets_server.public_ip]

  depends_on = [aws_eip.inlets_server]
}
# NOTE: SSL/TLS is provisioned on the EC2 instance using certbot (Let's Encrypt).
# 
# FUTURE CONSIDERATION - ACM + ALB Approach:
# If we want AWS-managed certificates and better scaling/reliability, we can:
# 1. Create an Application Load Balancer (ALB) in front of the EC2 instance
# 2. Use ACM to provision and auto-renew SSL certificates
# 3. Configure the ALB to terminate TLS and forward HTTP to the EC2 instance
# 4. Remove certbot/nginx TLS config from the instance (nginx would only handle HTTP)
# 5. Update security group to only allow ALB -> instance traffic on HTTP
# This approach provides: managed certs, better availability, AWS-native scaling,
# and eliminates the need for certbot renewal on the instance.