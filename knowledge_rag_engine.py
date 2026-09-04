"""
================================================================================
  📚 OmniDimension AI Knowledge Base & RAG FAQ Brain Engine
================================================================================
  Allows injecting dynamic company knowledge, product catalogs, FAQ documents,
  and objection-handling matrices directly into Voice AI Assistants.
================================================================================
"""

import os
import json

KNOWLEDGE_STORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".knowledge_bases.json")


def load_knowledge_bases():
    if os.path.exists(KNOWLEDGE_STORE_FILE):
        try:
            with open(KNOWLEDGE_STORE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Default initial presets
    return {
        "sales_closer": {
            "title": "🎯 High-Converting Sales Closer",
            "business_type": "Sales & Direct Conversion",
            "faq_list": [
                {"q": "How much does it cost?", "a": "Our standard plan starts at $49/month with unlimited calls and real-time AI analytics."},
                {"q": "Can I get a discount?", "a": "If you confirm your spot today, I can apply a special 20% executive discount immediately."},
                {"q": "Is there a contract?", "a": "No, it is completely pay-as-you-go with zero lock-in contracts."}
            ],
            "objections": {
                "too_expensive": "Offer a 20% discount or 14-day risk-free trial.",
                "not_interested": "Ask if they would prefer a 2-minute WhatsApp video demo instead.",
                "send_info": "Confirm their WhatsApp number and state that a PDF brochure is being dispatched immediately."
            },
            "guardrails": "Never guarantee specific financial returns. Always be polite, assertive, and helpful."
        },
        "clinic_receptionist": {
            "title": "🏥 Dental & Clinic Appointment Assistant",
            "business_type": "Healthcare & Appointments",
            "faq_list": [
                {"q": "What are your clinic timings?", "a": "We are open Monday to Saturday from 9:00 AM to 8:00 PM."},
                {"q": "Where is the clinic located?", "a": "We are located at Ground Floor, Central Plaza, Main Market."},
                {"q": "Do you accept insurance?", "a": "Yes, we accept all major cashless health cards and insurance policies."}
            ],
            "objections": {
                "busy_timing": "Offer the earliest Saturday morning slot or evening 7:00 PM slot.",
                "doctor_fee": "Mention that the initial consultation is only $15 and includes a free digital X-ray."
            },
            "guardrails": "Do not prescribe medication over the phone. Advise in-person diagnosis."
        }
    }


def save_knowledge_bases(data):
    try:
        with open(KNOWLEDGE_STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("Knowledge store save error:", e)


def build_system_prompt_from_knowledge(kb_key, agent_name="Dark Angel Voice AI", custom_task=""):
    """
    Compile a high-converting system prompt containing FAQ context,
    objection handling, and strict behavioral guardrails.
    """
    kbs = load_knowledge_bases()
    kb = kbs.get(kb_key, kbs.get("sales_closer"))

    prompt = (
        f"You are {agent_name}, a world-class professional voice AI representative for {kb.get('title')}.\n\n"
        f"🎯 PRIMARY TASK: {custom_task or 'Assist the caller warmly, deliver the primary message clearly, and answer questions.'}\n\n"
        "📖 KNOWLEDGE BASE & FREQUENTLY ASKED QUESTIONS:\n"
    )

    for item in kb.get("faq_list", []):
        prompt += f"• Q: {item['q']}\n  A: {item['a']}\n"

    prompt += "\n🛡️ OBJECTION HANDLING GUIDELINES:\n"
    for obj, resp in kb.get("objections", {}).items():
        prompt += f"• If customer says '{obj.replace('_', ' ')}': {resp}\n"

    prompt += f"\n⛔ CRITICAL GUARDRAILS:\n{kb.get('guardrails', 'Be polite and professional.')}\n"
    prompt += "Keep all spoken answers concise (1-2 sentences), natural, and engaging."

    return prompt
