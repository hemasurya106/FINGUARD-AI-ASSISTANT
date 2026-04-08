import graphviz

def generate_architecture_diagram():
    # Create a new directed graph
    dot = graphviz.Digraph('AI_Financial_Assistant_Architecture', comment='Complete System Architecture')
    
    # Global attributes for a premium look
    dot.attr(rankdir='TB', size='12,12', overlap='false', splines='ortho')
    dot.attr('node', shape='box', style='filled, rounded', fontname='Arial', fontsize='12', margin='0.2')
    dot.attr('edge', fontname='Arial', fontsize='10', color='#2c3e50')

    # Define Color Palette
    colors = {
        'ui': '#E1F5FE',       # Light Blue
        'services': '#FFF9C4', # Light Yellow
        'ai_ml': '#F3E5F5',    # Light Purple
        'data': '#E8F5E9',      # Light Green
        'external': '#FAFAFA'  # Off-White
    }

    # 1. User Interface Layer
    with dot.subgraph(name='cluster_ui') as c:
        c.attr(label='User Interface Layer', style='filled', color='#f0f4f8', fontcolor='#2c3e50', fontsize='14')
        c.node('finguard_ui', 'FinGuard Dashboard\n(React.js / Tailwind)', fillcolor=colors['ui'])
        c.node('dealdetective_ui', 'DealDetective UI\n(React.js / Vite)', fillcolor=colors['ui'])
        c.node('voice_interface', 'Voice Interface\n(Mic/Speaker)', fillcolor=colors['ui'], shape='ellipse')

    # 2. Application Services Layer
    with dot.subgraph(name='cluster_services') as c:
        c.attr(label='Application Services Layer', style='filled', color='#fdfcf0', fontcolor='#2c3e50', fontsize='14')
        c.node('finbot_api', 'FinBot Core API\n(FastAPI)', fillcolor=colors['services'])
        c.node('dealdetective_engine', 'DealDetective Engine\n(FastAPI)', fillcolor=colors['services'])
        c.node('voice_server', 'Voice Intelligence Server\n(WebSockets / FastAPI)', fillcolor=colors['services'])

    # 3. AI/ML Intelligence Layer
    with dot.subgraph(name='cluster_ai_ml') as c:
        c.attr(label='AI/ML Intelligence Layer', style='filled', color='#f3f0f5', fontcolor='#2c3e50', fontsize='14')
        c.node('gemini', 'Gemini 2.0 Flash\n(LLM / Reasoning)', fillcolor=colors['ai_ml'])
        c.node('deepgram', 'Deepgram Nova-2\n(STT / TTS)', fillcolor=colors['ai_ml'])
        c.node('dole_model', 'DOLE Predictor\n(Random Forest ML)', fillcolor=colors['ai_ml'])
        c.node('ocr_engine', 'OCR Engine\n(Tesseract/EasyOCR)', fillcolor=colors['ai_ml'])

    # 4. Data Layer
    with dot.subgraph(name='cluster_data') as c:
        c.attr(label='Data Persistence Layer', style='filled', color='#f0f5f1', fontcolor='#2c3e50', fontsize='14')
        c.node('db', 'Core Database\n(PostgreSQL / SQLite)', fillcolor=colors['data'], shape='cylinder')
        c.node('cache', 'Session Cache\n(In-memory)', fillcolor=colors['data'], shape='cylinder')

    # Connections - UI to Services
    dot.edge('finguard_ui', 'finbot_api', label='REST API')
    dot.edge('dealdetective_ui', 'dealdetective_engine', label='REST API')
    dot.edge('voice_interface', 'voice_server', label='WebSocket Binary Stream')

    # Connections - Internal Service Orchestration
    dot.edge('finbot_api', 'dealdetective_engine', label='Cross-Service Calls', style='dashed')
    dot.edge('voice_server', 'finbot_api', label='Trigger Actions')

    # Connections - Services to AI/ML
    dot.edge('finbot_api', 'ocr_engine', label='Process Receipts')
    dot.edge('finbot_api', 'dole_model', label='Risk Inference')
    dot.edge('voice_server', 'deepgram', label='STT/TTS stream')
    dot.edge('voice_server', 'gemini', label='Natural Language Context')
    dot.edge('dealdetective_engine', 'gemini', label='Product Matching / Analysis')

    # Connections - Services to Data
    dot.edge('finbot_api', 'db', label='SQLAlchemy')
    dot.edge('dealdetective_engine', 'db', label='SQLAlchemy')
    dot.edge('voice_server', 'cache', label='State Mgmt')

    # Save DOT source first
    source = dot.source
    with open('system_architecture.dot', 'w') as f:
        f.write(source)
    print("DOT source saved as system_architecture.dot")

    # Attempt to render the diagram
    try:
        dot.render('system_architecture', format='png', cleanup=True)
        print("Architecture diagram generated as system_architecture.png")
    except Exception as e:
        print(f"Notice: Graphics rendering failed (system 'dot' binary not found).")
        print("You can view or render the generated 'system_architecture.dot' file at https://dreampuf.github.io/GraphvizOnline/")
    
    return source

if __name__ == "__main__":
    generate_architecture_diagram()
