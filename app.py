import streamlit as st
import pandas as pd
import requests
import warnings
from datetime import datetime
import time

warnings.filterwarnings('ignore')

# ==============================================================================
# STREAMLIT PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="🚀 Degen Solana Hunter V4.2",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #FF4B4B; text-align: center;}
    .sub-header {font-size: 1.2rem; color: #FFA500; text-align: center; margin-bottom: 2rem;}
    .risk-flag {color: #FF4B4B; font-weight: bold;}
    .bullish-signal {color: #00FF00; font-weight: bold;}
    .debug-box {background-color: #1a1a1a; padding: 1rem; border-radius: 0.5rem; font-family: monospace; font-size: 0.9rem;}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# CORE HUNTER ENGINE (Fixed Search Logic)
# ==============================================================================
class SolanaMemecoinHunter:
    def __init__(self, min_liquidity=1000, max_age_hours=72, debug_mode=False):
        self.min_liquidity = min_liquidity
        self.max_age_hours = max_age_hours
        self.debug_mode = debug_mode
        self.dexscreener_base = "https://api.dexscreener.com/latest/dex"

    def test_connection(self):
        """Test if DexScreener API is reachable"""
        try:
            url = f"{self.dexscreener_base}/search?q=SOL"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(url, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def get_trending_solana_tokens(self):
        """Get trending Solana tokens using multiple search queries"""
        all_pairs = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        # Search for popular Solana terms
        search_queries = ['SOL', 'RAY', 'ORCA', 'JUP', 'BONK', 'WIF', 'PEPE']
        
        for query in search_queries:
            try:
                url = f"{self.dexscreener_base}/search?q={query}"
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    pairs = data.get('pairs', [])
                    
                    # Filter for Solana chain only
                    for pair in pairs:
                        if pair.get('chainId') == 'solana':
                            all_pairs.append(pair)
                
                time.sleep(0.3)  # Rate limiting
            except Exception as e:
                if self.debug_mode:
                    st.warning(f"Failed to fetch {query}: {e}")
        
        # Remove duplicates based on pair address
        unique_pairs = {}
        for pair in all_pairs:
            pair_addr = pair.get('pairAddress')
            if pair_addr and pair_addr not in unique_pairs:
                unique_pairs[pair_addr] = pair
        
        # Sort by 24h volume (descending)
        sorted_pairs = sorted(
            unique_pairs.values(),
            key=lambda x: float(x.get('volume', {}).get('h24', 0) or 0),
            reverse=True
        )
        
        if self.debug_mode:
            st.info(f"🔍 Found {len(sorted_pairs)} unique Solana pairs from {len(search_queries)} search queries")
        
        return sorted_pairs

    def detect_memecoin_signals(self, pair_data):
        """Detect memecoin characteristics and assign a Degen Score"""
        signals = []
        risk_flags = []
        score = 0

        base_token = pair_data.get('baseToken', {}) or {}
        name = base_token.get('name', 'Unknown')
        symbol = base_token.get('symbol', 'UNK')
        name_lower = str(name).lower()
        symbol_lower = str(symbol).lower()

        # 1. MEMECOIN NARRATIVE DETECTION
        memecoin_keywords = ['doge', 'pepe', 'shib', 'floki', 'inu', 'elon', 'moon', 'safe',
                             'baby', 'mini', 'rocket', 'ponzi', 'trump', 'biden', 'wojak', 
                             'bonk', 'samo', 'cheems', 'cope', 'giga', 'based', 'sigma',
                             'meme', 'frog', 'cat', 'dog', 'puppy', 'wif', 'hat', 'cat']
        
        is_memecoin = any(keyword in name_lower or keyword in symbol_lower for keyword in memecoin_keywords)
        if is_memecoin:
            score += 20
            signals.append("🎭 Memecoin narrative detected")

        # 2. PRICE ACTION ANALYSIS (Null-safe)
        price_change = pair_data.get('priceChange', {}) or {}
        price_change_5m = float(price_change.get('m5', 0) or 0)
        price_change_1h = float(price_change.get('h1', 0) or 0)
        price_change_24h = float(price_change.get('h24', 0) or 0)

        if price_change_5m > 20:
            score += 15
            signals.append(f"🚀 Strong 5m pump: +{price_change_5m:.1f}%")
        if 10 < price_change_1h < 50:
            score += 15
            signals.append(f"🌱 Early stage pump: +{price_change_1h:.1f}% (1h)")

        # 3. VOLUME & LIQUIDITY
        volume = pair_data.get('volume', {}) or {}
        liquidity = pair_data.get('liquidity', {}) or {}
        volume_24h = float(volume.get('h24', 0) or 0)
        liquidity_usd = float(liquidity.get('usd', 0) or 0)

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
        txns = pair_data.get('txns', {}) or {}
        txns_5m = txns.get('m5', {}) or {}
        buys_5m = int(txns_5m.get('buys', 0) or 0)
        sells_5m = int(txns_5m.get('sells', 0) or 0)

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
            elif age_hours > self.max_age_hours:
                score -= 15

        # 6. FREE RUG-CHECK PROXIES
        info = pair_data.get('info', {}) or {}
        if not info.get('twitter') and not info.get('telegram') and not info.get('website'):
            risk_flags.append("⚠️ No social links detected (Anonymous dev)")
        
        if price_change_24h < -50:
            risk_flags.append("🔴 Down 50%+ today (Potential death spiral)")

        return {
            'score': max(0, min(100, score)),
            'signals': signals,
            'risk_flags': risk_flags,
            'is_memecoin': is_memecoin,
            'price_change_1h': price_change_1h,
            'price_change_24h': price_change_24h,
            'volume_24h': volume_24h,
            'liquidity_usd': liquidity_usd,
            'buys_5m': buys_5m,
            'sells_5m': sells_5m,
            'age_hours': age_hours
        }

    def scan_for_gems(self, max_tokens=30, progress_bar=None, status_text=None):
        """Main scanning function with debug output"""
        if status_text:
            status_text.text("🔍 Fetching Solana pairs from DexScreener...")
        
        trending_tokens = self.get_trending_solana_tokens()
        
        if not trending_tokens:
            if self.debug_mode:
                st.error("❌ No pairs found from API. This could be a rate limit or network issue.")
            return []
        
        if status_text:
            status_text.text(f"📊 Analyzing {len(trending_tokens)} pairs...")
        
        results = []
        seen_addresses = set()
        filtered_count = 0
        major_token_count = 0
        low_liq_count = 0

        for i, pair in enumerate(trending_tokens):
            if progress_bar:
                progress_bar.progress(min(1.0, (i + 1) / len(trending_tokens)))
                
            if len(results) >= max_tokens:
                break
                
            addr = pair.get('baseToken', {}).get('address')
            if not addr or addr in seen_addresses:
                continue
            seen_addresses.add(addr)

            # Skip major tokens
            symbol = str(pair.get('baseToken', {}).get('symbol', '')).upper()
            if symbol in ['USDC', 'USDT', 'SOL', 'WSOL', 'WETH', 'WBTC', 'JUP', 'RAY', 'PYTH', 'ORCA', 'MSOL']:
                major_token_count += 1
                continue

            analysis = self.detect_memecoin_signals(pair)
            
            if analysis['liquidity_usd'] < self.min_liquidity:
                low_liq_count += 1
                continue

            current_price = float(pair.get('priceUsd', 0) or 0)
            if current_price == 0:
                continue
            
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
            time.sleep(0.2)

        results.sort(key=lambda x: x['score'], reverse=True)
        
        if self.debug_mode:
            st.markdown(f"""
            <div class="debug-box">
            <strong>🔍 Scan Debug Info:</strong><br>
            • Total pairs fetched: {len(trending_tokens)}<br>
            • Major tokens skipped: {major_token_count}<br>
            • Low liquidity filtered: {low_liq_count}<br>
            • Gems found: {len(results)}
            </div>
            """, unsafe_allow_html=True)
        
        return results

# ==============================================================================
# STREAMLIT UI LAYOUT
# ==============================================================================
st.markdown('<div class="main-header">💎 DEGEN SOLANA HUNTER V4.2 💎</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Free system for finding high-potential Solana memecoins 🚀</div>', unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.header("⚙️ Degen Configuration")
min_liq = st.sidebar.slider("Min Liquidity ($)", 500, 100000, 1000, step=500, help="Lower for ultra-degen, higher for safer plays")
max_age = st.sidebar.slider("Max Age (Hours)", 1, 168, 72)
max_tokens = st.sidebar.slider("Tokens to Scan", 10, 100, 30)
debug_mode = st.sidebar.checkbox("🐛 Debug Mode", help="Show detailed filtering info")

st.sidebar.markdown("---")
st.sidebar.info("**How it works:**\n1. Searches for popular Solana DEX tokens (SOL, RAY, BONK, etc.)\n2. Filters for Solana chain only\n3. Sorts by 24h volume to find trending pairs\n4. Scores on volume, buy pressure, age, and narrative\n5. Flags rug risks (low liq, no socials, death spirals)")

# Test Connection Button
if st.sidebar.button("🔌 Test API Connection"):
    hunter_test = SolanaMemecoinHunter(debug_mode=debug_mode)
    if hunter_test.test_connection():
        st.sidebar.success("✅ Successfully connected to DexScreener API!")
    else:
        st.sidebar.error("❌ Failed to connect. Check your internet or try again later.")

# Main Execution Area
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    scan_button = st.button("🔥 START GEM HUNT", type="primary", use_container_width=True)

if scan_button:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    hunter = SolanaMemecoinHunter(min_liquidity=min_liq, max_age_hours=max_age, debug_mode=debug_mode)
    
    if not hunter.test_connection():
        st.error("❌ Cannot reach DexScreener API. Please check your internet connection or try again in a few minutes.")
        st.stop()
    
    gems = hunter.scan_for_gems(max_tokens=max_tokens, progress_bar=progress_bar, status_text=status_text)
    
    progress_bar.empty()
    status_text.empty()
    
    if not gems:
        st.warning("⚠️ No gems found matching your criteria. Try lowering the Min Liquidity slider or enabling Debug Mode to see what's being filtered.")
    else:
        st.session_state['gems'] = gems

# Display Results
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
    for i, gem in enumerate(gems[:15], 1):
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
