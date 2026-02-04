#!/usr/bin/env python3
"""
Run Tech Company Website Project with Ollama
This script directly calls Ollama API to generate website files
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime

# Configuration
OLLAMA_URL = "http://localhost:11434"
PROJECT_PATH = Path.home() / "workspace" / "6amdev-platform" / "projects" / "active" / "techwave-website"

# Agent configurations
AGENTS = {
    "uxui_designer": {
        "model": "llama3:latest",
        "temperature": 0.6,
        "role": "UX/UI Designer"
    },
    "frontend_dev": {
        "model": "qwen2.5-coder:7b",
        "temperature": 0.3,
        "role": "Frontend Developer"
    },
    "tech_lead": {
        "model": "deepseek-r1:8b",
        "temperature": 0.3,
        "role": "Tech Lead"
    }
}

def call_ollama(model: str, prompt: str, system: str = None, temperature: float = 0.5) -> str:
    """Call Ollama API"""
    url = f"{OLLAMA_URL}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature
        }
    }

    if system:
        payload["system"] = system

    print(f"   Calling {model}...", end=" ", flush=True)

    try:
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()
        print("✅")
        return result.get("response", "")
    except Exception as e:
        print(f"❌ Error: {e}")
        return ""

def extract_code_block(text: str, lang: str = None) -> str:
    """Extract code from markdown code blocks"""
    import re

    if lang:
        pattern = rf"```{lang}\n(.*?)```"
    else:
        pattern = r"```(?:\w+)?\n(.*?)```"

    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return matches[0].strip()
    return text

def save_file(path: Path, content: str):
    """Save content to file"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    print(f"   Saved: {path.name}")

def run_stage_1_design():
    """Stage 1: UX/UI Design"""
    print("\n" + "="*60)
    print("Stage 1: Website Design (uxui_designer → llama3)")
    print("="*60)

    agent = AGENTS["uxui_designer"]

    system_prompt = """You are a UX/UI Designer creating a website design document.
Be concise and practical. Focus on modern, clean design."""

    prompt = """Create a design document for TechWave Solutions website.

TechWave Solutions is a technology company with services:
1. AI & Machine Learning
2. Cloud Infrastructure
3. Digital Transformation
4. Software Development

Create DESIGN.md with:
1. Color scheme (hex codes)
2. Typography (font recommendations)
3. Page layout structure
4. Component list

Keep it concise and actionable."""

    response = call_ollama(
        model=agent["model"],
        prompt=prompt,
        system=system_prompt,
        temperature=agent["temperature"]
    )

    save_file(PROJECT_PATH / "DESIGN.md", response)
    return response

def run_stage_2_development():
    """Stage 2: Frontend Development"""
    print("\n" + "="*60)
    print("Stage 2: Development (frontend_dev → qwen2.5-coder)")
    print("="*60)

    agent = AGENTS["frontend_dev"]

    # Generate HTML
    print("\n   [2.1] Creating index.html...")
    html_response = call_ollama(
        model=agent["model"],
        prompt="""Create a complete index.html for TechWave Solutions website.

Requirements:
- Modern tech company landing page
- Hero section with tagline "Innovating Tomorrow, Today"
- Services section (4 services: AI/ML, Cloud, Digital Transformation, Software Dev)
- About section
- Contact form
- Footer
- Link to css/style.css and js/main.js
- Use semantic HTML5
- Mobile-friendly structure

Output ONLY the HTML code, no explanation.""",
        system="You are a frontend developer. Output only clean, valid HTML code.",
        temperature=agent["temperature"]
    )

    html_code = extract_code_block(html_response, "html") or html_response
    if not html_code.strip().startswith("<!DOCTYPE") and not html_code.strip().startswith("<"):
        # If response is not HTML, use a template
        html_code = create_fallback_html()

    save_file(PROJECT_PATH / "index.html", html_code)

    # Generate CSS
    print("\n   [2.2] Creating style.css...")
    css_response = call_ollama(
        model=agent["model"],
        prompt="""Create CSS for a modern tech company website.

Requirements:
- Modern, clean design
- Color scheme: #1a1a2e (dark), #16213e (navy), #0f3460 (blue), #e94560 (accent)
- Responsive (mobile-first)
- Flexbox/Grid layout
- Smooth animations
- Professional typography

Sections to style:
- Navigation
- Hero section
- Services grid (4 cards)
- About section
- Contact form
- Footer

Output ONLY CSS code, no explanation.""",
        system="You are a CSS expert. Output only clean, valid CSS code.",
        temperature=agent["temperature"]
    )

    css_code = extract_code_block(css_response, "css") or css_response
    save_file(PROJECT_PATH / "css" / "style.css", css_code)

    # Generate JS
    print("\n   [2.3] Creating main.js...")
    js_response = call_ollama(
        model=agent["model"],
        prompt="""Create simple JavaScript for a company website.

Features needed:
- Smooth scroll for navigation links
- Mobile menu toggle
- Form validation for contact form
- Simple scroll animations

Output ONLY JavaScript code, no explanation.""",
        system="You are a JavaScript developer. Output only clean, valid JavaScript code.",
        temperature=agent["temperature"]
    )

    js_code = extract_code_block(js_response, "javascript") or js_response
    save_file(PROJECT_PATH / "js" / "main.js", js_code)

