"""
Health monitoring and alerting system for the Amazon Affiliate Bot
"""
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
from loguru import logger

from config import config
from models import get_db, BotMetrics


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check endpoints"""
    
    def __init__(self, monitor, *args, **kwargs):
        self.monitor = monitor
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/health":
            self._handle_health_check()
        elif self.path == "/metrics":
            self._handle_metrics()
        elif self.path == "/status":
            self._handle_status()
        else:
            self._send_response(404, {"error": "Not found"})
    
    def _handle_health_check(self):
        """Handle basic health check"""
        try:
            health_status = self.monitor.get_health_status()
            status_code = 200 if health_status.get('healthy', False) else 503
            self._send_response(status_code, health_status)
        except Exception as e:
            self._send_response(500, {"error": str(e)})
    
    def _handle_metrics(self):
        """Handle metrics endpoint"""
        try:
            metrics = self.monitor.get_metrics()
            self._send_response(200, metrics)
        except Exception as e:
            self._send_response(500, {"error": str(e)})
    
    def _handle_status(self):
        """Handle detailed status endpoint"""
        try:
            status = self.monitor.get_detailed_status()
            self._send_response(200, status)
        except Exception as e:
            self._send_response(500, {"error": str(e)})
    
    def _send_response(self, status_code: int, data: Dict[str, Any]):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = json.dumps(data, indent=2, default=str)
        self.wfile.write(response.encode())
    
    def log_message(self, format, *args):
        """Override to use loguru instead of print"""
        logger.debug(f"HTTP: {format % args}")


class HealthMonitor:
    """Health monitoring system for the bot"""
    
    def __init__(self, bot_instance=None):
        """Initialize health monitor"""
        self.bot_instance = bot_instance
        self.logger = logger.bind(component="health_monitor")
        
        # Health check server
        self.server = None
        self.server_thread = None
        
        # Monitoring state
        self.start_time = datetime.utcnow()
        self.last_health_check = None
        self.alerts_sent = []
    
    def start_server(self):
        """Start health check HTTP server"""
        try:
            def handler(*args, **kwargs):
                return HealthCheckHandler(self, *args, **kwargs)
            
            self.server = HTTPServer(('0.0.0.0', config.HEALTH_CHECK_PORT), handler)
            
            self.server_thread = threading.Thread(
                target=self.server.serve_forever,
                daemon=True
            )
            self.server_thread.start()
            
            self.logger.info(f"Health check server started on port {config.HEALTH_CHECK_PORT}")
            
        except Exception as e:
            self.logger.error(f"Failed to start health check server: {str(e)}")
    
    def stop_server(self):
        """Stop health check server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.logger.info("Health check server stopped")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get basic health status"""
        try:
            db = get_db()
            try:
                # Check database connectivity
                db.execute("SELECT 1")
                db_healthy = True
            except Exception:
                db_healthy = False
            finally:
                db.close()
            
            # Check if bot is running
            bot_healthy = self.bot_instance.is_running if self.bot_instance else False
            
            # Overall health
            healthy = db_healthy and bot_healthy
            
            status = {
                'healthy': healthy,
                'timestamp': datetime.utcnow().isoformat(),
                'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
                'components': {
                    'database': db_healthy,
                    'bot': bot_healthy
                }
            }
            
            self.last_health_check = datetime.utcnow()
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting health status: {str(e)}")
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get bot metrics"""
        try:
            db = get_db()
            try:
                # Get metrics for the last 24 hours
                cutoff = datetime.utcnow() - timedelta(hours=24)
                recent_metrics = db.query(BotMetrics).filter(
                    BotMetrics.date >= cutoff
                ).all()
                
                if not recent_metrics:
                    return {
                        'period': '24h',
                        'deals_detected': 0,
                        'tweets_posted': 0,
                        'errors': 0,
                        'api_calls_keepa': 0,
                        'api_calls_twitter': 0
                    }
                
                return {
                    'period': '24h',
                    'deals_detected': sum(m.deals_detected for m in recent_metrics),
                    'tweets_posted': sum(m.tweets_posted for m in recent_metrics),
                    'errors': sum(m.errors_count for m in recent_metrics),
                    'api_calls_keepa': sum(m.api_calls_keepa for m in recent_metrics),
                    'api_calls_twitter': sum(m.api_calls_twitter for m in recent_metrics),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error getting metrics: {str(e)}")
            return {'error': str(e)}
    
    def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed status information"""
        try:
            basic_health = self.get_health_status()
            metrics = self.get_metrics()
            
            # Additional status information
            status = {
                'health': basic_health,
                'metrics': metrics,
                'configuration': {
                    'environment': config.ENVIRONMENT,
                    'max_tweets_per_hour': config.MAX_TWEETS_PER_HOUR,
                    'min_discount_percent': config.MIN_DISCOUNT_PERCENT,
                    'min_price_drop': config.MIN_PRICE_DROP,
                    'max_product_price': config.MAX_PRODUCT_PRICE
                },
                'bot_info': {
                    'start_time': self.start_time.isoformat(),
                    'cycle_count': self.bot_instance.cycle_count if self.bot_instance else 0,
                    'is_running': self.bot_instance.is_running if self.bot_instance else False
                }
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting detailed status: {str(e)}")
            return {'error': str(e)}
    
    def check_alerts(self):
        """Check for conditions that should trigger alerts"""
        try:
            # Get recent metrics
            db = get_db()
            try:
                cutoff = datetime.utcnow() - timedelta(hours=1)
                recent_metrics = db.query(BotMetrics).filter(
                    BotMetrics.date >= cutoff
                ).all()
                
                if recent_metrics:
                    total_errors = sum(m.errors_count for m in recent_metrics)
                    total_deals = sum(m.deals_detected for m in recent_metrics)
                    
                    # Alert if error rate is too high
                    if total_errors > 5:
                        self._send_alert(
                            "high_error_rate",
                            f"High error rate detected: {total_errors} errors in the last hour"
                        )
                    
                    # Alert if no deals detected for a while
                    if total_deals == 0 and len(recent_metrics) >= 2:
                        self._send_alert(
                            "no_deals_detected",
                            "No deals detected in the last hour"
                        )
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"Error checking alerts: {str(e)}")
    
    def _send_alert(self, alert_type: str, message: str):
        """Send alert (placeholder for notification system)"""
        # Check if we've already sent this alert recently
        recent_alert = any(
            alert['type'] == alert_type and 
            (datetime.utcnow() - alert['timestamp']).total_seconds() < 3600
            for alert in self.alerts_sent
        )
        
        if not recent_alert:
            self.logger.warning(f"ALERT [{alert_type}]: {message}")
            
            # Record alert
            self.alerts_sent.append({
                'type': alert_type,
                'message': message,
                'timestamp': datetime.utcnow()
            })
            
            # TODO: Implement actual notification system
            # - Email notifications
            # - Slack/Discord webhooks
            # - SMS alerts
            # - Push notifications
    
    def get_prometheus_metrics(self) -> str:
        """Generate Prometheus-compatible metrics"""
        try:
            metrics = self.get_metrics()
            health = self.get_health_status()
            
            prometheus_metrics = f"""# HELP affiliate_bot_deals_detected_total Total number of deals detected
# TYPE affiliate_bot_deals_detected_total counter
affiliate_bot_deals_detected_total {metrics.get('deals_detected', 0)}

# HELP affiliate_bot_tweets_posted_total Total number of tweets posted
# TYPE affiliate_bot_tweets_posted_total counter
affiliate_bot_tweets_posted_total {metrics.get('tweets_posted', 0)}

# HELP affiliate_bot_errors_total Total number of errors
# TYPE affiliate_bot_errors_total counter
affiliate_bot_errors_total {metrics.get('errors', 0)}

# HELP affiliate_bot_healthy Bot health status (1 = healthy, 0 = unhealthy)
# TYPE affiliate_bot_healthy gauge
affiliate_bot_healthy {1 if health.get('healthy', False) else 0}

# HELP affiliate_bot_uptime_seconds Bot uptime in seconds
# TYPE affiliate_bot_uptime_seconds gauge
affiliate_bot_uptime_seconds {health.get('uptime_seconds', 0)}
"""
            return prometheus_metrics
            
        except Exception as e:
            self.logger.error(f"Error generating Prometheus metrics: {str(e)}")
            return "# Error generating metrics"