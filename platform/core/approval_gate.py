#!/usr/bin/env python3
"""
Approval Gate System for WitMind.AI Platform
Handles human checkpoints in workflows
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    PARTIAL = "partial"


class ApprovalGate:
    """Manages approval gates in workflows."""

    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.approvals_path = self.root / 'logs' / 'approvals'
        self.approvals_path.mkdir(parents=True, exist_ok=True)

    def create_approval_request(
        self,
        project_id: str,
        stage: str,
        files_to_review: List[str],
        description: str,
        available_actions: List[Dict],
        metadata: Dict = None
    ) -> str:
        """Create an approval request for human review."""

        request_id = f"{project_id}_{stage}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        request = {
            'id': request_id,
            'project_id': project_id,
            'stage': stage,
            'status': ApprovalStatus.PENDING.value,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),

            'description': description,
            'files_to_review': files_to_review,
            'available_actions': available_actions,

            'response': None,
            'user_notes': None,
            'responded_at': None,

            'metadata': metadata or {}
        }

        # Save request
        request_file = self.approvals_path / f"{request_id}.json"
        with open(request_file, 'w', encoding='utf-8') as f:
            json.dump(request, f, indent=2, ensure_ascii=False)

        # Create notification
        self._notify_user(request)

        return request_id

    def get_pending_approvals(self, project_id: str = None) -> List[Dict]:
        """Get all pending approval requests."""
        pending = []

        for file in self.approvals_path.glob('*.json'):
            with open(file, 'r', encoding='utf-8') as f:
                request = json.load(f)

            if request['status'] == ApprovalStatus.PENDING.value:
                if project_id is None or request['project_id'] == project_id:
                    pending.append(request)

        return sorted(pending, key=lambda x: x['created_at'])

    def respond_to_approval(
        self,
        request_id: str,
        action: str,
        notes: str = None,
        additional_data: Dict = None
    ) -> Dict:
        """Respond to an approval request."""

        request_file = self.approvals_path / f"{request_id}.json"

        if not request_file.exists():
            raise ValueError(f"Approval request not found: {request_id}")

        with open(request_file, 'r', encoding='utf-8') as f:
            request = json.load(f)

        # Validate action
        valid_actions = [a['action'] for a in request['available_actions']]
        if action not in valid_actions:
            raise ValueError(f"Invalid action: {action}. Valid: {valid_actions}")

        # Update request
        request['status'] = self._action_to_status(action)
        request['response'] = {
            'action': action,
            'additional_data': additional_data or {}
        }
        request['user_notes'] = notes
        request['responded_at'] = datetime.now().isoformat()
        request['updated_at'] = datetime.now().isoformat()

        # Save updated request
        with open(request_file, 'w', encoding='utf-8') as f:
            json.dump(request, f, indent=2, ensure_ascii=False)

        return request

    def wait_for_approval(self, request_id: str, timeout_seconds: int = None) -> Dict:
        """Wait for approval response (blocking)."""
        import time

        request_file = self.approvals_path / f"{request_id}.json"
        start_time = time.time()

        while True:
            if not request_file.exists():
                raise ValueError(f"Approval request not found: {request_id}")

            with open(request_file, 'r', encoding='utf-8') as f:
                request = json.load(f)

            if request['status'] != ApprovalStatus.PENDING.value:
                return request

            if timeout_seconds and (time.time() - start_time) > timeout_seconds:
                raise TimeoutError(f"Approval timeout for {request_id}")

            time.sleep(5)  # Check every 5 seconds

    def _action_to_status(self, action: str) -> str:
        """Convert action to status."""
        if action in ['approve', 'approve_partial']:
            return ApprovalStatus.APPROVED.value
        elif action in ['reject', 'cancel']:
            return ApprovalStatus.REJECTED.value
        elif action in ['modify_plan', 'request_more_analysis', 'add_requirements']:
            return ApprovalStatus.MODIFIED.value
        else:
            return ApprovalStatus.PENDING.value

    def _notify_user(self, request: Dict):
        """Send notification to user about pending approval."""
        # Create notification file
        notif_path = self.root / 'logs' / 'notifications'
        notif_path.mkdir(parents=True, exist_ok=True)

        notification = {
            'type': 'approval_needed',
            'request_id': request['id'],
            'project_id': request['project_id'],
            'stage': request['stage'],
            'description': request['description'],
            'files': request['files_to_review'],
            'created_at': datetime.now().isoformat(),
            'read': False
        }

        notif_file = notif_path / f"approval_{request['id']}.json"
        with open(notif_file, 'w', encoding='utf-8') as f:
            json.dump(notification, f, indent=2, ensure_ascii=False)

        # Also print to console for CLI
        print(f"\n{'='*60}")
        print(f"🔔 APPROVAL NEEDED: {request['stage']}")
        print(f"{'='*60}")
        print(f"Project: {request['project_id']}")
        print(f"Description: {request['description']}")
        print(f"\nFiles to review:")
        for f in request['files_to_review']:
            print(f"  - {f}")
        print(f"\nActions available:")
        for action in request['available_actions']:
            print(f"  - {action['action']}: {action['description']}")
        print(f"\nRun: wit approve {request['id']} --action <action>")
        print(f"{'='*60}\n")


class ApprovalCLI:
    """CLI commands for approval management."""

    def __init__(self, root_path: str):
        self.gate = ApprovalGate(root_path)
        self.root = Path(root_path)

    def list_pending(self, project_id: str = None):
        """List all pending approvals."""
        pending = self.gate.get_pending_approvals(project_id)

        if not pending:
            print("\n✅ No pending approvals\n")
            return

        print(f"\n📋 Pending Approvals ({len(pending)}):\n")

        for req in pending:
            print(f"  ID: {req['id']}")
            print(f"  Project: {req['project_id']}")
            print(f"  Stage: {req['stage']}")
            print(f"  Created: {req['created_at'][:16]}")
            print(f"  Files: {len(req['files_to_review'])} files")
            print()

    def show_approval(self, request_id: str):
        """Show details of an approval request."""
        request_file = self.gate.approvals_path / f"{request_id}.json"

        if not request_file.exists():
            print(f"\n❌ Approval request not found: {request_id}\n")
            return

        with open(request_file, 'r', encoding='utf-8') as f:
            request = json.load(f)

        print(f"\n{'='*60}")
        print(f"📋 Approval Request: {request['id']}")
        print(f"{'='*60}")
        print(f"\nProject: {request['project_id']}")
        print(f"Stage: {request['stage']}")
        print(f"Status: {request['status']}")
        print(f"Created: {request['created_at']}")

        print(f"\n📝 Description:")
        print(f"   {request['description']}")

        print(f"\n📁 Files to Review:")
        project_path = self.root / 'projects' / 'active' / request['project_id']
        for f in request['files_to_review']:
            file_path = project_path / f
            status = "✅" if file_path.exists() else "❌"
            print(f"   {status} {f}")

        print(f"\n🎯 Available Actions:")
        for action in request['available_actions']:
            print(f"   - {action['action']}: {action['description']}")
            if action.get('prompt_user'):
                print(f"     (จะถาม: {action['prompt_user']})")

        print(f"\n{'='*60}\n")

    def approve(self, request_id: str, action: str, notes: str = None):
        """Respond to an approval request."""
        try:
            result = self.gate.respond_to_approval(
                request_id=request_id,
                action=action,
                notes=notes
            )
            print(f"\n✅ Approval response recorded: {action}")
            print(f"   Request: {request_id}")
            if notes:
                print(f"   Notes: {notes}")
            print()
        except ValueError as e:
            print(f"\n❌ Error: {e}\n")

    def review_file(self, request_id: str, file_path: str):
        """Open a file for review (show content)."""
        request_file = self.gate.approvals_path / f"{request_id}.json"

        if not request_file.exists():
            print(f"\n❌ Approval request not found: {request_id}\n")
            return

        with open(request_file, 'r', encoding='utf-8') as f:
            request = json.load(f)

        project_path = self.root / 'projects' / 'active' / request['project_id']
        full_path = project_path / file_path

        if not full_path.exists():
            print(f"\n❌ File not found: {file_path}\n")
            return

        print(f"\n{'='*60}")
        print(f"📄 {file_path}")
        print(f"{'='*60}\n")

        content = full_path.read_text(encoding='utf-8')
        print(content)
        print(f"\n{'='*60}\n")


# Singleton instance
_approval_gate = None


def get_approval_gate(root_path: str = None) -> ApprovalGate:
    """Get or create the approval gate instance."""
    global _approval_gate
    if _approval_gate is None:
        if root_path is None:
            root_path = os.environ.get('WITMIND_ROOT', str(Path.home() / 'witmind-data'))
        _approval_gate = ApprovalGate(root_path)
    return _approval_gate
