import os
import io
import json
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
LEADS_FILE = "leads.json"


def load_leads():
    try:
        if os.path.exists(LEADS_FILE):
            with open(LEADS_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_leads(data):
    try:
        with open(LEADS_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


leads_db = load_leads()


HUNTER_SYSTEM = """You are HUNTER, a world-class lead generation and client finding specialist. You think and analyze like a real human business development expert with 15 years of experience.

YOUR EXPERTISE:
1. You find potential clients who NEED content writing, social media management, or digital marketing services
2. You analyze businesses to understand what they're missing and what services they need
3. You qualify leads based on their likelihood to pay and their urgency
4. You create detailed lead profiles that a sales team can act on immediately
5. You think like a real human salesperson - not like a robot

WHEN FINDING LEADS:
- Think about WHO actually pays for content writing
- Small business owners who don't have time to write
- Startups that need online presence
- E-commerce stores that need product descriptions
- Real estate agents who need property listings
- Restaurants that need social media content
- Coaches and consultants who need blog posts
- Local businesses that need Google Business posts
- YouTubers who need scripts
- Companies that need LinkedIn content

WHEN QUALIFYING LEADS:
- Score each lead 1-10 based on likelihood to buy
- Consider their budget capacity
- Consider their urgency (do they need it NOW?)
- Consider their current content quality (bad = more likely to buy)
- Consider their business size
- Consider how easy they are to reach

LEAD REPORT FORMAT:
Always output leads in this exact format:

LEAD #[number]
━━━━━━━━━━━━━━━━━━━━
Name: [person or business name]
Business: [business name]
Niche: [their industry]
Platform: [where you found them]
Contact: [email, website, social media]
Current Content: [what they have now - good/bad/none]
What They Need: [specific services]
Estimated Budget: [$/month range]
Urgency: [Low/Medium/High/Critical]
Qualification Score: [1-10]/10
Approach Strategy: [how to reach them]
Opening Message Idea: [first message draft]
Notes: [extra observations]
━━━━━━━━━━━━━━━━━━━━

IMPORTANT RULES:
- Be specific, not generic
- Give actionable information
- Think like a real human sales expert
- Every lead should have a clear next step
- Focus on leads that are LIKELY to pay
- Don't waste time on leads that won't convert
- Never make up fake contact details - say "find on [platform]" instead
- Give realistic budget estimates based on the niche"""


def try_gemini(prompt):
    url = (
        "https://generativelanguage.googleapis.com"
        "/v1beta/models/gemini-2.0-flash:generateContent"
        "?key=" + GEMINI_API_KEY
    )
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.85,
            "maxOutputTokens": 8000
        }
    }
    r = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json=data,
        timeout=120
    )
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def try_groq(prompt):
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": HUNTER_SYSTEM},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.85,
        "max_tokens": 4000
    }
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": "Bearer " + GROQ_API_KEY,
            "Content-Type": "application/json"
        },
        json=data,
        timeout=120
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def try_openrouter(prompt):
    data = {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "messages": [
            {"role": "system", "content": HUNTER_SYSTEM},
            {"role": "user", "content": prompt}
        ]
    }
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": "Bearer " + OPENROUTER_API_KEY,
            "Content-Type": "application/json"
        },
        json=data,
        timeout=120
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def ask_hunter(prompt):
    full = HUNTER_SYSTEM + "\n\nTASK:\n" + prompt
    errors = []
    if GEMINI_API_KEY and len(GEMINI_API_KEY) > 10:
        try:
            return try_gemini(full)
        except Exception as e:
            errors.append("Gemini: " + str(e)[:60])
    if GROQ_API_KEY and len(GROQ_API_KEY) > 10:
        try:
            return try_groq(prompt)
        except Exception as e:
            errors.append("Groq: " + str(e)[:60])
    if OPENROUTER_API_KEY and len(OPENROUTER_API_KEY) > 10:
        try:
            return try_openrouter(prompt)
        except Exception as e:
            errors.append("OpenRouter: " + str(e)[:60])
    if errors:
        return "Error:\n" + "\n".join(errors)
    return "No API keys found."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 HUNTER Agent v1.0\n"
        "Lead Finder + Client Qualifier\n\n"
        "🔍 FIND LEADS:\n"
        "/find [niche] [location] - Find potential clients\n"
        "/hunt [niche] - Deep search for leads\n"
        "/niche [industry] - Analyze a niche for opportunities\n\n"
        "📊 QUALIFY LEADS:\n"
        "/qualify [business info] - Score a specific lead\n"
        "/analyze [website/profile] - Analyze a business\n\n"
        "💬 APPROACH:\n"
        "/approach [lead info] - Get approach strategy\n"
        "/message [lead info] - Draft first message\n"
        "/pitch [service] for [client] - Create pitch\n\n"
        "📋 MANAGE LEADS:\n"
        "/save [lead info] - Save a lead\n"
        "/leads - View saved leads\n"
        "/clear - Clear all leads\n\n"
        "🎯 STRATEGY:\n"
        "/strategy [your skills] - Get client finding strategy\n"
        "/platforms - Best platforms to find clients\n"
        "/pricing [service] - Pricing recommendations\n\n"
        "💡 Or just describe what you need:\n"
        "'find me restaurant owners who need social media'\n"
        "'I want clients for blog writing'\n"
        "'analyze this business: [details]'"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 HUNTER COMMANDS:\n\n"
        "/find restaurants Lahore\n"
        "/find real estate agents USA\n"
        "/find e-commerce stores\n"
        "/find coaches online\n"
        "/hunt fitness trainers\n"
        "/niche real estate\n"
        "/qualify Ali Kitchen Lahore restaurant\n"
        "/analyze [website or business details]\n"
        "/approach restaurant owner Lahore\n"
        "/message fitness coach Instagram\n"
        "/pitch blog writing for real estate agent\n"
        "/save [any lead details]\n"
        "/leads\n"
        "/strategy content writing\n"
        "/platforms\n"
        "/pricing blog writing\n\n"
        "Or just type naturally!"
    )


