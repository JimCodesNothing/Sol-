import streamlit as st
import pandas as pd
import requests
import warnings
from datetime import datetime
import time
import re

warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="🚀 Degen Solana Hunter V5.3.1",
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
    .social-badge {display: inline-block; padding: 0.2rem 0.5rem; border-radius: 0.3rem; margin: 0.1rem; font-size: 0.8rem;}
    .social-twitter {background-color: #1DA1F2; color: white;}
    .social-telegram {background-color: #0088cc; color: white;}
    .social-website {background-color: #28a745; color: white;}
    .social-none {background-color: #dc3545; color: white;}
    </style>
""", unsafe_allow_html=True)

class SocialSentimentAnalyzer:
    """Free social sentiment analysis without API keys"""
    
    @staticmethod
    def check_telegram_members(telegram_url):
        """Try to get Telegram member count"""
        if not telegram_url:
            return None
        
        try:
            if 't.me/' in telegram_url:
                username = telegram_url.split('t.me/')[-1].split('?')[0].split('/')[0]
            elif 'telegram.me/' in telegram_url:
                username = telegram_url.split('telegram.me/')[-1].split('?')[0].split('/')[0]
            else:
                return None
            
            url = f"https://t.me/{username}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*(?:members|subscribers)', response.text, re.I)
                if match:
                    members = int(match.group(1).replace(',', ''))
                    return members
            return None
        except Exception:
            return None
    
    @staticmethod
    def check_twitter_followers(twitter_url):
        """Try to get Twitter follower count"""
        if not twitter_url:
            return None
        
        try:
            if 'twitter.com/' in twitter_url:
                username = twitter_url.split('twitter.com/')[-1].split('?')[0].split('/')[0]
            elif 'x.com/' in twitter_url:
                username = twitter_url.split('x.com/')[-1].split('?')[0].split('/')[0]
            else:
                return None
            
            nitter_url = f"https://nitter.net/{username}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(nitter_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*Followers', response.text)
                if match:
                    followers = int(match.group(1).replace(',', ''))
                    return followers
            return None
        except Exception:
            return None
    
    @staticmethod
    def analyze_social_presence(info):
        """Analyze social media presence from DexScreener info"""
        twitter = info.get('twitter')
        telegram = info.get('telegram')
        website = info.get('website')
        
        social_score = 0
        social_badges = []
        
        # Check Twitter
        if twitter:
            followers = SocialSentimentAnalyzer.check_twitter_followers(twitter)
            if followers:
                if followers > 10000:
                    social_score += 30
                    social_badges.append(f"🐦 Twitter: {followers:,} followers")
                elif followers > 1000:
                    social_score += 20
                    social_badges.append(f"🐦 Twitter: {followers:,} followers")
                elif followers > 100:
                    social_score += 10
                    social_badges.append(f"🐦 Twitter: {followers:,} followers")
                else:
                    social_score += 5
                    social_badges.append("🐦 Twitter (small)")
            else:
                social_score += 5
                social_badges.append("🐦 Twitter")
        else:
            social_badges.append("❌ No Twitter")
        
        # Check Telegram
        if telegram:
            members = SocialSentimentAnalyzer.check_telegram_members(telegram)
            if members:
                if members > 5000:
                    social_score += 30
                    social_badges.append(f"✈️ Telegram: {members:,} members")
                elif members > 1000:
                    social_score += 20
                    social_badges.append(f"✈️ Telegram: {members:,} members")
                elif members > 100:
                    social_score += 10
                    social_badges.append(f"✈️ Telegram: {members:,} members")
                else:
                    social_score += 5
                    social_badges.append("✈️ Telegram (small)")
            else:
                social_score += 5
                social_badges.append("✈️ Telegram")
        else:
            social_badges.append("❌ No Telegram")
        
        # Check Website
        if website:
            social_score += 10
            social_badges.append("🌐 Website")
        else:
            social_badges.append("❌ No Website")
        
        return {
            'social_score': min(100, social_score),
            'badges': social_badges,
            'has_twitter': bool(twitter),
            'has_telegram': bool(telegram),
            'has_website': bool(website)
        }

class SolanaMemecoinHunter:
    def __init__(self, min_liquidity=1000, max_age_hours=24, max_fdv=500000, debug_mode=False):
        self.min_liquidity = min_liquidity
        self.max_age_hours = max_age_hours
        self.max_fdv = max_fdv
        self.debug_mode = debug_mode
        self.dexscreener_base = "https://api.dexscreener.com/latest/dex"
        self.social_analyzer = SocialSentimentAnalyzer()

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
        """Convert DexScreener pair to gem format with social data"""
        base_token = pair_data.get('baseToken', {}) or {}
        symbol = base_token.get('symbol', 'UNK')
        name = base_token.get('name', 'Unknown')
        address = base_token.get('address', '')
        
        if 'dex' in name.lower() or 'dex' in symbol.lower():
            return None
        
        info = pair_data.get('info', {}) or {}
        
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
        
        # Analyze social presence
        social_data = self.social_analyzer.analyze_social_presence(info)
        
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
            'social_score': social_data['social_score'],
            'social_badges': social_data['badges'],
            'has_social': social_data['has_twitter'] or social_data['has_telegram'],
            'reddit_posts_24h': 0,
            'reddit_comments_24h': 0,
            'reddit_engagement': 0,
            'twitter_url': info.get('twitter'),
            'telegram_url': info.get('telegram'),
            'website_url': info.get('website')
        }

    def detect_memecoin_signals(self, gem):
        """Score and analyze a gem with social metrics"""
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
            score += 25
            signals.append(f"🆕 BRAND NEW: {gem['age_hours']*60:.0f} minutes old!")
        elif gem['age_hours'] < 6:
            score += 20
            signals.append(f"🌟 Very new: {gem['age_hours']:.1f}h old")
        elif gem['age_hours'] < 12:
            score += 15
            signals.append(f"✨ Fresh: {gem['age_hours']:.1f}h old")

        # 6. MARKET CAP
        if gem['fdv'] > 0:
            if gem['fdv'] > self.max_fdv:
                score -= 30
                risk_flags.append(f"🔴 Large cap: ${gem['fdv']:,.0f}")
            elif gem['fdv'] < 50000:
                score += 15
                signals.append(f"💎 Micro cap: ${gem['fdv']:,.0f}")

        # 7. SOCIAL SENTIMENT
        social_score = gem.get('social_score', 0)
        if social_score >= 60:
            score += 20
            signals.append(f"💬 Strong social presence (score: {social_score})")
        elif social_score >= 30:
            score += 10
            signals.append(f"💬 Moderate social presence")
        elif social_score == 0:
            risk_flags.append("🚩 No social media presence")
            score -= 20

        # 8. RUG CHECKS
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
            status_text.text(f"📊 Analyzing {len(new_pairs)} pairs with social metrics...")
        
        results = []
        seen_addresses = set()
        
        for i, pair in enumerate(new_pairs):
            if progress_bar:
                progress_bar.progress(min(1.0, (i + 1) / len(new_pairs)))
            
            if len(results) >= max_tokens:
                break
            
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
            
            if status_text and i % 5 == 0:
                status_text.text(f"📊 Analyzing... ({i+1}/{len(new_pairs)}) Checking social metrics...")
            
            time.sleep(0.3)
        
        results.sort(key=lambda x: x['score'], reverse=True)
        
        if self.debug_mode and results:
            avg_social = sum(g.get('social_score', 0) for g in results) / len(results)
            st.markdown(f"""
            <div class="debug-box">
            <strong>🔍 Scan Complete:</strong><br>
            • Total new pairs: {len(new_pairs)}<br>
            • Gems found: {len(results)}<br>
            • Avg social score: {avg_social:.0f}/100
            </div>
            """, unsafe_allow_html=True)
        
        return results

# ==============================================================================
# STREAMLIT UI
# ==============================================================================
st.markdown('<div class="main-header">💎 DEGEN SOLANA HUNTER V5.3.1 💎</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">With Social Sentiment & Community Analysis 📱</div>', unsafe_allow_html=True)

st.sidebar.header("⚙️ Degen Configuration")
min_liq = st.sidebar.slider("Min Liquidity ($)", 500, 50000, 1000, step=500)
max_age = st.sidebar.slider("Max Age (Hours)", 1, 168, 24)
max_fdv = st.sidebar.slider("Max Market Cap ($)", 50000, 5000000, 500000, step=50000)
max_tokens = st.sidebar.slider("Tokens to Scan", 10, 100, 20)
debug_mode = st.sidebar.checkbox("🐛 Debug Mode")

st.sidebar.markdown("---")
st.sidebar.info("**V5.3.1 - Social Sentiment:**\n• Analyzes Twitter follower count\n• Checks Telegram member count\n• Social presence scoring\n• Community engagement metrics")

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
    
    st.markdown("### 🏆 Top Opportunities with Social Metrics")
    cols = st.columns(3)
    cols[0].metric("Total Gems", len(gems))
    high_conviction = [g for g in gems if g['score'] >= 70]
    cols[1].metric("High Conviction (70+)", len(high_conviction))
    avg_social = sum(g.get('social_score', 0) for g in gems) / len(gems) if gems else 0
    cols[2].metric("Avg Social Score", f"{avg_social:.0f}/100")

    st.markdown("---")

    for i, gem in enumerate(gems[:15], 1):
        score_color = "🔴" if gem['score'] < 50 else "🟡" if gem['score'] < 70 else "🟢"
        
        with st.expander(f"#{i} {score_color} **${gem['symbol']}** | Score: **{gem['score']}/100** | Social: **{gem.get('social_score', 0)}/100**", expanded=(i <= 3)):
            
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

            # Social Media Section
            st.markdown("---")
            st.markdown("**📱 Social Media Presence:**")
            
            badges_html = ""
            for badge in gem.get('social_badges', []):
                if 'Twitter' in badge:
                    badges_html += f'<span class="social-badge social-twitter">{badge}</span>'
                elif 'Telegram' in badge:
                    badges_html += f'<span class="social-badge social-telegram">{badge}</span>'
                elif 'Website' in badge:
                    badges_html += f'<span class="social-badge social-website">{badge}</span>'
                elif 'No' in badge or '❌' in badge:
                    badges_html += f'<span class="social-badge social-none">{badge}</span>'
            
            st.markdown(badges_html, unsafe_allow_html=True)

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
            if gem.get('twitter_url'):
                links.append(f"[🐦 Twitter]({gem['twitter_url']})")
            if gem.get('telegram_url'):
                links.append(f"[✈️ Telegram]({gem['telegram_url']})")
            if gem.get('website_url'):
                links.append(f"[🌐 Website]({gem['website_url']})")
            links.append(f"[🔍 Solscan](https://solscan.io/token/{gem['address']})")
            
            st.markdown(" | ".join(links))

    st.markdown("---")
    df = pd.DataFrame(gems)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"solana_gems_social_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

else:
    st.info("👈 Configure and click **START GEM HUNT**")

st.markdown("---")
st.markdown("""
<div style="background-color: #2b0000; padding: 1.5rem; border-radius: 0.5rem; border: 1px solid #FF4B4B;">
    <h3 style="color: #FF4B4B; margin-top: 0;">⚠️ DEGEN DISCLAIMER</h3>
    <ul style="color: #FFCCCC; line-height: 1.6;">
        <li><strong>Social metrics can be faked</strong> - bots, bought followers, fake Telegram members</li>
        <li><strong>High social score ≠ safe investment</strong> - many scams have huge communities</li>
        <li><strong>Always DYOR</strong> - check RugCheck.xyz, read the contract, verify team</li>
        <li><strong>99% of new memecoins fail</strong> - only invest what you can lose</li>
    </ul>
    <p style="color: #FFCCCC; font-weight: bold; text-align: center; margin-bottom: 0;">NFA. Trade responsibly. 🫡</p>
</div>
""", unsafe_allow_html=True)
