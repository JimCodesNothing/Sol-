import streamlit as st
import pandas as pd
import requests
import warnings
from datetime import datetime
import time

warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="🚀 Degen Solana Hunter V5.0",
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
        self.pumpfun_base = "https://frontend-api.pump.fun"
        self.dexscreener_base = "https://api.dexscreener.com/latest/dex"

    def test_connection(self):
        try:
            url = f"{self.pumpfun_base}/coins/latest"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def get_pumpfun_new_coins(self, limit=50):
        """Get NEW coins from Pump.fun (where most Solana memecoins launch)"""
        try:
            url = f"{self.pumpfun_base}/coins/latest?limit={limit}&offset=0&includeNsfw=false"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                if self.debug_mode:
                    st.error(f"Pump.fun API returned {response.status_code}")
                return []
            
            coins = response.json()
            
            if self.debug_mode:
                st.info(f"🔍 Found {len(coins)} new coins from Pump.fun")
            
            return coins
        except Exception as e:
            if self.debug_mode:
                st.error(f"Failed to fetch from Pump.fun: {e}")
            return []

    def get_dexscreener_data(self, token_address):
        """Get price data from DexScreener for a specific token"""
        try:
            url = f"{self.dexscreener_base}/tokens/{token_address}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                if pairs:
                    # Return the most liquid pair
                    pairs.sort(key=lambda x: float(x.get('liquidity', {}).get('usd', 0) or 0), reverse=True)
                    return pairs[0]
            return None
        except Exception:
            return None

    def analyze_pumpfun_coin(self, coin_data):
        """Analyze a Pump.fun coin and convert to our format"""
        mint = coin_data.get('mint')
        name = coin_data.get('name', 'Unknown')
        symbol = coin_data.get('symbol', 'UNK')
        
        # Get DexScreener data for price/volume info
        dex_data = self.get_dexscreener_data(mint)
        time.sleep(0.3)  # Rate limiting
        
        if not dex_data:
            # Coin hasn't graduated to Raydium yet, use Pump.fun data
            market_cap = float(coin_data.get('market_cap', 0) or 0)
            usd_market_cap = float(coin_data.get('usd_market_cap', 0) or 0)
            
            return {
                'symbol': symbol,
                'name': name,
                'address': mint,
                'pair_address': '',
                'price': float(coin_data.get('usd_price', 0) or 0),
                'score': 0,
                'is_memecoin': False,
                'signals': ['🆕 Still on Pump.fun bonding curve'],
                'risk_flags': ['⚠️ Not yet on Raydium (bonding curve)'],
                'price_change_1h': 0,
                'price_change_24h': 0,
                'liquidity_usd': 0,
                'volume_24h': 0,
                'buy_pressure_5m': 50.0,
                'age_hours': 0,
                'fdv': usd_market_cap,
                'url': f"https://pump.fun/{mint}",
                'stop_loss': 0,
                'tp1': 0, 'tp2': 0, 'tp3': 0, 'tp4': 0,
                'source': 'pumpfun'
            }
        else:
            # Coin has graduated to Raydium, use DexScreener data
            return self.convert_dexscreener_pair(dex_data, source='raydium')

    def convert_dexscreener_pair(self, pair_data, source='raydium'):
        """Convert DexScreener pair data to our format"""
        base_token = pair_data.get('baseToken', {}) or {}
        symbol = base_token.get('symbol', 'UNK')
        name = base_token.get('name', 'Unknown')
        address = base_token.get('address', '')
        
        price_change = pair_data.get('priceChange', {}) or {}
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
        
        entry = current_price
        stop_loss = entry * 0.80
        tp1, tp2, tp3, tp4 = entry * 1.5, entry * 2.5, entry * 5.0, entry * 10.0
        
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
            'price_change_1h': price_change_1h,
            'price_change_24h': price_change_24h,
            'liquidity_usd': liquidity_usd,
            'volume_24h': volume_24h,
            'buy_pressure_5m': round((buys_5m / (buys_5m + sells_5m)) * 100, 1) if (buys_5m + sells_5m) > 0 else 50.0,
            'age_hours': age_hours,
            'fdv': fdv,
            'url': pair_data.get('url', ''),
            'stop_loss': stop_loss,
            'tp1': tp1, 'tp2': tp2, 'tp3': tp3, 'tp4': tp4,
            'source': source,
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

        # 2. PRICE ACTION (only if graduated)
        if gem['source'] == 'raydium':
            if gem['price_change_1h'] > 20:
                score += 15
                signals.append(f"🚀 Strong 1h pump: +{gem['price_change_1h']:.1f}%")
            elif 10 < gem['price_change_1h'] < 50:
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
        if gem['source'] == 'raydium':
            if gem['buy_pressure_5m'] > 75 and gem['buys_5m'] > 15:
                score += 15
                signals.append(f"🐋 Heavy buy pressure: {gem['buy_pressure_5m']:.0f}% buys")

        # 5. AGE CHECK
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
        if gem['source'] == 'raydium':
            if gem['price_change_24h'] < -50:
                risk_flags.append("🔴 Down 50%+ today")

        gem['score'] = max(0, min(100, score))
        gem['signals'] = signals
        gem['risk_flags'] = risk_flags
        gem['is_memecoin'] = is_memecoin
        
        return gem

    def scan_for_gems(self, max_tokens=30, progress_bar=None, status_text=None):
        if status_text:
            status_text.text("🔍 Fetching NEW coins from Pump.fun...")
        
        pumpfun_coins = self.get_pumpfun_new_coins(limit=50)
        
        if not pumpfun_coins:
            if self.debug_mode:
                st.error("❌ No coins found from Pump.fun")
            return []
        
        if status_text:
            status_text.text(f"📊 Analyzing {len(pumpfun_coins)} new coins...")
        
        results = []
        seen_addresses = set()
        
        for i, coin in enumerate(pumpfun_coins):
            if progress_bar:
                progress_bar.progress(min(1.0, (i + 1) / len(pumpfun_coins)))
            
            if len(results) >= max_tokens:
                break
            
            mint = coin.get('mint')
            if not mint or mint in seen_addresses:
                continue
            seen_addresses.add(mint)
            
            # Analyze the coin
            gem = self.analyze_pumpfun_coin(coin)
            
            # Apply filters
            if gem['liquidity_usd'] > 0 and gem['liquidity_usd'] < self.min_liquidity:
                continue
            
            if gem['age_hours'] > self.max_age_hours:
                continue
            
            if gem['fdv'] > self.max_fdv:
                continue
            
            # Score the gem
            gem = self.detect_memecoin_signals(gem)
            
            results.append(gem)
            time.sleep(0.3)
        
        results.sort(key=lambda x: x['score'], reverse=True)
        
        if self.debug_mode:
            pumpfun_count = len([g for g in results if g['source'] == 'pumpfun'])
            raydium_count = len([g for g in results if g['source'] == 'raydium'])
            st.markdown(f"""
            <div class="debug-box">
            <strong>🔍 Scan Debug Info:</strong><br>
            • Total coins from Pump.fun: {len(pumpfun_coins)}<br>
            • Still on bonding curve: {pumpfun_count}<br>
            • Graduated to Raydium: {raydium_count}<br>
            • Gems found: {len(results)}
            </div>
            """, unsafe_allow_html=True)
        
        return results

