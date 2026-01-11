"""
Angel-X Trading System Version Information
"""

__title__ = "angelx"
__description__ = "Advanced Institutional-Grade Options Trading System"
__version__ = "1.0.0"
__version_info__ = (1, 0, 0)
__author__ = "Angel-X Development Team"
__license__ = "MIT"
__copyright__ = "Copyright 2026 Angel-X Team"

# System components status
SYSTEM_STATUS = {
    "Core Infrastructure": "✅ Complete",
    "AngelOne Integration": "✅ Complete",
    "Greeks Engine": "✅ Complete",
    "Smart Money Analysis": "✅ Complete",
    "Market Bias Engine": "✅ Complete",
    "Strike Selection": "✅ Complete",
    "Entry Signal Generator": "✅ Complete",
    "Risk Management": "✅ Complete",
    "Analytics Dashboard": "✅ Complete",
    "Adaptive Learning": "✅ Complete"
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
    System: Self-correcting, Market-adaptive, Risk-disciplined
    
    {chr(10).join(f'    ✓ {cap}' for cap in CAPABILITIES[:5])}
    """
    print(banner)
