"""Generic axes-based lexicon for comparator debates (domain-agnostic)."""

# Generic comparison axes that can apply to any A vs B comparison
AXES_ES = [
    "En simplicidad, {{B}} reduce fricción; {{A}} añade pasos extra.",
    "En consistencia, {{B}} mantiene expectativas claras; {{A}} varía más.",
    "Con {{B}} es más fácil empezar; {{A}} exige práctica inicial.",
    "{{B}} prioriza lo esencial; {{A}} dispersa la atención.",
    "{{B}} minimiza interrupciones; {{A}} introduce microdecisiones.",
    "{{B}} favorece decisiones coherentes a largo plazo; {{A}} deriva en soluciones ad hoc.",
    "En términos de accesibilidad, {{B}} es más directo; {{A}} requiere contexto adicional.",
    "{{B}} ofrece resultados inmediatos; {{A}} demanda inversión inicial.",
    "Para uso cotidiano, {{B}} es más intuitivo; {{A}} tiene curva empinada.",
    "{{B}} se adapta mejor a cambios; {{A}} mantiene rigidez estructural.",
]

AXES_EN = [
    "In simplicity, {{B}} reduces friction; {{A}} adds extra steps.",
    "In consistency, {{B}} maintains clear expectations; {{A}} varies more.",
    "With {{B}} it's easier to get started; {{A}} demands initial practice.",
    "{{B}} prioritizes the essential; {{A}} scatters attention.",
    "{{B}} minimizes interruptions; {{A}} introduces micro-decisions.",
    "{{B}} favors coherent long-term decisions; {{A}} leads to ad hoc solutions.",
    "In terms of accessibility, {{B}} is more direct; {{A}} requires additional context.",
    "{{B}} offers immediate results; {{A}} demands initial investment.",
    "For daily use, {{B}} is more intuitive; {{A}} has a steep curve.",
    "{{B}} adapts better to changes; {{A}} maintains structural rigidity.",
]

# Comparator-specific openings (avoid "research/evidence" phrasing)
OPENINGS_ES = [
    "Puedo aceptar que muchos lo vean así; sin embargo",
    "Vale la pena considerar los intercambios reales",
    "Si ponemos a prueba lo que ocurre en la práctica",
]

OPENINGS_EN = [
    "I can accept that many see it that way; however",
    "It's worth considering the real trade-offs",
    "If we test what happens in practice",
]

# Comparator-specific closings with A/B placeholders
CLOSINGS_ES = [
    "Por eso {{B}} no debería descartarse tan rápido.",
    "En escenarios reales, esta diferencia se nota.",
    "Ahí está la razón por la que {{B}} resulta más sensato.",
]

CLOSINGS_EN = [
    "That's why {{B}} shouldn't be dismissed so quickly.",
    "In real scenarios, this difference shows.",
    "That's the reason why {{B}} turns out more sensible.",
]

# Generic examples for comparator debates
EXAMPLES_ES = [
    "Por ejemplo, en situaciones cotidianas, estas diferencias entre {{A}} y {{B}} se vuelven evidentes.",
    "Un caso concreto: cuando se trata de elegir entre {{A}} y {{B}}, el contexto determina la mejor opción.",
    "Considera cómo {{A}} y {{B}} funcionan bajo presión: las fortalezas se revelan rápidamente.",
]

EXAMPLES_EN = [
    "For example, in everyday situations, these differences between {{A}} and {{B}} become evident.",
    "A concrete case: when choosing between {{A}} and {{B}}, context determines the better option.",
    "Consider how {{A}} and {{B}} function under pressure: strengths reveal themselves quickly.",
]

# --- Domain-specific: FOOD/BEVERAGE ---