# ==============================================================================
# STREAMLIT UI
# ==============================================================================
st.markdown('<div class="main-header">💎 DEGEN SOLANA HUNTER V5.0 💎</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Finds BRAND NEW Solana memecoins from Pump.fun 🚀</div>', unsafe_allow_html=True)

st.sidebar.header("⚙️ Degen Configuration")
min_liq = st.sidebar.slider("Min Liquidity ($)", 0, 50000, 1000, step=500, help="Set to 0 for bonding curve coins")
max_age = st.sidebar.slider("Max Age (Hours)", 1, 168, 24, help="Only show tokens newer than this")
max_fdv = st.sidebar.slider("Max Market Cap ($)", 10000, 5000000, 500000, step=10000, help="Exclude large tokens")
max_tokens = st.sidebar.slider("Tokens to Scan", 10, 100, 30)
debug_mode = st.sidebar.checkbox("🐛 Debug Mode", help="Show detailed info")

st.sidebar.markdown("---")
st.sidebar.info("**V5.0 - Pump.fun Integration:**\n• Fetches NEW coins directly from Pump.fun\n• Shows both bonding curve & graduated coins\n• Real new launches, not the same old tokens\n• Most will rug - DYOR!")

if st.sidebar.button("🔌 Test API Connection"):
    hunter_test = SolanaMemecoinHunter(debug_mode=debug_mode)
    if hunter_test.test_connection():
        st.sidebar.success("✅ Connected to Pump.fun API!")
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
        st.error("❌ Cannot reach Pump.fun API.")
        st.stop()
    
    gems = hunter.scan_for_gems(max_tokens=max_tokens, progress_bar=progress_bar, status_text=status_text)
    
    progress_bar.empty()
    status_text.empty()
    
    if not gems:
        st.warning("⚠️ No gems found. Try adjusting filters.")
    else:
        st.session_state['gems'] = gems

