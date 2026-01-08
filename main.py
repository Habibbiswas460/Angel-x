"""
ANGEL-X Main Strategy Orchestrator
Coordinates all 9 layers of ANGEL-X system
Optimized for local network with auto-reconnection and monitoring
"""

import signal
import time
import logging
from datetime import datetime, timedelta
from threading import Lock

# Configuration
from config import config
from config.test_config import get_active_config, TestProgression

# Utils
from app.utils.logger import StrategyLogger
from app.integrations.data_feeds.data_feed import DataFeed
from app.utils.trade_journal import TradeJournal
from app.utils.network_resilience import get_network_monitor
from app.engines.greeks.greeks_data_manager import GreeksDataManager

# Engines
from app.engines.market_bias.engine import BiasEngine, BiasState
from app.engines.strike_selection.engine import StrikeSelectionEngine
from app.engines.entry.engine import EntryEngine, EntrySignal
from app.engines.trap_detection.engine import TrapDetectionEngine
from app.engines.portfolio.multi_strike_engine import MultiStrikePortfolioEngine

# Adaptive System (Phase 10)
from app.adaptive.adaptive_controller import AdaptiveController

# Core
from app.core.position_sizing import PositionSizing
from app.core.order_manager import OrderManager, OrderAction, OrderType, ProductType
from app.core.trade_manager import TradeManager
from app.core.expiry_manager import ExpiryManager
from app.utils.options_helper import OptionsHelper
from app.integration_hub import get_integration_hub

logger = StrategyLogger.get_logger(__name__)


