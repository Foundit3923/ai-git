#!/usr/bin/env python3
"""
AI Commit - Generate commit messages using local Ollama

Author: Himanshu Kumar
GitHub: https://github.com/himanshu231204/ai-commit
Email: himanshu231204@gmail.com
"""

import json
import subprocess
import sys
import argparse
from typing import Optional
import requests


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class AiSummary:
    general_summary = ""
    general_summary_type = "single_file_general"
    complete_file_changes_summary = ""
    complete_file_changes_summary_type = "single_file_complete_file_changes"
    oldest_newest_diff_summary = ""
    oldest_newest_diff_summary_type = "single_file_oldest_newest_diff"

class GitHash:
    hash = ""
    is_valid = False

    def __init__(self, _hash: str):
        if _hash:
            self.hash = _hash
            if GitService.validate_hash(hash):
                self.is_valid = True

class FileDetails:
    git_summary = None #GitSummary
    file_path = ""
    file_name = ""
    oldest_commit_hash = None #GitHash
    newest_commit_hash = None #GitHash
    oldest_commit_complete_file = ""
    newest_commit_complete_file = ""
    oldest_newest_diff = ""
    ai_summary = None #AiSummary
    is_new = False
    is_changed = False
    is_removed = False
    is_ready = False
    has_summary = False

    def __init__(self, _git_summary: GitSummary, _file_path: str, _is_new: bool, _is_changed: bool, _is_removed: bool):
        if (_git_summary):
            self.git_summary = _git_summary
        else:
            raise ValueError(f"GitSummary is not valid: ${_git_summary} is not valid")
        
        if _file_path:
            self.file_path = _file_path
            file_name = self.file_path.split('/')[-1]
        else:
            raise ValueError(f"File path: ${_file_path} is not valid")

    
        self.is_new = _is_new
        self.is_changed = _is_changed   
        self.is_removed = _is_removed

        self.ai_summary = AiSummary()

        suffix = ""
        if self.is_new:
            suffix = "_new"
        elif self.is_changed:
            suffix = "_changed"
        elif self.is_removed:
            suffix = "_removed"

        self.ai_summary.complete_file_changes_summary_type = self.ai_summary.complete_file_changes_summary_type + suffix
        self.ai_summary.general_summary_type = self.ai_summary.general_summary_type + suffix
        self.ai_summary.oldest_newest_diff_summary_type = self.ai_summary.oldest_newest_diff_summary_type + suffix

        self.get_oldest_commit_hash()
        self.get_newest_commit_hash()
        self.get_oldest_version_of_file()
        self.get_newest_version_of_file()
        self.get_oldest_newest_diff()
        self.is_ready = True

    def __key(self):
        return (self.file_path)

    def __hash__(self):
        return hash(self.__key)

    def __eq__(self, other):
        if isinstance(other,FileDetails):
            return self.__key() == other.__key()
        return NotImplemented   

    def get_oldest_commit_hash(self):
        for commit_hash in self.git_summary.commit_hashes_in_range.reverse:
            files_touched_by_commit = GitService.get_all_files_touched_in_commit(commit_hash)
            for file_data in files_touched_by_commit:
                if self.file_path in file_data:
                    self.oldest_commit_hash = commit_hash   

    def get_newest_commit_hash(self):
        for commit_hash in self.git_summary.commit_hashes_in_range:
            files_touched_by_commit = GitService.get_all_files_touched_in_commit(commit_hash)
            for file_data in files_touched_by_commit:
                if self.file_path in file_data:
                    self.oldest_commit_hash = commit_hash   

    def get_oldest_version_of_file(self):
        self.oldest_commit_complete_file = GitService.get_file_from_commit(self.file_path, self.oldest_commit_hash)

    def get_newest_version_of_file(self):
        self.newest_commit_complete_file = GitService.get_file_from_commit(self.file_path, self.newest_commit_hash)

    def get_oldest_newest_diff(self):
        self.oldest_newest_diff = GitService.get_file_diff_between_commits(self.file_path, self.oldest_commit_hash, self.newest_commit_hash)

    def get_ai_summary(self):
        if self.is_ready:
            self.ai_summary.complete_file_changes_summary = self.git_summary.generator.generate_single_file_message(self.git_summary.diff, self, self.ai_summary.complete_file_changes_summary_type)
            self.ai_summary.oldest_newest_diff_summary = self.git_summary.generator.generate_single_file_message(self.git_summary.diff, self, self.ai_summary.oldest_newest_diff_summary_type)
            self.ai_summary.general_summary = self.git_summary.generator.generate_single_file_message(self.git_summary.diff, self, self.ai_summary.general_summary_type)

    def print_summary(self):
        print(f"{Colors.GREEN}{Colors.BOLD} {self.file_name} Summary:{Colors.END}")
        print(f"{Colors.BOLD}General Summary: {self.ai_summary.general_summary}{Colors.END}\n")
        print(f"{Colors.BOLD}Complete File Changes Summary: {self.ai_summary.complete_file_changes_summary}{Colors.END}\n")
        print(f"{Colors.BOLD}Oldest/Newest Diff Summary: {self.ai_summary.oldest_newest_diff_summary}{Colors.END}\n")
        print(f"{Colors.CYAN}{'─' * 25}{Colors.END}\n")
        

