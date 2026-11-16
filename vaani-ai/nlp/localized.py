"""Offline localised replies so VaaniAI can answer in Hindi, Marathi, Gujarati, Spanish, French, German
even without internet. Placeholders: {time} {date} {person}."""

LOCAL = {
    "greeting": {
        "hi": "नमस्ते! मैं वाणी एआई हूँ। आप किसी भी भाषा में बोलिए या लिखिए।",
        "mr": "नमस्कार! मी वाणी एआय आहे. तुम्ही कोणत्याही भाषेत बोला किंवा लिहा.",
        "gu": "નમસ્તે! હું વાણી એઆઈ છું. તમે કોઈપણ ભાષામાં બોલો અથવા લખો.",
        "es": "¡Hola! Soy VaaniAI. Habla o escribe en cualquier idioma.",
        "fr": "Bonjour ! Je suis VaaniAI. Parlez ou écrivez dans n'importe quelle langue.",
        "de": "Hallo! Ich bin VaaniAI. Sprich oder schreibe in jeder Sprache."},
    "goodbye": {
        "hi": "अलविदा! आपका दिन शुभ हो।", "mr": "निरोप! तुमचा दिवस छान जावो.", "gu": "આવજો! તમારો દિવસ સરસ રહે.",
        "es": "¡Adiós! Que tengas un buen día.", "fr": "Au revoir ! Passez une excellente journée.",
        "de": "Auf Wiedersehen! Einen schönen Tag noch."},
    "thanks": {
        "hi": "आपका स्वागत है! मदद करके खुशी हुई।", "mr": "तुमचे स्वागत आहे! मदत करून आनंद झाला.",
        "gu": "તમારું સ્વાગત છે! મદદ કરીને આનંદ થયો.",
        "es": "¡De nada! Encantado de ayudar.", "fr": "De rien ! Ravi de vous aider.", "de": "Gern geschehen!"},
    "ask_time": {
        "hi": "अभी समय {time} है।", "mr": "सध्याची वेळ {time} आहे.", "gu": "અત્યારનો સમય {time} છે.",
        "es": "La hora actual es {time}.", "fr": "Il est {time}.", "de": "Es ist {time} Uhr."},
    "ask_date": {
        "hi": "आज की तारीख {date} है।", "mr": "आजची तारीख {date} आहे.", "gu": "આજની તારીખ {date} છે.",
        "es": "Hoy es {date}.", "fr": "Aujourd'hui, nous sommes le {date}.", "de": "Heute ist der {date}."},
    "ask_name": {
        "hi": "मैं वाणी एआई हूँ, एनएलपी से बना एक बहुभाषी वॉइस असिस्टेंट।",
        "mr": "मी वाणी एआय आहे, एनएलपी वापरून बनवलेला बहुभाषिक व्हॉइस असिस्टंट.",
        "gu": "હું વાણી એઆઈ છું, એનએલપીથી બનેલો બહુભાષી વૉઇસ આસિસ્ટન્ટ.",
        "es": "Soy VaaniAI, un asistente de voz multilingüe.", "fr": "Je suis VaaniAI, un assistant vocal multilingue.",
        "de": "Ich bin VaaniAI, ein mehrsprachiger Sprachassistent."},
    "user_intro": {
        "hi": "आपसे मिलकर खुशी हुई, {person}!", "mr": "तुम्हाला भेटून आनंद झाला, {person}!",
        "gu": "તમને મળીને આનંદ થયો, {person}!", "es": "¡Encantado de conocerte, {person}!",
        "fr": "Enchanté, {person} !", "de": "Freut mich, dich kennenzulernen, {person}!"},
    "user_intro_noname": {
        "hi": "आपसे मिलकर खुशी हुई!", "mr": "तुम्हाला भेटून आनंद झाला!", "gu": "તમને મળીને આનંદ થયો!",
        "es": "¡Encantado de conocerte!", "fr": "Enchanté !", "de": "Freut mich, dich kennenzulernen!"},
    "capabilities": {
        "hi": "मैं आपकी आवाज़ को टेक्स्ट में बदल सकता हूँ, भाषा पहचान, अनुवाद, भावना विश्लेषण और बातचीत कर सकता हूँ।",
        "mr": "मी तुमचा आवाज मजकुरात बदलू शकतो, भाषा ओळखू शकतो, भाषांतर, भावना विश्लेषण आणि गप्पा करू शकतो.",
        "gu": "હું તમારા અવાજને ટેક્સ્ટમાં ફેરવી શકું છું, ભાષા ઓળખી શકું છું, અનુવાદ, લાગણી વિશ્લેષણ અને વાતચીત કરી શકું છું.",
        "es": "Puedo transcribir voz, detectar idioma, traducir, analizar sentimientos y conversar.",
        "fr": "Je peux transcrire la voix, détecter la langue, traduire, analyser les sentiments et discuter.",
        "de": "Ich kann Sprache transkribieren, Sprachen erkennen, übersetzen, Stimmung analysieren und chatten."},
    "sad": {
        "hi": "मुझे खेद है कि आप ऐसा महसूस कर रहे हैं। मैं सुनने के लिए यहाँ हूँ।",
        "mr": "तुम्हाला असे वाटत आहे याचे मला वाईट वाटते. मी ऐकायला इथे आहे.",
        "gu": "તમને આવું લાગે છે તેનું મને દુઃખ છે. હું સાંભળવા માટે અહીં છું.",
        "es": "Lamento que te sientas así. Estoy aquí para escucharte.",
        "fr": "Je suis désolé que vous vous sentiez ainsi. Je suis là pour vous écouter.",
        "de": "Es tut mir leid, dass du dich so fühlst. Ich höre dir zu."},
    "happy": {
        "hi": "यह सुनकर बहुत अच्छा लगा! मुस्कुराते रहिए।", "mr": "हे ऐकून खूप छान वाटले! हसत राहा.",
        "gu": "આ સાંભળીને ખૂબ આનંદ થયો! હસતા રહો.", "es": "¡Qué bueno oír eso! Sigue sonriendo.",
        "fr": "Ravi de l'entendre ! Continuez à sourire.", "de": "Das freut mich zu hören! Lächle weiter."},
    "compliment": {
        "hi": "धन्यवाद, आप बहुत दयालु हैं!", "mr": "धन्यवाद, तुम्ही खूप दयाळू आहात!", "gu": "આભાર, તમે ખૂબ દયાળુ છો!",
        "es": "¡Gracias, eres muy amable!", "fr": "Merci, c'est très gentil !", "de": "Danke, das ist sehr nett!"},
    "weather": {
        "hi": "इस ऑफ़लाइन संस्करण में मैं लाइव मौसम नहीं बता सकता, पर मौसम एपीआई आसानी से जोड़ी जा सकती है।",
        "mr": "या ऑफलाइन आवृत्तीत मी थेट हवामान सांगू शकत नाही, पण हवामान एपीआय सहज जोडता येईल.",
        "gu": "આ ઓફલાઇન આવૃત્તિમાં હું લાઇવ હવામાન જણાવી શકતો નથી, પણ હવામાન એપીઆઈ સરળતાથી જોડી શકાય."},
    "about_project": {
        "hi": "वाणी एआई एक एनएलपी प्रोजेक्ट है: स्पीच-टू-टेक्स्ट, भाषा पहचान, अनुवाद, भावना विश्लेषण और इंटेंट-आधारित चैटबॉट।",
        "mr": "वाणी एआय हा एनएलपी प्रकल्प आहे: स्पीच-टू-टेक्स्ट, भाषा ओळख, भाषांतर, भावना विश्लेषण आणि इंटेंट-आधारित चॅटबॉट.",
        "gu": "વાણી એઆઈ એક એનએલપી પ્રોજેક્ટ છે: સ્પીચ-ટુ-ટેક્સ્ટ, ભાષા ઓળખ, અનુવાદ, લાગણી વિશ્લેષણ અને ઇન્ટેન્ટ આધારિત ચેટબોટ."},
    "fallback": {
        "hi": "माफ़ कीजिए, मैं समझ नहीं पाया। आप समय, जोक या अनुवाद के बारे में पूछ सकते हैं।",
        "mr": "माफ करा, मला समजले नाही. तुम्ही मला वेळ, विनोद किंवा भाषांतर विचारू शकता.",
        "gu": "માફ કરશો, મને સમજાયું નહીં. તમે મને સમય, જોક કે અનુવાદ વિશે પૂછી શકો છો.",
        "es": "Lo siento, no entendí. Pregúntame la hora, un chiste o una traducción.",
        "fr": "Désolé, je n'ai pas compris. Demandez-moi l'heure, une blague ou une traduction.",
        "de": "Entschuldigung, das habe ich nicht verstanden. Frag mich nach Uhrzeit, Witz oder Übersetzung."},
}
