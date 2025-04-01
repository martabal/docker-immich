#!/usr/bin/env python3

import argparse
from jinja2 import Environment, FileSystemLoader
import os
import shutil
import sys
from typing import List, TypedDict, Optional
from .patches import (
    ApplyPatches,
    PatchType,
    Patches,
    get_matching_patches,
)


class Flavor(TypedDict):
    name: str
    machine_learning_provider: Optional[str]


class App:
    flavors: List[Flavor] = [
        {
            "name": "rknn",
            "machine_learning_provider": "rknn",
        },
        {
            "name": "armnn",
            "machine_learning_provider": "armnn",
        },
        {
            "name": "cpu",
            "machine_learning_provider": "cpu",
        },
        {
            "name": "cuda",
            "machine_learning_provider": "cuda",
        },
        {
            "name": "noml",
            "machine_learning_provider": None,
        },
        {
            "name": "openvino",
            "machine_learning_provider": "openvino",
        },
    ]
    dockerfile_template_name = "Dockerfile.j2"
    output_dir = os.getcwd()
    patches_dir = os.path.join(output_dir, "patches")
    patches_build_dir = "patches"
    templates_dir = os.path.join(output_dir, "templates")
    build_folder_prefix = "build-"
    s6_path = "etc/s6-overlay/s6-rc.d"
    s6_content = os.path.join(s6_path, "user/contents.d")
    machine_learning_svc = "svc-machine-learning"
    machine_learning_svc_path = os.path.join(s6_path, machine_learning_svc)
    machine_learning_svc_content = os.path.join(s6_content, machine_learning_svc)

    env = Environment(loader=FileSystemLoader(templates_dir))
    dockerfile_template = env.get_template(dockerfile_template_name)

    subfolders_templates_run = [
        os.path.basename(f.path) for f in os.scandir(templates_dir) if f.is_dir()
    ]


def generate_all(
    build_path: Optional[str] = None,
    print_content: Optional[bool] = None,
    no_generate: Optional[bool] = None,
    patch_path: Optional[Patches] = None,
) -> None:
    if no_generate is False:
        print("generating Dockerfiles and context for all flavors: ")
    for flavor in App.flavors:
        build_folder_name = App.build_folder_prefix + flavor["name"]
        if build_path:
            root_folder = os.path.join(App.output_dir, build_path)
            build_folder = os.path.join(root_folder, build_folder_name)
        else:
            build_folder = os.path.join(App.output_dir, build_folder_name)

        if no_generate is False:
            generate_template(build_folder, flavor, patch_path)
        if print_content is True:
            dockerfile_path = os.path.join(build_folder, "Dockerfile")
            print_dockerfile_content(dockerfile_path)


def generate_template(
    build_folder: str,
    flavor: Flavor,
    patch_path: Optional[Patches] = None,
) -> None:
    flavor_name = flavor["name"]
    machine_learning_provider = flavor["machine_learning_provider"]
    root_folder_path = os.path.join(build_folder, "root")
    dockerfile_path = os.path.join(build_folder, "Dockerfile")

    project_patches: ApplyPatches = {
        PatchType.CLI.value: len(patch_path[PatchType.CLI.value]) > 0
        if patch_path
        else False,
        PatchType.ML.value: (
            len(patch_path[PatchType.ML.value]) > 0
            if machine_learning_provider
            else False
        )
        if patch_path
        else False,
        PatchType.SCRIPTS.value: len(patch_path[PatchType.SCRIPTS.value]) > 0
        if patch_path
        else False,
        PatchType.SERVER.value: len(patch_path[PatchType.SERVER.value]) > 0
        if patch_path
        else False,
        PatchType.WEB.value: len(patch_path[PatchType.WEB.value]) > 0
        if patch_path
        else False,
    }

    patches_path = os.path.join(build_folder, App.patches_build_dir)
    patches = (
        project_patches["web"]
        or project_patches["server"]
        or project_patches["cli"]
        or project_patches["ml"]
    )

    if not os.path.exists(build_folder):
        os.makedirs(build_folder)

    if patches and os.path.exists(patches_path):
        shutil.rmtree(patches_path)

    if os.path.exists(root_folder_path):
        shutil.rmtree(root_folder_path)

    if os.path.exists(dockerfile_path):
        os.remove(dockerfile_path)

    variables = {
        "machine_learning_provider": machine_learning_provider,
        "patches": patches,
    }

    dockerfile_rendered_template = App.dockerfile_template.render(variables)

    with open(dockerfile_path, "w") as dockerfile:
        dockerfile.write(dockerfile_rendered_template)

    shutil.copytree(os.path.join(App.output_dir, "root"), root_folder_path)

    if patches:
        projects = [patch_type.value for patch_type in PatchType]
        for project in projects:
            if len(patch_path[project]) > 0:
                pathes_build_path = os.path.join(build_folder, App.patches_build_dir)
                project_build_dir = os.path.join(pathes_build_path, project)
                os.makedirs(project_build_dir, exist_ok=True)
                for path in patch_path[project]:
                    dest_path = os.path.join(project_build_dir, os.path.basename(path))
                    shutil.copyfile(path, dest_path)

    for subfolder in App.subfolders_templates_run:
        folder_name = os.path.basename(subfolder)
        if not (
            machine_learning_provider is None and "machine-learning" in folder_name
        ):
            run_template_name = os.path.join(subfolder, "run.j2")
            run_template = App.env.get_template(run_template_name)
            run_rendered_template = run_template.render(variables)

            s6_rc_path = os.path.join(
                os.path.join(root_folder_path, App.s6_path),
                folder_name,
            )
            run_path = os.path.join(s6_rc_path, "run")

            with open(run_path, "w") as run:
                run.write(run_rendered_template)
                st = os.stat(run_path)
                os.chmod(run_path, st.st_mode | 0o111)

        if machine_learning_provider is None and "machine-learning" in folder_name:
            shutil.rmtree(os.path.join(root_folder_path, App.machine_learning_svc_path))
            os.remove(
                os.path.join(
                    root_folder_path,
                    App.machine_learning_svc_content,
                )
            )
    print(f" - Dockerfile and context for {flavor_name} generated successfully.")