class GitSummary:
    generator = None #CommitGenerator(ollama)
    diff = ""
    commit_hash_range_oldest: GitHash = None #GitHash
    commit_hash_range_newest: GitHash = None #GitHash
    commit_hashes_in_range: list[GitHash] = [] #GitHash[]
    all_files_raw = [] #str
    new_files: list[FileDetails] = [] #FileDetails[]
    changed_files: list[FileDetails] = [] #FileDetails[]
    removed_files: list[FileDetails] = [] #FileDetails[]
    is_range = False
    is_staged = False
    is_ready = False

    def __init__(self, _commit_hash_1: str, _commit_hash_2: str, _generator: CommitGenerator, _diff: str ):
        staged_check = False
        git_hash_1 = GitHash(_commit_hash_1)
        if git_hash_1.is_valid:
            self.commit_hash_range_oldest = git_hash_1 
        elif _commit_hash_1 is None:
            raise ValueError(f"Commit hash 1: ${_commit_hash_1} is not valid")
        else:
            staged_check = True

        git_hash_2 = GitHash(_commit_hash_2)
        if git_hash_2.is_valid:
            self.commit_hash_range_newest = git_hash_2
        elif _commit_hash_2 is None:
            raise ValueError(f"Commit hash 2: ${_commit_hash_2} is not valid")
        else:
            if staged_check:
                if GitService.has_staged_changes():
                    self.is_staged = True

        if self.is_staged is False:
            if self.commit_hash_range_oldest.hash is not self.commit_hash_range_newest.hash:
                self.is_range = True

        if _generator:
            self.generator = _generator    

        if _diff:
            self.diff = _diff   

        if self.is_range:
            self.compile_all_commit_hashes_in_range()
        else:
            self.commit_hashes_in_range.append(self.commit_hash_range_oldest)

        self.compile_list_of_all_files_touched_in_range()
        self.compile_list_of_all_new_files()
        self.compile_list_of_all_removed_files()
        self.compile_list_of_all_changed_files()
        self.is_ready = True

    def compile_all_commit_hashes_in_range(self):
        self.commit_hashes_in_range = GitService.get_list_of_ancestry_path(self.commit_hash_range_oldest, self.commit_hash_range_newest)

    def compile_list_of_all_files_touched_in_range(self):
        self.all_files_raw = GitService.get_all_files_touched_in_range(self.commit_hashes_in_range)
    
    def compile_list_of_all_new_files(self):
        for file in self.all_files_raw:
            if file[0] is 'A':
                name_only = file[1:].lstrip()
                file_details = FileDetails(self, name_only, True, False, False)
                if file_details not in self.new_files:
                    self.new_files.append(name_only)

    def compile_list_of_all_removed_files(self):
        for file in self.all_files_raw:
            if file[0] is 'D':
                name_only = file[1:].lstrip()
                if name_only not in self.removed_files:
                    self.removed_files.append(name_only)

    def compile_list_of_all_changed_files(self):
        for file in self.all_files_raw:
            if file[0] is 'M':
                name_only = file[1:].lstrip()
                if name_only not in self.changed_files:
                    self.changed_files.append(name_only)

    def generate_summaries(self):
        for new_file_details in self.new_files:
            new_file_details.get_ai_summary()

        for changed_file_details in self.changed_files:
            changed_file_details.get_ai_summary()

        for removed_file_details in self.removed_files:
            removed_file_details.get_ai_summary()

    def print_summaries(self):
        print(f"{Colors.GREEN}{Colors.BOLD} New Files:{Colors.END}\n")
        print(f"{Colors.CYAN}{'─' * 50}{Colors.END}\n")
        for new_file_details in self.new_files:
            new_file_details.print_summary()

        print(f"\n{Colors.GREEN}{Colors.BOLD} Changed Files:{Colors.END}\n")
        print(f"{Colors.CYAN}{'─' * 50}{Colors.END}\n")
        for changed_file_details in self.changed_files:
            changed_file_details.print_summary()

        print(f"\n{Colors.GREEN}{Colors.BOLD} Removed Files:{Colors.END}\n")
        print(f"{Colors.CYAN}{'─' * 50}{Colors.END}\n")
        for removed_file_details in self.removed_files:
            removed_file_details.print_summary()
        

