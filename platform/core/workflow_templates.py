#!/usr/bin/env python3
"""
Workflow Templates - Smart agent selection based on work type

Different types of work need different agents. This module provides
templates that automatically select the right agents for each job.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class WorkflowTemplate:
    """Template defining which agents are needed for a type of work"""
    id: str
    name: str
    description: str
    agents: List[str]  # Agent IDs in execution order
    parallel_stages: List[List[str]] = None  # Groups that can run in parallel
    conditions: Dict[str, str] = None  # Conditional agent inclusion


# ============================================================================
# Development Templates
# ============================================================================

SIMPLE_WEBSITE = WorkflowTemplate(
    id='simple_website',
    name='Simple Website',
    description='Landing page, portfolio, blog',
    agents=['pm', 'frontend_dev', 'qa_tester'],
    parallel_stages=None
)

FULLSTACK_APP = WorkflowTemplate(
    id='fullstack_app',
    name='Full-stack Application',
    description='Complete web application with backend',
    agents=[
        'pm',
        'business_analyst',
        'tech_lead',
        'uxui_designer',
        # Parallel development
        'frontend_dev',  # These 2 run parallel
        'backend_dev',   #
        # Testing & deployment
        'qa_tester',
        'security_auditor',
        'devops'
    ],
    parallel_stages=[
        ['frontend_dev', 'backend_dev']  # Can work simultaneously
    ]
)

MOBILE_APP = WorkflowTemplate(
    id='mobile_app',
    name='Mobile Application',
    description='iOS/Android app',
    agents=[
        'pm',
        'tech_lead',
        'uxui_designer',
        'mobile_dev',
        'qa_tester',
        'devops'
    ]
)

API_BACKEND = WorkflowTemplate(
    id='api_backend',
    name='API/Backend Service',
    description='REST API, microservice, backend only',
    agents=[
        'pm',
        'tech_lead',
        'backend_dev',
        'qa_tester',
        'security_auditor',
        'devops'
    ]
)

CODE_REVIEW = WorkflowTemplate(
    id='code_review',
    name='Code Review',
    description='Review existing code for quality & security',
    agents=[
        'tech_lead',
        'security_auditor',
        'qa_tester'
    ]
)

# ============================================================================
# Marketing Templates
# ============================================================================

CONTENT_CAMPAIGN = WorkflowTemplate(
    id='content_campaign',
    name='Content Marketing Campaign',
    description='Blog posts, SEO content, social media',
    agents=[
        'marketing_lead',
        'content_writer',
        'seo_specialist',
        'social_media_manager'
    ],
    parallel_stages=[
        ['content_writer', 'copywriter']  # Can write simultaneously
    ]
)

SEO_OPTIMIZATION = WorkflowTemplate(
    id='seo_optimization',
    name='SEO Optimization',
    description='Improve search rankings',
    agents=[
        'seo_specialist',
        'content_writer'
    ]
)

# ============================================================================
# Creative Templates
# ============================================================================

BRANDING_PROJECT = WorkflowTemplate(
    id='branding',
    name='Branding & Design',
    description='Logo, brand identity, design system',
    agents=[
        'creative_director',
        'graphic_designer',
        'ui_designer'
    ]
)

VIDEO_PRODUCTION = WorkflowTemplate(
    id='video_production',
    name='Video Production',
    description='Promotional video, tutorial, demo',
    agents=[
        'creative_director',
        'motion_designer',
        'video_editor'
    ]
)

# ============================================================================
# Template Registry
# ============================================================================

ALL_TEMPLATES = {
    # Development
    'simple_website': SIMPLE_WEBSITE,
    'fullstack_app': FULLSTACK_APP,
    'mobile_app': MOBILE_APP,
    'api_backend': API_BACKEND,
    'code_review': CODE_REVIEW,

    # Marketing
    'content_campaign': CONTENT_CAMPAIGN,
    'seo_optimization': SEO_OPTIMIZATION,

    # Creative
    'branding': BRANDING_PROJECT,
    'video_production': VIDEO_PRODUCTION,
}


def get_template(template_id: str) -> Optional[WorkflowTemplate]:
    """Get workflow template by ID"""
    return ALL_TEMPLATES.get(template_id)


def list_templates(category: Optional[str] = None) -> List[WorkflowTemplate]:
    """List all available templates"""
    templates = list(ALL_TEMPLATES.values())

    if category:
        # Filter by category (future enhancement)
        pass

    return templates


def suggest_template(description: str) -> WorkflowTemplate:
    """
    Suggest best template based on work description.

    Future: Use LLM to analyze description and pick best template.
    For now, return fullstack_app as default.
    """
    description_lower = description.lower()

    # Simple keyword matching
    if any(word in description_lower for word in ['website', 'landing', 'portfolio', 'blog']):
        return SIMPLE_WEBSITE

    elif any(word in description_lower for word in ['mobile', 'ios', 'android', 'app']):
        return MOBILE_APP

    elif any(word in description_lower for word in ['api', 'backend', 'microservice']):
        return API_BACKEND

    elif any(word in description_lower for word in ['review', 'audit', 'refactor']):
        return CODE_REVIEW

    elif any(word in description_lower for word in ['content', 'blog', 'seo', 'article']):
        return CONTENT_CAMPAIGN

    elif any(word in description_lower for word in ['video', 'motion', 'animation']):
        return VIDEO_PRODUCTION

    elif any(word in description_lower for word in ['brand', 'logo', 'design']):
        return BRANDING_PROJECT

    # Default to full-stack
    return FULLSTACK_APP


# Example usage
if __name__ == '__main__':
    print("📋 Available Workflow Templates:\n")

    for template in list_templates():
        print(f"🎯 {template.name}")
        print(f"   {template.description}")
        print(f"   Agents: {' → '.join(template.agents)}")
        if template.parallel_stages:
            print(f"   Parallel: {template.parallel_stages}")
        print()

    # Test suggestion
    print("\n🤖 Template Suggestion:")
    desc = "Build a mobile app for iOS and Android"
    suggested = suggest_template(desc)
    print(f"   Input: {desc}")
    print(f"   Suggested: {suggested.name}")
    print(f"   Agents: {', '.join(suggested.agents)}")