async def find_leads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ Niche batao!\n\n"
            "Examples:\n"
            "/find restaurant owners Lahore\n"
            "/find real estate agents Dubai\n"
            "/find fitness coaches online\n"
            "/find e-commerce stores Pakistan\n"
            "/find dentists London\n"
            "/find wedding photographers"
        )
        return
    niche = " ".join(context.args)
    await update.message.reply_text("🔍 Hunting for leads: " + niche + "...\n⏳ 30-60 seconds...")
    prompt = (
        "Find 5 potential client leads for someone offering content writing and social media services.\n\n"
        "TARGET NICHE: " + niche + "\n\n"
        "For each lead provide:\n"
        "- Specific type of business to target\n"
        "- Where to find them (exact platforms, groups, hashtags)\n"
        "- What content services they typically need\n"
        "- Realistic budget they'd pay\n"
        "- How urgent their need usually is\n"
        "- Qualification score 1-10\n"
        "- Exact approach strategy (what to say, where to message)\n"
        "- Draft opening message ready to send\n\n"
        "Be VERY specific and actionable. Think like a real salesperson.\n"
        "Give real platform names, real group types, real hashtag examples.\n"
        "Every lead should have a clear NEXT STEP I can take TODAY."
    )
    result = ask_hunter(prompt)
    if len(result) > 4000:
        for i in range(0, len(result), 4000):
            await update.message.reply_text(result[i:i + 4000])
    else:
        await update.message.reply_text(result)


