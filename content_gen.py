import os
import anthropic
from datetime import datetime

SYSTEM_PROMPT = """אתה מנהל תוכן מקצועי לחשבון אינסטגרם בנושא באולינג בעברית.
הפוסטים שלך:
- כתובים בעברית תקנית וקולחת
- אנרגטיים, מעוררי עניין ומתחברים לקהל
- כתובים בטקסט רגיל בלבד — ללא כוכביות, ללא hashtag בתוך הטקסט, ללא markdown
- מסתיימים תמיד ב-6 עד 8 האשטאגים רלוונטיים בשורה נפרדת (מיקס עברית ואנגלית)
- לא יותר מ-250 מילים — חובה לסיים את הטקסט לפני ה-hashtags"""

PROMPTS = {
    "tip": """כתוב טיפ מקצועי לשיפור משחק באולינג לפוסט אינסטגרם.
הטיפ צריך להיות ספציפי, מעשי וניתן ליישום מיד.
התחל עם שורה פותחת מושכת ואמוג'י מתאים.""",

    "fact": """כתוב עובדה מפתיעה ומרתקת על ספורט הבאולינג לפוסט אינסטגרם.
העובדה צריכה להיות ייחודית — משהו שרוב האנשים לא יודעים.
התחל בשאלה רטורית קצרה כדי לגרום לעניין.""",

    "motivation": """כתוב פוסט מוטיבציה ועידוד הקשורים לבאולינג לאינסטגרם.
השתמש בקשר בין הספורט לחיים — השאר, התמדה, שיפור עצמי.
התחל עם ציטוט מחזק או משפט כוח קצר.""",

    "question": """כתוב שאלה מעוררת אינטראקציה לפוסט אינסטגרם בנושא באולינג.
השאלה צריכה להיות כיפית, קלה למענה ולגרום לאנשים לתייג חברים.
הוסף הנחיה לתגובה (לדוגמה: "כתבו בתגובות!" או "תייגו מישהו שאתם אוהבים לשחק איתו!").""",
}

SLOT_TYPES = {
    0: "tip",        # בוקר
    1: "fact",       # צהריים
    2: "motivation", # ערב
}


def get_content_type(slot: int) -> str:
    """מחזיר סוג תוכן בהתבסס על slot ויום השנה לגיוון."""
    base_type = SLOT_TYPES.get(slot % 3, "tip")
    types = list(PROMPTS.keys())
    day = datetime.now().timetuple().tm_yday
    # כל 4 ימים מחליף את סוג התוכן של כל slot לגיוון
    index = (types.index(base_type) + day // 4) % len(types)
    return types[index]


def generate_caption(slot: int) -> str:
    content_type = get_content_type(slot)
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": PROMPTS[content_type]}],
    )
    return response.content[0].text
