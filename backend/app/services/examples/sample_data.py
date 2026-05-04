"""Sample data for new users."""
from typing import List, Dict, Any

# Pre-built Knowledge Base Templates
KNOWLEDGE_BASE_TEMPLATES = [
    {
        "name": "AI & Machine Learning Basics",
        "description": "Introduction to artificial intelligence and machine learning concepts, including neural networks, deep learning, and common algorithms.",
        "tags": ["AI", "Machine Learning", "Tutorial"],
        "documents": [
            {
                "title": "Introduction to Machine Learning",
                "content": """# Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.

## What is Machine Learning?

Machine learning focuses on developing algorithms that can access data and use it to learn patterns and make decisions with minimal human intervention.

### Types of Machine Learning

1. **Supervised Learning**: Learning from labeled examples
   - Classification: Categorizing data into classes
   - Regression: Predicting continuous values

2. **Unsupervised Learning**: Finding patterns in unlabeled data
   - Clustering: Grouping similar data points
   - Dimensionality Reduction: Simplifying features

3. **Reinforcement Learning**: Learning through trial and error
   - Agent takes actions in an environment
   - Receives rewards or penalties

## Key Concepts

- **Features**: Input variables used for prediction
- **Labels**: Output variables to predict
- **Training**: Process of learning from data
- **Testing**: Evaluating model performance
- **Overfitting**: Model memorizes training data
- **Underfitting**: Model too simple to learn patterns"""
            },
            {
                "title": "Neural Networks Explained",
                "content": """# Neural Networks Explained

Neural networks are computing systems inspired by biological neural networks in animal brains.

## Structure of Neural Networks

### Neurons (Nodes)
- Receive input signals
- Process and transform signals
- Pass output to next layer

### Layers
- **Input Layer**: Receives initial data
- **Hidden Layers**: Process and transform data
- **Output Layer**: Produces final predictions

## Activation Functions

Common activation functions include:
- ReLU (Rectified Linear Unit)
- Sigmoid
- Tanh
- Softmax

## Backpropagation

The learning algorithm that adjusts weights:
1. Calculate prediction error
2. Propagate error backward
3. Update weights to reduce error"""
            },
            {
                "title": "Deep Learning Fundamentals",
                "content": """# Deep Learning Fundamentals

Deep learning is a subset of machine learning with neural networks that have multiple layers.

## Why Deep Learning?

- Automatic feature extraction
- Handle unstructured data
- Scale with data and computation
- State-of-the-art performance

## Common Architectures

### Convolutional Neural Networks (CNN)
- Image recognition
- Object detection
- Computer vision tasks

### Recurrent Neural Networks (RNN)
- Sequential data
- Natural language processing
- Time series analysis

### Transformers
- Attention mechanisms
- BERT, GPT models
- State-of-the-art NLP

## Training Tips

1. Use proper data augmentation
2. Implement dropout for regularization
3. Use batch normalization
4. Choose appropriate learning rate"""
            }
        ]
    },
    {
        "name": "Product Design Guide",
        "description": "Comprehensive guide to product design, covering user research, prototyping, usability testing, and design systems.",
        "tags": ["Product", "UX", "Design"],
        "documents": [
            {
                "title": "User Research Methods",
                "content": """# User Research Methods

Understanding your users is fundamental to creating successful products.

## Research Types

### Qualitative Research
- Interviews
- Focus groups
- Contextual inquiry
- Ethnographic studies

### Quantitative Research
- Surveys
- Analytics
- A/B testing
- Usability metrics

## User Research Process

1. **Define Objectives**: What questions need answering?
2. **Choose Methods**: Match methods to objectives
3. **Recruit Participants**: Find representative users
4. **Conduct Research**: Gather data
5. **Analyze Findings**: Identify patterns and insights
6. **Share Results**: Communicate to stakeholders

## Creating User Personas

Personas are fictional representations of users:
- Demographics
- Goals and motivations
- Pain points
- Behaviors and preferences"""
            },
            {
                "title": "Prototyping Best Practices",
                "content": """# Prototyping Best Practices

Prototyping helps validate ideas before full development.

## Prototyping Levels

### Low-Fidelity
- Paper sketches
- Wireframes
- Quick and cheap
- Early ideation

### Mid-Fidelity
- Digital wireframes
- Interactive but simple
- Most common for UX

### High-Fidelity
- Fully designed
- Interactive
- Near final product

## Prototyping Tools

1. Figma
2. Sketch
3. Adobe XD
4. InVision
5. Axure

## Best Practices

- Start simple, iterate often
- Test with real users
- Don't fall in love with prototypes
- Use appropriate fidelity level
- Document decisions"""
            }
        ]
    },
    {
        "name": "Programming & Development",
        "description": "Programming guides covering Python, JavaScript, web development, APIs, databases, and best practices.",
        "tags": ["Programming", "Development", "Coding"],
        "documents": [
            {
                "title": "Python Best Practices",
                "content": """# Python Best Practices

Write clean, maintainable Python code.

## Code Style

### PEP 8 Guidelines
- 4 spaces for indentation
- 79 characters max line length
- Two blank lines between functions
- Descriptive variable names

### Naming Conventions
- Functions: snake_case
- Classes: PascalCase
- Constants: UPPER_SNAKE_CASE
- Modules: short, lowercase

## Functions

```python
def calculate_mean(numbers: list[float]) -> float:
    """Calculate the arithmetic mean of a list of numbers."""
    if not numbers:
        raise ValueError("Cannot calculate mean of empty list")
    return sum(numbers) / len(numbers)
```

## Type Hints

Use type hints for better code clarity:
```python
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

## Error Handling

- Be specific with exceptions
- Don't suppress errors
- Log appropriately
- Clean up resources with finally"""
            },
            {
                "title": "REST API Design Guide",
                "content": """# REST API Design Guide

Design clean, consistent, and scalable APIs.

## REST Principles

1. Client-Server Architecture
2. Statelessness
3. Cacheability
4. Uniform Interface

## URL Structure

```
/api/v1/users
/api/v1/users/{id}
/api/v1/users/{id}/orders
```

## HTTP Methods

| Method | Purpose |
|--------|---------|
| GET | Retrieve resources |
| POST | Create new resources |
| PUT | Update entire resource |
| PATCH | Partial update |
| DELETE | Remove resources |

## Response Codes

- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Server Error

## Best Practices

- Use nouns, not verbs
- Version your APIs
- Support filtering and pagination
- Return consistent error formats
- Document everything"""
            }
        ]
    },
    {
        "name": "Project Management",
        "description": "Effective project management strategies, including agile methodologies, task management, and team collaboration.",
        "tags": ["Management", "Agile", "Productivity"],
        "documents": [
            {
                "title": "Agile Methodology Overview",
                "content": """# Agile Methodology Overview

Agile is an iterative approach to project management and software development.

## Agile Manifesto Values

1. Individuals and interactions over processes and tools
2. Working software over comprehensive documentation
3. Customer collaboration over contract negotiation
4. Responding to change over following a plan

## Scrum Framework

### Roles
- **Product Owner**: Maximizes product value
- **Scrum Master**: Facilitates ceremonies
- **Development Team**: Delivers increments

### Ceremonies
- **Sprint Planning**: Define sprint goals
- **Daily Standup**: Sync team progress
- **Sprint Review**: Demo completed work
- **Sprint Retrospective**: Improve processes

### Artifacts
- **Product Backlog**: Prioritized features
- **Sprint Backlog**: Current sprint tasks
- **Increment**: Potentially shippable product

## Kanban Principles

1. Visualize workflow
2. Limit work in progress
3. Manage flow
4. Make policies explicit"""
            },
            {
                "title": "Task Management Strategies",
                "content": """# Task Management Strategies

Organize and prioritize work effectively.

## Prioritization Methods

### Eisenhower Matrix
- Urgent + Important: Do first
- Important + Not Urgent: Schedule
- Urgent + Not Important: Delegate
- Neither: Eliminate

### MoSCoW Method
- **M**ust have
- **S**hould have
- **C**ould have
- **W**on't have (this time)

### RICE Scoring
Score = (Reach × Impact × Confidence) / Effort

## Breaking Down Tasks

Use SMART criteria:
- Specific
- Measurable
- Achievable
- Relevant
- Time-bound

## Collaboration Tips

- Use clear task descriptions
- Assign ownership
- Set deadlines
- Link related tasks
- Document decisions"""
            }
        ]
    }
]

