"""
================================================================================
  🎛️ Dark Angel Voice AI — Per-User Assistant Settings & Voice Catalog
================================================================================
  Provides dynamic per-user personalization for:
  - 🗣️ 25+ Realistic Indian & Global AI Voices (Cartesia, Sarvam, ElevenLabs)
  - 🧠 State-of-the-Art LLMs (GPT-4o Mini, GPT-4o, Claude 3.5 Sonnet, Gemini Flash, DeepSeek)
  - 🎧 Telephony-Optimized STT Providers (Soniox, Sarvam AI, Deepgram Nova-2)
  - 🌐 Native Indian & Global Languages with Auto-Switch
  - ⏱️ Speech Pacing & Voice Speed (0.85x, 1.0x, 1.15x)
================================================================================
"""

from typing import Dict, Any, List

AVAILABLE_VOICES: Dict[str, Dict[str, Any]] = {
    # --- Page 1: Indian Female & Conversational Persona Voices ---
    "v_riya": {
        "name": "Riya - College Roommate",
        "gender": "Feminine",
        "lang": "Hindi / Hinglish",
        "provider": "Cartesia",
        "voice_id": "riya-hi-conversational",
        "desc": "Playful, warm, friendly woman for engaging dialogues"
    },
    "v_kavita": {
        "name": "Kavita - Customer Care Agent",
        "gender": "Feminine",
        "lang": "Hindi",
        "provider": "Cartesia",
        "voice_id": "kavita-hi-support",
        "desc": "Mature, polite Indian female for customer service & care"
    },
    "v_aarti": {
        "name": "Aarti - Conversationalist",
        "gender": "Feminine",
        "lang": "Hindi / Hinglish",
        "provider": "Cartesia",
        "voice_id": "aarti-hi-natural",
        "desc": "Relatable dialogue & natural conversation flow"
    },
    "v_anjali": {
        "name": "ANJALI - Support & Calling",
        "gender": "Feminine",
        "lang": "Hindi / Kumaoni",
        "provider": "Cartesia",
        "voice_id": "anjali-hi-kumaoni",
        "desc": "Clear, polite & human-like for service follow-ups"
    },
    "v_reena": {
        "name": "Reena - Soft Tone Hindi",
        "gender": "Feminine",
        "lang": "Hindi",
        "provider": "Cartesia",
        "voice_id": "reena-hi-soft",
        "desc": "Gentle, clear & pleasant female voice"
    },
    "v_priti": {
        "name": "Priti - Energetic Youth",
        "gender": "Feminine",
        "lang": "Hindi",
        "provider": "Cartesia",
        "voice_id": "priti-hi-energetic",
        "desc": "Young, energetic & dynamic sales caller"
    },
    "v_zoya": {
        "name": "Zoya - Young Indian Girl",
        "gender": "Feminine",
        "lang": "Hindi",
        "provider": "Cartesia",
        "voice_id": "zoya-hi-young",
        "desc": "Natural, sweet & expressive young female"
    },
    "v_svaara": {
        "name": "Svaara - Telecaller & Lead Qualifier",
        "gender": "Feminine",
        "lang": "Hindi",
        "provider": "Cartesia",
        "voice_id": "svaara-hi-qualifier",
        "desc": "Filters leads & books appointments naturally"
    },

    # --- Page 2: Indian Male & Persona Clones ---
    "v_ayush": {
        "name": "Ayush - Friendly Neighbor",
        "gender": "Masculine",
        "lang": "Hindi",
        "provider": "Cartesia",
        "voice_id": "ayush-hi-friendly",
        "desc": "Confident young Indian male for demos & instructions"
    },
    "v_suraj": {
        "name": "Suraj - Fluent Hindi Youth",
        "gender": "Masculine",
        "lang": "Hindi",
        "provider": "Cartesia",
        "voice_id": "suraj-hi-fluent",
        "desc": "Calm, expressive, friendly & helpful assistant"
    },
    "v_punit": {
        "name": "Punit - Deep Cinematic Narration",
        "gender": "Masculine",
        "lang": "Hindi / English",
        "provider": "Cartesia",
        "voice_id": "punit-hi-cinematic",
        "desc": "Deep, mysterious, authoritative & engaging tone"
    },
    "v_amit": {
        "name": "AMIT - Coach & Client Follow-up",
        "gender": "Masculine",
        "lang": "Hindi",
        "provider": "Cartesia",
        "voice_id": "amit-hi-coach",
        "desc": "Professional & friendly coach persona"
    },
    "v_aniket": {
        "name": "Mr. Aniket Chaturvedi - Confident Male",
        "gender": "Masculine",
        "lang": "Hindi",
        "provider": "Cartesia",
        "voice_id": "aniket-hi-motivational",
        "desc": "Motivational, energetic & relatable for Indian audience"
    },
    "v_vikas": {
        "name": "Vikas Ji - Mature Senior Consultant",
        "gender": "Masculine",
        "lang": "Hindi / Haryanvi",
        "provider": "Cartesia",
        "voice_id": "vikas-hi-consultant",
        "desc": "Deep, mature (45-50y) & trustworthy clinic coordinator"
    },
    "v_nakul": {
        "name": "Nakul - Real Estate Property Consultant",
        "gender": "Masculine",
        "lang": "Hindi (Jaipur)",
        "provider": "Cartesia",
        "voice_id": "nakul-hi-realtor",
        "desc": "Trustworthy, humble & confident property advisor"
    },
    "v_aftab": {
        "name": "Aftab - Hospitality & Restaurant Concierge",
        "gender": "Masculine",
        "lang": "Hinglish",
        "provider": "Cartesia",
        "voice_id": "aftab-hi-concierge",
        "desc": "Calm, polite, soft & premium customer approach"
    },
    "v_krishna": {
        "name": "Krishna - Male Hindi Natural",
        "gender": "Masculine",
        "lang": "Hindi",
        "provider": "Cartesia",
        "voice_id": "krishna-hi-natural",
        "desc": "Direct, clear & natural male speaker"
    },
    "v_shivkishor": {
        "name": "Shivkishor - Professional Support",
        "gender": "Masculine",
        "lang": "English / Hindi",
        "provider": "Cartesia",
        "voice_id": "shivkishor-en-hi",
        "desc": "Moderate pace, polite & conversational style"
    },

    # --- Page 3: Global, Regional & Native Engine Voices ---
    "v_sarvam_male": {
        "name": "Sarvam - Shuddh Hindi Male",
        "gender": "Masculine",
        "lang": "Shuddh Hindi",
        "provider": "Sarvam AI",
        "voice_id": "sarvam-shuddh-male",
        "desc": "Native Indian STT/TTS with pure Hindi intonation"
    },
    "v_sarvam_female": {
        "name": "Sarvam - Shuddh Hindi Female",
        "gender": "Feminine",
        "lang": "Shuddh Hindi",
        "provider": "Sarvam AI",
        "voice_id": "sarvam-shuddh-female",
        "desc": "Clear, cultured native Indian female voice"
    },
    "v_sweta": {
        "name": "Sweta - Soft North Indian Accent",
        "gender": "Feminine",
        "lang": "Hindi",
        "provider": "Cartesia",
        "voice_id": "sweta-hi-north",
        "desc": "Soft, natural conversational Hindi tone"
    },
    "v_aman": {
        "name": "Aman v2 - North Indian (UP Accent)",
        "gender": "Masculine",
        "lang": "Hindi",
        "provider": "Cartesia",
        "voice_id": "aman-hi-up",
        "desc": "Authentic North Indian / UP accent flow"
    },
    "v_riyasharma": {
        "name": "Riya Sharma - Natural Sales Assistant",
        "gender": "Feminine",
        "lang": "Hinglish",
        "provider": "Cartesia",
        "voice_id": "riyasharma-hinglish",
        "desc": "Friendly, polite (20-25y) smart sales assistant"
    },
    "v_eleven_rachel": {
        "name": "ElevenLabs - Rachel (Global Female)",
        "gender": "Feminine",
        "lang": "English / Multilingual",
        "provider": "ElevenLabs",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "desc": "Global calm, professional & emotive female"
    },
    "v_eleven_adam": {
        "name": "ElevenLabs - Adam (Global Male)",
        "gender": "Masculine",
        "lang": "English / Multilingual",
        "provider": "ElevenLabs",
        "voice_id": "pNInz6obpgDQGcFmaJgB",
        "desc": "Deep, authoritative narration & conversational male"
    }
}

