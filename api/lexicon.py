"""Content lexicon for multilingual debate responses."""
from typing import Any

# Content banks per language for deterministic variety
CONTENT_BANKS: dict[str, dict[str, Any]] = {
    "en": {
        "anchors": {
            "supporting": [
                "I firmly believe that {topic} is fundamentally beneficial and necessary.",
                "I maintain that {topic} represents a crucial advancement for society.",
                "In my view, {topic} offers indispensable benefits that we cannot ignore."
            ],
            "opposing": [
                "I maintain that {topic} presents significant concerns that cannot be ignored.",
                "I believe {topic} raises serious issues that require careful consideration.",
                "In my assessment, {topic} poses challenges that outweigh potential benefits."
            ]
        },
        "arguments": [
            "First, consider that {argument}. This is crucial because {reasoning}.",
            "Moreover, {argument}. The evidence clearly shows {reasoning}.",
            "Additionally, {argument}. We cannot ignore that {reasoning}.",
            "Furthermore, {argument}. It's evident that {reasoning}.",
            "Most importantly, {argument}. This demonstrates {reasoning}.",
            "It's important to note that {argument}. Research indicates {reasoning}."
        ],
        "analogies": [
            "Think of it like {analogy} - both share the fundamental principle of {principle}.",
            "Consider the analogy of {analogy}: just as in that case, {principle} applies here.",
            "It's similar to {analogy} in that both involve {principle}.",
            "Like {analogy}, this situation demonstrates {principle}."
        ],
        "questions": [
            "But ask yourself: {question}?",
            "Don't you think {question}?",
            "Isn't it true that {question}?"
        ],
        "topic_switch": "Let's stay focused on {topic_fixed}; we can open a new thread for {topic_new}."
    },
    "es": {
        "anchors": {
            "supporting": [
                "Creo firmemente que {topic} es fundamentalmente beneficioso y necesario.",
                "Sostengo que {topic} representa un avance crucial para la sociedad.",
                "En mi opinión, {topic} ofrece beneficios indispensables que no podemos ignorar."
            ],
            "opposing": [
                "Mantengo que {topic} presenta preocupaciones significativas que no se pueden ignorar.",
                "Creo que {topic} plantea problemas serios que requieren consideración cuidadosa.",
                "En mi evaluación, {topic} plantea desafíos que superan los beneficios potenciales."
            ]
        },
        "arguments": [
            "Primero, consideremos que {argument}. Esto es crucial porque {reasoning}.",
            "Además, {argument}. La evidencia muestra claramente que {reasoning}.",
            "Adicionalmente, {argument}. No podemos ignorar que {reasoning}.",
            "Por otra parte, {argument}. Es evidente que {reasoning}.",
            "Más importante aún, {argument}. Esto demuestra que {reasoning}.",
            "Es importante señalar que {argument}. La investigación indica que {reasoning}."
        ],
        "analogies": [
            "Piénsalo como {analogy}: ambos comparten el principio fundamental de {principle}.",
            "Considera la analogía de {analogy}: tal como en ese caso, {principle} se aplica aquí.",
            "Es similar a {analogy} en que ambos involucran {principle}.",
            "Como {analogy}, esta situación demuestra {principle}."
        ],
        "questions": [
            "¿Pero acaso no crees que {question}?",
            "¿No te parece que {question}?",
            "¿No es cierto que {question}?"
        ],
        "topic_switch": "Sigamos centrados en {topic_fixed}; si quieres, abrimos otro hilo para {topic_new}."
    }
}

# Reasoning and closing phrase banks per language for variety
REASONING_PHRASES: dict[str, list[str]] = {
    "en": [
        "the evidence strongly supports this approach",
        "research confirms this perspective",
        "data indicates this viewpoint",
        "studies demonstrate this position",
        "analysis validates this stance",
        "evidence substantiates this view"
    ],
    "es": [
        "la evidencia respalda claramente este enfoque",
        "la investigación confirma esta perspectiva",
        "los datos indican este punto de vista",
        "los estudios demuestran esta posición",
        "el análisis valida esta postura",
        "la evidencia sustenta esta visión"
    ]
}

