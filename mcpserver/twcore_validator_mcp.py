#!/usr/bin/env python3
"""
TW Core FHIR Validator MCP Server
"""

import os
import requests
import tarfile
import subprocess
from pathlib import Path
import shutil
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("TW Core FHIR Validator")

def _is_environment_setup():
    """Check if environment is already set up"""
    home = Path.home()
    packages_dir = home / ".fhir" / "packages" / "tw.gov.mohw.twcore#0.3.2"
    return packages_dir.exists() and os.path.exists("validator_cli.jar")

def _setup_environment_if_needed(version="0.3.2"):
    """Setup environment only if not already done"""
    if _is_environment_setup():
        return "Environment already set up"
    
    try:
        # Setup .fhir/packages directory
        home = Path.home()
        packages_dir = home / ".fhir" / "packages"
        packages_dir.mkdir(parents=True, exist_ok=True)
        
        # Download TW Core package
        url = f"https://twcore.mohw.gov.tw/ig/twcore/{version}/package.tgz"
        response = requests.get(url)
        response.raise_for_status()
        
        package_file = f"tw.gov.mohw.twcore-{version}.tgz"
        with open(package_file, 'wb') as f:
            f.write(response.content)
        
        # Extract package
        package_name = f"tw.gov.mohw.twcore#{version}"
        target_dir = packages_dir / package_name
        
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True)
        
        with tarfile.open(package_file, 'r:gz') as tar:
            tar.extractall(target_dir)
        os.remove(package_file)
        
        # Download validator CLI
        validator_url = "https://github.com/hapifhir/org.hl7.fhir.core/releases/latest/download/validator_cli.jar"
        response = requests.get(validator_url)
        response.raise_for_status()
        
        with open("validator_cli.jar", 'wb') as f:
            f.write(response.content)
        
        return f"Setup complete. Package installed in: {target_dir}"
        
    except Exception as e:
        return f"Setup failed: {str(e)}"

@mcp.tool()
def setup_environment(version: str = "0.3.2") -> str:
    """Setup TW Core IG validation environment (manual setup)"""
    return _setup_environment_if_needed(version)

@mcp.tool()
def execute_validator(json_file: str, ig_version: str = "tw.gov.mohw.twcore") -> str:
    """Execute FHIR validator on JSON file"""
    # Auto-setup if needed
    setup_result = _setup_environment_if_needed()
    if "failed" in setup_result.lower():
        return setup_result
    
    try:
        if not os.path.exists(json_file):
            return f"Error: File {json_file} not found"
        
        cmd = [
            "java", "-jar", "validator_cli.jar",
            json_file,
            "-version", "4.0",
            "-ig", ig_version
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        output = f"Exit code: {result.returncode}\n"
        output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}"
        
        return output
        
    except Exception as e:
        return f"Validation failed: {str(e)}"

def main():
    mcp.run()

if __name__ == "__main__":
    main()