AVAILABLE_MODELS: Dict[str, Dict[str, Any]] = {
    "m_gpt4mini": {
        "name": "GPT-4o Mini (Ultra-Fast & Emotive — Recommended)",
        "short_name": "GPT-4o Mini ⚡",
        "model_id": "gpt-4o-mini",
        "desc": "Low latency (sub-200ms), highly expressive & conversational"
    },
    "m_gpt4o": {
        "name": "GPT-4o (Omni Reasoning & Complex Dialogue)",
        "short_name": "GPT-4o 🧠",
        "model_id": "gpt-4o",
        "desc": "Best for complex objection handling & multi-turn discussions"
    },
    "m_claude_sonnet": {
        "name": "Claude 3.5 Sonnet (Natural Nuance & Human Flow)",
        "short_name": "Claude 3.5 Sonnet 🎭",
        "model_id": "claude-3-5-sonnet",
        "desc": "Exceptional empathy, human tone & natural pauses"
    },
    "m_gemini_flash": {
        "name": "Gemini 1.5 Flash (Sub-200ms Telephony)",
        "short_name": "Gemini 1.5 Flash ⚡",
        "model_id": "gemini-1.5-flash",
        "desc": "Ultra-fast response generation for quick exchanges"
    },
    "m_deepseek": {
        "name": "DeepSeek Chat (Dynamic Conversationalist)",
        "short_name": "DeepSeek Chat 💡",
        "model_id": "deepseek-chat",
        "desc": "Intelligent, creative & adaptive dialogue execution"
    }
}

