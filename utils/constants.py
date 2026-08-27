"""
Central constants repository for ZeroGuard AI application.
Includes shared emergency helpline numbers and metadata.
"""

EMERGENCY_HELPLINES = [
    {
        'number': '1930',
        'title': 'National Cyber Crime Helpline',
        'subtitle': 'Financial Fraud & Golden Hour Freeze',
        'note': '1930 — Call immediately if money was lost, to request a transaction freeze.',
        'description': 'Managed by Ministry of Home Affairs (I4C). Immediately flags fraudulent transactions to the recipient bank and payment gateways to freeze stolen funds within the Golden Hour.',
        'badge': 'CRITICAL FINANCIAL HOTLINE',
        'badge_class': 'badge-critical',
        'color': 'var(--danger)',
        'btn_class': 'btn-danger'
    },
    {
        'number': '112',
        'title': 'National Emergency Number (ERSS)',
        'subtitle': 'Police / Emergency Response',
        'note': '112 — Unified national emergency helpline for immediate police dispatch or urgent threats.',
        'description': 'Unified emergency response support system for immediate local police dispatch, urgent physical threats, extortion containment, and general emergency coordination across all states.',
        'badge': 'ALL-IN-ONE EMERGENCY',
        'badge_class': 'badge-medium',
        'color': 'var(--primary)',
        'btn_class': 'btn-primary'
    },
    {
        'number': '1091',
        'title': 'Women Helpline',
        'subtitle': 'Cyberstalking & Harassment',
        'note': '1091 — Dedicated 24x7 helpline for women facing cyber harassment, sextortion, or doxxing.',
        'description': 'Dedicated assistance for women facing cyber stalking, morphing, non-consensual image sharing (NCII), doxxing, or online defamation.',
        'badge': 'WOMEN SAFETY',
        'badge_class': 'badge-medium',
        'color': 'var(--ai-purple)',
        'btn_class': 'btn-outline'
    },
    {
        'number': '14440',
        'title': 'RBI Financial Fraud Helpline',
        'subtitle': 'Banking Ombudsman & Disputes',
        'note': '14440 — Reserve Bank of India helpline for escalating unresolved banking debits & payment disputes.',
        'description': 'Reserve Bank of India helpline for escalating unresolved banking disputes, unauthorized debit reversals under the Zero Liability circular, and digital payment issues.',
        'badge': 'BANKING OMBUDSMAN',
        'badge_class': 'badge-success',
        'color': 'var(--accent-green)',
        'btn_class': 'btn-outline'
    }
]