# Pre-built Workflow Templates
WORKFLOW_TEMPLATES = [
    {
        "name": "Content Creation Workflow",
        "description": "Automated workflow for creating and publishing content, from ideation to final review.",
        "graph_data": {
            "nodes": [
                {"id": "start", "type": "start", "position": {"x": 100, "y": 200}},
                {"id": "topic", "type": "input", "data": {"label": "Topic Input", "description": "Enter content topic"}},
                {"id": "research", "type": "llm", "data": {"label": "Research", "prompt": "Research and outline key points for: {{topic}}"}},
                {"id": "draft", "type": "llm", "data": {"label": "Draft", "prompt": "Write a first draft based on: {{research}}"}},
                {"id": "review", "type": "llm", "data": {"label": "Review", "prompt": "Review and suggest improvements for: {{draft}}"}},
                {"id": "finalize", "type": "llm", "data": {"label": "Finalize", "prompt": "Create final polished version incorporating: {{draft}}, {{review}}"}},
                {"id": "end", "type": "end", "data": {"label": "Complete"}}
            ],
            "edges": [
                {"source": "start", "target": "topic"},
                {"source": "topic", "target": "research"},
                {"source": "research", "target": "draft"},
                {"source": "draft", "target": "review"},
                {"source": "review", "target": "finalize"},
                {"source": "finalize", "target": "end"}
            ]
        }
    },
    {
        "name": "Code Review Workflow",
        "description": "Automated code review process that analyzes code quality, security, and best practices.",
        "graph_data": {
            "nodes": [
                {"id": "start", "type": "start", "position": {"x": 100, "y": 200}},
                {"id": "code_input", "type": "input", "data": {"label": "Code Input", "description": "Paste code to review"}},
                {"id": "syntax", "type": "llm", "data": {"label": "Syntax Check", "prompt": "Check for syntax errors and code style issues in: {{code_input}}"}},
                {"id": "security", "type": "llm", "data": {"label": "Security Scan", "prompt": "Identify potential security vulnerabilities in: {{code_input}}"}},
                {"id": "best_practices", "type": "llm", "data": {"label": "Best Practices", "prompt": "Review against best practices for: {{code_input}}"}},
                {"id": "summary", "type": "llm", "data": {"label": "Summary", "prompt": "Create a summary of findings from syntax: {{syntax}}, security: {{security}}, best practices: {{best_practices}}"}},
                {"id": "end", "type": "end", "data": {"label": "Review Complete"}}
            ],
            "edges": [
                {"source": "start", "target": "code_input"},
                {"source": "code_input", "target": "syntax"},
                {"source": "code_input", "target": "security"},
                {"source": "code_input", "target": "best_practices"},
                {"source": "syntax", "target": "summary"},
                {"source": "security", "target": "summary"},
                {"source": "best_practices", "target": "summary"},
                {"source": "summary", "target": "end"}
            ]
        }
    },
    {
        "name": "Data Analysis Workflow",
        "description": "End-to-end data analysis workflow from data ingestion to insights generation and visualization.",
        "graph_data": {
            "nodes": [
                {"id": "start", "type": "start", "position": {"x": 100, "y": 300}},
                {"id": "data_source", "type": "input", "data": {"label": "Data Source", "description": "Specify data source"}},
                {"id": "clean", "type": "llm", "data": {"label": "Data Cleaning", "prompt": "Analyze data quality and suggest cleaning steps for: {{data_source}}"}},
                {"id": "explore", "type": "llm", "data": {"label": "Exploratory Analysis", "prompt": "Perform exploratory data analysis on: {{data_source}}"}},
                {"id": "analyze", "type": "llm", "data": {"label": "Statistical Analysis", "prompt": "Conduct statistical analysis and identify patterns in: {{explore}}"}},
                {"id": "insights", "type": "llm", "data": {"label": "Generate Insights", "prompt": "Generate key insights and recommendations from: {{analyze}}"}},
                {"id": "report", "type": "llm", "data": {"label": "Create Report", "prompt": "Create a formatted report with visualizations recommendations based on: {{insights}}"}},
                {"id": "end", "type": "end", "data": {"label": "Analysis Complete"}}
            ],
            "edges": [
                {"source": "start", "target": "data_source"},
                {"source": "data_source", "target": "clean"},
                {"source": "data_source", "target": "explore"},
                {"source": "clean", "target": "analyze"},
                {"source": "explore", "target": "analyze"},
                {"source": "analyze", "target": "insights"},
                {"source": "insights", "target": "report"},
                {"source": "report", "target": "end"}
            ]
        }
    }
]