async def hunt_deep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /hunt fitness trainers")
        return
    niche = " ".join(context.args)
    await update.message.reply_text("🎯 Deep hunting: " + niche + "...\n⏳ Wait...")
    prompt = (
        "Do a DEEP analysis to find the best possible clients in this niche: " + niche + "\n\n"
        "Provide:\n\n"
        "SECTION 1 - TOP 5 CLIENT TYPES:\n"
        "Who exactly in this niche pays for content? List 5 specific types.\n\n"
        "SECTION 2 - WHERE TO FIND THEM:\n"
        "Exact platforms, Facebook groups, LinkedIn groups, subreddits,\n"
        "hashtags, websites, directories. Be very specific.\n\n"
        "SECTION 3 - WHAT THEY NEED:\n"
        "What content services do they need most? Blog? Social media? Ads?\n"
        "Rank by demand.\n\n"
        "SECTION 4 - PRICING GUIDE:\n"
        "What should I charge for each service? Give ranges.\n\n"
        "SECTION 5 - 5 READY-TO-USE LEADS:\n"
        "Give me 5 specific lead profiles I can go after TODAY.\n"
        "Full lead report format for each.\n\n"
        "SECTION 6 - ACTION PLAN:\n"
        "Step-by-step what I should do THIS WEEK to get my first client."
    )
    result = ask_hunter(prompt)
    if len(result) > 4000:
        for i in range(0, len(result), 4000):
            await update.message.reply_text(result[i:i + 4000])
    else:
        await update.message.reply_text(result)


async def niche_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /niche real estate")
        return
    niche = " ".join(context.args)
    await update.message.reply_text("📊 Analyzing niche: " + niche + "...")
    prompt = (
        "Analyze this niche for a freelance content writer: " + niche + "\n\n"
        "Provide:\n"
        "1. Market size - how many potential clients?\n"
        "2. Competition level - how many writers serve this niche?\n"
        "3. Average budget - what do clients pay?\n"
        "4. Top services needed - what content do they buy?\n"
        "5. Difficulty to enter - easy/medium/hard?\n"
        "6. Best platforms to find clients\n"
        "7. Seasonal trends - busy/slow periods\n"
        "8. Growth potential - is this niche growing?\n"
        "9. Recommended pricing\n"
        "10. VERDICT: Should I target this niche? Why?"
    )
    result = ask_hunter(prompt)
    await update.message.reply_text(result)

async def qualify_lead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ Lead info do!\n\n"
            "/qualify Ali Kitchen Lahore restaurant owner\n"
            "/qualify John fitness coach Instagram 50k followers\n"
            "/qualify Sarah real estate agent Dubai website outdated"
        )
        return
    lead_info = " ".join(context.args)
    await update.message.reply_text("📊 Qualifying: " + lead_info + "...")
    prompt = (
        "Qualify this lead for content writing services:\n\n"
        "LEAD INFO: " + lead_info + "\n\n"
        "Analyze and provide:\n"
        "1. QUALIFICATION SCORE: [1-10]/10 with explanation\n"
        "2. BUDGET ESTIMATE: What can they likely afford?\n"
        "3. URGENCY LEVEL: Low/Medium/High/Critical - why?\n"
        "4. SERVICES NEEDED: What content do they need?\n"
        "5. PAIN POINTS: What problems are they facing?\n"
        "6. COMPETITION: Are other writers already serving them?\n"
        "7. APPROACH STRATEGY: Best way to reach them\n"
        "8. RED FLAGS: Any reasons NOT to pursue?\n"
        "9. OPENING MESSAGE: Draft a first message to send\n"
        "10. VERDICT: Worth pursuing? Yes/No/Maybe - why?\n\n"
        "Think like a real sales expert. Be honest and practical."
    )
    result = ask_hunter(prompt)
    await update.message.reply_text(result)