CLOSING_PHRASES: dict[str, list[str]] = {
    "en": [
        "This approach offers the most sustainable long-term solution.",
        "These considerations should guide our decision-making process.",
        "The evidence clearly supports this perspective.",
        "This framework provides the most viable path forward.",
        "These principles ensure the most effective outcomes.",
        "This strategy delivers the most balanced results."
    ],
    "es": [
        "Este enfoque ofrece la solución más sostenible a largo plazo.",
        "Estas consideraciones deben guiar nuestro proceso de toma de decisiones.",
        "La evidencia respalda claramente esta perspectiva.",
        "Este marco proporciona el camino más viable hacia adelante.",
        "Estos principios aseguran los resultados más efectivos.",
        "Esta estrategia ofrece los resultados más equilibrados."
    ]
}

# Topic arguments per language with keywords, arguments, analogies, principles, and questions
TOPIC_DATA: dict[str, dict[str, dict[str, list[str]]]] = {
    "en": {
        'climate': {
            'keywords': ['climate', 'global warming', 'carbon', 'emissions', 'environment', 'renewable'],
            'arguments': ['renewable energy adoption', 'carbon footprint reduction', 'sustainable practices'],
            'analogies': ['maintaining a healthy diet', 'caring for a garden', 'preserving a family legacy'],
            'principles': ['environmental stewardship', 'sustainable living', 'long-term thinking'],
            'questions': ['we can afford to ignore environmental consequences', 'future generations matter', 'planet health is important']
        },
        'technology': {
            'keywords': ['technology', 'ai', 'artificial intelligence', 'digital', 'internet', 'robots'],
            'arguments': ['innovation advancement', 'efficiency improvements', 'accessibility benefits'],
            'analogies': ['learning to drive', 'using new tools', 'adopting better methods'],
            'principles': ['continuous improvement', 'adaptation to change', 'embracing progress'],
            'questions': ['progress should be halted due to minor concerns', 'innovation benefits society', 'efficiency matters']
        },
        'education': {
            'keywords': ['education', 'school', 'learning', 'student', 'teacher', 'knowledge'],
            'arguments': ['knowledge accessibility', 'skill development', 'future preparation'],
            'analogies': ['building a foundation', 'planting seeds', 'shaping minds'],
            'principles': ['lifelong learning', 'knowledge sharing', 'intellectual growth'],
            'questions': ['knowledge should be restricted rather than shared', 'education improves lives', 'learning is valuable']
        },
        'general': {
            'keywords': [],
            'arguments': ['practical benefits', 'long-term implications', 'societal impact'],
            'analogies': ['tending a garden', 'building a house', 'running a marathon'],
            'principles': ['careful planning', 'consistent effort', 'balanced approach'],
            'questions': ['we should avoid necessary improvements', 'progress is important', 'change is beneficial']
        }
    },
    "es": {
        'climate': {
            'keywords': ['clima', 'calentamiento global', 'carbono', 'emisiones', 'ambiente', 'renovable'],
            'arguments': ['adopción de energía renovable', 'reducción de huella de carbono', 'prácticas sostenibles'],
            'analogies': ['mantener una dieta saludable', 'cuidar un jardín', 'preservar un legado familiar'],
            'principles': ['cuidado ambiental', 'vida sostenible', 'pensamiento a largo plazo'],
            'questions': ['podemos ignorar las consecuencias ambientales', 'las futuras generaciones importan', 'la salud del planeta es importante']
        },
        'technology': {
            'keywords': ['tecnología', 'inteligencia artificial', 'digital', 'internet', 'robots', 'máquinas'],
            'arguments': ['avance en innovación', 'mejoras en eficiencia', 'beneficios de accesibilidad'],
            'analogies': ['aprender a conducir', 'usar nuevas herramientas', 'adoptar mejores métodos'],
            'principles': ['mejora continua', 'adaptación al cambio', 'adopción del progreso'],
            'questions': ['el progreso debe detenerse por preocupaciones menores', 'la innovación beneficia a la sociedad', 'la eficiencia importa']
        },
        'education': {
            'keywords': ['educación', 'escuela', 'aprendizaje', 'estudiante', 'maestro', 'conocimiento'],
            'arguments': ['accesibilidad al conocimiento', 'desarrollo de habilidades', 'preparación para el futuro'],
            'analogies': ['construir una base', 'plantar semillas', 'moldear mentes'],
            'principles': ['aprendizaje de por vida', 'compartir conocimiento', 'crecimiento intelectual'],
            'questions': ['el conocimiento debe restringirse en lugar de compartirse', 'la educación mejora vidas', 'el aprendizaje es valioso']
        },
        'general': {
            'keywords': [],
            'arguments': ['beneficios prácticos', 'implicaciones a largo plazo', 'impacto social'],
            'analogies': ['cuidar un jardín', 'construir una casa', 'correr un maratón'],
            'principles': ['planificación cuidadosa', 'esfuerzo consistente', 'enfoque equilibrado'],
            'questions': ['debemos evitar mejoras necesarias', 'el progreso es importante', 'el cambio es beneficioso']
        }
    }
}

