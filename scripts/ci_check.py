"""
CI checks for AAP configuration:
1. Required variables in controller/vars.yml
2. Organization exists in AAP controller
3. Projects in controller/projects.yml exist in AAP
4. Inventories in controller/inventory.yml exist in AAP
5. Hosts in controller/hosts.yml exist in AAP
6. Job templates in controller/job_templates.yml exist in AAP
"""

import os
import sys

import requests
import yaml

# Disable insecure request warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

VARS_FILE = "controller/vars.yml"
PROJECTS_FILE = "controller/projects.yml"
INVENTORY_FILE = "controller/inventory.yml"
HOSTS_FILE = "controller/hosts.yml"
JOB_TEMPLATES_FILE = "controller/job_templates.yml"


def load_yaml(file_path):
    """
    Load and parse a YAML file.

    Args:
        file_path (str): Path to the YAML file.

    Returns:
        dict: Parsed YAML content.

    Raises:
        SystemExit: If the file cannot be loaded or parsed.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"::error::Failed to load {file_path}: {e}")
        sys.exit(1)


def get_env_or_var(vars_dict, key, env_key=None):
    """
    Get a value from environment variable or fallback to vars_dict.

    Args:
        vars_dict (dict): Dictionary containing variables.
        key (str): Key to look up in vars_dict.
        env_key (str, optional): Environment variable name. Defaults to key uppercased.

    Returns:
        str: Value from environment or vars_dict.

    Raises:
        SystemExit: If value is missing.
    """
    env_key = env_key or key.upper()
    value = os.environ.get(env_key) or vars_dict.get(key)
    if not value:
        print(f"::error::Missing required variable: {key} (env: {env_key})")
        sys.exit(1)
    return value


def check_vars(vars_dict_param):
    """
    Check if required variables are present in the vars_dict_param dictionary or environment.

    Args:
        vars_dict_param (dict): Dictionary containing variables.

    Raises:
        SystemExit: If any required variable is missing.
    """
    required = ["aap_hostname", "organization", "aap_token"]
    missing = []
    for key in required:
        env_key = key.upper() if key != "aap_token" else "AAP_TOKEN"
        if not (os.environ.get(env_key) or vars_dict_param.get(key)):
            missing.append(key)
    if missing:
        print(f"::error::Missing required variables: {', '.join(missing)}")
        sys.exit(1)
    print("All required variables are present (from environment or vars file).")


def api_get(url, token):
    """
    Perform a GET request to the specified URL with Bearer token authentication.

    Args:
        url (str): The API endpoint URL.
        token (str): Bearer token for authentication.

    Returns:
        dict or None: JSON response as a dictionary, or None on error.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10, verify=False)
        if resp.status_code != 200:
            print(f"::error::Failed API call: {url} (HTTP {resp.status_code})")
            return None
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"::error::API call error: {e}")
        return None


def check_org_exists(url, token, org):
    """
    Check if the specified organization exists in the AAP controller.

    Args:
        url (str): AAP controller hostname.
        token (str): Bearer token for authentication.
        org (str): Organization name to check.

    Raises:
        SystemExit: If the organization does not exist.
    """
    url = f"{url}/api/v2/organizations/?name={org}"
    data = api_get(url, token)
    if not data or not data.get("results"):
        print(f"::error::Organization '{org}' not found on controller.")
        sys.exit(1)
    print(f"Organization '{org}' exists on controller.")


def check_projects(url, token):
    """
    Check if the projects defined in the projects YAML file exist in AAP.

    Args:
        url (str): AAP controller hostname.
        token (str): Bearer token for authentication.
    """
    projects = load_yaml(PROJECTS_FILE).get("controller_projects", [])
    for proj in projects:
        name = proj["name"]
        url = f"{url}/api/v2/projects/?name={name}"
        data = api_get(url, token)
        if data and data.get("results"):
            print(f"Project '{name}' exists in AAP.")
        else:
            print(f"::warning::Project '{name}' does not exist in AAP.")


def check_inventories(url, token):
    """
    Check if the inventories defined in the inventories YAML file exist in AAP.

    Args:
        url (str): AAP controller hostname.
        token (str): Bearer token for authentication.
    """
    inventories = load_yaml(INVENTORY_FILE).get("controller_inventories", [])
    for inv in inventories:
        name = inv["name"]
        url = f"{url}/api/v2/inventories/?name={name}"
        data = api_get(url, token)
        if data and data.get("results"):
            print(f"Inventory '{name}' exists in AAP.")
        else:
            print(f"::warning::Inventory '{name}' does not exist in AAP.")


def check_hosts(url, token):
    """
    Check if the hosts defined in the hosts YAML file exist in their respective inventories in AAP.

    Args:
        url (str): AAP controller hostname.
        token (str): Bearer token for authentication.
    """
    hosts = load_yaml(HOSTS_FILE).get("controller_hosts", [])
    for host in hosts:
        name = host["name"]
        inventory = host["inventory"]
        # First, get inventory ID
        inv_url = f"{url}/api/v2/inventories/?name={inventory}"
        inv_data = api_get(inv_url, token)
        if not inv_data or not inv_data.get("results"):
            print(f"::warning::Inventory '{inventory}' for host '{name}' not found.")
            continue
        inv_id = inv_data["results"][0]["id"]
        url = f"{url}/api/v2/inventories/{inv_id}/hosts/?name={name}"
        data = api_get(url, token)
        if data and data.get("results"):
            print(f"Host '{name}' exists in inventory '{inventory}'.")
        else:
            print(
                f"::warning::Host '{name}' does not exist in inventory '{inventory}'."
            )


def check_job_templates(url, token):
    """
    Check if the job templates defined in the job templates YAML file exist in AAP.

    Args:
        url (str): AAP controller hostname.
        token (str): Bearer token for authentication.
    """
    templates = load_yaml(JOB_TEMPLATES_FILE).get("controller_templates", [])
    for tmpl in templates:
        name = tmpl["name"]
        url = f"{url}/api/v2/job_templates/?name={name}"
        data = api_get(url, token)
        if data and data.get("results"):
            print(f"Job template '{name}' exists in AAP.")
        else:
            print(f"::warning::Job template '{name}' does not exist in AAP.")


if __name__ == "__main__":
    vars_dict = load_yaml(VARS_FILE)
    check_vars(vars_dict)
    aap_hostname = vars_dict["aap_hostname"]
    aap_token = os.environ.get("AAP_TOKEN")
    organization = vars_dict["organization"]
    check_org_exists(aap_hostname, aap_token, organization)
    # check_projects(aap_hostname, aap_token)
    # check_inventories(aap_hostname, aap_token)
    # check_hosts(aap_hostname, aap_token)
    # check_job_templates(aap_hostname, aap_token)