# Pre-built Example Conversations
EXAMPLE_CONVERSATIONS = [
    {
        "title": "Getting Started with AI Agents",
        "model": "llama2",
        "model_provider": "ollama",
        "messages": [
            {
                "role": "user",
                "content": "What are AI agents and how do they work?"
            },
            {
                "role": "assistant",
                "content": """AI agents are autonomous systems that can perceive their environment, make decisions, and take actions to achieve specific goals. Unlike simple chatbots that just respond to prompts, AI agents can:

1. **Plan and Reason**: Break down complex tasks into steps
2. **Use Tools**: Interact with external systems like web browsers, code executors, or APIs
3. **Maintain Memory**: Remember previous interactions and context
4. **Iterate**: Refine their approach based on feedback

For example, an AI agent could be given a goal like "research the latest AI developments and summarize them." It would:
1. Search the web for recent articles
2. Read and analyze the content
3. Synthesize the information
4. Present a coherent summary

AI agents typically combine a language model with tools and a loop that lets them take multiple actions until reaching their goal. Would you like to create an AI agent?"
            },
            {
                "role": "user",
                "content": "Yes, show me how to create a research agent."
            },
            {
                "role": "assistant",
                "content": """Great! I'll guide you through creating a research agent:

**Step 1: Define the Agent's Purpose**
Give your agent a clear role and instructions.

**Step 2: Add Tools**
Research agents typically need:
- Web search tool
- Web browsing tool
- Text summarization tool

**Step 3: Set Parameters**
- Model: Choose an appropriate model
- Temperature: 0.7 for balanced creativity
- Max tokens: 4096 for detailed responses

**Step 4: Test and Iterate**
Start with a simple task and gradually expand capabilities.

Would you like me to help you set up a research agent in the Agents section?"
            }
        ]
    },
    {
        "title": "Building a Knowledge Base",
        "model": "llama2",
        "model_provider": "ollama",
        "messages": [
            {
                "role": "user",
                "content": "How can I build a knowledge base with my documents?"
            },
            {
                "role": "assistant",
                "content": """Building a knowledge base allows you to create a searchable repository of your documents that an AI can query and cite. Here's how it works:

**Step 1: Create a Knowledge Base**
1. Go to the Knowledge section
2. Click "Create Knowledge Base"
3. Give it a name and description
4. Configure embedding settings (we recommend nomic-embed-text)

**Step 2: Add Documents**
You can add documents in several ways:
- Upload files (PDF, TXT, Markdown, etc.)
- Add content from URLs
- Paste text directly

**Step 3: Processing**
The system will:
1. Split documents into chunks
2. Generate embeddings for each chunk
3. Store in a vector database

**Step 4: Chat with Your Knowledge**
Use the RAG chat feature to ask questions. The AI will:
1. Find relevant chunks
2. Include them as context
3. Generate accurate answers with citations

Want to try creating one now?"
            },
            {
                "role": "user",
                "content": "What's the best way to organize my documents?"
            },
            {
                "role": "assistant",
                "content": """Here are best practices for organizing knowledge base documents:

**By Topic**
Group related documents together:
- Product documentation
- Technical guides
- Company policies

**By Use Case**
Organize for specific purposes:
- Customer support knowledge
- Employee onboarding
- Project documentation

**Tips for Better Results**
1. **Clear titles**: Use descriptive filenames
2. **Consistent formatting**: Use headers and structure
3. **Complete documents**: Avoid partial or outdated content
4. **Regular updates**: Keep content current

**Metadata**
Add tags to help with filtering:
- Department
- Date
- Document type
- Status (draft/review/published)

Would you like me to help you set up an organized knowledge base structure?"
            }
        ]
    },
    {
        "title": "Automating Workflows",
        "model": "llama2",
        "model_provider": "ollama",
        "messages": [
            {
                "role": "user",
                "content": "What are workflows and how can they help me?"
            },
            {
                "role": "assistant",
                "content": """Workflows let you automate complex, multi-step processes by chaining together different AI capabilities.

**What You Can Automate:**
- Content creation pipelines
- Code review processes
- Data analysis workflows
- Customer support routing
- Document processing

**Key Concepts:**

1. **Nodes**: Individual steps in the workflow
   - Start/End nodes
   - LLM nodes (for AI processing)
   - Input nodes (user parameters)
   - Conditional nodes (branching logic)

2. **Edges**: Connections between nodes

3. **Variables**: Pass data between nodes using {{variable_name}} syntax

**Example Workflow:**
```
Start → Input Topic → Research → Draft → Review → Finalize → End
```

Each step can use AI with specific prompts, and the output flows to the next step automatically.

Would you like to see some pre-built workflow templates?"
            },
            {
                "role": "user",
                "content": "Yes, show me the content creation workflow."
            },
            {
                "role": "assistant",
                "content": """Here's the Content Creation Workflow template:

**Flow:**
1. **Start** → 2. **Topic Input** → 3. **Research** → 4. **Draft** → 5. **Review** → 6. **Finalize** → 7. **End**

**How it works:**

1. **Topic Input**: You enter your content topic
2. **Research Node**: AI researches and outlines key points
3. **Draft Node**: AI writes a first draft based on research
4. **Review Node**: AI reviews and suggests improvements
5. **Finalize Node**: Creates polished final version
6. **End**: Outputs the complete content

**Benefits:**
- Consistent quality
- Multiple review rounds
- Time savings
- Scalable content production

You can customize each node's prompt to match your style and requirements. Would you like to create this workflow?"
            }
        ]
    }
]

