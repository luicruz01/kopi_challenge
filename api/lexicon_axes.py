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