AVAILABLE_STT: Dict[str, Dict[str, Any]] = {
    "stt_soniox": {
        "name": "Soniox (Indian & Global Accents — Telephony Optimized)",
        "short_name": "Soniox 🎧",
        "provider_id": "soniox",
        "desc": "Superior accuracy across diverse Indian & global accents"
    },
    "stt_sarvam": {
        "name": "Sarvam AI (Native Indian Languages & Dialects)",
        "short_name": "Sarvam AI 🇮🇳",
        "provider_id": "sarvam",
        "desc": "Specialized for Indian regional accents and pure Hindi"
    },
    "stt_deepgram": {
        "name": "Deepgram Nova-2 (Ultra-Low Latency Telephony)",
        "short_name": "Deepgram Nova-2 ⚡",
        "provider_id": "deepgram",
        "desc": "Industry-leading speech recognition speed for live calling"
    }
}

AVAILABLE_LANGUAGES: Dict[str, Dict[str, Any]] = {
    "lang_hindi": {"name": "🇮🇳 Hindi (हिन्दी)", "short_name": "Hindi", "code": "hi"},
    "lang_hinglish": {"name": "🇮🇳 Hinglish (Conversational Mix)", "short_name": "Hinglish", "code": "hi-IN-en"},
    "lang_english": {"name": "🇬🇧 English (Indian / Global)", "short_name": "English", "code": "en"},
    "lang_marathi": {"name": "🇮🇳 Marathi (मराठी)", "short_name": "Marathi", "code": "mr"},
    "lang_bengali": {"name": "🇮🇳 Bengali (বাংলা)", "short_name": "Bengali", "code": "bn"},
    "lang_tamil": {"name": "🇮🇳 Tamil (தமிழ்)", "short_name": "Tamil", "code": "ta"},
    "lang_telugu": {"name": "🇮🇳 Telugu (తెలుగు)", "short_name": "Telugu", "code": "te"},
    "lang_gujarati": {"name": "🇮🇳 Gujarati (ગુજરાતી)", "short_name": "Gujarati", "code": "gu"},
    "lang_punjabi": {"name": "🇮🇳 Punjabi (ਪੰਜਾਬੀ)", "short_name": "Punjabi", "code": "pa"},
    "lang_auto": {"name": "🌐 Multi-Lingual Auto-Switch (90+ Locales)", "short_name": "Auto (90+)", "code": "auto"}
}

AVAILABLE_SPEEDS: Dict[str, Dict[str, Any]] = {
    "spd_slow": {"name": "🐢 Slow & Calm (0.85x)", "short_name": "Slow (0.85x)", "rate": 0.85},
    "spd_normal": {"name": "⚡ Normal (1.0x — Standard)", "short_name": "Normal (1.0x)", "rate": 1.0},
    "spd_fast": {"name": "🚀 Fast (1.15x)", "short_name": "Fast (1.15x)", "rate": 1.15}
}

