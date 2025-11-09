# FAQ_DATA.py
"""
FAQ configuration for Tenancy Chatbot
All questions are based on actual clauses in tenancy_agreement.pdf
"""

FAQ_ITEMS = {
    "Rent & Payment": [
        "When is my rent due each month?",
        "What happens if I pay rent late?",
        "How is late payment interest calculated?",
    ],
    
    "Security Deposit": [
        "How much is my security deposit?",
        "When will I get my deposit back?",
        "Can I use the deposit to pay last month's rent?",
    ],
    
    "Repairs & Maintenance": [
        "Who pays for repairs under $200?",
        "Who is responsible for air-conditioning maintenance?",
        "What happens if something breaks due to wear and tear?",
        "Do I need to replace light bulbs myself?",
    ],
    
    "Termination & Early Exit": [
        "What is the diplomatic clause?",
        "Can I terminate the lease early?",
        "Do I need to pay commission if I use the diplomatic clause?",
    ],
    
    "Move-In & Move-Out": [
        "What is the defect-free period?",
        "What do I need to do before returning the unit?",
        "Do I need to repaint walls when moving out?",
        "Who pays for professional cleaning?",
    ],
    
    "Access & Privacy": [
        "Can the landlord enter my unit?",
        "Can the landlord show the unit to potential tenants?",
        "How much notice is required for viewings?",
    ],
    
    "House Rules": [
        "Can I keep pets?",
        "Can I make alterations to the unit?",
        "Can I sublet the property?",
    ],
    
    "Utilities & Bills": [
        "Who pays for electricity and water?",
        "Who pays property tax?",
    ],
    
    "Renewal Options": [
        "Can I renew my tenancy?",
        "How much notice do I need to give for renewal?",
        "Will the diplomatic clause apply to renewal?",
    ]
}

# Benchmark questions for testing (from project requirements)
BENCHMARK_QUESTIONS = [
    "What's the diplomatic clause?",
    "When things are spoiled/broken, who pays to repair?",
    "What to do before returning the unit?",
]