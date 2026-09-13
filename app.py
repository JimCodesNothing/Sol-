import streamlit as st
import pandas as pd
import requests
import warnings
from datetime import datetime
import time

warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="🚀 Degen Solana Hunter V5.4",
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
    .social-badge {display: inline-block; padding: 0.4rem 0.8rem; border-radius: 0.3rem; margin: 0.2rem; font-size: 0.9rem; text-decoration: none; color: white !important; font-weight: bold;}
    .social-twitter {background-color: #1DA1F2;}
    .social-telegram {background-color: #0088cc;}
    .social-website {background-color: #28a745;}
    .social-none {background-color: #6c757d;}
    .security-safe {background-color: #d4edda; color: #155724; padding: 0.3rem 0.6rem; border-radius: 0.3rem; display: inline-block; margin: 0.1rem;}
    .security-warn {background-color: #fff3cd; color: #856404; padding: 0.3rem 0.6rem; border-radius: 0.3rem; display: inline-block; margin: 0.1rem;}
    .security-danger {background-color: #f8d7da; color: #721c24; padding: 0.3rem 0.6rem; border-radius: 0.3rem; display: inline-block; margin: 0.1rem;}
    </style>
""", unsafe_allow_html=True)

class RugCheckAnalyzer:
    """Free security + social analysis via RugCheck.xyz API (NO API KEY NEEDED)"""
    
    @staticmethod
    def get_token_report(mint_address):
        """Get full token report from RugCheck (social + security data)"""
        if not mint_address:
            return None
        
        try:
            url = f"https://api.rugcheck.xyz/v1/tokens/{mint_address}/report/summary"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            return None
    
    @staticmethod
    def analyze_token(mint_address):
        """Extract social + security data from RugCheck report"""
        report = RugCheckAnalyzer.get_token_report(mint_address)
        
        # Default values
        result = {
            'social_score': 0,
            'social_badges': [],
            'twitter_url': None,
            'telegram_url': None,
            'website_url': None,
            'has_twitter': False,
            'has_telegram': False,
            'has_website': False,
            'security_score': 0,
            'security_badges': [],
            'mint_authority': None,
            'freeze_authority': None,
            'top_holders': [],
            'lp_locked': False,
            'risk_level': 'unknown',
            'rugcheck_available': False
        }
        
        if not report:
            return result
        
        result['rugcheck_available'] = True
        
        # Extract social links
        metadata = report.get('tokenMeta', {}) or {}
        twitter = metadata.get('twitter')
        telegram = metadata.get('telegram')
        website = metadata.get('website')
        
        if twitter:
            result['twitter_url'] = twitter
            result['has_twitter'] = True
            result['social_score'] += 25
            result['social_badges'].append(('🐦 Twitter', twitter, 'social-twitter'))
        
        if telegram:
            result['telegram_url'] = telegram
            result['has_telegram'] = True
            result['social_score'] += 25
            result['social_badges'].append(('✈️ Telegram', telegram, 'social-telegram'))
        
        if website:
            result['website_url'] = website
            result['has_website'] = True
            result['social_score'] += 15
            result['social_badges'].append(('🌐 Website', website, 'social-website'))
        
        # If no social links at all
        if not (twitter or telegram or website):
            result['social_badges'].append(('❌ No Social Links', None, 'social-none'))
        
        # Extract security data
        mint_authority = metadata.get('mintAuthority')
        freeze_authority = metadata.get('freezeAuthority')
        
        result['mint_authority'] = mint_authority
        result['freeze_authority'] = freeze_authority
        
        # Mint authority check
        if mint_authority is None or mint_authority == '':
            result['security_score'] += 30
            result['security_badges'].append(('✅ Mint Authority: REVOKED', 'safe'))
        else:
            result['security_score'] -= 30
            result['security_badges'].append(('🚨 Mint Authority: ACTIVE (can mint more!)', 'danger'))
        
        # Freeze authority check
        if freeze_authority is None or freeze_authority == '':
            result['security_score'] += 20
            result['security_badges'].append(('✅ Freeze Authority: REVOKED', 'safe'))
        else:
            result['security_score'] -= 20
            result['security_badges'].append(('🚨 Freeze Authority: ACTIVE (can freeze wallets!)', 'danger'))
        
        # Top holders analysis
        top_holders = report.get('topHolders', []) or []
        result['top_holders'] = top_holders[:10]
        
        # Check if top 10 holders own too much
        if top_holders:
            # Skip LP and known system accounts
            non_lp_holders = [h for h in top_holders if not h.get('isMutable', False)]
            if len(non_lp_holders) >= 2:
                top_2_pct = sum(h.get('pct', 0) for h in non_lp_holders[:2])
                if top_2_pct > 30:
                    result['security_score'] -= 20
                    result['security_badges'].append((f'⚠️ Top 2 holders own {top_2_pct:.1f}%', 'warn'))
                elif top_2_pct > 15:
                    result['security_score'] -= 10
                    result['security_badges'].append((f'⚠️ Top 2 holders own {top_2_pct:.1f}%', 'warn'))
                else:
                    result['security_score'] += 10
                    result['security_badges'].append((f'✅ Healthy distribution (top 2: {top_2_pct:.1f}%)', 'safe'))
        
        # Risk level from RugCheck
        risk_level = report.get('risk', {}) or {}
        risk_score = risk_level.get('score', 0)
        risk_level_name = risk_level.get('level', 'unknown')
        result['risk_level'] = risk_level_name
        
        if risk_level_name == 'good':
            result['security_score'] += 20
            result['security_badges'].append(('🛡️ RugCheck: GOOD', 'safe'))
        elif risk_level_name == 'warning':
            result['security_badges'].append(('⚠️ RugCheck: WARNING', 'warn'))
        elif risk_level_name == 'danger':
            result['security_score'] -= 30
            result['security_badges'].append(('🚨 RugCheck: DANGER', 'danger'))
        
        # Normalize scores
        result['social_score'] = min(100, max(0, result['social_score']))
        result['security_score'] = min(100, max(0, result['security_score']))
        
        return result


class SolanaMemecoinHunter:
    def __init__(self, min_liquidity=1000, max_age_hours=24, max_fdv=500000, debug_mode=False):
        self.min_liquidity = min_liquidity
        self.max_age_hours = max_age_hours
        self.max_fdv = max_fdv
        self.debug_mode = debug_mode
        self.dexscreener_base = "https://api.dexscreener.com/latest/dex"
        self.rugcheck = RugCheckAnalyzer()

    def test_connection(self):
        try:
            url = f"{self.dexscreener_base}/search?q=raydium"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(url, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def get_new_solana_tokens(self):
        """Get new Solana tokens"""
        all_pairs = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        dex_queries = ['raydium', 'orca', 'meteora']
        
        for query in dex_queries:
            try:
                url = f"{self.dexscreener_base}/search?q={query}"
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    pairs = data.get('pairs', [])
                    
                    for pair in pairs:
                        if pair.get('chainId') != 'solana':
                            continue
                        
                        created_at = pair.get('pairCreatedAt')
                        if not created_at:
                            continue
                        
                        age_hours = (datetime.now().timestamp() * 1000 - created_at) / (1000 * 3600)
                        
                        if age_hours <= self.max_age_hours:
                            all_pairs.append(pair)
                
                time.sleep(0.4)
            except Exception as e:
                if self.debug_mode:
                    st.warning(f"Failed to fetch {query}: {e}")
        
        unique_pairs = {}
        for pair in all_pairs:
            pair_addr = pair.get('pairAddress')
            if pair_addr and pair_addr not in unique_pairs:
                unique_pairs[pair_addr] = pair
        
        sorted_pairs = sorted(
            unique_pairs.values(),
            key=lambda x: x.get('pairCreatedAt', 0),
            reverse=True
        )
        
        if self.debug_mode:
            st.info(f"🔍 Found {len(sorted_pairs)} NEW Solana pairs (< {self.max_age_hours}h old)")
        
        return sorted_pairs

    def convert_pair_to_gem(self, pair_data):
        """Convert DexScreener pair to gem format with RugCheck data"""
        base_token = pair_data.get('baseToken', {}) or {}
        symbol = base_token.get('symbol', 'UNK')
        name = base_token.get('name', 'Unknown')
        address = base_token.get('address', '')
        
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
        
        # Get RugCheck data (social + security)
        rugcheck_data = self.rugcheck.analyze_token(address)
        
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
            'sells_5m': sells_5m,
            # Social data from RugCheck
            'social_score': rugcheck_data['social_score'],
            'social_badges': rugcheck_data['social_badges'],
            'twitter_url': rugcheck_data['twitter_url'],
            'telegram_url': rugcheck_data['telegram_url'],
            'website_url': rugcheck_data['website_url'],
            'has_social': rugcheck_data['has_twitter'] or rugcheck_data['has_telegram'],
            # Security data from RugCheck
            'security_score': rugcheck_data['security_score'],
            'security_badges': rugcheck_data['security_badges'],
            'mint_authority': rugcheck_data['mint_authority'],
            'freeze_authority': rugcheck_data['freeze_authority'],
            'top_holders': rugcheck_data['top_holders'],
            'risk_level': rugcheck_data['risk_level'],
            'rugcheck_available': rugcheck_data['rugcheck_available']
        }

    def detect_memecoin_signals(self, gem):
        """Score and analyze a gem with social + security metrics"""
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
            score += 15
            signals.append("🎭 Memecoin narrative detected")

        # 2. PRICE ACTION
        if gem['price_change_5m'] > 20:
            score += 15
            signals.append(f"🚀 Strong 5m pump: +{gem['price_change_5m']:.1f}%")
        
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

        # 5. AGE CHECK
        if gem['age_hours'] < 1:
            score += 20
            signals.append(f"🆕 BRAND NEW: {gem['age_hours']*60:.0f} minutes old!")
        elif gem['age_hours'] < 6:
            score += 15
            signals.append(f"🌟 Very new: {gem['age_hours']:.1f}h old")
        elif gem['age_hours'] < 12:
            score += 10
            signals.append(f"✨ Fresh: {gem['age_hours']:.1f}h old")

        # 6. MARKET CAP
        if gem['fdv'] > 0:
            if gem['fdv'] > self.max_fdv:
                score -= 30
                risk_flags.append(f"🔴 Large cap: ${gem['fdv']:,.0f}")
            elif gem['fdv'] < 50000:
                score += 10
                signals.append(f"💎 Micro cap: ${gem['fdv']:,.0f}")

        # 7. SOCIAL SENTIMENT (from RugCheck)
        social_score = gem.get('social_score', 0)
        if social_score >= 50:
            score += 15
            signals.append(f"💬 Strong social presence ({social_score}/100)")
        elif social_score >= 25:
            score += 8
            signals.append(f"💬 Some social presence")
        elif social_score == 0:
            risk_flags.append("🚩 No social media (anonymous dev)")
            score -= 15

        # 8. SECURITY SCORE (from RugCheck) - NEW!
        security_score = gem.get('security_score', 0)
        if security_score >= 60:
            score += 20
            signals.append(f"🛡️ Strong security ({security_score}/100)")
        elif security_score >= 30:
            score += 5
            signals.append(f"🛡️ Moderate security")
        elif security_score < 0:
            risk_flags.append(f"🚨 SECURITY RISKS DETECTED ({security_score}/100)")
            score -= 25

        # 9. RUG CHECKS
        if gem['price_change_24h'] < -50:
            risk_flags.append("🔴 Down 50%+ today")

        gem['score'] = max(0, min(100, score))
        gem['signals'] = signals
        gem['risk_flags'] = risk_flags
        gem['is_memecoin'] = is_memecoin
        
        return gem

    def scan_for_gems(self, max_tokens=30, progress_bar=None, status_text=None):
        if status_text:
            status_text.text("🔍 Fetching NEW Solana pairs...")
        
        new_pairs = self.get_new_solana_tokens()
        
        if not new_pairs:
            if self.debug_mode:
                st.error("❌ No new pairs found.")
            return []
        
        if status_text:
            status_text.text(f"📊 Analyzing {len(new_pairs)} pairs with RugCheck...")
        
        results = []
        seen_addresses = set()
        
        for i, pair in enumerate(new_pairs):
            if progress_bar:
                progress_bar.progress(min(1.0, (i + 1) / len(new_pairs)))
            
            if len(results) >= max_tokens:
                break
            
            if status_text and i % 3 == 0:
                status_text.text(f"🔍 Analyzing... ({i+1}/{len(new_pairs)}) Fetching social + security data from RugCheck...")
            
            gem = self.convert_pair_to_gem(pair)
            
            if gem is None:
                continue
            
            addr = gem['address']
            if addr in seen_addresses:
                continue
            seen_addresses.add(addr)
            
            if gem['liquidity_usd'] < self.min_liquidity:
                continue
            
            if gem['fdv'] > self.max_fdv:
                continue
            
            gem = self.detect_memecoin_signals(gem)
            results.append(gem)
            
            time.sleep(0.5)  # Respect RugCheck rate limits
        
        results.sort(key=lambda x: x['score'], reverse=True)
        
        if self.debug_mode and results:
            avg_social = sum(g.get('social_score', 0) for g in results) / len(results)
            avg_security = sum(g.get('security_score', 0) for g in results) / len(results)
            st.markdown(f"""
            <div class="debug-box">
            <strong>🔍 Scan Complete:</strong><br>
            • Total new pairs: {len(new_pairs)}<br>
            • Gems found: {len(results)}<br>
            • Avg social score: {avg_social:.0f}/100<br>
            • Avg security score: {avg_security:.0f}/100
            </div>
            """, unsafe_allow_html=True)
        
        return results

# ==============================================================================
# STREAMLIT UI
# ==============================================================================
st.markdown('<div class="main-header">💎 DEGEN SOLANA HUNTER V5.4 💎</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">With RugCheck Security + Social Analysis 🛡️📱</div>', unsafe_allow_html=True)

st.sidebar.header("⚙️ Degen Configuration")
min_liq = st.sidebar.slider("Min Liquidity ($)", 500, 50000, 1000, step=500)
max_age = st.sidebar.slider("Max Age (Hours)", 1, 168, 24)
max_fdv = st.sidebar.slider("Max Market Cap ($)", 50000, 5000000, 500000, step=50000)
max_tokens = st.sidebar.slider("Tokens to Scan", 5, 50, 15, help="Lower = faster scan (RugCheck rate limits)")
debug_mode = st.sidebar.checkbox("🐛 Debug Mode")

st.sidebar.markdown("---")
st.sidebar.info("**V5.4 - RugCheck Integration:**\n• ✅ FREE social links (Twitter/Telegram/Website)\n• ✅ FREE mint authority check\n• ✅ FREE freeze authority check\n• ✅ FREE top holders analysis\n• ✅ FREE RugCheck risk score\n• NO API KEY NEEDED!")

if st.sidebar.button("🔌 Test API Connection"):
    hunter_test = SolanaMemecoinHunter(debug_mode=debug_mode)
    if hunter_test.test_connection():
        st.sidebar.success("✅ Connected!")
    else:
        st.sidebar.error("❌ Failed.")

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
        st.warning("⚠️ No gems found.")
    else:
        st.session_state['gems'] = gems

if 'gems' in st.session_state and st.session_state['gems']:
    gems = st.session_state['gems']
    
    st.markdown("### 🏆 Top Opportunities")
    cols = st.columns(4)
    cols[0].metric("Total Gems", len(gems))
    high_conviction = [g for g in gems if g['score'] >= 70]
    cols[1].metric("High Conviction (70+)", len(high_conviction))
    avg_social = sum(g.get('social_score', 0) for g in gems) / len(gems) if gems else 0
    cols[2].metric("Avg Social", f"{avg_social:.0f}/100")
    avg_security = sum(g.get('security_score', 0) for g in gems) / len(gems) if gems else 0
    cols[3].metric("Avg Security", f"{avg_security:.0f}/100")

    st.markdown("---")

    for i, gem in enumerate(gems[:15], 1):
        score_color = "🔴" if gem['score'] < 50 else "🟡" if gem['score'] < 70 else "🟢"
        sec_emoji = "🛡️" if gem.get('security_score', 0) >= 60 else "⚠️" if gem.get('security_score', 0) >= 30 else "🚨"
        
        with st.expander(f"#{i} {score_color} **${gem['symbol']}** | Score: **{gem['score']}/100** | Social: **{gem.get('social_score', 0)}** | Security: **{sec_emoji}{gem.get('security_score', 0)}**", expanded=(i <= 3)):
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown(f"**Contract:** `{gem['address']}`")
                st.markdown(f"**Price:** `${gem['price']:.10f}`")
                st.markdown(f"**Age:** `{gem['age_hours']:.1f}` hours")
                st.markdown(f"**Market Cap:** `${gem['fdv']:,.0f}`")
                st.markdown(f"**Liquidity:** `${gem['liquidity_usd']:,.0f}`")
            
            with col_b:
                st.markdown("**📈 Price Action:**")
                st.markdown(f"• 5m: `{gem['price_change_5m']:+.2f}%`")
                st.markdown(f"• 1h: `{gem['price_change_1h']:+.2f}%`")
                st.markdown(f"• 24h: `{gem['price_change_24h']:+.2f}%`")
                st.markdown(f"**🐋 Buy Pressure:** `{gem['buy_pressure_5m']:.1f}%`")

            # SOCIAL MEDIA SECTION (FIXED!)
            st.markdown("---")
            st.markdown("**📱 Social Media Presence:**")
            
            social_badges = gem.get('social_badges', [])
            if social_badges:
                badges_html = ""
                for badge_text, badge_url, badge_class in social_badges:
                    if badge_url:
                        badges_html += f'<a href="{badge_url}" target="_blank" class="social-badge {badge_class}">{badge_text}</a>'
                    else:
                        badges_html += f'<span class="social-badge {badge_class}">{badge_text}</span>'
                st.markdown(badges_html, unsafe_allow_html=True)
            else:
                st.warning("❌ No social links found on RugCheck")

            # SECURITY SECTION (NEW BONUS!)
            st.markdown("---")
            st.markdown("**🛡️ Security Analysis (from RugCheck):**")
            
            security_badges = gem.get('security_badges', [])
            if security_badges:
                sec_html = ""
                for badge_text, badge_type in security_badges:
                    sec_html += f'<span class="security-{badge_type}">{badge_text}</span>'
                st.markdown(sec_html, unsafe_allow_html=True)
            else:
                st.info("ℹ️ Security data not available for this token")

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
                    st.markdown("No strong signals")

            st.markdown("**🎯 Entry/Exit:**")
            plan_cols = st.columns(5)
            plan_cols[0].metric("Entry", f"${gem['price']:.8f}")
            plan_cols[1].metric("Stop", f"${gem['stop_loss']:.8f}", "-20%")
            plan_cols[2].metric("TP1", f"${gem['tp1']:.8f}", "+50%")
            plan_cols[3].metric("TP2", f"${gem['tp2']:.8f}", "+150%")
            plan_cols[4].metric("TP3", f"${gem['tp3']:.8f}", "+400%")

            # Links
            links = []
            if gem['url']:
                links.append(f"[🔗 DexScreener]({gem['url']})")
            links.append(f"[🛡️ RugCheck](https://rugcheck.xyz/tokens/{gem['address']})")
            links.append(f"[🔍 Solscan](https://solscan.io/token/{gem['address']})")
            
            st.markdown(" | ".join(links))

    st.markdown("---")
    df = pd.DataFrame(gems)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"solana_gems_v54_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

else:
    st.info("👈 Configure and click **START GEM HUNT**")

st.markdown("---")
st.markdown("""
<div style="background-color: #2b0000; padding: 1.5rem; border-radius: 0.5rem; border: 1px solid #FF4B4B;">
    <h3 style="color: #FF4B4B; margin-top: 0;">⚠️ DEGEN DISCLAIMER</h3>
    <ul style="color: #FFCCCC; line-height: 1.6;">
        <li><strong>Social metrics can be faked</strong> - bought followers, bot groups</li>
        <li><strong>Security checks are helpful but NOT foolproof</strong> - always DYOR</li>
        <li><strong>Even "safe" tokens can rug</strong> - dev can still dump their holdings</li>
        <li><strong>99% of new memecoins fail</strong> - only invest what you can lose</li>
    </ul>
    <p style="color: #FFCCCC; font-weight: bold; text-align: center; margin-bottom: 0;">NFA. Trade responsibly. 🫡</p>
</div>
""", unsafe_allow_html=True)