# Welcome message for first-time users
WELCOME_MESSAGE = """
# Welcome to AI Platform! 🎉

You're all set up and ready to explore. Here's a quick tour:

## Getting Started

1. **Chat**: Start conversations with AI models
2. **Agents**: Create specialized AI assistants with custom prompts and tools
3. **Knowledge**: Build a searchable knowledge base from your documents
4. **Workflows**: Automate complex tasks with multi-step AI pipelines

## Key Features

- **Multi-Model Support**: Use Ollama (local) or cloud models like OpenAI
- **RAG Chat**: Chat with your uploaded documents
- **Tool Integration**: Agents can browse web, run code, and more
- **Dark Mode**: Toggle between light and dark themes

## Quick Tips

- Click "New Chat" to start a fresh conversation
- Use the sidebar to navigate between sections
- Your data is private and isolated to your account

Need help? Just ask me anything!
"""

# Onboarding checklist for new users
ONBOARDING_CHECKLIST = [
    {
        "id": "profile",
        "title": "Set up your profile",
        "description": "Add your name and customize your account",
        "action": "/settings",
        "completed": False
    },
    {
        "id": "model",
        "title": "Configure AI models",
        "description": "Connect to Ollama or add OpenAI API key",
        "action": "/models",
        "completed": False
    },
    {
        "id": "first_chat",
        "title": "Start your first chat",
        "description": "Try chatting with an AI model",
        "action": "/chat",
        "completed": False
    },
    {
        "id": "create_agent",
        "title": "Create an agent",
        "description": "Build a specialized AI assistant",
        "action": "/agents/new",
        "completed": False
    },
    {
        "id": "add_knowledge",
        "title": "Add knowledge",
        "description": "Upload documents to your knowledge base",
        "action": "/knowledge",
        "completed": False
    }
]
