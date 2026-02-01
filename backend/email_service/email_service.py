"""
Email Service Module
Sends confirmation and digest emails with retry logic
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from pathlib import Path
import time

logger = logging.getLogger(__name__)


class SendGridClient:
    """SendGrid email client"""
    
    def __init__(self, api_key: str, from_email: str, from_name: str):
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            self.client = SendGridAPIClient(api_key)
            self.from_email = from_email
            self.from_name = from_name
            self.Mail = Mail
        except ImportError:
            raise ImportError("sendgrid package required for SendGrid client")
    
    def send(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email via SendGrid"""
        try:
            message = self.Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            response = self.client.send(message)
            return response.status_code in [200, 201, 202]
            
        except Exception as e:
            logger.error(f"SendGrid send error: {e}")
            return False


class SMTPClient:
    """SMTP email client"""
    
    def __init__(self, config: Dict):
        self.host = config.get("host", "smtp.gmail.com")
        self.port = config.get("port", 587)
        self.username = config.get("username")
        self.password = config.get("password")
        self.from_email = config.get("from_email", self.username)
        self.from_name = config.get("from_name", "AI Job Bot")
    
    def send(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP send error: {e}")
            return False


class TemplateEngine:
    """Simple HTML template engine"""
    
    def __init__(self, templates_dir: str = None):
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            self.templates_dir = Path(__file__).parent / "templates"
        
        self.templates_dir.mkdir(parents=True, exist_ok=True)
    
    def render(self, template_name: str, data: Dict) -> str:
        """Render template with data"""
        template_path = self.templates_dir / template_name
        
        if template_path.exists():
            with open(template_path, 'r') as f:
                template = f.read()
        else:
            # Use default template
            template = self._get_default_template(template_name)
        
        # Simple string replacement
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            template = template.replace(placeholder, str(value))
        
        return template
    
    def _get_default_template(self, template_name: str) -> str:
        """Get default template if file doesn't exist"""
        if "confirmation" in template_name:
            return self._default_confirmation_template()
        elif "digest" in template_name:
            return self._default_digest_template()
        else:
            return "<html><body>{{content}}</body></html>"
    
    def _default_confirmation_template(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                         color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                .job-details { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; 
                              border-left: 4px solid #667eea; }
                .button { display: inline-block; padding: 12px 30px; background: #667eea; 
                         color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }
                .footer { text-align: center; margin-top: 30px; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Application Submitted!</h1>
                </div>
                <div class="content">
                    <p>Hi {{user_name}},</p>
                    <p>Great news! Your application has been successfully submitted.</p>
                    
                    <div class="job-details">
                        <h2>{{job_title}}</h2>
                        <p><strong>Company:</strong> {{company}}</p>
                        <p><strong>Location:</strong> {{location}}</p>
                        <p><strong>Application ID:</strong> {{application_id}}</p>
                        <p><strong>Submitted:</strong> {{timestamp}}</p>
                    </div>
                    
                    <p><strong>Next Steps:</strong></p>
                    <ul>
                        <li>The employer will review your application</li>
                        <li>You'll be notified of any updates</li>
                        <li>Prepare for potential interviews</li>
                    </ul>
                    
                    <a href="{{job_url}}" class="button">View Job Posting</a>
                    
                    <p>Good luck! 🍀</p>
                </div>
                <div class="footer">
                    <p>AI Job Recommendation Bot | Powered by AI</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _default_digest_template(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                         color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                .stats { display: flex; justify-content: space-around; margin: 20px 0; }
                .stat-box { background: white; padding: 20px; border-radius: 8px; text-align: center; flex: 1; margin: 0 10px; }
                .stat-number { font-size: 32px; font-weight: bold; color: #667eea; }
                .footer { text-align: center; margin-top: 30px; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Your Weekly Job Search Summary</h1>
                </div>
                <div class="content">
                    <p>Hi {{user_name}},</p>
                    <p>Here's your job search activity for the past week:</p>
                    
                    <div class="stats">
                        <div class="stat-box">
                            <div class="stat-number">{{total_applications}}</div>
                            <div>Applications</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">{{recommendations_viewed}}</div>
                            <div>Jobs Viewed</div>
                        </div>
                    </div>
                    
                    <h3>💡 Recommended for You</h3>
                    <p>{{recommendations}}</p>
                    
                    <p><strong>Keep going! You're making great progress. 🚀</strong></p>
                </div>
                <div class="footer">
                    <p>AI Job Recommendation Bot | <a href="{{unsubscribe_url}}">Unsubscribe</a></p>
                </div>
            </div>
        </body>
        </html>
        """


class EmailService:
    """Main email service with retry logic"""
    
    def __init__(self, provider: str = "sendgrid", config: Dict = None):
        config = config or {}
        
        if provider == "sendgrid":
            self.client = SendGridClient(
                config.get("sendgrid_api_key"),
                config.get("from_email", "noreply@jobbot.com"),
                config.get("from_name", "AI Job Bot")
            )
        elif provider == "smtp":
            self.client = SMTPClient(config.get("smtp_config", {}))
        else:
            raise ValueError(f"Unknown email provider: {provider}")
        
        self.template_engine = TemplateEngine()
    
    def send_application_confirmation(self, user_email: str, application: Dict) -> bool:
        """
        Send application confirmation email
        
        Args:
            user_email: User's email address
            application: Application dictionary
            
        Returns:
            True if sent successfully
        """
        subject = f"Application Submitted: {application.get('job_title', 'Job')}"
        
        html_content = self.template_engine.render(
            "application_confirmation.html",
            {
                "user_name": application.get("user_name", "there"),
                "job_title": application.get("job_title", ""),
                "company": application.get("company", ""),
                "location": application.get("location", ""),
                "application_id": application.get("application_id", ""),
                "timestamp": application.get("timestamp", ""),
                "job_url": application.get("job_url", "#")
            }
        )
        
        return self._retry_send(user_email, subject, html_content)
    
    def send_weekly_digest(self, user_email: str, stats: Dict, 
                          recommendations: List[Dict]) -> bool:
        """
        Send weekly summary email
        
        Args:
            user_email: User's email address
            stats: Statistics dictionary
            recommendations: List of job recommendations
            
        Returns:
            True if sent successfully
        """
        subject = "Your Weekly Job Search Summary"
        
        # Format recommendations
        rec_text = ""
        for rec in recommendations[:3]:
            job = rec.get("job", {})
            rec_text += f"• {job.get('title', '')} at {job.get('company', '')}\n"
        
        html_content = self.template_engine.render(
            "weekly_digest.html",
            {
                "user_name": "there",
                "total_applications": stats.get("total", 0),
                "recommendations_viewed": stats.get("viewed", 0),
                "recommendations": rec_text or "No new recommendations this week",
                "unsubscribe_url": "#"
            }
        )
        
        return self._retry_send(user_email, subject, html_content)
    
    def _retry_send(self, to_email: str, subject: str, html_content: str, 
                   max_retries: int = 2) -> bool:
        """
        Retry email sending on failure
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML content
            max_retries: Maximum retry attempts
            
        Returns:
            True if sent successfully
        """
        for attempt in range(max_retries + 1):
            try:
                success = self.client.send(to_email, subject, html_content)
                if success:
                    return True
                
                if attempt < max_retries:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.warning(f"Email send failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Email send attempt {attempt + 1} failed: {e}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
        
        return False
