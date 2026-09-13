import streamlit as st
import pandas as pd
import requests
import warnings
from datetime import datetime
import time

warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="🚀 Degen Solana Hunter V4.3",
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

class SolanaMemecoinHunter:
    def __init__(self, min_liquidity=1000, max_age_hours=24, max_fdv=500000, debug_mode=False):
        self.min_liquidity = min_liquidity
        self.max_age_hours = max_age_hours
        self.max_fdv = max_fdv
        self.debug_mode = debug_mode
        self.dexscreener_base = "https://api.dexscreener.com/latest/dex"

    def test_connection(self):
        try:
            url = f"{self.dexscreener_base}/search?q=new"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(url, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def get_new_solana_tokens(self):
        """Get NEW Solana memecoins using smart search patterns"""
        all_pairs = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        # Search for NEW memecoin patterns (not established tokens)
        search_queries = [
            'new', 'launch', 'moon', 'gem', '100x', 'early',
            'dog', 'cat', 'frog', 'meme', 'coin', 'token'
        ]
        
        for query in search_queries:
            try:
                url = f"{self.dexscreener_base}/search?q={query}"
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    pairs = data.get('pairs', [])
                    
                    for pair in pairs:
                        if pair.get('chainId') == 'solana':
                            all_pairs.append(pair)
                
                time.sleep(0.3)
            except Exception as e:
                if self.debug_mode:
                    st.warning(f"Failed to fetch {query}: {e}")
        
        # Remove duplicates
        unique_pairs = {}
        for pair in all_pairs:
            pair_addr = pair.get('pairAddress')
            if pair_addr and pair_addr not in unique_pairs:
                unique_pairs[pair_addr] = pair
        
        # Filter by age FIRST (before sorting)
        filtered_pairs = []
        for pair in unique_pairs.values():
            created_at = pair.get('pairCreatedAt')
            if created_at:
                age_hours = (datetime.now().timestamp() * 1000 - created_at) / (1000 * 3600)
                if age_hours <= self.max_age_hours:
                    filtered_pairs.append(pair)
        
        # Sort by creation time (newest first)
        filtered_pairs.sort(
            key=lambda x: x.get('pairCreatedAt', 0),
            reverse=True
        )
        
        if self.debug_mode:
            st.info(f"🔍 Found {len(filtered_pairs)} NEW Solana pairs (< {self.max_age_hours}h old) from {len(search_queries)} search queries")
        
        return filtered_pairs

    def detect_memecoin_signals(self, pair_data):
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
                             'baby', 'mini', 'rocket', 'trump', 'biden', 'wojak', 
                             'bonk', 'samo', 'cheems', 'cope', 'giga', 'based', 'sigma',
                             'meme', 'frog', 'cat', 'dog', 'puppy', 'wif', 'hat']
        
        is_memecoin = any(keyword in name_lower or keyword in symbol_lower for keyword in memecoin_keywords)
        if is_memecoin:
            score += 20
            signals.append("🎭 Memecoin narrative detected")

        # 2. PRICE ACTION ANALYSIS
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
            score -= 10
        elif liquidity_usd > 10000:
            score += 10
            signals.append(f"✅ Good liquidity: ${liquidity_usd:,.0f}")

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

        # 5. AGE CHECK (CRITICAL FOR NEW LAUNCHES)
        created_at = pair_data.get('pairCreatedAt')
        age_hours = 999
        if created_at:
            age_hours = (datetime.now().timestamp() * 1000 - created_at) / (1000 * 3600)
            if age_hours < 1:
                score += 25
                signals.append(f"🆕 BRAND NEW: {age_hours*60:.0f} minutes old!")
            elif age_hours < 6:
                score += 20
                signals.append(f"🌟 Very new: {age_hours:.1f}h old")
            elif age_hours < 12:
                score += 15
                signals.append(f"✨ Fresh launch: {age_hours:.1f}h old")
            elif age_hours < 24:
                score += 10
                signals.append(f"📊 New: {age_hours:.1f}h old")

        # 6. MARKET CAP CHECK (EXCLUDE ESTABLISHED TOKENS)
        fdv = pair_data.get('fdv')
        if fdv:
            fdv_val = float(fdv)
            if fdv_val > self.max_fdv:
                score -= 30  # Heavy penalty for large market caps
                risk_flags.append(f"🔴 Large cap: ${fdv_val:,.0f} (not a gem)")
            elif fdv_val < 50000:
                score += 15
                signals.append(f"💎 Micro cap: ${fdv_val:,.0f} FDV")
            elif fdv_val < 200000:
                score += 10
                signals.append(f"🔹 Small cap: ${fdv_val:,.0f} FDV")

        # 7. FREE RUG-CHECK PROXIES
        info = pair_data.get('info', {}) or {}
        if not info.get('twitter') and not info.get('telegram') and not info.get('website'):
            risk_flags.append("⚠️ No social links (Anonymous dev)")
        
        if price_change_24h < -50:
            risk_flags.append("🔴 Down 50%+ today (Death spiral?)")

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
            'age_hours': age_hours,
            'fdv': float(fdv) if fdv else 0
        }

    def scan_for_gems(self, max_tokens=30, progress_bar=None, status_text=None):
        if status_text:
            status_text.text("🔍 Fetching NEW Solana memecoins from DexScreener...")
        
        new_tokens = self.get_new_solana_tokens()
        
        if not new_tokens:
            if self.debug_mode:
                st.error("❌ No NEW pairs found. Try increasing Max Age Hours.")
            return []
        
        if status_text:
            status_text.text(f"📊 Analyzing {len(new_tokens)} new pairs...")
        
        results = []
        seen_addresses = set()
        filtered_count = 0
        major_token_count = 0
        low_liq_count = 0
        old_token_count = 0
        large_cap_count = 0

        for i, pair in enumerate(new_tokens):
            if progress_bar:
                progress_bar.progress(min(1.0, (i + 1) / len(new_tokens)))
                
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
            
            # Filter by liquidity
            if analysis['liquidity_usd'] < self.min_liquidity:
                low_liq_count += 1
                continue
            
            # Filter by age (double-check)
            if analysis['age_hours'] > self.max_age_hours:
                old_token_count += 1
                continue
            
            # Filter by market cap
            if analysis['fdv'] > self.max_fdv:
                large_cap_count += 1
                continue

            current_price = float(pair.get('priceUsd', 0) or 0)
            if current_price == 0:
                continue
            
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
                'fdv': analysis['fdv'],
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
            • Total NEW pairs fetched: {len(new_tokens)}<br>
            • Major tokens skipped: {major_token_count}<br>
            • Low liquidity filtered: {low_liq_count}<br>
            • Old tokens filtered: {old_token_count}<br>
            • Large cap filtered: {large_cap_count}<br>
            • Gems found: {len(results)}
            </div>
            """, unsafe_allow_html=True)
        
        return results

# ==============================================================================
# STREAMLIT UI
# ==============================================================================
st.markdown('<div class="main-header">💎 DEGEN SOLANA HUNTER V4.3 💎</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Finds NEW Solana memecoins with 10-100x potential 🚀</div>', unsafe_allow_html=True)

st.sidebar.header("⚙️ Degen Configuration")
min_liq = st.sidebar.slider("Min Liquidity ($)", 500, 50000, 1000, step=500, help="Lower = more degen")
max_age = st.sidebar.slider("Max Age (Hours)", 1, 168, 24, help="Only show tokens newer than this")
max_fdv = st.sidebar.slider("Max Market Cap ($)", 50000, 5000000, 500000, step=50000, help="Exclude large established tokens")
max_tokens = st.sidebar.slider("Tokens to Scan", 10, 100, 30)
debug_mode = st.sidebar.checkbox("🐛 Debug Mode", help="Show detailed filtering info")

st.sidebar.markdown("---")
st.sidebar.info("**V4.3 Changes:**\n• Only shows tokens < Max Age hours old\n• Excludes tokens with market cap > Max FDV\n• Heavily scores brand new launches\n• Filters out established tokens like PEPE, BONK")

if st.sidebar.button("🔌 Test API Connection"):
    hunter_test = SolanaMemecoinHunter(debug_mode=debug_mode)
    if hunter_test.test_connection():
        st.sidebar.success("✅ Successfully connected to DexScreener API!")
    else:
        st.sidebar.error("❌ Failed to connect.")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    scan_button = st.button("🔥 START GEM HUNT", type="primary", use_container_width=True)

if scan_button:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    hunter = SolanaMemecoinHunter(
        min_liquidity=min_liq, 
        max_age_hours=max_age, 
        max_fdv=max_fdv,
        debug_mode=debug_mode
    )
    
    if not hunter.test_connection():
        st.error("❌ Cannot reach DexScreener API.")
        st.stop()
    
    gems = hunter.scan_for_gems(max_tokens=max_tokens, progress_bar=progress_bar, status_text=status_text)
    
    progress_bar.empty()
    status_text.empty()
    
    if not gems:
        st.warning("⚠️ No NEW gems found. Try increasing Max Age Hours or Max Market Cap.")
    else:
        st.session_state['gems'] = gems

if 'gems' in st.session_state and st.session_state['gems']:
    gems = st.session_state['gems']
    
    st.markdown("### 🏆 Top NEW Opportunities")
    cols = st.columns(3)
    cols[0].metric("Total Gems Found", len(gems))
    high_conviction = [g for g in gems if g['score'] >= 70]
    cols[1].metric("High Conviction (70+)", len(high_conviction))
    avg_liq = sum(g['liquidity_usd'] for g in gems) / len(gems) if gems else 0
    cols[2].metric("Avg Liquidity", f"${avg_liq:,.0f}")

    st.markdown("---")

    for i, gem in enumerate(gems[:15], 1):
        score_color = "🔴" if gem['score'] < 50 else "🟡" if gem['score'] < 70 else "🟢"
        
        with st.expander(f"#{i} {score_color} **${gem['symbol']}** - {gem['name']} | Score: **{gem['score']}/100** | Age: **{gem['age_hours']:.1f}h** | Liq: **${gem['liquidity_usd']:,.0f}**", expanded=(i <= 3)):
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown(f"**Contract:** `{gem['address']}`")
                st.markdown(f"**Price:** `${gem['price']:.10f}`")
                st.markdown(f"**Age:** `{gem['age_hours']:.1f}` hours")
                st.markdown(f"**Market Cap:** `${gem['fdv']:,.0f}`")
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

    st.markdown("---")
    st.markdown("### 📥 Export Data")
    df = pd.DataFrame(gems)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Gems as CSV",
        data=csv,
        file_name=f"solana_new_gems_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

else:
    st.info("👈 Configure your settings and click **START GEM HUNT** to find NEW memecoins.")

st.markdown("---")
st.markdown("""
<div style="background-color: #2b0000; padding: 1.5rem; border-radius: 0.5rem; border: 1px solid #FF4B4B;">
    <h3 style="color: #FF4B4B; margin-top: 0;">⚠️ ULTIMATE DEGEN DISCLAIMER</h3>
    <ul style="color: #FFCCCC; line-height: 1.6;">
        <li><strong>This finds BRAND NEW tokens</strong> - most will go to ZERO within hours</li>
        <li><strong>90%+ are rugs or scams.</strong> Always check RugCheck.xyz before buying</li>
        <li><strong>Never invest more than you can afford to lose completely</strong></li>
        <li><strong>Take profits FAST</strong> - new memecoins dump 99% in minutes</li>
    </ul>
    <p style="color: #FFCCCC; font-weight: bold; text-align: center; margin-bottom: 0;">DYOR. NFA. Trade responsibly. 🫡</p>
</div>
""", unsafe_allow_html=True)
