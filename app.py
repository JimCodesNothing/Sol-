import streamlit as st
import pandas as pd
import requests
import warnings
from datetime import datetime, timedelta
import time
import json

warnings.filterwarnings('ignore')

# ==============================================================================
# STREAMLIT PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="🚀 Degen Solana Hunter V4.0",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for degen aesthetics
st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #FF4B4B; text-align: center;}
    .sub-header {font-size: 1.2rem; color: #FFA500; text-align: center; margin-bottom: 2rem;}
    .gem-card {background-color: #1E1E1E; padding: 1rem; border-radius: 0.5rem; border-left: 5px solid #FF4B4B;}
    .risk-flag {color: #FF4B4B; font-weight: bold;}
    .bullish-signal {color: #00FF00; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# CORE HUNTER ENGINE (Cleaned & Fixed)
# ==============================================================================
class SolanaMemecoinHunter:
    def __init__(self, min_liquidity=5000, max_age_hours=72):
        self.min_liquidity = min_liquidity
        self.max_age_hours = max_age_hours
        self.dexscreener_base = "https://api.dexscreener.com/latest/dex"

    def get_trending_solana_tokens(self):
        """Get trending Solana tokens from DexScreener (Free, No API Key)"""
        try:
            url = f"{self.dexscreener_base}/trending"
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return []
            
            data = response.json()
            pairs = data.get('pairs', [])
            
            # Filter for Solana only
            solana_tokens = [pair for pair in pairs if pair.get('chainId') == 'solana']
            return solana_tokens
        except Exception:
            return []

    def detect_memecoin_signals(self, pair_data):
        """Detect memecoin characteristics and assign a Degen Score"""
        signals = []
        risk_flags = []
        score = 0

        name = pair_data.get('baseToken', {}).get('name', 'Unknown')
        symbol = pair_data.get('baseToken', {}).get('symbol', 'UNK')
        name_lower = name.lower()
        symbol_lower = symbol.lower()

        # 1. MEMECOIN NAME/SYMBOL DETECTION
        memecoin_keywords = ['doge', 'pepe', 'shib', 'floki', 'inu', 'elon', 'moon', 'safe',
                             'baby', 'mini', 'rocket', 'ponzi', 'trump', 'biden', 'wojak', 
                             'bonk', 'samo', 'cheems', 'cope', 'giga', 'based', 'sigma',
                             'meme', 'frog', 'cat', 'dog', 'puppy', 'wif', 'hat']
        
        is_memecoin = any(keyword in name_lower or keyword in symbol_lower for keyword in memecoin_keywords)
        if is_memecoin:
            score += 20
            signals.append("🎭 Memecoin narrative detected")

        # 2. PRICE ACTION ANALYSIS
        price_change_5m = float(pair_data.get('priceChange', {}).get('m5', 0) or 0)
        price_change_1h = float(pair_data.get('priceChange', {}).get('h1', 0) or 0)
        price_change_24h = float(pair_data.get('priceChange', {}).get('h24', 0) or 0)

        if price_change_5m > 20:
            score += 15
            signals.append(f"🚀 Strong 5m pump: +{price_change_5m:.1f}%")
        if 10 < price_change_1h < 50:
            score += 15
            signals.append(f"🌱 Early stage pump: +{price_change_1h:.1f}% (1h)")

        # 3. VOLUME & LIQUIDITY
        volume_24h = float(pair_data.get('volume', {}).get('h24', 0) or 0)
        liquidity_usd = float(pair_data.get('liquidity', {}).get('usd', 0) or 0)

        if liquidity_usd > 0:
            vol_to_liq_ratio = volume_24h / liquidity_usd
            if vol_to_liq_ratio > 5:
                score += 15
                signals.append(f"💸 High volume: {vol_to_liq_ratio:.1f}x liquidity")
        
        if liquidity_usd < 2000:
            risk_flags.append("🚩 EXTREME LOW LIQ: < $2k (High Rug Risk)")
            score -= 20
        elif liquidity_usd > 20000:
            score += 10
            signals.append(f"✅ Healthy liquidity: ${liquidity_usd:,.0f}")

        # 4. TRANSACTION PRESSURE
        txns_5m = pair_data.get('txns', {}).get('m5', {})
        buys_5m = txns_5m.get('buys', 0)
        sells_5m = txns_5m.get('sells', 0)

        if buys_5m + sells_5m > 0:
            buy_pressure = buys_5m / (buys_5m + sells_5m)
            if buy_pressure > 0.75 and buys_5m > 15:
                score += 15
                signals.append(f"🐋 Heavy buy pressure: {buy_pressure*100:.0f}% buys (5m)")

        # 5. AGE CHECK
        created_at = pair_data.get('pairCreatedAt')
        age_hours = 999
        if created_at:
            age_hours = (datetime.now().timestamp() * 1000 - created_at) / (1000 * 3600)
            if age_hours < 1:
                score += 15
                signals.append(f"🆕 Brand new: {age_hours*60:.0f} minutes old")
            elif age_hours < 6:
                score += 10
                signals.append(f"🌟 Very new: {age_hours:.1f}h old")

        # 6. FREE RUG-CHECK PROXIES
        info = pair_data.get('info', {})
        if not info.get('twitter') and not info.get('telegram') and not info.get('website'):
            risk_flags.append("⚠️ No social links detected (Anonymous dev)")
        
        if price_change_24h < -50:
            risk_flags.append("🔴 Down 50%+ today (Potential death spiral)")

        return {
            'score': max(0, min(100, score)), # Cap at 100
            'signals': signals,
            'risk_flags': risk_flags,
            'is_memecoin': is_memecoin,
            'price_change_5m': price_change_5m,
            'price_change_1h': price_change_1h,
            'price_change_24h': price_change_24h,
            'volume_24h': volume_24h,
            'liquidity_usd': liquidity_usd,
            'buys_5m': buys_5m,
            'sells_5m': sells_5m,
            'age_hours': age_hours
        }

    def scan_for_gems(self, max_tokens=30):
        """Main scanning function"""
        trending_tokens = self.get_trending_solana_tokens()
        results = []
        seen_addresses = set()

        for pair in trending_tokens:
            if len(results) >= max_tokens:
                break
                
            addr = pair.get('baseToken', {}).get('address')
            if not addr or addr in seen_addresses:
                continue
            seen_addresses.add(addr)

            # Skip major tokens
            symbol = pair.get('baseToken', {}).get('symbol', '').upper()
            if symbol in ['USDC', 'USDT', 'SOL', 'WSOL', 'WETH', 'WBTC', 'JUP']:
                continue

            analysis = self.detect_memecoin_signals(pair)
            
            if analysis['liquidity_usd'] < self.min_liquidity:
                continue

            current_price = float(pair.get('priceUsd', 0) or 0)
            
            # Degen Entry/Exit Logic
            entry = current_price
            stop_loss = entry * 0.80
            tp1, tp2, tp3, tp4 = entry * 1.5, entry * 2.5, entry * 5.0, entry * 10.0

            result = {
                'symbol': symbol,
                'name': pair.get('baseToken', {}).get('name', 'Unknown'),
                'address': addr,
                'pair_address': pair.get('pairAddress', ''),
                'price': current_price,
                'score': analysis['score'],
                'is_memecoin': analysis['is_memecoin'],
                'signals': analysis['signals'],
                'risk_flags': analysis['risk_flags'],
                'price_change_1h': analysis['price_change_1h'],
                'price_change_24h': analysis['price_change_24h'],
                'liquidity_usd': analysis['liquidity_usd'],
                'volume_24h': analysis['volume_24h'],
                'buy_pressure_5m': round((analysis['buys_5m'] / (analysis['buys_5m'] + analysis['sells_5m'])) * 100, 1) if (analysis['buys_5m'] + analysis['sells_5m']) > 0 else 50.0,
                'age_hours': analysis['age_hours'],
                'url': pair.get('url', ''),
                'stop_loss': stop_loss,
                'tp1': tp1, 'tp2': tp2, 'tp3': tp3, 'tp4': tp4
            }
            results.append(result)
            time.sleep(0.3) # Respect rate limits

        results.sort(key=lambda x: x['score'], reverse=True)
        return results

# ==============================================================================
# STREAMLIT UI LAYOUT
# ==============================================================================
st.markdown('<div class="main-header">💎 DEGEN SOLANA HUNTER V4.0 💎</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Ultimate free system for finding 100x Solana memecoins before they moon 🚀</div>', unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.header("⚙️ Degen Configuration")
min_liq = st.sidebar.slider("Min Liquidity ($)", 1000, 100000, 10000, step=1000)
max_age = st.sidebar.slider("Max Age (Hours)", 1, 168, 72)
max_tokens = st.sidebar.slider("Tokens to Scan", 10, 100, 30)

st.sidebar.markdown("---")
st.sidebar.info("**How it works:**\n1. Fetches trending Solana pairs from DexScreener (Free API).\n2. Scores them on volume, buy pressure, age, and narrative.\n3. Flags rug risks (low liq, no socials, death spirals).")

# Main Execution Area
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    scan_button = st.button("🔥 START GEM HUNT", type="primary", use_container_width=True)

if scan_button:
    with st.spinner("🔍 Scanning Solana DEXs for trending tokens... This may take 10-20 seconds."):
        hunter = SolanaMemecoinHunter(min_liquidity=min_liq, max_age_hours=max_age)
        gems = hunter.scan_for_gems(max_tokens=max_tokens)
        st.session_state['gems'] = gems

if 'gems' in st.session_state and st.session_state['gems']:
    gems = st.session_state['gems']
    
    # Top Metrics
    st.markdown("### 🏆 Top Opportunities")
    cols = st.columns(3)
    cols[0].metric("Total Gems Found", len(gems))
    high_conviction = [g for g in gems if g['score'] >= 70]
    cols[1].metric("High Conviction (70+)", len(high_conviction))
    avg_liq = sum(g['liquidity_usd'] for g in gems) / len(gems) if gems else 0
    cols[2].metric("Avg Liquidity", f"${avg_liq:,.0f}")

    st.markdown("---")

    # Detailed Gem Cards
    for i, gem in enumerate(gems[:15], 1): # Show top 15 to avoid overwhelming the UI
        score_color = "🔴" if gem['score'] < 50 else "🟡" if gem['score'] < 70 else "🟢"
        
        with st.expander(f"#{i} {score_color} **${gem['symbol']}** - {gem['name']} | Score: **{gem['score']}/100** | Liq: **${gem['liquidity_usd']:,.0f}**", expanded=(i <= 3)):
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown(f"**Contract:** `{gem['address']}`")
                st.markdown(f"**Price:** `${gem['price']:.10f}`")
                st.markdown(f"**Age:** `{gem['age_hours']:.1f}` hours")
                st.markdown(f"**24h Volume:** `${gem['volume_24h']:,.0f}`")
            
            with col_b:
                st.markdown("**📈 Price Action:**")
                st.markdown(f"• 1h: `{'+' if gem['price_change_1h'] > 0 else ''}{gem['price_change_1h']:.2f}%`")
                st.markdown(f"• 24h: `{'+' if gem['price_change_24h'] > 0 else ''}{gem['price_change_24h']:.2f}%`")
                st.markdown(f"**🐋 Buy Pressure (5m):** `{gem['buy_pressure_5m']:.1f}%`")

            st.markdown("---")
            
            # Signals & Risks
            col_risk, col_bull = st.columns(2)
            with col_risk:
                st.markdown("**⚠️ Risk Flags:**")
                if gem['risk_flags']:
                    for flag in gem['risk_flags']:
                        st.markdown(f"<span class='risk-flag'>• {flag}</span>", unsafe_allow_html=True)
                else:
                    st.markdown("✅ No major red flags detected.")
            
            with col_bull:
                st.markdown("**✅ Bullish Signals:**")
                if gem['signals']:
                    for sig in gem['signals']:
                        st.markdown(f"<span class='bullish-signal'>• {sig}</span>", unsafe_allow_html=True)
                else:
                    st.markdown("No strong bullish signals.")

            # Entry/Exit Plan
            st.markdown("**🎯 Degen Entry/Exit Plan:**")
            plan_cols = st.columns(5)
            plan_cols[0].metric("Entry", f"${gem['price']:.8f}")
            plan_cols[1].metric("Stop Loss", f"${gem['stop_loss']:.8f}", "-20%")
            plan_cols[2].metric("TP1 (50%)", f"${gem['tp1']:.8f}", "+50%")
            plan_cols[3].metric("TP2 (150%)", f"${gem['tp2']:.8f}", "+150%")
            plan_cols[4].metric("TP3 (400%)", f"${gem['tp3']:.8f}", "+400%")

            st.markdown(f"[🔗 View on DexScreener]({gem['url']}) | [🔍 View Contract on Solscan](https://solscan.io/token/{gem['address']})")

    # Export to CSV
    st.markdown("---")
    st.markdown("### 📥 Export Data")
    df = pd.DataFrame(gems)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Gems as CSV",
        data=csv,
        file_name=f"solana_gems_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

else:
    st.info("👈 Configure your settings in the sidebar and click **START GEM HUNT** to begin scanning.")

# Footer Disclaimer
st.markdown("---")
st.markdown("""
<div style="background-color: #2b0000; padding: 1.5rem; border-radius: 0.5rem; border: 1px solid #FF4B4B;">
    <h3 style="color: #FF4B4B; margin-top: 0;">⚠️ ULTIMATE DEGEN DISCLAIMER</h3>
    <ul style="color: #FFCCCC; line-height: 1.6;">
        <li><strong>This is a free, educational tool.</strong> It uses public DexScreener data. It does NOT check on-chain mint/freeze authority (requires paid RPC).</li>
        <li><strong>90%+ of memecoins go to ZERO.</strong> You will get rugged. Multiple times.</li>
        <li><strong>Never invest money you cannot afford to lose completely.</strong> This is gambling, not investing.</li>
        <li><strong>Always verify contracts</strong> on Solscan or RugCheck.xyz before buying.</li>
        <li><strong>Take profits on the way up.</strong> Memecoins can dump 99% in minutes.</li>
    </ul>
    <p style="color: #FFCCCC; font-weight: bold; text-align: center; margin-bottom: 0;">DYOR. NFA. Trade responsibly. 🫡</p>
</div>
""", unsafe_allow_html=True)
