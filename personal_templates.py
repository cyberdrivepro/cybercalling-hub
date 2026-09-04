"""
================================================================================
  👑 Personal Voice AI Templates & Scenario Task Presets
================================================================================
  Everyday personal calling presets for instant 1-click execution.
================================================================================
"""

PERSONAL_TEMPLATES = {
    "restaurant": {
        "title": "🍕 Restaurant & Table Reservation",
        "description": "Calls a restaurant to book a table for guests.",
        "welcome": "Hello! I am calling to check table availability and book a reservation.",
        "prompt": "You are calling a restaurant on behalf of your user. Politely request a table for 2 to 4 people for dinner. Ask for available time slots, indoor/outdoor seating, and confirm the reservation."
    },
    "delivery": {
        "title": "📦 Courier & Delivery Status Check",
        "description": "Calls delivery boy or courier hub to check package status.",
        "welcome": "Hello! I am calling to check the delivery status of my pending order.",
        "prompt": "You are calling regarding a pending courier package or order delivery. Ask what time the delivery executive will arrive, if any landmark is needed, and request a quick update."
    },
    "enquiry": {
        "title": "🔍 Product Price & Stock Enquiry",
        "description": "Calls a store to check product pricing and availability.",
        "welcome": "Hello! I wanted to inquire about product pricing and stock availability.",
        "prompt": "You are inquiring about product availability, current pricing, discounts, and store closing time. Be polite, concise, and note down all details."
    },
    "appointment": {
        "title": "🏥 Doctor & Clinic Appointment Booking",
        "description": "Calls a clinic/salon/doctor to book a consultation slot.",
        "welcome": "Hello! I am calling to schedule an appointment consultation.",
        "prompt": "You are calling a clinic or service center to schedule an appointment. Ask for available slots today or tomorrow, consultation fees, and lock the preferred slot."
    },
    "reminder": {
        "title": "🔔 Personal Wake-Up & Task Alert Call",
        "description": "AI calls the user's phone to wake them up or deliver a reminder.",
        "welcome": "Good morning! This is your personal Voice AI assistant with your scheduled reminder.",
        "prompt": "You are the user's personal Jarvis assistant. Deliver the scheduled task reminder with high energy and enthusiasm, confirm they received the message, and wish them a productive day."
    }
}


def get_template_by_key(key):
    return PERSONAL_TEMPLATES.get(key.lower(), PERSONAL_TEMPLATES["enquiry"])


def list_all_templates():
    return [
        {"key": k, "title": v["title"], "description": v["description"]}
        for k, v in PERSONAL_TEMPLATES.items()
    ]
