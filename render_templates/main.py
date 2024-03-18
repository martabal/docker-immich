#!/usr/bin/env python3

import argparse
import sys
from jinja2 import Environment, FileSystemLoader
import os
from shutil import copytree, rmtree
from typing import List, TypedDict, Optional


class Flavor(TypedDict):
    name: str
    machine_learning_provider: Optional[str]


def get_flavor_by_name(flavor_name) -> Optional[Flavor]:
    for flavor in flavors:
        if flavor["name"] == flavor_name:
            return flavor
    return None


flavors: List[Flavor] = [
    {
        "name": "cuda",
        "machine_learning_provider": "cuda",
    },
    {
        "name": "openvino",
        "machine_learning_provider": "openvino",
    },
    {
        "name": "classic",
        "machine_learning_provider": "cpu",
    },
    {
        "name": "noml",
        "machine_learning_provider": None,
    },
]
dockerfile_template_name: str = "Dockerfile.j2"
output_dir: str = os.getcwd()
templates_dir: str = os.path.join(output_dir, "templates")
build_folder_prefix = "build-"

env = Environment(loader=FileSystemLoader(templates_dir))
dockerfile_template = env.get_template(dockerfile_template_name)

subfolders_templates_run: List[str] = [
    os.path.basename(f.path) for f in os.scandir(templates_dir) if f.is_dir()
]


def generate_all(build_path: Optional[str] = None) -> None:
    print("generating Dockerfiles and context for all flavors: ")
    for flavor in flavors:

        if build_path:
            build_folder = os.path.join(output_dir, build_path)
            flavor_folder = os.path.join(
                build_folder, f"{build_folder_prefix}{flavor['name']}"
            )
        else:
            flavor_folder = os.path.join(
                output_dir, f"{build_folder_prefix}{flavor['name']}"
            )

        generate_template(
            flavor_folder,
            flavor,
        )


def generate_template(
    flavor_folder: str,
    flavor: Flavor,
) -> None:

    flavor_name = flavor["name"]
    machine_learning_provider = flavor["machine_learning_provider"]
    flavor_root_folder = os.path.join(flavor_folder, "root")
    dockerfile_filepath = os.path.join(flavor_folder, "Dockerfile")

    if not os.path.exists(flavor_folder):
        os.makedirs(flavor_folder)

    if os.path.exists(flavor_root_folder):
        rmtree(flavor_root_folder)

    if os.path.exists(dockerfile_filepath):
        os.remove(dockerfile_filepath)

    variables = {
        "machine_learning_provider": machine_learning_provider,
    }

    dockerfile_rendered_template = dockerfile_template.render(variables)

    with open(dockerfile_filepath, "w") as dockerfile:
        dockerfile.write(dockerfile_rendered_template)

    copytree(os.path.join(output_dir, "root"), flavor_root_folder)

    for subfolder in subfolders_templates_run:
        folder_name = os.path.basename(subfolder)
        if not (
            machine_learning_provider is None and "machine-learning" in folder_name
        ):
            init_config_template_name: str = os.path.join(subfolder, "run.j2")
            init_config_template = env.get_template(init_config_template_name)
            init_config_rendered_template: str = init_config_template.render(variables)

            folder_dir_path: str = os.path.join(
                os.path.join(flavor_root_folder, "etc/s6-overlay/s6-rc.d"),
                folder_name,
            )
            run_filepath: str = os.path.join(folder_dir_path, "run")

            with open(run_filepath, "w") as run:
                run.write(init_config_rendered_template)
                st = os.stat(run_filepath)
                os.chmod(run_filepath, st.st_mode | 0o111)
        if machine_learning_provider is None and "machine-learning" in folder_name:
            rmtree(
                os.path.join(
                    flavor_root_folder, "etc/s6-overlay/s6-rc.d/svc-machine-learning"
                )
            )
            os.remove(
                os.path.join(
                    flavor_root_folder,
                    "etc/s6-overlay/s6-rc.d/user/contents.d/svc-machine-learning",
                )
            )
    print(f" - Dockerfile and context for {flavor_name} generated successfully.")


def init(argv: Optional[List[str]] = None) -> None:
    if argv is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description="Example program with optional arguments"
    )
    parser.add_argument(
        "-b",
        "--build-path",
        help="Specify the build path",
        type=str,
    )
    parser.add_argument(
        "-f",
        "--flavor",
        help="Specify the flavor",
        type=str,
        choices=[flavor["name"] for flavor in flavors],
    )

    args = parser.parse_args(argv)

    if args.flavor is not None:
        flavor = get_flavor_by_name(args.flavor)
        flavor_name = flavor["name"]
        if flavor is None:
            raise Exception(f"Flavor {args.flavor} does not exist")

        if args.build_path:
            build_folder = os.path.join(output_dir, args.build_path)
            flavor_folder = os.path.join(
                build_folder, f"{build_folder_prefix}{flavor_name}"
            )
        else:
            flavor_folder = os.path.join(
                output_dir, f"{build_folder_prefix}{flavor_name}"
            )
        print(f"generating Dockerfiles and context for {flavor_name}: ")
        generate_template(
            flavor_folder,
            flavor,
        )

    else:
        generate_all(args.build_path)


if __name__ == "__main__":
    init()
