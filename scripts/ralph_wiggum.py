"""
Ralph Wiggum Loop Implementation

Autonomous multi-step task completion using the Ralph Wiggum pattern.
Keeps Qwen Code working until a task is complete by intercepting exit attempts
and re-injecting prompts when tasks are incomplete.

Usage:
    python ralph_loop.py "Process all files in Needs_Action" --vault /path/to/vault

Reference: https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum
"""

import os
import sys
import subprocess
import signal
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable


class RalphWiggumLoop:
    """
    Ralph Wiggum Loop for autonomous task completion.
    
    How it works:
    1. Start Qwen Code with a prompt
    2. Monitor for exit attempt
    3. Check if task is complete
    4. If not complete, re-inject prompt and continue
    5. Repeat until complete or max iterations
    """
    
    def __init__(self, vault_path: str, max_iterations: int = 10,
                 completion_check: Callable = None):
        """
        Initialize Ralph Wiggum Loop.
        
        Args:
            vault_path: Path to the Obsidian vault
            max_iterations: Maximum loop iterations
            completion_check: Function to check if task is complete
        """
        self.vault_path = Path(vault_path)
        self.max_iterations = max_iterations
        self.completion_check = completion_check or self._default_completion_check
        
        # Paths
        self.logs_dir = self.vault_path / 'Logs'
        self.plans_dir = self.vault_path / 'Plans'
        self.done_dir = self.vault_path / 'Done'
        self.needs_action_dir = self.vault_path / 'Needs_Action'
        
        # Ensure directories exist
        for dir_path in [self.logs_dir, self.plans_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # State
        self.iteration = 0
        self.running = False
        self.current_process: Optional[subprocess.Popen] = None
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging."""
        import logging
        
        log_file = self.logs_dir / f'ralph_loop_{datetime.now().strftime("%Y%m%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('RalphWiggum')
    
    def _default_completion_check(self) -> bool:
        """
        Default completion check.
        
        Checks if Needs_Action folder is empty.
        Override with custom check for specific tasks.
        """
        # Task is complete if Needs_Action is empty
        pending = list(self.needs_action_dir.glob('*.md'))
        return len(pending) == 0
    
    def _check_qwen_available(self) -> bool:
        """Check if Qwen Code is available."""
        try:
            result = subprocess.run(
                ['qwen', '--version'],
                capture_output=True,
                text=True,
                timeout=10,
                shell=True
            )
            return result.returncode == 0
        except:
            return False
    
    def run(self, prompt: str, completion_promise: str = None):
        """
        Run the Ralph Wiggum Loop.
        
        Args:
            prompt: Initial prompt for Qwen Code
            completion_promise: String that indicates completion when output
        """
        self.logger.info("=" * 60)
        self.logger.info("Ralph Wiggum Loop Starting")
        self.logger.info(f"Vault: {self.vault_path}")
        self.logger.info(f"Max iterations: {self.max_iterations}")
        self.logger.info(f"Prompt: {prompt[:100]}...")
        self.logger.info("=" * 60)
        
        # Check Qwen availability
        if not self._check_qwen_available():
            self.logger.error("Qwen Code not found. Install with: npm install -g @anthropics/qwen-code")
            return
        
        self.running = True
        self.iteration = 0
        
        current_prompt = prompt
        
        while self.running and self.iteration < self.max_iterations:
            self.iteration += 1
            self.logger.info(f"\n{'='*40}")
            self.logger.info(f"Iteration {self.iteration}/{self.max_iterations}")
            self.logger.info(f"{'='*40}")
            
            # Run Qwen Code
            result = self._run_qwen(current_prompt)
            
            # Check completion
            if self._is_complete(result, completion_promise):
                self.logger.info("\n✓ Task completed successfully!")
                self.running = False
                break
            
            # Not complete - prepare for next iteration
            self.logger.info("Task not complete, continuing...")
            current_prompt = self._prepare_next_prompt(result, prompt)
            
            # Small delay between iterations
            time.sleep(2)
        
        if self.iteration >= self.max_iterations:
            self.logger.warning(f"\nReached max iterations ({self.max_iterations})")
        
        self.logger.info("\nRalph Wiggum Loop finished")
    
    def _run_qwen(self, prompt: str) -> dict:
        """
        Run Qwen Code with the given prompt.
        
        Args:
            prompt: Prompt to send to Qwen
            
        Returns:
            dict with stdout, stderr, returncode
        """
        try:
            self.logger.info("Starting Qwen Code...")
            
            # Run Qwen Code
            process = subprocess.Popen(
                ['qwen', '--prompt', prompt],
                cwd=str(self.vault_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True
            )
            
            self.current_process = process
            
            # Wait for completion (with timeout)
            try:
                stdout, stderr = process.communicate(timeout=300)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                self.logger.error("Qwen Code timed out")
            
            self.logger.info(f"Qwen Code exited with code {process.returncode}")
            
            # Log output (first 500 chars)
            if stdout:
                self.logger.info(f"Output: {stdout[:500]}...")
            if stderr:
                self.logger.warning(f"Stderr: {stderr[:500]}...")
            
            return {
                'stdout': stdout or '',
                'stderr': stderr or '',
                'returncode': process.returncode
            }
            
        except Exception as e:
            self.logger.error(f"Error running Qwen Code: {e}")
            return {
                'stdout': '',
                'stderr': str(e),
                'returncode': 1
            }
    
    def _is_complete(self, result: dict, completion_promise: str = None) -> bool:
        """
        Check if the task is complete.
        
        Args:
            result: Result from Qwen Code run
            completion_promise: String that indicates completion
            
        Returns:
            True if complete
        """
        # Check completion promise in output
        if completion_promise:
            if completion_promise in result.get('stdout', ''):
                self.logger.info(f"Completion promise found: {completion_promise}")
                return True
        
        # Check using completion check function
        if self.completion_check():
            self.logger.info("Completion check passed")
            return True
        
        # Check for error states
        if result.get('returncode', 0) != 0:
            self.logger.warning("Qwen Code returned error")
            return False
        
        return False
    
    def _prepare_next_prompt(self, previous_result: dict, original_prompt: str) -> str:
        """
        Prepare prompt for next iteration.
        
        Args:
            previous_result: Result from previous Qwen run
            original_prompt: Original prompt
            
        Returns:
            New prompt for next iteration
        """
        # Create continuation prompt
        next_prompt = f"""{original_prompt}

CONTINUATION: You previously worked on this task but did not complete it.

Previous output:
{previous_result.get('stdout', '')[:2000]}

Continue working on the task. Review what was done and what still needs to be done.
Complete any remaining steps and move completed items to /Done.

If you encounter errors, try to resolve them or document what needs human intervention.
"""
        return next_prompt
    
    def stop(self):
        """Stop the loop."""
        self.logger.info("Stopping Ralph Wiggum Loop...")
        self.running = False
        
        if self.current_process:
            self.current_process.terminate()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ralph Wiggum Loop for Qwen Code')
    parser.add_argument('prompt', help='Initial prompt for Qwen Code')
    parser.add_argument('--vault', help='Path to Obsidian vault')
    parser.add_argument('--max-iterations', type=int, default=10, 
                       help='Maximum loop iterations')
    parser.add_argument('--completion-promise', help='String indicating completion')
    
    args = parser.parse_args()
    
    # Default vault path
    default_vault = Path(__file__).parent.parent / 'AI_Employee_Vault'
    vault_path = args.vault if args.vault else str(default_vault)
    
    # Create loop
    loop = RalphWiggumLoop(vault_path, max_iterations=args.max_iterations)
    
    # Handle Ctrl+C
    def signal_handler(sig, frame):
        print("\nInterrupted by user")
        loop.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run loop
    loop.run(args.prompt, completion_promise=args.completion_promise)


if __name__ == '__main__':
    main()
