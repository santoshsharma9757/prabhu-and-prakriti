from __future__ import annotations

from random import shuffle


TREND_BANK: dict[str, list[dict[str, object]]] = {
    "mahakal": [
        {
            "topic": "जब सब साथ छोड़ दें, महाकाल पर भरोसा क्यों शक्ति देता है",
            "hook": "जिसके सिर पर महाकाल हों, उसे डर किस बात का?",
            "cta": "जय श्री महाकाल लिखो",
            "queries": ["shiva statue", "temple india", "mountains sunrise spiritual"],
        },
        {
            "topic": "महाकाल की भक्ति में धैर्य क्यों सबसे बड़ी तपस्या है",
            "hook": "हर देर, महाकाल की तैयारी भी हो सकती है",
            "cta": "हर हर महादेव कमेंट करो",
            "queries": ["diya flame", "incense temple", "temple bells"],
        },
        {
            "topic": "क्यों श्मशान के स्वामी शिव ही जीवन के रक्षक हैं",
            "hook": "मृत्यु से भय उन्हें लगता है जो शिव को नहीं जानते",
            "cta": "हर हर महादेव",
            "queries": ["shiva meditation", "ghat aarti", "smoke spiritual"],
        },
    ],
    "hanuman ji": [
        {
            "topic": "हनुमान जी का नाम कठिन समय में मन को अडिग कैसे बनाता है",
            "hook": "जब मन टूटे, बजरंगबली का स्मरण ढाल बन जाता है",
            "cta": "जय बजरंगबली कमेंट करो",
            "queries": ["prayer hands", "temple india", "devotional crowd"],
        },
        {
            "topic": "हनुमान जी से सीखें: असंभव को संभव बनाने का मंत्र",
            "hook": "राम काज कीन्ही बिनु मोहि कहाँ विश्राम",
            "cta": "जय हनुमान लिखो",
            "queries": ["sunrise peak", "strength power", "hanuman statue"],
        },
    ],
    "maa durga": [
        {
            "topic": "मां दुर्गा की शक्ति हमें आत्मसम्मान और साहस क्यों सिखाती है",
            "hook": "कमजोर मत समझो खुद को, तुम्हारे भीतर भी मां की शक्ति है",
            "cta": "जय माता दी लिखो",
            "queries": ["diya flame", "temple bells", "prayer hands"],
        },
        {
            "topic": "मां दुर्गा की उपासना कठिन समय में आंतरिक शक्ति कैसे जगाती है",
            "hook": "जब कोई रास्ता न दिखे, मां शक्ति बनकर खड़ी होती हैं",
            "cta": "जय माता दी कमेंट करो",
            "queries": ["incense temple", "river aarti", "devotional crowd"],
        },
    ],
    "vishnu ji": [
        {
            "topic": "विष्णु जी हमें धैर्य, संतुलन और धर्म पर टिके रहना क्यों सिखाते हैं",
            "hook": "जिसका आधार धर्म है, उसका संतुलन नहीं टूटता",
            "cta": "हरि ओम लिखो",
            "queries": ["meditation india", "river aarti", "mountains sunrise spiritual"],
        }
    ],
    "narasimha": [
        {
            "topic": "नरसिंह भगवान की स्मृति अन्याय के सामने निर्भयता क्यों देती है",
            "hook": "जब सत्य पर संकट आए, संरक्षण भी प्रकट होता है",
            "cta": "नरसिंह भगवान की जय लिखो",
            "queries": ["temple india", "fire spiritual", "prayer hands"],
        }
    ],
    "krishna bhakti": [
        {
            "topic": "कृष्ण भक्ति हमें परिणाम छोड़कर कर्म पर ध्यान देना क्यों सिखाती है",
            "hook": "जब मन उलझे, कृष्ण स्मरण दिशा देता है",
            "cta": "राधे राधे लिखो",
            "queries": ["river aarti", "meditation india", "temple bells"],
        },
        {
            "topic": "सच्चा प्रेम और समर्पण क्या है? राधा-कृष्ण से सीखें",
            "hook": "प्रेम वो नहीं जो बांध ले, प्रेम वो है जो मुक्त कर दे",
            "cta": "जय श्री कृष्णा",
            "queries": ["flute music", "peacock feather", "garden spiritual"],
        },
    ],
    "nature": [
        {
            "topic": "प्रकृति की शांति में ही ईश्वर की आवाज़ सुनाई देती है",
            "hook": "क्या आपने कभी पत्तों की सरसराहट में खुदा को सुना है?",
            "cta": "प्रकृति से प्यार है तो ❤️ दें",
            "queries": ["forest mist", "waterfall slow motion", "nature landscape"],
        },
        {
            "topic": "नदी का बहाव सिखाता है कि जीवन में रुकना नहीं, बहना है",
            "hook": "पत्थर कितने भी हों, नदी अपना रास्ता बना ही लेती है",
            "cta": "I Love Nature लिखो",
            "queries": ["river flow", "mountain stream", "sunset reflection"],
        },
    ],
    "ram bhakti": [
        {
            "topic": "राम भक्ति जीवन में मर्यादा और स्थिरता की शक्ति कैसे देती है",
            "hook": "मर्यादा में ही वह बल है जो जीवन संभालता है",
            "cta": "जय श्री राम लिखो",
            "queries": ["temple india", "sunrise spiritual", "prayer hands"],
        }
    ],
    "shiv bhakti": [
        {
            "topic": "शिव भक्ति हमें अहंकार छोड़कर शांति की ओर क्यों ले जाती है",
            "hook": "जब अहंकार टूटता है, तब भीतर शिव प्रकट होते हैं",
            "cta": "हर हर महादेव लिखो",
            "queries": ["shiva statue", "diya flame", "mountains sunrise spiritual"],
        }
    ],
    "karma and destiny": [
        {
            "topic": "कर्म, समय और विश्वास का संतुलन किस्मत को कैसे बदलता है",
            "hook": "किस्मत बंद नहीं होती, कर्म से खुलती है",
            "cta": "कर्म पर विश्वास हो तो लिखो हरि ओम",
            "queries": ["mountains sunrise spiritual", "meditation india", "river aarti"],
        }
    ],
    "faith during hard times": [
        {
            "topic": "कठिन समय में ईश्वर पर विश्वास टूटने न देना क्यों जरूरी है",
            "hook": "अंधेरा जितना गहरा हो, प्रभु उतने करीब भी हो सकते हैं",
            "cta": "भगवान पर भरोसा है तो लिखो जय श्री राम",
            "queries": ["diya flame", "mountains sunrise spiritual", "prayer hands"],
        }
    ],
    "spiritual discipline": [
        {
            "topic": "आध्यात्मिक अनुशासन मन की बिखरी ऊर्जा को ताकत में कैसे बदलता है",
            "hook": "जो मन को साध ले, वही जीवन को साध लेता है",
            "cta": "अनुशासन चाहिए तो हरि ओम लिखो",
            "queries": ["meditation india", "sunrise spiritual", "mountains sunrise spiritual"],
        }
    ],
    "self-control through bhakti": [
        {
            "topic": "भक्ति हमें प्रतिक्रिया नहीं, संयम चुनना क्यों सिखाती है",
            "hook": "संयम भी भक्ति का ही एक रूप है",
            "cta": "संयम की शक्ति चाहिए तो जय श्री कृष्ण लिखो",
            "queries": ["meditation india", "prayer hands", "temple bells"],
        }
    ],
}


def get_theme_bank() -> dict[str, list[dict[str, object]]]:
    return TREND_BANK


def list_theme_names() -> list[str]:
    return list(TREND_BANK.keys())


def get_seed_topics(limit: int = 20) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for theme, entries in TREND_BANK.items():
        for entry in entries:
            enriched = dict(entry)
            enriched["theme"] = theme
            items.append(enriched)
    shuffle(items)
    return items[:limit]


def search_local_trends(query: str, limit: int = 5) -> list[dict[str, object]]:
    query_l = query.strip().lower()
    matches: list[dict[str, object]] = []
    for theme, entries in TREND_BANK.items():
        haystack = f"{theme} {' '.join(str(e['topic']) for e in entries)}".lower()
        if query_l in haystack:
            for entry in entries:
                enriched = dict(entry)
                enriched["theme"] = theme
                matches.append(enriched)
    return matches[:limit]