DEFAULT_ASSISTANT_SETTINGS: Dict[str, Any] = {
    "voice_key": "v_riya",
    "model_key": "m_gpt4mini",
    "stt_key": "stt_soniox",
    "language_key": "lang_hindi",
    "speed_key": "spd_normal",
    "interruptible": True,
    "silence_timeout_ms": 200
}

# -------------------------------------------------------------
# KEYBOARD BUILDERS
# -------------------------------------------------------------

def format_settings_card(user_name: str, chat_id: Any, settings: Dict[str, Any]) -> str:
    """Renders visual settings inspection dashboard."""
    vk = settings.get("voice_key", "v_riya")
    mk = settings.get("model_key", "m_gpt4mini")
    sk = settings.get("stt_key", "stt_soniox")
    lk = settings.get("language_key", "lang_hindi")
    spk = settings.get("speed_key", "spd_normal")

    v_info = AVAILABLE_VOICES.get(vk, AVAILABLE_VOICES["v_riya"])
    m_info = AVAILABLE_MODELS.get(mk, AVAILABLE_MODELS["m_gpt4mini"])
    s_info = AVAILABLE_STT.get(sk, AVAILABLE_STT["stt_soniox"])
    l_info = AVAILABLE_LANGUAGES.get(lk, AVAILABLE_LANGUAGES["lang_hindi"])
    sp_info = AVAILABLE_SPEEDS.get(spk, AVAILABLE_SPEEDS["spd_normal"])

    clean_cid = str(chat_id)
    masked_cid = (clean_cid[:3] + "***" + clean_cid[-3:]) if len(clean_cid) >= 7 else clean_cid

    return (
        f"⚙️ *[DARK ANGEL VOICE AI — ASSISTANT SETTINGS]* 🎛️\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• 👤 *Personal Profile:* `{user_name}` (`{masked_cid}`)\n"
        f"• 🗣️ *Active Voice (TTS):* `{v_info['name']}` ({v_info['provider']})\n"
        f"• 🧠 *AI Model (LLM):* `{m_info['short_name']}`\n"
        f"• 🎧 *Transcription (STT):* `{s_info['short_name']}`\n"
        f"• 🌐 *Language:* `{l_info['name']}`\n"
        f"• ⏱️ *Speech Pacing:* `{sp_info['name']}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔒 *100% User Isolation Guarantee:*\n"
        f"_Ye settings sirf aapke outbound calls par apply hongi. Kisi dusre user ke calls par iska koi asar nahi padega._\n\n"
        f"👉 *Neeche diye gaye buttons se configuration personalize karein:*"
    )