class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = None):
        self.base_url = base_url.rstrip('/')
        self.model = model  # Will be auto-selected if None
    
    def is_available(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def list_models(self) -> list:
        """List available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except requests.exceptions.RequestException:
            return []
    
    def auto_select_model(self) -> Optional[str]:
        """
        Auto-select the best available model.
        Priority: lighter/faster models first for better performance
        """
        available = self.list_models()
        
        if not available:
            return None
        
        # Priority order: lightest/fastest first
        # phi > mistral > codellama > llama2 > llama3 (larger models)
        priority_order = [
            'phi',           # Smallest, fastest
            'mistral',       # Fast and good quality
            'qwen',          # Fast alternative
            'codellama',     # Good for code
            'llama2',        # Larger but reliable
            'llama2:13b',     # Even larger but reliable
            'llama3',        # Largest, slowest
            'llama3.2',       # BIG BEEFY BOY
            'ssfdre38/gemma4-nano', #Newest
            'jacobatkinson200/code-reviewer', #code review test
            'moesaif/meer-whale-1' #another test
        ]
        
        # First, try to match exact priority
        for priority_model in priority_order:
            for available_model in available:
                if available_model.lower().startswith(priority_model):
                    return available_model
        
        # If no match, return first available
        return available[0]
    
    def generate(self, prompt: str, ctx: int = 2026) -> Optional[str]:
        """Generate text using Ollama"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_ctx": ctx
                    }
                },
                timeout=120  # Increased to 2 minutes for larger models
            )
            
            if response.status_code == 200:
                return response.json().get('response', '').strip()
            else:
                print(f"{Colors.RED}Ollama returned status {response.status_code}{Colors.END}")
                return None
        except requests.exceptions.Timeout:
            print(f"{Colors.RED}Request timed out. Model '{self.model}' might be too large.{Colors.END}")
            print(f"{Colors.YELLOW}Try using a lighter model like 'phi' or 'mistral'{Colors.END}")
            return None
        except requests.exceptions.ConnectionError:
            print(f"{Colors.RED}Cannot connect to Ollama at {self.base_url}{Colors.END}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"{Colors.RED}Error: {e}{Colors.END}")
            return None

class GitService:
    """Service for Git operations"""
    
    @staticmethod
    def is_git_repo() -> bool:
        """Check if current directory is a git repository"""
        try:
            subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def has_unstaged_changes() -> bool:
        """Check if current directory has unstaged changes"""
        try:
            subprocess.run(
                ['git', 'update-index', '--refresh']
            )

            subprocess.run(
                ['git', 'diff-index', '--quiet', 'HEAD', '--'],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    @staticmethod
    def get_staged_diff() -> Optional[str]:
        """Get diff of staged changes"""
        try:
            result = subprocess.run(
                ['git', 'status'],
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)
            return True
        except subprocess.CalledProcessError:
            return False
        
    @staticmethod
    def stage_all_changes() -> bool:
        """Stage all existing changes"""
        try:
            result = subprocess.run(
                ['git', 'add', '.'],
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    @staticmethod
    def has_staged_changes() -> bool:
        """Check if there are staged changes"""
        diff = GitService.get_staged_diff()
        return bool(diff and diff.strip())
    
    @staticmethod
    def validate_hash(hash: str) -> bool:
        """Check if the repo has the specified hash"""
        try:
            subprocess.run(
                ['git', 'branch', '--contains', hash],
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
        
    @staticmethod
    def retrieve_commit(hash: str) -> Optional[str]:
        """Retrieve the diff of a commit from the current branch"""      
        if GitService.validate_hash(hash):
            try:
                result = subprocess.run(
                    ['git', 'show', hash ],
                    capture_output=True,
                    text=True,
                    check=True
                ) 
                return result.stdout
            except subprocess.CalledProcessError:
                return None

    @staticmethod
    def retrieve_range_commit_diff(hash1: str, hash2: str) -> Optional[str]:
        "Retrieve the diff between two commits from the current branch"
        if GitService.validate_hash(hash1):
            if GitService.validate_hash(hash2):
                try:
                    result = subprocess.run(
                    ['git', 'diff', hash1, hash2 ],
                    capture_output=True,
                    text=True,
                    check=True
                    ) 
                    return result.stdout
                except subprocess.CalledProcessError:
                    return None
    
    @staticmethod
    def commit(message: str) -> bool:
        """Create a git commit with the given message"""
        try:
            subprocess.run(
                ['git', 'commit', '-m', message],
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def get_list_of_ancestry_path(old_commit_hash: GitHash, new_commit_hash: GitHash) -> Optional[list]:
        if old_commit_hash.is_valid:
            if new_commit_hash.is_valid:
                if (GitService.is_ancestor(old_commit_hash, new_commit_hash)):
                    try:
                        result = subprocess.run(
                            ['git', 'rev-list', '--ancestry-path', old_commit_hash, new_commit_hash ],
                            capture_output=True,
                            text=True,
                            check=True
                        ) 
                        ancestry_path = []
                        for hash in result.stdout:
                            git_hash = GitHash(hash)
                            if git_hash.is_valid:
                                ancestry_path.append(git_hash)
                        ancestry_path.append(old_commit_hash)
                        return ancestry_path
                    except subprocess.CalledProcessError:
                        return None
                else:
                    raise ValueError(f"Old Commit Hash: ${old_commit_hash} is not ancestor of New Commit Hash: ${new_commit_hash}")
            else:
                raise ValueError(f"New Commit Hash: ${new_commit_hash} is not valid")
        else:
            raise ValueError(f"Old Commit Hash: ${old_commit_hash} is not valid")

    @staticmethod
    def is_ancestor(maybe_old_commit_hash: GitHash, maybe_new_commit_hash: GitHash) -> bool:
        if maybe_old_commit_hash.is_valid:
            if maybe_new_commit_hash.is_valid:
                try:
                    result = subprocess.run(
                        ['git', 'merge-base', '--is-ancestor', maybe_old_commit_hash, maybe_new_commit_hash ],
                        check=True
                    ) 
                    return True if result is 0 else False
                except subprocess.CalledProcessError:
                    return False
            else:
                raise ValueError(f"Maybe New Commit hash: ${maybe_new_commit_hash} is not valid")
        else:
            raise ValueError(f"Maybe New Commit Hash: ${maybe_old_commit_hash} is not valid")

        return False

    @staticmethod
    def get_all_files_touched_in_range(commit_range_list) -> Optional[list]:
        list_of_unique_files = []
        for commit_hash in commit_range_list:
            if commit_hash.is_valid:
                files_touched_in_commit = GitService.get_all_files_touched_in_commit(commit_hash)
                for file_name_status in files_touched_in_commit:
                    if ".meta" not in file_name_status:
                        if file_name_status not in list_of_unique_files:
                            list_of_unique_files.append(file_name_status)
            else:
                raise ValueError(f"Old Commit Hash: ${commit_hash.hash} is not valid")

        return list_of_unique_files

    @staticmethod
    def get_all_files_touched_in_commit(target_commit_hash: GitHash) -> Optional[list]:
        if target_commit_hash.is_valid:
            try:
                result = subprocess.run(
                    ['git', 'show', '--name-status', target_commit_hash.hash],
                    capture_output=True,
                    text=True,
                    check=True
                ) 
                return result.stdout
            except subprocess.CalledProcessError:
                return None
        else:
            raise ValueError(f"Target Commit Hash: ${target_commit_hash.hash} is not valid")

    @staticmethod
    def get_file_from_commit(file_path: str, target_commit_hash: GitHash) -> Optional[str]:
        if target_commit_hash.is_valid:
            if file_path:
                try:
                    hash_file_path = target_commit_hash.hash + ":" + file_path  
                    result = subprocess.run(
                        ['git', 'show', hash_file_path],
                        capture_output=True,
                        text=True,
                        check=True
                    ) 
                    return result.stdout
                except subprocess.CalledProcessError:
                    return None
            else:
                raise ValueError(f"file path: ${file_path} is not valid")
        else:
            raise ValueError(f"Target Commit Hash: ${target_commit_hash.hash} is not valid")

    @staticmethod
    def get_file_diff_between_commits(file_path: str, commit_hash_1: GitHash, commit_hash_2: GitHash) -> str:
        if commit_hash_1.is_valid:
            if commit_hash_2.is_valid:
                if file_path:
                    try:
                        result = subprocess.run(
                            ['git', 'diff', commit_hash_1.hash, commit_hash_2.hash, "--", file_path],
                            capture_output=True,
                            text=True,
                            check=True
                        ) 
                        return result.stdout
                    except subprocess.CalledProcessError:
                        return None
                else:
                    raise ValueError(f"file path: ${file_path} is not valid")
            else:
                raise ValueError(f"Target Commit Hash: ${commit_hash_2.hash} is not valid") 
        else:
            raise ValueError(f"Target Commit Hash: ${commit_hash_1.hash} is not valid") 

class CommitGenerator:
    """Generate commit messages using AI"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
    
    def generate_commit_message(self, diff: str, style: str = "conventional") -> Optional[str]:
        """Generate a commit message from git diff"""
        
        prompts = {
"conventional": 
"""You are a text editor, programming, C Sharp, Unity, and git commit message expert. Analyze the following git diff and generate a commit message following the Conventional Commits format.

Rules:
- Use format: <type>(<scope>): <subject>
- Types: feat, fix, docs, style, refactor, test, chore
- Subject should be lowercase, no period at end
- Count the number of changes and summarize each
- Address each change (Important)
- If needed, add a body explaining what and why (not how)

The changed files are in this diff: {diff}. Concentrate your analysis on these files only.

comments are indicated by '//', these provide context but are not always correct, evaluate for yourself

Generate ONLY the commit message, nothing else:""",
            

"semantic": 
"""You are a text editor, programming, C Sharp, Unity, git commit message,  expert. Analyze the following git diff and generate a clear, semantic commit message. The goal is to accurately describe the reason for the changes.

Rules:
- Start with a verb (Add, Update, Fix, Remove, etc.)
- Use present tense
- Describe was was wrong. Be explicit. Keep it concise (max 72 characters)
- Describe the change or changes in exacting detail. Do NOT guess. Keep it concise (max 72 characters)
- Describe the reason for each change. Keep it concise (max 72 characters)

The changed files are in this diff: {diff}. Concentrate your analysis on these files only.

Generate ONLY the commit message, nothing else:""",


"detailed-summary": 
"""You are a Unity, C Sharp, and git expert. Analyze the following git diff and generate a detailed commit message. Include both summary and body.

Rules:
- First line: Brief summary (max 50 chars)
- Blank line
- Body: Explain what and why (not how)
- Use bullet points if multiple changes

The changed files are in this diff: {diff}. Concentrate your analysis on these files only.

Generate ONLY the commit message, nothing else:""",


"detailed-newfiles": 
"""You are a Unity, C Sharp, git, and list making expert. Analyze the following git diff and generate a detailed bullet point list of the names of every new file.

Rules:
- Be specific.
- Do not summarize anything.
- First Line: New Files
- List every new file name in bullet point format. Be specific.
- If there are no new files say only "No new files"

The changed files are in this diff: {diff}. Concentrate your analysis on these files only.

Generate ONLY the commit message, nothing else:""",


"detailed-alteredfiles": 
"""You are a Unity, C Sharp, and git expert. Analyze the following git diff and generate a detailed list.

Rules:
- Use format: <FileName>: <Summary>
<EditedMembers>
<NewMember>
<EditedMethods>
<NewMethods>
- FileName: List all edited files (exclude .meta) in bullet point format. Only inlucde edited files.
- Summary: Summarize the changes (not how). Be specific.
- EditedMembers: List all edited members with old and new values. Be specific.
- NewMembers: List all new members. Only include new members. Be specific.
- EditedMethods: List all edited methods. Only included edited methods. Be specific.
- NewMethods: List all new methods. Only include new methods. Be specific.

The changed files are in this diff: {diff}. Concentrate your analysis on these files only.

Generate ONLY the commit message, nothing else:""",


"exact": 
"""You are a text, programming, C Sharp, Unity, C Sharp, and git expert. Analyze the following git diff.
Rules:
- Report any differences in exacting detail. 
- Do be concise
- Prioritize accuracy above all else.
- Review commit and update for accuracy.
- The changed files are in this diff: {diff}. Concentrate your analysis on these files only.

Generate ONLY the commit message, nothing else:"""
        }

        if style is "detailed":
            finalmessage = ""
            for promptkey in prompts.keys():
                if style in str(promptkey):
                    print(f"Generating {promptkey} prompt")
                    prompt = prompts.get(promptkey, prompts["conventional"]).format(diff=diff)  # Limit diff size
                    tokens = len(prompt.split())
                    print(f"Prompt Length: {len(prompt)}")
                    print(f"Tokens Required: {tokens}")
                    message = self.ollama.generate(prompt, tokens)
                    if message:
                        # Clean up the message
                        message = message.strip()
                        # Remove any markdown code blocks
                        if message.startswith('```'):
                            lines = message.split('\n\n')
                            message = '\n'.join(lines[1:-1] if len(lines) > 2 else lines)
                        message = message.strip()
                        message = message + "\n\n"
                        print(f"{message}")
                        finalmessage = finalmessage + message
                    else:
                        finalmessage = finalmessage + "No Response\n\n"
            message = finalmessage
        else:
            prompt = prompts.get(style, prompts["conventional"]).format(diff=diff)  # Limit diff size
            
            tokens = len(prompt.split())
            print(f"Prompt Length: {len(prompt)}")
            print(f"Tokens Required: {tokens}")
            message = self.ollama.generate(prompt, tokens)
        
            if message:
                # Clean up the message
                message = message.strip()
                # Remove any markdown code blocks
                if message.startswith('```'):
                    lines = message.split('\n')
                    message = '\n'.join(lines[1:-1] if len(lines) > 2 else lines)
                message = message.strip()
        
        return message

    def generate_single_file_message(self, diff: str, file_details: FileDetails, style: str = "conventional") -> Optional[str]:
        """Generate a commit message from git diff"""
        
        prompts = {
"single_file_general_new": 
"""You are a text editor, C Sharp, Unity, and git commit message expert. You are summarizing the purpose of this file by analyzing the following summaries, git diff, and files based on the provided references.

Summarize the reason this files has been added based on your analysis of the changes and purpose of this file using the following:
- `The New Code`: {file_details.newest_commit_complete_file}
- Summary based on `The New Code`: {file_details.ai_summary.complete_file_changes_summary}
Concentrate your analysis on these files for the summary.

Contextualize your summary with information from this diff: {diff}. 
Concentrate your analysis on this file for motivation and context.

comments are indicated by '//', these provide context but are not always correct, evaluate for yourself

Generate ONLY the summary, nothing else:""",


"single_file_general_changed": 
"""You are a text editor, C Sharp, Unity, and git commit message expert. You are summarizing the changes and purpose of this file by analyzing the following summaries, git diff, and files based on the provided references.

Summarize the changes and purpose of this file using the following:
- `The Old Code`: {file_details.oldest_commit_complete_file}
- `The New Code`: {file_details.newest_commit_complete_file}
- `The Changes`: {file_details.oldest_newest_diff}
- Summary comparing `The Old Code` and `The New Code`: {file_details.ai_summary.complete_file_changes_summary}
- Summary based on `The Changes`: {file_details.ai_summary.oldest_newest_diff_summary}
Concentrate your analysis on these files for the summary.

Contextualize your summary with information from this diff: {diff}. 
Concentrate your analysis on this file for motivation and context.

comments are indicated by '//', these provide context but are not always correct, evaluate for yourself

Generate ONLY the summary, nothing else:""",


"single_file_general_removed": 
"""You are a text editor, C Sharp, Unity, and git commit message expert. You are summarizing the reason that this file has been removed by analyzing the following summaries, git diff, and files based on the provided references.

Summarize the reason this file has been removed based on your analysis of the changes and purpose of this file using the following:
- `The Old Code`: {file_details.oldest_commit_complete_file}
- Summary based on `The Old Code`: {file_details.ai_summary.complete_file_changes_summary}
Concentrate your analysis on these files for the summary.

Contextualize your summary with information from this diff: {diff}. 
Concentrate your analysis on this file for motivation and context.

comments are indicated by '//', these provide context but are not always correct, evaluate for yourself

Generate ONLY the summary, nothing else:""",


"single_file_complete_file_changes_new": 
"""You are a text editor, C Sharp, Unity, and git commit message expert. You are summarizing the purpose of this file by analyzing the following summaries, git diff, and files based on the provided references.

Summarize the reason this files has been added based on your analysis of the changes and purpose of this file using the following:
- `The New Code`: {file_details.newest_commit_complete_file}
Concentrate your analysis on these files for the summary.

Contextualize your summary with information from this diff: {diff}. 
Concentrate your analysis on this file for motivation and context.

comments are indicated by '//', these provide context but are not always correct, evaluate for yourself

Generate ONLY the summary, nothing else:""",


"single_file_complete_file_changes_changed": 
"""You are a text editor, C Sharp, Unity, and git commit message expert. You are summarizing the changes and purpose of this file by analyzing the following summaries, git diff, and files based on the provided references.

Summarize the changes and purpose of this file using the following:
- `The Old Code`: {file_details.oldest_commit_complete_file}
- `The New Code`: {file_details.newest_commit_complete_file}
Concentrate your analysis on these files for the summary.

Contextualize your summary with information from this diff: {diff}. 
Concentrate your analysis on this file for motivation and context.

comments are indicated by '//', these provide context but are not always correct, evaluate for yourself

Generate ONLY the summary, nothing else:""",


"single_file_complete_file_changes_removed": 
"""You are a text editor, C Sharp, Unity, and git commit message expert. You are summarizing the reason that this file has been removed by analyzing the following summaries, git diff, and files based on the provided references.

Summarize the reason this file has been removed based on your analysis of the changes and purpose of this file using the following:
- `The Old Code`: {file_details.oldest_commit_complete_file}
Concentrate your analysis on these files for the summary.

Contextualize your summary with information from this diff: {diff}. 
Concentrate your analysis on this file for motivation and context.

comments are indicated by '//', these provide context but are not always correct, evaluate for yourself

Generate ONLY the summary, nothing else:""",


"single_file_oldest_newest_diff_new": 
"""You are a text editor, C Sharp, Unity, and git commit message expert. You are summarizing the reason and purpose this file has been added by analyzing the following diffs and files based on the provided references.

Summarize the reason this files has been added based on your analysis of the changes and purpose of this file using the following:
- `The New Diff`: {file_details.oldest_newest_diff}
Concentrate your analysis on these files for the summary.

Contextualize your summary with information from this diff: {diff}. 
Concentrate your analysis on this file for motivation and context.

comments are indicated by '//', these provide context but are not always correct, evaluate for yourself

Generate ONLY the summary, nothing else:""",


"single_file_oldest_newest_diff_changed": 
"""You are a text editor, C Sharp, Unity, and git commit message expert. You are summarizing the changes and purpose of this file by analyzing the following summaries, git diff, and files based on the provided references.

Summarize the changes and purpose of this file using the following:
- `The Changes`: {file_details.oldest_newest_diff}
Concentrate your analysis on these files for the summary.

Contextualize your summary with information from this diff: {diff}. 
Concentrate your analysis on this file for motivation and context.

comments are indicated by '//', these provide context but are not always correct, evaluate for yourself

Generate ONLY the summary, nothing else:""",


"single_file_oldest_newest_diff_removed": 
"""You are a text editor, C Sharp, Unity, and git commit message expert. You are summarizing the reason that this file has been removed by analyzing the following summaries, git diff, and files based on the provided references.

Summarize the reason this file has been removed based on your analysis of the changes and purpose of this file using the following:
- `The Changes`: {file_details.oldest_newest_diff}
Concentrate your analysis on these files for the summary.

Contextualize your summary with information from this diff: {diff}. 
Concentrate your analysis on this file for motivation and context.

comments are indicated by '//', these provide context but are not always correct, evaluate for yourself

Generate ONLY the summary, nothing else:""",
        }

        prompt = prompts.get(style, prompts["conventional"]).format(diff=diff)  # Limit diff size
        
        tokens = len(prompt.split())
        print(f"Prompt Length: {len(prompt)}")
        print(f"Tokens Required: {tokens}")
        message = self.ollama.generate(prompt, tokens)
    
        if message:
            # Clean up the message
            message = message.strip()
            # Remove any markdown code blocks
            if message.startswith('```'):
                lines = message.split('\n')
                message = '\n'.join(lines[1:-1] if len(lines) > 2 else lines)
            message = message.strip()

        
        return message

def print_banner():
    """Print application banner"""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════╗
║         🤖 AI Commit Message Tool         ║
║      Powered by Local Ollama 🦙           ║
╚═══════════════════════════════════════════╝
{Colors.END}
"""
    print(banner)


def print_diff_summary(diff: str):
    """Print a summary of the diff"""
    lines = diff.split('\n')
    added = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
    removed = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))
    
    print(f"{Colors.YELLOW}📊 Changes:{Colors.END}")
    print(f"  {Colors.GREEN}+ {added} lines added{Colors.END}")
    print(f"  {Colors.RED}- {removed} lines removed{Colors.END}")
    print()


def get_user_choice(message: str) -> str:
    """Get user input for yes/no questions"""
    while True:
        choice = input(f"{message} {Colors.CYAN}[y/n/r/e]{Colors.END}: ").lower()
        if choice in ['y', 'n', 'r', 'e']:
            return choice
        print(f"{Colors.RED}Invalid choice. Use y (yes), n (no), r (regenerate), or e (edit){Colors.END}")


def main():
    """Main application entry point"""
    print_banner()

    parser = argparse.ArgumentParser()    
    parser.add_argument("-c", "--commit", help="summarize specific commit", nargs=1, required=False)
    parser.add_argument("-r", "--range", help="summarize a range of commits", nargs=2, required=False)
    parser.add_argument("-m", "--model", help="select a model", nargs=1, required=False)
    parser.add_argument("-s", "--style", help="select a commit style", nargs=1, required=False)
    parser.add_argument("-a", "--autoStage", help="stages all files automatically", nargs=1, required=False)
    parser.add_argument("-b", "--bypass", help="agree to everything", nargs=1, required=False)

    args = parser.parse_args()

    # Check if we're in a git repository
    if not GitService.is_git_repo():
        print(f"{Colors.RED}❌ Error: Not a git repository{Colors.END}")
        print(f"{Colors.YELLOW}Please run this command in a git repository{Colors.END}")
        sys.exit(1)
    # Initialize Ollama client
    ollama = OllamaClient()
    available = ollama.list_models()

    style = "conventional"
    selected_model = "phi"
    shouldAutoSelect = True
    styleOverride = False

    oldest_commit_hash = ""
    newest_commit_hash = ""

    if args.style is not None:
        style = args.style[0]
        styleOverride = True


    if args.model is not None:
        print(f"Checking if {args.model[0]} is available")
        found = False
        matchingModel = ""
        for model in available:
            print(f"Comparing {args.model[0]} and {model}")
            if args.model[0] in model:
                matchingModel = model
                found = True
                break
        if found:
            selected_model = matchingModel
            print(f"{Colors.GREEN}✓ Specified model found: {Colors.BOLD}{selected_model}{Colors.END}")
            shouldAutoSelect = False
        else:
            print(f"{Colors.RED}❌ Error: {args.model[0]} model not detected. Defaulting to auto-select{Colors.YELLOW, Colors.END}")
            shouldAutoSelect = True


    if args.range is not None:
        print("summarize a range of commits")
        oldest_commit_hash = args.range[0]
        newest_commit_hash = args.range[1]
        diff = GitService.retrieve_range_commit_diff(args.range[0], args.range[1])
        if styleOverride is False:
            style = "detailed"
        if args.model is None:
            found = False
            for model in available:
                if "codellama" in model:
                    found = True
                    break
            if found:
                selected_model = "codellama"
                shouldAutoSelect = False
            else:
                print(f"{Colors.RED}❌ Error: codellama model not detected. Defaulting to auto-select{Colors.YELLOW, Colors.END}")
                shouldAutoSelect = True

    elif args.commit is not None:
        print(f"summarize the commit {args.commit}")
        oldest_commit_hash = args.range[0]
        newest_commit_hash = args.range[0]
        diff = GitService.retrieve_commit(args.commit[0])
        if styleOverride is False:
            style = "detailed"
        if args.model is None:
            found = False
            print(f"{Colors.RED}❌ Error: No selected model. Defaulting to auto-select{Colors.YELLOW, Colors.END}")
            for model in available:
                if "codellama" in model:
                    found = True
                    break
            if found:
                selected_model = "codellama"
                shouldAutoSelect = False
            else:
                print(f"{Colors.RED}❌ Error: codellama model not detected. Defaulting to auto-select{Colors.YELLOW, Colors.END}")
                shouldAutoSelect = True
    else:
        print("summarize staged changes")
        # Check for staged changes
        if not GitService.has_staged_changes():
            if args.autoStage is not None:
                if GitService.has_unstaged_changes():
                    if (GitService.stage_all_changes()):
                        if GitService.has_staged_changes():
                            print(f"{Colors.GREEN}✓ Successfully staged changes. Continuing.{Colors.END}\n")
                        else:
                            print(f"{Colors.RED}❌ Error: Unable to stage changes.{Colors.YELLOW, Colors.END}")
                            sys.exit(1)
                    else:
                            print(f"{Colors.RED}❌ Error: Unable to stage changes.{Colors.YELLOW, Colors.END}")
                            sys.exit(1)
                else:
                    print(f"{Colors.RED}❌ Error: No changes to stage.{Colors.YELLOW, Colors.END}")
                    sys.exit(1)
            else:
                print(f"{Colors.YELLOW}⚠️  No staged changes found{Colors.END}")
                print(f"{Colors.CYAN}Please stage your changes first:{Colors.END}")
                print(f"  git add <files>")

                # Ask user what to do
                print(f"{Colors.YELLOW}Options:{Colors.END}")
                print(f"  {Colors.GREEN}y{Colors.END} - Stage all available files")
                print(f"  {Colors.BLUE}e{Colors.END} - Exit")
                
                choice = get_user_choice("\nWhat would you like to do?")
                if choice == 'y':
                    if (GitService.stage_all_changes()):
                        if GitService.has_staged_changes():
                            print(f"{Colors.GREEN}✓ Successfully staged changes. Continuing.{Colors.END}\n")
                        else:
                            print(f"{Colors.RED}❌ Error: Unable to stage changes.{Colors.YELLOW, Colors.END}")
                            sys.exit(1)
                    else:
                            print(f"{Colors.RED}❌ Error: Unable to stage changes.{Colors.YELLOW, Colors.END}")
                            sys.exit(1)
                elif choice == 'e':
                    sys.exit(1)
        # Get staged diff
        diff = GitService.get_staged_diff()

    if not diff:
        print(f"{Colors.RED}❌ Error: Could not get git diff{Colors.YELLOW, Colors.END}")
        sys.exit(1)
    


    
    # Check if Ollama is running
    print(f"{Colors.CYAN}🔍 Checking Ollama server...{Colors.END}")
    if not ollama.is_available():
        print(f"{Colors.RED}❌ Error: Cannot connect to Ollama{Colors.END}")
        print(f"{Colors.YELLOW}Please make sure Ollama is running:{Colors.END}")
        print(f"  ollama serve")
        sys.exit(1)
    
    print(f"{Colors.GREEN}✓ Ollama server is running{Colors.END}\n")
    
    # List available models
    available_models = ollama.list_models()
    
    if not available_models:
        print(f"{Colors.RED}❌ No Ollama models found{Colors.END}")
        print(f"{Colors.YELLOW}Please install a model first:{Colors.END}")
        print(f"  ollama pull phi          # Fastest, recommended")
        print(f"  ollama pull mistral      # Good balance")
        print(f"  ollama pull llama2       # Default")
        sys.exit(1)
    
    # Display available models
    print(f"{Colors.CYAN}Available models ({len(available_models)}):{Colors.END}")
    for model in available_models:
        print(f"  • {model}")
    print()
    
    # Auto-select the best (lightest/fastest) model
    if shouldAutoSelect:
        selected_model = ollama.auto_select_model()
        if selected_model:
            ollama.model = selected_model
            print(f"{Colors.GREEN}✓ Auto-selected: {Colors.BOLD}{selected_model}{Colors.END}")
            print(f"{Colors.CYAN}  (Prioritizing lighter/faster models){Colors.END}\n")
        else:
            print(f"{Colors.YELLOW}Warning: Could not auto-select model, using first available{Colors.END}\n")
            ollama.model = available_models[0]
    else:
        if selected_model:
            ollama.model = selected_model
            print(f"{Colors.GREEN}✓ Selected: {Colors.BOLD}{selected_model}{Colors.END}")
        else:
            print(f"{Colors.YELLOW}Warning: Could not auto-select model, using first available{Colors.END}\n")
            ollama.model = available_models[0]
    
    
    print_diff_summary(diff)
    
    # Generate commit message
    generator = CommitGenerator(ollama)
    
    print(f"{Colors.CYAN}🤖 Generating {style} commit message...{Colors.END}\n")

    git_summary = None

    if oldest_commit_hash and newest_commit_hash:
        print(f"{Colors.CYAN}🤖 Building {style} git summary...{Colors.END}\n")
        git_summary = GitSummary(oldest_commit_hash, newest_commit_hash, generator, diff)
        while True:
            if git_summary.is_ready:
                break;
        git_summary.generate_summaries()
    
    while True:
        commit_message = generator.generate_commit_message(diff, style=style)
        
        if not commit_message:
            print(f"{Colors.RED}❌ Failed to generate commit message{Colors.END}")
            sys.exit(1)
        
        # Display generated message
        print(f"{Colors.GREEN}{Colors.BOLD}Generated Commit Message:{Colors.END}")
        print(f"{Colors.CYAN}{'─' * 50}{Colors.END}")
        print(f"{Colors.BOLD}{commit_message}{Colors.END}")
        print(f"{Colors.CYAN}{'─' * 50}{Colors.END}\n")

        git_summary.print_summaries()
        
        # Ask user what to do
        print(f"{Colors.YELLOW}Options:{Colors.END}")
        print(f"  {Colors.GREEN}y{Colors.END} - Accept and commit")
        print(f"  {Colors.YELLOW}r{Colors.END} - Regenerate message")
        print(f"  {Colors.BLUE}e{Colors.END} - Edit message")
        print(f"  {Colors.RED}n{Colors.END} - Cancel")

        if args.bypass is not None:
            choice = 'y'
        else:        
            choice = get_user_choice("\nWhat would you like to do?")
        
        if choice == 'y':
            # Commit with the generated message
            print(f"\n{Colors.CYAN}📝 Creating commit...{Colors.END}")
            if GitService.commit(commit_message):
                print(f"{Colors.GREEN}✓ Commit created successfully!{Colors.END}")
                sys.exit(0)
            else:
                print(f"{Colors.RED}❌ Failed to create commit{Colors.END}")
                sys.exit(1)
        
        elif choice == 'r':
            # Regenerate
            print(f"\n{Colors.CYAN}🔄 Regenerating...{Colors.END}\n")
            continue
        
        elif choice == 'e':
            # Edit message
            print(f"\n{Colors.CYAN}✏️  Enter your commit message (press Ctrl+D when done):{Colors.END}")
            try:
                lines = []
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                edited_message = '\n'.join(lines).strip()
                if edited_message:
                    if GitService.commit(edited_message):
                        print(f"{Colors.GREEN}✓ Commit created successfully!{Colors.END}")
                        sys.exit(0)
                    else:
                        print(f"{Colors.RED}❌ Failed to create commit{Colors.END}")
                        sys.exit(1)
        
        elif choice == 'n':
            # Cancel
            print(f"\n{Colors.YELLOW}Operation cancelled{Colors.END}")
            sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Operation cancelled by user{Colors.END}")
        sys.exit(0)