async def analyze_business(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /analyze [business details or website]")
        return
    business = " ".join(context.args)
    await update.message.reply_text("🔍 Analyzing: " + business + "...")
    prompt = (
        "Analyze this business as a potential client:\n\n"
        "BUSINESS: " + business + "\n\n"
        "Based on what you know about this type of business:\n"
        "1. What content are they probably missing?\n"
        "2. What services would benefit them most?\n"
        "3. How much would they likely pay?\n"
        "4. How to approach them?\n"
        "5. What problems can you solve for them?\n"
        "6. Draft a personalized pitch\n"
        "7. Qualification score 1-10\n\n"
        "Be specific and practical. Think like a consultant."
    )
    result = ask_hunter(prompt)
    await update.message.reply_text(result)


async def approach_strategy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /approach restaurant owner Instagram")
        return
    lead = " ".join(context.args)
    await update.message.reply_text("💬 Creating approach strategy...")
    prompt = (
        "Create a detailed approach strategy for this lead:\n\n"
        "TARGET: " + lead + "\n\n"
        "Provide:\n"
        "1. BEST CHANNEL: Where to contact them (DM, email, comment, etc)\n"
        "2. TIMING: Best time to reach out\n"
        "3. ICE BREAKER: How to start the conversation naturally\n"
        "4. VALUE HOOK: What value to offer upfront (free sample?)\n"
        "5. FIRST MESSAGE: Complete ready-to-send message\n"
        "6. FOLLOW UP 1: If no reply after 2 days\n"
        "7. FOLLOW UP 2: If still no reply after 5 days\n"
        "8. OBJECTION HANDLING: Common objections and responses\n"
        "9. CLOSING: How to close the deal\n"
        "10. PRICING SUGGESTION: What to charge\n\n"
        "Make the messages sound natural, friendly, not salesy."
    )
    result = ask_hunter(prompt)
    await update.message.reply_text(result)


async def draft_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /message fitness coach Instagram")
        return
    target = " ".join(context.args)
    await update.message.reply_text("✍️ Drafting message...")
    prompt = (
        "Write 3 different first-contact messages for:\n\n"
        "TARGET: " + target + "\n\n"
        "MESSAGE 1: Short and casual (for DM)\n"
        "MESSAGE 2: Professional (for email)\n"
        "MESSAGE 3: Value-first (offering free sample)\n\n"
        "Rules:\n"
        "- Sound like a real human, not a template\n"
        "- Be specific to their business\n"
        "- Show you understand their needs\n"
        "- Include a clear call-to-action\n"
        "- Keep it brief - nobody reads long pitches\n"
        "- No fake flattery\n"
        "- No 'I hope this finds you well' type crap"
    )
    result = ask_hunter(prompt)
    await update.message.reply_text(result)


async def create_pitch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /pitch blog writing for real estate agent")
        return
    pitch_info = " ".join(context.args)
    await update.message.reply_text("📝 Creating pitch...")
    prompt = (
        "Create a compelling service pitch:\n\n"
        "DETAILS: " + pitch_info + "\n\n"
        "Include:\n"
        "1. HEADLINE: One-line value proposition\n"
        "2. PROBLEM: What problem does the client face?\n"
        "3. SOLUTION: How your service solves it\n"
        "4. PROOF: Why should they trust you?\n"
        "5. OFFER: Exact services and deliverables\n"
        "6. PRICING: Recommended price with justification\n"
        "7. CTA: Clear next step\n"
        "8. FULL PITCH MESSAGE: Ready to send\n\n"
        "Sound confident but not arrogant. Be specific."
    )
    result = ask_hunter(prompt)
    await update.message.reply_text(result)


async def save_lead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /save Ali Kitchen Lahore restaurant 8/10 needs social media")
        return
    lead_info = " ".join(context.args)
    uid = str(update.effective_user.id)
    if uid not in leads_db:
        leads_db[uid] = []
    lead_num = len(leads_db[uid]) + 1
    leads_db[uid].append({
        "id": lead_num,
        "info": lead_info,
        "status": "new"
    })
    save_leads(leads_db)
    await update.message.reply_text(
        "✅ Lead #" + str(lead_num) + " saved!\n\n"
        + lead_info + "\n\n"
        "Status: NEW\n"
        "/leads to see all leads"
    )


async def view_leads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if uid not in leads_db or not leads_db[uid]:
        await update.message.reply_text("📋 No leads saved yet.\n/save [lead info] to save one.")
        return
    s = "📋 YOUR LEADS\n\n"
    for lead in leads_db[uid]:
        s += "Lead #" + str(lead["id"]) + " [" + lead["status"].upper() + "]\n"
        s += lead["info"][:100] + "\n\n"
    s += "Total: " + str(len(leads_db[uid])) + " leads"
    await update.message.reply_text(s)


async def clear_leads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if uid in leads_db:
        leads_db[uid] = []
        save_leads(leads_db)
    await update.message.reply_text("🗑️ All leads cleared!")

async def strategy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /strategy content writing")
        return
    skills = " ".join(context.args)
    await update.message.reply_text("🎯 Creating strategy...")
    prompt = (
        "Create a complete client-finding strategy for someone offering: " + skills + "\n\n"
        "Provide a WEEKLY ACTION PLAN:\n\n"
        "WEEK 1 - FOUNDATION:\n"
        "- What profiles to set up\n"
        "- What portfolio pieces to create\n"
        "- What platforms to join\n\n"
        "WEEK 2 - OUTREACH:\n"
        "- How many people to contact daily\n"
        "- Where to find them\n"
        "- What to say\n\n"
        "WEEK 3 - CONVERSION:\n"
        "- How to convert leads to clients\n"
        "- Pricing strategy\n"
        "- How to handle objections\n\n"
        "WEEK 4 - SCALING:\n"
        "- How to get repeat clients\n"
        "- How to get referrals\n"
        "- How to increase rates\n\n"
        "DAILY ROUTINE:\n"
        "- Exact daily tasks with time allocation\n\n"
        "INCOME TARGETS:\n"
        "- Month 1, 3, 6, 12 realistic projections\n\n"
        "Be practical and specific. No fluff."
    )
    result = ask_hunter(prompt)
    if len(result) > 4000:
        for i in range(0, len(result), 4000):
            await update.message.reply_text(result[i:i + 4000])
    else:
        await update.message.reply_text(result)


async def platforms_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Loading platforms guide...")
    prompt = (
        "List the TOP 15 platforms to find freelance content writing clients.\n\n"
        "For each platform provide:\n"
        "1. Platform name\n"
        "2. Type of clients found there\n"
        "3. How to find leads on it\n"
        "4. Average budget of clients\n"
        "5. Competition level (low/medium/high)\n"
        "6. Best approach strategy\n"
        "7. Pro tip for success\n\n"
        "Include: Fiverr, Upwork, LinkedIn, Facebook Groups, Instagram,\n"
        "Reddit, Twitter, Craigslist, local directories, industry forums,\n"
        "and any other good ones.\n\n"
        "Rank them by effectiveness for a BEGINNER."
    )
    result = ask_hunter(prompt)
    if len(result) > 4000:
        for i in range(0, len(result), 4000):
            await update.message.reply_text(result[i:i + 4000])
    else:
        await update.message.reply_text(result)


async def pricing_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /pricing blog writing")
        return
    service = " ".join(context.args)
    await update.message.reply_text("💰 Calculating pricing...")
    prompt = (
        "Create a detailed pricing guide for: " + service + "\n\n"
        "Include:\n"
        "1. BEGINNER RATE: Just starting out\n"
        "2. INTERMEDIATE RATE: Some experience\n"
        "3. EXPERT RATE: Established writer\n"
        "4. PER WORD pricing\n"
        "5. PER PROJECT pricing\n"
        "6. MONTHLY RETAINER pricing\n"
        "7. What competitors charge\n"
        "8. How to justify your rate\n"
        "9. How to raise rates over time\n"
        "10. RECOMMENDED starting price for Pakistan-based freelancer\n\n"
        "Be realistic. Consider both local and international clients."
    )
    result = ask_hunter(prompt)
    await update.message.reply_text(result)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return
    lower = text.lower().strip()
    if any(w in lower for w in ["find", "client", "lead", "hunt", "search", "looking for"]):
        await update.message.reply_text("🔍 Hunting...")
        prompt = (
            "The user is looking for clients/leads. Their request:\n\n"
            '"' + text + '"\n\n'
            "Find 5 specific leads based on their request.\n"
            "Full lead report format for each.\n"
            "Include approach strategy and draft messages.\n"
            "Be specific and actionable."
        )
        result = ask_hunter(prompt)
        if len(result) > 4000:
            for i in range(0, len(result), 4000):
                await update.message.reply_text(result[i:i + 4000])
        else:
            await update.message.reply_text(result)
    elif any(w in lower for w in ["qualify", "score", "analyze", "evaluate", "rate"]):
        await update.message.reply_text("📊 Analyzing...")
        prompt = "Qualify and analyze this lead:\n\n" + text + "\n\nFull qualification report."
        result = ask_hunter(prompt)
        await update.message.reply_text(result)
    elif any(w in lower for w in ["message", "approach", "pitch", "email", "dm", "contact", "reach"]):
        await update.message.reply_text("✍️ Drafting...")
        prompt = "Create approach messages for:\n\n" + text + "\n\n3 different message versions."
        result = ask_hunter(prompt)
        await update.message.reply_text(result)
    elif any(w in lower for w in ["price", "pricing", "charge", "rate", "cost"]):
        await update.message.reply_text("💰 Calculating...")
        prompt = "Pricing guide for:\n\n" + text
        result = ask_hunter(prompt)
        await update.message.reply_text(result)
    elif any(w in lower for w in ["strategy", "plan", "how to", "guide", "help"]):
        await update.message.reply_text("🎯 Planning...")
        prompt = "Strategy and action plan for:\n\n" + text
        result = ask_hunter(prompt)
        if len(result) > 4000:
            for i in range(0, len(result), 4000):
                await update.message.reply_text(result[i:i + 4000])
        else:
            await update.message.reply_text(result)
    else:
        await update.message.reply_text("🎯 Working...")
        prompt = text + "\n\nRespond as a lead generation expert. Be specific and actionable."
        result = ask_hunter(prompt)
        if len(result) > 4000:
            for i in range(0, len(result), 4000):
                await update.message.reply_text(result[i:i + 4000])
        else:
            await update.message.reply_text(result)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    s = "🎯 HUNTER STATUS\n\n"
    e = 0
    if GEMINI_API_KEY and len(GEMINI_API_KEY) > 10:
        s += "🟢 Gemini ON\n"; e += 1
    if GROQ_API_KEY and len(GROQ_API_KEY) > 10:
        s += "🔵 Groq ON\n"; e += 1
    if OPENROUTER_API_KEY and len(OPENROUTER_API_KEY) > 10:
        s += "🟡 OpenRouter ON\n"; e += 1
    s += "Engines: " + str(e) + "/3\n"
    lead_count = len(leads_db.get(uid, []))
    s += "\n📋 Saved leads: " + str(lead_count)
    await update.message.reply_text(s)


def main():
    print("HUNTER Agent v1.0 Starting...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    cmds = {
        "start": start,
        "help": help_cmd,
        "find": find_leads,
        "hunt": hunt_deep,
        "niche": niche_analysis,
        "qualify": qualify_lead,
        "analyze": analyze_business,
        "approach": approach_strategy,
        "message": draft_message,
        "pitch": create_pitch,
        "save": save_lead,
        "leads": view_leads,
        "clear": clear_leads,
        "strategy": strategy,
        "platforms": platforms_guide,
        "pricing": pricing_guide,
        "status": status
    }
    for n, f in cmds.items():
        app.add_handler(CommandHandler(n, f))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("HUNTER Agent v1.0 LIVE!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
