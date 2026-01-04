"""
Angel-X Trading System Version Information
"""

__title__ = "angelx"
__description__ = "Advanced Institutional-Grade Options Trading System"
__version__ = "10.0.0"
__version_info__ = (10, 0, 0)
__author__ = "Angel-X Development Team"
__license__ = "MIT"
__copyright__ = "Copyright 2026 Angel-X Team"

# Phase completion status
PHASE_STATUS = {
    "Phase 1": "✅ Complete - Core Infrastructure",
    "Phase 2": "✅ Complete - Angel One Integration",
    "Phase 3": "✅ Complete - Greeks Engine",
    "Phase 4": "✅ Complete - Smart Money (OI) Engine",
    "Phase 5": "✅ Complete - Market Bias Engine",
    "Phase 6": "✅ Complete - Strike Selection Engine",
    "Phase 7": "✅ Complete - Entry Engine",
    "Phase 8": "✅ Complete - Risk Management",
    "Phase 9": "✅ Complete - Analytics Dashboard",
    "Phase 10": "✅ Complete - Adaptive Learning System"
}

# System capabilities
CAPABILITIES = [
    "Greeks-aware (Real-time Gamma, Delta, Theta, Vega)",
    "OI-driven (Smart Money Conviction Analysis)",
    "Bias-sensitive (Market Direction Detection)",
    "Strike-smart (ATM/ITM/OTM Selection)",
    "Entry-precise (Multi-factor Signal Generation)",
    "Risk-disciplined (Multi-layer Filtering)",
    "Analytics-powered (Real-time Dashboard)",
    "Self-correcting (Adaptive Learning)",
    "Emotion-proof (Confidence-based Decisions)",
    "Market-adaptive (Regime-aware Trading)"
]

# API version
API_VERSION = "v1"

def get_version():
    """Get version string"""
    return __version__

def get_version_info():
    """Get version info tuple"""
    return __version_info__

def get_full_version():
    """Get full version string with phase info"""
    return f"{__title__} v{__version__} - Institutional Trading System"

def print_banner():
    """Print Angel-X banner"""
    banner = f"""
    ╔══════════════════════════════════════════════════════════╗
    ║                    ANGEL-X v{__version__}                      ║
    ║        Advanced Institutional Options Trading System     ║
    ╚══════════════════════════════════════════════════════════╝
    
    Status: Production Ready
    Phases: 10/10 Complete
    System: Self-correcting, Market-adaptive, Risk-disciplined
    
    {chr(10).join(f'    ✓ {cap}' for cap in CAPABILITIES[:5])}
    """
    print(banner)