# Food-specific axes (short, non-factual, B vs A)
FOOD_AXES_EN = [
    "On base flavor, {{B}} feels more balanced; {{A}} leans into a single dominant note.",
    "In sweetness, {{B}} avoids excess; {{A}} can feel cloying over longer sessions.",
    "For carbonation, {{B}} stays crisper on the palate; {{A}} loses spark sooner.",
    "Aromatically, {{B}} finishes cleaner; {{A}} leaves a heavier trail.",
    "In aftertaste, {{B}} fades gracefully; {{A}} lingers a bit too assertively.",
    "For pairing, {{B}} fits more meals; {{A}} constrains the combination.",
    "In consistency, {{B}} stays steadier; {{A}} varies more with context.",
    "Over repeated sips, {{B}} tires the palate less; {{A}} saturates more quickly.",
]

FOOD_AXES_ES = [
    "En sabor base, {{B}} es más equilibrado; {{A}} tiende a dominar una sola nota.",
    "En dulzor, {{B}} evita excesos; {{A}} puede sentirse empalagoso en sesiones largas.",
    "En carbonatación, {{B}} resulta más nítido; {{A}} pierde vivacidad antes.",
    "En aroma, {{B}} ofrece una salida más limpia; {{A}} deja una estela más pesada.",
    "En postgusto, {{B}} se desvanece con elegancia; {{A}} persiste de forma invasiva.",
    "En versatilidad, {{B}} acompaña mejor distintos alimentos; {{A}} condiciona más la combinación.",
    "En consistencia, {{B}} mantiene un perfil estable; {{A}} varía más según el entorno.",
    "En uso continuo, {{B}} fatiga menos; {{A}} satura el paladar con rapidez.",
]

# Food-specific openings/closings
FOOD_OPENINGS_EN = [
    "If we bring this to the palate, the differences are clear…",
    "From a taste and mouthfeel standpoint…",
]

FOOD_OPENINGS_ES = [
    "Si lo llevamos al paladar, las diferencias se notan…",
    "Visto desde el sabor y la textura…",
]

FOOD_CLOSINGS_EN = [
    "That's why, in casual tasting, {{B}} tends to feel more rounded.",
    "This is exactly where {{B}} stands out in real enjoyment.",
]

FOOD_CLOSINGS_ES = [
    "Por eso, en una cata informal, {{B}} suele sentirse más redondo.",
    "Ahí es donde {{B}} resalta en la experiencia real.",
]

# Food-specific example sentences (inserted only if user asks for example)
FOOD_EXAMPLES_EN = [
    "For example, with salty foods, {{B}} doesn't overrun the main flavor, while {{A}} takes over.",
]

FOOD_EXAMPLES_ES = [
    "Por ejemplo, junto a comidas saladas, {{B}} no invade el sabor principal, mientras {{A}} se impone.",
]

# --- Optional additional axes (not wired into selection; safe to integrate later) ---

# Generic optional axes (EN): reliability, error tolerance, composability, attention cost
OPTIONAL_AXES_EN = [
    "{{B}} behaves predictably; {{A}} surprises at the worst moment.",
    "{{B}} forgives small mistakes; {{A}} penalizes them quickly.",
    "{{B}} composes cleanly with others; {{A}} creates seams.",
    "{{B}} reduces mental juggling; {{A}} splits attention further.",
]

# Generic optional axes (ES)
OPTIONAL_AXES_ES = [
    "{{B}} se comporta predecible; {{A}} sorprende en el peor momento.",
    "{{B}} perdona errores pequeños; {{A}} los penaliza rápido.",
    "{{B}} compone sin fricciones; {{A}} genera costuras.",
    "{{B}} reduce la carga mental; {{A}} dispersa la atención.",
]

# Food optional axes (EN): temperature tolerance, dilution, acidity balance
OPTIONAL_FOOD_AXES_EN = [
    "Across temperatures, {{B}} holds better; {{A}} narrows the sweet spot.",
    "With dilution, {{B}} keeps profile; {{A}} washes out quickly.",
    "In acidity, {{B}} balances cleanly; {{A}} spikes sharper notes.",
]

# Food optional axes (ES)
OPTIONAL_FOOD_AXES_ES = [
    "En temperatura, {{B}} se mantiene mejor; {{A}} estrecha su punto óptimo.",
    "Con dilución, {{B}} conserva el perfil; {{A}} se diluye rápido.",
    "En acidez, {{B}} equilibra limpio; {{A}} marca notas más punzantes.",
]