# Language-specific stance detection markers
LANGUAGE_MARKERS: dict[str, dict[str, list[str]]] = {
    "es": {
        "specific_words": [
            'que', 'la', 'el', 'de', 'y', 'con', 'se', 'te', 'le', 'su', 'por', 'son', 'como', 'para',
            'del', 'una', 'vez', 'más', 'muy', 'pero', 'todo', 'bien', 'sí', 'también', 'ya', 'otro',
            'hasta', 'hacer', 'qué', 'cómo', 'cuándo', 'dónde', 'creo', 'pienso', 'hola', 'gracias'
        ],
        "patterns": ['inteligencia artificial', 'tecnología', 'cambio climático', 'educación'],
        "negation_markers": ['no', 'nunca', 'jamás', 'sin', 'nada', 'ningún', 'ninguna'],
        "contra_indicators": [
            'malo', 'terrible', 'peligroso', 'dañino', 'problemático', 'preocupante',
            'contra', 'opuesto', 'rechazar', 'evitar', 'prohibir', 'limitar'
        ],
        "pro_indicators": [
            'bueno', 'excelente', 'beneficioso', 'positivo', 'apoyo', 'mejor',
            'importante', 'necesario', 'útil', 'valioso', 'esencial', 'genial', 'fantástico',
            'increíble', 'maravilloso', 'revolucionario', 'transformar', 'mejorar'
        ]
    },
    "en": {
        "specific_words": [
            'the', 'and', 'that', 'this', 'with', 'for', 'you', 'are', 'from', 'they', 'have', 'had',
            'will', 'can', 'would', 'should', 'about', 'think', 'believe', 'hello', 'thanks', 'good'
        ],
        "patterns": ['artificial intelligence', 'technology', 'climate change', 'education'],
        "negation_markers": ['not', 'never', 'no', 'without', 'nothing', 'none'],
        "contra_indicators": [
            'bad', 'terrible', 'dangerous', 'harmful', 'problematic', 'concerning',
            'against', 'oppose', 'reject', 'avoid', 'ban', 'limit', 'restrict', 'threat',
            'risk', 'worry', 'fear', 'concern', 'issue', 'problem'
        ],
        "pro_indicators": [
            'good', 'great', 'beneficial', 'positive', 'support', 'better',
            'important', 'necessary', 'useful', 'valuable', 'essential', 'amazing', 'fantastic',
            'incredible', 'wonderful', 'revolutionary', 'revolutionize', 'transform', 'improve'
        ]
    }
}
