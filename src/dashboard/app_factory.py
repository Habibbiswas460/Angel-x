"""
Flask App Factory for Angel-X Dashboard
Creates and configures Flask app with real data sources
"""

from flask import Flask
from flask_cors import CORS
from typing import Optional
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_dashboard_app(
    trade_journal=None,
    data_feed=None,
    broker_client=None,
    config: Optional[dict] = None
) -> Flask:
    """
    Create and configure Flask app for Angel-X dashboard
    
    Args:
        trade_journal: TradeJournalEngine instance for trade data
        data_feed: DataFeed instance for market data
        broker_client: Broker client for connection status
        config: Optional configuration dictionary
        
    Returns:
        Configured Flask app instance
    """
    
    # Create Flask app
    app = Flask(__name__, static_folder=None)
    
    # Enable CORS for all routes
    CORS(app)
    
    # Store data sources in app context for access by routes
    app.trade_journal = trade_journal
    app.data_feed = data_feed
    app.broker_client = broker_client
    
    # Configuration
    if config is None:
        config = {}
    
    app.config.update(
        DEBUG=config.get('debug', False),
        JSON_SORT_KEYS=False,
        JSONIFY_PRETTYPRINT_REGULAR=True,
    )
    
    # Register dashboard blueprint with initialized aggregator
    from .routes import dashboard_bp, initialize_aggregator
    
    # Initialize the aggregator with real data sources
    initialize_aggregator(trade_journal, data_feed, broker_client)
    app.register_blueprint(dashboard_bp)
    
    # Register health check endpoint
    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        return {
            'status': 'healthy',
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'data_sources': {
                'trade_journal': trade_journal is not None,
                'data_feed': data_feed is not None,
                'broker_client': broker_client is not None,
            }
        }, 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return {'error': 'Not found', 'message': str(error)}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        logger.error(f"Internal server error: {error}")
        return {'error': 'Internal server error', 'message': str(error)}, 500
    
    logger.info("Dashboard app created successfully")
    logger.info(f"Data sources initialized: trade_journal={trade_journal is not None}, "
                f"data_feed={data_feed is not None}, broker_client={broker_client is not None}")
    
    return app


def run_dashboard_app(
    trade_journal=None,
    data_feed=None,
    broker_client=None,
    host: str = '0.0.0.0',
    port: int = 5000,
    debug: bool = False
):
    """
    Run the dashboard app directly (for standalone execution)
    
    Args:
        trade_journal: TradeJournalEngine instance
        data_feed: DataFeed instance
        broker_client: Broker client instance
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
    """
    
    app = create_dashboard_app(
        trade_journal=trade_journal,
        data_feed=data_feed,
        broker_client=broker_client,
        config={'debug': debug}
    )
    
    logger.info(f"Starting dashboard on {host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    # Run with dummy data for testing
    app = create_dashboard_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