if 'gems' in st.session_state and st.session_state['gems']:
    gems = st.session_state['gems']
    
    st.markdown("### 🏆 Top NEW Opportunities")
    cols = st.columns(3)
    cols[0].metric("Total Gems", len(gems))
    high_conviction = [g for g in gems if g['score'] >= 70]
    cols[1].metric("High Conviction (70+)", len(high_conviction))
    bonding_curve = len([g for g in gems if g['source'] == 'pumpfun'])
    cols[2].metric("On Bonding Curve", bonding_curve)

    st.markdown("---")

    for i, gem in enumerate(gems[:15], 1):
        score_color = "🔴" if gem['score'] < 50 else "🟡" if gem['score'] < 70 else "🟢"
        source_badge = "🟣 PUMP" if gem['source'] == 'pumpfun' else "🔵 RAY"
        
        with st.expander(f"#{i} {score_color} {source_badge} **${gem['symbol']}** | Score: **{gem['score']}/100** | Age: **{gem['age_hours']:.1f}h**", expanded=(i <= 3)):
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown(f"**Contract:** `{gem['address']}`")
                st.markdown(f"**Price:** `${gem['price']:.10f}`")
                st.markdown(f"**Age:** `{gem['age_hours']:.1f}` hours")
                st.markdown(f"**Market Cap:** `${gem['fdv']:,.0f}`")
                if gem['liquidity_usd'] > 0:
                    st.markdown(f"**Liquidity:** `${gem['liquidity_usd']:,.0f}`")
                    st.markdown(f"**24h Volume:** `${gem['volume_24h']:,.0f}`")
            
            with col_b:
                if gem['source'] == 'raydium':
                    st.markdown("**📈 Price Action:**")
                    st.markdown(f"• 1h: `{'+' if gem['price_change_1h'] > 0 else ''}{gem['price_change_1h']:.2f}%`")
                    st.markdown(f"• 24h: `{'+' if gem['price_change_24h'] > 0 else ''}{gem['price_change_24h']:.2f}%`")
                    st.markdown(f"**🐋 Buy Pressure (5m):** `{gem['buy_pressure_5m']:.1f}%`")
                else:
                    st.markdown("**🆕 Bonding Curve Status:**")
                    st.markdown("• Still on Pump.fun")
                    st.markdown("• No price history yet")
                    st.markdown("• Graduates at ~$69k market cap")

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

            if gem['source'] == 'raydium' and gem['price'] > 0:
                st.markdown("**🎯 Degen Entry/Exit Plan:**")
                plan_cols = st.columns(5)
                plan_cols[0].metric("Entry", f"${gem['price']:.8f}")
                plan_cols[1].metric("Stop Loss", f"${gem['stop_loss']:.8f}", "-20%")
                plan_cols[2].metric("TP1 (50%)", f"${gem['tp1']:.8f}", "+50%")
                plan_cols[3].metric("TP2 (150%)", f"${gem['tp2']:.8f}", "+150%")
                plan_cols[4].metric("TP3 (400%)", f"${gem['tp3']:.8f}", "+400%")

            st.markdown(f"[🔗 View on Pump.fun]({gem['url']}) | [🔍 View on Solscan](https://solscan.io/token/{gem['address']})")

    st.markdown("---")
    st.markdown("### 📥 Export Data")
    df = pd.DataFrame(gems)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Gems as CSV",
        data=csv,
        file_name=f"solana_pumpfun_gems_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

else:
    st.info("👈 Configure settings and click **START GEM HUNT** to find NEW memecoins from Pump.fun")

st.markdown("---")
st.markdown("""
<div style="background-color: #2b0000; padding: 1.5rem; border-radius: 0.5rem; border: 1px solid #FF4B4B;">
    <h3 style="color: #FF4B4B; margin-top: 0;">⚠️ ULTIMATE DEGEN DISCLAIMER</h3>
    <ul style="color: #FFCCCC; line-height: 1.6;">
        <li><strong>Pump.fun coins are EXTREMELY high risk</strong> - 99% go to zero</li>
        <li><strong>Bonding curve coins** can rug instantly - dev can pull liquidity</li>
        <li><strong>Always check RugCheck.xyz</strong> before buying any token</li>
        <li><strong>Never invest more than you can afford to lose completely</strong></li>
        <li><strong>Take profits FAST** - most pump.fun coins dump within hours</li>
    </ul>
    <p style="color: #FFCCCC; font-weight: bold; text-align: center; margin-bottom: 0;">DYOR. NFA. Trade responsibly. 🫡</p>
</div>
""", unsafe_allow_html=True)
