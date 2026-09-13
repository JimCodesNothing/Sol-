import streamlit as st
import pandas as pd
import requests
import warnings
from datetime import datetime
import time

warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="🚀 Degen Solana Hunter V5.2",
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
            url = f"{self.dexscreener_base}/search?q=raydium"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(url, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def get_new_solana_tokens(self):
        """Get new Solana tokens by searching for DEX protocols and filtering by age"""
        all_pairs = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        # Search for actual DEX protocols on Solana (not random words)
        dex_queries = ['raydium', 'orca', 'meteora', 'jupiter']
        
        for query in dex_queries:
            try:
                url = f"{self.dexscreener_base}/search?q={query}"
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    pairs = data.get('pairs', [])
                    
                    for pair in pairs:
                        # Only Solana chain
                        if pair.get('chainId') != 'solana':
                            continue
                        
                        # Get creation time
                        created_at = pair.get('pairCreatedAt')
                        if not created_at:
                            continue
                        
                        # Calculate age in hours
                        age_hours = (datetime.now().timestamp() * 1000 - created_at) / (1000 * 3600)
                        
                        # Only keep tokens within max age
                        if age_hours <= self.max_age_hours:
                            all_pairs.append(pair)
                
                time.sleep(0.4)  # Respect rate limits
            except Exception as e:
                if self.debug_mode:
                    st.warning(f"Failed to fetch {query}: {e}")
        
        # Remove duplicates
        unique_pairs = {}
        for pair in all_pairs:
            pair_addr = pair.get('pairAddress')
            if pair_addr and pair_addr not in unique_pairs:
                unique_pairs[pair_addr] = pair
        
        # Sort by creation time (newest first)
        sorted_pairs = sorted(
            unique_pairs.values(),
            key=lambda x: x.get('pairCreatedAt', 0),
            reverse=True
        )
        
        if self.debug_mode:
            st.info(f"🔍 Found {len(sorted_pairs)} NEW Solana pairs (< {self.max_age_hours}h old)")
        
        return sorted_pairs

    def convert_pair_to_gem(self, pair_data):
        """Convert DexScreener pair to gem format"""
        base_token = pair_data.get('baseToken', {}) or {}
        symbol = base_token.get('symbol', 'UNK')
        name = base_token.get('name', 'Unknown')
        address = base_token.get('address', '')
        
        # Skip if name contains "dex" (filter out DEX tokens)
        if 'dex' in name.lower() or 'dex' in symbol.lower():
            return None
        
        price_change = pair_data.get('priceChange', {}) or {}
        price_change_5m = float(price_change.get('m5', 0) or 0)
        price_change_1h = float(price_change.get('h1', 0) or 0)
        price_change_24h = float(price_change.get('h24', 0) or 0)
        
        volume = pair_data.get('volume', {}) or {}
        liquidity = pair_data.get('liquidity', {}) or {}
        volume_24h = float(volume.get('h24', 0) or 0)
        liquidity_usd = float(liquidity.get('usd', 0) or 0)
        
        txns = pair_data.get('txns', {}) or {}
        txns_5m = txns.get('m5', {}) or {}
        buys_5m = int(txns_5m.get('buys', 0) or 0)
        sells_5m = int(txns_5m.get('sells', 0) or 0)
        
        created_at = pair_data.get('pairCreatedAt')
        age_hours = 999
        if created_at:
            age_hours = (datetime.now().timestamp() * 1000 - created_at) / (1000 * 3600)
        
        fdv = float(pair_data.get('fdv', 0) or 0)
        current_price = float(pair_data.get('priceUsd', 0) or 0)
        
        if current_price == 0:
            return None
        
        entry = current_price
        stop_loss = entry * 0.80
        tp1, tp2, tp3, tp4 = entry * 1.5, entry * 2.5, entry * 5.0, entry * 10.0
        
        buy_pressure = round((buys_5m / (buys_5m + sells_5m)) * 100, 1) if (buys_5m + sells_5m) > 0 else 50.0
        
        return {
            'symbol': symbol,
            'name': name,
            'address': address,
            'pair_address': pair_data.get('pairAddress', ''),
            'price': current_price,
            'score': 0,
            'is_memecoin': False,
            'signals': [],
            'risk_flags': [],
            'price_change_5m': price_change_5m,
            'price_change_1h': price_change_1h,
            'price_change_24h': price_change_24h,
            'liquidity_usd': liquidity_usd,
            'volume_24h': volume_24h,
            'buy_pressure_5m': buy_pressure,
            'age_hours': age_hours,
            'fdv': fdv,
            'url': pair_data.get('url', ''),
            'stop_loss': stop_loss,
            'tp1': tp1, 'tp2': tp2, 'tp3': tp3, 'tp4': tp4,
            'buys_5m': buys_5m,
            'sells_5m': sells_5m
        }

    def detect_memecoin_signals(self, gem):
        """Score and analyze a gem"""
        signals = []
        risk_flags = []
        score = 0

        name_lower = str(gem['name']).lower()
        symbol_lower = str(gem['symbol']).lower()

        # 1. MEMECOIN NARRATIVE
        memecoin_keywords = ['doge', 'pepe', 'shib', 'floki', 'inu', 'elon', 'moon', 'safe',
                             'baby', 'mini', 'rocket', 'trump', 'biden', 'wojak', 
                             'bonk', 'samo', 'cheems', 'cope', 'giga', 'based', 'sigma',
                             'meme', 'frog', 'cat', 'dog', 'puppy', 'wif', 'hat']
        
        is_memecoin = any(keyword in name_lower or keyword in symbol_lower for keyword in memecoin_keywords)
        if is_memecoin:
            score += 20
            signals.append("🎭 Memecoin narrative detected")

        # 2. PRICE ACTION
        if gem['price_change_5m'] > 20:
            score += 15
            signals.append(f"🚀 Strong 5m pump: +{gem['price_change_5m']:.1f}%")
        elif gem['price_change_5m'] > 10:
            score += 10
            signals.append(f"📈 5m pump: +{gem['price_change_5m']:.1f}%")
        
        if 10 < gem['price_change_1h'] < 50:
            score += 10
            signals.append(f"🌱 Early pump: +{gem['price_change_1h']:.1f}% (1h)")

        # 3. VOLUME & LIQUIDITY
        if gem['liquidity_usd'] > 0:
            vol_to_liq_ratio = gem['volume_24h'] / gem['liquidity_usd']
            if vol_to_liq_ratio > 5:
                score += 15
                signals.append(f"💸 High volume: {vol_to_liq_ratio:.1f}x liquidity")
            
            if gem['liquidity_usd'] < 2000:
                risk_flags.append("🚩 EXTREME LOW LIQ: < $2k")
                score -= 10
            elif gem['liquidity_usd'] > 10000:
                score += 10
                signals.append(f"✅ Good liquidity: ${gem['liquidity_usd']:,.0f}")

        # 4. BUY PRESSURE
        if gem['buy_pressure_5m'] > 75 and gem['buys_5m'] > 15:
            score += 15
            signals.append(f"🐋 Heavy buy pressure: {gem['buy_pressure_5m']:.0f}% buys")

        # 5. AGE CHECK (CRITICAL)
        if gem['age_hours'] < 1:
            score += 25
            signals.append(f"🆕 BRAND NEW: {gem['age_hours']*60:.0f} minutes old!")
        elif gem['age_hours'] < 6:
            score += 20
            signals.append(f"🌟 Very new: {gem['age_hours']:.1f}h old")
        elif gem['age_hours'] < 12:
            score += 15
            signals.append(f"✨ Fresh: {gem['age_hours']:.1f}h old")
        elif gem['age_hours'] < 24:
            score += 10
            signals.append(f"📊 New: {gem['age_hours']:.1f}h old")

        # 6. MARKET CAP
        if gem['fdv'] > 0:
            if gem['fdv'] > self.max_fdv:
                score -= 30
                risk_flags.append(f"🔴 Large cap: ${gem['fdv']:,.0f}")
            elif gem['fdv'] < 50000:
                score += 15
                signals.append(f"💎 Micro cap: ${gem['fdv']:,.0f}")
            elif gem['fdv'] < 200000:
                score += 10
                signals.append(f"🔹 Small cap: ${gem['fdv']:,.0f}")

        # 7. RUG CHECKS
        if gem['price_change_24h'] < -50:
            risk_flags.append("🔴 Down 50%+ today")

        gem['score'] = max(0, min(100, score))
        gem['signals'] = signals
        gem['risk_flags'] = risk_flags
        gem['is_memecoin'] = is_memecoin
        
        return gem

    def scan_for_gems(self, max_tokens=30, progress_bar=None, status_text=None):
        if status_text:
            status_text.text("🔍 Fetching NEW Solana pairs from DexScreener...")
        
        new_pairs = self.get_new_solana_tokens()
        
        if not new_pairs:
            if self.debug_mode:
                st.error("❌ No new pairs found. Try increasing Max Age Hours.")
            return []
        
        if status_text:
            status_text.text(f"📊 Analyzing {len(new_pairs)} new pairs...")
        
        results = []
        seen_addresses = set()
        filtered_dex = 0
        filtered_liq = 0
        filtered_cap = 0
        
        for i, pair in enumerate(new_pairs):
            if progress_bar:
                progress_bar.progress(min(1.0, (i + 1) / len(new_pairs)))
            
            if len(results) >= max_tokens:
                break
            
            gem = self.convert_pair_to_gem(pair)
            
            if gem is None:
                if 'dex' in str(pair.get('baseToken', {}).get('name', '')).lower():
                    filtered_dex += 1
                continue
            
            addr = gem['address']
            if addr in seen_addresses:
                continue
            seen_addresses.add(addr)
            
            # Apply filters
            if gem['liquidity_usd'] < self.min_liquidity:
                filtered_liq += 1
                continue
            
            if gem['fdv'] > self.max_fdv:
                filtered_cap += 1
                continue
            
            gem = self.detect_memecoin_signals(gem)
            results.append(gem)
            time.sleep(0.2)
        
        results.sort(key=lambda x: x['score'], reverse=True)
        
        if self.debug_mode:
            st.markdown(f"""
            <div class="debug-box">
            <strong>🔍 Scan Debug Info:</strong><br>
            • Total new pairs found: {len(new_pairs)}<br>
            • Filtered (DEX tokens): {filtered_dex}<br>
            • Filtered (low liquidity): {filtered_liq}<br>
            • Filtered (large cap): {filtered_cap}<br>
            • Gems found: {len(results)}
            </div>
            """, unsafe_allow_html=True)
        
        return results

# ==============================================================================
# STREAMLIT UI
# ==============================================================================
st.markdown('<div class="main-header">💎 DEGEN SOLANA HUNTER V5.2 💎</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Finds NEW Solana memecoins from Raydium/Orca/Meteora 🚀</div>', unsafe_allow_html=True)

st.sidebar.header("⚙️ Degen Configuration")
min_liq = st.sidebar.slider("Min Liquidity ($)", 500, 50000, 1000, step=500)
max_age = st.sidebar.slider("Max Age (Hours)", 1, 168, 24, help="Only show tokens newer than this")
max_fdv = st.sidebar.slider("Max Market Cap ($)", 50000, 5000000, 500000, step=50000)
max_tokens = st.sidebar.slider("Tokens to Scan", 10, 100, 30)
debug_mode = st.sidebar.checkbox("🐛 Debug Mode")

st.sidebar.markdown("---")
st.sidebar.info("**V5.2 - Smart Filtering:**\n• Searches Raydium, Orca, Meteora pairs\n• Filters by creation time (NEW only)\n• Excludes DEX tokens\n• Filters by liquidity & market cap\n• Real new launches!")

if st.sidebar.button("🔌 Test API Connection"):
    hunter_test = SolanaMemecoinHunter(debug_mode=debug_mode)
    if hunter_test.test_connection():
        st.sidebar.success("✅ Connected to DexScreener!")
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
        st.warning("⚠️ No gems found. Try increasing Max Age Hours or lowering Min Liquidity.")
    else:
        st.session_state['gems'] = gems

if 'gems' in st.session_state and st.session_state['gems']:
    gems = st.session_state['gems']
    
    st.markdown("### 🏆 Top NEW Opportunities")
    cols = st.columns(3)
    cols[0].metric("Total Gems", len(gems))
    high_conviction = [g for g in gems if g['score'] >= 70]
    cols[1].metric("High Conviction (70+)", len(high_conviction))
    avg_age = sum(g['age_hours'] for g in gems) / len(gems) if gems else 0
    cols[2].metric("Avg Age", f"{avg_age:.1f}h")

    st.markdown("---")

    for i, gem in enumerate(gems[:15], 1):
        score_color = "🔴" if gem['score'] < 50 else "🟡" if gem['score'] < 70 else "🟢"
        
        with st.expander(f"#{i} {score_color} **${gem['symbol']}** - {gem['name']} | Score: **{gem['score']}/100** | Age: **{gem['age_hours']:.1f}h**", expanded=(i <= 3)):
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown(f"**Contract:** `{gem['address']}`")
                st.markdown(f"**Price:** `${gem['price']:.10f}`")
                st.markdown(f"**Age:** `{gem['age_hours']:.1f}` hours")
                st.markdown(f"**Market Cap:** `${gem['fdv']:,.0f}`")
                st.markdown(f"**Liquidity:** `${gem['liquidity_usd']:,.0f}`")
                st.markdown(f"**24h Volume:** `${gem['volume_24h']:,.0f}`")
            
            with col_b:
                st.markdown("**📈 Price Action:**")
                st.markdown(f"• 5m: `{'+' if gem['price_change_5m'] > 0 else ''}{gem['price_change_5m']:.2f}%`")
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
                    st.markdown("✅ No major red flags")
            
            with col_bull:
                st.markdown("**✅ Bullish Signals:**")
                if gem['signals']:
                    for sig in gem['signals']:
                        st.markdown(f"<span class='bullish-signal'>• {sig}</span>", unsafe_allow_html=True)
                else:
                    st.markdown("No strong signals yet")

            st.markdown("**🎯 Degen Entry/Exit Plan:**")
            plan_cols = st.columns(5)
            plan_cols[0].metric("Entry", f"${gem['price']:.8f}")
            plan_cols[1].metric("Stop Loss", f"${gem['stop_loss']:.8f}", "-20%")
            plan_cols[2].metric("TP1 (50%)", f"${gem['tp1']:.8f}", "+50%")
            plan_cols[3].metric("TP2 (150%)", f"${gem['tp2']:.8f}", "+150%")
            plan_cols[4].metric("TP3 (400%)", f"${gem['tp3']:.8f}", "+400%")

            st.markdown(f"[🔗 View on DexScreener]({gem['url']}) | [🔍 View on Solscan](https://solscan.io/token/{gem['address']})")

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
    st.info("👈 Configure settings and click **START GEM HUNT**")

st.markdown("---")
st.markdown("""
<div style="background-color: #2b0000; padding: 1.5rem; border-radius: 0.5rem; border: 1px solid #FF4B4B;">
    <h3 style="color: #FF4B4B; margin-top: 0;">⚠️ ULTIMATE DEGEN DISCLAIMER</h3>
    <ul style="color: #FFCCCC; line-height: 1.6;">
        <li><strong>New memecoins are EXTREMELY high risk</strong> - 99% go to zero</li>
        <li><strong>Always check RugCheck.xyz</strong> before buying</li>
        <li><strong>Never invest more than you can afford to lose</strong></li>
        <li><strong>Take profits FAST</strong> - most dump within hours</li>
    </ul>
    <p style="color: #FFCCCC; font-weight: bold; text-align: center; margin-bottom: 0;">DYOR. NFA. Trade responsibly. 🫡</p>
</div>
""", unsafe_allow_html=True)