def get_flavor_by_name(flavor_name: str) -> Optional[Flavor]:
    for flavor in App.flavors:
        if flavor["name"] == flavor_name:
            return flavor
    return None


def print_dockerfile_content(dockerfile_path: str) -> None:
    print("\nDockerfile generated")
    with open(dockerfile_path, "r") as f:
        print(f.read())


def init(argv: Optional[List[str]] = None):
    if argv is None:
        args = sys.argv
    parser = argparse.ArgumentParser(
        description="Render templates for different AIO flavors"
    )
    parser.add_argument(
        "-b",
        "--build-path",
        help="Specify the build path",
        type=str,
        required=False,
    )
    parser.add_argument(
        "-f",
        "--flavor",
        help="Specify the flavor",
        type=str,
        choices=[flavor["name"] for flavor in App.flavors],
        required=False,
    )
    parser.add_argument(
        "-p",
        "--print-dockerfile",
        help="Show the generated Dockerfiles",
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-n",
        "--no-generate",
        help="Do not generate the generate Dockerfile(s)",
        action="store_true",
        required=False,
    )

    parser.add_argument(
        "--enable-patches",
        help="Use patches (require --immich-version)",
        action="store_true",
        required=False,
    )

    parser.add_argument(
        "--immich-version",
        help="Immich version",
        type=str,
        required=False,
    )

    args = parser.parse_args(argv)
    if args.print_dockerfile is False and args.no_generate is True:
        parser.error("You can't have --no-generate without --print-dockerfile")

    if args.enable_patches is False and args.immich_version is None:
        print("Immich version not passed")

    patches = (
        get_matching_patches(App.patches_dir, args.immich_version)
        if args.enable_patches is True and args.immich_version is not None
        else None
    )

    if args.flavor is not None:
        flavor = get_flavor_by_name(args.flavor)
        flavor_name = flavor["name"]
        if flavor is None:
            raise Exception(f"Flavor {args.flavor} does not exist")

        build_folder_name = App.build_folder_prefix + flavor_name
        if args.build_path:
            root_folder = os.path.join(App.output_dir, args.build_path)
            build_folder = os.path.join(root_folder, build_folder_name)
        else:
            build_folder = os.path.join(App.output_dir, build_folder_name)
        print(f"generating Dockerfiles and context for {flavor_name}: ")

        if args.no_generate is False:
            generate_template(build_folder, flavor, patches)
        if args.print_dockerfile is True:
            dockerfile_path = os.path.join(build_folder, "Dockerfile")
            print_dockerfile_content(dockerfile_path)

    else:
        generate_all(args.build_path, args.print_dockerfile, args.no_generate, patches)


if __name__ == "__main__":
    init()