def run_stage_3_review():
    """Stage 3: Code Review"""
    print("\n" + "="*60)
    print("Stage 3: Code Review (tech_lead → deepseek-r1)")
    print("="*60)

    agent = AGENTS["tech_lead"]

    # Read generated files
    html_file = PROJECT_PATH / "index.html"
    css_file = PROJECT_PATH / "css" / "style.css"

    html_content = html_file.read_text(encoding='utf-8') if html_file.exists() else "Not found"
    css_content = css_file.read_text(encoding='utf-8') if css_file.exists() else "Not found"

    prompt = f"""Review this website code:

=== index.html ===
{html_content[:2000]}...

=== style.css ===
{css_content[:1500]}...

Create a brief code review with:
1. Overall assessment (1-10)
2. Strengths
3. Areas for improvement
4. Security considerations

Be concise."""

    response = call_ollama(
        model=agent["model"],
        prompt=prompt,
        system="You are a Tech Lead reviewing frontend code. Be constructive and concise.",
        temperature=agent["temperature"]
    )

    save_file(PROJECT_PATH / "REVIEW.md", response)

def create_fallback_html():
    """Fallback HTML if generation fails"""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TechWave Solutions - Innovating Tomorrow, Today</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <nav class="navbar">
        <div class="logo">TechWave</div>
        <ul class="nav-links">
            <li><a href="#home">Home</a></li>
            <li><a href="#services">Services</a></li>
            <li><a href="#about">About</a></li>
            <li><a href="#contact">Contact</a></li>
        </ul>
    </nav>

    <section id="home" class="hero">
        <h1>Innovating Tomorrow, Today</h1>
        <p>Your trusted partner in digital transformation</p>
        <a href="#contact" class="cta-button">Get Started</a>
    </section>

    <section id="services" class="services">
        <h2>Our Services</h2>
        <div class="services-grid">
            <div class="service-card">
                <h3>AI & Machine Learning</h3>
                <p>Custom AI solutions for business automation</p>
            </div>
            <div class="service-card">
                <h3>Cloud Infrastructure</h3>
                <p>Scalable cloud solutions on AWS, GCP, Azure</p>
            </div>
            <div class="service-card">
                <h3>Digital Transformation</h3>
                <p>End-to-end digital transformation consulting</p>
            </div>
            <div class="service-card">
                <h3>Software Development</h3>
                <p>Custom software and mobile app development</p>
            </div>
        </div>
    </section>

    <section id="about" class="about">
        <h2>About TechWave</h2>
        <p>We are a leading technology company dedicated to helping businesses thrive in the digital age.</p>
    </section>

    <section id="contact" class="contact">
        <h2>Contact Us</h2>
        <form class="contact-form">
            <input type="text" placeholder="Name" required>
            <input type="email" placeholder="Email" required>
            <textarea placeholder="Message" required></textarea>
            <button type="submit">Send Message</button>
        </form>
    </section>

    <footer>
        <p>&copy; 2024 TechWave Solutions. All rights reserved.</p>
    </footer>

    <script src="js/main.js"></script>
</body>
</html>"""

def main():
    print("="*60)
    print("  TechWave Website - Ollama Multi-Agent Build")
    print("="*60)
    print(f"\nProject: {PROJECT_PATH}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check Ollama
    print("\nChecking Ollama...")
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        models = response.json().get("models", [])
        print(f"   ✅ Ollama running with {len(models)} models")
        print("   Models:", ", ".join(m["name"] for m in models))
    except Exception as e:
        print(f"   ❌ Ollama not accessible: {e}")
        return

    # Create project directory
    PROJECT_PATH.mkdir(parents=True, exist_ok=True)

    # Run stages
    run_stage_1_design()
    run_stage_2_development()
    run_stage_3_review()

    # Summary
    print("\n" + "="*60)
    print("  BUILD COMPLETE!")
    print("="*60)
    print(f"\nFiles created in: {PROJECT_PATH}")

    for f in PROJECT_PATH.rglob("*"):
        if f.is_file():
            size = f.stat().st_size
            print(f"   {f.relative_to(PROJECT_PATH)} ({size} bytes)")

    print("\nTo view the website:")
    print(f"   cd {PROJECT_PATH}")
    print("   python3 -m http.server 8080")
    print("   Open: http://localhost:8080")

if __name__ == "__main__":
    main()
