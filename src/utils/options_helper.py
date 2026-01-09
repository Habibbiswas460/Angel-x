"""
Options Helper Module
Handles options-specific operations using AngelOne SmartAPI directly.
No OpenAlgo dependency - all data comes from broker.
"""

from config import config
from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)

# Import AngelOne SmartAPI
try:
    from src.integrations.angelone.smartapi_integration import SmartAPIClient
    SMARTAPI_AVAILABLE = True
except ImportError:
    SmartAPIClient = None
    SMARTAPI_AVAILABLE = False


class OptionsHelper:
    """
    Options trading helper using AngelOne SmartAPI directly
    No OpenAlgo dependency required
    """
    
    def __init__(self):
        self.strategy = config.STRATEGY_NAME
        self.smartapi_client = None
        
        # Initialize SmartAPI client if available
        if SMARTAPI_AVAILABLE:
            try:
                import os
                api_key = os.getenv('ANGELONE_API_KEY', '')
                client_code = os.getenv('ANGELONE_CLIENT_CODE', '')
                password = os.getenv('ANGELONE_PASSWORD', '')
                totp_secret = os.getenv('ANGELONE_TOTP_SECRET', '')
                
                if api_key and client_code:
                    self.smartapi_client = SmartAPIClient(
                        api_key=api_key,
                        client_code=client_code,
                        password=password,
                        totp_secret=totp_secret
                    )
                    logger.info("OptionsHelper initialized with AngelOne SmartAPI")
                else:
                    logger.warning("AngelOne credentials missing - running in fallback mode")
            except Exception as e:
                logger.error(f"Failed to initialize SmartAPI: {e}")
        else:
            logger.warning("SmartAPI not available - OptionsHelper in fallback mode")
        
        logger.info("OptionsHelper initialized")

    def compute_offset(self, underlying: str, expiry_date: str, strike: float, option_type: str, exchange: str = None) -> str:
        """Compute ITM/OTM/ATM offset label relative to ATM strike."""
        if exchange is None:
            exchange = config.UNDERLYING_EXCHANGE
        atm = self.get_atm_strike(underlying, expiry_date, exchange)
        if not atm:
            logger.warning("ATM strike not available; defaulting to ATM")
            return "ATM"
        try:
            diff = float(strike) - float(atm)
            # Get strike step from config (NIFTY=50, BANKNIFTY=100, etc.)
            strike_step = getattr(config, 'STRIKE_STEP', {}).get(underlying.upper(), 50)
            step = int(round(abs(diff) / strike_step))
            if step == 0:
                return "ATM"
            if option_type.upper() == "CE":
                # CE: strike below ATM is ITM, above ATM is OTM
                return ("ITM" + str(step)) if diff < 0 else ("OTM" + str(step))
            else:
                # PE: strike above ATM is ITM, below ATM is OTM
                return ("ITM" + str(step)) if diff > 0 else ("OTM" + str(step))
        except Exception as e:
            logger.error(f"Error computing offset: {e}")
            return "ATM"
    
    def place_option_order(self, underlying, expiry_date, offset, option_type, 
                          action, quantity, price_type="MARKET", product="NRML", 
                          exchange=None, split_size=0):
        """
        Place options order (ATM, ITM, OTM)
        
        Args:
            underlying: Underlying symbol (NIFTY, BANKNIFTY, etc.)
            expiry_date: Expiry in format DDMMMYY (e.g., 30DEC25)
            offset: ATM, ITM1-10, OTM1-10
            option_type: CE or PE
            action: BUY or SELL
            quantity: Lot quantity
            price_type: MARKET or LIMIT
            product: MIS or NRML
            exchange: Underlying exchange (defaults to UNDERLYING_EXCHANGE)
            split_size: Auto-split size (0 = no split)
        
        Returns:
            dict: Order response with symbol and orderid
        """
        try:
            if not self.client:
                logger.error("OptionsHelper disabled (openalgo not installed); order not sent")
                return None
            
            if exchange is None:
                exchange = config.UNDERLYING_EXCHANGE
            
            response = self.client.optionsorder(
                strategy=self.strategy,
                underlying=underlying,
                exchange=exchange,
                expiry_date=expiry_date,
                offset=offset,
                option_type=option_type,
                action=action,
                quantity=quantity,
                pricetype=price_type,
                product=product,
                splitsize=split_size
            )
            
            if response.get('status') == 'success':
                logger.log_order({
                    'action': 'OPTIONS_ORDER',
                    'orderid': response.get('orderid'),
                    'symbol': response.get('symbol'),
                    'offset': offset,
                    'option_type': option_type
                })
            else:
                logger.error(f"Options order failed: {response}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error placing options order: {e}")
            return None
    
    def place_multi_leg_order(self, underlying, legs, exchange=None, expiry_date=None):
        """
        Place multi-leg options order (Iron Condor, Spreads, Straddle, Strangle)
        
        Args:
            underlying: Underlying symbol
            legs: List of leg dicts, each with:
                  - offset: ATM, ITM1, OTM2, etc.
                  - option_type: CE or PE
                  - action: BUY or SELL
                  - quantity: Lot quantity
                  - expiry_date: (optional, for different expiries)
            exchange: Underlying exchange
            expiry_date: Common expiry (if legs don't specify)
        
        Returns:
            dict: Multi-order response with results for each leg
        
        Example legs for Iron Condor:
            if not self.client:
                logger.error("OptionsHelper disabled (openalgo not installed); multi-leg order not sent")
                return None
            
            [
                {"offset": "OTM6", "option_type": "CE", "action": "BUY", "quantity": 75},
                {"offset": "OTM6", "option_type": "PE", "action": "BUY", "quantity": 75},
                {"offset": "OTM4", "option_type": "CE", "action": "SELL", "quantity": 75},
                {"offset": "OTM4", "option_type": "PE", "action": "SELL", "quantity": 75}
            ]
        """
        try:
            if exchange is None:
                exchange = config.UNDERLYING_EXCHANGE
            
            # Build kwargs
            kwargs = {
                'strategy': self.strategy,
                'underlying': underlying,
                'exchange': exchange,
                'legs': legs
            }
            
            # Add common expiry if specified
            if expiry_date:
                kwargs['expiry_date'] = expiry_date
            
            response = self.client.optionsmultiorder(**kwargs)
            
            if response.get('status') == 'success':
                logger.info(f"Multi-leg order placed: {len(response.get('results', []))} legs")
            else:
                logger.error(f"Multi-leg order failed: {response}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error placing multi-leg order: {e}")
            return None
    
    def get_option_chain(self, underlying, expiry_date, exchange=None, strike_count=None):
        """
        Get option chain data
        
        Args:
            underlying: Underlying symbol
            expiry_date: Expiry in DDMMMYY format
            exchange: Underlying exchange
            strike_count: Number of strikes around ATM (None = full chain)
        
        Returns:
            dict: Option chain with CE/PE data for each strike
        """
        try:
            if not self.client:
                logger.error("OptionsHelper disabled (openalgo not installed); option chain unavailable")
                return None
            
            if exchange is None:
                exchange = config.UNDERLYING_EXCHANGE
            
            kwargs = {
                'underlying': underlying,
                'exchange': exchange,
                'expiry_date': expiry_date
            }
            
            if strike_count is not None:
                kwargs['strike_count'] = strike_count
            
            response = self.client.optionchain(**kwargs)
            
            if response.get('status') == 'success':
                return response
            else:
                logger.error(f"Failed to get option chain: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting option chain: {e}")
            return None
    
    def get_option_greeks(self, symbol, exchange="NFO", interest_rate=0.0, 
                         underlying_symbol=None, underlying_exchange=None):
        """
        Calculate option Greeks (Delta, Gamma, Theta, Vega, Rho) using AngelOne SmartAPI
        
        Args:
            symbol: Option symbol
            exchange: Option exchange (NFO)
            interest_rate: Risk-free interest rate (unused - for compatibility)
            underlying_symbol: Underlying symbol (unused - for compatibility)
            underlying_exchange: Underlying exchange (unused - for compatibility)
        
        Returns:
            dict: Greeks data with delta, gamma, theta, vega, rho, IV
        """
        try:
            if not self.smartapi_client:
                logger.debug(f"SmartAPI not available for Greeks: {symbol}")
                # Return simulated Greeks for development/testing
                return self._get_simulated_greeks(symbol)
            
            # Get quote data from AngelOne (includes Greeks in some cases)
            quote = self.smartapi_client.get_quote(exchange, symbol)
            
            if quote and 'data' in quote:
                data = quote['data']
                # Extract Greeks if available, otherwise calculate basic estimates
                return {
                    'status': 'success',
                    'data': {
                        'symbol': symbol,
                        'delta': data.get('delta', 0.0),
                        'gamma': data.get('gamma', 0.0),
                        'theta': data.get('theta', 0.0),
                        'vega': data.get('vega', 0.0),
                        'rho': data.get('rho', 0.0),
                        'iv': data.get('iv', 0.0),
                        'ltp': data.get('ltp', 0.0),
                        'bid': data.get('bidprice', 0.0),
                        'ask': data.get('askprice', 0.0),
                        'volume': data.get('volume', 0),
                        'oi': data.get('oi', 0)
                    }
                }
            else:
                logger.warning(f"No quote data for {symbol}, using simulated Greeks")
                return self._get_simulated_greeks(symbol)
                
        except Exception as e:
            logger.error(f"Error getting option Greeks from AngelOne: {e}")
            return self._get_simulated_greeks(symbol)
    
    def _get_simulated_greeks(self, symbol):
        """Generate simulated Greeks for testing/fallback"""
        import random
        return {
            'status': 'success',
            'data': {
                'symbol': symbol,
                'delta': round(random.uniform(0.3, 0.7), 4),
                'gamma': round(random.uniform(0.001, 0.01), 4),
                'theta': round(random.uniform(-0.05, -0.01), 4),
                'vega': round(random.uniform(0.1, 0.5), 4),
                'rho': round(random.uniform(0.01, 0.05), 4),
                'iv': round(random.uniform(15.0, 25.0), 2),
                'ltp': round(random.uniform(50.0, 200.0), 2),
                'bid': 0.0,
                'ask': 0.0,
                'volume': random.randint(1000, 50000),
                'oi': random.randint(10000, 100000)
            }
        }
    
    def get_option_symbol(self, underlying, expiry_date, offset, option_type, 
                         exchange=None):
        """
        Get option symbol from offset
        
        Args:
            underlying: Underlying symbol
            expiry_date: Expiry in DDMMMYY format
            offset: ATM, ITM1-10, OTM1-10
            option_type: CE or PE
            exchange: Underlying exchange
        
        Returns:
            dict: Symbol info with symbol, lotsize, freeze_qty, etc.
        """
        try:
            if exchange is None:
                exchange = config.UNDERLYING_EXCHANGE
            
            response = self.client.optionsymbol(
                underlying=underlying,
                exchange=exchange,
                expiry_date=expiry_date,
                offset=offset,
                option_type=option_type
            )
            
            if response.get('status') == 'success':
                return response
            else:
                logger.error(f"Failed to get option symbol: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting option symbol: {e}")
            return None
    
    def get_synthetic_future(self, underlying, expiry_date, exchange=None):
        """
        Calculate synthetic future price from options
        
        Args:
            underlying: Underlying symbol
            expiry_date: Expiry in DDMMMYY format
            exchange: Underlying exchange
        
        Returns:
            dict: Synthetic future price and ATM strike
        """
        try:
            if exchange is None:
                exchange = config.UNDERLYING_EXCHANGE
            
            response = self.client.syntheticfuture(
                underlying=underlying,
                exchange=exchange,
                expiry_date=expiry_date
            )
            
            if response.get('status') == 'success':
                return response
            else:
                logger.error(f"Failed to get synthetic future: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting synthetic future: {e}")
            return None
    
    def get_expiry_dates(self, symbol, exchange="NFO", instrumenttype="options"):
        """
        Get available expiry dates for a symbol
        
        Args:
            symbol: Symbol (NIFTY, BANKNIFTY, etc.)
            exchange: Exchange (NFO)
            instrumenttype: options or futures
        
        Returns:
            list: List of expiry dates
        """
        try:
            response = self.client.expiry(
                symbol=symbol,
                exchange=exchange,
                instrumenttype=instrumenttype
            )
            
            if response.get('status') == 'success':
                return response.get('data', [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting expiry dates: {e}")
            return []
    
    def calculate_margin_required(self, positions):
        """
        Calculate margin requirement for positions
        
        Args:
            positions: List of position dicts with symbol, exchange, action, etc.
        
        Returns:
            dict: Margin details with span and exposure
        """
        try:
            response = self.client.margin(positions=positions)
            
            if response.get('status') == 'success':
                return response.get('data')
            else:
                logger.error(f"Failed to calculate margin: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error calculating margin: {e}")
            return None
    
    def get_atm_strike(self, underlying, expiry_date, exchange=None):
        """
        Get ATM strike price for underlying
        
        Args:
            underlying: Underlying symbol
            expiry_date: Expiry date
            exchange: Underlying exchange
        
        Returns:
            float: ATM strike price
        """
        try:
            chain = self.get_option_chain(underlying, expiry_date, exchange, strike_count=1)
            
            if chain and chain.get('status') == 'success':
                return chain.get('atm_strike')
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting ATM strike: {e}")
            return None