def build_settings_main_keyboard(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Builds the main Assistant Settings inline keyboard."""
    vk = settings.get("voice_key", "v_riya")
    mk = settings.get("model_key", "m_gpt4mini")
    sk = settings.get("stt_key", "stt_soniox")
    lk = settings.get("language_key", "lang_hindi")
    spk = settings.get("speed_key", "spd_normal")

    v_short = AVAILABLE_VOICES.get(vk, {}).get("name", "Riya")[:22]
    m_short = AVAILABLE_MODELS.get(mk, {}).get("short_name", "GPT-4o Mini")
    s_short = AVAILABLE_STT.get(sk, {}).get("short_name", "Soniox")
    l_short = AVAILABLE_LANGUAGES.get(lk, {}).get("short_name", "Hindi")
    sp_short = AVAILABLE_SPEEDS.get(spk, {}).get("short_name", "Normal")

    return {
        "inline_keyboard": [
            [{"text": f"🗣️ Voice: {v_short}", "callback_data": "set_menu_voice_p1"}],
            [{"text": f"🧠 AI Model: {m_short}", "callback_data": "set_menu_model"}],
            [{"text": f"🎧 Transcription (STT): {s_short}", "callback_data": "set_menu_stt"}],
            [
                {"text": f"🌐 Lang: {l_short}", "callback_data": "set_menu_lang"},
                {"text": f"⏱️ Speed: {sp_short}", "callback_data": "set_menu_speed"}
            ],
            [
                {"text": "🔄 Reset Defaults", "callback_data": "set_reset_defaults"},
                {"text": "❌ Close Menu", "callback_data": "set_close"}
            ]
        ]
    }

def build_voice_selection_keyboard(page: int = 1, current_voice_key: str = "v_riya") -> Dict[str, Any]:
    """Builds paginated voice selection keypad."""
    p1_keys = ["v_riya", "v_kavita", "v_aarti", "v_anjali", "v_reena", "v_priti", "v_zoya", "v_svaara"]
    p2_keys = ["v_ayush", "v_suraj", "v_punit", "v_amit", "v_aniket", "v_vikas", "v_nakul", "v_aftab", "v_krishna", "v_shivkishor"]
    p3_keys = ["v_sarvam_male", "v_sarvam_female", "v_sweta", "v_aman", "v_riyasharma", "v_eleven_rachel", "v_eleven_adam"]

    buttons = []
    if page == 1:
        target_keys = p1_keys
    elif page == 2:
        target_keys = p2_keys
    else:
        target_keys = p3_keys

    for vk in target_keys:
        info = AVAILABLE_VOICES.get(vk, {})
        is_sel = "🟢 " if vk == current_voice_key else ""
        buttons.append([{"text": f"{is_sel}🎙️ {info.get('name')}", "callback_data": f"set_v_{vk}"}])

    nav_row = []
    if page > 1:
        nav_row.append({"text": f"⬅️ Page {page-1}", "callback_data": f"set_menu_voice_p{page-1}"})
    if page < 3:
        nav_row.append({"text": f"Page {page+1} ➡️", "callback_data": f"set_menu_voice_p{page+1}"})
    if nav_row:
        buttons.append(nav_row)

    buttons.append([{"text": "🔙 Back to Settings", "callback_data": "set_menu_main"}])
    return {"inline_keyboard": buttons}

def build_model_selection_keyboard(current_model_key: str = "m_gpt4mini") -> Dict[str, Any]:
    """Builds AI LLM Model selection keypad."""
    buttons = []
    for mk, info in AVAILABLE_MODELS.items():
        is_sel = "🟢 " if mk == current_model_key else ""
        buttons.append([{"text": f"{is_sel}⚡ {info['name']}", "callback_data": f"set_m_{mk}"}])
    buttons.append([{"text": "🔙 Back to Settings", "callback_data": "set_menu_main"}])
    return {"inline_keyboard": buttons}

def build_stt_selection_keyboard(current_stt_key: str = "stt_soniox") -> Dict[str, Any]:
    """Builds STT Provider selection keypad."""
    buttons = []
    for sk, info in AVAILABLE_STT.items():
        is_sel = "🟢 " if sk == current_stt_key else ""
        buttons.append([{"text": f"{is_sel}🎧 {info['name']}", "callback_data": f"set_stt_{sk}"}])
    buttons.append([{"text": "🔙 Back to Settings", "callback_data": "set_menu_main"}])
    return {"inline_keyboard": buttons}

def build_language_selection_keyboard(current_lang_key: str = "lang_hindi") -> Dict[str, Any]:
    """Builds Language selection keypad."""
    buttons = []
    items = list(AVAILABLE_LANGUAGES.items())
    for i in range(0, len(items), 2):
        row = []
        for lk, info in items[i:i+2]:
            is_sel = "🟢 " if lk == current_lang_key else ""
            row.append({"text": f"{is_sel}{info['name']}", "callback_data": f"set_lang_{lk}"})
        buttons.append(row)
    buttons.append([{"text": "🔙 Back to Settings", "callback_data": "set_menu_main"}])
    return {"inline_keyboard": buttons}

def build_speed_selection_keyboard(current_speed_key: str = "spd_normal") -> Dict[str, Any]:
    """Builds Speech Pacing selection keypad."""
    buttons = []
    for spk, info in AVAILABLE_SPEEDS.items():
        is_sel = "🟢 " if spk == current_speed_key else ""
        buttons.append([{"text": f"{is_sel}{info['name']}", "callback_data": f"set_spd_{spk}"}])
    buttons.append([{"text": "🔙 Back to Settings", "callback_data": "set_menu_main"}])
    return {"inline_keyboard": buttons}
