#!/usr/bin/env python3

import argparse
from jinja2 import Environment, FileSystemLoader
import os
from shutil import copytree, rmtree
from typing import List, Tuple, TypedDict, Optional


class FlavorType(TypedDict):
    name: str
    machine_learning_provider: Optional[str]


class Flavor(TypedDict):
    types: List[FlavorType]
    name: str
    machine_learning: bool


flavors: List[Flavor] = [
    {
        "types": [
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
        ],
        "name": "main",
        "machine_learning": True,
    },
    {
        "types": [
            {
                "name": "classic",
                "machine_learning_provider": None,
            },
        ],
        "name": "noml",
        "machine_learning": False,
    },
]
dockerfile_template_name = "Dockerfile.j2"
output_dir = os.getcwd()
templates_dir = os.path.join(output_dir, "templates")

env = Environment(loader=FileSystemLoader(templates_dir))
dockerfile_template = env.get_template(dockerfile_template_name)

subfolders_templates_run = [
    os.path.basename(f.path) for f in os.scandir(templates_dir) if f.is_dir()
]


def get_type_flavor(
    type_name: str, flavor_name: str
) -> Optional[Tuple[FlavorType, Flavor]]:
    for flavor in flavors:
        if flavor["name"] == type_name:
            for flavor_type in flavor["types"]:
                if flavor_type["name"] == flavor_name:
                    return flavor_type, flavor
    return None


def get_flavor_choices() -> List[str]:
    choices = set()
    for flavor in flavors:
        for flavor_type in flavor["types"]:
            choices.add(flavor_type["name"])
    return list(choices)


def generate_all() -> None:
    for i, flavor in enumerate(flavors):
        print(f"generating Dockerfiles and context for {flavor['name']}: ")

        type_folder = os.path.join(output_dir, f"build-{flavor['name']}")

        for type in flavor["types"]:
            generate_template(
                type["name"],
                type_folder,
                type["machine_learning_provider"],
                flavor["machine_learning"],
            )

        if i < len(flavors) - 1:
            print("")


def generate_template(
    type_name: str,
    type_folder: str,
    type_machine_learning_provider,
    flavor_machine_learning,
) -> None:
    flavor_folder = os.path.join(type_folder, type_name)
    flavor_root_folder = os.path.join(flavor_folder, "root")
    dockerfile_filepath = os.path.join(flavor_folder, "Dockerfile")

    if not os.path.exists(flavor_folder):
        os.makedirs(flavor_folder)

    if os.path.exists(flavor_root_folder):
        rmtree(flavor_root_folder)

    if os.path.exists(dockerfile_filepath):
        os.remove(dockerfile_filepath)

    variables = {
        "gpu_acceleration_name": type_machine_learning_provider,
        "machine_learning": flavor_machine_learning,
    }

    dockerfile_rendered_template = dockerfile_template.render(variables)

    with open(dockerfile_filepath, "w") as dockerfile:
        dockerfile.write(dockerfile_rendered_template)

    copytree(os.path.join(output_dir, "root"), flavor_root_folder)

    for subfolder in subfolders_templates_run:
        folder_name = os.path.basename(subfolder)
        if not (flavor_machine_learning is False and "machine-learning" in folder_name):
            init_config_template_name = os.path.join(subfolder, "run.j2")
            init_config_template = env.get_template(init_config_template_name)
            init_config_rendered_template = init_config_template.render(variables)

            folder_dir = os.path.join(
                os.path.join(flavor_root_folder, "etc/s6-overlay/s6-rc.d"),
                folder_name,
            )
            run_filepath = os.path.join(folder_dir, "run")

            with open(run_filepath, "w") as run:
                run.write(init_config_rendered_template)
                st = os.stat(run_filepath)
                os.chmod(run_filepath, st.st_mode | 0o111)
        if flavor_machine_learning is False and "machine-learning" in folder_name:
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
    print(f" - Dockerfile and context for {type_name} generated successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Example program with optional arguments"
    )
    parser.add_argument(
        "-t",
        "--type",
        help="Specify the type",
        type=str,
        choices=[flavor["name"] for flavor in flavors],
    )
    parser.add_argument(
        "-f",
        "--flavor",
        help="Specify the flavor",
        type=str,
        choices=get_flavor_choices(),
    )

    args = parser.parse_args()

    if args.type is not None and args.flavor is not None:
        type_flavor_info = get_type_flavor(args.type, args.flavor)
        if type_flavor_info:
            flavor_type, flavor = type_flavor_info
            type_folder = os.path.join(output_dir, f"build-{flavor['name']}")
            print(f"generating Dockerfiles and context for {args.type}: ")
            generate_template(
                flavor_type["name"],
                type_folder,
                flavor_type["name"],
                flavor["machine_learning"],
            )
        else:
            print(f"Can't generate templates for {args.type} - {args.flavor}")
            exit(1)
    elif args.type is None and args.flavor is None:
        generate_all()
    else:
        print(
            f"Please provide a {'type' if args.type is None else 'flavor'}; you need to provide both --type and --flavor arguments"
        )
        exit(1)


if __name__ == "__main__":
    main()