class AngelXStrategy:
    """
    ANGEL-X: Professional Options Scalping Strategy
    
    9-Layer Architecture:
    1. Data Ingestion (WebSocket)
    2. Data Normalization & Health Check
    3. Market State Engine (Bias)
    4. Option Selection Engine
    5. Entry Engine (Trigger)
    6. Position Sizing Engine (Risk)
    7. Execution Engine (Orders)
    8. Trade Management Engine (Greek exits)
    9. Daily Risk & Kill-Switch
    """
    
    def __init__(self):
        """Initialize ANGEL-X strategy"""
        logger.info("="*80)
        logger.info("ANGEL-X STRATEGY INITIALIZATION")
        logger.info("="*80)
        
        # Check if running in test mode
        self.test_config = get_active_config()
        if self.test_config:
            test_name = getattr(self.test_config, '__name__', 'Unknown')
            logger.info(f"🧪 TEST MODE ACTIVE: {test_name}")
            logger.info(f"   DEMO_MODE: {getattr(self.test_config, 'DEMO_MODE', False)}")
            logger.info(f"   ORDER_PLACEMENT: {getattr(self.test_config, 'ORDER_PLACEMENT', False)}")
            logger.info("="*80)
        
        # Initialize network monitor for local network resilience
        self.network_monitor = get_network_monitor()
        self.network_monitor.start_monitoring()
        logger.info("Network monitor started - monitoring connectivity and data flow")
        
        # Initialize all components
        self.data_feed = DataFeed()
        self.bias_engine = BiasEngine()
        self.trap_detection = TrapDetectionEngine()
        self.strike_selection = StrikeSelectionEngine()
        self.entry_engine = EntryEngine(self.bias_engine, self.trap_detection)
        self.position_sizing = PositionSizing()
        self.order_manager = OrderManager()
        self.trade_manager = TradeManager()
        self.trade_journal = TradeJournal()
        self.options_helper = OptionsHelper()
        self.multi_strike_engine = MultiStrikePortfolioEngine(self.options_helper)
        self.integration = get_integration_hub()
        
        # Greeks data manager for real-time Greeks and OI
        self.greeks_manager = GreeksDataManager()
        logger.info("Greeks data manager initialized")
        
        # Adaptive Controller (Phase 10) - Self-correcting, Market-aware brain
        adaptive_enabled = getattr(config, 'ADAPTIVE_ENABLED', True)
        self.adaptive = AdaptiveController(config={'adaptive_enabled': adaptive_enabled})
        logger.info(f"Adaptive Controller initialized (enabled={adaptive_enabled})")
        
        # Expiry manager - auto-detect from OpenAlgo
        self.expiry_manager = ExpiryManager()
        self.expiry_manager.refresh_expiry_chain(config.PRIMARY_UNDERLYING)
        
        # Strategy state
        self.running = False
        self.state_lock = Lock()
        self.last_tick_time = None
        
        # Daily limits
        self.daily_start_time = datetime.now()
        self.daily_pnl = 0.0
        self.daily_trades = 0
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("All components initialized successfully")
        logger.info("="*80)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Received shutdown signal")
        self.stop()
    
    def _place_multileg_order(self, entry_context, position, expiry_rules):
        """Place multi-leg options order (straddle/strangle) based on config."""
        try:
            current_exp = self.expiry_manager.get_current_expiry()
            if not current_exp:
                logger.error("No current expiry; cannot place multileg order")
                return None
            
            expiry_date = current_exp.expiry_date
            qty = int(position.quantity * expiry_rules.get('max_position_size_factor', 1.0))
            
            legs = []
            
            if config.MULTILEG_STRATEGY_TYPE == "STRADDLE":
                # ATM CE + ATM PE (long both)
                legs = [
                    {
                        "offset": config.MULTILEG_BUY_LEG_OFFSET,
                        "option_type": "CE",
                        "action": "BUY",
                        "quantity": qty,
                        "pricetype": config.DEFAULT_OPTION_PRICE_TYPE,
                        "product": config.DEFAULT_OPTION_PRODUCT
                    },
                    {
                        "offset": config.MULTILEG_BUY_LEG_OFFSET,
                        "option_type": "PE",
                        "action": "BUY",
                        "quantity": qty,
                        "pricetype": config.DEFAULT_OPTION_PRICE_TYPE,
                        "product": config.DEFAULT_OPTION_PRODUCT
                    }
                ]
                logger.log_order({'type': 'STRADDLE_LEGS', 'legs': legs})
            
            elif config.MULTILEG_STRATEGY_TYPE == "STRANGLE":
                # OTM CE + OTM PE (long both)
                legs = [
                    {
                        "offset": config.MULTILEG_BUY_LEG_OFFSET,
                        "option_type": "CE",
                        "action": "BUY",
                        "quantity": qty,
                        "pricetype": config.DEFAULT_OPTION_PRICE_TYPE,
                        "product": config.DEFAULT_OPTION_PRODUCT
                    },
                    {
                        "offset": config.MULTILEG_BUY_LEG_OFFSET,
                        "option_type": "PE",
                        "action": "BUY",
                        "quantity": qty,
                        "pricetype": config.DEFAULT_OPTION_PRICE_TYPE,
                        "product": config.DEFAULT_OPTION_PRODUCT
                    }
                ]
                logger.log_order({'type': 'STRANGLE_LEGS', 'legs': legs})
            
            if legs:
                order = self.trade_manager.enter_multi_leg_order(
                    underlying=config.PRIMARY_UNDERLYING,
                    legs=legs,
                    expiry_date=expiry_date
                )
                return order
            
            return None
        
        except Exception as e:
            logger.error(f"Error placing multileg order: {e}")
            return None
    
    def start(self):
        """Start the strategy"""
        try:
            logger.info("Starting ANGEL-X strategy...")
            
            # Check demo mode
            if config.DEMO_MODE:
                logger.info("=" * 80)
                logger.info("DEMO MODE ENABLED - Running in simulation")
                logger.info("=" * 80)
                if config.DEMO_SKIP_WEBSOCKET:
                    logger.info("WebSocket connection skipped in demo mode")
                    return True
            
            # Connect to data feed
            if config.WEBSOCKET_ENABLED and not config.DEMO_SKIP_WEBSOCKET:
                logger.info("Connecting to WebSocket...")
                if not self.data_feed.connect():
                    logger.error("Failed to connect to data feed")
                    if not config.DEMO_MODE:
                        return False
                    else:
                        logger.warning("Continuing in demo mode despite connection failure")
                        return True
                
                # Subscribe to LTP
                instruments = [{'exchange': config.UNDERLYING_EXCHANGE, 'symbol': config.PRIMARY_UNDERLYING}]
                self.data_feed.subscribe_ltp(instruments)
                
                logger.info(f"Subscribed to {config.PRIMARY_UNDERLYING} LTP stream")
            
            # Start bias engine
            self.bias_engine.start()
            
            # Start Greeks background refresh if enabled
            if getattr(config, 'GREEKS_BACKGROUND_REFRESH', True) and getattr(config, 'USE_REAL_GREEKS_DATA', True):
                self.greeks_manager.start_background_refresh()
                logger.info("Greeks background refresh started")
            
            # Set running flag
            self.running = True
            
            logger.info("Strategy started successfully")
            logger.info("="*80)
            
            # Main loop
            self._run_loop()
            
        except Exception as e:
            logger.error(f"Error starting strategy: {e}")
            self.stop()
            return False
    
    def _run_loop(self):
        """Main strategy loop"""
        logger.info("Entering main trading loop...")
        
        # Expiry refresh tracking (time-based, following OpenAlgo best practices)
        last_expiry_refresh = 0
        EXPIRY_REFRESH_INTERVAL = 300  # 5 minutes
        
        try:
            while self.running:
                try:
                    # Check daily limits
                    if not self._check_daily_limits():
                        logger.warning("Daily limits exceeded, stopping")
                        self.running = False
                        break
                    
                    # Check trading hours
                    if not self._is_trading_allowed():
                        time.sleep(5)
                        continue
                    
                    # Refresh expiry data every 5 minutes (not every iteration!)
                    current_time = time.time()
                    if current_time - last_expiry_refresh >= EXPIRY_REFRESH_INTERVAL:
                        self.expiry_manager.refresh_expiry_chain(config.PRIMARY_UNDERLYING)
                        expiry_stats = self.expiry_manager.get_expiry_statistics()
                        logger.info(f"✅ Expiry refreshed: {expiry_stats}")
                        last_expiry_refresh = current_time
                    
                    # Get expiry rules (lightweight, can be called every iteration)
                    expiry_rules = self.expiry_manager.apply_expiry_rules()
                    
                    # Get latest market data with freshness check
                    ltp_data = self.data_feed.get_ltp_with_timestamp(config.PRIMARY_UNDERLYING)
                    
                    # 🔴 CHECK DATA FRESHNESS
                    if not ltp_data:
                        logger.warning("❌ NO DATA from broker - waiting for connection")
                        time.sleep(2)
                        continue
                    
                    ltp = ltp_data.get('price', 0)
                    last_tick_time = ltp_data.get('timestamp')
                    
                    # Check if data is stale (older than 5 seconds)
                    if last_tick_time:
                        age_sec = (datetime.now() - last_tick_time).total_seconds()
                        if age_sec > 5:  # config.DATA_FRESHNESS_TOLERANCE
                            logger.error(f"❌ STALE DATA: Last tick {age_sec:.1f}s old - HALTING trades")
                            logger.error(f"   WebSocket may be disconnected. Waiting for fresh data...")
                            time.sleep(3)
                            continue
                    
                    if not ltp or ltp <= 0:
                        logger.warning("Invalid LTP received, waiting...")
                        time.sleep(1)
                        continue
                    
                    # Update market state
                    bias_state = self.bias_engine.get_bias()
                    bias_confidence = self.bias_engine.get_confidence()
                    
                    # Check for entry opportunities
                    active_trades = self.trade_manager.get_active_trades()
                    
                    if len(active_trades) == 0:
                        # Look for entry - USING REAL GREEKS DATA
                        # Get ATM strike and build Greeks data
                        atm_strike = self.strike_selection.get_atm_strike(ltp)
                        current_exp = self.expiry_manager.get_current_expiry()
                        
                        if not current_exp:
                            logger.warning("No current expiry - cannot fetch Greeks")
                            time.sleep(1)
                            continue
                        
                        # Build option symbol
                        current_option_type = "CE" if bias_state.value == "bullish" else "PE"
                        option_symbol = self.expiry_manager.build_order_symbol(
                            atm_strike,
                            current_option_type
                        )
                        
                        # Get real Greeks from API
                        greeks_data = self.greeks_manager.get_greeks(
                            symbol=option_symbol,
                            exchange="NFO",
                            underlying_symbol=config.PRIMARY_UNDERLYING,
                            underlying_exchange=config.UNDERLYING_EXCHANGE,
                            force_refresh=True  # Force refresh for entry decision
                        )
                        
                        # Get previous Greeks for delta/gamma comparison
                        current_greeks, prev_greeks = self.greeks_manager.get_rolling_greeks(option_symbol)
                        
                        # Validate we have real data before proceeding
                        if not greeks_data:
                            logger.warning(f"❌ Failed to get real Greeks for {option_symbol} - SKIPPING entry")
                            time.sleep(2)
                            continue
                        
                        # Extract real values
                        current_delta = greeks_data.delta
                        current_gamma = greeks_data.gamma
                        current_iv = greeks_data.iv
                        current_oi = greeks_data.oi
                        current_ltp = greeks_data.ltp if greeks_data.ltp > 0 else ltp
                        current_volume = greeks_data.volume
                        bid = greeks_data.bid
                        ask = greeks_data.ask
                        
                        # Previous values
                        if prev_greeks:
                            prev_delta = prev_greeks.delta
                            prev_gamma = prev_greeks.gamma
                            prev_iv = prev_greeks.iv
                            prev_oi = prev_greeks.oi
                            prev_ltp = prev_greeks.ltp
                            prev_volume = prev_greeks.volume
                        else:
                            # First time - use current as previous
                            prev_delta = current_delta
                            prev_gamma = current_gamma
                            prev_iv = current_iv
                            prev_oi = current_oi
                            prev_ltp = current_ltp
                            prev_volume = current_volume
                        
                        # Calculate spread percentage
                        current_spread_percent = ((ask - bid) / current_ltp * 100) if current_ltp > 0 else 0
                        oi_change = current_oi - prev_oi
                        
                        logger.info(f"Entry Signal Check for {option_symbol}")
                        logger.info(f"  Greeks: Δ={current_delta:.4f}, Γ={current_gamma:.4f}, IV={current_iv:.2f}%")
                        logger.info(f"  OI: {current_oi} (Δ={oi_change}), Spread: {current_spread_percent:.2f}%")
                        
                        # Entry with REAL Greeks data
                        entry_context = self.entry_engine.check_entry_signal(
                            bias_state=bias_state.value,
                            bias_confidence=bias_confidence,
                            current_delta=current_delta,           # ✅ REAL
                            prev_delta=prev_delta,                 # ✅ REAL
                            current_gamma=current_gamma,           # ✅ REAL
                            prev_gamma=prev_gamma,                 # ✅ REAL
                            current_oi=current_oi,                 # ✅ REAL
                            current_oi_change=oi_change,           # ✅ REAL
                            current_ltp=current_ltp,               # ✅ REAL
                            prev_ltp=prev_ltp,                     # ✅ REAL
                            current_volume=current_volume,         # ✅ REAL
                            prev_volume=prev_volume,               # ✅ REAL
                            current_iv=current_iv,                 # ✅ REAL
                            prev_iv=prev_iv,                       # ✅ REAL
                            bid=bid,                               # ✅ REAL
                            ask=ask,                               # ✅ REAL
                            selected_strike=atm_strike,            # ✅ REAL ATM
                            current_spread_percent=current_spread_percent  # ✅ REAL
                        )
                        
                        if entry_context and entry_context.signal != EntrySignal.NO_SIGNAL:
                            # Validate entry quality
                            if self.entry_engine.validate_entry_quality(entry_context):
                                
                                # 🧠 ADAPTIVE DECISION (Phase 10) - Market-aware filtering
                                if self.adaptive.enabled:
                                    # Prepare market data for regime detection
                                    market_data = {
                                        'vix': current_iv,  # Using current IV as VIX proxy
                                        'higher_highs': bias_state.value == "bullish",
                                        'lower_lows': bias_state.value == "bearish",
                                        'atr_pct': abs(current_ltp - prev_ltp) / prev_ltp * 100 if prev_ltp > 0 else 0,
                                        'price_range_pct': current_spread_percent,
                                        'rate_of_change': (current_ltp - prev_ltp) / prev_ltp if prev_ltp > 0 else 0,
                                        'oi_imbalance': abs(current_oi_change) / current_oi if current_oi > 0 else 0,
                                        'iv_expansion': current_iv > prev_iv,
                                        'volume_surge': current_volume > prev_volume * 1.5
                                    }
                                    
                                    # Prepare signal data for bucket extraction
                                    signal_data = {
                                        'time': datetime.now(),
                                        'bias_strength': bias_confidence,
                                        'oi_conviction': 'HIGH' if current_oi_change > 1000 else 'MEDIUM' if current_oi_change > 500 else 'WEAK',
                                        'gamma': current_gamma,
                                        'theta': entry_context.entry_theta,
                                        'vix': current_iv,
                                        'entry_delta': current_delta
                                    }
                                    
                                    # Get recent trades for confidence scoring
                                    recent_trades = self.trade_manager.get_recent_trades(limit=20)
                                    
                                    # Evaluate signal with adaptive controller
                                    adaptive_decision = self.adaptive.evaluate_signal(
                                        market_data=market_data,
                                        signal_data=signal_data,
                                        recent_trades=recent_trades
                                    )
                                    
                                    if not adaptive_decision.should_trade:
                                        logger.warning(f"🧠 ADAPTIVE SYSTEM BLOCKED TRADE")
                                        logger.warning(f"   Reason: {adaptive_decision.block_reason}")
                                        logger.warning(f"   Regime: {adaptive_decision.regime.regime.value if adaptive_decision.regime else 'UNKNOWN'}")
                                        logger.warning(f"   Confidence: {adaptive_decision.confidence.confidence_level.value if adaptive_decision.confidence else 'UNKNOWN'}")
                                        continue  # Skip this entry
                                    
                                    # Log adaptive approval
                                    logger.info(f"🧠 Adaptive System: APPROVED")
                                    logger.info(f"   Confidence: {adaptive_decision.confidence.confidence_level.value} ({adaptive_decision.confidence.overall_score:.1%})")
                                    logger.info(f"   Regime: {adaptive_decision.regime.regime.value} ({adaptive_decision.regime.confidence:.1%})")
                                    logger.info(f"   Size Adjustment: {adaptive_decision.recommended_size:.0%}")
                                    logger.info(f"   Explanation: {adaptive_decision.decision_explanation}")
                                
                                # Calculate position size
                                position = self.position_sizing.calculate_position_size(
                                    entry_price=entry_context.entry_price,
                                    hard_sl_price=entry_context.entry_price * 0.93,
                                    target_price=entry_context.entry_price * 1.07
                                )
                                
                                if position.sizing_valid:
                                    # Apply adaptive size adjustment if enabled
                                    base_qty = int(position.quantity * expiry_rules.get('max_position_size_factor', 1.0))
                                    if self.adaptive.enabled and 'adaptive_decision' in locals():
                                        adjusted_qty = int(base_qty * adaptive_decision.recommended_size)
                                        logger.info(f"📊 Position size adjusted: {base_qty} → {adjusted_qty} ({adaptive_decision.recommended_size:.0%})")
                                        qty = adjusted_qty
                                    else:
                                        qty = base_qty
                                    
                                    # 🔴 MANDATORY: Check risk manager before entry
                                    # This prevents account blow-up and daily limits
                                    risk_amount = qty * (entry_context.entry_price - position.hard_sl_price)
                                    
                                    # Risk manager check
                                    from app.core.risk_manager import RiskManager
                                    risk_mgr = RiskManager()
                                    can_trade, risk_reason = risk_mgr.can_take_trade({
                                        'quantity': qty,
                                        'risk_amount': risk_amount,
                                        'entry_price': entry_context.entry_price,
                                        'sl_price': position.hard_sl_price
                                    })
                                    
                                    if not can_trade:
                                        logger.warning(f"⚠️  Trade BLOCKED by Risk Manager: {risk_reason}")
                                        logger.warning(f"   Entry: ₹{entry_context.entry_price:.2f}, SL: ₹{position.hard_sl_price:.2f}, Risk: ₹{risk_amount:.2f}")
                                        continue  # Skip this entry
                                    
                                    logger.info(f"✅ Risk Manager: APPROVED")
                                    logger.info(f"   Daily P&L: {risk_mgr.get_daily_pnl():.2f}, Daily Risk: {risk_mgr.get_daily_risk_used():.2f}%")
                                    
                                    # Entry tags for journaling
                                    if hasattr(entry_context, 'entry_reason_tags') and entry_context.entry_reason_tags:
                                        entry_tags = entry_context.entry_reason_tags
                                    elif hasattr(entry_context, 'entry_reason') and entry_context.entry_reason:
                                        entry_tags = [str(entry_context.entry_reason)]
                                    else:
                                        entry_tags = [entry_signal.value if 'entry_signal' in locals() else 'entry']
                                    
                                    current_exp_for_entry = self.expiry_manager.get_current_expiry()
                                    expiry_date_str = current_exp_for_entry.expiry_date if current_exp_for_entry else None
                                    
                                    # Enter trade
                                    trade = self.trade_manager.enter_trade(
                                        underlying=config.PRIMARY_UNDERLYING,
                                        expiry_date=expiry_date_str,
                                        option_type=entry_context.option_type,
                                        strike=entry_context.strike,
                                        entry_price=entry_context.entry_price,
                                        quantity=qty,
                                        entry_delta=entry_context.entry_delta,
                                        entry_gamma=entry_context.entry_gamma,
                                        entry_theta=entry_context.entry_theta,
                                        entry_iv=entry_context.entry_iv,
                                        sl_price=position.hard_sl_price,
                                        target_price=position.target_price,
                                        entry_reason_tags=entry_tags
                                    )

                                    # Multi-strike planning (ATM + hedges) if enabled
                                    if getattr(config, 'USE_MULTI_STRIKE', False):
                                        planned_legs = self.multi_strike_engine.plan_portfolio(
                                            base_strike=entry_context.strike,
                                            option_type=entry_context.option_type
                                        )
                                        logger.info(f"Multi-strike plan: {[f'{leg.option_type} {leg.strike} {leg.action}' for leg in planned_legs]}")
                                    
                                    # Start tracking Greeks for this symbol
                                    if trade and getattr(config, 'USE_REAL_GREEKS_DATA', True):
                                        current_exp = self.expiry_manager.get_current_expiry()
                                        if current_exp:
                                            option_symbol = self.expiry_manager.build_order_symbol(
                                                trade.strike,
                                                trade.option_type
                                            )
                                            self.greeks_manager.track_symbol(option_symbol)
                                            logger.info(f"Started tracking Greeks for {option_symbol}")
                                    
                                    order = None
                                    if config.USE_MULTILEG_STRATEGY:
                                        # Place multi-leg order (straddle/strangle)
                                        order = self._place_multileg_order(entry_context, position, expiry_rules)
                                    else:
                                        # Default: resolve offset and place options order via OrderManager (adapter-aware)
                                        current_exp = self.expiry_manager.get_current_expiry()
                                        if current_exp:
                                            expiry_date = current_exp.expiry_date
                                            offset = self.options_helper.compute_offset(
                                                config.PRIMARY_UNDERLYING,
                                                expiry_date,
                                                entry_context.strike,
                                                entry_context.option_type
                                            )
                                            order = self.order_manager.place_option_order(
                                                strategy=config.STRATEGY_NAME,
                                                underlying=config.PRIMARY_UNDERLYING,
                                                expiry_date=expiry_date,
                                                offset=offset,
                                                option_type=entry_context.option_type,
                                                action=OrderAction.BUY.value,
                                                quantity=int(position.quantity * expiry_rules.get('max_position_size_factor', 1.0)),
                                                pricetype=config.DEFAULT_OPTION_PRICE_TYPE,
                                                product=config.DEFAULT_OPTION_PRODUCT,
                                                splitsize=config.DEFAULT_SPLIT_SIZE
                                            )
                                        else:
                                            logger.error("No current expiry; cannot place options order")
                                        current_exp = self.expiry_manager.get_current_expiry()
                                        order_symbol = None
                                        if current_exp:
                                            expiry_date = current_exp.expiry_date
                                            offset = self.options_helper.compute_offset(
                                                config.PRIMARY_UNDERLYING,
                                                expiry_date,
                                                entry_context.strike,
                                                entry_context.option_type
                                            )
                                            order_symbol = self.expiry_manager.get_option_symbol_by_offset(
                                                underlying=config.PRIMARY_UNDERLYING,
                                                expiry_date=expiry_date,
                                                offset=offset,
                                                option_type=entry_context.option_type
                                            )
                                        if not order_symbol:
                                            # Fallback to manual symbol build
                                            order_symbol = self.expiry_manager.build_order_symbol(
                                                entry_context.strike,
                                                entry_context.option_type
                                            )
                                        order = self.order_manager.place_order(
                                            exchange=config.UNDERLYING_EXCHANGE,
                                            symbol=order_symbol,
                                            action=OrderAction.BUY,
                                            order_type=OrderType.LIMIT,
                                            price=entry_context.entry_price,
                                            quantity=int(position.quantity * expiry_rules.get('max_position_size_factor', 1.0)),
                                            product=ProductType.MIS
                                        )
                                    
                                    # 🔴 VALIDATE ORDER PLACEMENT
                                    if not order:
                                        logger.error(f"❌ Order placement FAILED - returned None")
                                        logger.error(f"   Symbol: {order_symbol}, Price: {entry_context.entry_price}")
                                        # Don't record trade - order wasn't placed
                                        continue
                                    
                                    if isinstance(order, dict) and order.get('status') != 'success':
                                        logger.error(f"❌ Order REJECTED by broker")
                                        logger.error(f"   Error: {order.get('message', 'Unknown error')}")
                                        # Don't record trade - order was rejected
                                        continue
                                    
                                    order_id = order.get('orderid') if isinstance(order, dict) else getattr(order, 'orderid', None)
                                    if not order_id:
                                        logger.error(f"❌ Order placed but NO ORDER ID returned")
                                        logger.error(f"   Cannot track order status")
                                        continue
                                    
                                    # 🟢 ORDER VALIDATED SUCCESSFULLY
                                    logger.info(f"✅ Order placed successfully")
                                    logger.info(f"   Order ID: {order_id}")
                                    logger.info(f"   Symbol: {order_symbol}, Qty: {int(position.quantity)}, Price: ₹{entry_context.entry_price:.2f}")
                    else:
                        # Update active trades with REAL Greeks data
                        for trade in active_trades:
                            # Build option symbol from trade
                            current_exp = self.expiry_manager.get_current_expiry()
                            if not current_exp:
                                logger.warning("No current expiry for Greeks fetch")
                                time.sleep(1)
                                continue
                            
                            option_symbol = self.expiry_manager.build_order_symbol(
                                trade.strike, 
                                trade.option_type
                            )
                            
                            # Get real-time Greeks if enabled
                            if getattr(config, 'USE_REAL_GREEKS_DATA', True):
                                greeks_snapshot = self.greeks_manager.get_greeks(
                                    symbol=option_symbol,
                                    exchange="NFO",
                                    underlying_symbol=config.PRIMARY_UNDERLYING,
                                    underlying_exchange=config.UNDERLYING_EXCHANGE,
                                    force_refresh=False  # Use cache if fresh
                                )
                                
                                if not greeks_snapshot:
                                    logger.error(f"❌ CRITICAL: No Greeks data for {option_symbol} - SKIPPING trade update")
                                    logger.error(f"   This prevents decision-making with fake data. Trade will be checked next iteration.")
                                    # SKIP this trade update - don't manage with fake OI
                                    continue
                                else:
                                    # Get previous Greeks for delta tracking
                                    current_greeks, prev_greeks = self.greeks_manager.get_rolling_greeks(option_symbol)
                                    
                                    # Extract current values
                                    current_delta = greeks_snapshot.delta
                                    current_gamma = greeks_snapshot.gamma
                                    current_theta = greeks_snapshot.theta
                                    current_iv = greeks_snapshot.iv
                                    current_price = greeks_snapshot.ltp if greeks_snapshot.ltp > 0 else ltp
                                    current_oi = greeks_snapshot.oi
                                    
                                    # Get previous values
                                    if prev_greeks:
                                        prev_delta = prev_greeks.delta
                                        prev_gamma = prev_greeks.gamma
                                        prev_oi = prev_greeks.oi
                                        prev_price = prev_greeks.ltp
                                    else:
                                        prev_delta = current_delta
                                        prev_gamma = current_gamma
                                        prev_oi = current_oi
                                        prev_price = current_price
                            else:
                                # Use dummy values (old behavior for testing)
                                current_delta = 0.5
                                current_gamma = 0.005
                                current_theta = 0
                                current_iv = 25.0
                                current_price = ltp
                                current_oi = 1000
                                prev_oi = 900
                                prev_price = ltp * 0.99
                            
                            # Update trade with real or fallback data
                            exit_reason = self.trade_manager.update_trade(
                                trade,
                                current_price=current_price,
                                current_delta=current_delta,
                                current_gamma=current_gamma,
                                current_theta=current_theta,
                                current_iv=current_iv,
                                current_oi=current_oi,
                                prev_oi=prev_oi,
                                prev_price=prev_price,
                                expiry_rules=expiry_rules
                            )
                            
                            if exit_reason:
                                # Exit order execution (paper/live aware)
                                exit_order = None
                                try:
                                    exit_order = self.trade_manager.execute_exit_order(trade, option_symbol, current_price)
                                    if exit_order and isinstance(exit_order, dict) and exit_order.get('status') not in (None, 'success'):
                                        logger.warning(f"⚠️ Exit order response indicates failure: {exit_order}")
                                except Exception as exit_exc:
                                    logger.error(f"Exit order execution failed: {exit_exc}")
                                
                                # Exit trade with final snapshot
                                self.trade_manager.exit_trade(
                                    trade,
                                    exit_reason,
                                    exit_price=current_price,
                                    exit_delta=current_delta,
                                    exit_gamma=current_gamma,
                                    exit_theta=current_theta,
                                    exit_iv=current_iv
                                )
                                
                                # 🧠 Record trade outcome for adaptive learning (Phase 10)
                                if self.adaptive.enabled:
                                    try:
                                        holding_minutes = (trade.exit_time - trade.entry_time).total_seconds() / 60
                                        self.adaptive.record_trade_outcome({
                                            'entry_time': trade.entry_time,
                                            'exit_time': trade.exit_time,
                                            'bias_strength': bias_confidence,
                                            'oi_conviction': 'HIGH' if abs(current_oi - prev_oi) > 1000 else 'MEDIUM' if abs(current_oi - prev_oi) > 500 else 'WEAK',
                                            'gamma': trade.entry_gamma,
                                            'theta': trade.entry_theta,
                                            'vix': current_iv,
                                            'exit_reason': exit_reason,
                                            'holding_minutes': holding_minutes,
                                            'won': trade.pnl > 0,
                                            'pnl': trade.pnl
                                        })
                                        logger.info(f"🧠 Trade outcome recorded for adaptive learning")
                                    except Exception as e:
                                        logger.error(f"Failed to record trade outcome: {e}")
                                
                                # Stop tracking Greeks for this symbol
                                if getattr(config, 'USE_REAL_GREEKS_DATA', True):
                                    self.greeks_manager.untrack_symbol(option_symbol)
                                    logger.info(f"Stopped tracking Greeks for {option_symbol}")
                                
                                # Log to journal with real timestamps and greeks snapshot
                                self.trade_journal.log_trade(
                                    underlying=trade.underlying,
                                    strike=trade.strike,
                                    option_type=trade.option_type,
                                    expiry_date=trade.expiry_date or "unknown",
                                    entry_price=trade.entry_price,
                                    exit_price=trade.exit_price,
                                    qty=trade.quantity,
                                    entry_delta=trade.entry_delta,
                                    entry_gamma=trade.entry_gamma,
                                    entry_theta=trade.entry_theta,
                                    entry_vega=0,
                                    entry_iv=trade.entry_iv,
                                    exit_delta=trade.exit_delta,
                                    exit_gamma=trade.exit_gamma,
                                    exit_theta=trade.exit_theta,
                                    exit_vega=0,
                                    exit_iv=trade.exit_iv,
                                    entry_spread=0.5,
                                    exit_spread=0.5,
                                    entry_reason_tags=trade.entry_reason_tags,
                                    exit_reason_tags=trade.exit_reason_tags or [exit_reason],
                                    original_sl_price=trade.sl_price,
                                    original_sl_percent=7.0,
                                    original_target_price=trade.target_price,
                                    original_target_percent=7.0,
                                    entry_time=trade.entry_time,
                                    exit_time=trade.exit_time
                                )
                                
                                self.daily_pnl += trade.pnl
                                self.daily_trades += 1
                    
                    # Sync dashboard/analytics once per loop
                    if getattr(config, 'DASHBOARD_ENABLED', True):
                        try:
                            self.integration.update_position_data(self.trade_manager, self.greeks_manager)
                        except Exception as dash_exc:
                            logger.error(f"Dashboard sync failed: {dash_exc}")

                    time.sleep(1)
                
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    time.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self.stop()
    
    def _check_daily_limits(self) -> bool:
        """Check if daily limits are exceeded"""
        # Check max daily loss
        if self.daily_pnl < -config.MAX_DAILY_LOSS_AMOUNT:
            logger.warning(f"Daily loss limit exceeded: ₹{self.daily_pnl:.2f}")
            return False
        
        # Check max trades
        if self.daily_trades >= config.MAX_TRADES_PER_DAY:
            logger.warning(f"Daily trade limit reached: {self.daily_trades}")
            return False
        
        return True
    
    def _is_trading_allowed(self) -> bool:
        """Check if trading is allowed at this time"""
        now = datetime.now().time()
        
        start_time = datetime.strptime(config.TRADING_SESSION_START, "%H:%M").time()
        end_time = datetime.strptime(config.TRADING_SESSION_END, "%H:%M").time()
        
        if not (start_time <= now <= end_time):
            return False
        
        return True
    
    def stop(self):
        """Stop the strategy"""
        logger.info("Stopping ANGEL-X strategy...")
        
        self.running = False
        
        # Close all positions
        active_trades = self.trade_manager.get_active_trades()
        for trade in active_trades:
            self.trade_manager.exit_trade(trade, "strategy_stop")
        
        # Disconnect and cleanup
        self.bias_engine.stop()
        self.data_feed.disconnect()
        
        # Stop Greeks manager and print stats
        if hasattr(self, 'greeks_manager'):
            self.greeks_manager.stop_background_refresh()
            stats = self.greeks_manager.get_stats()
            logger.info("Greeks Data Manager Stats:")
            logger.info(f"  API Calls: {stats['api_calls_total']}")
            logger.info(f"  Cache Hit Rate: {stats['cache_hit_rate']:.1f}%")
            logger.info(f"  Active Symbols: {stats['active_symbols']}")
            logger.info(f"  Cached Symbols: {stats['cached_symbols']}")
        
        # Stop network monitoring
        if hasattr(self, 'network_monitor'):
            logger.info("Network Health Summary:")
            health = self.network_monitor.get_health_status()
            logger.info(f"  API Calls: {health['api_calls']}")
            logger.info(f"  API Errors: {health['api_errors']} ({health['api_error_rate']:.1%})")
            logger.info(f"  WebSocket Reconnects: {health['websocket_reconnects']}")
            logger.info(f"  Alerts: {health['alerts_count']}")
            self.network_monitor.stop_monitoring()
        
        # 🧠 Run EOD adaptive learning (Phase 10)
        if hasattr(self, 'adaptive') and self.adaptive.enabled:
            logger.info("="*80)
            logger.info("RUNNING EOD ADAPTIVE LEARNING")
            logger.info("="*80)
            try:
                summary = self.adaptive.run_daily_learning()
                logger.info(f"🧠 Adaptive Learning Complete:")
                logger.info(f"   Insights Generated: {summary['insights_generated']}")
                logger.info(f"   Loss Patterns Detected: {summary['loss_patterns_detected']}")
                logger.info(f"   Proposals Created: {summary['proposals_created']}")
                logger.info(f"   Proposals Approved: {summary['proposals_approved']}")
                logger.info(f"   Proposals Rejected: {summary['proposals_rejected']}")
                
                # Export adaptive state
                import os
                os.makedirs('logs/adaptive', exist_ok=True)
                state_file = f"logs/adaptive/state_{datetime.now().strftime('%Y%m%d')}.json"
                self.adaptive.export_state(state_file)
                logger.info(f"   State exported to: {state_file}")
                
                # Show adaptive status
                status = self.adaptive.get_adaptive_status()
                logger.info(f"🌍 Market Regime: {status['regime']['regime']} ({status['regime']['confidence']:.1%})")
                logger.info(f"📚 Total Trades Learned: {status['learning']['total_trades']}")
                logger.info(f"🚫 Active Blocks: {status['patterns']['active_blocks']}")
                
            except Exception as e:
                logger.error(f"EOD adaptive learning failed: {e}")
            logger.info("="*80)
        
        # Print summary
        stats = self.trade_manager.get_trade_statistics()
        logger.info("="*80)
        logger.info("STRATEGY STOPPED - DAILY SUMMARY")
        logger.info("="*80)
        logger.info(f"Total Trades: {stats['total']}")
        logger.info(f"Wins: {stats['wins']} | Losses: {stats['losses']}")
        logger.info(f"Win Rate: {stats['win_rate']:.2f}%")
        logger.info(f"Total P&L: ₹{stats['total_pnl']:.2f}")
        logger.info(f"Daily P&L: ₹{self.daily_pnl:.2f}")
        logger.info("="*80)
        
        # Export summary
        self.trade_journal.print_daily_summary()
        self.trade_journal.export_summary_report()


def main():
    """Main entry point"""
    strategy = AngelXStrategy()
    strategy.start()


if __name__ == "__main__":
    main()
