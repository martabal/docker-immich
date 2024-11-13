from enum import Enum
import json
import os
import re
from typing import List, Optional, TypedDict


class Patches(TypedDict):
    cli: List[str]
    ml: List[str]
    scripts: List[str]
    server: List[str]
    web: List[str]


class ApplyPatches(TypedDict):
    cli: bool
    ml: bool
    scripts: bool
    server: bool
    web: bool


class PatchType(Enum):
    CLI = "cli"
    ML = "ml"
    SCRIPTS = "scripts"
    SERVER = "server"
    WEB = "web"


def extract_source_project(diff_text):
    match = re.search(r"diff --git a/([^/]+)/", diff_text)
    if match:
        project = (
            PatchType.ML if match.group(1) == "machine-learning" else match.group(1)
        )
        return project
    return None


def get_matching_patches(folder_path, current_version) -> Patches:
    patch_paths: Patches = {"cli": [], "ml": [], "scripts": [], "server": [], "web": []}
    current_version = current_version.lstrip("v")
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            json_file_path = os.path.join(folder_path, filename)
            patch_file_path = json_file_path.replace(".json", ".patch")

            if os.path.exists(patch_file_path):
                with open(json_file_path, "r") as json_file:
                    data = json.load(json_file)
                    version_range = data.get("version").lstrip("v")
                    if version_range == current_version:
                        patch_file_content = open(patch_file_path, "r").read()
                        apply_to_project: Optional[PatchType] = extract_source_project(
                            patch_file_content
                        )
                        if apply_to_project in patch_paths:
                            patch_paths[apply_to_project].append(patch_file_path)

    all_patch_files = [
        os.path.basename(file)
        for patch_list in patch_paths.values()
        for file in patch_list
    ]
    print(f"Patches applied: {all_patch_files}\n")
    return patch_paths
